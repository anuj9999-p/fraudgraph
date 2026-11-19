import pathlib, sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from app import db
from app.main import app

ROOT = pathlib.Path(__file__).resolve().parents[1]
def cfg():
    c = Config(str(ROOT / "alembic.ini")); c.set_main_option("script_location", str(ROOT / "alembic")); return c

def test_migrations_match_models_and_downgrade(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path}/m.db"; monkeypatch.setenv("FG_DATABASE_URL", url); command.upgrade(cfg(), "head"); eng = sa.create_engine(url)
    assert {"cases", "audit_log", "jobs", "experiments"} <= set(sa.inspect(eng).get_table_names())
    with eng.connect() as conn:   # schema drift guard: models changed without a new migration -> this fails
        assert compare_metadata(MigrationContext.configure(conn), db.Base.metadata) == []
    command.downgrade(cfg(), "base"); assert not ({"cases", "jobs", "experiments", "audit_log"} & set(sa.inspect(sa.create_engine(url)).get_table_names()))

def test_ready_requires_migrations_when_autocreate_off(tmp_path, monkeypatch):
    monkeypatch.setenv("FG_DATABASE_URL", f"sqlite:///{tmp_path}/r.db"); monkeypatch.setenv("FG_DB_AUTO_CREATE", "false")
    c = TestClient(app); assert c.get("/ready").status_code == 503
    command.upgrade(cfg(), "head"); assert c.get("/ready").status_code == 200
