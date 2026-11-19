import time, pytest
from fastapi.testclient import TestClient
from app import db
from app.main import app

c = TestClient(app); H = {"X-API-Key": "k"}

@pytest.fixture(autouse=True)
def iso(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_DATABASE_URL", f"sqlite:///{tmp_path}/e.db"); monkeypatch.setenv("FG_ARTIFACT_DIR", str(tmp_path)); monkeypatch.setenv("FG_API_KEY", "k")

def test_auth_and_validation():
    assert c.post("/api/v1/experiments", json={}).status_code == 401
    assert c.post("/api/v1/experiments", json={"scenario": "bogus"}, headers=H).status_code == 422
    assert c.post("/api/v1/experiments", json={"seed": -1}, headers=H).status_code == 422

def test_only_one_active_experiment():
    db.create_experiment("busy", "base", 1); db.update_experiment("busy", status="running")
    assert c.post("/api/v1/experiments", json={}, headers=H).status_code == 409

def test_failed_run_is_recorded(monkeypatch):
    def boom(**kw): raise RuntimeError("no data")
    monkeypatch.setattr("app.ml.experiment.run_experiment", boom)
    r = c.post("/api/v1/experiments", json={"seed": 1}, headers=H); assert r.status_code == 202
    e = c.get(f"/api/v1/experiments/{r.json()['id']}").json(); assert e["status"] == "failed" and "no data" in e["error"]
    assert c.get(f"/api/v1/experiments/{e['id']}/metrics").status_code == 409

def test_run_to_completion_and_history():
    r = c.post("/api/v1/experiments", json={"scenario": "base", "seed": 3}, headers=H); eid = r.json()["id"]
    for _ in range(150):
        e = c.get(f"/api/v1/experiments/{eid}").json()
        if e["status"] in ("done", "failed"): break
        time.sleep(1)
    assert e["status"] == "done", e
    m = c.get(f"/api/v1/experiments/{eid}/metrics").json()
    assert "FULL_fraudgraph_atfrp" in m["models"] and m["decay_tuning"]["table"] and m["seed"] == 3
    assert c.get("/api/v1/experiments/latest/metrics").json()["seed"] == 3
    assert [x["id"] for x in c.get("/api/v1/experiments").json()["items"]] == [eid]
    assert c.get("/api/v1/experiments/nope/metrics").status_code == 404
    assert (__import__("pathlib").Path(__import__("os").environ["FG_ARTIFACT_DIR"]) / "experiments/runs" / eid).exists()
