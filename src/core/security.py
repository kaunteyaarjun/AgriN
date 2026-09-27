"""Password hashing and verification (M008).

Sync core functions are pure CPU work (bcrypt, work factor 12 — explicit,
revisited in M055 per decision D3). Request handlers must use the async
wrappers, which run the core in a worker thread so hashing never blocks the
event loop. Nothing in this module logs; password material must never reach
a log line, error message, or exception.
"""

from __future__ import annotations

import asyncio

from passlib.context import CryptContext

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
