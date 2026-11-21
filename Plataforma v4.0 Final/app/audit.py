"""Registro do histórico de alterações da plataforma."""
import json

from .config import HISTORY_LIMIT
from .utils import new_id, now_iso

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
