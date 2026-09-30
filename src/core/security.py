"""Password hashing and JWT token helpers (M008/M009).

Sync core functions are pure CPU work (bcrypt, work factor 12 — explicit,
revisited in M055 per decision D3). Request handlers must use the async
wrappers, which run the core in a worker thread so hashing never blocks the
event loop. Nothing in this module logs; password material and the JWT
signing secret must never reach a log line, error message, or exception.
"""

from __future__ import annotations

import asyncio
import functools
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt as pyjwt
from passlib.context import CryptContext

from src.core.config import get_settings
from src.core.errors import InvalidToken

BCRYPT_ROUNDS = 12
"""Explicit work factor; ~250ms per hash on commodity hardware."""

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=BCRYPT_ROUNDS,
)


def hash_password(password: str) -> str:
    """Return a salted bcrypt hash of ``password`` (never store plaintext)."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check ``password`` against ``password_hash``.

    A malformed/corrupted stored hash returns ``False`` rather than raising —
    verification failure is not an error condition.
    """
    try:
        return _pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


async def hash_password_async(password: str) -> str:
    """``hash_password`` off the event loop — use this in request handlers."""
    return await asyncio.to_thread(hash_password, password)


async def verify_password_async(password: str, password_hash: str) -> bool:
    """``verify_password`` off the event loop — use this in request handlers."""
    return await asyncio.to_thread(verify_password, password, password_hash)


# --- JWT (M009, PyJWT per decision D5) -------------------------------------

JWT_ALGORITHM = "HS256"
CLOCK_LEEWAY_S = 5
"""Allowed clock skew between issuing and validating (seconds)."""


def get_jwt_secret() -> str:
    """Signing secret from settings; never a hardcoded or logged fallback."""
    settings = get_settings()
    secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else ""
    if not secret:
        raise RuntimeError(
            "jwt_secret is not configured; set JWT_SECRET before issuing or "
            "validating tokens (no default secret is ever used)."
        )
    return secret


def _create_token(
    user_id: uuid.UUID, token_type: str, ttl: timedelta, *, jti: str | None = None
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, str | int] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    if jti is not None:
        payload["jti"] = jti
    return pyjwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID) -> str:
    """Short-lived access token (settings.jwt_access_ttl_minutes)."""
    settings = get_settings()
    return _create_token(user_id, "access", timedelta(minutes=settings.jwt_access_ttl_minutes))


def create_refresh_token(user_id: uuid.UUID, *, jti: uuid.UUID) -> str:
    """Longer-lived refresh token (settings.jwt_refresh_ttl_days).

    ``jti`` is REQUIRED (M055): the caller must persist the row in
    ``refresh_tokens`` under that id or revocation cannot work. Access
    tokens stay stateless and carry no ``jti``.
    """
    settings = get_settings()
    return _create_token(
        user_id,
        "refresh",
        timedelta(days=settings.jwt_refresh_ttl_days),
        jti=str(jti),
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Validate ``token`` and return its claims.

    Raises :class:`InvalidToken` (401) on expiry, tampering, missing claims,
    or when the token's ``type`` differs from ``expected_type`` — an access
    token can never be replayed as a refresh token and vice versa.
    """
    try:
        claims = pyjwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            leeway=CLOCK_LEEWAY_S,
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except pyjwt.ExpiredSignatureError as exc:
        raise InvalidToken("The provided token has expired.") from exc
    except pyjwt.InvalidTokenError as exc:
        raise InvalidToken() from exc
    if claims.get("type") != expected_type:
        raise InvalidToken("The provided token has the wrong type.")
    return claims


@functools.lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """Valid bcrypt hash used to equalize login timing for unknown emails."""
    return hash_password(secrets.token_urlsafe(32))
