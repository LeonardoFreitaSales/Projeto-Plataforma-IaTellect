from app.audit import log
from app.permissions import (
    get_discipline,
    require_edit,
    require_role,
    require_visible,
    visible_ids,
)
from app.routes.policies import policy_rows
from app.utils import HTTPError, NOT_FOUND, bad, key_of, new_id, now_iso, pick, text


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
