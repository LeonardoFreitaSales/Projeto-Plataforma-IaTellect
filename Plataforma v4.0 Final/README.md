# Plataforma v4.0 final

## Executar

Extraia toda a pasta e execute `iniciar.bat` no Windows, ou `python server.py` com Python 3.
Abra http://127.0.0.1:3002/acesso.html. A plataforma usa Python e SQLite, sem dependencias extras.

Na primeira execucao, o banco sera criado em `data/`. Se ADMIN_PASSWORD nao estiver definida,
a senha inicial sera gerada e salva somente no arquivo local `data/senha_admin_inicial.txt`.
Leia esse arquivo localmente, entre como admin, altere a senha e apague o arquivo de senha.
O ZIP nao inclui banco, contas pessoais, senha inicial, logs ou dependencias geradas.

## Contas e permissoes

Todos os perfis entram com nome e senha. Contas antigas sem senha e suas sessoes ficam bloqueadas.
Um professor autorizado ou administrador pode usar Definir senha; contas e matriculas sao mantidas.
Senhas esquecidas precisam desse atendimento. Alterar senha exige a senha atual e encerra outras sessoes.
O minimo de oito caracteres nao garante uma senha forte: evite nomes, datas e sequencias previsiveis.

Alunos novos escolhem turma e senha. As materias sao liberadas apos aprovacao da matricula.
Cadastro recebido e conflito de nome retornam a mesma resposta neutra, sem login automatico.
Um conflito nao sobrescreve senha nem matricula de outra pessoa; procure o professor para conferir o cadastro.
O teto de matriculas pendentes nao foi implementado, conforme solicitado.

## Migrar dados da v3.0

Pare os servidores e guarde um backup antes de copiar seu banco para `data/Banco de Dados SQLite.db`
nesta pasta. O schema e atualizado ao iniciar. Nao compartilhe o mesmo arquivo entre versoes em execucao.
A v4 usa um cookie proprio: faca login novamente. Contas sem senha precisam de atendimento do responsavel.
A variavel DATA_DIR externa e ignorada; o banco normal fica sempre em data/ ao lado de server.py.

## Escopo

Este pacote contem a plataforma Python ativa. O painel Node.js/JSON permanece um prototipo historico,
sem autenticacao nem sincronizacao, no repositorio original; nao faz parte desta entrega executavel.
Os prototipos anteriores foram preservados no computador. O ZIP original foi entregue antes da publicacao no GitHub.
Consulte REVISAO.md para os resultados e limites dos testes.
