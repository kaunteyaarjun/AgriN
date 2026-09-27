"""Reusable FastAPI dependencies for authentication and authorization (M009+).

``get_current_user`` resolves ``Authorization: Bearer <access token>`` to a
``User``. Missing, malformed, expired, tampered or wrong-type credentials
all yield a clean 401 — never a 500. Role checks (``require_role``) arrive
with M010 and build on this dependency.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.errors import InvalidToken, NotAuthenticated
from src.core.security import decode_token
from src.models import User

_bearer = HTTPBearer(auto_error=False)
"""``auto_error=False``: we raise our own 401 (FastAPI's default would 403)."""

SessionDep = Annotated[AsyncSession, Depends(get_db)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


async def get_current_user(
    credentials: CredentialsDep,
    session: SessionDep,
) -> User:
    """Return the active user behind a valid access token, else raise 401."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise NotAuthenticated()

    claims = decode_token(credentials.credentials, "access")

    try:
        user_uuid = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise InvalidToken() from exc

    # Exactly one DB hit per request: the primary-key lookup for this user.
    user = await session.get(User, user_uuid)
    if user is None or not user.is_active:
        raise InvalidToken("The account for this token no longer exists or is active.")
    return user
