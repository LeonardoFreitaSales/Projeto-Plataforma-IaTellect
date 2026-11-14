"""SQLite-compatible adapter using authenticated libSQL transactions."""
import sqlite3
from libsql_client import create_client_sync, LibsqlError


class Row(dict):
    def __getitem__(self, key):
        return tuple(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class Cursor:
    def __init__(self, result):
        self.rows = iter(Row(zip(result.columns, row)) for row in result.rows)
        self.rowcount = result.rows_affected

    def __iter__(self):
        return self.rows

    def fetchone(self):
        return next(self.rows, None)

    def fetchall(self):
        return list(self.rows)


class Connection:
    def __init__(self, url, token):
        if not url.startswith(('libsql://', 'wss://')) or not token:
            raise RuntimeError('Configure TURSO_DATABASE_URL e TURSO_AUTH_TOKEN.')
        self.client = create_client_sync(url, auth_token=token)
        self.transaction = None
        self.client.execute('PRAGMA foreign_keys = ON')

    def execute(self, sql, args=()):
        if self.transaction is None:
            self.transaction = self.client.transaction()
        try:
            return Cursor(self.transaction.execute(sql, list(args)))
        except LibsqlError as exc:
            if exc.code.startswith('SQLITE_CONSTRAINT'):
                raise sqlite3.IntegrityError('Restrição de integridade do banco.') from None
            raise RuntimeError('Falha no banco remoto: ' + exc.code) from None

    def executescript(self, script):
        statement = ''
        for char in script:
            statement += char
            if char == ';' and sqlite3.complete_statement(statement):
                self.execute(statement)
                statement = ''

    def commit(self):
        if self.transaction is not None:
            self.transaction.commit()
            self.transaction = None

    def rollback(self):
        if self.transaction is not None:
            self.transaction.rollback()
            self.transaction = None

    def close(self):
        try:
            self.rollback()
        finally:
            self.client.close()
