import numpy as np
from app.data.synthetic import generate
from app.ml.experiment import atfrp_scores, chrono_split, tune_lam, _events
from app.algorithms.atfrp import ATFRPParams, ATFRPEngine
from app.clustering.clusters import detect_clusters
from app.clustering.timeline import cluster_timeline, lineage
from app.core.settings import get_settings
from app.services.state import State

def _reference(df, params, g):
    ref = {s.tx_id: s for s in ATFRPEngine(params).replay(_events(df))}
    eng, snaps = cluster_timeline(_events(df), params, 0.6, 3, g.cluster_checkpoints); final = detect_clusters(eng, 0.6, 3); lin = lineage(final, snaps, 3)
    return ref, {c["cluster_id"]: (c["members"], lin[c["cluster_id"]]["detected_at"], lin[c["cluster_id"]]["growth"]) for c in final}

def _check(s, df, params):
    ref, clusters = _reference(df, params, get_settings())
    assert {k: v.risk for k, v in s.scores.items()} == {k: v.risk for k, v in ref.items()} and s.params == params
    assert {c["cluster_id"]: (c["members"], c["detected_at"], c["growth"]) for c in s.clusters} == clusters and clusters

def test_state_load_matches_independent_reference():
    df = generate(5, n_accounts=80); y = df.isFraud.to_numpy(); tr, _, _ = chrono_split(df)
    params = ATFRPParams(**atfrp_scores(df, y, tr)[1]); s = State(); s.load_df(df, "t", dataset_id="t"); _check(s, df, params)

def test_state_load_with_tuning_matches_reference_and_reuses_best_fit():
    df = generate(5, n_accounts=80); y = df.isFraud.to_numpy(); tr, va, _ = chrono_split(df)
    lam, table, prm = tune_lam(df, y, tr, va, return_params=True)
    assert lam == tune_lam(df, y, tr, va)[0] and prm["lam"] == lam
    s = State(); s.load_df(df, "t", tune=True, dataset_id="t2"); _check(s, df, ATFRPParams(**prm))
    assert [s.scores[i].risk for i in df.tx_id] == list(atfrp_scores(df, y, tr, lam=lam)[0])

def test_params_skip_refit_and_engine_returned():
    df = generate(5, n_accounts=60); y = df.isFraud.to_numpy(); tr, _, _ = chrono_split(df)
    r, p = atfrp_scores(df, y, tr); r2, p2, eng, sc = atfrp_scores(df, y, tr, params=p, return_engine=True)
    assert np.array_equal(r, r2) and p == p2 and len(sc) == len(df) and eng.risk

def test_config_change_still_recomputes_clusters_by_replay():
    s = State(); s.load_df(generate(5, n_accounts=80), "t", dataset_id="t3"); n = len(s.clusters); assert n
    s.cfg["cluster_min_size"] = 7; s.refresh(); assert len(s.clusters) < n
