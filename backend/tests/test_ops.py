import numpy as np, pytest
from fastapi.testclient import TestClient
from app import db
from app.main import app, S
from app.algorithms.atfrp import ATFRPEngine, ATFRPParams, Event
from app.data.synthetic import generate
from app.ml.latency import benchmark

c = TestClient(app)

def test_process_matches_replay_and_peek_does_not_mutate():
    evs = [Event(f"t{i}", float(i), f"a{i % 3}", 10.0 + i, (("device", "d1"),)) for i in range(12)]
    ref = [s.risk for s in ATFRPEngine().replay(evs)]; eng = ATFRPEngine(); assert [eng.process(e).risk for e in evs] == ref
    before = (len(eng.amounts), len(eng.ids), dict(eng.risk)); eng.process(Event("x", 99.0, "brand_new", 5.0, (("device", "zz"),)), commit=False)
    assert (len(eng.amounts), len(eng.ids), dict(eng.risk)) == before

def test_ready_and_interrupted_cleanup(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_DATABASE_URL", f"sqlite:///{tmp_path}/o.db")
    r = c.get("/ready"); assert r.status_code == 200 and r.json()["checks"]["database"] is True
    db.create_job("j1"); db.update_job("j1", status="running"); db.create_experiment("e1", "base", 1); db.update_experiment("e1", status="running")
    db.create_experiment("e2", "base", 2); db.update_experiment("e2", status="done")
    assert db.fail_interrupted() == 2
    assert db.get_job("j1")["status"] == "failed" and "restart" in db.get_job("j1")["error"]
    assert db.get_experiment("e1")["status"] == "failed" and db.get_experiment("e2")["status"] == "done"
    monkeypatch.setenv("FG_DATABASE_URL", "sqlite:////nonexistent_dir_xyz/zzz/o.db"); monkeypatch.setattr("pathlib.Path.mkdir", lambda *a, **k: None)
    assert c.get("/ready").status_code == 503

def test_latency_benchmark_shape():
    out = benchmark(generate(2, n_accounts=40), ATFRPParams(), max_timed=150)
    assert out["timed_events"] == 150 and set(out["modes"]) == {"score_only", "score_and_update", "score_update_explain"} and out["hardware"]["python"]
    for m in out["modes"].values(): assert 0 < m["p50_ms"] <= m["p95_ms"] <= m["p99_ms"] <= m["max_ms"]

def test_latency_endpoint_not_evaluated(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_ARTIFACT_DIR", str(tmp_path)); assert c.get("/api/v1/system/latency").status_code == 404

@pytest.fixture
def loaded(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_DATABASE_URL", f"sqlite:///{tmp_path}/s.db"); S.load_demo(42)

def test_score_endpoint_is_read_only_and_validated(loaded):
    acct = S.clusters[0]["members"][0]; t = S.max_t + 60; n_amounts = len(S.engine.amounts); risk = dict(S.engine.risk); n = len(S.scores)
    body = {"account": acct, "amount": 5000, "t": t, "identifiers": [{"type": "device", "value": "ring_dev_2"}]}
    r1 = c.post("/api/v1/transactions/score", json=body); assert r1.status_code == 200 and r1.json()["dry_run"] and 0 <= r1.json()["risk"] <= 1
    assert r1.json() == c.post("/api/v1/transactions/score", json=body).json()                      # repeatable: nothing was applied
    new = c.post("/api/v1/transactions/score", json={"account": "never_seen", "amount": 10, "t": t}).json()
    assert any("Cold start" in w for w in new["explanation"]["warnings"])
    assert len(S.engine.amounts) == n_amounts and S.engine.risk == risk and len(S.scores) == n
    assert c.post("/api/v1/transactions/score", json={**body, "t": 1.0}).status_code == 422          # would peek at the future
    assert c.post("/api/v1/transactions/score", json={**body, "amount": -1}).status_code == 422
    assert c.post("/api/v1/transactions/score", json={**body, "identifiers": [{"type": "d", "value": "x"}] * 11}).status_code == 422
