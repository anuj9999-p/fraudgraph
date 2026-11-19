import pytest
from app.core.settings import get_settings, atfrp_defaults
from app.algorithms.atfrp import ATFRPParams

def test_defaults_and_env_overrides(monkeypatch):
    monkeypatch.delenv("FG_API_KEY", raising=False); assert get_settings().api_key is None and get_settings().high == 0.6
    monkeypatch.setenv("FG_API_KEY", "abc"); monkeypatch.setenv("FG_RISK_HIGH", "0.7"); monkeypatch.setenv("FG_CORS_ORIGINS", "http://a.com, http://b.com")
    monkeypatch.setenv("FG_TUNE_TAUS_DAYS", "2,8"); g = get_settings()
    assert g.api_key == "abc" and g.high == 0.7 and g.cors_origins == ("http://a.com", "http://b.com") and g.tune_taus_days == (2.0, 8.0)

def test_invalid_settings_rejected(monkeypatch):
    monkeypatch.setenv("FG_RISK_MEDIUM", "0.9"); monkeypatch.setenv("FG_RISK_HIGH", "0.5")
    with pytest.raises(ValueError): get_settings()
    monkeypatch.delenv("FG_RISK_MEDIUM"); monkeypatch.delenv("FG_RISK_HIGH"); monkeypatch.setenv("FG_TRAIN_FRAC", "0.9"); monkeypatch.setenv("FG_VAL_FRAC", "0.2")
    with pytest.raises(ValueError): get_settings()

def test_atfrp_env_overrides_validated(monkeypatch):
    assert atfrp_defaults() == {}
    monkeypatch.setenv("FG_ATFRP_TAU_DAYS", "2"); monkeypatch.setenv("FG_ATFRP_MAX_FANOUT", "10")
    p = ATFRPParams(**atfrp_defaults()); assert p.lam == pytest.approx(1 / (2 * 86400)) and p.max_fanout == 10
    monkeypatch.setenv("FG_ATFRP_ENTITY_EWMA", "0")
    with pytest.raises(ValueError): ATFRPParams(**atfrp_defaults())
