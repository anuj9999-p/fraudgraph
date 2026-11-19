import numpy as np
from app.data.synthetic import generate
from app.ml.experiment import _events, atfrp_scores, chrono_split
from app.algorithms.atfrp import ATFRPParams, ATFRPEngine
from app.clustering.clusters import detect_clusters
from app.clustering.timeline import cluster_timeline, lineage

def _setup():
    df = generate(5, n_accounts=80); y = df.isFraud.to_numpy(); tr, _, _ = chrono_split(df)
    _, p = atfrp_scores(df, y, tr); return df, ATFRPParams(**p)

def test_snapshot_equals_replay_of_prefix_only():
    df, p = _setup(); evs = _events(df); _, snaps = cluster_timeline(evs, p, 0.6, 3, 12)
    assert snaps and snaps[-1][0] == df.t.max()
    for t, cl in snaps[2:8:2]:
        eng = ATFRPEngine(p); eng.replay([e for e in evs if e.t <= t])          # no events after t
        assert {tuple(c["members"]) for c in detect_clusters(eng, 0.6, 3)} == {tuple(c["members"]) for c in cl}

def test_lineage_detection_not_after_final_and_growth_monotone():
    df, p = _setup(); evs = _events(df); eng, snaps = cluster_timeline(evs, p, 0.6, 3, 20)
    final = detect_clusters(eng, 0.6, 3); lin = lineage(final, snaps, 3); assert final
    end = df.t.max(); first_seen = df.groupby("account").t.min()
    for c in final:
        L = lin[c["cluster_id"]]; assert L["detected_at"] is not None and L["detected_at"] <= end
        assert L["detected_at"] >= min(first_seen[a] for a in c["members"])
        sizes = [g["size"] for g in L["growth"]]; assert sizes == sorted(sizes) and sizes[-1] == c["size"]
    assert min(lin[c["cluster_id"]]["detected_at"] for c in final) < 0.6 * end      # early ring found before the end of the data
