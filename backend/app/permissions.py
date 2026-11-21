"""Regras de acesso a disciplinas e turmas."""
import sqlite3

from .utils import HTTPError


def require_role(user, *roles):
    # O CHECK do banco impede esse estado; ainda assim, trate linhas legadas
    # ou objetos incompletos como sem permissões por padrão.
    if not isinstance(user, (dict, sqlite3.Row)) or "role" not in user.keys() or user["role"] not in roles:
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
