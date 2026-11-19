import json, pytest
from fastapi.testclient import TestClient
from app import db
from app.main import app, S
from app.core.settings import get_settings

c = TestClient(app); ADMIN = {"X-API-Key": "adm"}; ANALYST = {"X-API-Key": "ana"}

@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_DATABASE_URL", f"sqlite:///{tmp_path}/sec.db"); monkeypatch.setenv("FG_API_KEY", "adm"); monkeypatch.setenv("FG_ANALYST_API_KEY", "ana")
    monkeypatch.setenv("FG_ARTIFACT_DIR", str(tmp_path)); return monkeypatch

def test_roles_admin_vs_analyst(env):
    S.load_demo(42); a = c.get("/api/v1/alerts").json()["items"][0]["alert_id"]
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "under_review"}, headers=ANALYST).status_code == 200      # analyst may update cases
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "resolved"}, headers=ADMIN).status_code == 200            # admin may too
    for r in (c.patch("/api/v1/config", json={"high": 0.7}, headers=ANALYST), c.post("/api/v1/experiments", json={}, headers=ANALYST),
              c.post("/api/v1/datasets/upload", files={"transactions": ("t.csv", b"a\n1\n", "text/csv")}, headers=ANALYST)):
        assert r.status_code == 403 and "admin" in r.json()["detail"]
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "open"}).status_code == 401
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "open"}, headers={"X-API-Key": "wrong"}).status_code == 401
    assert c.patch("/api/v1/config", json={"high": 0.65}, headers=ADMIN).status_code == 200; c.patch("/api/v1/config", json={"high": 0.6}, headers=ADMIN)

def test_analyst_key_disabled_when_unset_and_audit_has_role_not_key(env):
    S.load_demo(42); a = c.get("/api/v1/alerts").json()["items"][0]["alert_id"]
    c.patch(f"/api/v1/alerts/{a}", json={"status": "escalated", "note": "secret-note"}, headers=ANALYST)
    with db.session() as s: rows = [x.detail for x in s.query(db.Audit)]
    blob = " ".join(rows); assert '"role": "analyst"' in blob and "ana" not in blob.replace("analyst", "") and "secret-note" not in blob
    env.delenv("FG_ANALYST_API_KEY"); assert c.patch(f"/api/v1/alerts/{a}", json={"status": "open"}, headers=ANALYST).status_code == 401

def test_settings_reject_identical_or_negative(monkeypatch):
    monkeypatch.setenv("FG_API_KEY", "x"); monkeypatch.setenv("FG_ANALYST_API_KEY", "x")
    with pytest.raises(ValueError): get_settings()
    monkeypatch.delenv("FG_ANALYST_API_KEY"); monkeypatch.setenv("FG_RATE_LIMIT_PER_MINUTE", "-1")
    with pytest.raises(ValueError): get_settings()

def test_global_rate_limit_and_health_exempt(env):
    env.setenv("FG_RATE_LIMIT_PER_MINUTE", "5")
    assert [c.get("/api/v1/config").status_code for _ in range(5)] == [200] * 5
    r = c.get("/api/v1/config"); assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1 and "rate limit" in r.json()["detail"]
    assert c.get("/health").status_code == 200 and c.get("/ready").status_code == 200

def test_write_rate_limit_is_tighter(env):
    env.setenv("FG_RATE_LIMIT_WRITE_PER_MINUTE", "2")
    codes = [c.patch("/api/v1/config", json={"high": 0.6}, headers=ADMIN).status_code for _ in range(3)]
    assert codes == [200, 200, 429] and c.get("/api/v1/config").status_code == 200

def test_failed_auth_throttle_blocks_even_valid_key(env):
    env.setenv("FG_AUTH_FAIL_LIMIT", "3")
    assert [c.patch("/api/v1/config", json={}, headers={"X-API-Key": "bad"}).status_code for _ in range(3)] == [401] * 3
    r = c.patch("/api/v1/config", json={}, headers=ADMIN); assert r.status_code == 429 and r.headers["Retry-After"] == "60"

def test_proxy_header_only_trusted_when_enabled(env):
    env.setenv("FG_RATE_LIMIT_PER_MINUTE", "2")
    h = lambda ip: {"X-Forwarded-For": ip}
    assert [c.get("/api/v1/config", headers=h(f"1.1.1.{i}")).status_code for i in range(3)] == [200, 200, 429]   # untrusted: spoofing doesn't help
    from app.core.ratelimit import limiter; limiter.reset(); env.setenv("FG_TRUST_PROXY", "true")
    assert [c.get("/api/v1/config", headers=h(f"2.2.2.{i}")).status_code for i in range(3)] == [200] * 3          # trusted: separate clients
