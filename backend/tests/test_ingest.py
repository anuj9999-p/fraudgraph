import io, time, os, pandas as pd, numpy as np
from fastapi.testclient import TestClient
from app.data.synthetic import generate
from app.pipelines.ingest import ingest_ieee
from app.algorithms.atfrp import ATFRPParams, ATFRPEngine, Event

def ieee_files(tmp_path, dup=True):
    d = generate(7); codes = pd.factorize(d.account)[0]
    tx = pd.DataFrame({"TransactionID": np.arange(1000, 1000 + len(d)), "TransactionDT": d.t, "TransactionAmt": d.amount,
                       "card1": codes, "card2": 111.0, "card4": "visa", "addr1": 300.0, "isFraud": d.isFraud})
    ident = pd.DataFrame({"TransactionID": tx.TransactionID, "DeviceInfo": d.device}).iloc[::2]   # half unmatched
    if dup: tx = pd.concat([tx, tx.iloc[:5]])
    tp, ip = tmp_path / "t.csv", tmp_path / "i.csv"; tx.to_csv(tp, index=False); ident.to_csv(ip, index=False); return tp, ip

def test_ingest_join_dedupe_unmatched(tmp_path):
    tp, ip = ieee_files(tmp_path); df, q = ingest_ieee(tp, ip)
    assert q["duplicate_ids_dropped"] == 5 and q["unmatched_kept"] > 0 and q["rows_kept"] == q["rows_read"] - 5
    assert df.t.is_monotonic_increasing and df.device.isna().any() and q["has_labels"] and q["fraud_rows"] > 0
    assert df.account.str.startswith("acct_").all()

def test_ingest_validation(tmp_path):
    p = tmp_path / "bad.csv"; pd.DataFrame({"TransactionID": [1], "TransactionDT": [1]}).to_csv(p, index=False)
    try: ingest_ieee(p); assert False
    except ValueError as e: assert "TransactionAmt" in str(e)

def test_hub_suppression_uses_only_past_state():
    p = ATFRPParams(max_fanout=2, lam=0.0)
    ev = [Event(f"t{i}", float(i), f"a{i}", 10.0, (("device", "hub"),)) for i in range(6)]
    e = ATFRPEngine(p); e.replay(ev[:5]); e.risk = {k: 1.0 for k in e.risk}
    s = e.replay([Event("x", 99.0, "z", 10.0, (("device", "hub"),))])[0]
    assert s.N == 0                     # hub (5 accounts > 2) ignored
    e2 = ATFRPEngine(ATFRPParams(max_fanout=50, lam=0.0)); e2.replay(ev[:5]); e2.risk = {k: 1.0 for k in e2.risk}
    assert e2.replay([Event("x", 99.0, "z", 10.0, (("device", "hub"),))])[0].N > 0

def test_upload_job_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_API_KEY", "k"); from app.main import app; c = TestClient(app); tp, ip = ieee_files(tmp_path)
    files = lambda: {"transactions": ("../../evil.csv", open(tp, "rb"), "text/csv"), "identity": ("i.csv", open(ip, "rb"), "text/csv")}
    assert c.post("/api/v1/datasets/upload", files=files()).status_code == 401
    r = c.post("/api/v1/datasets/upload", files=files(), headers={"X-API-Key": "k"}); assert r.status_code == 202
    jid = r.json()["job_id"]
    for _ in range(120):
        j = c.get(f"/api/v1/pipelines/jobs/{jid}").json()
        if j["status"] in ("done", "failed"): break
        time.sleep(1)
    assert j["status"] == "done", j
    assert j["quality"]["unmatched_kept"] > 0
    st = c.get("/api/v1/system/status").json(); assert st["data_source"] == "IEEE-CIS upload" and "fitted" in st["weights"]
    ds = [d for d in c.get("/api/v1/datasets").json()["items"] if d["id"] == f"upload:{jid}"]
    assert ds and ds[0]["active"] and ds[0]["source"] == "IEEE-CIS upload" and ds[0]["quality"]["unmatched_kept"] > 0
    assert c.get(f"/api/v1/datasets/upload:{jid}/quality").json()["rows_kept"] == ds[0]["rows"]
    assert "isFraud" not in str(c.get("/api/v1/transactions?page_size=3").json())
    bad = c.post("/api/v1/datasets/upload", files={"transactions": ("x.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}, headers={"X-API-Key": "k"})
    jb = bad.json()["job_id"]; time.sleep(2); assert c.get(f"/api/v1/pipelines/jobs/{jb}").json()["status"] == "failed"

def test_jobs_list_endpoint():
    from app.main import app
    r = TestClient(app).get("/api/v1/pipelines/jobs"); assert r.status_code == 200 and "items" in r.json()
