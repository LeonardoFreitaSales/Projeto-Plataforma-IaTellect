import json
import secrets
from ipaddress import ip_address
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
from app.config import COOKIE_NAME, SESSION_DAYS, TRUST_PROXY, TRUSTED_PROXY_IPS
from app.security import session_cookie, token_digest
from app.utils import bad, iso_in, now_iso


class Ctx:
    def __init__(self, conn, handler, method, parts, query, raw_body):
        self.conn, self.handler, self.method = conn, handler, method
        self.parts, self.query, self.raw_body = parts, query, raw_body
        self.cookies = []
        self.user = None
        self._body = None
        cookie = SimpleCookie()
        try:
            cookie.load(handler.headers.get("Cookie") or "")
        except Exception:
            cookie = SimpleCookie()
        morsel = cookie.get(COOKIE_NAME)
        self.token = morsel.value if morsel else None
        self.token_hash = token_digest(self.token) if self.token else None

    @property
    def ip(self):
        peer = self.handler.client_address[0]
        if not TRUST_PROXY or ip_address(peer) not in TRUSTED_PROXY_IPS:
            return peer
        forwarded = self.handler.headers.get_all("X-Forwarded-For") or []
        current = ip_address(peer)
        for value in reversed(",".join(forwarded).split(",")):
            if current not in TRUSTED_PROXY_IPS:
                break
            try:
                current = ip_address(value.strip())
            except ValueError:
                return peer
        return str(current)

    @property
    def body(self):
        if self._body is None:
            if not self.raw_body:
                self._body = {}
            else:
                try:
                    parsed = json.loads(self.raw_body.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise bad("JSON inválido.")
                if not isinstance(parsed, dict):
                    raise bad("JSON inválido.")
                self._body = parsed
        return self._body

    def q(self, name):
        values = parse_qs(self.query, keep_blank_values=True).get(name)
        return values[0] if values else None

    def authenticate(self):
        if not self.token_hash:
            return None
        return self.conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.userId WHERE s.tokenHash = ? AND s.expiresAt > ? AND u.passwordHash IS NOT NULL AND u.passwordHash != ''",
            (self.token_hash, now_iso())).fetchone()

    def open_session(self, user_id):
        token = secrets.token_urlsafe(32)
        self.conn.execute("DELETE FROM sessions WHERE expiresAt < ?", (now_iso(),))
        self.conn.execute(
            "INSERT INTO sessions (tokenHash, userId, createdAt, expiresAt) VALUES (?,?,?,?)",
            (token_digest(token), user_id, now_iso(), iso_in(SESSION_DAYS)))
        self.cookies.append(session_cookie(token, SESSION_DAYS * 86400))


def public_user(row):
    return {"id": row["id"], "name": row["name"], "role": row["role"]}
