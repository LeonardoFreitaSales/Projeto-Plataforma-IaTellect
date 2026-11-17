"""Vercel entrypoint; static files are served only by the application allowlist."""
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('COOKIE_SECURE', '1')
from server import PanelHandler, init_database

_initialization_lock = threading.Lock()
_initialized = False


class handler(PanelHandler):
    def _handle_api(self, parsed, raw):
        global _initialized
        with _initialization_lock:
            if not _initialized:
                init_database()
                _initialized = True
        return super()._handle_api(parsed, raw)
