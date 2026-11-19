import os, tempfile
_d = tempfile.mkdtemp(prefix="fgtest_")
os.environ["FG_DATABASE_URL"] = f"sqlite:///{_d}/test.db"; os.environ["FG_ARTIFACT_DIR"] = _d   # isolate tests from real data
os.environ.update(FG_RATE_LIMIT_PER_MINUTE="0", FG_RATE_LIMIT_WRITE_PER_MINUTE="0", FG_AUTH_FAIL_LIMIT="0")   # limits off by default in tests; enabled per test
import pytest
@pytest.fixture(autouse=True)
def _reset_limiter():
    from app.core.ratelimit import limiter; limiter.reset(); yield; limiter.reset()
