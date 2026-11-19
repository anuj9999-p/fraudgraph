"""All runtime configuration comes from environment variables (prefix FG_). Read on every call, so
changing the environment takes effect without code changes. Unset variables use the defaults below."""
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def _s(n, d): v = os.environ.get(n); return d if v is None or v == "" else v
def _f(n, d): return float(_s(n, d))
def _i(n, d): return int(_s(n, d))
def _l(n, d, cast=str): return tuple(cast(x.strip()) for x in str(_s(n, d)).split(",") if x.strip())

@dataclass(frozen=True)
class Settings:
    api_key: str | None; database_url: str; cors_origins: tuple; max_upload_mb: int; log_level: str
    data_dir: Path; artifact_dir: Path; seed: int
    train_frac: float; val_frac: float; tune_taus_days: tuple
    medium: float; high: float; critical: float; cluster_risk: float; cluster_min_size: int; cluster_checkpoints: int; db_auto_create: bool; tune_rule: str; tune_confidence: float; tune_bootstrap: int
    analyst_api_key: str | None; rate_limit_per_minute: int; rate_limit_write_per_minute: int; auth_fail_limit: int; trust_proxy: bool

def get_settings() -> Settings:
    data = Path(_s("FG_DATA_DIR", ROOT / "data")); art = Path(_s("FG_ARTIFACT_DIR", ROOT / "artifacts"))
    s = Settings(api_key=_s("FG_API_KEY", None), database_url=_s("FG_DATABASE_URL", f"sqlite:///{data / 'fraudgraph.db'}"),
        cors_origins=_l("FG_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"), max_upload_mb=_i("FG_MAX_UPLOAD_MB", 300),
        log_level=_s("FG_LOG_LEVEL", "INFO").upper(), data_dir=data, artifact_dir=art, seed=_i("FG_SEED", 42),
        train_frac=_f("FG_TRAIN_FRAC", 0.6), val_frac=_f("FG_VAL_FRAC", 0.2), tune_taus_days=_l("FG_TUNE_TAUS_DAYS", "0.25,1,4,16", float),
        medium=_f("FG_RISK_MEDIUM", 0.3), high=_f("FG_RISK_HIGH", 0.6), critical=_f("FG_RISK_CRITICAL", 0.9),
        cluster_risk=_f("FG_CLUSTER_RISK", 0.6), cluster_min_size=_i("FG_CLUSTER_MIN_SIZE", 3), cluster_checkpoints=_i("FG_CLUSTER_CHECKPOINTS", 30), db_auto_create=_s("FG_DB_AUTO_CREATE", "true").lower() in ("1", "true", "yes"),
        tune_rule=_s("FG_TUNE_RULE", "conservative").lower(), tune_confidence=_f("FG_TUNE_CONFIDENCE", 0.95), tune_bootstrap=_i("FG_TUNE_BOOTSTRAP", 200),
        analyst_api_key=_s("FG_ANALYST_API_KEY", None), rate_limit_per_minute=_i("FG_RATE_LIMIT_PER_MINUTE", 300), rate_limit_write_per_minute=_i("FG_RATE_LIMIT_WRITE_PER_MINUTE", 30),
        auth_fail_limit=_i("FG_AUTH_FAIL_LIMIT", 10), trust_proxy=_s("FG_TRUST_PROXY", "false").lower() in ("1", "true", "yes"))
    if not (0 < s.train_frac and 0 < s.val_frac and s.train_frac + s.val_frac < 1): raise ValueError("FG_TRAIN_FRAC + FG_VAL_FRAC must be < 1 and both > 0")
    if not (0 <= s.medium <= s.high <= s.critical <= 1): raise ValueError("need 0 <= FG_RISK_MEDIUM <= HIGH <= CRITICAL <= 1")
    if s.cluster_min_size < 2 or s.cluster_checkpoints < 1 or not s.tune_taus_days or min(s.tune_taus_days) <= 0: raise ValueError("invalid FG_CLUSTER_MIN_SIZE or FG_TUNE_TAUS_DAYS")
    if s.analyst_api_key and s.analyst_api_key == s.api_key: raise ValueError("FG_ANALYST_API_KEY must differ from FG_API_KEY")
    if min(s.rate_limit_per_minute, s.rate_limit_write_per_minute, s.auth_fail_limit) < 0: raise ValueError("rate limits must be >= 0 (0 disables)")
    if s.tune_rule not in ("conservative", "argmax") or not (0.5 < s.tune_confidence <= 1) or s.tune_bootstrap < 20: raise ValueError("invalid FG_TUNE_RULE / FG_TUNE_CONFIDENCE / FG_TUNE_BOOTSTRAP")
    return s

def atfrp_defaults() -> dict:
    """Optional ATFRP parameter overrides; only variables that are set are applied (others keep dataclass defaults)."""
    spec = {"FG_ATFRP_TAU_DAYS": ("lam", lambda v: 1 / (float(v) * 86400.0)), "FG_ATFRP_TAU_T_HOURS": ("lam_t", lambda v: 1 / (float(v) * 3600.0)),
            "FG_ATFRP_MIN_HISTORY": ("min_history", int), "FG_ATFRP_Z_SCALE": ("z_scale", float), "FG_ATFRP_HIGH_THRESHOLD": ("high_threshold", float),
            "FG_ATFRP_CONC_REF": ("conc_ref", int), "FG_ATFRP_ENTITY_EWMA": ("entity_ewma", float), "FG_ATFRP_MAX_FANOUT": ("max_fanout", int)}
    return {k: f(os.environ[n]) for n, (k, f) in spec.items() if os.environ.get(n)}
