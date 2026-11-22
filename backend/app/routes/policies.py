from app.audit import log
from app.config import STATUSES, TYPES
from app.permissions import get_discipline, require_edit, require_visible, visible_ids
from app.utils import HTTPError, NOT_FOUND, bad, new_id, now_iso, text


def policy_view(conn, policy_id):
    return dict(conn.execute(
        "SELECT p.*, d.name AS disciplineName FROM policies p LEFT JOIN disciplines d ON d.id = p.disciplineId "
        "WHERE p.id = ?", (policy_id,)).fetchone())


def policy_rows(conn, where="", args=()):
    return [dict(r) for r in conn.execute(
        "SELECT p.*, d.name AS disciplineName FROM policies p LEFT JOIN disciplines d ON d.id = p.disciplineId "
        f"{where} ORDER BY p.rowid", args)]


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


def visible_policies(conn, user):
    visible = visible_ids(conn, user)
    return [p for p in policy_rows(conn) if visible is None or p["disciplineId"] in visible]


def policies(ctx, user, ident):
    conn, method = ctx.conn, ctx.method
    if ident is None:
        if method == "GET":
            items = visible_policies(conn, user)
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
