PLATAFORMA V4 - VERCEL E TURSO

Root Directory: Plataforma v4.0 Final; preset Other.
Python 3.12; apenas biblioteca padrao, sem dependencias externas.
Turso usa HTTPS /v2/pipeline com transacoes, commit e rollback.
api/index.py exporta handler e inicializa o schema na primeira chamada da API.
vercel.json encaminha as rotas ao servidor, que serve somente HTML e assets permitidos.

Variaveis secretas de Production:
TURSO_DATABASE_URL: URL libsql do banco.
TURSO_AUTH_TOKEN: token de leitura e escrita exclusivo do banco.
ADMIN_PASSWORD: senha forte do admin inicial (recomendado 12 ou mais caracteres; minimo 8).
A senha e usada somente quando ainda nao existe administrador.
Cookie Secure e habilitado pelo entrypoint Vercel.
Nunca grave credenciais no Git. Nao existe fallback SQLite local na Vercel.

Localmente: python server.py continua usando SQLite em data/.
Teste local: python test_permissoes.py.
Depois do deploy: validar /api/health, login, logout, permissoes e persistencia.
Faca backups periodicos pelo painel Turso (Download SQLite File).
Alteracoes de segredos na Vercel exigem novo deploy para entrar em vigor.
PRAGMA user_version, WAL e checkpoints sao usados somente no SQLite local.
