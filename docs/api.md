# API guide
Interactive docs: `/docs` (OpenAPI). Base path `/api/v1`. Errors are JSON `{"detail": "..."}` with 4xx/5xx codes.
Roles: **admin** (`FG_API_KEY`) can call every protected endpoint; **analyst** (`FG_ANALYST_API_KEY`, optional) can only `PATCH /api/v1/alerts/{id}` (403 on the others). Failed attempts are throttled (429 after `FG_AUTH_FAIL_LIMIT` per minute per client) and all requests are rate limited (429 with `Retry-After`; `/health` and `/ready` exempt).
Protected endpoints (`POST /api/v1/datasets/upload`, `POST /api/v1/experiments`, `PATCH /api/v1/alerts/{alert_id}`, `PATCH /api/v1/config`) require header `X-API-Key` equal to env `FG_API_KEY`; they return 503 if it is unset and 401 if wrong.
Fraud labels (`isFraud`) are never returned by any endpoint.

## Routes (generated from the running app)
| Method | Path |
|---|---|
| GET | `/api/v1/alerts` |
| PATCH | `/api/v1/alerts/{alert_id}` |
| GET | `/api/v1/config` |
| PATCH | `/api/v1/config` |
| GET | `/api/v1/datasets` |
| POST | `/api/v1/datasets/upload` |
| GET | `/api/v1/datasets/{dataset_id}` |
| GET | `/api/v1/datasets/{dataset_id}/quality` |
| POST | `/api/v1/demo/load` |
| GET | `/api/v1/entities/{entity_id}/risk-history` |
| GET | `/api/v1/experiments` |
| POST | `/api/v1/experiments` |
| GET | `/api/v1/experiments/latest/metrics` |
| GET | `/api/v1/experiments/{experiment_id}` |
| GET | `/api/v1/experiments/{experiment_id}/metrics` |
| GET | `/api/v1/exports/alerts` |
| GET | `/api/v1/exports/evaluation` |
| GET | `/api/v1/graph/clusters` |
| GET | `/api/v1/graph/entities/{entity_id}/neighbors` |
| GET | `/api/v1/pipelines/jobs` |
| GET | `/api/v1/pipelines/jobs/{job_id}` |
| GET | `/api/v1/stats/trends` |
| GET | `/api/v1/system/latency` |
| GET | `/api/v1/system/status` |
| GET | `/api/v1/transactions` |
| POST | `/api/v1/transactions/score` |
| GET | `/api/v1/transactions/{tx_id}` |
| GET | `/health` |
| GET | `/ready` |

## Examples
```bash
curl -X POST localhost:8000/api/v1/demo/load
curl "localhost:8000/api/v1/transactions?category=high&sort=-risk&page=1&page_size=25"
curl localhost:8000/api/v1/transactions/T000123          # includes explanation evidence
curl localhost:8000/api/v1/graph/clusters
curl -X PATCH -H "X-API-Key: $FG_API_KEY" -H "Content-Type: application/json" -d '{"status":"escalated","note":"checked"}' localhost:8000/api/v1/alerts/A-T000123
```
Case statuses: open, under_review, escalated, resolved, dismissed. Config keys: medium, high, critical (0<=medium<=high<=critical<=1), cluster_risk, cluster_min_size (>=2).
Limits: page_size <= 200; uploads <= 300 MB; upload returns 202 + job id (poll `/api/v1/pipelines/jobs/{id}`).
Exports: `GET /api/v1/exports/alerts?format=csv|json[&status=]` and `GET /api/v1/exports/evaluation?format=csv|json` (attachments; text cells are protected against spreadsheet formula injection; reads are unauthenticated like other GETs).
Experiments: `POST /api/v1/experiments {"scenario":"base|decay|decay_hard","seed":42}` -> 202 with an id; one active run at a time (409 otherwise); poll `GET /api/v1/experiments/{id}` (status, stage); `.../metrics` returns 409 until done; `/experiments/latest/metrics` returns the latest completed run (else the legacy CLI artifact).
Clusters: detected time-sliced (state as of each of `FG_CLUSTER_CHECKPOINTS` checkpoints, using only events up to that time); each has `detected_at` (checkpoint resolution, seconds relative to first event), `growth` history and `detection_basis`.
`GET /api/v1/entities/{id}/risk-history` returns an account's prediction-time scores over time; `GET /api/v1/stats/trends?buckets=N` returns per-bucket transaction/alert counts and the cluster timeline.
`POST /api/v1/transactions/score` is a read-only dry run: it scores a hypothetical event (`account`, `amount`, `t`, optional `identifiers`) against the current state and stores/updates nothing. `t` must be >= the latest processed event time (422 otherwise), so it never peeks at the future. Unknown accounts return a cold-start warning.
`GET /ready` returns 200/503 from settings and database checks (dataset presence is informational). `GET /api/v1/system/latency` returns the latest latency benchmark artifact (404 = not evaluated).
Datasets: `GET /api/v1/datasets` (+ `/{id}`, `/{id}/quality`; ids like `demo:42`, `upload:<job id>`). Metadata and the quality report persist in the database; the data itself is in memory (`data_in_memory`/`active` show which one is loaded).
Not implemented (listed in the original spec): per-user accounts.
