"""Funções comuns de validação, identificação e datas."""
from datetime import datetime, timedelta, timezone
import unicodedata
import uuid


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def iso_in(days):
    moment = datetime.now(timezone.utc) + timedelta(days=days)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id():
    return str(uuid.uuid4())


def norm_name(value):
    """Nome sem espacos extras (mantem maiusculas e acentos)."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def key_of(value):
    """Chave de comparacao: sem diferenca de maiuscula/minuscula nem de espacos."""
    return norm_name(value).casefold()


class HTTPError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def bad(message):
    return HTTPError(400, message)


def text(value, name, maximum=5000, required=True):
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise bad(f"{name} deve ser texto.")
    out = value.strip()
    if required and not out:
        raise bad(f"{name} é obrigatório.")
    if len(out) > maximum:
        raise bad(f"{name} excede {maximum} caracteres.")
    return out


def pick(data, key, fallback):
    value = data.get(key)
    return fallback if value is None else value


NOT_FOUND = HTTPError(404, "Rota de API não encontrada.")
