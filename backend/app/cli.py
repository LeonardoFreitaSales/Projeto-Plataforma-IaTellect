"""Plataforma v4.0 - servidor (Python 3 + SQLite, sem bibliotecas externas).

Perfis: admin, professor e aluno.
- admin: tudo (comunicados, usuarios, donos das materias, todas as turmas).
- professor: altera apenas as materias de que e dono; gerencia turmas e
  aprova/recusa matriculas; ve o historico; faz anotacoes privadas.
- aluno: entra com nome completo e senha; contas antigas sem senha ficam
  bloqueadas ate que um responsavel defina uma. Ve apenas as materias
  das turmas em que a matricula foi aprovada.

Variaveis de ambiente (todas opcionais):
  PORT             porta HTTP (padrao 3002)
  HOST             endereco de escuta (padrao 0.0.0.0)
  ADMIN_NAME       nome do administrador criado na 1a execucao (padrao admin)
  ADMIN_PASSWORD   senha do administrador na 1a execucao (minimo 8 caracteres).
                   Se faltar, uma senha aleatoria e gerada e gravada em
                   data/senha_admin_inicial.txt
  COOKIE_SECURE    1 quando o site usa HTTPS (cookie so trafega por HTTPS)
  TRUST_PROXY      1 quando ha proxy reverso confiavel (usa X-Forwarded-For)
  ALLOWED_ORIGINS  origens extras aceitas em requisicoes de escrita
                   (separadas por virgula), alem do proprio Host

Comandos:
  python server.py                 inicia o servidor
  python server.py --reset-admin   redefine a senha do administrador
"""
import sys
from app.config import COOKIE_SECURE, DATA_DIR, DB_FILE, HOST, PORT, ROOT, TEST_MODE
from app.db import init_database, reset_admin_password
from app.http_server import PanelHandler, PanelServer


def main():
    if "--reset-admin" in sys.argv:
        raise SystemExit(reset_admin_password())
    try:
        init_database()
    except Exception as exc:  # noqa: BLE001
        print(f"Não foi possível abrir o Banco de Dados SQLite: {exc}", file=sys.stderr)
        raise SystemExit(1)
    local = HOST in ("127.0.0.1", "localhost", "::1")
    if not local and not COOKIE_SECURE:
        print("Aviso: se o site usa HTTPS, defina COOKIE_SECURE=1.", file=sys.stderr)
    expected_data = (ROOT.parent / "data").resolve()
    if not TEST_MODE and DATA_DIR.resolve() != expected_data:
        print("A pasta de dados não corresponde a esta versão da plataforma.", file=sys.stderr)
        raise SystemExit(1)
    print(f"Banco {'temporário de teste' if TEST_MODE else 'desta versão'}: {DB_FILE}", flush=True)
    server = PanelServer((HOST, PORT), PanelHandler)
    print(f"Painel disponível em http://localhost:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
