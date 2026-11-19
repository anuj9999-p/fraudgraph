# FraudGraph AI

Adaptive Temporal Graph-Based Financial Fraud Detection, built around **ATFRP** (Adaptive Temporal Fraud-Risk Propagation).
Authors: Anuj Shukla (24BCE0314),  Decision-support research prototype: it does not block transactions, and a high score is not confirmed fraud.

## Status
Working: ATFRP engine, synthetic data, chronological experiment (baselines, ablations, metrics), clusters, evidence-based explanations,
FastAPI backend, IEEE-CIS ingestion + upload jobs, React frontend (Overview, Transactions, Graph, Investigations, Model Lab, Datasets, Config).
Not built yet: per-user accounts/SSO, verified Postgres, a full IEEE-CIS run, in-memory scores/graph (cases and jobs persist).
Docker files are unverified. No IEEE-CIS benchmark has been run; all reported metrics are from SYNTHETIC data.

## Configuration (environment variables)
All settings are `FG_*` environment variables, documented with defaults in `.env.example` (API key, CORS origins, database URL, upload limit,
log level, seed, split fractions, tau grid, risk thresholds, cluster settings, ATFRP overrides). `cp .env.example .env`, edit, then
`set -a; source .env; set +a` before starting the backend (Docker loads `.env` itself). Invalid values fail fast with a clear error.
Cases, audit trail and upload jobs persist in the database (`FG_DATABASE_URL`, SQLite by default); with `FG_DB_AUTO_CREATE=true` (default) tables are created on first use; for production set it to `false` and run migrations: `cd backend && alembic upgrade head`
(new schema change: edit `app/db.py`, then `alembic revision --autogenerate -m "msg"`; a test fails if models and migrations drift). CI: `.github/workflows/ci.yml` (backend tests, frontend tests and build; not run in the authoring sandbox).

## Run (local)
```bash
cd backend && pip install -r requirements.txt
python3 -m pytest -q                                   # 73 tests
FG_API_KEY=yourkey python3 -m uvicorn app.main:app --port 8000
cd ../frontend && npm install && npm test && npm run dev    # 22 frontend tests; app at http://localhost:5173 (proxies /api to :8000)
```
Open the app, click **Load synthetic demo** on Overview. API docs: http://localhost:8000/docs

## Experiments
From the UI: Model Lab -> *Run an experiment* (needs the API key; one run at a time; progress shown; runs and metrics are stored in the database, artifacts under `artifacts/experiments/runs/<id>/`).
CLI:
```bash
cd backend && python3 -m app.ml.experiment --seed 42   # writes artifacts/experiments/synthetic_seed42/{metrics.json,report.md}
```
Scenarios: `--scenario base|decay|decay_hard` (decay scenarios test fresh-vs-stale device reuse; author-designed, synthetic).
Models: A (logreg, gradient-boosted tree), B static graph, C temporal-behavioral, D ATFRP w/o recency (+ D1 no decay only, D2 no T only), E ATFRP w/o neighborhood, full ATFRP.
Weights fit on the first 60% of time, thresholds chosen on the next 20% (max F1), metrics reported on the final 20%.

## Access control and rate limits
Two roles via API keys (sent in `X-API-Key`): **admin** = `FG_API_KEY` (config, uploads, experiments, case updates); **analyst** = optional `FG_ANALYST_API_KEY` (case updates only; 403 elsewhere).
Reads are open. Per-client sliding-window limits (`FG_RATE_LIMIT_*`, `FG_AUTH_FAIL_LIMIT`; in-memory, per process) return 429 + `Retry-After`; keys are compared in constant time and never logged (the audit trail records the role).
This is shared-secret access control, not per-user identity: there are no user accounts, sessions or per-user audit.

## Scalability
`python3 scripts/scale_profile.py <n_accounts>` profiles stage time and peak memory; results and caveats in `docs/scalability.md` (synthetic ~560k rows: ~56 s load, ~1.0 GB peak on 1 vCPU).

## Latency
`cd backend && python3 -m app.ml.latency --scenario base --seed 42` measures per-event in-process scoring latency (method and results in `docs/evaluation.md`).
On startup, queued/running jobs and experiments left by a previous process are marked failed (single server process assumed). `GET /ready` checks settings and database.

## Real data (IEEE-CIS)
See `docs/dataset.md`. Upload via `POST /api/v1/datasets/upload` (header `X-API-Key`), then poll `/api/v1/pipelines/jobs/{id}`:
```bash
curl -H "X-API-Key: yourkey" -F transactions=@data/raw/train_transaction.csv -F identity=@data/raw/train_identity.csv localhost:8000/api/v1/datasets/upload
```
A small IEEE-shaped synthetic pair: `python3 scripts/generate_sample_data.py` -> `data/samples/`.

## Docker (unverified)
`cp .env.example .env`, set `FG_API_KEY`, then `docker compose up --build` -> http://localhost:8080
