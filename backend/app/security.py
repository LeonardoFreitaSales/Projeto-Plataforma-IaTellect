"""Senhas e sessões da plataforma."""
import hashlib
import hmac
import secrets

from .config import COOKIE_NAME, COOKIE_SECURE, PBKDF2_ITERATIONS
from .utils import bad


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algo, iterations, salt, expected = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, AttributeError):
        return False


DUMMY_HASH = hash_password("senha-falsa-para-igualar-o-tempo")


def check_new_password(password):
    if not isinstance(password, str) or len(password) < 8:
        raise bad("A senha deve ter pelo menos 8 caracteres.")
    if len(password) > 200:
        raise bad("A senha excede 200 caracteres.")


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_cookie(token, max_age):
    parts = [f"{COOKIE_NAME}={token}", "Path=/", "HttpOnly", "SameSite=Lax", f"Max-Age={max_age}"]
    if COOKIE_SECURE:
        parts.append("Secure")
    return "; ".join(parts)
