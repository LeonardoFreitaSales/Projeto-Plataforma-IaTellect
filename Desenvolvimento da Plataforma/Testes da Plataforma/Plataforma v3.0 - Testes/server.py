#!/usr/bin/env python3
"""Plataforma v3.0 - servidor (Python 3 + SQLite, sem bibliotecas externas).

Perfis: admin, professor e aluno.
- admin: tudo (comunicados, usuarios, donos das materias, todas as turmas).
- professor: altera apenas as materias de que e dono; gerencia turmas e
  aprova/recusa matriculas; ve o historico; faz anotacoes privadas.
- aluno: entra so com o nome completo; ve apenas as materias das turmas
  em que a matricula foi aprovada.

Variaveis de ambiente (todas opcionais):
  PORT             porta HTTP (padrao 3001)
  HOST             endereco de escuta (padrao 0.0.0.0)
  ADMIN_NAME       nome do administrador criado na 1a execucao (padrao admin)
  ADMIN_PASSWORD   senha do administrador na 1a execucao (minimo 8 caracteres).
                   Se faltar, uma senha aleatoria e gerada e gravada em
                   data/senha_admin_inicial.txt
  COOKIE_SECURE    1 quando o site usa HTTPS (cookie so trafega por HTTPS)
  TRUST_PROXY      1 quando ha proxy reverso confiavel (usa X-Forwarded-For)
  ALLOWED_ORIGINS  origens extras aceitas em requisicoes de escrita
                   (separadas por virgula), alem do proprio Host

Comandos:
  python server.py                 inicia o servidor
  python server.py --reset-admin   redefine a senha do administrador
"""
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import getpass
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import sys
import threading
import time
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parent
TEST_MODE = os.environ.get("TEST_MODE") == "1"
DATA_DIR = Path(os.environ["TEST_DATA_DIR"]).resolve() if TEST_MODE and os.environ.get("TEST_DATA_DIR") else ROOT / "data"
DB_FILE = DATA_DIR / "Banco de Dados SQLite.db"
SCHEMA_FILE = ROOT / "schema_Banco_de_Dados_SQLite.sql"
HOST = os.environ.get("HOST") or "0.0.0.0"
PORT = int(os.environ.get("PORT") or "3001")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "sim", "yes")
TRUST_PROXY = os.environ.get("TRUST_PROXY", "").lower() in ("1", "true", "sim", "yes")
ALLOWED_ORIGINS = {o.strip().lower() for o in (os.environ.get("ALLOWED_ORIGINS") or "").split(",") if o.strip()}

COOKIE_NAME = "plataforma_v3_testes_sessao"
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
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
}

DB_LOCK = threading.Lock()


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def iso_in(days):
    moment = datetime.now(timezone.utc) + timedelta(days=days)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id():
    return str(uuid.uuid4())


def norm_name(value):
    """Nome sem espacos extras (mantem maiusculas e acentos)."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def key_of(value):
    """Chave de comparacao: sem diferenca de maiuscula/minuscula nem de espacos."""
    return norm_name(value).casefold()


class HTTPError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def bad(message):
    return HTTPError(400, message)


def text(value, name, maximum=5000, required=True):
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise bad(f"{name} deve ser texto.")
    out = value.strip()
    if required and not out:
        raise bad(f"{name} é obrigatório.")
    if len(out) > maximum:
        raise bad(f"{name} excede {maximum} caracteres.")
    return out


def pick(data, key, fallback):
    value = data.get(key)
    return fallback if value is None else value


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


# ----------------------------------------------------------------------
# Senhas e sessoes
# ----------------------------------------------------------------------
def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algo, iterations, salt, expected = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, AttributeError):
        return False


DUMMY_HASH = hash_password("senha-falsa-para-igualar-o-tempo")


def check_new_password(password):
    if not isinstance(password, str) or len(password) < 8:
        raise bad("A senha deve ter pelo menos 8 caracteres.")
    if len(password) > 200:
        raise bad("A senha excede 200 caracteres.")


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_cookie(token, max_age):
    parts = [f"{COOKIE_NAME}={token}", "Path=/", "HttpOnly", "SameSite=Lax", f"Max-Age={max_age}"]
    if COOKIE_SECURE:
        parts.append("Secure")
    return "; ".join(parts)


# ----------------------------------------------------------------------
# Banco de dados
# ----------------------------------------------------------------------
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_DIR.is_symlink() or (hasattr(DATA_DIR, "is_junction") and DATA_DIR.is_junction()):
        raise RuntimeError("A pasta data desta versão não pode ser um atalho para outro local.")
    if DB_FILE.is_symlink():
        raise RuntimeError("O banco desta versão não pode ser um atalho para outro arquivo.")
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn, table):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column(conn, table, column, definition):
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_database(create_admin=True):
    """Cria/atualiza as tabelas (inclusive bancos v2) e garante o admin inicial."""
    conn = connect()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        # Migracao de bancos criados pela v2
        _add_column(conn, "disciplines", "ownerId", "TEXT REFERENCES users(id) ON DELETE SET NULL")
        for column in ("authorId", "authorName", "authorRole", "changes"):
            _add_column(conn, "history", column, "TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_disciplines_owner ON disciplines(ownerId)")
        conn.execute("PRAGMA user_version = 3")
        conn.commit()
        if create_admin:
            ensure_admin(conn)
            conn.commit()
        conn.execute("DELETE FROM sessions WHERE expiresAt < ?", (now_iso(),))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


def ensure_admin(conn):
    if conn.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
        return
    name = norm_name(os.environ.get("ADMIN_NAME") or "admin")
    password = os.environ.get("ADMIN_PASSWORD") or ""
    generated = False
    if not password:
        password, generated = secrets.token_urlsafe(9), True
    if len(password) < 8:
        raise ValueError("ADMIN_PASSWORD deve ter pelo menos 8 caracteres.")
    stamp = now_iso()
    conn.execute(
        "INSERT INTO users (id, name, nameKey, role, passwordHash, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)",
        (new_id(), name, key_of(name), "admin", hash_password(password), stamp, stamp),
    )
    if generated:
        note = DATA_DIR / "senha_admin_inicial.txt"
        note.write_text(
            f"Usuario: {name}\nSenha: {password}\n\nTroque esta senha em 'Usuarios e donos das materias' "
            "e apague este arquivo.\n", encoding="utf-8")
        print(f"Administrador criado. Usuario: {name} | Senha: {password}", flush=True)
        print(f"(a senha tambem foi gravada em {note})", flush=True)
    else:
        print(f"Administrador criado. Usuario: {name}", flush=True)


def reset_admin_password():
    init_database(create_admin=True)
    conn = connect()
    try:
        admin = conn.execute("SELECT id, name FROM users WHERE role = 'admin' ORDER BY createdAt LIMIT 1").fetchone()
        first = getpass.getpass(f"Nova senha para '{admin['name']}' (minimo 8 caracteres): ")
        if first != getpass.getpass("Repita a senha: "):
            print("As senhas nao conferem.")
            return 1
        if len(first) < 8:
            print("A senha deve ter pelo menos 8 caracteres.")
            return 1
        conn.execute("UPDATE users SET passwordHash = ?, updatedAt = ? WHERE id = ?", (hash_password(first), now_iso(), admin["id"]))
        conn.execute("DELETE FROM sessions WHERE userId = ?", (admin["id"],))
        conn.commit()
        print("Senha redefinida.")
        return 0
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Historico (trilha de auditoria)
# ----------------------------------------------------------------------
FIELDS = {
    "discipline": ["name", "code", "instructor", "ownerId"],
    "policy": ["disciplineId", "activityType", "activityName", "status", "conditions", "details", "source"],
    "announcement": ["title", "message", "active"],
    "turma": ["name"],
    "user": ["name", "role"],
    "matricula": ["status"],
}


def _show(value):
    if value is None:
        return None
    if value is True:
        return "sim"
    if value is False:
        return "não"
    return str(value)[:200]


def _field_value(conn, field, value):
    if field == "disciplineId" and value is not None:
        row = conn.execute("SELECT name FROM disciplines WHERE id = ?", (value,)).fetchone()
        return _show(row["name"] if row else value)
    if field == "ownerId" and value is not None:
        row = conn.execute("SELECT name FROM users WHERE id = ?", (value,)).fetchone()
        return _show(row["name"] if row else value)
    return _show(value)


def diff(conn, entity, before, after):
    changes = []
    for field in FIELDS.get(entity, []):
        old = before.get(field) if before is not None else None
        new = after.get(field) if after is not None else None
        if before is not None and after is not None:
            if old == new or (old is None and new is None):
                continue
        else:
            value = old if before is not None else new
            if value is None or value == "":
                continue
        changes.append({
            "field": field,
            "from": _field_value(conn, field, old) if before is not None else None,
            "to": _field_value(conn, field, new) if after is not None else None,
        })
    return changes


def log(conn, user, action, entity, entity_id, summary, before=None, after=None):
    changes = diff(conn, entity, before, after)
    conn.execute(
        "INSERT INTO history (id, action, entity, entityId, summary, createdAt, authorId, authorName, authorRole, changes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (new_id(), action, entity, entity_id, summary, now_iso(), user["id"], user["name"], user["role"],
         json.dumps(changes, ensure_ascii=False)),
    )
    conn.execute(
        "DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY createdAt DESC, rowid DESC LIMIT ?)",
        (HISTORY_LIMIT,),
    )


# ----------------------------------------------------------------------
# Permissoes
# ----------------------------------------------------------------------
def require_role(user, *roles):
    if user["role"] not in roles:
        raise HTTPError(403, "Sem permissão para esta ação.")


def visible_ids(conn, user):
    """Conjunto de materias que o usuario pode ver; None = todas (admin)."""
    if user["role"] == "admin":
        return None
    if user["role"] == "professor":
        rows = conn.execute("SELECT id FROM disciplines WHERE ownerId = ?", (user["id"],))
    else:
        rows = conn.execute(
            "SELECT DISTINCT td.disciplineId AS id FROM matriculas m "
            "JOIN turma_disciplines td ON td.turmaId = m.turmaId "
            "WHERE m.studentId = ? AND m.status = 'aprovada'", (user["id"],))
    return {row["id"] for row in rows}


def require_visible(conn, user, discipline_id):
    visible = visible_ids(conn, user)
    if visible is not None and discipline_id not in visible:
        raise HTTPError(404, "Disciplina não encontrada.")


def get_discipline(conn, discipline_id):
    row = conn.execute("SELECT * FROM disciplines WHERE id = ?", (discipline_id,)).fetchone()
    if row is None:
        raise HTTPError(404, "Disciplina não encontrada.")
    return row


def require_edit(conn, user, discipline_id):
    """Admin altera tudo; professor altera so as materias de que e dono (senao 403)."""
    row = get_discipline(conn, discipline_id) if isinstance(discipline_id, str) else None
    if row is None:
        raise HTTPError(404, "Disciplina não encontrada.")
    if user["role"] == "admin" or (user["role"] == "professor" and row["ownerId"] == user["id"]):
        return row
    raise HTTPError(403, "Você só pode alterar as suas próprias matérias.")


def can_edit(conn, user, discipline_id):
    try:
        require_edit(conn, user, discipline_id)
        return True
    except HTTPError:
        return False


def can_manage_turma(conn, user, turma):
    if user["role"] == "admin":
        return True
    if user["role"] != "professor":
        return False
    if turma["createdBy"] == user["id"]:
        return True
    return conn.execute(
        "SELECT 1 FROM turma_disciplines td JOIN disciplines d ON d.id = td.disciplineId "
        "WHERE td.turmaId = ? AND d.ownerId = ? LIMIT 1", (turma["id"], user["id"])).fetchone() is not None


def require_manage_turma(conn, user, turma):
    if not can_manage_turma(conn, user, turma):
        raise HTTPError(403, "Você não gerencia esta turma.")


def get_turma(conn, turma_id):
    row = conn.execute("SELECT * FROM turmas WHERE id = ?", (turma_id,)).fetchone()
    if row is None:
        raise HTTPError(404, "Turma não encontrada.")
    return row


def turma_disciplines(conn, turma_id):
    return [dict(r) for r in conn.execute(
        "SELECT d.id, d.name, d.ownerId FROM turma_disciplines td "
        "JOIN disciplines d ON d.id = td.disciplineId WHERE td.turmaId = ? ORDER BY td.rowid", (turma_id,))]


# ----------------------------------------------------------------------
# Contexto da requisicao
# ----------------------------------------------------------------------
class Ctx:
    def __init__(self, conn, handler, method, parts, query, raw_body):
        self.conn, self.handler, self.method = conn, handler, method
        self.parts, self.query, self.raw_body = parts, query, raw_body
        self.cookies = []
        self.user = None
        self._body = None
        cookie = SimpleCookie()
        try:
            cookie.load(handler.headers.get("Cookie") or "")
        except Exception:
            cookie = SimpleCookie()
        morsel = cookie.get(COOKIE_NAME)
        self.token = morsel.value if morsel else None
        self.token_hash = token_digest(self.token) if self.token else None

    @property
    def ip(self):
        if TRUST_PROXY:
            forwarded = (self.handler.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
            if forwarded:
                return forwarded
        return self.handler.client_address[0]

    @property
    def body(self):
        if self._body is None:
            if not self.raw_body:
                self._body = {}
            else:
                try:
                    parsed = json.loads(self.raw_body.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise bad("JSON inválido.")
                if not isinstance(parsed, dict):
                    raise bad("JSON inválido.")
                self._body = parsed
        return self._body

    def q(self, name):
        values = parse_qs(self.query, keep_blank_values=True).get(name)
        return values[0] if values else None

    def authenticate(self):
        if not self.token_hash:
            return None
        return self.conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.userId WHERE s.tokenHash = ? AND s.expiresAt > ?",
            (self.token_hash, now_iso())).fetchone()

    def open_session(self, user_id):
        token = secrets.token_urlsafe(32)
        self.conn.execute("DELETE FROM sessions WHERE expiresAt < ?", (now_iso(),))
        self.conn.execute(
            "INSERT INTO sessions (tokenHash, userId, createdAt, expiresAt) VALUES (?,?,?,?)",
            (token_digest(token), user_id, now_iso(), iso_in(SESSION_DAYS)))
        self.cookies.append(session_cookie(token, SESSION_DAYS * 86400))


def public_user(row):
    return {"id": row["id"], "name": row["name"], "role": row["role"]}


# ----------------------------------------------------------------------
# Rotas
# ----------------------------------------------------------------------
NOT_FOUND = HTTPError(404, "Rota de API não encontrada.")


def api(ctx):
    parts = ctx.parts
    resource = parts[0] if parts else None
    ident = parts[1] if len(parts) > 1 else None
    sub = parts[2] if len(parts) > 2 else None
    sid = parts[3] if len(parts) > 3 else None
    method, conn = ctx.method, ctx.conn

    if resource == "health" and method == "GET":
        return 200, {"status": "ok", "time": now_iso()}
    if resource == "public":
        if ident == "turmas" and method == "GET":
            return 200, public_turmas(conn)
        raise NOT_FOUND
    if resource == "auth":
        return auth_routes(ctx, ident)

    user = ctx.authenticate()
    if user is None:
        raise HTTPError(401, "Faça login para continuar.")
    ctx.user = user

    if resource == "me":
        return 200, public_user(user)
    if resource == "dashboard":
        return 200, dashboard(conn, user)
    if resource == "disciplines":
        return disciplines(ctx, user, ident)
    if resource == "policies":
        return policies(ctx, user, ident)
    if resource == "announcements":
        return announcements(ctx, user, ident)
    if resource == "history" and method == "GET":
        require_role(user, "professor", "admin")
        return 200, history(ctx)
    if resource == "ai-check" and method == "POST":
        return 200, ai_check(ctx, user)
    if resource == "users":
        return users(ctx, user, ident, sub)
    if resource == "turmas":
        return turmas(ctx, user, ident, sub, sid)
    if resource == "matriculas" and ident and method in ("PUT", "PATCH"):
        return matricula_update(ctx, user, ident)
    if resource == "notas" and ident and method == "PUT":
        return nota_save(ctx, user, ident)
    raise NOT_FOUND


# ---- publico e autenticacao ------------------------------------------
def public_turmas(conn):
    result = []
    for turma in conn.execute("SELECT id, name FROM turmas ORDER BY rowid"):
        names = ", ".join(d["name"] for d in turma_disciplines(conn, turma["id"]))
        result.append({"id": turma["id"], "name": turma["name"], "disciplines": names})
    return result


def auth_routes(ctx, action):
    conn, data = ctx.conn, None
    if action == "logout" and ctx.method == "POST":
        if ctx.token_hash:
            conn.execute("DELETE FROM sessions WHERE tokenHash = ?", (ctx.token_hash,))
        ctx.cookies.append(session_cookie("", 0))
        return 200, {"ok": True}
    if ctx.method != "POST" or action not in ("login", "register"):
        raise NOT_FOUND
    data = ctx.body
    name = norm_name(text(data.get("name"), "Nome", 180))
    if not name:
        raise bad("Nome é obrigatório.")

    if action == "login":
        name_key = f"{key_of(name)}|{ctx.ip}"
        if LOGIN_BY_NAME.blocked(name_key) or LOGIN_BY_IP.blocked(ctx.ip):
            raise HTTPError(429, "Muitas tentativas. Aguarde alguns minutos e tente de novo.")
        row = conn.execute("SELECT * FROM users WHERE nameKey = ?", (key_of(name),)).fetchone()
        password = data.get("password") if isinstance(data.get("password"), str) else ""
        ok = False
        if row is None:
            verify_password(password, DUMMY_HASH)  # iguala o tempo de resposta
        elif row["role"] == "aluno" and not row["passwordHash"]:
            ok = True
        elif row["passwordHash"]:
            ok = verify_password(password, row["passwordHash"])
        if not ok:
            LOGIN_BY_NAME.add(name_key)
            LOGIN_BY_IP.add(ctx.ip)
            raise HTTPError(401, "Nome ou senha incorretos.")
        LOGIN_BY_NAME.clear(name_key)
        ctx.open_session(row["id"])
        return 200, public_user(row)

    # register (aluno)
    if REGISTER_BY_IP.blocked(ctx.ip):
        raise HTTPError(429, "Muitos cadastros deste endereço. Tente mais tarde.")
    turma_id = data.get("turmaId")
    turma = conn.execute("SELECT * FROM turmas WHERE id = ?", (turma_id,)).fetchone() if isinstance(turma_id, str) else None
    if turma is None:
        raise bad("Escolha uma turma válida.")
    if len(name.split(" ")) < 2:
        raise bad("Informe o nome completo.")
    if conn.execute("SELECT 1 FROM users WHERE nameKey = ?", (key_of(name),)).fetchone():
        raise HTTPError(409, "Já existe um usuário com esse nome.")
    REGISTER_BY_IP.add(ctx.ip)
    stamp, user_id = now_iso(), new_id()
    conn.execute(
        "INSERT INTO users (id, name, nameKey, role, passwordHash, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)",
        (user_id, name, key_of(name), "aluno", None, stamp, stamp))
    matricula_id = new_id()
    conn.execute(
        "INSERT INTO matriculas (id, turmaId, studentId, status, createdAt, updatedAt) VALUES (?,?,?,?,?,?)",
        (matricula_id, turma["id"], user_id, "pendente", stamp, stamp))
    student = {"id": user_id, "name": name, "role": "aluno"}
    log(conn, student, "created", "matricula", matricula_id,
        f"Cadastro de aluno: {name} pediu matrícula na turma {turma['name']}", None, {"status": "pendente"})
    ctx.open_session(user_id)
    return 201, student


# ---- painel ----------------------------------------------------------
def dashboard(conn, user):
    visible = visible_ids(conn, user)
    counts = {"proibido": 0, "restricao": 0, "permitido": 0}
    total = 0
    for row in conn.execute("SELECT disciplineId, status FROM policies"):
        if visible is None or row["disciplineId"] in visible:
            counts[row["status"]] += 1
            total += 1
    disciplines_count = conn.execute("SELECT COUNT(*) FROM disciplines").fetchone()[0] if visible is None else len(visible)
    items = [announcement_view(r) for r in conn.execute(
        "SELECT * FROM announcements WHERE active = 1 ORDER BY rowid LIMIT 5")]
    return {"disciplines": disciplines_count, "policies": total, "changedSinceLastVisit": 0,
            "distribution": counts, "announcements": items}


# ---- disciplinas -----------------------------------------------------
def clean_owner(conn, value):
    if value is None or value == "":
        return None
    row = conn.execute("SELECT id, role FROM users WHERE id = ?", (value,)).fetchone() if isinstance(value, str) else None
    if row is None or row["role"] not in ("professor", "admin"):
        raise bad("Responsável inválido.")
    return row["id"]


def discipline_name_taken(conn, name, exclude_id=None):
    wanted = key_of(name)
    return any(key_of(r["name"]) == wanted and r["id"] != exclude_id
               for r in conn.execute("SELECT id, name FROM disciplines"))


def discipline_dict(row):
    return {k: row[k] for k in ("id", "name", "code", "instructor", "createdAt", "updatedAt", "ownerId")}


def policy_view(conn, policy_id):
    return dict(conn.execute(
        "SELECT p.*, d.name AS disciplineName FROM policies p LEFT JOIN disciplines d ON d.id = p.disciplineId "
        "WHERE p.id = ?", (policy_id,)).fetchone())


def policy_rows(conn, where="", args=()):
    return [dict(r) for r in conn.execute(
        "SELECT p.*, d.name AS disciplineName FROM policies p LEFT JOIN disciplines d ON d.id = p.disciplineId "
        f"{where} ORDER BY p.rowid", args)]


def disciplines(ctx, user, ident):
    conn, method, data = ctx.conn, ctx.method, None
    if ident is None:
        if method == "GET":
            visible = visible_ids(conn, user)
            rows = conn.execute(
                "SELECT d.*, o.name AS ownerName FROM disciplines d LEFT JOIN users o ON o.id = d.ownerId ORDER BY d.rowid")
            return 200, [dict(r) for r in rows if visible is None or r["id"] in visible]
        if method == "POST":
            require_role(user, "admin")
            data = ctx.body
            name = text(data.get("name"), "name", 180)
            if discipline_name_taken(conn, name):
                raise HTTPError(409, "Já existe uma disciplina com esse nome.")
            item = {"id": new_id(), "name": name, "code": text(data.get("code"), "code", 40, False),
                    "instructor": text(data.get("instructor"), "instructor", 180, False),
                    "createdAt": now_iso(), "updatedAt": now_iso(), "ownerId": clean_owner(conn, data.get("ownerId"))}
            conn.execute("INSERT INTO disciplines (id, name, code, instructor, createdAt, updatedAt, ownerId) VALUES (?,?,?,?,?,?,?)",
                         (item["id"], item["name"], item["code"], item["instructor"], item["createdAt"], item["updatedAt"], item["ownerId"]))
            log(conn, user, "created", "discipline", item["id"], f"Disciplina criada: {name}", None, item)
            return 201, item
        raise NOT_FOUND

    current = get_discipline(conn, ident)
    require_visible(conn, user, ident)
    if method == "GET":
        result = discipline_dict(current)
        result["policies"] = policy_rows(conn, "WHERE p.disciplineId = ?", (ident,))
        return 200, result
    require_edit(conn, user, ident)

    if method in ("PUT", "PATCH"):
        data = ctx.body
        name = text(pick(data, "name", current["name"]), "name", 180)
        if discipline_name_taken(conn, name, ident):
            raise HTTPError(409, "Já existe uma disciplina com esse nome.")
        changes = {"name": name,
                   "code": text(pick(data, "code", current["code"]), "code", 40, False),
                   "instructor": text(pick(data, "instructor", current["instructor"]), "instructor", 180, False),
                   "updatedAt": now_iso(), "ownerId": current["ownerId"]}
        if "ownerId" in data:
            require_role(user, "admin")
            changes["ownerId"] = clean_owner(conn, data.get("ownerId"))
        before = dict(current)
        conn.execute("UPDATE disciplines SET name=?, code=?, instructor=?, updatedAt=?, ownerId=? WHERE id=?",
                     (changes["name"], changes["code"], changes["instructor"], changes["updatedAt"], changes["ownerId"], ident))
        after = discipline_dict(get_discipline(conn, ident))
        log(conn, user, "updated", "discipline", ident, f"Disciplina atualizada: {name}", before, after)
        return 200, after
    if method == "DELETE":
        require_role(user, "admin")
        if conn.execute("SELECT 1 FROM policies WHERE disciplineId = ? LIMIT 1", (ident,)).fetchone():
            raise HTTPError(409, "Remova ou mova as políticas desta disciplina antes de excluí-la.")
        conn.execute("DELETE FROM disciplines WHERE id = ?", (ident,))
        log(conn, user, "deleted", "discipline", ident, f"Disciplina removida: {current['name']}", dict(current), None)
        return 200, {"deleted": True, "id": ident}
    raise NOT_FOUND


# ---- politicas -------------------------------------------------------
def policy_data(data, current):
    def get(key, default=""):
        value = data.get(key)
        if value is not None:
            return value
        value = current.get(key)
        return default if value is None else value

    status, activity_type = get("status", None), get("activityType", "outro")
    if not isinstance(status, str) or status not in STATUSES:
        raise bad("status deve ser proibido, restricao ou permitido.")
    if not isinstance(activity_type, str) or activity_type not in TYPES:
        raise bad("Tipo de atividade inválido.")
    discipline_id = get("disciplineId", None)
    if not isinstance(discipline_id, str):
        raise bad("disciplineId é obrigatório.")
    return {"disciplineId": discipline_id, "activityType": activity_type,
            "activityName": text(get("activityName", None), "activityName", 180), "status": status,
            "conditions": text(get("conditions"), "conditions", 3000, False),
            "details": text(get("details"), "details", 5000, False),
            "source": text(get("source"), "source", 500, False), "updatedAt": now_iso()}


def policies(ctx, user, ident):
    conn, method = ctx.conn, ctx.method
    if ident is None:
        if method == "GET":
            visible = visible_ids(conn, user)
            items = [p for p in policy_rows(conn) if visible is None or p["disciplineId"] in visible]
            discipline_id, status, term = ctx.q("disciplineId"), ctx.q("status"), (ctx.q("q") or "").casefold()
            if discipline_id:
                items = [p for p in items if p["disciplineId"] == discipline_id]
            if status:
                items = [p for p in items if p["status"] == status]
            if term:
                items = [p for p in items if term in " ".join(
                    str(p.get(k) or "") for k in ("activityName", "details", "conditions", "disciplineName")).casefold()]
            return 200, items
        if method == "POST":
            data = policy_data(ctx.body, {})
            require_edit(conn, user, data["disciplineId"])
            item = {"id": new_id(), **data, "createdAt": now_iso()}
            conn.execute(
                "INSERT INTO policies (id, disciplineId, activityType, activityName, status, conditions, details, source, createdAt, updatedAt) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (item["id"], item["disciplineId"], item["activityType"], item["activityName"], item["status"],
                 item["conditions"], item["details"], item["source"], item["createdAt"], item["updatedAt"]))
            log(conn, user, "created", "policy", item["id"], f"Política criada: {item['activityName']}", None, item)
            return 201, policy_view(conn, item["id"])
        raise NOT_FOUND

    row = conn.execute("SELECT * FROM policies WHERE id = ?", (ident,)).fetchone()
    if row is None:
        raise HTTPError(404, "Política não encontrada.")
    current = dict(row)
    require_visible(conn, user, current["disciplineId"])
    if method == "GET":
        return 200, policy_view(conn, ident)
    require_edit(conn, user, current["disciplineId"])
    if method in ("PUT", "PATCH"):
        data = policy_data(ctx.body, current)
        require_edit(conn, user, data["disciplineId"])
        conn.execute(
            "UPDATE policies SET disciplineId=?, activityType=?, activityName=?, status=?, conditions=?, details=?, source=?, updatedAt=? WHERE id=?",
            (data["disciplineId"], data["activityType"], data["activityName"], data["status"], data["conditions"],
             data["details"], data["source"], data["updatedAt"], ident))
        log(conn, user, "updated", "policy", ident, f"Política atualizada: {data['activityName']}", current, {**current, **data})
        return 200, policy_view(conn, ident)
    if method == "DELETE":
        conn.execute("DELETE FROM policies WHERE id = ?", (ident,))
        log(conn, user, "deleted", "policy", ident, f"Política removida: {current['activityName']}", current, None)
        return 200, {"deleted": True, "id": ident}
    raise NOT_FOUND


# ---- comunicados -----------------------------------------------------
def announcement_view(row):
    result = dict(row)
    result["active"] = bool(result["active"])
    return result


def announcements(ctx, user, ident):
    conn, method = ctx.conn, ctx.method
    if ident is None and method == "GET":
        everything = ctx.q("all") == "true" and user["role"] == "admin"
        where = "" if everything else "WHERE active = 1"
        return 200, [announcement_view(r) for r in conn.execute(f"SELECT * FROM announcements {where} ORDER BY rowid")]
    require_role(user, "admin")
    if ident is None and method == "POST":
        data = ctx.body
        item = {"id": new_id(), "title": text(data.get("title"), "title", 180), "message": text(data.get("message"), "message", 3000),
                "active": data.get("active") is not False, "createdAt": now_iso(), "updatedAt": now_iso()}
        conn.execute("INSERT INTO announcements (id, title, message, active, createdAt, updatedAt) VALUES (?,?,?,?,?,?)",
                     (item["id"], item["title"], item["message"], int(item["active"]), item["createdAt"], item["updatedAt"]))
        log(conn, user, "created", "announcement", item["id"], f"Comunicado criado: {item['title']}", None, item)
        return 201, item
    if ident:
        row = conn.execute("SELECT * FROM announcements WHERE id = ?", (ident,)).fetchone()
        if row is None:
            raise HTTPError(404, "Comunicado não encontrado.")
        current = announcement_view(row)
        if method in ("PUT", "PATCH"):
            data = ctx.body
            active = pick(data, "active", current["active"])
            item = {"title": text(pick(data, "title", current["title"]), "title", 180),
                    "message": text(pick(data, "message", current["message"]), "message", 3000),
                    "active": bool(active), "updatedAt": now_iso()}
            conn.execute("UPDATE announcements SET title=?, message=?, active=?, updatedAt=? WHERE id=?",
                         (item["title"], item["message"], int(item["active"]), item["updatedAt"], ident))
            log(conn, user, "updated", "announcement", ident, f"Comunicado atualizado: {item['title']}", current, item)
            return 200, announcement_view(conn.execute("SELECT * FROM announcements WHERE id = ?", (ident,)).fetchone())
        if method == "DELETE":
            conn.execute("DELETE FROM announcements WHERE id = ?", (ident,))
            log(conn, user, "deleted", "announcement", ident, f"Comunicado removido: {current['title']}", current, None)
            return 200, {"deleted": True, "id": ident}
    raise NOT_FOUND


# ---- historico e consulta "Posso usar IA?" ------------------------------
def history(ctx):
    try:
        number = float(ctx.q("limit") or 50)
    except ValueError:
        number = 50.0
    limit = 50 if number != number else int(max(1, min(HISTORY_LIMIT, number)))
    result = []
    for row in ctx.conn.execute("SELECT * FROM history ORDER BY createdAt DESC, rowid DESC LIMIT ?", (limit,)):
        item = dict(row)
        try:
            item["changes"] = json.loads(item["changes"]) if item.get("changes") else []
        except ValueError:
            item["changes"] = []
        result.append(item)
    return result


def ai_check(ctx, user):
    conn, data = ctx.conn, ctx.body
    discipline_id = text(data.get("disciplineId"), "disciplineId", 100)
    activity_type = text(data.get("activityType"), "activityType", 40)
    require_visible(conn, user, discipline_id)
    get_discipline(conn, discipline_id)
    if activity_type not in TYPES:
        raise bad("Tipo de atividade inválido.")
    matches = [p for p in policy_rows(conn, "WHERE p.disciplineId = ?", (discipline_id,))
               if p["activityType"] in (activity_type, "outro")]
    if not matches:
        decision = "sem_politica"
    elif any(p["status"] == "proibido" for p in matches):
        decision = "proibido"
    elif any(p["status"] == "restricao" for p in matches):
        decision = "restricao"
    else:
        decision = "permitido"
    return {"disciplineId": discipline_id, "activityType": activity_type, "policies": matches, "decision": decision,
            "message": None if matches else "Nenhuma política cadastrada para esta atividade."}


# ---- usuarios (admin) ------------------------------------------------
def users(ctx, user, ident, sub):
    conn, method = ctx.conn, ctx.method
    require_role(user, "admin")
    if ident is None and method == "GET":
        rows = conn.execute("SELECT id, name, role FROM users WHERE role != 'aluno' ORDER BY role, name COLLATE NOCASE")
        return 200, [dict(r) for r in rows]
    if ident is None and method == "POST":
        data = ctx.body
        name = norm_name(text(data.get("name"), "name", 180))
        if not name:
            raise bad("name é obrigatório.")
        check_new_password(data.get("password"))
        if conn.execute("SELECT 1 FROM users WHERE nameKey = ?", (key_of(name),)).fetchone():
            raise HTTPError(409, "Já existe um usuário com esse nome.")
        stamp, user_id = now_iso(), new_id()
        conn.execute(
            "INSERT INTO users (id, name, nameKey, role, passwordHash, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)",
            (user_id, name, key_of(name), "professor", hash_password(data["password"]), stamp, stamp))
        log(conn, user, "created", "user", user_id, f"Professor cadastrado: {name}", None, {"name": name, "role": "professor"})
        return 201, {"id": user_id, "name": name, "role": "professor"}
    if ident and sub == "password" and method == "PUT":
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role != 'aluno'", (ident,)).fetchone()
        if target is None:
            raise HTTPError(404, "Usuário não encontrado.")
        check_new_password(ctx.body.get("password"))
        conn.execute("UPDATE users SET passwordHash = ?, updatedAt = ? WHERE id = ?",
                     (hash_password(ctx.body["password"]), now_iso(), ident))
        # encerra as sessoes antigas do usuario (mantem a sessao atual de quem redefiniu a propria senha)
        conn.execute("DELETE FROM sessions WHERE userId = ? AND tokenHash != ?", (ident, ctx.token_hash or ""))
        log(conn, user, "updated", "user", ident, f"Senha redefinida pelo administrador: {target['name']}")
        return 200, {"ok": True}
    raise NOT_FOUND


# ---- turmas, matriculas e anotacoes ---------------------------------------
def turmas(ctx, user, ident, sub, sid):
    conn, method = ctx.conn, ctx.method
    if ident is None:
        if method == "GET":
            return 200, turmas_list(conn, user)
        if method == "POST":
            require_role(user, "professor", "admin")
            name = norm_name(text(ctx.body.get("name"), "name", 120))
            if not name:
                raise bad("name é obrigatório.")
            if conn.execute("SELECT 1 FROM turmas WHERE nameKey = ?", (key_of(name),)).fetchone():
                raise HTTPError(409, "Já existe uma turma com esse nome.")
            turma = {"id": new_id(), "name": name, "createdBy": user["id"], "createdAt": now_iso()}
            conn.execute("INSERT INTO turmas (id, name, nameKey, createdBy, createdAt) VALUES (?,?,?,?,?)",
                         (turma["id"], name, key_of(name), user["id"], turma["createdAt"]))
            log(conn, user, "created", "turma", turma["id"], f"Turma criada: {name}", None, turma)
            return 201, {"id": turma["id"], "name": name}
        raise NOT_FOUND

    turma = get_turma(conn, ident)
    if sub == "disciplines" and sid and method in ("PUT", "DELETE"):
        discipline = require_edit(conn, user, sid)
        if user["role"] == "professor":
            require_manage_turma(conn, user, turma)
        conn.execute("DELETE FROM turma_disciplines WHERE turmaId = ? AND disciplineId = ?", (ident, sid))
        if method == "PUT":
            conn.execute("INSERT INTO turma_disciplines (turmaId, disciplineId) VALUES (?,?)", (ident, sid))
        verb = "vinculada à" if method == "PUT" else "desvinculada da"
        log(conn, user, "updated", "turma", ident, f"Matéria {discipline['name']} {verb} turma {turma['name']}")
        return 200, {"ok": True}
    require_manage_turma(conn, user, turma)
    if sub == "enrollments" and method == "GET":
        rows = conn.execute(
            "SELECT m.id, m.studentId, m.status, m.createdAt, u.name AS studentName FROM matriculas m "
            "JOIN users u ON u.id = m.studentId WHERE m.turmaId = ? ORDER BY m.createdAt, m.rowid", (ident,))
        return 200, [dict(r) for r in rows]
    if sub == "notes" and method == "GET":
        require_role(user, "professor")
        rows = conn.execute(
            "SELECT n.studentId, n.text FROM notas_privadas n JOIN matriculas m ON m.studentId = n.studentId "
            "WHERE n.professorId = ? AND m.turmaId = ?", (user["id"], ident))
        return 200, {r["studentId"]: r["text"] for r in rows}
    if sub is None and method == "DELETE":
        if user["role"] != "admin" and turma["createdBy"] != user["id"]:
            raise HTTPError(403, "Só quem criou a turma (ou um administrador) pode excluí-la.")
        conn.execute("DELETE FROM turmas WHERE id = ?", (ident,))
        log(conn, user, "deleted", "turma", ident, f"Turma removida: {turma['name']}", dict(turma), None)
        return 200, {"deleted": True, "id": ident}
    raise NOT_FOUND


def turmas_list(conn, user):
    if user["role"] == "aluno":
        rows = conn.execute(
            "SELECT t.id, t.name, m.status FROM matriculas m JOIN turmas t ON t.id = m.turmaId "
            "WHERE m.studentId = ? ORDER BY m.createdAt, m.rowid", (user["id"],))
        return [{"id": r["id"], "name": r["name"], "status": r["status"],
                 "disciplines": turma_disciplines(conn, r["id"]) if r["status"] == "aprovada" else []} for r in rows]
    result = []
    for turma in conn.execute("SELECT * FROM turmas ORDER BY rowid").fetchall():
        if not can_manage_turma(conn, user, turma):
            continue
        shown = [d for d in turma_disciplines(conn, turma["id"]) if user["role"] == "admin" or d["ownerId"] == user["id"]]
        pending = conn.execute("SELECT COUNT(*) FROM matriculas WHERE turmaId = ? AND status = 'pendente'", (turma["id"],)).fetchone()[0]
        result.append({"id": turma["id"], "name": turma["name"], "createdBy": turma["createdBy"],
                       "disciplines": shown, "manage": True, "pendentes": pending})
    return result


def matricula_update(ctx, user, ident):
    conn = ctx.conn
    row = conn.execute(
        "SELECT m.*, u.name AS studentName FROM matriculas m JOIN users u ON u.id = m.studentId WHERE m.id = ?", (ident,)).fetchone()
    if row is None:
        raise HTTPError(404, "Matrícula não encontrada.")
    turma = get_turma(conn, row["turmaId"])
    require_manage_turma(conn, user, turma)
    status = ctx.body.get("status")
    if not isinstance(status, str) or status not in MATRICULA_STATUS:
        raise bad("status inválido.")
    conn.execute("UPDATE matriculas SET status = ?, updatedAt = ? WHERE id = ?", (status, now_iso(), ident))
    log(conn, user, "updated", "matricula", ident, f"Matrícula {status}: {row['studentName']} na turma {turma['name']}",
        {"status": row["status"]}, {"status": status})
    return 200, {"id": ident, "status": status}


def nota_save(ctx, user, student_id):
    conn = ctx.conn
    require_role(user, "professor")
    student = conn.execute("SELECT id FROM users WHERE id = ? AND role = 'aluno'", (student_id,)).fetchone()
    allowed = False
    if student:
        for turma in conn.execute(
                "SELECT t.* FROM turmas t JOIN matriculas m ON m.turmaId = t.id WHERE m.studentId = ?", (student_id,)):
            if can_manage_turma(conn, user, turma):
                allowed = True
                break
    if not allowed:
        raise HTTPError(404, "Aluno não encontrado nas suas turmas.")
    value = text(ctx.body.get("text"), "text", 2000, False)
    if value:
        conn.execute(
            "INSERT INTO notas_privadas (professorId, studentId, text, updatedAt) VALUES (?,?,?,?) "
            "ON CONFLICT(professorId, studentId) DO UPDATE SET text = excluded.text, updatedAt = excluded.updatedAt",
            (user["id"], student_id, value, now_iso()))
    else:
        conn.execute("DELETE FROM notas_privadas WHERE professorId = ? AND studentId = ?", (user["id"], student_id))
    return 200, {"ok": True}


# ----------------------------------------------------------------------
# Servidor HTTP
# ----------------------------------------------------------------------
STATIC_FILES = {"/": "index.html", "/index.html": "index.html"}


class PanelHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "PainelPoliticas"

    def log_message(self, format_string, *args):
        return

    def _dispatch(self):
        try:
            parsed = urlsplit(self.path)
            raw = self._read_raw()
            if parsed.path == "/api" or parsed.path.startswith("/api/"):
                self._handle_api(parsed, raw)
            else:
                self._static(parsed.path)
        except HTTPError as exc:
            self._send_json(exc.status, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            print(f"Erro interno do servidor: {exc!r}", file=sys.stderr)
            self._send_json(500, {"error": "Erro interno do servidor."})

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _dispatch

    def _read_raw(self):
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        if length > MAX_BODY:
            self.close_connection = True
            raise HTTPError(413, "Corpo da requisição excede 1 MB.")
        return self.rfile.read(length) if length > 0 else b""

    def _check_origin(self):
        if self.command in ("GET", "HEAD"):
            return
        origin = self.headers.get("Origin")
        if not origin:
            return
        allowed = {(self.headers.get("Host") or "").lower()} | ALLOWED_ORIGINS
        if urlsplit(origin).netloc.lower() not in allowed and origin.lower() not in allowed:
            raise HTTPError(403, "Origem não permitida.")

    def _handle_api(self, parsed, raw):
        self._check_origin()
        rest = parsed.path[5:].strip("/")
        parts = [unquote(p) for p in rest.split("/")] if rest else []
        with DB_LOCK:
            conn = connect()
            try:
                ctx = Ctx(conn, self, self.command, parts, parsed.query, raw)
                status, body = api(ctx)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        self._send_json(status, body, ctx.cookies)

    def _send_headers(self, status, content_type, length, extra=(), cache="no-store"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(length))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        for cookie in extra:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _send_json(self, status, body, cookies=()):
        raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_headers(status, "application/json; charset=utf-8", len(raw), cookies)
        if self.command != "HEAD":
            self.wfile.write(raw)

    def _static(self, path):
        if self.command not in ("GET", "HEAD"):
            self._send_json(405, {"error": "Método não permitido."})
            return
        target = None
        if path in STATIC_FILES:
            target = ROOT / STATIC_FILES[path]
        elif path.startswith("/assets/"):
            candidate = (ROOT / "assets" / unquote(path[len("/assets/"):])).resolve()
            try:
                candidate.relative_to((ROOT / "assets").resolve())
                target = candidate
            except ValueError:
                target = None
        if target is None or not target.is_file():
            self._send_json(404, {"error": "Arquivo não encontrado."})
            return
        raw = target.read_bytes()
        self._send_headers(200, MIME_TYPES.get(target.suffix.lower(), "application/octet-stream"), len(raw), cache="no-cache")
        if self.command != "HEAD":
            self.wfile.write(raw)


class PanelServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    if "--reset-admin" in sys.argv:
        raise SystemExit(reset_admin_password())
    try:
        init_database()
    except Exception as exc:  # noqa: BLE001
        print(f"Não foi possível abrir o Banco de Dados SQLite: {exc}", file=sys.stderr)
        raise SystemExit(1)
    local = HOST in ("127.0.0.1", "localhost", "::1")
    if not local and os.environ.get("ADMIN_PASSWORD") == "admin1234":
        print("ATENCAO: ADMIN_PASSWORD=admin1234 e uma senha de teste. Troque antes de publicar.", file=sys.stderr)
    if not local and not COOKIE_SECURE:
        print("Aviso: se o site usa HTTPS, defina COOKIE_SECURE=1.", file=sys.stderr)
    expected_data = (ROOT / "data").resolve()
    if not TEST_MODE and DATA_DIR.resolve() != expected_data:
        print("A pasta de dados não corresponde a esta versão da plataforma.", file=sys.stderr)
        raise SystemExit(1)
    print(f"Banco {'temporário de teste' if TEST_MODE else 'desta versão'}: {DB_FILE}", flush=True)
    server = PanelServer((HOST, PORT), PanelHandler)
    print(f"Painel disponível em http://localhost:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
