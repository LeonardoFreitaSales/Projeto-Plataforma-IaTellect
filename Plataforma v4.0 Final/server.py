#!/usr/bin/env python3
"""Plataforma v4.0 - servidor (Python 3 + SQLite, sem bibliotecas externas).

Perfis: admin, professor e aluno.
- admin: tudo (comunicados, usuarios, donos das materias, todas as turmas).
- professor: altera apenas as materias de que e dono; gerencia turmas e
  aprova/recusa matriculas; ve o historico; faz anotacoes privadas.
- aluno: entra com nome completo e senha; contas antigas sem senha ficam
  bloqueadas ate que um responsavel defina uma. Ve apenas as materias
  das turmas em que a matricula foi aprovada.

Variaveis de ambiente (todas opcionais):
  PORT             porta HTTP (padrao 3002)
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
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
from app.config import (
    ALLOWED_ORIGINS,
    COOKIE_SECURE,
    DATA_DIR,
    DB_FILE,
    HOST,
    MAX_BODY,
    MIME_TYPES,
    PORT,
    ROOT,
    SECURITY_HEADERS,
    TEST_MODE,
)
from app.context import Ctx
from app.db import DB_LOCK, connect, init_database, reset_admin_password
from app.permissions import require_role
from app.routes import api
from app.utils import HTTPError


STATIC_FILES = {"/": "index.html", "/index.html": "index.html", "/acesso.html": "acesso.html"}


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
