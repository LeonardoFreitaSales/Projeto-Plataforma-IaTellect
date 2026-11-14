"""Testes de permissao da Plataforma v4.0.

Uso:  python test_permissoes.py
Sobe um servidor temporario (banco novo em pasta temporaria, nao mexe no seu
banco real), roda as verificacoes e encerra.
"""
import hashlib
import json
import sqlite3
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from server import HTTPError, require_role

ROOT = Path(__file__).resolve().parent
PORT = 3999
BASE = f"http://127.0.0.1:{PORT}"
FALHAS = []


class Cliente:
    def __init__(self, nome):
        self.nome, self.cookie = nome, None

    def req(self, metodo, caminho, corpo=None, origem=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        r = urllib.request.Request(BASE + caminho, data=dados, method=metodo)
        r.add_header("Content-Type", "application/json")
        if self.cookie:
            r.add_header("Cookie", self.cookie)
        if origem:
            r.add_header("Origin", origem)
        try:
            resp = urllib.request.urlopen(r)
        except urllib.error.HTTPError as e:
            resp = e
        for h in resp.headers.get_all("Set-Cookie") or []:
            par = h.split(";")[0]
            self.cookie = par if not par.endswith("=") else None
        raw = resp.read().decode()
        try:
            return resp.status if hasattr(resp, "status") else resp.code, json.loads(raw)
        except ValueError:
            return resp.code, raw


def checa(descricao, obtido, esperado):
    ok = obtido == esperado
    print(("OK    " if ok else "FALHA ") + f"{descricao} (esperado {esperado}, veio {obtido})")
    if not ok:
        FALHAS.append(descricao)


def main():
    # Uma linha sem papel nao pode obter permissao; a regra CHECK continua
    # impedindo que esse estado seja gravado no SQLite.
    try:
        require_role({"role": None}, "admin")
        checa("papel ausente e negado", False, True)
    except HTTPError as exc:
        checa("papel ausente e negado", exc.status, 403)
    try:
        require_role({}, "admin")
        checa("objeto sem chave role e negado", False, True)
    except HTTPError as exc:
        checa("objeto sem chave role e negado", exc.status, 403)
    con_check = sqlite3.connect(":memory:")
    con_check.executescript((ROOT / "schema_Banco_de_Dados_SQLite.sql").read_text(encoding="utf-8"))
    try:
        con_check.execute("INSERT INTO users (id,name,nameKey,role,createdAt,updatedAt) VALUES ('x','x','x',NULL,'a','a')")
        checa("NOT NULL rejeita papel ausente", False, True)
    except sqlite3.IntegrityError:
        checa("NOT NULL rejeita papel ausente", True, True)
    try:
        con_check.execute("INSERT INTO users (id,name,nameKey,role,createdAt,updatedAt) VALUES ('y','y','y','desconhecido','a','a')")
        checa("CHECK rejeita papel desconhecido", False, True)
    except sqlite3.IntegrityError:
        checa("CHECK rejeita papel desconhecido", True, True)
    con_check.close()
    tmp = tempfile.mkdtemp()
    env = dict(os.environ, PORT=str(PORT), HOST="127.0.0.1", TEST_MODE="1", TEST_DATA_DIR=tmp,
               ADMIN_PASSWORD="admin-teste-123")
    proc = subprocess.Popen([sys.executable, str(ROOT / "server.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(BASE + "/api/health")
                break
            except Exception:
                time.sleep(0.1)
        anon, adm, pa, pb, al = (Cliente(n) for n in ("anon", "admin", "profA", "profB", "aluno"))

        checa("sem login -> 401", anon.req("GET", "/api/disciplines")[0], 401)
        checa("senha errada -> 401", anon.req("POST", "/api/auth/login", {"name": "admin", "password": "x"})[0], 401)
        checa("login admin", adm.req("POST", "/api/auth/login", {"name": "admin", "password": "admin-teste-123"})[0], 200)
        checa("cookie de origem estranha -> 403", adm.req("POST", "/api/turmas", {"name": "X"}, origem="http://evil.example")[0], 403)

        s, a = adm.req("POST", "/api/users", {"name": "Professor A", "password": "senha-prof-a1"})
        s, b = adm.req("POST", "/api/users", {"name": "Professor B", "password": "senha-prof-b1"})
        checa("senha curta -> 400", adm.req("POST", "/api/users", {"name": "Prof C", "password": "123"})[0], 400)
        checa("prof A login", pa.req("POST", "/api/auth/login", {"name": "Professor A", "password": "senha-prof-a1"})[0], 200)
        checa("prof B login", pb.req("POST", "/api/auth/login", {"name": "Professor B", "password": "senha-prof-b1"})[0], 200)

        s, da = adm.req("POST", "/api/disciplines", {"name": "Matematica", "ownerId": a["id"]})
        s, db = adm.req("POST", "/api/disciplines", {"name": "Historia", "ownerId": b["id"]})
        checa("professor nao cria disciplina -> 403", pa.req("POST", "/api/disciplines", {"name": "Nova"})[0], 403)

        pol = {"disciplineId": da["id"], "activityName": "Prova 1", "activityType": "prova", "status": "proibido"}
        checa("dono cria politica", pa.req("POST", "/api/policies", pol)[0], 201)
        checa("outro professor cria politica na materia alheia -> 403", pb.req("POST", "/api/policies", pol)[0], 403)
        checa("outro professor nao ve a materia -> 404", pb.req("GET", f"/api/disciplines/{da['id']}")[0], 404)
        checa("outro professor nao edita a materia -> 404", pb.req("PUT", f"/api/disciplines/{da['id']}", {"name": "Hack"})[0], 404)
        checa("professor nao troca dono -> 403", pa.req("PUT", f"/api/disciplines/{da['id']}", {"ownerId": b["id"]})[0], 403)
        checa("professor nao cria comunicado -> 403", pa.req("POST", "/api/announcements", {"title": "t", "message": "m"})[0], 403)
        checa("professor nao cria professor -> 403", pa.req("POST", "/api/users", {"name": "Z Z", "password": "12345678"})[0], 403)

        s, t = pa.req("POST", "/api/turmas", {"name": "9o ano"})
        checa("professor cria turma", s, 201)
        checa("vincula a propria materia", pa.req("PUT", f"/api/turmas/{t['id']}/disciplines/{da['id']}")[0], 200)
        checa("nao vincula materia alheia -> 403", pa.req("PUT", f"/api/turmas/{t['id']}/disciplines/{db['id']}")[0], 403)
        s, pub = anon.req("GET", "/api/public/turmas")
        checa("lista publica de turmas", [x["name"] for x in pub], ["9o ano"])

        checa("cadastro com nome simples -> 400", anon.req("POST", "/api/auth/register", {"name": "Maria", "turmaId": t["id"]})[0], 400)
        s, cadastro_ok = al.req("POST", "/api/auth/register", {"name": "Maria Souza", "turmaId": t["id"], "password": "senha-aluna-1"})
        checa("cadastro do aluno retorna resposta neutra", s, 202)
        checa("cadastro nao autentica automaticamente", al.cookie, None)
        checa("cadastro sem senha -> 400", anon.req("POST", "/api/auth/register", {"name": "Carlos Lima", "turmaId": t["id"]})[0], 400)
        checa("cadastro com senha curta -> 400", anon.req("POST", "/api/auth/register", {"name": "Carlos Lima", "turmaId": t["id"], "password": "123"})[0], 400)
        s, dup = anon.req("POST", "/api/auth/register", {"name": "maria  souza", "turmaId": t["id"], "password": "outra-senha-1"})
        checa("conflito de cadastro retorna mesmo status neutro", s, 202)
        checa("conflito nao revela existencia do nome", dup == cadastro_ok, True)
        checa("aluno entra apos solicitar cadastro", al.req("POST", "/api/auth/login", {"name": "Maria Souza", "password": "senha-aluna-1"})[0], 200)
        s, ds = al.req("GET", "/api/disciplines")
        checa("aluno pendente nao ve materias", ds, [])
        checa("aluno nao ve historico -> 403", al.req("GET", "/api/history")[0], 403)
        checa("aluno nao cria politica -> 403", al.req("POST", "/api/policies", pol)[0], 403)

        s, en = pa.req("GET", f"/api/turmas/{t['id']}/enrollments")
        checa("professor da turma lista alunos", [e["studentName"] for e in en], ["Maria Souza"])
        checa("professor B nao lista alunos -> 403", pb.req("GET", f"/api/turmas/{t['id']}/enrollments")[0], 403)
        checa("professor B nao aprova -> 403", pb.req("PUT", f"/api/matriculas/{en[0]['id']}", {"status": "aprovada"})[0], 403)
        checa("professor A aprova", pa.req("PUT", f"/api/matriculas/{en[0]['id']}", {"status": "aprovada"})[0], 200)
        checa("status invalido -> 400", pa.req("PUT", f"/api/matriculas/{en[0]['id']}", {"status": "x"})[0], 400)

        s, ds = al.req("GET", "/api/disciplines")
        checa("aluno aprovado ve so a materia da turma", [d["name"] for d in ds], ["Matematica"])
        checa("aluno nao ve materia de fora -> 404", al.req("GET", f"/api/disciplines/{db['id']}")[0], 404)
        al2 = Cliente("aluno2")
        checa("aluno com senha nao entra so com o nome -> 401", al2.req("POST", "/api/auth/login", {"name": "maria souza"})[0], 401)
        checa("aluno entra com nome e senha", al2.req("POST", "/api/auth/login", {"name": "maria souza", "password": "senha-aluna-1"})[0], 200)

        checa("anotacao privada (prof A)", pa.req("PUT", f"/api/notas/{en[0]['studentId']}", {"text": "Atencao"})[0], 200)
        s, notas = pa.req("GET", f"/api/turmas/{t['id']}/notes")
        checa("prof A ve a propria anotacao", list(notas.values()), ["Atencao"])
        checa("admin nao le anotacoes -> 403", adm.req("GET", f"/api/turmas/{t['id']}/notes")[0], 403)
        checa("aluno nao grava anotacao -> 403", al.req("PUT", f"/api/notas/{en[0]['studentId']}", {"text": "x"})[0], 403)
        checa("prof B nao grava anotacao -> 404", pb.req("PUT", f"/api/notas/{en[0]['studentId']}", {"text": "x"})[0], 404)

        s, h = pa.req("GET", "/api/history?limit=500")
        checa("historico tem autor", h[0].get("authorName") is not None, True)
        checa("professor nao exclui turma alheia (so criador/admin)", pb.req("DELETE", f"/api/turmas/{t['id']}")[0], 403)

        # --- Integração do login: tela de acesso e matriz de permissões ---
        s, pagina = anon.req("GET", "/acesso.html")
        checa("tela de acesso e servida sem login -> 200", s, 200)
        checa("tela de acesso nao traz senha fixa", isinstance(pagina, str) and "modoprofessor" not in pagina, True)
        checa("professor sem senha -> 401", Cliente("sem-senha").req("POST", "/api/auth/login", {"name": "Professor A"})[0], 401)
        checa("aluno nao lista usuarios -> 403", al.req("GET", "/api/users")[0], 403)
        checa("professor nao lista usuarios -> 403", pa.req("GET", "/api/users")[0], 403)
        checa("admin lista usuarios -> 200", adm.req("GET", "/api/users")[0], 200)
        checa("aluno nao cria comunicado -> 403", al.req("POST", "/api/announcements", {"title": "t", "message": "m"})[0], 403)
        checa("aluno nao cria disciplina -> 403", al.req("POST", "/api/disciplines", {"name": "Nova 2"})[0], 403)
        checa("aluno nao cria turma -> 403", al.req("POST", "/api/turmas", {"name": "Turma X"})[0], 403)
        checa("aluno nao lista alunos da turma -> 403", al.req("GET", f"/api/turmas/{t['id']}/enrollments")[0], 403)
        checa("aluno nao redefine senha -> 403", al.req("PUT", f"/api/users/{a['id']}/password", {"password": "12345678"})[0], 403)
        checa("professor nao redefine senha -> 403", pa.req("PUT", f"/api/users/{b['id']}/password", {"password": "12345678"})[0], 403)
        forjado = Cliente("forjado")
        forjado.cookie = "plataforma_v4_sessao=token-que-nao-existe"
        checa("sessao invalida -> 401", forjado.req("GET", "/api/me")[0], 401)
        con = sqlite3.connect(Path(tmp) / "Banco de Dados SQLite.db", timeout=10)
        admin_id = con.execute("SELECT id FROM users WHERE role = 'admin'").fetchone()[0]
        con.execute("INSERT INTO sessions (tokenHash, userId, createdAt, expiresAt) VALUES (?,?,?,?)",
                    (hashlib.sha256(b"token-expirado").hexdigest(), admin_id, "2000-01-01T00:00:00.000Z", "2000-01-02T00:00:00.000Z"))
        con.commit()
        con.close()
        expirado = Cliente("expirado")
        expirado.cookie = "plataforma_v4_sessao=token-expirado"
        checa("sessao expirada -> 401", expirado.req("GET", "/api/me")[0], 401)

        # --- 3b: conta antiga sem senha, definir senha do aluno e histórico restrito ---
        con = sqlite3.connect(Path(tmp) / "Banco de Dados SQLite.db", timeout=10)
        con.execute("INSERT INTO users (id, name, nameKey, role, passwordHash, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)",
                    ("aluno-antigo", "Joao Antigo", "joao antigo", "aluno", None, "2026-01-01T00:00:00.000Z", "2026-01-01T00:00:00.000Z"))
        con.execute("INSERT INTO matriculas (id, turmaId, studentId, status, createdAt, updatedAt) VALUES (?,?,?,?,?,?)",
                    ("mat-antiga", t["id"], "aluno-antigo", "aprovada", "2026-01-01T00:00:00.000Z", "2026-01-01T00:00:00.000Z"))
        con.commit()
        con.close()
        antigo = Cliente("antigo")
        checa("conta antiga sem senha bloqueada", antigo.req("POST", "/api/auth/login", {"name": "Joao Antigo"})[0], 401)
        checa("senha arbitraria nao libera conta antiga", antigo.req("POST", "/api/auth/login", {"name": "Joao Antigo", "password": "qualquer-senha"})[0], 401)
        con = sqlite3.connect(Path(tmp) / "Banco de Dados SQLite.db")
        con.execute("INSERT INTO sessions VALUES (?,?,?,?)", (hashlib.sha256(b"sessao-legada").hexdigest(), "aluno-antigo", "2026-01-01", "2099-01-01"))
        con.commit()
        con.close()
        antigo.cookie = "plataforma_v4_sessao=sessao-legada"
        checa("sessao legada sem senha bloqueada", antigo.req("GET", "/api/me")[0], 401)
        checa("sessao legada nao acessa materias", antigo.req("GET", "/api/disciplines")[0], 401)
        checa("aluno nao define senha de aluno -> 403", al.req("PUT", "/api/alunos/aluno-antigo/password", {"password": "12345678"})[0], 403)
        checa("professor sem relacao com a turma nao define senha -> 404", pb.req("PUT", "/api/alunos/aluno-antigo/password", {"password": "12345678"})[0], 404)
        checa("senha curta -> 400", pa.req("PUT", "/api/alunos/aluno-antigo/password", {"password": "123"})[0], 400)
        checa("professor da turma define senha do aluno", pa.req("PUT", "/api/alunos/aluno-antigo/password", {"password": "senha-do-joao-1"})[0], 200)
        checa("sessao antiga do aluno e encerrada", antigo.req("GET", "/api/me")[0], 401)
        checa("aluno com senha definida nao entra so com o nome -> 401", Cliente("antigo2").req("POST", "/api/auth/login", {"name": "Joao Antigo"})[0], 401)
        checa("aluno entra com a senha definida", Cliente("antigo3").req("POST", "/api/auth/login", {"name": "Joao Antigo", "password": "senha-do-joao-1"})[0], 200)
        con = sqlite3.connect(Path(tmp) / "Banco de Dados SQLite.db")
        checa("matricula antiga preservada apos definir senha", con.execute("SELECT status FROM matriculas WHERE id='mat-antiga'").fetchone(), ("aprovada",))
        con.close()
        checa("admin define senha de aluno", adm.req("PUT", "/api/alunos/aluno-antigo/password", {"password": "senha-do-joao-2"})[0], 200)
        adm.req("POST", "/api/announcements", {"title": "Aviso", "message": "Teste"})
        ids_a = {h["entityId"] for h in pa.req("GET", "/api/history?limit=500")[1]}
        ids_b = {h["entityId"] for h in pb.req("GET", "/api/history?limit=500")[1]}
        ids_adm = {h["entityId"] for h in adm.req("GET", "/api/history?limit=500")[1]}
        checa("historico do professor A tem a propria materia", da["id"] in ids_a, True)
        checa("historico do professor A nao tem materia do professor B", db["id"] not in ids_a, True)
        checa("historico do professor A nao tem cadastro de usuarios", a["id"] not in ids_a and b["id"] not in ids_a, True)
        checa("historico do professor B tem a propria materia", db["id"] in ids_b, True)
        checa("historico do professor B nao tem materia do professor A", da["id"] not in ids_b, True)
        checa("admin ve o historico completo", {da["id"], db["id"], a["id"]} <= ids_adm, True)
        checa("professor nao ve comunicados no historico", not any(h["entity"] == "announcement" for h in pa.req("GET", "/api/history?limit=500")[1]), True)

        # --- alterar a própria senha ---
        checa("alterar senha sem login -> 401", Cliente("anon-pw").req("PUT", "/api/me/password", {"currentPassword": "x", "newPassword": "12345678"})[0], 401)
        checa("senha atual errada -> 403", al2.req("PUT", "/api/me/password", {"currentPassword": "errada-123", "newPassword": "nova-senha-1"})[0], 403)
        checa("nova senha curta -> 400", al2.req("PUT", "/api/me/password", {"currentPassword": "senha-aluna-1", "newPassword": "123"})[0], 400)
        checa("nova senha igual a atual -> 400", al2.req("PUT", "/api/me/password", {"currentPassword": "senha-aluna-1", "newPassword": "senha-aluna-1"})[0], 400)
        checa("aluno altera a propria senha", al2.req("PUT", "/api/me/password", {"currentPassword": "senha-aluna-1", "newPassword": "senha-aluna-2"})[0], 200)
        checa("sessao atual continua valida", al2.req("GET", "/api/me")[0], 200)
        checa("outras sessoes do aluno sao encerradas", al.req("GET", "/api/me")[0], 401)
        checa("senha antiga nao entra mais -> 401", Cliente("n1").req("POST", "/api/auth/login", {"name": "maria souza", "password": "senha-aluna-1"})[0], 401)
        checa("senha nova entra", Cliente("n2").req("POST", "/api/auth/login", {"name": "maria souza", "password": "senha-aluna-2"})[0], 200)
        checa("professor altera a propria senha", pa.req("PUT", "/api/me/password", {"currentPassword": "senha-prof-a1", "newPassword": "senha-prof-a2"})[0], 200)
        con = sqlite3.connect(Path(tmp) / "Banco de Dados SQLite.db", timeout=10)
        con.execute("INSERT INTO users (id, name, nameKey, role, passwordHash, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)",
                    ("aluno-antigo-2", "Ana Antiga", "ana antiga", "aluno", None, "2026-01-01T00:00:00.000Z", "2026-01-01T00:00:00.000Z"))
        con.commit()
        con.close()
        ana = Cliente("ana")
        ana.req("POST", "/api/auth/login", {"name": "Ana Antiga"})
        checa("conta bloqueada nao se autodefine senha -> 401", ana.req("PUT", "/api/me/password", {"currentPassword": "", "newPassword": "12345678"})[0], 401)
        tentativas = [pb.req("PUT", "/api/me/password", {"currentPassword": "errada", "newPassword": "12345678"})[0] for _ in range(6)]
        checa("bloqueio apos varias senhas atuais erradas", tentativas[-1], 429)

        checa("admin exclui turma", adm.req("DELETE", f"/api/turmas/{t['id']}")[0], 200)
        con = sqlite3.connect(Path(tmp) / "Banco de Dados SQLite.db")
        checa("exclusao remove matriculas da turma", con.execute("SELECT COUNT(*) FROM matriculas WHERE turmaId=?", (t["id"],)).fetchone()[0], 0)
        checa("exclusao preserva conta do aluno", con.execute("SELECT COUNT(*) FROM users WHERE id='aluno-antigo'").fetchone()[0], 1)
        con.close()

        checa("server.py nao e servido -> 404", anon.req("GET", "/server.py")[0], 404)
        checa("banco nao e servido -> 404", anon.req("GET", "/data/Banco%20de%20Dados%20SQLite.db")[0], 404)
        checa("logout", pa.req("POST", "/api/auth/logout")[0], 200)
        checa("apos logout -> 401", pa.req("GET", "/api/me")[0], 401)

        spam = Cliente("spam")
        codigos = [spam.req("POST", "/api/auth/login", {"name": "Professor A", "password": "errada"})[0] for _ in range(7)]
        checa("bloqueio apos varias tentativas", codigos[-1], 429)
    finally:
        proc.terminate()
        proc.wait()
    print("\nTudo certo." if not FALHAS else f"\n{len(FALHAS)} falha(s): {FALHAS}")
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
