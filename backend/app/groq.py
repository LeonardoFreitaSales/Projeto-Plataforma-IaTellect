"""Reformulação opcional; a Groq recebe apenas a pergunta escolhida."""
import json
from http.client import HTTPSConnection, HTTPException

from app.config import GROQ_API_KEY, GROQ_MODEL, LIA_GROQ_ENABLED
from app.ratelimit import RateLimiter
from app.utils import HTTPError, text
from app.routes.lia import FORA, IGNORAR, palavras, pertence_ao_escopo
from app.routes.policies import visible_policies


limite = RateLimiter(10, 60)


def reformular(ctx, user):
    pergunta = text(ctx.body.get("query"), "query", 500)
    if not LIA_GROQ_ENABLED:
        raise HTTPError(503, "Reformulação indisponível.")
    if not pertence_ao_escopo(pergunta, visible_policies(ctx.conn, user)):
        raise HTTPError(400, FORA)
    if not limite.try_add(user["id"]):
        raise HTTPError(429, "Aguarde um minuto para reformular outra pergunta.")
    dados = {
        "model": GROQ_MODEL, "temperature": 0, "max_completion_tokens": 512,
        "messages": [
            {"role": "system", "content": "Reescreva em português como termos curtos de busca de políticas acadêmicas. Preserve disciplina, atividade e situação mencionadas. Retorne só a consulta, sem responder, inferir regras ou inventar nomes."},
            {"role": "user", "content": pergunta},
        ],
    }
    conn = HTTPSConnection("api.groq.com", timeout=8)
    try:
        conn.request("POST", "/openai/v1/chat/completions", json.dumps(dados),
                     {"Authorization": "Bearer " + GROQ_API_KEY, "Content-Type": "application/json"})
        resp = conn.getresponse()
        if resp.status != 200:
            raise HTTPError(503, "Groq indisponível ou com limite de uso atingido. A busca local continua disponível.")
        sugestao = json.loads(resp.read(16384))["choices"][0]["message"]["content"]
        if not isinstance(sugestao, str) or not 1 <= len(sugestao.strip()) <= 500:
            raise ValueError("consulta inválida")
        # Exiba somente termos da pergunta original, sem afirmações geradas pelo modelo.
        termos = palavras(pergunta) - IGNORAR
        sugeridos = [t for t in sugestao.split() if palavras(t) and palavras(t) <= termos]
        if not sugeridos:
            raise HTTPError(422, "Tente o nome da disciplina ou da atividade.")
        return {"query": " ".join(sugeridos)}
    except (OSError, HTTPException, ValueError, KeyError, IndexError, TypeError):
        raise HTTPError(503, "Não foi possível reformular a pergunta agora.")
    finally:
        conn.close()
