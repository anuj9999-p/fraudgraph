from pathlib import Path
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app import db
from app.core.settings import get_settings

config = context.config
if config.config_file_name: fileConfig(config.config_file_name)
url = get_settings().database_url
if url.startswith("sqlite:///"): Path(url[10:]).parent.mkdir(parents=True, exist_ok=True)
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
target_metadata = db.Base.metadata

def run_migrations_offline():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online():
    engine = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()

run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
