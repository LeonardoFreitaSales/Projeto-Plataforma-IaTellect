from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote_to_bytes, urlsplit
import json
import os
import sys
import threading
import uuid

ROOT = Path(__file__).resolve().parent
ACCESS_FILE = (ROOT / ".." / ".." / "Tela de Login" / "Tela de Login v2.0" / "acesso.html").resolve()
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "database.json"
PORT = int(os.environ.get("PORT") or "3001")
STATUSES = {"proibido", "restricao", "permitido"}
TYPES = {"prova", "trabalho", "atividade", "pesquisa", "outro"}
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}
JS_TRIM_CHARS = "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
MISSING = object()
DB_LOCK = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id():
    return str(uuid.uuid4())

class HTTPError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def empty_database():
    return {"disciplines": [], "policies": [], "announcements": [], "history": []}


def write_database(database):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = Path(str(DB_FILE) + ".tmp")
    serialized = json.dumps(database, ensure_ascii=False, indent=2)
    with temp_file.open("w", encoding="utf-8", newline="") as handle:
        handle.write(serialized)
    os.replace(temp_file, DB_FILE)


def reject_json_constant(value):
    raise ValueError(f"Constante JSON inválida: {value}")

def load_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        database = empty_database()
        write_database(database)
        return database
    try:
        with DB_FILE.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle, parse_constant=reject_json_constant)
        database = empty_database()
        if isinstance(loaded, dict):
            database.update(loaded)
        elif isinstance(loaded, list):
            database.update({str(index): value for index, value in enumerate(loaded)})
        return database
    except Exception as exc:
        raise RuntimeError(f"Não foi possível ler {DB_FILE}. Corrija o JSON antes de iniciar o servidor.") from exc


try:
    db = load_database()
except Exception as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(1)


def persist():
    write_database(db)


def iso_length(value):
    return len(value.encode("utf-16-le")) // 2


def js_get(obj, key):
    if obj is None:
        raise TypeError("Não é possível ler propriedades de null.")
    if isinstance(obj, dict):
        return obj.get(key, MISSING)
    return MISSING


def coalesce(value, fallback):
    return fallback if value is MISSING or value is None else value


def text(value, name, maximum=5000, required=True):
    if (value is MISSING or value is None) and not required:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{name} deve ser texto.")
    output = value.strip(JS_TRIM_CHARS)
    if required and not output:
        raise ValueError(f"{name} é obrigatório.")
    if iso_length(output) > maximum:
        raise ValueError(f"{name} excede {maximum} caracteres.")
    return output


def add_history(action, entity, entity_id, summary):
    db["history"].insert(0, {
        "id": new_id(), "action": action, "entity": entity,
        "entityId": entity_id, "summary": summary, "createdAt": now_iso(),
    })
    db["history"] = db["history"][:500]


def parse_policy(input_data, existing=None):
    if existing is None:
        existing = {}
    discipline_id = coalesce(js_get(input_data, "disciplineId"), existing.get("disciplineId", MISSING))
    if not any(item.get("id", MISSING) == discipline_id for item in db["disciplines"]):
        raise HTTPError(404, "Disciplina não encontrada.")
    status = coalesce(js_get(input_data, "status"), existing.get("status", MISSING))
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("status deve ser proibido, restricao ou permitido.")
    activity_type = coalesce(js_get(input_data, "activityType"), existing.get("activityType", MISSING))
    activity_type = coalesce(activity_type, "outro")
    if not isinstance(activity_type, str) or activity_type not in TYPES:
        raise ValueError("Tipo de atividade inválido.")
    return {
        "disciplineId": discipline_id, "activityType": activity_type,
        "activityName": text(coalesce(js_get(input_data, "activityName"), existing.get("activityName", MISSING)), "activityName", 180),
        "status": status,
        "conditions": text(coalesce(js_get(input_data, "conditions"), existing.get("conditions", "")), "conditions", 3000, False),
        "details": text(coalesce(js_get(input_data, "details"), existing.get("details", "")), "details", 5000, False),
        "source": text(coalesce(js_get(input_data, "source"), existing.get("source", "")), "source", 500, False),
        "updatedAt": now_iso(),
    }


def policy_view(policy):
    discipline = next((item for item in db["disciplines"] if item.get("id", MISSING) == policy.get("disciplineId", MISSING)), None)
    result = dict(policy)
    result["disciplineName"] = discipline.get("name") if discipline and discipline.get("name") is not None else None
    return result


def js_truthy(value):
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and (value == 0 or value != value):
        return False
    if isinstance(value, str) and value == "":
        return False
    return True


def dashboard():
    counts = {"proibido": 0, "restricao": 0, "permitido": 0}
    for policy in db["policies"]:
        status = policy.get("status")
        if status in counts:
            counts[status] += 1
    return {
        "disciplines": len(db["disciplines"]), "policies": len(db["policies"]),
        "changedSinceLastVisit": 0, "distribution": counts,
        "announcements": [item for item in db["announcements"] if js_truthy(item.get("active"))][:5],
    }


def decode_uri_component(value):
    index = 0
    while index < len(value):
        if value[index] == "%":
            if index + 2 >= len(value) or any(char not in "0123456789abcdefABCDEF" for char in value[index + 1:index + 3]):
                raise ValueError("URI malformada.")
            index += 3
        else:
            index += 1
    return unquote_to_bytes(value).decode("utf-8")


def route_id(path, base):
    rest = path[len(base):]
    if not rest or rest == "/":
        return None
    return decode_uri_component(rest[1:] if rest.startswith("/") else rest)


def query_first(query, name):
    values = parse_qs(query, keep_blank_values=True).get(name)
    return values[0] if values else None


def js_number(value):
    if value is None or value == "":
        return 50.0
    stripped = value.strip()
    if not stripped:
        return 0.0
    try:
        return float(stripped)
    except ValueError:
        try:
            if stripped.lower().startswith(("0x", "+0x", "-0x")):
                sign = -1 if stripped.startswith("-") else 1
                body = stripped[1:] if stripped[:1] in "+-" else stripped
                return float(sign * int(body, 16))
        except ValueError:
            pass
        return float("nan")


class PanelHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format_string, *args):
        return

    def __getattr__(self, name):
        if name.startswith("do_"):
            return self._dispatch
        raise AttributeError(name)

    def _dispatch(self):
        try:
            parsed = urlsplit(self.path)
            if parsed.path.startswith("/api/"):
                with DB_LOCK:
                    handled = self._api(parsed.path, parsed.query)
                if not handled:
                    self._fail(404, "Rota de API não encontrada.")
                return
            self._static(parsed.path)
        except Exception as exc:
            message = str(exc)
            lowered = message.casefold()
            is_validation = any(word in lowered for word in ("inválido", "obrigatório", "excede", "deve ser", "tipo de atividade"))
            status = exc.status if isinstance(exc, HTTPError) else (400 if is_validation else 500)
            if status == 500:
                print(f"Erro interno do servidor: {exc!r}", file=sys.stderr)
            self._fail(status, message if status != 500 else "Erro interno do servidor.")

    def _send_json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def _fail(self, status, message):
        self._send_json(status, {"error": message})

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        body_text = raw.decode("utf-8", errors="replace")
        if iso_length(body_text) > 1_000_000:
            raise ValueError("Corpo da requisição excede 1 MB.")
        try:
            return json.loads(body_text, parse_constant=reject_json_constant)
        except Exception as exc:
            raise ValueError("JSON inválido.") from exc

    def _api(self, path, query):
        method = self.command
        if method == "GET" and path == "/api/health":
            self._send_json(200, {"status": "ok", "time": now_iso()})
            return True
        if method == "GET" and path == "/api/dashboard":
            self._send_json(200, dashboard())
            return True
        if path == "/api/disciplines" and method == "GET":
            self._send_json(200, db["disciplines"])
            return True
        if path == "/api/disciplines" and method == "POST":
            data = self._read_json()
            name = text(js_get(data, "name"), "name", 180)
            lowered_name = name.lower()
            if any(item.get("name", "").lower() == lowered_name for item in db["disciplines"]):
                self._fail(409, "Já existe uma disciplina com esse nome.")
                return True
            item = {
                "id": new_id(), "name": name,
                "code": text(coalesce(js_get(data, "code"), ""), "code", 40, False),
                "instructor": text(coalesce(js_get(data, "instructor"), ""), "instructor", 180, False),
                "createdAt": now_iso(), "updatedAt": now_iso(),
            }
            db["disciplines"].append(item)
            add_history("created", "discipline", item["id"], f"Disciplina criada: {item['name']}")
            persist()
            self._send_json(201, item)
            return True
        if path.startswith("/api/disciplines/"):
            identifier = route_id(path, "/api/disciplines")
            item = next((entry for entry in db["disciplines"] if entry.get("id", MISSING) == identifier), None)
            if item is None:
                self._fail(404, "Disciplina não encontrada.")
                return True
            if method == "GET":
                result = dict(item)
                result["policies"] = [policy_view(policy) for policy in db["policies"] if policy.get("disciplineId") == identifier]
                self._send_json(200, result)
                return True
            if method in ("PUT", "PATCH"):
                data = self._read_json()
                name = text(coalesce(js_get(data, "name"), item.get("name", MISSING)), "name", 180)
                if any(entry.get("id") != identifier and entry.get("name", "").lower() == name.lower() for entry in db["disciplines"]):
                    self._fail(409, "Já existe uma disciplina com esse nome.")
                    return True
                item.update({
                    "name": name,
                    "code": text(coalesce(js_get(data, "code"), item.get("code", MISSING)), "code", 40, False),
                    "instructor": text(coalesce(js_get(data, "instructor"), item.get("instructor", MISSING)), "instructor", 180, False),
                    "updatedAt": now_iso(),
                })
                add_history("updated", "discipline", identifier, f"Disciplina atualizada: {item['name']}")
                persist()
                self._send_json(200, item)
                return True
            if method == "DELETE":
                if any(policy.get("disciplineId") == identifier for policy in db["policies"]):
                    self._fail(409, "Remova ou mova as políticas desta disciplina antes de excluí-la.")
                    return True
                db["disciplines"] = [entry for entry in db["disciplines"] if entry.get("id") != identifier]
                add_history("deleted", "discipline", identifier, f"Disciplina removida: {item.get('name')}")
                persist()
                self._send_json(200, {"deleted": True, "id": identifier})
                return True

        if path == "/api/policies" and method == "GET":
            items = db["policies"]
            discipline_id = query_first(query, "disciplineId")
            status_filter = query_first(query, "status")
            search = (query_first(query, "q") or "").lower()
            if discipline_id:
                items = [item for item in items if item.get("disciplineId") == discipline_id]
            if status_filter:
                items = [item for item in items if item.get("status") == status_filter]
            if search:
                filtered = []
                for item in items:
                    view = policy_view(item)
                    searchable = " ".join(str(view.get(field, "undefined")) for field in ("activityName", "details", "conditions", "disciplineName")).lower()
                    if search in searchable:
                        filtered.append(item)
                items = filtered
            self._send_json(200, [policy_view(item) for item in items])
            return True
        if path == "/api/policies" and method == "POST":
            data = self._read_json()
            item = {"id": new_id(), **parse_policy(data), "createdAt": now_iso()}
            db["policies"].append(item)
            add_history("created", "policy", item["id"], f"Política criada: {item['activityName']}")
            persist()
            self._send_json(201, policy_view(item))
            return True
        if path.startswith("/api/policies/"):
            identifier = route_id(path, "/api/policies")
            item = next((entry for entry in db["policies"] if entry.get("id", MISSING) == identifier), None)
            if item is None:
                self._fail(404, "Política não encontrada.")
                return True
            if method == "GET":
                self._send_json(200, policy_view(item))
                return True
            if method in ("PUT", "PATCH"):
                data = self._read_json()
                item.update(parse_policy(data, item))
                add_history("updated", "policy", identifier, f"Política atualizada: {item['activityName']}")
                persist()
                self._send_json(200, policy_view(item))
                return True
            if method == "DELETE":
                db["policies"] = [entry for entry in db["policies"] if entry.get("id") != identifier]
                add_history("deleted", "policy", identifier, f"Política removida: {item['activityName']}")
                persist()
                self._send_json(200, {"deleted": True, "id": identifier})
                return True

        if path == "/api/announcements" and method == "GET":
            include_inactive = query_first(query, "all") == "true"
            self._send_json(200, [item for item in db["announcements"] if js_truthy(item.get("active")) or include_inactive])
            return True
        if path == "/api/announcements" and method == "POST":
            data = self._read_json()
            active = js_get(data, "active")
            item = {
                "id": new_id(), "title": text(js_get(data, "title"), "title", 180),
                "message": text(js_get(data, "message"), "message", 3000), "active": active is not False,
                "createdAt": now_iso(), "updatedAt": now_iso(),
            }
            db["announcements"].insert(0, item)
            add_history("created", "announcement", item["id"], f"Comunicado criado: {item['title']}")
            persist()
            self._send_json(201, item)
            return True
        if path.startswith("/api/announcements/"):
            identifier = route_id(path, "/api/announcements")
            item = next((entry for entry in db["announcements"] if entry.get("id", MISSING) == identifier), None)
            if item is None:
                self._fail(404, "Comunicado não encontrado.")
                return True
            if method in ("PUT", "PATCH"):
                data = self._read_json()
                active = coalesce(js_get(data, "active"), item.get("active", MISSING))
                item.update({
                    "title": text(coalesce(js_get(data, "title"), item.get("title", MISSING)), "title", 180),
                    "message": text(coalesce(js_get(data, "message"), item.get("message", MISSING)), "message", 3000),
                    "active": active, "updatedAt": now_iso(),
                })
                add_history("updated", "announcement", identifier, f"Comunicado atualizado: {item['title']}")
                persist()
                self._send_json(200, item)
                return True
            if method == "DELETE":
                db["announcements"] = [entry for entry in db["announcements"] if entry.get("id") != identifier]
                add_history("deleted", "announcement", identifier, f"Comunicado removido: {item['title']}")
                persist()
                self._send_json(200, {"deleted": True, "id": identifier})
                return True

        if method == "GET" and path == "/api/history":
            raw_limit = query_first(query, "limit")
            number = js_number(raw_limit or "50")
            limit = 0 if number != number else int(max(1, min(100, number)))
            self._send_json(200, db["history"][:limit])
            return True
        if method == "POST" and path == "/api/ai-check":
            data = self._read_json()
            discipline_id = text(js_get(data, "disciplineId"), "disciplineId", 100)
            if not any(item.get("id", MISSING) == discipline_id for item in db["disciplines"]):
                self._fail(404, "Disciplina não encontrada.")
                return True
            activity_type = text(js_get(data, "activityType"), "activityType", 40)
            if not isinstance(activity_type, str) or activity_type not in TYPES:
                self._fail(400, "Tipo de atividade inválido.")
                return True
            matches = [
                policy_view(item) for item in db["policies"]
                if item.get("disciplineId") == discipline_id
                and (item.get("activityType") == activity_type or item.get("activityType") == "outro")
            ]
            if matches:
                if any(item.get("status") == "proibido" for item in matches):
                    decision = "proibido"
                elif any(item.get("status") == "restricao" for item in matches):
                    decision = "restricao"
                else:
                    decision = "permitido"
                message = None
            else:
                decision = "sem_politica"
                message = "Nenhuma política cadastrada para esta atividade."
            self._send_json(200, {
                "disciplineId": discipline_id, "activityType": activity_type,
                "policies": matches, "decision": decision, "message": message,
            })
            return True
        return False

    def _static(self, raw_path):
        if self.command not in ("GET", "HEAD"):
            self._fail(405, "Método não permitido.")
            return
        if raw_path == "/acesso.html":
            if not ACCESS_FILE.exists() or not ACCESS_FILE.is_file():
                self._fail(404, "Tela de acesso não encontrada.")
                return
            self._send_file(ACCESS_FILE, ".html")
            return
        requested = decode_uri_component("/index.html" if raw_path == "/" else raw_path)
        target = (ROOT / requested.lstrip("/")).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self._fail(403, "Acesso negado.")
            return
        if not target.exists() or not target.is_file():
            self._fail(404, "Arquivo não encontrado.")
            return
        self._send_file(target, target.suffix)

    def _send_file(self, file_path, suffix):
        raw = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", MIME_TYPES.get(suffix, "application/octet-stream"))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)


class PanelServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    server = PanelServer(("0.0.0.0", PORT), PanelHandler)
    print(f"Painel disponível em http://localhost:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
