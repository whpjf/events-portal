import secrets
import time

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Request

hasher = PasswordHasher()


def hash_password(password):
    return hasher.hash(password)


def verify_password(password_hash, password):
    try:
        return hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def get_csrf(request: Request):
    """Токен формы хранится в сессии и вставляется в каждую форму."""
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


async def verify_csrf(request: Request):
    from app.deps import CsrfError

    form = await request.form()
    sent = form.get("csrf_token", "")
    real = request.session.get("csrf", "")
    if not real or not secrets.compare_digest(sent, real):
        raise CsrfError()


class LoginGuard:
    """После 5 неудачных входов подряд вход с этим логином и адреса закрывается на 5 минут."""

    limit = 5
    lock_seconds = 300

    def __init__(self):
        self.fails = {}

    def seconds_left(self, key):
        count, last = self.fails.get(key, (0, 0))
        if count >= self.limit:
            left = self.lock_seconds - (time.time() - last)
            if left > 0:
                return int(left) + 1
            del self.fails[key]
        return 0

    def fail(self, key):
        count, _ = self.fails.get(key, (0, 0))
        self.fails[key] = (count + 1, time.time())

    def ok(self, key):
        self.fails.pop(key, None)


guard = LoginGuard()
