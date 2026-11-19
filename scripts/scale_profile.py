"""Time + peak-RSS profile of pipeline stages on a synthetic dataset of a given size (one process per size).
Usage (from repo root): python3 scripts/scale_profile.py <n_accounts> [--tune]"""
import json, os, resource, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import numpy as np, pandas as pd
from app.data.synthetic import generate
from app.pipelines.ingest import ingest_ieee
from app.algorithms.atfrp import ATFRPParams, ATFRPEngine
from app.ml.experiment import _events, atfrp_scores, chrono_split, tune_lam
from app.services.state import State

def rss_mb(): return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)   # peak so far (Linux: KiB)
n = int(sys.argv[1]); out = dict(n_accounts=n); T = time.perf_counter
def stage(name, fn):
    t = T(); r = fn(); out[name] = dict(seconds=round(T() - t, 2), peak_rss_mb=rss_mb()); return r
df = stage("generate", lambda: generate(42, n_accounts=n)); out["rows"] = len(df)
d = tempfile.mkdtemp()
tx = pd.DataFrame({"TransactionID": np.arange(len(df)) + 1_000_000, "TransactionDT": df.t, "TransactionAmt": df.amount, "card1": pd.factorize(df.account)[0], "card2": 1.0, "card4": "v", "addr1": 2.0, "isFraud": df.isFraud})
tx.to_csv(f"{d}/t.csv", index=False); pd.DataFrame({"TransactionID": tx.TransactionID, "DeviceInfo": df.device}).to_csv(f"{d}/i.csv", index=False)
stage("ingest_csv", lambda: ingest_ieee(f"{d}/t.csv", f"{d}/i.csv"))
evs = stage("build_events", lambda: _events(df)); y = df.isFraud.to_numpy(); tr, va, _ = chrono_split(df)
stage("one_replay", lambda: ATFRPEngine(ATFRPParams()).replay(evs))
stage("fit_atfrp_scores", lambda: atfrp_scores(df, y, tr))
if "--tune" in sys.argv: stage("tune_lam_4_taus", lambda: tune_lam(df, y, tr, va))
s = State(); stage("state_load_df_no_tune", lambda: s.load_df(df, "scale-test", 0, dataset_id="scale"))
out["clusters_found"] = len(s.clusters)
print(json.dumps(out))
