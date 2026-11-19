from app.algorithms.atfrp import ATFRPParams, ATFRPEngine
from app.data.synthetic import generate
from app.ml.experiment import atfrp_scores, chrono_split, tune_lam, _events
from app.clustering.clusters import detect_clusters
from app.clustering.timeline import cluster_timeline, lineage, Checkpointer
from app.explainability.explain import explain

from app.core.settings import get_settings, atfrp_defaults
DEFAULT_CFG = dict(medium=0.3, high=0.6, critical=0.9, cluster_risk=0.6, cluster_min_size=3)   # keys/shape; values come from env
def default_cfg():
    g = get_settings(); return {k: getattr(g, k) for k in DEFAULT_CFG}

def quality_for_df(df):
    """Same shape as the ingestion quality report, for datasets that did not come through ingestion (the demo)."""
    q = dict(rows_read=len(df), rows_kept=len(df), accounts=int(df["account"].nunique()), missing_device_pct=round(float(df["device"].isna().mean() * 100), 2) if "device" in df else None,
             has_labels="isFraud" in df.columns)
    if q["has_labels"]: q["fraud_rows"] = int(df["isFraud"].sum()); q["fraud_rate"] = round(float(df["isFraud"].mean()), 5)
    return q

class State:
    def __init__(self):
        self.loaded = False; self.source = None; self.weights = None; self.cfg = default_cfg(); self.dataset_id = None; self.cases = {}; self.audit = []
    def load_demo(self, seed=42):
        self.load_df(generate(seed), "SYNTHETIC demo data", seed, dataset_id=f"demo:{seed}")
    def load_df(self, df, source, seed=0, tune=False, dataset_id=None, quality=None):
        self.dataset_id = dataset_id or f"{source}:{seed}"
        df = df.sort_values(["t", "tx_id"], kind="stable").reset_index(drop=True)
        g = get_settings(); rt, ms = self.cfg["cluster_risk"], self.cfg["cluster_min_size"]
        ck = Checkpointer(float(df["t"].min()), float(df["t"].max()), rt, ms, g.cluster_checkpoints)   # snapshots taken during the one scoring replay
        if "isFraud" in df.columns and df["isFraud"].nunique() == 2:
            y = df["isFraud"].to_numpy(); tr, va, _ = chrono_split(df); fixed = tune_lam(df, y, tr, va, return_params=True)[2] if tune else None   # validation-only selection
            _, p, eng, scores = atfrp_scores(df, y, tr, params=fixed, on_batch=ck.on_batch, return_engine=True)   # labels used ONLY to fit on train rows
            self.params = ATFRPParams(**p); self.weights = "fitted on chronological train period"
        else:
            self.params = ATFRPParams(**atfrp_defaults()); self.weights = "UNFITTED default weights (no labels available)"
            eng = ATFRPEngine(self.params); scores = {s.tx_id: s for s in eng.replay(_events(df), on_batch=ck.on_batch)}
        self.df = df.drop(columns=[c for c in ("isFraud", "kind") if c in df.columns]).set_index("tx_id")  # labels never kept in service state
        self.scores = scores; self.engine = eng
        self.by_account = {}
        for tid, sc in self.scores.items(): self.by_account.setdefault(sc.account, []).append(tid)
        self.quality = quality or quality_for_df(df); self.max_t = float(df["t"].max()); self.source = source; self.seed = seed; self.loaded = True; self.cases = {}; self.refresh(ck.snaps)
    def refresh(self, snaps=None):
        """Final clusters from the end state + time-sliced detection (re-replays events; cost ~ one replay)."""
        g = get_settings(); rt, ms = self.cfg["cluster_risk"], self.cfg["cluster_min_size"]
        if snaps is None: _, snaps = cluster_timeline(_events(self.df.reset_index()), self.params, rt, ms, g.cluster_checkpoints)   # config change: re-replay
        final = detect_clusters(self.engine, rt, ms); lin = lineage(final, snaps, ms)
        for c in final:
            L = lin[c["cluster_id"]]; c["detected_at"] = L["detected_at"] if L["detected_at"] is not None else c["detected_at"]; c["growth"] = L["growth"]
            c["detection_basis"] = "time-sliced (state as of each checkpoint)"
        self.clusters = final; self.cluster_of = {m: c for c in self.clusters for m in c["members"]}
        self.cluster_timeline = [dict(t=t, clusters=len(cl), flagged_accounts=sum(x["size"] for x in cl)) for t, cl in snaps]
    def category(self, r):
        c = self.cfg
        return "critical" if r >= c["critical"] else "high" if r >= c["high"] else "medium" if r >= c["medium"] else "low"
    def tx(self, tid, detail=False):
        s = self.scores[tid]; row = self.df.loc[tid]
        d = dict(tx_id=tid, account=s.account, t=s.t, amount=round(float(row.amount), 2),
                 risk=round(s.risk, 4), category=self.category(s.risk), model="atfrp-v1")
        if detail: d["explanation"] = explain(s, self.params, self.cluster_of.get(s.account))
        return d
