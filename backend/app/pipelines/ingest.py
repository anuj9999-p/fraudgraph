"""IEEE-CIS ingestion. Account proxy: IEEE-CIS has no account/merchant id, so an account is the
pseudonymous hash of (card1, card2, card4, addr1). Device = DeviceInfo (identity file; missing for
unmatched transactions, which are kept). Email domains are NOT used as identifiers (too generic).
TransactionDT is seconds from an undisclosed reference, used as relative event time. isFraud is
kept only as an evaluation/training label column."""
import hashlib, pandas as pd

MAX_BYTES = 300 * 1024 * 1024
REQUIRED = ["TransactionID", "TransactionDT", "TransactionAmt", "card1"]

def _acct(r):
    k = "|".join("" if pd.isna(v) else str(v) for v in r)
    return "acct_" + hashlib.sha1(k.encode()).hexdigest()[:12]

def ingest_ieee(tx_path, id_path=None):
    head = pd.read_csv(tx_path, nrows=0).columns
    miss = [c for c in REQUIRED if c not in head]
    if miss: raise ValueError(f"missing required columns: {miss}")
    use = [c for c in REQUIRED + ["card2", "card4", "addr1", "isFraud"] if c in head]
    tx = pd.read_csv(tx_path, usecols=use); n_raw = len(tx)
    dups = int(tx.duplicated("TransactionID").sum()); tx = tx.drop_duplicates("TransactionID")
    for c in ("TransactionDT", "TransactionAmt"): tx[c] = pd.to_numeric(tx[c], errors="coerce")
    bad = tx["TransactionDT"].isna() | tx["TransactionAmt"].isna() | (tx["TransactionAmt"] < 0)
    n_bad = int(bad.sum()); tx = tx[~bad].copy()
    tx["device"] = None; matched = 0
    if id_path:
        ih = pd.read_csv(id_path, nrows=0).columns
        if "TransactionID" not in ih: raise ValueError("identity file lacks TransactionID")
        ids = pd.read_csv(id_path, usecols=["TransactionID"] + (["DeviceInfo"] if "DeviceInfo" in ih else []))
        ids = ids.drop_duplicates("TransactionID"); matched = int(tx["TransactionID"].isin(ids["TransactionID"]).sum())
        if "DeviceInfo" in ids: tx = tx.drop(columns="device").merge(ids, on="TransactionID", how="left").rename(columns={"DeviceInfo": "device"})
    acct_cols = [c for c in ("card1", "card2", "card4", "addr1") if c in tx.columns]
    out = pd.DataFrame({"tx_id": "T" + tx["TransactionID"].astype("int64").astype(str).str.zfill(8),
                        "t": tx["TransactionDT"].astype(float), "amount": tx["TransactionAmt"].astype(float),
                        "account": [_acct(r) for r in tx[acct_cols].itertuples(index=False)],
                        "device": tx["device"].astype("object").where(tx["device"].notna(), None), "email": None})
    if "isFraud" in tx: out["isFraud"] = tx["isFraud"].astype(int).to_numpy()
    out = out.sort_values(["t", "tx_id"], kind="stable").reset_index(drop=True)
    q = dict(rows_read=n_raw, rows_kept=len(out), duplicate_ids_dropped=dups, invalid_rows_dropped=n_bad,
             with_identity=matched, unmatched_kept=len(out) - matched if id_path else len(out),
             missing_device_pct=round(float(out["device"].isna().mean() * 100), 2), accounts=int(out["account"].nunique()),
             has_labels="isFraud" in out)
    if "isFraud" in out: q["fraud_rows"] = int(out["isFraud"].sum()); q["fraud_rate"] = round(float(out["isFraud"].mean()), 5)
    return out, q
