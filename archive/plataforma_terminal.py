"""
Painel de políticas de uso de IA — versão para terminal (Python puro).

Simula no terminal tudo o que a plataforma web faz (index.html + app.js + server.py):
disciplinas, políticas, "Posso usar IA?", comunicados, histórico e ferramentas.

Usa o mesmo arquivo data/database.json do server.py, então os dados são
compartilhados entre a versão web e a versão de terminal.

Executar:  python plataforma_terminal.py
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "database.json"

STATUSES = {"proibido": "Proibido", "restricao": "Permitido com restrição", "permitido": "Permitido"}
TYPES = ["prova", "trabalho", "atividade", "pesquisa", "outro"]
SENHA_PROFESSOR = "modoprofessor"  # protótipo: igual à tela de acesso, não é segurança real

os.system("")  # habilita cores ANSI no terminal do Windows
COR = {"proibido": "\033[91m", "restricao": "\033[93m", "permitido": "\033[92m",
       "sem_politica": "\033[90m", "titulo": "\033[1;96m", "fim": "\033[0m"}


# ---------------------------------------------------------------- banco de dados
def agora():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def banco_vazio():
    return {"disciplines": [], "policies": [], "announcements": [], "history": []}


def salvar(db):
    """Gravação atômica: escreve em .tmp e troca pelo arquivo final."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(DB_FILE) + ".tmp")
    tmp.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DB_FILE)


def carregar():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        db = banco_vazio()
        salvar(db)
        return db
    try:
        db = banco_vazio()
        db.update(json.loads(DB_FILE.read_text(encoding="utf-8")))
        return db
    except Exception:
        raise SystemExit(f"Não foi possível ler {DB_FILE}. Corrija o JSON antes de iniciar.")


db = carregar()


def registrar(acao, entidade, entidade_id, resumo):
    db["history"].insert(0, {"id": str(uuid.uuid4()), "action": acao, "entity": entidade,
                             "entityId": entidade_id, "summary": resumo, "createdAt": agora()})
    db["history"] = db["history"][:500]
    salvar(db)


# ---------------------------------------------------------------- entrada de dados
def titulo(texto):
    print(f"\n{COR['titulo']}=== {texto} ==={COR['fim']}")


def pausa():
    input("\nPressione Enter para continuar...")


def perguntar(rotulo, maximo=5000, obrigatorio=False, atual=""):
    """Lê um texto validando tamanho. Se 'atual' existir, Enter mantém o valor."""
    while True:
        dica = f" [{atual}]" if atual else ""
        valor = input(f"{rotulo}{' *' if obrigatorio else ''}{dica}: ").strip()
        if not valor:
            valor = atual
        if obrigatorio and not valor:
            print("  ! Campo obrigatório.")
        elif len(valor) > maximo:
            print(f"  ! Excede {maximo} caracteres.")
        else:
            return valor


def escolher(rotulo, opcoes, atual=None):
    """opcoes: lista de (chave, texto). Retorna a chave escolhida."""
    print(f"\n{rotulo}")
    for i, (_, texto) in enumerate(opcoes, 1):
        print(f"  {i}) {texto}")
    while True:
        dica = f" [Enter mantém: {atual}]" if atual else ""
        resp = input(f"Escolha{dica}: ").strip()
        if not resp and atual:
            return atual
        if resp.isdigit() and 1 <= int(resp) <= len(opcoes):
            return opcoes[int(resp) - 1][0]
        print("  ! Opção inválida.")


def confirmar(pergunta):
    return input(f"{pergunta} (s/n): ").strip().lower() in ("s", "sim")


def escolher_disciplina(rotulo="Disciplina", atual_id=None):
    if not db["disciplines"]:
        print("Cadastre uma disciplina antes.")
        return None
    ops = [(d["id"], d["name"]) for d in db["disciplines"]]
    return escolher(rotulo, ops, atual_id)


def nome_disciplina(disc_id):
    d = next((x for x in db["disciplines"] if x["id"] == disc_id), None)
    return d["name"] if d else "—"


# ---------------------------------------------------------------- acesso
def acesso():
    titulo("Acesso ao painel")
    perfil = escolher("Escolha seu perfil:", [("aluno", "Sou aluno"), ("professor", "Sou professor")])
    nome = perguntar("Nome", 100, True)
    if perfil == "professor":
        for _ in range(3):
            if input("Senha do professor: ").strip() == SENHA_PROFESSOR:
                return nome, perfil
            print("  ! Senha incorreta.")
        print("Tentativas esgotadas. Entrando como aluno.")
        return nome, "aluno"
    return nome, perfil


# ---------------------------------------------------------------- início
def inicio(usuario):
    titulo("Políticas de uso de IA")
    print(f"Conectado como {usuario[0]} ({usuario[1]})")
    contagem = {"proibido": 0, "restricao": 0, "permitido": 0}
    for p in db["policies"]:
        if p.get("status") in contagem:
            contagem[p["status"]] += 1
    total = sum(contagem.values())
    print(f"\nDisciplinas: {len(db['disciplines'])}   Políticas: {len(db['policies'])}")
    if not db["disciplines"]:
        print("\nPor onde começar: cadastre uma disciplina e registre a política de IA de cada atividade.")
    print("\nDistribuição por nível:")
    for chave, qtd in contagem.items():
        barra = "█" * (round(qtd / total * 30) if total else 0)
        print(f"  {COR[chave]}{STATUSES[chave]:<24}{COR['fim']} {qtd:>3} {COR[chave]}{barra}{COR['fim']}")
    ativos = [a for a in db["announcements"] if a.get("active")][:5]
    print("\nComunicados:")
    if not ativos:
        print("  Nenhum comunicado no momento.")
    for a in ativos:
        print(f"  * {a['title']}\n    {a['message']}")


# ---------------------------------------------------------------- disciplinas
def gerenciar_disciplinas():
    while True:
        titulo("Disciplinas")
        if not db["disciplines"]:
            print("Nenhuma disciplina cadastrada.")
        for i, d in enumerate(db["disciplines"], 1):
            print(f"  {i}. {d['name']}  | código: {d.get('code') or '—'}  | docente: {d.get('instructor') or '—'}")
        op = escolher("O que deseja fazer?", [("add", "Adicionar disciplina"), ("edit", "Editar"),
                                              ("del", "Remover"), ("voltar", "Voltar")])
        if op == "voltar":
            return
        if op == "add":
            nome = perguntar("Nome da disciplina", 180, True)
            if any(d["name"].lower() == nome.lower() for d in db["disciplines"]):
                print("  ! Já existe uma disciplina com esse nome.")
                continue
            item = {"id": str(uuid.uuid4()), "name": nome, "code": perguntar("Código", 40),
                    "instructor": perguntar("Docente", 180), "createdAt": agora(), "updatedAt": agora()}
            db["disciplines"].append(item)
            registrar("created", "discipline", item["id"], f"Disciplina criada: {nome}")
            print("Disciplina salva.")
        else:
            did = escolher_disciplina("Qual disciplina?")
            if not did:
                continue
            item = next(d for d in db["disciplines"] if d["id"] == did)
            if op == "edit":
                nome = perguntar("Nome da disciplina", 180, True, item["name"])
                if any(d["id"] != did and d["name"].lower() == nome.lower() for d in db["disciplines"]):
                    print("  ! Já existe uma disciplina com esse nome.")
                    continue
                item.update(name=nome, code=perguntar("Código", 40, atual=item.get("code", "")),
                            instructor=perguntar("Docente", 180, atual=item.get("instructor", "")),
                            updatedAt=agora())
                registrar("updated", "discipline", did, f"Disciplina atualizada: {nome}")
                print("Disciplina atualizada.")
            else:
                if any(p["disciplineId"] == did for p in db["policies"]):
                    print("  ! Remova ou mova as políticas desta disciplina antes de excluí-la.")
                elif confirmar(f"Remover '{item['name']}'?"):
                    db["disciplines"] = [d for d in db["disciplines"] if d["id"] != did]
                    registrar("deleted", "discipline", did, f"Disciplina removida: {item['name']}")
                    print("Disciplina removida.")


# ---------------------------------------------------------------- políticas
def mostrar_politicas(lista):
    if not lista:
        print("Nenhuma política encontrada.")
    for i, p in enumerate(lista, 1):
        cor = COR[p["status"]]
        print(f"\n{i}. {nome_disciplina(p['disciplineId'])} — {p['activityName']} ({p['activityType']})")
        print(f"   Uso de IA: {cor}{STATUSES[p['status']]}{COR['fim']}")
        texto = p.get("conditions") or p.get("details")
        if texto:
            print(f"   Condições: {texto}")
        if p.get("source"):
            print(f"   Fonte: {p['source']}")


def listar_politicas():
    titulo("Todas as políticas")
    busca = input("Buscar por atividade ou disciplina (Enter = todas): ").strip().lower()
    filtro = escolher("Filtrar por nível:", [("", "Todos os níveis")] + list(STATUSES.items()))
    lista = [p for p in db["policies"]
             if (not filtro or p["status"] == filtro)
             and busca in f"{p['activityName']} {nome_disciplina(p['disciplineId'])}".lower()]
    mostrar_politicas(lista)


def formulario_politica(item=None):
    item = item or {}
    did = escolher_disciplina("Disciplina *", item.get("disciplineId"))
    if not did:
        return
    tipo = escolher("Tipo de atividade:", [(t, t.capitalize()) for t in TYPES], item.get("activityType"))
    nome = perguntar("Atividade (ex.: Relatório final)", 180, True, item.get("activityName", ""))
    status = escolher("Uso de IA:", list(STATUSES.items()), item.get("status"))
    dados = dict(disciplineId=did, activityType=tipo, activityName=nome, status=status,
                 conditions=perguntar("Condições", 3000, atual=item.get("conditions", "")),
                 details=perguntar("Detalhes", 5000, atual=item.get("details", "")),
                 source=perguntar("Fonte", 500, atual=item.get("source", "")), updatedAt=agora())
    if item:
        item.update(dados)
        registrar("updated", "policy", item["id"], f"Política atualizada: {nome}")
        print("Política atualizada.")
    else:
        novo = {"id": str(uuid.uuid4()), **dados, "createdAt": agora()}
        db["policies"].append(novo)
        registrar("created", "policy", novo["id"], f"Política criada: {nome}")
        print("Política salva.")


def gerenciar_politicas():
    while True:
        titulo("Políticas")
        op = escolher("O que deseja fazer?", [("add", "Adicionar política"), ("edit", "Editar política"),
                                              ("del", "Remover política"), ("ver", "Ver todas"),
                                              ("voltar", "Voltar")])
        if op == "voltar":
            return
        if op == "add":
            if not db["disciplines"]:
                print("Cadastre uma disciplina antes de criar políticas.")
            else:
                formulario_politica()
        elif op == "ver":
            listar_politicas()
        else:
            if not db["policies"]:
                print("Nenhuma política cadastrada.")
                continue
            ops = [(p["id"], f"{nome_disciplina(p['disciplineId'])} · {p['activityName']} "
                             f"[{STATUSES[p['status']]}]") for p in db["policies"]]
            pid = escolher("Qual política?", ops)
            item = next(p for p in db["policies"] if p["id"] == pid)
            if op == "edit":
                formulario_politica(item)
            elif confirmar(f"Remover '{item['activityName']}'?"):
                db["policies"] = [p for p in db["policies"] if p["id"] != pid]
                registrar("deleted", "policy", pid, f"Política removida: {item['activityName']}")
                print("Política removida.")


# ---------------------------------------------------------------- posso usar IA?
def posso_usar_ia():
    titulo("Posso usar IA?")
    did = escolher_disciplina()
    if not did:
        return
    tipo = escolher("Tipo de atividade:", [(t, t.capitalize()) for t in TYPES])
    achadas = [p for p in db["policies"]
               if p["disciplineId"] == did and p["activityType"] in (tipo, "outro")]
    if not achadas:
        decisao = "sem_politica"
    elif any(p["status"] == "proibido" for p in achadas):
        decisao = "proibido"
    elif any(p["status"] == "restricao" for p in achadas):
        decisao = "restricao"
    else:
        decisao = "permitido"
    rotulos = {**STATUSES, "sem_politica": "Sem política cadastrada"}
    print(f"\nResultado: {COR[decisao]}{rotulos[decisao]}{COR['fim']}")
    if achadas:
        print(f"{len(achadas)} regra(s) encontrada(s):")
        mostrar_politicas(achadas)
    else:
        print("Nenhuma política cadastrada para esta atividade.")


# ---------------------------------------------------------------- comunicados, histórico, ferramentas
def comunicados():
    while True:
        titulo("Comunicados")
        if not db["announcements"]:
            print("Nenhum comunicado publicado.")
        for a in db["announcements"]:
            print(f"* {a['title']}\n  {a['message']}")
        op = escolher("O que deseja fazer?", [("new", "Novo comunicado"), ("del", "Remover comunicado"),
                                              ("voltar", "Voltar")])
        if op == "voltar":
            return
        if op == "new":
            item = {"id": str(uuid.uuid4()), "title": perguntar("Título", 180, True),
                    "message": perguntar("Mensagem", 3000, True), "active": True,
                    "createdAt": agora(), "updatedAt": agora()}
            db["announcements"].insert(0, item)
            registrar("created", "announcement", item["id"], f"Comunicado criado: {item['title']}")
            print("Comunicado publicado.")
        elif db["announcements"]:
            aid = escolher("Qual comunicado?", [(a["id"], a["title"]) for a in db["announcements"]])
            item = next(a for a in db["announcements"] if a["id"] == aid)
            if confirmar(f"Remover '{item['title']}'?"):
                db["announcements"] = [a for a in db["announcements"] if a["id"] != aid]
                registrar("deleted", "announcement", aid, f"Comunicado removido: {item['title']}")
                print("Comunicado removido.")


def historico():
    titulo("Histórico (últimas 20 alterações)")
    if not db["history"]:
        print("O histórico aparecerá após as primeiras alterações.")
    for h in db["history"][:20]:
        quando = datetime.fromisoformat(h["createdAt"].replace("Z", "+00:00")).astimezone()
        print(f"{quando:%d/%m/%Y %H:%M}  {h['action']:<8} {h['summary']}")


def ferramentas():
    titulo("Ferramentas")
    print(f"Armazenamento ativo: {DB_FILE}")
    print(f"Hora: {datetime.now():%d/%m/%Y %H:%M:%S}")
    print(f"Registros: {len(db['disciplines'])} disciplinas, {len(db['policies'])} políticas, "
          f"{len(db['announcements'])} comunicados, {len(db['history'])} itens no histórico.")


def ajuda():
    titulo("Guia e ajuda")
    print("Cadastre disciplinas e políticas em 'Gerenciar'. Em 'Posso usar IA?', escolha a disciplina\n"
          "e a atividade para consultar as regras. As alterações ficam no Histórico.\n"
          f"Os dados são guardados em {DB_FILE}.")


# ---------------------------------------------------------------- menu principal
MENU = [
    ("1", "Início", None),
    ("2", "Todas as políticas", listar_politicas),
    ("3", "Posso usar IA?", posso_usar_ia),
    ("4", "Gerenciar disciplinas", gerenciar_disciplinas),
    ("5", "Gerenciar políticas", gerenciar_politicas),
    ("6", "Comunicados", comunicados),
    ("7", "Histórico", historico),
    ("8", "Ferramentas", ferramentas),
    ("9", "Guia e ajuda", ajuda),
    ("0", "Sair", None),
]


def main():
    usuario = acesso()
    inicio(usuario)
    while True:
        titulo("Menu")
        for tecla, texto, _ in MENU:
            print(f"  {tecla}) {texto}")
        escolha = input("Opção: ").strip()
        if escolha == "0":
            print("Até logo!")
            return
        if escolha == "1":
            inicio(usuario)
            continue
        acao = next((f for t, _, f in MENU if t == escolha), None)
        if acao is None:
            print("Opção inválida.")
            continue
        acao()
        if acao in (listar_politicas, posso_usar_ia, historico, ferramentas, ajuda):
            pausa()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrado.")
