from app.audit import log
from app.config import MATRICULA_STATUS
from app.permissions import (
    can_manage_turma,
    get_turma,
    require_edit,
    require_manage_turma,
    require_role,
    turma_disciplines,
)
from app.utils import HTTPError, NOT_FOUND, bad, key_of, new_id, norm_name, now_iso, text


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


def manages_student(conn, user, student_id):
    """Admin (qualquer aluno) ou professor que gerencia alguma turma em que o aluno está matriculado."""
    if conn.execute("SELECT 1 FROM users WHERE id = ? AND role = 'aluno'", (student_id,)).fetchone() is None:
        return False
    if user["role"] == "admin":
        return True
    return any(can_manage_turma(conn, user, turma) for turma in conn.execute(
        "SELECT t.* FROM turmas t JOIN matriculas m ON m.turmaId = t.id WHERE m.studentId = ?", (student_id,)))


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
