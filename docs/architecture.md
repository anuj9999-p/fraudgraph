# Architecture (implemented)
```mermaid
flowchart LR
  CSV[IEEE-CIS CSV / synthetic] --> ING[pipelines/ingest.py]
  ING --> ST[services/state.py]
  ST --> ENG[algorithms/atfrp.py engine]
  ENG --> CL[clustering] & EX[explainability]
  ST --> API[FastAPI /api/v1]
  CL --> API
  EX --> API
  API --> UI[React frontend]
  EXP[ml/experiment.py] --> ART[artifacts/experiments/*.json]
  ART --> API
```
In-memory state (no database yet). Clusters are detected time-sliced (`clustering/timeline.py`): a fresh replay snapshots cluster state at checkpoints using only past events; per-transaction scores are prediction-time. Changing cluster settings re-runs that replay.
