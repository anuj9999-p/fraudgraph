# Final implementation and verification report
Status: research prototype, partially complete. Not production-certified; does not detect all fraud; scores are not confirmed fraud.
## Verification run
- Backend tests: **73 passed** (`cd backend && python3 -m pytest -q`).
- Frontend tests: **22 passed** (`cd frontend && npm test`); type-check + production build pass (`npm run build`).
- Wiring check: API reached through the frontend server's proxy (demo load, clusters, protected config PATCH). No real-browser or visual check was done.
- Docker, PostgreSQL: **not verified / not built**.
## Completed
ATFRP engine (B, N, C, T, sigmoid risk; hub suppression; deterministic ordered replay; ablation switches); synthetic data (3 scenarios); chronological experiment with baselines A/B/C,
ablations D/D1/D2/E and full model; validation-only decay-rate tuning; time-sliced cluster detection (verified equal to replaying only past events), risk-history and trend endpoints; evidence-based explanations; FastAPI backend (alerts, case status, config, graph neighborhoods, upload jobs);
IEEE-CIS ingestion with documented account proxy; React frontend (Overview, Transactions, Graph, Investigations, Model Lab, Datasets, Config); docs, Dockerfiles, requirements.
## Measured results
See `docs/evaluation.md`. All synthetic. Honest summary: neighborhood propagation clearly helps; on the `base` scenario full ATFRP is not distinguishable from strong simple baselines (gradient-boosted tree, static graph); on the author-designed `decay_hard` scenario decay helps and the full model leads. Strongest finding: removing temporal decay lowered PR-AUC by 0.19 on 8/8 `decay_hard` seeds (author-designed scenario). T signal: no reliable effect.
## Measured latency
In-process per-event scoring p50 ~0.0123 ms, p99 ~0.0359 ms with state update (single run, 1 vCPU, small synthetic graph; see docs/evaluation.md).

## Measured scale
Synthetic ~560k rows (IEEE-CIS-sized): full load ~56 s (was ~92 s before replay sharing), peak ~1.0 GB RSS on 1 vCPU (docs/scalability.md). Real IEEE-CIS data not run.

## Not done (vs. the original specification)
verified PostgreSQL (SQLAlchemy persistence + Alembic migrations (0001 initial, 0002 datasets) exist and are tested on SQLite only); per-user identity/SSO (access control is two shared API keys: admin and analyst; rate limits are in-memory per process); a human-readable evaluation report beyond `report.md` (ROC/PR curves, confusion matrices and CSV/JSON exports now exist);
merchant nodes; IEEE-CIS benchmark run (dataset absent); CI workflow written but not executed (no GitHub runner here); Docker verification.
## Known limitations
Account is a hashed proxy (card1/card2/card4/addr1); only DeviceInfo is an identifier (sparse); in-memory state and graph (scale measured on synthetic data up to ~560k rows only); risk is an uncalibrated score;
cluster detection time has checkpoint resolution (default 30 slices) and changing cluster settings triggers a re-replay (slow on very large data); learned weights are fitted (not online-learned); decay rate selection is a validation-only variance/safety trade-off (conservative default; see docs/evaluation.md), the grid is coarse and dataset time-scale dependent.
## Definition-of-done check
Met: app starts (build/proxy check), endpoints documented, synthetic demo loadable, typed graph with timestamps, ATFRP uses all four signals, ordered propagation, clusters and explanations from data, baselines/ablations run, metrics from real predictions, no fabricated benchmarks.
Not met: migrations, verified Docker, IEEE-CIS benchmark, several spec'd endpoints/pages features listed above.
