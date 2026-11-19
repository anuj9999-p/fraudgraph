# Dataset setup
1. Obtain IEEE-CIS Fraud Detection from Kaggle (accept the competition rules; use the official download). Do not redistribute it.
2. Place `train_transaction.csv` and `train_identity.csv` in `data/raw/` (git-ignored).
3. Upload via the API (see README). Reference figures (~590,540 transactions, ~144,233 identity rows, ~20,663 fraud) are to be verified
   against the quality report returned by the job, not assumed.
Assumptions: no real account/merchant id exists, so account = hash(card1, card2, card4, addr1) (a proxy); the only identifier is `DeviceInfo`
(many rows lack it; unmatched transactions are kept); `TransactionDT` is relative seconds; `isFraud` is used only to fit/evaluate.
Limitations: generic DeviceInfo values are handled by hub suppression, not removed; sparse identifiers mean weaker graph signal than the synthetic data.
