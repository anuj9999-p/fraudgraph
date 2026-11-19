"""In-memory sliding-window limiter (per process; resets on restart; not shared across workers)."""
import threading, time
from collections import deque

class Limiter:
    MAX_KEYS = 10000
    def __init__(self): self._h = {}; self._lock = threading.Lock()
    def _dq(self, bucket, key, now, window):
        dq = self._h.setdefault((bucket, key), deque())
        while dq and dq[0] <= now - window: dq.popleft()
        if len(self._h) > self.MAX_KEYS:
            for k in [k for k, v in self._h.items() if not v][: self.MAX_KEYS // 2] or list(self._h)[: self.MAX_KEYS // 2]: self._h.pop(k, None)
            dq = self._h.setdefault((bucket, key), dq)
        return dq
    def allow(self, bucket, key, limit, window=60.0):
        """Record a hit unless over `limit` in the window. limit <= 0 disables. Returns (allowed, retry_after_seconds)."""
        if limit <= 0: return True, 0.0
        with self._lock:
            now = time.monotonic(); dq = self._dq(bucket, key, now, window)
            if len(dq) >= limit: return False, max(0.0, dq[0] + window - now)
            dq.append(now); return True, 0.0
    def hit(self, bucket, key, window=60.0):
        with self._lock: self._dq(bucket, key, time.monotonic(), window).append(time.monotonic())
    def blocked(self, bucket, key, limit, window=60.0):
        if limit <= 0: return False
        with self._lock: return len(self._dq(bucket, key, time.monotonic(), window)) >= limit
    def reset(self):
        with self._lock: self._h.clear()

limiter = Limiter()
