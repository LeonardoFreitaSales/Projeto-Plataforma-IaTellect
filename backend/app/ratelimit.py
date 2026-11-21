"""Controle de tentativas de login e cadastro."""
import threading
import time


class RateLimiter:
    """Limite simples em memoria: no maximo `limit` eventos por `window` segundos."""

    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.hits, self.lock = {}, threading.Lock()

    def _recent(self, key):
        cutoff = time.monotonic() - self.window
        values = [t for t in self.hits.get(key, []) if t > cutoff]
        if values:
            self.hits[key] = values
        else:
            self.hits.pop(key, None)
        return values

    def blocked(self, key):
        with self.lock:
            return len(self._recent(key)) >= self.limit

    def add(self, key):
        with self.lock:
            self._recent(key)
            self.hits.setdefault(key, []).append(time.monotonic())

    def clear(self, key):
        with self.lock:
            self.hits.pop(key, None)


LOGIN_BY_NAME = RateLimiter(5, 600)
LOGIN_BY_IP = RateLimiter(40, 600)
REGISTER_BY_IP = RateLimiter(20, 3600)
