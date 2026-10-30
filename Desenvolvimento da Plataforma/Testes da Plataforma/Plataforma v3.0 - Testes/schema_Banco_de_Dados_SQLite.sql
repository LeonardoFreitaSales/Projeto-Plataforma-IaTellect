PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS disciplines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    code TEXT NOT NULL DEFAULT '',
    instructor TEXT NOT NULL DEFAULT '',
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entityId TEXT NOT NULL,
    summary TEXT NOT NULL,
    createdAt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_created ON history(createdAt DESC);
