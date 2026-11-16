"""Vercel entrypoint; static files use the application allowlist."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("COOKIE_SECURE", "1")
from server import PanelHandler, init_database

init_database()


class handler(PanelHandler):
    pass
