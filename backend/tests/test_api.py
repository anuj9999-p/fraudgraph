import pytest
from fastapi.testclient import TestClient
from app.main import app, S
c = TestClient(app); H = {"X-API-Key": "k"}

@pytest.fixture(scope="module", autouse=True)
def loaded():
    import os; os.environ["FG_API_KEY"] = "k"; assert c.post("/api/v1/demo/load").status_code == 200

def test_no_data_error():
    from app.services.state import State
    import app.main as m; old = m.S; m.S = State()
    try: assert c.get("/api/v1/transactions").status_code == 409
    finally: m.S = old

def test_labels_never_exposed():
    r = c.get("/api/v1/transactions?page_size=5").json()
    assert "isFraud" not in str(r) and "kind" not in r["items"][0]
    t = c.get("/api/v1/transactions/" + r["items"][0]["tx_id"]).json()
    assert "isFraud" not in str(t) and t["explanation"]["summary"]

def test_filter_sort_paginate():
    r = c.get("/api/v1/transactions?category=high&sort=-risk&page_size=10").json()
    assert all(i["category"] == "high" for i in r["items"]) and len(r["items"]) <= 10
    assert c.get("/api/v1/transactions?sort=bogus").status_code == 422
    assert c.get("/api/v1/transactions/nope").status_code == 404

def test_clusters_found_with_evidence():
    cl = c.get("/api/v1/graph/clusters").json()["items"]
    assert cl and all(x["size"] >= 3 and x["shared_identifiers"] and "not confirmed" in x["explanation"] for x in cl)

def test_neighbors_graph():
    m = c.get("/api/v1/graph/clusters").json()["items"][0]["members"][0]
    g = c.get(f"/api/v1/graph/entities/{m}/neighbors").json()
    assert g["nodes"] and g["edges"] and g["cluster"]

def test_alert_update_requires_auth_and_persists():
    a = c.get("/api/v1/alerts").json()["items"][0]["alert_id"]
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "escalated"}).status_code == 401
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "bogus"}, headers=H).status_code == 422
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "escalated", "note": "x"}, headers=H).status_code == 200
    assert c.get("/api/v1/alerts?status=escalated").json()["total"] >= 1

def test_config_validation():
    assert c.patch("/api/v1/config", json={"high": 0.1}, headers=H).status_code == 422
    assert c.patch("/api/v1/config", json={"nope": 1}, headers=H).status_code == 422
    assert c.patch("/api/v1/config", json={"high": 0.7}, headers=H).json()["high"] == 0.7
    c.patch("/api/v1/config", json={"high": 0.6}, headers=H)

def test_metrics_endpoint():
    assert c.get("/api/v1/experiments/latest/metrics").status_code in (200, 404)

def test_cases_and_audit_persist_across_reload():
    from app import db
    a = c.get("/api/v1/alerts").json()["items"][1]["alert_id"]
    assert c.patch(f"/api/v1/alerts/{a}", json={"status": "dismissed", "note": "n1"}, headers=H).status_code == 200
    assert c.post("/api/v1/demo/load").status_code == 200            # reload resets in-memory state
    assert any(i["alert_id"] == a for i in c.get("/api/v1/alerts?status=dismissed").json()["items"])
    with db.session() as s: assert s.query(db.Audit).filter_by(action="alert_update").count() >= 1

def test_alert_export_csv_json_safe_and_label_free():
    r = c.get("/api/v1/exports/alerts?format=csv"); assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"] and r.text.splitlines()[0].startswith("alert_id,status") and "isFraud" not in r.text
    j = c.get("/api/v1/exports/alerts?format=json").json(); assert j["items"] and "isFraud" not in str(j)
    assert c.get("/api/v1/exports/alerts?format=xml").status_code == 422

def test_csv_formula_injection_neutralised():
    from app.main import _cell, _csv
    assert _cell("=HYPERLINK(1)") == "'=HYPERLINK(1)" and _cell("+1") == "'+1" and _cell(5) == 5 and _cell("acct_1") == "acct_1"
    assert "'=cmd" in _csv([dict(a="=cmd")], ["a"])

def test_evaluation_export(tmp_path, monkeypatch):
    import json, os
    d = tmp_path / "experiments/synthetic_seed42"; d.mkdir(parents=True)
    m = dict(dataset="x", models={"FULL": dict(test=dict(precision=.9, recall=.8, f1=.85, fpr=.01, roc_auc=.99, pr_auc=.95, threshold=.5, tp=8, fp=1, fn=2, tn=90))})
    (d / "metrics.json").write_text(json.dumps(m)); monkeypatch.setenv("FG_ARTIFACT_DIR", str(tmp_path))
    r = c.get("/api/v1/exports/evaluation"); assert r.status_code == 200 and "FULL,0.9,0.8" in r.text
    assert c.get("/api/v1/exports/evaluation?format=json").json()["dataset"] == "x"
    monkeypatch.setenv("FG_ARTIFACT_DIR", str(tmp_path / "none")); assert c.get("/api/v1/exports/evaluation").status_code == 404

def test_clusters_have_time_sliced_detection_and_growth():
    cl = c.get("/api/v1/graph/clusters").json()["items"]
    assert all(x["detected_at"] is not None and x["growth"] and x["detection_basis"].startswith("time-sliced") for x in cl)
    assert len({round(x["detected_at"]) for x in cl}) > 1                 # rings are detected at different times

def test_risk_history_and_trends():
    acct = c.get("/api/v1/graph/clusters").json()["items"][0]["members"][0]
    h = c.get(f"/api/v1/entities/{acct}/risk-history").json(); ts = [i["t"] for i in h["items"]]
    assert ts == sorted(ts) and all(0 <= i["risk"] <= 1 for i in h["items"]) and h["total"] >= len(h["items"])
    assert c.get("/api/v1/entities/nope/risk-history").status_code == 404
    tr = c.get("/api/v1/stats/trends?buckets=10").json(); assert len(tr["buckets"]) == 10
    assert sum(b["transactions"] for b in tr["buckets"]) == c.get("/api/v1/system/status").json()["transactions"]
    assert tr["cluster_timeline"] and tr["cluster_timeline"][-1]["clusters"] >= 1
    assert c.get("/api/v1/stats/trends?buckets=1").status_code == 422

def test_dataset_listing_detail_quality_and_unknown():
    d = c.get("/api/v1/datasets").json()["items"]; demo = next(x for x in d if x["id"] == "demo:42")
    assert demo["active"] and demo["source"] == "SYNTHETIC demo data" and demo["rows"] == c.get("/api/v1/system/status").json()["transactions"]
    q = c.get("/api/v1/datasets/demo:42/quality").json(); assert q["has_labels"] and q["fraud_rows"] > 0 and q["accounts"] > 0 and q["rows_kept"] == demo["rows"]
    assert c.get("/api/v1/datasets/demo:42").json()["data_in_memory"] is True
    assert c.get("/api/v1/datasets/nope").status_code == 404 and c.get("/api/v1/datasets/nope/quality").status_code == 404
    assert c.get("/api/v1/system/status").json()["latest_event_t"] > 0
