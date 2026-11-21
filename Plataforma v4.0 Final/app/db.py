"""Conexão, inicialização e migrações do banco de dados."""
import getpass
import os
import secrets
import sqlite3
import threading

from .config import DATA_DIR, DB_FILE, SCHEMA_FILE
from .security import hash_password
from .utils import key_of, new_id, norm_name, now_iso

DB_LOCK = threading.Lock()


def connect():
    if os.environ.get("TURSO_DATABASE_URL"):
        from turso_db import Connection
        return Connection(os.environ["TURSO_DATABASE_URL"], os.environ.get("TURSO_AUTH_TOKEN", ""))
    if os.environ.get("VERCEL"):
        raise RuntimeError("Banco remoto não configurado.")
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
        if not os.environ.get("TURSO_DATABASE_URL"):
            conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        # Migracao de bancos criados pela v2
        _add_column(conn, "disciplines", "ownerId", "TEXT REFERENCES users(id) ON DELETE SET NULL")
        for column in ("authorId", "authorName", "authorRole", "changes"):
            _add_column(conn, "history", column, "TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_disciplines_owner ON disciplines(ownerId)")
        if not os.environ.get("TURSO_DATABASE_URL"):
            conn.execute("PRAGMA user_version = 3")
        conn.commit()
        if create_admin:
            ensure_admin(conn)
            conn.commit()
        conn.execute("DELETE FROM sessions WHERE userId IN (SELECT id FROM users WHERE passwordHash IS NULL OR passwordHash = '')")
        conn.execute("DELETE FROM sessions WHERE expiresAt < ?", (now_iso(),))
        conn.commit()
        if not os.environ.get("TURSO_DATABASE_URL"):
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
        if os.environ.get("TURSO_DATABASE_URL") or os.environ.get("VERCEL"):
            raise RuntimeError("Defina ADMIN_PASSWORD para criar o administrador inicial.")
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
        print("Administrador criado. Consulte a senha inicial no arquivo local indicado abaixo.", flush=True)
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
