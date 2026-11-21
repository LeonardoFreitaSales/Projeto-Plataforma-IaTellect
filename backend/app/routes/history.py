import json
from app.config import HISTORY_LIMIT
from app.permissions import can_manage_turma


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
