"""SQLite-compatible transactions over Turso HTTPS Hrana."""
import base64
import json
import sqlite3
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def encode(value):
    if value is None:
        return {'type': 'null'}
    if isinstance(value, int):
        return {'type': 'integer', 'value': str(value)}
    if isinstance(value, float):
        return {'type': 'float', 'value': value}
    if isinstance(value, bytes):
        return {'type': 'blob', 'base64': base64.b64encode(value).decode()}
    return {'type': 'text', 'value': str(value)}


def decode(value):
    if value['type'] == 'null':
        return None
    if value['type'] == 'integer':
        return int(value['value'])
    if value['type'] == 'blob':
        return base64.b64decode(value['base64'])
    return value['value']


class Row(dict):
    def __getitem__(self, key):
        return tuple(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class Cursor:
    def __init__(self, result):
        columns = [c['name'] for c in result['cols']]
        self.rows = iter(Row(zip(columns, map(decode, row))) for row in result['rows'])
        self.rowcount = result['affected_row_count']

    def __iter__(self):
        return self.rows

    def fetchone(self):
        return next(self.rows, None)

    def fetchall(self):
        return list(self.rows)


class Connection:
    def __init__(self, url, token):
        parsed = urlsplit(url.replace('libsql://', 'https://', 1))
        if parsed.scheme != 'https' or not parsed.hostname or not token or parsed.username:
            raise RuntimeError('Configure TURSO_DATABASE_URL e TURSO_AUTH_TOKEN.')
        self.base_url = 'https://' + parsed.netloc
        self.token = token
        self.baton = None
        self.transaction = False
        self.closed = False

    @staticmethod
    def statement(sql, args=()):
        return {'type': 'execute', 'stmt': {'sql': sql, 'args': list(map(encode, args)), 'want_rows': True}}

    def pipeline(self, requests):
        if self.closed:
            raise RuntimeError('Conexao de banco encerrada.')
        payload = json.dumps({'baton': self.baton, 'requests': requests}).encode()
        request = Request(self.base_url.rstrip('/') + '/v2/pipeline', data=payload,
                          headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=15) as response:
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError):
            self.closed = True
            raise RuntimeError('Falha na conexao HTTPS com o banco remoto.') from None
        self.baton = data.get('baton')
        if data.get('base_url'):
            target = urlsplit(data['base_url'])
            if target.scheme != 'https' or not target.hostname or not target.hostname.endswith('.turso.io') or target.username:
                raise RuntimeError('Destino de banco remoto invalido.')
            self.base_url = data['base_url']
        results = []
        for item in data['results']:
            if item['type'] == 'error':
                code = item['error'].get('code', 'UNKNOWN')
                if code.startswith('SQLITE_CONSTRAINT'):
                    raise sqlite3.IntegrityError('Restricao de integridade do banco.')
                raise RuntimeError('Falha no banco remoto: ' + code)
            results.append(item['response'])
        return results

    def begin(self):
        if not self.transaction:
            self.pipeline([self.statement('PRAGMA foreign_keys = ON'), self.statement('BEGIN IMMEDIATE')])
            self.transaction = True

    def execute(self, sql, args=()):
        self.begin()
        return Cursor(self.pipeline([self.statement(sql, args)])[0]['result'])

    def executescript(self, script):
        self.begin()
        self.pipeline([{'type': 'sequence', 'sql': script}])

    def commit(self):
        if self.transaction:
            self.pipeline([self.statement('COMMIT')])
            self.transaction = False

    def rollback(self):
        if self.transaction and not self.closed:
            self.pipeline([self.statement('ROLLBACK')])
            self.transaction = False

    def close(self):
        try:
            self.rollback()
        finally:
            try:
                if self.baton and not self.closed:
                    self.pipeline([{'type': 'close'}])
            finally:
                self.closed = True
                self.token = ''
