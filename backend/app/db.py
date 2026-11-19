"""SQLAlchemy persistence for case state, audit trail and upload jobs. URL from FG_DATABASE_URL
(sqlite default; e.g. postgresql+psycopg://user:pass@host/db). Tables are created on first use (no Alembic migrations yet)."""
import json, datetime as dt
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.settings import get_settings

Base = declarative_base(); _state = {"url": None, "S": None}
now = lambda: dt.datetime.now(dt.timezone.utc)

class Case(Base):
    __tablename__ = "cases"; dataset = Column(String, primary_key=True); tx_id = Column(String, primary_key=True)
    status = Column(String, default="open"); notes = Column(Text, default="[]"); updated_at = Column(DateTime)
class Audit(Base):
    __tablename__ = "audit_log"; id = Column(Integer, primary_key=True, autoincrement=True); ts = Column(DateTime); action = Column(String); detail = Column(Text)
class Job(Base):
    __tablename__ = "jobs"; job_id = Column(String, primary_key=True); status = Column(String); stage = Column(String); error = Column(Text)
    quality = Column(Text); created_at = Column(DateTime)

class Experiment(Base):
    __tablename__ = "experiments"; id = Column(String, primary_key=True); scenario = Column(String); seed = Column(Integer); status = Column(String)
    stage = Column(String); error = Column(Text); created_at = Column(DateTime); finished_at = Column(DateTime); metrics = Column(Text)

class Dataset(Base):
    __tablename__ = "datasets"; id = Column(String, primary_key=True); source = Column(String); rows = Column(Integer); weights = Column(String)
    quality = Column(Text); created_at = Column(DateTime)

def session():
    url = get_settings().database_url
    if _state["url"] != url:
        if url.startswith("sqlite:///"): Path(url[10:]).parent.mkdir(parents=True, exist_ok=True)
        eng = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
        if get_settings().db_auto_create: Base.metadata.create_all(eng)      # dev convenience; production: FG_DB_AUTO_CREATE=false + `alembic upgrade head`
        _state.update(url=url, S=sessionmaker(eng, expire_on_commit=False))
    return _state["S"]()

def update_case(dataset, tx_id, status=None, note=None):
    with session() as s:
        c = s.get(Case, (dataset, tx_id)) or Case(dataset=dataset, tx_id=tx_id, status="open", notes="[]")
        if status: c.status = status
        if note: c.notes = json.dumps(json.loads(c.notes) + [note])
        c.updated_at = now(); s.merge(c); s.commit(); return dict(status=c.status, notes=json.loads(c.notes))
def all_cases(dataset):
    with session() as s: return {c.tx_id: dict(status=c.status, notes=json.loads(c.notes)) for c in s.query(Case).filter_by(dataset=dataset)}
def audit(action, detail):
    with session() as s: s.add(Audit(ts=now(), action=action, detail=json.dumps(detail, default=str))); s.commit()

def _job(j): return {k: v for k, v in dict(job_id=j.job_id, status=j.status, stage=j.stage, error=j.error,
                                           quality=json.loads(j.quality) if j.quality else None).items() if v is not None}
def create_job(job_id):
    with session() as s: s.add(Job(job_id=job_id, status="queued", stage="ingest", created_at=now())); s.commit()
    return get_job(job_id)
def update_job(job_id, **f):
    with session() as s:
        j = s.get(Job, job_id)
        for k, v in f.items(): setattr(j, k, json.dumps(v) if k == "quality" else v)
        s.commit()
def get_job(job_id):
    with session() as s: j = s.get(Job, job_id); return _job(j) if j else None
def list_jobs(limit=20):
    with session() as s: return [_job(j) for j in s.query(Job).order_by(Job.created_at.desc()).limit(limit)]

def _exp(e): return {k: v for k, v in dict(id=e.id, scenario=e.scenario, seed=e.seed, status=e.status, stage=e.stage, error=e.error,
                     created_at=e.created_at.isoformat() if e.created_at else None, finished_at=e.finished_at.isoformat() if e.finished_at else None).items() if v is not None}
def create_experiment(exp_id, scenario, seed):
    with session() as s: s.add(Experiment(id=exp_id, scenario=scenario, seed=seed, status="queued", stage="queued", created_at=now())); s.commit()
    return get_experiment(exp_id)
def update_experiment(exp_id, **f):
    with session() as s:
        e = s.get(Experiment, exp_id)
        for k, v in f.items(): setattr(e, k, json.dumps(v, default=float) if k == "metrics" else v)
        if f.get("status") in ("done", "failed"): e.finished_at = now()
        s.commit()
def get_experiment(exp_id):
    with session() as s: e = s.get(Experiment, exp_id); return _exp(e) if e else None
def list_experiments(limit=20):
    with session() as s: return [_exp(e) for e in s.query(Experiment).order_by(Experiment.created_at.desc()).limit(limit)]
def experiment_active():
    with session() as s: return s.query(Experiment).filter(Experiment.status.in_(["queued", "running"])).count() > 0
def experiment_metrics(exp_id=None):
    """Metrics of a given completed experiment, or of the most recent completed one."""
    with session() as s:
        q = s.query(Experiment).filter_by(status="done")
        e = s.get(Experiment, exp_id) if exp_id else q.order_by(Experiment.finished_at.desc()).first()
        return (json.loads(e.metrics) if e and e.metrics and e.status == "done" else None), (e.status if e else None)

def fail_interrupted():
    """Mark queued/running jobs and experiments as failed (the worker that owned them is gone). Assumes a single server process."""
    n = 0
    with session() as s:
        for M in (Job, Experiment):
            for r in s.query(M).filter(M.status.in_(["queued", "running"])):
                r.status = "failed"; r.error = "interrupted by server restart"; n += 1
                if M is Experiment: r.stage = "failed"; r.finished_at = now()
        s.commit()
    return n
def ping():
    from sqlalchemy import text
    with session() as s: s.execute(text("SELECT 1")); s.query(Job).limit(1).all()   # fails if tables are missing (migrations not applied)

def _ds(d): return dict(id=d.id, source=d.source, rows=d.rows, weights=d.weights, quality=json.loads(d.quality) if d.quality else None,
                         created_at=d.created_at.isoformat() if d.created_at else None)
def record_dataset(ds_id, source, rows, weights, quality):
    """Metadata only: the dataset itself lives in memory and must be reloaded after a restart."""
    with session() as s:
        s.merge(Dataset(id=ds_id, source=source, rows=rows, weights=weights, quality=json.dumps(quality, default=float), created_at=now())); s.commit()
def list_datasets(): 
    with session() as s: return [_ds(d) for d in s.query(Dataset).order_by(Dataset.created_at.desc())]
def get_dataset(ds_id):
    with session() as s: d = s.get(Dataset, ds_id); return _ds(d) if d else None
