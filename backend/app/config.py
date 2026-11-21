"""Configuração da plataforma."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_MODE = os.environ.get("TEST_MODE") == "1"
DATA_DIR = Path(os.environ["TEST_DATA_DIR"]).resolve() if TEST_MODE and os.environ.get("TEST_DATA_DIR") else ROOT / "data"
DB_FILE = DATA_DIR / "Banco de Dados SQLite.db"
SCHEMA_FILE = ROOT / "sql" / "schema.sql"
HOST = os.environ.get("HOST") or "0.0.0.0"
PORT = int(os.environ.get("PORT") or "3002")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "sim", "yes")
TRUST_PROXY = os.environ.get("TRUST_PROXY", "").lower() in ("1", "true", "sim", "yes")
ALLOWED_ORIGINS = {o.strip().lower() for o in (os.environ.get("ALLOWED_ORIGINS") or "").split(",") if o.strip()}

COOKIE_NAME = "plataforma_v4_sessao"
SESSION_DAYS = 7
PBKDF2_ITERATIONS = 310_000
MAX_BODY = 1_000_000
HISTORY_LIMIT = 500

STATUSES = ("proibido", "restricao", "permitido")
TYPES = ("prova", "trabalho", "atividade", "pesquisa", "outro")
MATRICULA_STATUS = ("pendente", "aprovada", "recusada")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".webp": "image/webp", ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
}
