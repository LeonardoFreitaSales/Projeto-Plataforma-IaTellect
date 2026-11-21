# Plataforma v4.0

## Executar no computador

Na pasta desta versão, execute `iniciar.bat` no Windows ou `python server.py` com Python 3. Abra [a tela de acesso](http://127.0.0.1:3002/acesso.html). O iniciador do Windows usa o endereço local. A execução direta aceita as variáveis `HOST` e `PORT`.

No primeiro acesso, use o nome `admin` (ou o valor de `ADMIN_NAME`). A senha inicial vem de `ADMIN_PASSWORD` ou, na execução local, do arquivo gerado em `data/senha_admin_inicial.txt`. Depois de entrar, altere a senha e apague o arquivo. Para recuperar o acesso administrativo local, execute `python server.py --reset-admin`.

## Contas e matrículas

- **Administrador** gerencia professores, responsáveis pelas disciplinas, comunicados e turmas.
- **Professor** edita suas disciplinas, gerencia turmas autorizadas, analisa matrículas e mantém anotações privadas sobre os alunos.
- **Aluno** se cadastra com nome completo, turma e senha. A aprovação da matrícula libera as disciplinas da turma.

O cadastro dá a mesma resposta quando recebe um pedido ou encontra um conflito de nome. Um conflito preserva os dados existentes. Contas antigas sem senha precisam da opção **Definir senha**, disponível ao administrador ou ao professor autorizado. A troca de senha pelo usuário exige a senha atual e encerra suas outras sessões. O mínimo é de oito caracteres.

## Onde trabalhar

| Caminho | Responsabilidade |
|---|---|
| `server.py` | Entrada da aplicação. |
| `app/` | Configuração, banco, autenticação, permissões, auditoria e servidor HTTP. |
| `app/routes/` | Rotas da API por domínio. |
| `frontend/` | HTML do acesso e do painel. |
| `frontend/assets/css/` e `frontend/assets/js/` | Estilos, comportamento das telas e acessibilidade compartilhada. |
| `sql/schema.sql` | Modelo do banco usado na inicialização. |
| `test_permissoes.py` | Suíte de integração com SQLite temporário. |

Execute `python test_permissoes.py` nesta pasta para verificar o fluxo local.

## Documentação técnica

- [SQLite, backup e migração das versões anteriores](docs/banco-de-dados.md)
