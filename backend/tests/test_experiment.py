import numpy as np
from app.data.synthetic import generate
from app.ml.experiment import chrono_split, best_threshold, run_experiment, history_features, _events
import dataclasses

def test_synthetic_deterministic():
    assert generate(1).equals(generate(1)) and not generate(1).equals(generate(2))

def test_chronological_split_no_overlap():
    df = generate(3); tr, va, te = chrono_split(df)
    assert df.t.iloc[tr].max() <= df.t.iloc[va].min() and df.t.iloc[va].max() <= df.t.iloc[te].min()

def test_events_have_no_label():
    e = _events(generate(3).head(5)); assert not any(hasattr(x, "isFraud") for x in e)

def test_history_features_ignore_future():
    df = generate(3); full = history_features(df); part = history_features(df.iloc[:500].reset_index(drop=True))
    assert np.allclose(full.iloc[:500].to_numpy(), part.to_numpy())

def test_threshold_from_validation_only():
    df = generate(3); res = run_experiment(df)
    _, va, te = chrono_split(df); assert res["split"]["test_fraud"] == int(df.isFraud.iloc[te].sum())
    assert res["models"]["FULL_fraudgraph_atfrp"]["test"]["threshold"] == res["models"]["FULL_fraudgraph_atfrp"]["validation"]["threshold"]
    assert set(res["models"]) >= {"A_logreg", "A_hgb", "B_static_graph", "C_temporal_behavioral",
                                  "D_atfrp_no_recency", "E_atfrp_no_neighborhood", "FULL_fraudgraph_atfrp"}

def test_decay_scenario_has_fresh_and_stale_groups_and_base_unchanged():
    d = generate(5, scenario="decay"); assert set(d.kind) >= {"decay_fresh", "decay_stale"}
    assert d[d.kind == "decay_fresh"].isFraud.eq(1).all() and d[d.kind == "decay_stale"].isFraud.eq(0).all()
    assert generate(5).equals(generate(5, scenario="base")) and not (generate(5).kind.str.startswith("decay")).any()

def test_tune_lam_ignores_test_labels_and_is_deterministic():
    from app.ml.experiment import tune_lam
    df = generate(11, n_accounts=60, scenario="decay_hard"); y = df.isFraud.to_numpy(); tr, va, te = chrono_split(df)
    a, ta = tune_lam(df, y, tr, va, taus_days=(0.25, 1, 4))
    y2 = y.copy(); y2[te] = 1 - y2[te]                       # corrupt TEST labels only
    b, tb = tune_lam(df, y2, tr, va, taus_days=(0.25, 1, 4))
    assert a == b and ta == tb and a > 0
    assert tune_lam(df, y, tr, va, taus_days=(0.25, 1, 4))[0] == a

def test_curves_are_real_and_well_formed():
    from app.ml.experiment import curves
    y = np.array([0, 0, 1, 1, 0, 1]); s = np.array([.1, .4, .35, .8, .2, .9]); c = curves(y, s)
    assert c["roc"]["fpr"][0] == 0 and c["roc"]["fpr"][-1] == 1 and c["roc"]["tpr"][-1] == 1
    assert c["roc"]["fpr"] == sorted(c["roc"]["fpr"]) and c["pr"]["recall"] == sorted(c["pr"]["recall"])
    assert curves(np.zeros(5), np.arange(5.0)) is None

def test_select_tau_rules_and_bootstrap_are_sane():
    from app.ml.experiment import select_tau, bootstrap_win_rates
    tbl = [dict(tau_days=0.25, val_pr_auc=0.90), dict(tau_days=1, val_pr_auc=0.88), dict(tau_days=4, val_pr_auc=0.80)]
    assert select_tau(tbl, {0.25: 0.7, 4: 0.1}, 1, 0.95, "argmax") == 0.25                 # argmax follows raw validation score
    assert select_tau(tbl, {0.25: 0.7, 4: 0.1}, 1, 0.95, "conservative") == 1              # not clearly better -> keep default
    assert select_tau(tbl, {0.25: 0.99, 4: 0.1}, 1, 0.95, "conservative") == 0.25          # clearly better -> switch
    rng = np.random.default_rng(0); n = 600; y = (rng.random(n) < 0.1).astype(int); g = np.arange(n) // 3
    good = y + rng.normal(0, 0.1, n); noisy_a = rng.random(n); noisy_b = rng.random(n)
    wr = bootstrap_win_rates(y, {1: noisy_a, 0.25: good, 4: noisy_b}, g, 1, 100)
    assert wr[0.25] > 0.95 and 0.0 <= wr[4] <= 1.0 and wr == bootstrap_win_rates(y, {1: noisy_a, 0.25: good, 4: noisy_b}, g, 1, 100)

def test_tuning_table_records_rule_and_default_always_considered():
    from app.ml.experiment import tune_lam
    df = generate(11, n_accounts=60, scenario="decay_hard"); y = df.isFraud.to_numpy(); tr, va, _ = chrono_split(df)
    lam, table = tune_lam(df, y, tr, va, taus_days=(0.25, 4)); assert any(r["tau_days"] == 1 for r in table) and lam > 0   # default tau (1 day) added to the grid
    assert all("win_rate_vs_default" in r for r in table) and next(r for r in table if r["tau_days"] == 1)["win_rate_vs_default"] is None
    lam2, table2 = tune_lam(df, y, tr, va, taus_days=(0.25, 4), rule="argmax"); assert lam2 > 0 and table2[0]["win_rate_vs_default"] is None
