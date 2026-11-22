# SQLite local

O arquivo de dados fica em `data/Banco de Dados SQLite.db`, relativo à raiz do repositório. O módulo `backend/app/db.py` aplica o schema de `backend/sql/schema.sql` e as migrações ao iniciar. A execução local normal ignora uma variável externa `DATA_DIR` e verifica se os caminhos do banco e da pasta de dados são atalhos.

## Tabelas

| Tabelas | Dados |
|---|---|
| `users`, `sessions` | Contas, hashes PBKDF2 e sessões. |
| `disciplines`, `policies` | Disciplinas, responsáveis e políticas de uso de IA. |
| `announcements` | Comunicados. |
| `turmas`, `turma_disciplines` | Turmas e disciplinas vinculadas. |
| `matriculas` | Solicitações pendentes, aprovadas ou recusadas. |
| `notas_privadas` | Anotações de cada professor sobre alunos. |
| `history` | Autor, perfil e alterações registradas pela auditoria. |

## Backup e migração

1. Encerre os servidores que usam o banco. Guarde uma cópia de segurança do arquivo SQLite e, se existirem, dos arquivos associados `-wal` e `-shm`.
2. Para migrar da v3, coloque a cópia do banco encerrado em `data/Banco de Dados SQLite.db` na v4. Preserve o backup original.
3. Inicie a v4 e confira as contas, disciplinas e matrículas. O cookie da v4 é próprio, por isso os usuários precisam entrar novamente.

A inicialização acrescenta tabelas e colunas previstas para bancos legados da v2. Um administrador pode atribuir responsáveis a disciplinas antigas sem dono. Registros antigos de histórico podem aparecer sem autor. Para contas legadas sem senha, siga o procedimento de primeiro acesso no [guia da plataforma](../../README.md).
