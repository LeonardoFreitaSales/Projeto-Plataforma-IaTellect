from app.context import public_user
from app.permissions import require_role
from app.utils import HTTPError, NOT_FOUND, now_iso
from . import announcements, auth, dashboard, disciplines, history, lia, policies, turmas, users


def api(ctx):
    parts = ctx.parts
    resource = parts[0] if parts else None
    ident = parts[1] if len(parts) > 1 else None
    sub = parts[2] if len(parts) > 2 else None
    sid = parts[3] if len(parts) > 3 else None
    method, conn = ctx.method, ctx.conn

    if resource == "health" and method == "GET":
        return 200, {"status": "ok", "time": now_iso()}
    if resource == "public":
        if ident == "turmas" and method == "GET":
            return 200, auth.public_turmas(conn)
        raise NOT_FOUND
    if resource == "auth":
        return auth.auth_routes(ctx, ident)

    user = ctx.authenticate()
    if user is None:
        raise HTTPError(401, "Faça login para continuar.")
    if user["role"] not in ("admin", "professor", "aluno"):
        raise HTTPError(403, "Perfil inválido. Peça ao administrador para revisar sua conta.")
    ctx.user = user

    if resource == "me" and ident == "password" and method == "PUT":
        return auth.me_password(ctx, user)
    if resource == "me":
        return 200, public_user(user)
    if resource == "dashboard":
        return 200, dashboard.dashboard(conn, user)
    if resource == "disciplines":
        return disciplines.disciplines(ctx, user, ident)
    if resource == "policies":
        return policies.policies(ctx, user, ident)
    if resource == "announcements":
        return announcements.announcements(ctx, user, ident)
    if resource == "history" and method == "GET":
        require_role(user, "professor", "admin")
        return 200, history.history(ctx)
    if parts == ["lia", "reformular"] and method == "POST":
        from app.groq import reformular
        return 200, reformular(ctx, user)
    if parts == ["lia", "consulta"] and method == "POST":
        return 200, lia.consulta(ctx, user)
    if resource == "ai-check" and method == "POST":
        return 200, policies.ai_check(ctx, user)
    if resource == "users":
        return users.users(ctx, user, ident, sub)
    if resource == "turmas":
        return turmas.turmas(ctx, user, ident, sub, sid)
    if resource == "matriculas" and ident and method in ("PUT", "PATCH"):
        return turmas.matricula_update(ctx, user, ident)
    if resource == "notas" and ident and method == "PUT":
        return turmas.nota_save(ctx, user, ident)
    if resource == "alunos" and ident and sub == "password" and method == "PUT":
        return users.aluno_password(ctx, user, ident)
    raise NOT_FOUND
