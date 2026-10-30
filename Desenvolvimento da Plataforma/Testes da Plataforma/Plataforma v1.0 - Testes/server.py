#!/usr/bin/env python3
"""Servidor local da Plataforma v1.0 (políticas de uso de IA por disciplina).

Só usa a biblioteca padrão do Python (3.8+), então não precisa instalar nada.

Como rodar, na pasta onde estão server.py, index.html e app.js:

    python server.py            # http://127.0.0.1:8000
    python server.py 5000       # outra porta

Os dados ficam em data/database.json, criado automaticamente na primeira execução.
"""

import json
import os
import re
import sys
import threading
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "database.json"

HOST = os.environ.get("HOST", "127.0.0.1")
DEFAULT_PORT = 8000

# Só estes arquivos são servidos (nada fora da lista, então não há path traversal).
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
}

# Do mais restritivo ao menos restritivo (a ordem é usada em "Posso usar IA?").
STATUSES = ("proibido", "restricao", "permitido")
STATUS_LABELS = {
    "proibido": "Proibido",
    "restricao": "Permitido com restrição",
    "permitido": "Permitido",
}
ACTIVITY_TYPES = ("prova", "trabalho", "atividade", "pesquisa", "outro")

MAX_BODY_BYTES = 256 * 1024
DASHBOARD_ANNOUNCEMENTS = 5   # quantos comunicados aparecem no painel inicial
MAX_HISTORY = 1000            # quantas entradas de histórico são guardadas
VISIT_GAP = timedelta(minutes=30)  # intervalo que separa uma "visita" da outra

LOCK = threading.RLock()


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------

class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def now():
    return datetime.now(timezone.utc)


def now_iso():
    return now().isoformat(timespec="milliseconds")


def new_id():
    return uuid.uuid4().hex[:12]


# ----------------------------------------------------------------------------
# Banco de dados (arquivo JSON)
# ----------------------------------------------------------------------------

def empty_db():
    return {
        "disciplines": [],
        "policies": [],
        "announcements": [],
        "history": [],
        "meta": {"lastVisit": None, "previousVisit": None},
    }


def load_db():
    if not DB_FILE.exists():
        return empty_db()
    try:
        with DB_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("estrutura inesperada")
    except (OSError, ValueError):
        # Arquivo corrompido: guarda uma cópia e começa de novo, sem apagar nada.
        try:
            stamp = now().strftime("%Y%m%d-%H%M%S")
            DB_FILE.replace(DATA_DIR / f"database.corrompido-{stamp}.json")
        except OSError:
            pass
        return empty_db()

    db = empty_db()
    for key in ("disciplines", "policies", "announcements", "history"):
        if isinstance(data.get(key), list):
            db[key] = data[key]
    if isinstance(data.get("meta"), dict):
        db["meta"].update(data["meta"])
    return db


def save_db(db):
    DATA_DIR.mkdir(exist_ok=True)
    tmp = DB_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_FILE)  # troca atômica: nunca deixa o arquivo pela metade


def log(db, action, summary):
    db["history"].append(
        {"id": new_id(), "action": action, "summary": summary, "createdAt": now_iso()}
    )
    del db["history"][:-MAX_HISTORY]


def register_visit():
    """Chamada quando a página é aberta; base do "alteradas desde sua última visita".

    Recarregar a página várias vezes seguidas conta como a mesma visita: só
    depois de 30 minutos sem abrir é que a visita anterior é "fechada".
    """
    with LOCK:
        db = load_db()
        meta = db["meta"]
        last = None
        if meta.get("lastVisit"):
            try:
                last = datetime.fromisoformat(meta["lastVisit"])
            except ValueError:
                last = None
        if last is None or now() - last > VISIT_GAP:
            meta["previousVisit"] = meta.get("lastVisit")
        meta["lastVisit"] = now_iso()
        save_db(db)


# ----------------------------------------------------------------------------
# Validação
# ----------------------------------------------------------------------------

def require_dict(body):
    if not isinstance(body, dict):
        raise ApiError("Corpo da requisição inválido.")
    return body


def text_field(body, name, max_len, label, required=False):
    value = body.get(name)
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ApiError(f'O campo "{label}" é inválido.')
    value = value.strip()
    if required and not value:
        raise ApiError(f'O campo "{label}" é obrigatório.')
    if len(value) > max_len:
        raise ApiError(f'O campo "{label}" aceita no máximo {max_len} caracteres.')
    return value


def choice_field(body, name, allowed, label, default):
    value = body.get(name) or default
    if value not in allowed:
        raise ApiError(f'Valor inválido para "{label}".')
    return value


def find(items, item_id):
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


def get_or_404(items, item_id, what):
    item = find(items, item_id)
    if item is None:
        raise ApiError(f"{what} não encontrada.", 404)
    return item


# ----------------------------------------------------------------------------
# Rotas da API — cada função recebe (db, args, query, body) e devolve (status, json)
# ----------------------------------------------------------------------------

def policy_view(db, policy):
    names = {d["id"]: d["name"] for d in db["disciplines"]}
    return {**policy, "disciplineName": names.get(policy.get("disciplineId"), "—")}


def latest_announcements(db, limit=None):
    items = sorted(db["announcements"], key=lambda a: a.get("createdAt", ""), reverse=True)
    return items[:limit] if limit else items


def api_health(db, args, query, body):
    return 200, {"status": "ok", "time": now_iso()}


def api_dashboard(db, args, query, body):
    distribution = {status: 0 for status in STATUSES}
    for policy in db["policies"]:
        if policy.get("status") in distribution:
            distribution[policy["status"]] += 1

    previous = db["meta"].get("previousVisit")
    changed = 0
    if previous:
        changed = sum(1 for p in db["policies"] if p.get("updatedAt", "") > previous)

    return 200, {
        "disciplines": len(db["disciplines"]),
        "policies": len(db["policies"]),
        "changedSinceLastVisit": changed,
        "distribution": distribution,
        "announcements": latest_announcements(db, DASHBOARD_ANNOUNCEMENTS),
    }


# ---- Disciplinas -----------------------------------------------------------

def discipline_fields(db, body, current_id=None):
    body = require_dict(body)
    fields = {
        "name": text_field(body, "name", 180, "Nome da disciplina", required=True),
        "code": text_field(body, "code", 40, "Código"),
        "instructor": text_field(body, "instructor", 180, "Docente"),
    }
    for other in db["disciplines"]:
        if other["id"] != current_id and other["name"].casefold() == fields["name"].casefold():
            raise ApiError("Já existe uma disciplina com este nome.", 409)
    return fields


def api_disciplines_list(db, args, query, body):
    items = sorted(db["disciplines"], key=lambda d: d["name"].casefold())
    return 200, items


def api_disciplines_create(db, args, query, body):
    fields = discipline_fields(db, body)
    stamp = now_iso()
    item = {"id": new_id(), **fields, "createdAt": stamp, "updatedAt": stamp}
    db["disciplines"].append(item)
    log(db, "Disciplina criada", item["name"])
    save_db(db)
    return 201, item


def api_disciplines_update(db, args, query, body):
    item = get_or_404(db["disciplines"], args[0], "Disciplina")
    item.update(discipline_fields(db, body, current_id=item["id"]))
    item["updatedAt"] = now_iso()
    log(db, "Disciplina editada", item["name"])
    save_db(db)
    return 200, item


def api_disciplines_delete(db, args, query, body):
    item = get_or_404(db["disciplines"], args[0], "Disciplina")
    db["disciplines"].remove(item)
    removed = [p for p in db["policies"] if p.get("disciplineId") == item["id"]]
    db["policies"] = [p for p in db["policies"] if p.get("disciplineId") != item["id"]]
    summary = item["name"]
    if removed:
        summary += f" (e {len(removed)} política(s) ligada(s) a ela)"
    log(db, "Disciplina removida", summary)
    save_db(db)
    return 200, {"ok": True}


# ---- Políticas -------------------------------------------------------------

def policy_fields(db, body):
    body = require_dict(body)
    discipline_id = text_field(body, "disciplineId", 80, "Disciplina", required=True)
    get_or_404(db["disciplines"], discipline_id, "Disciplina")
    return {
        "disciplineId": discipline_id,
        "activityType": choice_field(body, "activityType", ACTIVITY_TYPES, "Tipo de atividade", "atividade"),
        "activityName": text_field(body, "activityName", 180, "Atividade", required=True),
        "status": choice_field(body, "status", STATUSES, "Uso de IA", "proibido"),
        "source": text_field(body, "source", 500, "Fonte"),
        "conditions": text_field(body, "conditions", 3000, "Condições"),
        "details": text_field(body, "details", 5000, "Detalhes"),
    }


def policy_summary(db, policy):
    view = policy_view(db, policy)
    return f'{view["disciplineName"]} · {policy["activityName"]}: {STATUS_LABELS[policy["status"]]}'


def api_policies_list(db, args, query, body):
    items = [policy_view(db, p) for p in db["policies"]]
    items.sort(key=lambda p: (p["disciplineName"].casefold(), p["activityName"].casefold()))
    return 200, items


def api_policies_create(db, args, query, body):
    fields = policy_fields(db, body)
    stamp = now_iso()
    item = {"id": new_id(), **fields, "createdAt": stamp, "updatedAt": stamp}
    db["policies"].append(item)
    log(db, "Política criada", policy_summary(db, item))
    save_db(db)
    return 201, policy_view(db, item)


def api_policies_update(db, args, query, body):
    item = get_or_404(db["policies"], args[0], "Política")
    item.update(policy_fields(db, body))
    item["updatedAt"] = now_iso()
    log(db, "Política editada", policy_summary(db, item))
    save_db(db)
    return 200, policy_view(db, item)


def api_policies_delete(db, args, query, body):
    item = get_or_404(db["policies"], args[0], "Política")
    summary = policy_summary(db, item)
    db["policies"].remove(item)
    log(db, "Política removida", summary)
    save_db(db)
    return 200, {"ok": True}


# ---- "Posso usar IA?" ------------------------------------------------------

def api_ai_check(db, args, query, body):
    body = require_dict(body)
    discipline_id = text_field(body, "disciplineId", 80, "Disciplina", required=True)
    activity_type = choice_field(body, "activityType", ACTIVITY_TYPES, "Tipo de atividade", "atividade")
    get_or_404(db["disciplines"], discipline_id, "Disciplina")

    matches = [
        policy_view(db, p)
        for p in db["policies"]
        if p.get("disciplineId") == discipline_id and p.get("activityType") == activity_type
    ]
    if not matches:
        return 200, {
            "decision": "sem_politica",
            "policies": [],
            "message": "Nenhuma política cadastrada para esta disciplina e tipo de atividade.",
        }
    # Havendo mais de uma regra, vale a mais restritiva.
    decision = min((p["status"] for p in matches), key=STATUSES.index)
    return 200, {"decision": decision, "policies": matches, "message": ""}


# ---- Comunicados -----------------------------------------------------------

def api_announcements_list(db, args, query, body):
    show_all = query.get("all", [""])[0].lower() in ("1", "true", "sim")
    return 200, latest_announcements(db, None if show_all else DASHBOARD_ANNOUNCEMENTS)


def api_announcements_create(db, args, query, body):
    body = require_dict(body)
    item = {
        "id": new_id(),
        "title": text_field(body, "title", 180, "Título", required=True),
        "message": text_field(body, "message", 3000, "Mensagem", required=True),
        "createdAt": now_iso(),
    }
    db["announcements"].append(item)
    log(db, "Comunicado publicado", item["title"])
    save_db(db)
    return 201, item


def api_announcements_delete(db, args, query, body):
    item = get_or_404(db["announcements"], args[0], "Comunicado")
    db["announcements"].remove(item)
    log(db, "Comunicado removido", item["title"])
    save_db(db)
    return 200, {"ok": True}


# ---- Histórico -------------------------------------------------------------

def api_history(db, args, query, body):
    try:
        limit = int(query.get("limit", ["100"])[0])
    except ValueError:
        limit = 100
    limit = max(1, min(limit, 500))
    return 200, list(reversed(db["history"]))[:limit]


ID = r"([A-Za-z0-9_-]{1,80})"
ROUTES = [
    ("GET", r"/api/health", api_health),
    ("GET", r"/api/dashboard", api_dashboard),
    ("GET", r"/api/disciplines", api_disciplines_list),
    ("POST", r"/api/disciplines", api_disciplines_create),
    ("PUT", rf"/api/disciplines/{ID}", api_disciplines_update),
    ("DELETE", rf"/api/disciplines/{ID}", api_disciplines_delete),
    ("GET", r"/api/policies", api_policies_list),
    ("POST", r"/api/policies", api_policies_create),
    ("PUT", rf"/api/policies/{ID}", api_policies_update),
    ("DELETE", rf"/api/policies/{ID}", api_policies_delete),
    ("POST", r"/api/ai-check", api_ai_check),
    ("GET", r"/api/announcements", api_announcements_list),
    ("POST", r"/api/announcements", api_announcements_create),
    ("DELETE", rf"/api/announcements/{ID}", api_announcements_delete),
    ("GET", r"/api/history", api_history),
]


def find_route(method, path):
    path_exists = False
    for route_method, pattern, handler in ROUTES:
        match = re.fullmatch(pattern, path)
        if not match:
            continue
        path_exists = True
        if route_method == method:
            return handler, match.groups(), False
    return None, (), path_exists


# ----------------------------------------------------------------------------
# Servidor HTTP
# ----------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "PlataformaPoliticas/1.0"

    # -- respostas --
    def _send(self, status, payload, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, payload, "application/json; charset=utf-8")

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ApiError("Content-Length inválido.")
        if length > MAX_BODY_BYTES:
            raise ApiError("Requisição grande demais.", 413)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ApiError("JSON inválido.")

    # -- arquivos estáticos --
    def _serve_static(self, path):
        entry = STATIC_FILES.get(path)
        if entry is None:
            return self._json(404, {"error": "Página não encontrada."})
        filename, content_type = entry
        try:
            payload = (BASE_DIR / filename).read_bytes()
        except OSError:
            return self._json(404, {"error": f"Arquivo {filename} não encontrado ao lado do server.py."})
        if path in ("/", "/index.html"):
            with LOCK:
                register_visit()
        self._send(200, payload, content_type)

    # -- despacho --
    def _dispatch(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        method = "GET" if self.command == "HEAD" else self.command

        if not path.startswith("/api/"):
            if method != "GET":
                return self._json(405, {"error": "Método não permitido."})
            return self._serve_static(path)

        try:
            handler, args, path_exists = find_route(method, path)
            if handler is None:
                if path_exists:
                    raise ApiError("Método não permitido.", 405)
                raise ApiError("Rota não encontrada.", 404)
            body = self._read_body() if method in ("POST", "PUT") else {}
            query = parse_qs(parsed.query)
            with LOCK:
                db = load_db()
                status, data = handler(db, args, query, body)
            self._json(status, data)
        except ApiError as err:
            self._json(err.status, {"error": err.message})
        except Exception:  # erro inesperado: registra no terminal e responde 500
            traceback.print_exc()
            self._json(500, {"error": "Erro interno do servidor."})

    do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = _dispatch

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (datetime.now().strftime("%H:%M:%S"), fmt % args))


def main():
    port = DEFAULT_PORT
    raw_port = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PORT")
    if raw_port:
        try:
            port = int(raw_port)
        except ValueError:
            sys.exit(f"Porta inválida: {raw_port!r}")

    DATA_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"Plataforma v1.0 rodando em http://{HOST}:{port}  (Ctrl+C para encerrar)")
    print(f"Dados em: {DB_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
