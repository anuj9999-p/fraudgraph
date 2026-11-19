"""Time-sliced cluster detection. A fresh engine replays events in order; at ~n checkpoints the cluster
detector runs on the state as of that moment (only events with time <= snapshot time). Final clusters get a
first-detection time and a growth history from their lineage (earlier clusters whose members are a subset)."""
from app.algorithms.atfrp import ATFRPEngine
from app.clustering.clusters import detect_clusters

class Checkpointer:
    """Collects cluster snapshots during ANY replay: pass .on_batch to ATFRPEngine.replay (state at snapshot time = events <= t only)."""
    def __init__(self, t0, t1, risk_threshold, min_size, n_checkpoints):
        self.cps = [t0 + (t1 - t0) * k / n_checkpoints for k in range(1, n_checkpoints + 1)]; self.cps[-1] = t1
        self.rt, self.ms, self.i, self.snaps = risk_threshold, min_size, 0, []
    def on_batch(self, t, eng):
        if self.i < len(self.cps) and t >= self.cps[self.i]:
            self.snaps.append((t, detect_clusters(eng, self.rt, self.ms)))
            while self.i < len(self.cps) and t >= self.cps[self.i]: self.i += 1

def cluster_timeline(events, params, risk_threshold, min_size, n_checkpoints):
    evs = sorted(events, key=lambda e: (e.t, e.tx_id))
    if not evs: return ATFRPEngine(params), []
    ck = Checkpointer(evs[0].t, evs[-1].t, risk_threshold, min_size, n_checkpoints)
    eng = ATFRPEngine(params); eng.replay(evs, on_batch=ck.on_batch)
    return eng, ck.snaps

def lineage(final_clusters, snaps, min_size):
    out = {}
    for c in final_clusters:
        fm, detected, growth = set(c["members"]), None, []
        for t, cl in snaps:
            best = max((len(sc["members"]) for sc in cl if set(sc["members"]) <= fm), default=0)
            if best >= min_size and detected is None: detected = t
            if best and (not growth or growth[-1][1] != best): growth.append((t, best))
        out[c["cluster_id"]] = dict(detected_at=detected, growth=[dict(t=t, size=n) for t, n in growth])
    return out
