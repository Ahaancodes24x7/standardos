"""Password hashing, reset tokens, session cookies and cron authentication.

Password hashes use scrypt with Node.js defaults (N=16384, r=8, p=1, 64-byte
key) and the ``<salt-hex>:<key-hex>`` format, so accounts created by the
previous TypeScript backend keep working unchanged.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Optional

from fastapi import Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import get_settings

KEY_LENGTH = 64
_SCRYPT = {"n": 16384, "r": 8, "p": 1, "maxmem": 64 * 1024 * 1024, "dklen": KEY_LENGTH}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), **_SCRYPT)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _, digest = stored.partition(":")
    if not salt or not digest:
        return False
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), **_SCRYPT)
    try:
        expected = bytes.fromhex(digest)
    except ValueError:
        return False
    return len(expected) == len(key) and hmac.compare_digest(expected, key)


def hash_token(token: str) -> str:
    """Reset tokens are high-entropy already; SHA-256 allows lookup by exact hash."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Session cookie
# ---------------------------------------------------------------------------


class SessionSecretMissing(RuntimeError):
    pass


def _serializer() -> URLSafeTimedSerializer:
    secret = get_settings().session_secret
    if not secret or len(secret) < 32:
        raise SessionSecretMissing("SESSION_SECRET must be set to a random string of at least 32 characters.")
    return URLSafeTimedSerializer(secret, salt="standardos-session")


def read_session_user_id(request: Request) -> Optional[str]:
    settings = get_settings()
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        return None
    try:
        data = _serializer().loads(raw, max_age=settings.session_max_age_seconds)
    except BadSignature:
        return None
    uid = data.get("uid") if isinstance(data, dict) else None
    return str(uid) if uid else None


def set_session(response: Response, user_id: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        _serializer().dumps({"uid": user_id}),
        max_age=settings.session_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(get_settings().session_cookie_name, path="/")


# ---------------------------------------------------------------------------
# Cron
# ---------------------------------------------------------------------------


def cron_authorized(authorization: Optional[str]) -> Optional[int]:
    """Return None when authorised, else the HTTP status to answer with."""
    settings = get_settings()
    if not settings.cron_secret:
        return 500
    if not authorization or not authorization.startswith("Bearer "):
        return 401
    token = authorization[len("Bearer ") :].strip()
    digest = lambda v: hashlib.sha256(v.encode("utf-8")).digest()  # noqa: E731
    provided = digest(token)
    ok = hmac.compare_digest(provided, digest(settings.cron_secret)) or hmac.compare_digest(
        provided, digest(settings.cron_secret_previous or settings.cron_secret)
    )
    return None if ok else 401
