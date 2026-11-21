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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
import json
import sqlite3
import sys

from app.audit import log
from app.config import (
    ALLOWED_ORIGINS, COOKIE_SECURE, DATA_DIR, DB_FILE, HISTORY_LIMIT,
    HOST, MATRICULA_STATUS, MAX_BODY, MIME_TYPES, PORT, ROOT,
    SECURITY_HEADERS, STATUSES, TEST_MODE, TYPES,
)
from app.context import Ctx, public_user
from app.db import DB_LOCK, connect, init_database, reset_admin_password
from app.permissions import (
    can_edit, can_manage_turma, get_discipline, get_turma, require_edit, require_manage_turma,
    require_role, require_visible, turma_disciplines, visible_ids,
)
from app.ratelimit import LOGIN_BY_IP, LOGIN_BY_NAME, REGISTER_BY_IP
from app.security import (
    DUMMY_HASH, check_new_password, hash_password, session_cookie, verify_password,
)
from app.utils import HTTPError, bad, key_of, new_id, norm_name, now_iso, pick, text

REGISTER_NOTICE = ("Se o cadastro puder ser concluído, a solicitação seguirá para análise do professor. "
                   "Se não avançar, confira as informações ou fale com o professor.")


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
    if user["role"] not in ("admin", "professor", "aluno"):
        raise HTTPError(403, "Perfil inválido. Peça ao administrador para revisar sua conta.")
    ctx.user = user

    if resource == "me" and ident == "password" and method == "PUT":
        return me_password(ctx, user)
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
    if resource == "alunos" and ident and sub == "password" and method == "PUT":
        return aluno_password(ctx, user, ident)
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
        elif not row["passwordHash"]:
            verify_password(password, DUMMY_HASH)
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
    check_new_password(data.get("password"))
    REGISTER_BY_IP.add(ctx.ip)
    if conn.execute("SELECT 1 FROM users WHERE nameKey = ?", (key_of(name),)).fetchone():
        # Equaliza o trabalho criptográfico e não distingue conflito de nome
        # de um cadastro recebido na resposta HTTP.
        hash_password(data["password"])
        return 202, {"message": REGISTER_NOTICE}
    stamp, user_id = now_iso(), new_id()
    try:
        conn.execute(
            "INSERT INTO users (id, name, nameKey, role, passwordHash, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)",
            (user_id, name, key_of(name), "aluno", hash_password(data["password"]), stamp, stamp))
    except sqlite3.IntegrityError:
        # Mesmo tratamento para a corrida de unicidade detectada pelo banco.
        conn.rollback()
        if conn.execute("SELECT 1 FROM users WHERE nameKey = ?", (key_of(name),)).fetchone():
            hash_password(data["password"])
            return 202, {"message": REGISTER_NOTICE}
        raise
    matricula_id = new_id()
    conn.execute(
        "INSERT INTO matriculas (id, turmaId, studentId, status, createdAt, updatedAt) VALUES (?,?,?,?,?,?)",
        (matricula_id, turma["id"], user_id, "pendente", stamp, stamp))
    student = {"id": user_id, "name": name, "role": "aluno"}
    log(conn, student, "created", "matricula", matricula_id,
        f"Cadastro de aluno: {name} pediu matrícula na turma {turma['name']}", None, {"status": "pendente"})
    # Cadastro pendente não autentica automaticamente. A resposta neutra é
    # idêntica mesmo quando já existe um usuário com o mesmo nome.
    return 202, {"message": REGISTER_NOTICE}


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
    scoped = ctx.user["role"] == "professor"
    result = []
    for row in ctx.conn.execute("SELECT * FROM history ORDER BY createdAt DESC, rowid DESC LIMIT ?",
                                (HISTORY_LIMIT if scoped else limit,)):
        item = dict(row)
        try:
            item["changes"] = json.loads(item["changes"]) if item.get("changes") else []
        except ValueError:
            item["changes"] = []
        result.append(item)
    if scoped:
        allowed = professor_history_filter(ctx.conn, ctx.user)
        result = [item for item in result if allowed(item)][:limit]
    return result


def professor_history_filter(conn, user):
    """Professor vê o que ele mesmo fez e o que diz respeito às matérias e turmas que gerencia."""
    owned = conn.execute("SELECT id, name FROM disciplines WHERE ownerId = ?", (user["id"],)).fetchall()
    discipline_ids, discipline_names = {r["id"] for r in owned}, {r["name"] for r in owned}
    turma_ids = {t["id"] for t in conn.execute("SELECT * FROM turmas") if can_manage_turma(conn, user, t)}
    matricula_ids = {r["id"] for r in conn.execute("SELECT id, turmaId FROM matriculas") if r["turmaId"] in turma_ids}
    policy_discipline = {r["id"]: r["disciplineId"] for r in conn.execute("SELECT id, disciplineId FROM policies")}

    def allowed(item):
        if item["authorId"] == user["id"]:
            return True
        entity, entity_id = item["entity"], item["entityId"]
        if entity == "discipline":
            return entity_id in discipline_ids
        if entity == "policy":  # política removida não existe mais: usa o nome da matéria registrado na alteração
            return policy_discipline.get(entity_id) in discipline_ids or any(
                c.get("field") == "disciplineId" and (c.get("to") in discipline_names or c.get("from") in discipline_names)
                for c in item["changes"])
        if entity == "turma":
            return entity_id in turma_ids
        if entity == "matricula":
            return entity_id in matricula_ids
        return False

    return allowed


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


def me_password(ctx, user):
    """Troca da própria senha: exige a senha atual e encerra as outras sessões do usuário."""
    conn, data = ctx.conn, ctx.body
    if not user["passwordHash"]:
        raise bad("Sua conta ainda não tem senha. Peça a um professor da turma ou ao administrador para definir uma.")
    limit_key = f"senha|{user['id']}"
    if LOGIN_BY_NAME.blocked(limit_key):
        raise HTTPError(429, "Muitas tentativas. Aguarde alguns minutos e tente de novo.")
    current, new = data.get("currentPassword"), data.get("newPassword")
    if not isinstance(current, str) or not verify_password(current, user["passwordHash"]):
        LOGIN_BY_NAME.add(limit_key)
        raise HTTPError(403, "Senha atual incorreta.")
    check_new_password(new)
    if new == current:
        raise bad("A nova senha deve ser diferente da atual.")
    LOGIN_BY_NAME.clear(limit_key)
    conn.execute("UPDATE users SET passwordHash = ?, updatedAt = ? WHERE id = ?", (hash_password(new), now_iso(), user["id"]))
    conn.execute("DELETE FROM sessions WHERE userId = ? AND tokenHash != ?", (user["id"], ctx.token_hash or ""))
    log(conn, user, "updated", "user", user["id"], "Senha alterada pelo próprio usuário")
    return 200, {"ok": True}


def manages_student(conn, user, student_id):
    """Admin (qualquer aluno) ou professor que gerencia alguma turma em que o aluno está matriculado."""
    if conn.execute("SELECT 1 FROM users WHERE id = ? AND role = 'aluno'", (student_id,)).fetchone() is None:
        return False
    if user["role"] == "admin":
        return True
    return any(can_manage_turma(conn, user, turma) for turma in conn.execute(
        "SELECT t.* FROM turmas t JOIN matriculas m ON m.turmaId = t.id WHERE m.studentId = ?", (student_id,)))


def aluno_password(ctx, user, student_id):
    """Define a senha de um aluno (contas antigas sem senha ou senha esquecida). Encerra as sessões dele."""
    conn = ctx.conn
    require_role(user, "professor", "admin")
    if not manages_student(conn, user, student_id):
        raise HTTPError(404, "Aluno não encontrado nas suas turmas.")
    check_new_password(ctx.body.get("password"))
    student = conn.execute("SELECT name FROM users WHERE id = ?", (student_id,)).fetchone()
    conn.execute("UPDATE users SET passwordHash = ?, updatedAt = ? WHERE id = ?",
                 (hash_password(ctx.body["password"]), now_iso(), student_id))
    conn.execute("DELETE FROM sessions WHERE userId = ?", (student_id,))
    log(conn, user, "updated", "user", student_id, f"Senha definida para o aluno {student['name']}")
    return 200, {"ok": True}


def nota_save(ctx, user, student_id):
    conn = ctx.conn
    require_role(user, "professor")
    if not manages_student(conn, user, student_id):
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
