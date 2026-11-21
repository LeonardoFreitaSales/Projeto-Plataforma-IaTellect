from app.audit import log
from app.permissions import require_role
from app.utils import HTTPError, NOT_FOUND, new_id, now_iso, pick, text


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
