import sqlite3
from app.audit import log
from app.context import public_user
from app.permissions import turma_disciplines
from app.ratelimit import LOGIN_BY_IP, LOGIN_BY_NAME, REGISTER_BY_IP
from app.security import (
    DUMMY_HASH,
    check_new_password,
    hash_password,
    session_cookie,
    verify_password,
)
from app.utils import HTTPError, NOT_FOUND, bad, key_of, new_id, norm_name, now_iso, text


REGISTER_NOTICE = ("Se o cadastro puder ser concluído, a solicitação seguirá para análise do professor. "
                   "Se não avançar, confira as informações ou fale com o professor.")


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
