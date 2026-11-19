# ATFRP (as implemented in `backend/app/algorithms/atfrp.py`)
For an event of account i at time t (state strictly before t):
- **B** = tanh(|amount - median| / (1.4826*MAD + floor) / z_scale), robust to outliers; 0 with cold-start flag if history < `min_history`.
- **N** = sum_j A_ij * exp(-lambda * dt_ij) * R_j. j = other accounts sharing a device/email; A_ij = shared_count_ij / sum_k shared_count_ik
  (self excluded, so N in [0,1]); dt_ij = time since that link was last seen; R_j = EWMA of j's past transaction risks (0 if never scored).
- **C** = (high-risk neighbors / neighbors) * min(1, n_high / conc_ref).  **T** = exp(-lambda_t * gap since the account's previous event), 0 if none.
- **R** = sigmoid(wB*B + wN*N + wC*C + wT*T + b). A risk score, not a calibrated probability.
- **Hub suppression:** identifiers already shared by > `max_fanout` accounts are ignored (uses only past state).
- **Temporal safety:** events replay in (t, tx_id) order; all events with equal t are scored before any update; an event never affects its own score;
  Event has no label field.
- **Weights:** fitted by L2 logistic regression on training-period rows only, iterated 3x (fit -> replay) so weights match the propagation dynamics
  they are applied under. A single fit-then-replay inflated neighborhood weights and produced many false positives. This is fitting, not online learning.

## Cluster detection
Accounts with entity risk >= `cluster_risk` are linked when they share an identifier; connected components with >= `cluster_min_size` members are suspicious clusters (a structural pattern, not confirmed fraud).
Detection is time-sliced: at each checkpoint the detector runs on the engine state as of that time. A final cluster's `detected_at` is the first checkpoint where a subset of it (>= min size) was already clustered; `growth` lists subset sizes over time.
