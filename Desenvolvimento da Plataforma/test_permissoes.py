"""Testes de permissao da Plataforma v3.0.

Uso:  python test_permissoes.py
Sobe um servidor temporario (banco novo em pasta temporaria, nao mexe no seu
banco real), roda as verificacoes e encerra.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

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
        checa("cadastro do aluno", al.req("POST", "/api/auth/register", {"name": "Maria Souza", "turmaId": t["id"]})[0], 201)
        checa("nome repetido -> 409", anon.req("POST", "/api/auth/register", {"name": "maria  souza", "turmaId": t["id"]})[0], 409)
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
        checa("aluno entra so com o nome", al2.req("POST", "/api/auth/login", {"name": "maria souza"})[0], 200)

        checa("anotacao privada (prof A)", pa.req("PUT", f"/api/notas/{en[0]['studentId']}", {"text": "Atencao"})[0], 200)
        s, notas = pa.req("GET", f"/api/turmas/{t['id']}/notes")
        checa("prof A ve a propria anotacao", list(notas.values()), ["Atencao"])
        checa("admin nao le anotacoes -> 403", adm.req("GET", f"/api/turmas/{t['id']}/notes")[0], 403)
        checa("aluno nao grava anotacao -> 403", al.req("PUT", f"/api/notas/{en[0]['studentId']}", {"text": "x"})[0], 403)
        checa("prof B nao grava anotacao -> 404", pb.req("PUT", f"/api/notas/{en[0]['studentId']}", {"text": "x"})[0], 404)

        s, h = pa.req("GET", "/api/history?limit=500")
        checa("historico tem autor", h[0].get("authorName") is not None, True)
        checa("professor nao exclui turma alheia (so criador/admin)", pb.req("DELETE", f"/api/turmas/{t['id']}")[0], 403)

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
