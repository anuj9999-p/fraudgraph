"""Chronological experiment: baselines A/B/C, ATFRP full, ablations D/E. Measured metrics only."""
import argparse, json, time, numpy as np, pandas as pd
from dataclasses import replace, asdict
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (precision_recall_curve, roc_curve, roc_auc_score, average_precision_score,
                             precision_score, recall_score, f1_score, confusion_matrix)
from app.algorithms.atfrp import ATFRPParams, ATFRPEngine, Event
from app.data.synthetic import generate
from app.core.settings import get_settings, atfrp_defaults

def chrono_split(df, tr=None, va=None):
    g = get_settings(); tr = g.train_frac if tr is None else tr; va = g.val_frac if va is None else va
    n = len(df); a, b = int(n * tr), int(n * (tr + va))
    return np.arange(a), np.arange(a, b), np.arange(b, n)   # df must be time-sorted

def history_features(df):
    """Every feature uses strictly earlier events only. No label access."""
    g = df.groupby("account"); cnt = g.cumcount()
    prior_sum = g["amount"].cumsum() - df["amount"]
    pm = (prior_sum / cnt.replace(0, np.nan)).fillna(df["amount"])
    gap = (df["t"] - g["t"].shift(1)).fillna(1e7)
    f = pd.DataFrame({"log_amt": np.log1p(df["amount"]), "log_ratio": np.log(df["amount"] / pm),
                      "log_cnt": np.log1p(cnt), "log_gap": np.log1p(gap)})
    for col in ("device", "email"):
        seen, vals = {}, []
        for a, k in zip(df["account"], df[col]):
            s = seen.setdefault(k, set()); vals.append(len(s - {a})); s.add(a)
        f[f"shared_{col}"] = vals
    return f

def best_threshold(y, s):
    if y.sum() == 0: return 0.5
    p, r, th = precision_recall_curve(y, s); f1 = 2 * p[:-1] * r[:-1] / np.maximum(p[:-1] + r[:-1], 1e-12)
    return float(th[int(np.argmax(f1))])

def metrics(y, s, thr):
    pred = (s >= thr).astype(int); tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    ok = len(set(y)) == 2
    return dict(threshold=thr, precision=precision_score(y, pred, zero_division=0), recall=recall_score(y, pred),
                f1=f1_score(y, pred), fpr=fp / max(fp + tn, 1), roc_auc=roc_auc_score(y, s) if ok else None,
                pr_auc=average_precision_score(y, s) if ok else None, tp=int(tp), fp=int(fp), fn=int(fn), tn=int(tn))

def _down(a, b, n=100):
    idx = np.unique(np.linspace(0, len(a) - 1, min(n, len(a))).astype(int))
    return [round(float(a[i]), 5) for i in idx], [round(float(b[i]), 5) for i in idx]

def curves(y, s):
    """ROC and PR curve points (<=100 each) from real predictions; None when a class is absent."""
    if len(set(y)) < 2: return None
    f, t, _ = roc_curve(y, s); p, r, _ = precision_recall_curve(y, s)
    fx, ty = _down(f, t); rx, py = _down(r[::-1], p[::-1])
    return dict(roc=dict(fpr=fx, tpr=ty), pr=dict(recall=rx, precision=py))

def _events(df):
    ok = lambda v: isinstance(v, str) and v != ""
    return [Event(r.tx_id, r.t, r.account, r.amount, tuple((k, v) for k, v in (("device", r.device), ("email", r.email)) if ok(v)))
            for r in df.itertuples()]   # label deliberately not passed

def atfrp_scores(df, y, tr_idx, use_rec=True, use_nbr=True, n_iter=3, C=0.1, use_decay=True, use_T=True, lam=None,
                 params=None, on_batch=None, return_engine=False):
    """Fit weights on TRAIN rows only, iterating fit->replay so the weights match the propagation dynamics they are applied under,
    then run the final scoring replay. `params` skips fitting (reuse a previous fit). `on_batch` is attached to the FINAL replay only
    (e.g. a cluster Checkpointer); return_engine=True also returns that replay's engine and {tx_id: Score}. Events are built once."""
    evs = _events(df)
    p = ATFRPParams(**{**atfrp_defaults(), **({} if lam is None else {"lam": lam})}, use_recency=use_rec, use_neighborhood=use_nbr, use_decay=use_decay, use_T=use_T)
    cols = [0] + ([1, 2] if use_nbr else []) + ([3] if use_rec and use_T else [])
    def run(p, hook=None):
        eng = ATFRPEngine(p); sc = {s.tx_id: s for s in eng.replay(evs, on_batch=hook)}
        return np.array([[sc[i].B, sc[i].N, sc[i].C, sc[i].T, sc[i].risk] for i in df["tx_id"]]), eng, sc
    if params is not None: p = ATFRPParams(**params)
    else:
        for _ in range(n_iter):
            X = run(p)[0][:, :4]
            lr = LogisticRegression(C=C, class_weight="balanced", random_state=0, max_iter=1000).fit(X[tr_idx][:, cols], y[tr_idx])
            w = np.zeros(4); w[cols] = lr.coef_[0]
            p = replace(p, wB=w[0], wN=w[1], wC=w[2], wT=w[3], bias=float(lr.intercept_[0]))
    arr, eng, sc = run(p, on_batch)
    return (arr[:, 4], asdict(p), eng, sc) if return_engine else (arr[:, 4], asdict(p))

def bootstrap_win_rates(y, scores_by_tau, groups, base_tau, B, seed=0):
    """Paired cluster bootstrap over validation ACCOUNTS: fraction of resamples where each tau's PR-AUC beats base_tau's. Deterministic."""
    rng = np.random.default_rng(seed); accts = np.unique(groups); idx = {a: np.where(groups == a)[0] for a in accts}
    wins = {t: 0 for t in scores_by_tau if t != base_tau}; valid = 0
    for _ in range(B):
        rows = np.concatenate([idx[accts[i]] for i in rng.integers(0, len(accts), len(accts))]); yy = y[rows]
        if yy.sum() == 0 or yy.sum() == len(yy): continue
        valid += 1; ref = average_precision_score(yy, scores_by_tau[base_tau][rows])
        for t in wins: wins[t] += average_precision_score(yy, scores_by_tau[t][rows]) > ref
    return {t: (w / valid if valid else 0.0) for t, w in wins.items()}

def select_tau(table, win_rates, default_tau, confidence, rule):
    """argmax: best validation PR-AUC. conservative: keep default_tau unless another tau beats it in >= `confidence` of bootstrap resamples
    (then the best-PR-AUC such tau). Ties -> smaller tau."""
    key = lambda r: (r["val_pr_auc"], -r["tau_days"])
    if rule == "argmax": return max(table, key=key)["tau_days"]
    ok = [r for r in table if r["tau_days"] != default_tau and win_rates.get(r["tau_days"], 0.0) >= confidence]
    return max(ok, key=key)["tau_days"] if ok else default_tau

def tune_lam(df, y, tr_idx, va_idx, taus_days=None, return_params=False, rule=None):
    """Select the decay time constant tau on the VALIDATION period only. Rule (FG_TUNE_RULE): 'conservative' (default; keeps the default tau
    unless clearly better) or 'argmax'. Test-period labels are never passed in. Returns (lam_per_second, table) [+ winning fitted params]."""
    g = get_settings(); rule = rule or g.tune_rule; taus_days = list(taus_days or g.tune_taus_days)
    default_lam = atfrp_defaults().get("lam", 1 / 86400.0); default_tau = round(1 / (default_lam * 86400.0), 6)
    if default_tau not in taus_days: taus_days.append(default_tau)
    if len(set(y[va_idx])) < 2:
        r = (default_lam, [dict(note="validation lacks both classes; default tau kept")]); return (*r, None) if return_params else r
    table, fits, vs = [], {}, {}
    for d in taus_days:
        sc, prm = atfrp_scores(df, y, tr_idx, lam=1 / (d * 86400.0)); fits[d] = prm; vs[d] = sc[va_idx]
        table.append(dict(tau_days=d, val_pr_auc=float(average_precision_score(y[va_idx], sc[va_idx]))))
    wr = bootstrap_win_rates(y[va_idx], vs, df["account"].to_numpy()[va_idx], default_tau, g.tune_bootstrap) if rule == "conservative" else {}
    for r in table: r["win_rate_vs_default"] = None if r["tau_days"] == default_tau or rule != "conservative" else round(wr[r["tau_days"]], 3)
    best = select_tau(table, wr, default_tau, g.tune_confidence, rule)
    r = (1 / (best * 86400.0), table); return (*r, fits[best]) if return_params else r

def run_experiment(df=None, seed=None, out_dir=None, scenario="base", progress=None):
    seed = get_settings().seed if seed is None else seed; df = generate(seed, scenario=scenario) if df is None else df; y = df["isFraud"].to_numpy()
    tr, va, te = chrono_split(df); F = history_features(df); res = {}; params = {}
    _p = progress or (lambda st: None); _p("tuning decay rate")
    lam_sel, tuning = tune_lam(df, y, tr, va)
    sets = {"A_logreg": ["log_amt", "log_ratio", "log_cnt"], "A_hgb": ["log_amt", "log_ratio", "log_cnt"],
            "B_static_graph": ["log_amt", "shared_device", "shared_email"],
            "C_temporal_behavioral": ["log_ratio", "log_cnt", "log_gap"]}
    scores = {}
    _p("training baselines")
    for name, cols in sets.items():
        sc = StandardScaler().fit(F.iloc[tr][cols])                    # fitted on train only
        X = sc.transform(F[cols])
        m = (HistGradientBoostingClassifier(random_state=seed) if "hgb" in name
             else LogisticRegression(class_weight="balanced", max_iter=1000, random_state=seed))
        m.fit(X[tr], y[tr]); scores[name] = m.predict_proba(X)[:, 1]
    _p("fitting ATFRP variants")
    for name, kw in {"D_atfrp_no_recency": dict(use_rec=False), "D1_atfrp_no_decay_only": dict(use_decay=False), "D2_atfrp_no_T_only": dict(use_T=False),
                     "E_atfrp_no_neighborhood": dict(use_nbr=False),
                     "FULL_fraudgraph_atfrp": {}}.items():
        scores[name], params[name] = atfrp_scores(df, y, tr, lam=lam_sel, **kw)
    _p("evaluating")
    for name, s in scores.items():
        thr = best_threshold(y[va], s[va])                              # validation only
        res[name] = dict(validation=metrics(y[va], s[va], thr), test=metrics(y[te], s[te], thr), curves=curves(y[te], s[te]))
    out = dict(dataset="SYNTHETIC demo, scenario=" + scenario + " (not an IEEE-CIS benchmark)", seed=seed, n=len(df),
               split=dict(train=len(tr), val=len(va), test=len(te), test_fraud=int(y[te].sum())),
               threshold_selection="max F1 on validation", latency="Not evaluated",
               atfrp_params=params, models=res,
               decay_tuning=dict(criterion="validation PR-AUC", rule=get_settings().tune_rule, selected_tau_days=round(1 / (lam_sel * 86400), 4), table=tuning))
    if out_dir:
        d = Path(out_dir) / (f"synthetic_seed{seed}" if scenario == "base" else f"synthetic_{scenario}_seed{seed}"); d.mkdir(parents=True, exist_ok=True)
        (d / "metrics.json").write_text(json.dumps(out, indent=2, default=float))
        rows = "\n".join(f"| {k} | {v['test']['precision']:.3f} | {v['test']['recall']:.3f} | {v['test']['f1']:.3f} | "
                         f"{v['test']['fpr']:.4f} | {v['test']['roc_auc']:.3f} | {v['test']['pr_auc']:.3f} |" for k, v in res.items())
        (d / "report.md").write_text(f"# Evaluation (SYNTHETIC data, test period)\n\n{out['split']}\n\n"
            f"| model | precision | recall | F1 | FPR | ROC-AUC | PR-AUC |\n|---|---|---|---|---|---|---|\n{rows}\n")
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=None); ap.add_argument("--scenario", default="base", choices=["base", "decay", "decay_hard"])
    a = ap.parse_args(); t = time.time()
    o = run_experiment(seed=a.seed, scenario=a.scenario, out_dir=get_settings().artifact_dir / "experiments")
    print(json.dumps(o["split"]), f"{time.time()-t:.1f}s")
    for k, v in o["models"].items(): print(f"{k:26s}", {m: round(x, 3) for m, x in v["test"].items() if m in ("precision", "recall", "f1", "fpr", "roc_auc", "pr_auc")})
