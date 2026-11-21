from app.permissions import visible_ids
from app.routes.announcements import announcement_view


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
