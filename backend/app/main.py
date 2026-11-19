import os, json, csv, io, uuid, hmac, contextvars, tempfile, threading, traceback
from pathlib import Path
from enum import Enum
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Query, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.ratelimit import limiter
import logging
from app import db
from app.core.settings import get_settings
from app.services.state import State, DEFAULT_CFG
from app.algorithms.atfrp import Event
from app.explainability.explain import explain

logging.basicConfig(level=get_settings().log_level)
_client = contextvars.ContextVar("client_ip", default="unknown")

def _ip(request: Request, trust_proxy: bool):
    if trust_proxy and request.headers.get("x-forwarded-for"): return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "unknown"

async def _rate_limit(request: Request, call_next):
    s = get_settings(); ip = _ip(request, s.trust_proxy); _client.set(ip)
    if request.url.path not in ("/health", "/ready"):
        checks = [("all", s.rate_limit_per_minute)] + ([("write", s.rate_limit_write_per_minute)] if request.method in ("POST", "PATCH", "PUT", "DELETE") else [])
        for bucket, limit in checks:
            ok, retry = limiter.allow(bucket, ip, limit)
            if not ok: return JSONResponse({"detail": "rate limit exceeded; retry later"}, status_code=429, headers={"Retry-After": str(int(retry) + 1)})
    return await call_next(request)

@asynccontextmanager
async def lifespan(_):
    try:
        n = db.fail_interrupted()
        if n: logging.getLogger("fraudgraph").warning("marked %d interrupted job(s)/experiment(s) as failed", n)
    except Exception: logging.getLogger("fraudgraph").exception("startup cleanup failed")
    yield
app = FastAPI(title="FraudGraph AI", version="0.1.0", lifespan=lifespan); S = State()
app.add_middleware(BaseHTTPMiddleware, dispatch=_rate_limit)      # added before CORS so CORS stays outermost (429s carry CORS headers)
app.add_middleware(CORSMiddleware, allow_origins=list(get_settings().cors_origins), allow_methods=["GET", "POST", "PATCH"], allow_headers=["*"])
API = "/api/v1"; STATUSES = ["open", "under_review", "escalated", "resolved", "dismissed"]

def need_auth(key, role="admin"):
    """Returns the caller's role. admin key (FG_API_KEY) may do everything; analyst key (FG_ANALYST_API_KEY) only analyst-level actions."""
    s = get_settings(); ip = _client.get()
    if not s.api_key: raise HTTPException(503, "FG_API_KEY not configured; protected endpoints disabled")
    if limiter.blocked("authfail", ip, s.auth_fail_limit): raise HTTPException(429, "too many failed authentication attempts; retry later", headers={"Retry-After": "60"})
    given = (key or "").encode()
    if hmac.compare_digest(given, s.api_key.encode()): return "admin"
    if s.analyst_api_key and hmac.compare_digest(given, s.analyst_api_key.encode()):
        if role == "analyst": return "analyst"
        raise HTTPException(403, "this action requires the admin role")
    limiter.hit("authfail", ip); raise HTTPException(401, "invalid API key")

def need_data():
    if not S.loaded: raise HTTPException(409, "No dataset loaded. POST /api/v1/demo/load first.")

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/ready")
def ready():
    checks = {}
    try: get_settings(); checks["settings"] = True
    except Exception as e: checks["settings"] = False; checks["settings_error"] = str(e)
    try: db.ping(); checks["database"] = True
    except Exception: checks["database"] = False
    checks["dataset_loaded"] = S.loaded      # informational: readiness does not require data
    ok = checks["settings"] and checks["database"]
    return Response(json.dumps(dict(status="ready" if ok else "not_ready", checks=checks)), status_code=200 if ok else 503, media_type="application/json")

@app.get(f"{API}/system/latency")
def latency():
    fs = sorted((get_settings().artifact_dir / "experiments").glob("latency_*.json"), key=lambda p: p.stat().st_mtime)
    if not fs: raise HTTPException(404, "Not evaluated: run python3 -m app.ml.latency")
    return json.loads(fs[-1].read_text())

def _register():
    db.record_dataset(S.dataset_id, S.source, len(S.scores), S.weights, S.quality)

@app.get(f"{API}/datasets")
def datasets():
    return dict(items=[dict(d, active=bool(S.loaded and d["id"] == S.dataset_id)) for d in db.list_datasets()])

@app.get(API + "/datasets/{dataset_id}")
def dataset(dataset_id: str):
    d = db.get_dataset(dataset_id)
    if not d: raise HTTPException(404, "dataset not found")
    return dict(d, active=bool(S.loaded and d["id"] == S.dataset_id), data_in_memory=bool(S.loaded and d["id"] == S.dataset_id))

@app.get(API + "/datasets/{dataset_id}/quality")
def dataset_quality(dataset_id: str):
    d = db.get_dataset(dataset_id)
    if not d: raise HTTPException(404, "dataset not found")
    return d["quality"] or {}

@app.get(f"{API}/system/status")
def status():
    return dict(dataset_loaded=S.loaded, data_source=S.source if S.loaded else None, weights=S.weights if S.loaded else None,
                transactions=len(S.scores) if S.loaded else 0, clusters=len(S.clusters) if S.loaded else 0,
                model="atfrp-v1" if S.loaded else None, dataset_id=S.dataset_id if S.loaded else None, latest_event_t=S.max_t if S.loaded else None, ground_truth_exposed=False)

@app.post(f"{API}/demo/load")
def load(seed: int = 42):
    S.load_demo(seed); _register(); return status()

@app.get(f"{API}/transactions")
def transactions(category: str | None = None, min_amount: float = 0, search: str | None = None,
                 sort: str = "-risk", page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    need_data(); rows = [S.tx(i) for i in S.scores]
    rows = [r for r in rows if r["amount"] >= min_amount and (not category or r["category"] == category)
            and (not search or search in r["tx_id"])]
    key = sort.lstrip("-")
    if key not in ("risk", "amount", "t"): raise HTTPException(422, "sort must be risk, amount or t")
    rows.sort(key=lambda r: (r[key], r["tx_id"]), reverse=sort.startswith("-"))
    return dict(total=len(rows), page=page, items=rows[(page - 1) * page_size: page * page_size])

class IdentifierIn(BaseModel):
    type: str = Field(max_length=32); value: str = Field(max_length=200)

class ScoreRequest(BaseModel):
    account: str = Field(min_length=1, max_length=200); amount: float = Field(ge=0, allow_inf_nan=False)
    t: float = Field(allow_inf_nan=False); identifiers: list[IdentifierIn] = Field(default_factory=list, max_length=10)

@app.post(f"{API}/transactions/score")
def score_transaction(body: ScoreRequest):
    """Read-only (dry-run) scoring of a hypothetical new event against the current state; nothing is stored or updated."""
    need_data()
    if body.t < S.max_t: raise HTTPException(422, "event time precedes already-processed history; scoring is only as-of the latest state")
    e = Event("adhoc", body.t, body.account, body.amount, tuple((i.type, i.value) for i in body.identifiers))
    sc = S.engine.process(e, commit=False)
    return dict(dry_run=True, risk=round(sc.risk, 4), category=S.category(sc.risk), model="atfrp-v1", explanation=explain(sc, S.params, S.cluster_of.get(body.account)))

@app.get(API + "/transactions/{tx_id}")
def transaction(tx_id: str):
    need_data()
    if tx_id not in S.scores: raise HTTPException(404, "transaction not found")
    return S.tx(tx_id, detail=True)

@app.get(API + "/graph/entities/{entity_id}/neighbors")
def neighbors(entity_id: str, limit: int = Query(50, ge=1, le=200)):
    need_data(); e = S.engine
    if entity_id not in e.ids and entity_id not in e.risk: raise HTTPException(404, "entity not found")
    nodes = {entity_id: dict(id=entity_id, type="account", risk=round(e.risk.get(entity_id, 0), 4))}; edges = []
    for ident in sorted(e.ids[entity_id]):
        iid = f"{ident[0]}:{ident[1]}"; nodes[iid] = dict(id=iid, type=ident[0])
        edges.append(dict(source=entity_id, target=iid, last_seen=e.links[ident][entity_id][1]))
        for a, (cnt, ts) in list(e.links[ident].items())[:limit]:
            nodes.setdefault(a, dict(id=a, type="account", risk=round(e.risk.get(a, 0), 4)))
            if a != entity_id: edges.append(dict(source=a, target=iid, last_seen=ts, count=cnt))
    return dict(nodes=list(nodes.values()), edges=edges, cluster=S.cluster_of.get(entity_id, {}).get("cluster_id"))

@app.get(API + "/entities/{entity_id}/risk-history")
def risk_history(entity_id: str, limit: int = Query(200, ge=1, le=1000)):
    need_data(); ids = S.by_account.get(entity_id)
    if not ids: raise HTTPException(404, "entity not found")
    items = [dict(tx_id=i, t=S.scores[i].t, risk=round(S.scores[i].risk, 4), B=round(S.scores[i].B, 4), N=round(S.scores[i].N, 4),
                  C=round(S.scores[i].C, 4), T=round(S.scores[i].T, 4), category=S.category(S.scores[i].risk)) for i in ids[-limit:]]
    return dict(entity_id=entity_id, total=len(ids), items=items)

@app.get(f"{API}/stats/trends")
def trends(buckets: int = Query(24, ge=2, le=200)):
    need_data(); ts = [sc.t for sc in S.scores.values()]; t0, t1 = min(ts), max(ts); w = (t1 - t0) / buckets or 1.0
    rows = [dict(t_start=t0 + k * w, t_end=t0 + (k + 1) * w, transactions=0, alerts=0) for k in range(buckets)]
    for sc in S.scores.values():
        b = rows[min(int((sc.t - t0) / w), buckets - 1)]; b["transactions"] += 1; b["alerts"] += sc.risk >= S.cfg["high"]
    return dict(buckets=rows, cluster_timeline=S.cluster_timeline, time_unit="seconds relative to first event")

@app.get(f"{API}/graph/clusters")
def clusters(): need_data(); return dict(items=S.clusters)

def _alert_items(status=None):
    cases = db.all_cases(S.dataset_id); hi = [S.tx(i) for i in S.scores if S.scores[i].risk >= S.cfg["high"]]
    items = [dict(alert_id="A-" + r["tx_id"], status=cases.get(r["tx_id"], {}).get("status", "open"), **r) for r in hi]
    if status: items = [i for i in items if i["status"] == status]
    return sorted(items, key=lambda i: (-i["risk"], i["tx_id"]))

@app.get(f"{API}/alerts")
def alerts(status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    need_data(); items = _alert_items(status)
    return dict(total=len(items), items=items[(page - 1) * page_size: page * page_size])

def _cell(v):  # neutralise spreadsheet formula injection in text cells
    if isinstance(v, (int, float)) or v is None: return "" if v is None else v
    v = str(v); return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v

def _csv(rows, cols):
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(cols)
    for r in rows: w.writerow([_cell(r.get(c)) for c in cols])
    return buf.getvalue()

def _download(name, fmt, rows, cols, payload):
    if fmt == "json": return Response(json.dumps(payload, indent=2), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{name}.json"'})
    return Response(_csv(rows, cols), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})

@app.get(f"{API}/exports/alerts")
def export_alerts(format: str = Query("csv", pattern="^(csv|json)$"), status: str | None = None):
    need_data(); items = _alert_items(status)
    return _download("alerts", format, items, ["alert_id", "status", "tx_id", "account", "t", "amount", "risk", "category", "model"], dict(items=items, source=S.source))

@app.get(f"{API}/exports/evaluation")
def export_evaluation(format: str = Query("csv", pattern="^(csv|json)$")):
    m = _latest(); cols = ["model", "precision", "recall", "f1", "fpr", "roc_auc", "pr_auc", "threshold", "tp", "fp", "fn", "tn"]
    rows = [dict(model=k, **{c: v["test"].get(c) for c in cols[1:]}) for k, v in m["models"].items()]
    return _download("evaluation", format, rows, cols, m)

class CaseUpdate(BaseModel):
    status: str | None = None; note: str | None = Field(None, max_length=2000)

@app.patch(API + "/alerts/{alert_id}")
def update_alert(alert_id: str, body: CaseUpdate, x_api_key: str | None = Header(None)):
    role = need_auth(x_api_key, "analyst"); need_data(); tid = alert_id.removeprefix("A-")
    if tid not in S.scores or S.scores[tid].risk < S.cfg["high"]: raise HTTPException(404, "alert not found")
    if body.status and body.status not in STATUSES: raise HTTPException(422, f"status must be one of {STATUSES}")
    c = db.update_case(S.dataset_id, tid, body.status, body.note)
    db.audit("alert_update", dict(alert=alert_id, status=c["status"], note_added=bool(body.note), role=role)); return c

@app.get(f"{API}/config")
def get_config(): return S.cfg

@app.patch(f"{API}/config")
def patch_config(body: dict, x_api_key: str | None = Header(None)):
    role = need_auth(x_api_key); new = {**S.cfg, **body}
    if set(new) - set(DEFAULT_CFG): raise HTTPException(422, "unknown config key")
    if not (0 <= new["medium"] <= new["high"] <= new["critical"] <= 1): raise HTTPException(422, "need 0<=medium<=high<=critical<=1")
    if new["cluster_min_size"] < 2: raise HTTPException(422, "cluster_min_size must be >= 2")
    db.audit("config_update", dict(role=role, **body)); old, S.cfg = S.cfg, new
    if S.loaded and (old["cluster_risk"], old["cluster_min_size"]) != (new["cluster_risk"], new["cluster_min_size"]): S.refresh()
    return S.cfg

def _latest():
    m, _ = db.experiment_metrics()
    if m: return m
    p = get_settings().artifact_dir / "experiments/synthetic_seed42/metrics.json"   # legacy CLI-produced artifact
    if not p.exists(): raise HTTPException(404, "Not evaluated: launch an experiment or run python3 -m app.ml.experiment")
    return json.loads(p.read_text())

@app.get(f"{API}/experiments/latest/metrics")
def latest_metrics(): return _latest()

EXP_SCENARIOS = ("base", "decay", "decay_hard")

class ExperimentRequest(BaseModel):
    scenario: str = "base"; seed: int = Field(42, ge=0, le=1_000_000)

def _run_experiment(exp_id, scenario, seed):
    from app.ml.experiment import run_experiment
    try:
        db.update_experiment(exp_id, status="running", stage="starting")
        out = run_experiment(seed=seed, scenario=scenario, out_dir=get_settings().artifact_dir / "experiments" / "runs" / exp_id,
                             progress=lambda st: db.update_experiment(exp_id, stage=st))
        db.update_experiment(exp_id, status="done", stage="done", metrics=out)
    except Exception as e:
        db.update_experiment(exp_id, status="failed", stage="failed", error=f"{type(e).__name__}: {e}")

@app.post(f"{API}/experiments", status_code=202)
def launch_experiment(body: ExperimentRequest, bg: BackgroundTasks, x_api_key: str | None = Header(None)):
    role = need_auth(x_api_key)
    if body.scenario not in EXP_SCENARIOS: raise HTTPException(422, f"scenario must be one of {list(EXP_SCENARIOS)}")
    if db.experiment_active(): raise HTTPException(409, "an experiment is already queued or running")
    exp = db.create_experiment(uuid.uuid4().hex[:12], body.scenario, body.seed); db.audit("experiment_launch", dict(id=exp["id"], scenario=body.scenario, seed=body.seed, role=role))
    bg.add_task(_run_experiment, exp["id"], body.scenario, body.seed); return exp

@app.get(f"{API}/experiments")
def list_experiments(): return dict(items=db.list_experiments())

@app.get(API + "/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    e = db.get_experiment(experiment_id)
    if not e: raise HTTPException(404, "experiment not found")
    return e

@app.get(API + "/experiments/{experiment_id}/metrics")
def experiment_metrics(experiment_id: str):
    m, st = db.experiment_metrics(experiment_id)
    if st is None: raise HTTPException(404, "experiment not found")
    if m is None: raise HTTPException(409, f"experiment is {st}; metrics not available")
    return m

def _run_job(job_id, tx_path, id_path):
    from app.pipelines.ingest import ingest_ieee
    try:
        db.update_job(job_id, status="running"); df, q = ingest_ieee(tx_path, id_path); db.update_job(job_id, quality=q, stage="scoring")
        S.load_df(df, "IEEE-CIS upload", 0, tune=True, dataset_id=f"upload:{job_id}", quality=q); _register(); db.update_job(job_id, status="done", stage="done")
    except Exception as e:  # message only; no data in logs
        db.update_job(job_id, status="failed", error=f"{type(e).__name__}: {e}")
    finally:
        for p in (tx_path, id_path):
            if p: Path(p).unlink(missing_ok=True)

async def _save(up: UploadFile, d: str):
    limit = get_settings().max_upload_mb * 1024 * 1024
    path = os.path.join(d, uuid.uuid4().hex + ".csv"); n = 0   # server-chosen filename, never the client's
    with open(path, "wb") as f:
        while chunk := await up.read(1 << 20):
            n += len(chunk)
            if n > limit: f.close(); os.unlink(path); raise HTTPException(413, "file too large")
            f.write(chunk)
    if n == 0: os.unlink(path); raise HTTPException(422, "empty file")
    return path

@app.post(f"{API}/datasets/upload", status_code=202)
async def upload(bg: BackgroundTasks, transactions: UploadFile = File(...), identity: UploadFile | None = File(None),
                 x_api_key: str | None = Header(None)):
    need_auth(x_api_key); d = tempfile.mkdtemp(prefix="fg_")
    tp = await _save(transactions, d); ip = await _save(identity, d) if identity else None
    jid = uuid.uuid4().hex[:12]; job = db.create_job(jid)
    bg.add_task(_run_job, jid, tp, ip); return job

@app.get(API + "/pipelines/jobs/{job_id}")
def job(job_id: str):
    j = db.get_job(job_id)
    if not j: raise HTTPException(404, "job not found")
    return j

@app.get(API + "/pipelines/jobs")
def list_jobs(): return dict(items=db.list_jobs())
