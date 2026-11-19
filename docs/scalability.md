# Scalability (measured on synthetic data)
Command: `python3 scripts/scale_profile.py <n_accounts> [--tune]` (one process per size; raw results in `artifacts/scale/scale_profile.json`, including the figures from before the replay-sharing optimization).
Hardware: Intel(R) Xeon(R) Processor @ 2.10GHz, 1 logical CPU, 4 GB RAM visible, Python 3.12.3, Linux-6.18.44-fc-v114-x86_64-with-glibc2.39. One run per size, no concurrent load.
Data: SYNTHETIC rows (accounts scale up; the fraud-ring structure does not), written as IEEE-CIS-shaped CSVs for the ingest stage.

| Rows | CSV ingest s | One ATFRP replay s | Weight fitting s | Full load incl. time-sliced clusters, no tuning s | Full load before optimization s | Peak RSS MB |
|---|---|---|---|---|---|---|
| 10,227 | 0.07 | 0.14 | 0.81 | 0.75 | 1.39 | 184.9 (was 186.8) |
| 48,044 | 0.24 | 1.11 | 4.13 | 4.25 | 7.71 | 251.6 (was 266.3) |
| 199,518 | 1.18 | 5.49 | 25.66 | 24.32 | 38.76 | 505.8 (was 570.2) |
| 559,885 | 3.41 | 11.56 | 53.18 | 56.19 | 92.07 | 1070.9 (was 1226.3) |

Reading: cost is roughly linear in rows; the largest run (559,885 rows, close to IEEE-CIS' ~590k) loads in about 56 s (was 92 s) using about 1071 MB.
**Optimization (replay sharing, results verified identical by tests):** the final weight-fitting replay is reused as the scoring replay and takes the cluster snapshots (previously two extra replays), events are built once per fit instead of once per replay, and decay-rate tuning reuses the winning fit instead of refitting.
Remaining dominant cost: weight fitting (3 fit-and-replay iterations plus the final replay); loading is now essentially that cost.
Decay-rate tuning (used by uploads) was measured only at 48,044 rows: 18.0 s for 4 candidate rates, vs 5.39 s for one fit (about 3.3x). Extrapolating to ~560k rows suggests roughly 3.0 minutes; this is an estimate, not a measurement.
Caveats: real IEEE-CIS data differs (identifier fan-out, missing values, hundreds of columns of which only a few are read); cost per event grows with neighborhood size (capped by `max_fanout`); everything is single-threaded Python; timings vary run to run (the one-replay figure at the largest size differs by ~15% between runs).
Treat these as order-of-magnitude guidance, not a guarantee.
