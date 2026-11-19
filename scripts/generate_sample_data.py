"""Write the deterministic SYNTHETIC demo set as IEEE-CIS-shaped CSVs (for testing upload).
Usage (from repo root): python3 scripts/generate_sample_data.py [seed]"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))
import numpy as np, pandas as pd
from app.data.synthetic import generate
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
d = generate(seed); out = pathlib.Path(__file__).resolve().parents[1] / "data/samples"; out.mkdir(parents=True, exist_ok=True)
tx = pd.DataFrame({"TransactionID": np.arange(1_000_000, 1_000_000 + len(d)), "TransactionDT": d.t, "TransactionAmt": d.amount.round(2),
                   "card1": pd.factorize(d.account)[0], "card2": 111.0, "card4": "visa", "addr1": 300.0, "isFraud": d.isFraud})
tx.to_csv(out / "synthetic_transaction.csv", index=False)
pd.DataFrame({"TransactionID": tx.TransactionID, "DeviceInfo": d.device}).to_csv(out / "synthetic_identity.csv", index=False)
print(f"wrote {len(tx)} rows to {out} (SYNTHETIC, seed {seed})")
