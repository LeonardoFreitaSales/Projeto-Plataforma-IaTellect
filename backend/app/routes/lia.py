"""Consulta local das políticas cadastradas, limitada ao perfil autenticado."""
import re
import unicodedata

from app.config import LIA_GROQ_ENABLED
from app.utils import text
from .policies import visible_policies


IGNORAR = set("a as o os ao aos de da das do dos e em na nas no nos um uma para por com que qual quais posso usar uso ia chatgpt sobre disciplina atividade filtre filtrar mostre mostrar liste listar politica politicas".split())


TERMOS_STATUS = {
    "proibido": {"proibido", "proibida", "proibidos", "proibidas"},
    "permitido": {"permitido", "permitida", "permitidos", "permitidas"},
    "restricao": {"restricao", "restricoes", "restrita", "restritas", "restrito", "restritos"},
}


def normalizar(valor):
    normal = unicodedata.normalize("NFKD", valor.casefold())
    return " ".join(re.findall(r"[^\W_]+", "".join(c for c in normal if not unicodedata.combining(c))))


def palavras(valor):
    return set(normalizar(valor).split())


FORA = "O assunto não corresponde à plataforma. Posso ajudar com políticas de uso de IA, disciplinas, turmas e navegação."
CONTEXTO = r"\b(?:nessa|nesta|na mesma|dessa|desta) (?:mesma )?(?:materia|disciplina)\b"
IGNORAR |= set("regra regras academica academicas vale pelo pela poderia utilizar plataforma iatellect gostaria saber se".split())
VOCABULARIO = set("ia inteligencia artificial prova provas teste avaliacao trabalho tarefa pesquisa relatorio final parcial materia politica politicas professor permite permitido usar uso ferramenta ferramentas revisao consultar verificar vale aplicavel roteiro entrega orientacao autorizacao preciso conhecer existe pode tem sou aluno aluna estudar fazer devo seguir nesse nessa neste nesta minha meu meus nas dessa desta mesma mesmo deixa".split())
VOCABULARIO |= IGNORAR | set().union(*TERMOS_STATUS.values())


def pertence_ao_escopo(pergunta, politicas):
    termos = palavras(pergunta)
    assuntos = palavras("politica politicas regra regras prova provas avaliacao trabalho tarefa pesquisa relatorio disciplina materia atividade")
    assuntos.update(set().union(*TERMOS_STATUS.values()))
    conhecidos = VOCABULARIO.copy()
    for p in politicas:
        nomes = palavras(p["disciplineName"] + " " + p["activityName"] + " " + p["activityType"])
        assuntos.update(nomes - IGNORAR)
        conhecidos.update(nomes)
    return bool(termos & assuntos) and all(t in conhecidos or t.isdecimal() for t in termos)


# O destino é uma tela existente. O roteador do painel abre a tela após o clique.
DESTINOS = (
    (r"disciplinas?(?: e politicas)?|materias?|politicas", "disciplines", "Disciplinas e políticas", None),
    (r"turmas?(?: e matriculas)?|matriculas?", "classes", "Turmas e matrículas", None),
    (r"comunicados?|avisos?", "announcements", "Comunicados", None),
    (r"uso responsavel|reflexao", "responsible", "Uso responsável", None),
    (r"inicio|painel|visao geral", "home", "Visão geral", None),
    (r"usuarios?(?: e acessos)?", "users", "Usuários e acessos", {"admin"}),
    (r"historico", "history", "Histórico", {"admin", "professor"}),
    (r"relatorios?|clareza das politicas", "reports", "Clareza das políticas", {"admin", "professor"}),
)


def navegacao(frase, role):
    artigos = r"(?:(?:as?|os?|meus?|minhas?|uma?|na|no|tela|de|das?|dos?) )*"
    prefixo = r"(?:(?:onde (?:eu )?(?:(?:posso|consigo) )?(?:vejo|ver|encontro|encontrar|acesso|acessar|ficam?|estao)|como (?:eu )?(?:vejo|ver|acesso|acessar)|abrir|abra|mostrar|mostre|ir para) )"
    if re.fullmatch(r"como (?:eu )?(?:posso )?(?:aprovo|aprovar) (?:uma? |a )?matriculas?", frase):
        if role == "aluno":
            return {"message": "A aprovação de matrículas exige um perfil de professor ou administrador."}
        return {"view": "classes", "label": "Turmas e matrículas",
                "message": "Abra Turmas e matrículas e selecione Consultar matrículas para revisar as solicitações."}
    if re.fullmatch(r"como (?:eu )?(?:posso )?(?:crio|criar|cadastro|cadastrar) (?:uma |a )?politica", frase):
        if role == "aluno":
            return {"message": "O cadastro de políticas exige um perfil de professor ou administrador."}
        return {"view": "disciplines", "label": "Disciplinas e políticas",
                "message": "Abra Disciplinas e políticas e selecione Nova política."}
    for alvo, view, label, roles in DESTINOS:
        if re.fullmatch(prefixo + artigos + "(?:" + alvo + ")", frase):
            if roles and role not in roles:
                return {"message": "Essa tela está disponível apenas para os perfis autorizados."}
            return {"view": view, "label": label, "message": "Você pode consultar essa informação em " + label + "."}
    return None


def consultar_materias(ctx, user, frase):
    from .disciplines import disciplinas_visiveis
    from .turmas import turmas_list

    listar = frase in {"quais sao minhas materias", "quais sao minhas disciplinas", "minhas materias", "minhas disciplinas"}
    pedido = re.fullmatch(r"(?:(?:localize|procure|busque|encontre)(?: para mim)?(?: e confirme se tem)?|confirme se tem|tem|existe) (?:a |uma )?(?:materia|disciplina)(?: (.+))?", frase)
    if not listar and not pedido:
        return None
    termo = pedido.group(1) if pedido else None
    destino = {"view": "disciplines", "label": "Disciplinas e políticas"}
    if pedido and not termo:
        return {**destino, "message": "Qual é o nome da matéria? Envie, por exemplo, “Localize a matéria” seguido do nome."}
    # A consulta do chat é POST. Use a mesma listagem autorizada da tela GET.
    materias = disciplinas_visiveis(ctx.conn, user)
    if termo:
        exatas = [d for d in materias if normalizar(d["name"]) == termo]
        materias = exatas or [d for d in materias if termo in normalizar(d["name"])]
    if not materias:
        return {**destino, "message": "Nenhuma matéria correspondente está disponível para o seu perfil. Confira o nome ou sua matrícula."}
    nomes = ", ".join(d["name"] for d in materias)
    if listar:
        return {**destino, "message": "Matérias disponíveis: " + nomes}
    if len(materias) > 1:
        return {**destino, "message": "Encontrei mais de uma matéria: " + nomes + ". Consulte novamente usando o nome completo."}
    materia = materias[0]
    turmas = [t["name"] for t in turmas_list(ctx.conn, user) if any(d["id"] == materia["id"] for d in t["disciplines"])]
    detalhe = " Turmas: " + ", ".join(turmas) + "." if turmas else " Nenhuma turma vinculada está visível para o seu perfil."
    return {**destino, "disciplineId": materia["id"], "message": "Matéria encontrada: " + materia["name"] + "." + detalhe}


def consulta(ctx, user):
    pergunta = text(ctx.body.get("query"), "query", 500)
    frase = normalizar(pergunta)
    destino = consultar_materias(ctx, user, frase) or navegacao(frase, user["role"])
    if not destino and re.search(r"\b(?:presencas?|frequencia|faltas)\b", frase):
        destino = {"message": "A plataforma não disponibiliza registros de frequência para esta consulta. Confirme a informação com o professor."}
    if destino:
        return {"policies": [], "total": 0, **destino}
    contexto = ctx.body.get("disciplineContext")
    politicas = visible_policies(ctx.conn, user)
    # Remova a fórmula da pergunta sem apagar nomes como "Inteligência Artificial".
    busca = re.sub(r"\b(?:o professor deixa|posso)\s+usar\s+intelig[eê]ncia artificial\b",
                   "usar IA", pergunta, flags=re.IGNORECASE)
    busca = re.sub(CONTEXTO, " ", normalizar(busca))
    busca = re.sub(r"\b(?:e permitido|tenho permissao para|o professor permite) (?:usar|utilizar)\b", "usar", busca)
    termos = palavras(busca) - IGNORAR
    palavras_busca = palavras(busca)
    continuacao = re.match(r"^e\b", frase) or re.search(CONTEXTO, frase)
    disciplina_explicita = any(palavras(p["disciplineName"]) <= palavras_busca for p in politicas)
    if contexto and continuacao and not disciplina_explicita:
        politicas = [p for p in politicas if p["disciplineId"] == contexto]
    status = {chave for chave, nomes in TERMOS_STATUS.items() if termos & nomes}
    termos = termos.difference(*TERMOS_STATUS.values())
    resultados = []
    if termos or status:
        for politica in politicas:
            if status and politica["status"] not in status:
                continue
            campos = ("disciplineName", "activityName", "activityType", "conditions", "details", "status")
            conteudo = " ".join(politica[c] or "" for c in campos)
            if termos <= palavras(conteudo):
                resultados.append(politica)
    resposta = {"policies": resultados[:8], "total": len(resultados)}
    if not resultados:
        if pertence_ao_escopo(pergunta, politicas):
            if LIA_GROQ_ENABLED:
                resposta["podeReformular"] = True
        elif re.fullmatch(r"(?:posso usar ia |qual a politica )(?:na |no |da |do )(?:prova|atividade|trabalho) (?:de |da |do )?[a-z0-9]+(?: de [a-z0-9]+)?", frase):
            # Uma atividade ausente ou invisível recebe a mesma resposta local.
            pass
        elif not pergunta.isdecimal():
            resposta["message"] = FORA
    return resposta
