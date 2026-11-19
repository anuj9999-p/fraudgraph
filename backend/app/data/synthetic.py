"""Deterministic SYNTHETIC demo data (never an IEEE-CIS benchmark). Rules:
 - 250 normal accounts, ~Poisson(40) lognormal-amount txns over 30 days; ~10% share a 'family' device.
 - 15 takeover accounts: 1-3 amounts 10-30x their norm after day 5 (isFraud=1).
 - 3 rings x 6 new accounts sharing one device; a few small normal txns, then a burst of
   large txns starting day 5/15/24 (isFraud=1). Label column is for evaluation only."""
import numpy as np, pandas as pd
DAY = 86400.0

def generate(seed: int = 42, n_accounts: int = 250, days: int = 30, scenario: str = "base") -> pd.DataFrame:
    r = np.random.default_rng(seed); rows = []
    def add(a, t, amt, dev, mail, y, kind):
        rows.append(dict(account=a, t=float(t), amount=float(amt), device=dev, email=mail, isFraud=y, kind=kind))
    mus = {}
    for i in range(n_accounts):
        a = f"acct_{i}"; mus[a] = r.uniform(2.5, 4.5)
        dev = f"dev_{i}" if r.random() > 0.1 else f"dev_fam_{i % 15}"
        for t in r.uniform(0, days * DAY, r.poisson(40)):
            add(a, t, np.exp(r.normal(mus[a], 0.4)), dev, f"mail_{i}", 0, "normal")
    for i in r.choice(n_accounts, 15, replace=False):
        a = f"acct_{i}"
        for t in r.uniform(5 * DAY, days * DAY, r.integers(1, 4)):
            add(a, t, np.exp(mus[a]) * r.uniform(10, 30), f"dev_{i}", f"mail_{i}", 1, "takeover")
    for k, start in enumerate((5, 15, 24)):
        for m in range(6):
            a = f"ring{k}_{m}"; dev = f"ring_dev_{k}"; mail = f"ring_mail_{k}_{m}"
            for t in r.uniform(0, start * DAY, r.integers(3, 6)):
                add(a, t, np.exp(r.normal(3.0, 0.3)), dev, mail, 0, "ring_warmup")
            for t in start * DAY + r.uniform(0, 2 * DAY, r.integers(3, 7)):
                add(a, t, np.exp(r.normal(5.5, 0.3)), dev, mail, 1, "ring")
    if scenario in ("decay", "decay_hard"):   # 12 device-sharing groups; links are fresh (fraud) or stale (innocent reuse)
        for k in range(12):
            fresh = k % 2 == 0; dev = f"dec_dev_{k}"; burst = (2 + 25 / 11 * k) * DAY
            for m in range(4):
                a, mail = f"dring{k}_{m}", f"dring_mail_{k}_{m}"
                for t in r.uniform(0, burst, r.integers(3, 5)): add(a, t, np.exp(r.normal(3.0, 0.3)), dev, mail, 0, "decay_warmup")
                for t in burst + r.uniform(0, 0.5 * DAY, r.integers(3, 6)): add(a, t, np.exp(r.normal(5.5, 0.3)), dev, mail, 1, "decay_ring")
            for m in range(3):
                a, mail = f"dfol{k}_{m}", f"dfol_mail_{k}_{m}"
                if fresh: ts, mu, y, kind = burst + 0.5 * DAY + r.uniform(0, DAY, r.integers(2, 4)), 5.5, 1, "decay_fresh"
                else: ts, mu, y, kind = burst + (10 + r.uniform(0, 4)) * DAY + r.uniform(0, DAY, 2), (5.5 if scenario == "decay_hard" else 3.0), 0, "decay_stale"
                for t in ts[ts < days * DAY]: add(a, t, np.exp(r.normal(mu, 0.4)), dev, mail, y, kind)
    df = pd.DataFrame(rows).sort_values("t", kind="stable").reset_index(drop=True)
    df.insert(0, "tx_id", [f"T{i:06d}" for i in range(len(df))])
    return df
