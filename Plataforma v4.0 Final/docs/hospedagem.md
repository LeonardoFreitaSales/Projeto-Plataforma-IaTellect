# Hospedagem existente

## Configuração

Na Vercel, a pasta raiz do projeto é `Plataforma v4.0 Final`, com preset **Other** e Python 3.12. O adaptador `api/index.py` habilita o cookie Secure e inicializa o schema na primeira chamada da API. O roteamento de `vercel.json` encaminha as requisições ao servidor da aplicação.

## Variáveis de produção

| Variável | Uso |
|---|---|
| `TURSO_DATABASE_URL` | URL libSQL do banco. |
| `TURSO_AUTH_TOKEN` | Token de leitura e escrita exclusivo do banco. |
| `ADMIN_PASSWORD` | Senha para criar o primeiro administrador. O mínimo é de oito caracteres e o guia de hospedagem recomenda doze ou mais. |

Configure esses valores como segredos da hospedagem. Alterações exigem um novo deploy para entrar em vigor.

## Persistência e verificação

O cliente usa HTTPS em `/v2/pipeline` com transações, commit e rollback. A execução na Vercel exige o banco remoto configurado. O modo WAL, os checkpoints e o controle de versão com `PRAGMA user_version` ficam no SQLite local.

Após um deploy, confira `/api/health`, login, logout, permissões e persistência. O painel do Turso oferece **Download SQLite File** para backups. Os passos para executar e testar localmente estão no [README da plataforma](../README.md).
