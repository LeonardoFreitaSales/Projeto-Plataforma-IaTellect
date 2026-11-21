from app.audit import log
from app.permissions import require_role
from app.routes.turmas import manages_student
from app.security import check_new_password, hash_password
from app.utils import HTTPError, NOT_FOUND, bad, key_of, new_id, norm_name, now_iso, text


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
