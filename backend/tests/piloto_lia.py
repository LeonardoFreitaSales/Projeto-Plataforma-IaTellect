"""Piloto local da Lia com banco temporário e dados inteiramente fictícios."""
import argparse
import tempfile
import time

import test_permissoes as suporte


def requisitar(cliente, metodo, rota, dados=None):
    status, resposta = cliente.req(metodo, rota, dados)
    if not 200 <= status < 300:
        raise RuntimeError(f"{metodo} {rota}: HTTP {status}")
    return resposta


def preparar():
    admin, professor, aluno = (suporte.Cliente(nome) for nome in ("admin", "professor", "aluno"))
    requisitar(admin, "POST", "/api/auth/login", {"name": "admin", "password": "admin-teste-123"})
    docente = {"name": "Professor Fictício", "password": "piloto-docente-123"}
    estudante = {"name": "Aluno Fictício", "password": "piloto-aluno-123"}
    dono = requisitar(admin, "POST", "/api/users", docente)
    requisitar(professor, "POST", "/api/auth/login", docente)
    turma = requisitar(professor, "POST", "/api/turmas", {"name": "Turma Fictícia da Lia"})
    for nome, regra in [("Estatística", "proibido"), ("História", "permitido")]:
        materia = requisitar(admin, "POST", "/api/disciplines", {"name": nome, "ownerId": dono["id"]})
        requisitar(professor, "PUT", f"/api/turmas/{turma['id']}/disciplines/{materia['id']}")
        for tipo, status in [("prova", regra), ("trabalho", "restricao")]:
            requisitar(professor, "POST", "/api/policies", {
                "disciplineId": materia["id"], "activityName": tipo.capitalize() + " final",
                "activityType": tipo, "status": status, "source": "Guia fictício de " + nome,
                "conditions": "Somente para revisão ortográfica." if tipo == "trabalho" else "",
            })
    requisitar(aluno, "POST", "/api/auth/register", {**estudante, "turmaId": turma["id"]})
    matricula, = requisitar(professor, "GET", f"/api/turmas/{turma['id']}/enrollments")
    requisitar(professor, "PUT", "/api/matriculas/" + matricula["id"], {"status": "aprovada"})
    requisitar(aluno, "POST", "/api/auth/login", estudante)
    for nome, esperado in [("História", "permitido"), ("Estatística", "proibido")]:
        res = requisitar(aluno, "POST", "/api/lia/consulta", {"query": "Prova final de " + nome})
        if [p["status"] for p in res["policies"]] != [esperado]:
            raise RuntimeError("Verifique a política fictícia de " + nome)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="prepara, testa os acessos e encerra")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="iatellect-piloto-") as pasta, suporte.servidor_de_teste(pasta) as url:
        suporte.BASE = url
        preparar()
        print("TESTE COM DADOS FICTÍCIOS | Professor, aluno e regras das provas verificados.", flush=True)
        if not args.verificar:
            print(f"Abra {url} | Ctrl+C encerra o piloto e descarta os dados.", flush=True)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
