-- =====================================================================
-- Plataforma v3.0 - modelo do Banco de Dados SQLite
-- O server.py executa este arquivo a cada inicializacao. Todos os
-- comandos usam IF NOT EXISTS, entao ele nao apaga nada.
-- Bancos antigos (v2) sao atualizados pelo server.py (colunas novas em
-- disciplines e history) sem perder os dados ja importados.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- Usuarios: admin, professor (com senha) e aluno (entra so com o nome completo).
-- nameKey = nome sem acento de caixa/espacos extras, para garantir nome unico.
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    nameKey TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'professor', 'aluno')),
    passwordHash TEXT,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    CHECK (role = 'aluno' OR passwordHash IS NOT NULL)
);

-- Sessoes de login. Guarda apenas o hash do token (o token fica no cookie).
CREATE TABLE IF NOT EXISTS sessions (
    tokenHash TEXT PRIMARY KEY,
    userId TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    createdAt TEXT NOT NULL,
    expiresAt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(userId);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expiresAt);

-- Disciplinas. ownerId = professor responsavel (NULL = so o admin altera).
CREATE TABLE IF NOT EXISTS disciplines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    code TEXT NOT NULL DEFAULT '',
    instructor TEXT NOT NULL DEFAULT '',
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    ownerId TEXT REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS policies (
    id TEXT PRIMARY KEY,
    disciplineId TEXT NOT NULL REFERENCES disciplines(id) ON DELETE RESTRICT,
    activityType TEXT NOT NULL DEFAULT 'outro',
    activityName TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('proibido', 'restricao', 'permitido')),
    conditions TEXT NOT NULL DEFAULT '',
    details TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_policies_discipline ON policies(disciplineId);
CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);

CREATE TABLE IF NOT EXISTS announcements (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL
);

-- Turmas e as materias de cada turma.
CREATE TABLE IF NOT EXISTS turmas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    nameKey TEXT NOT NULL UNIQUE,
    createdBy TEXT REFERENCES users(id) ON DELETE SET NULL,
    createdAt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS turma_disciplines (
    turmaId TEXT NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    disciplineId TEXT NOT NULL REFERENCES disciplines(id) ON DELETE CASCADE,
    PRIMARY KEY (turmaId, disciplineId)
);
CREATE INDEX IF NOT EXISTS idx_turma_disciplines_disc ON turma_disciplines(disciplineId);

-- Matriculas: pendente -> aprovada ou recusada (decisao de um professor da turma).
CREATE TABLE IF NOT EXISTS matriculas (
    id TEXT PRIMARY KEY,
    turmaId TEXT NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    studentId TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovada', 'recusada')),
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    UNIQUE (turmaId, studentId)
);
CREATE INDEX IF NOT EXISTS idx_matriculas_student ON matriculas(studentId);

-- Anotacoes privadas: cada professor ve somente as proprias.
CREATE TABLE IF NOT EXISTS notas_privadas (
    professorId TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    studentId TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    PRIMARY KEY (professorId, studentId)
);

-- Historico com autor. authorId nao tem chave estrangeira de proposito:
-- o registro de auditoria continua existindo mesmo se o usuario for removido.
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entityId TEXT NOT NULL,
    summary TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    authorId TEXT,
    authorName TEXT,
    authorRole TEXT,
    changes TEXT
);
CREATE INDEX IF NOT EXISTS idx_history_created ON history(createdAt DESC);

-- Autodeclaracoes do assistente, visiveis ao aluno autor e ao professor responsavel.
CREATE TABLE IF NOT EXISTS assistant_reflections (
    id TEXT PRIMARY KEY,
    studentId TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    disciplineId TEXT NOT NULL REFERENCES disciplines(id) ON DELETE CASCADE,
    activityName TEXT NOT NULL,
    activityType TEXT NOT NULL,
    policySnapshot TEXT NOT NULL,
    answers TEXT NOT NULL,
    createdAt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assistant_reflections_discipline_date
    ON assistant_reflections(disciplineId, createdAt DESC);
CREATE INDEX IF NOT EXISTS idx_assistant_reflections_student_date
    ON assistant_reflections(studentId, createdAt DESC);
