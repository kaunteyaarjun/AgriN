"""Reusable FastAPI dependencies for authentication and authorization (M009+).

``get_current_user`` resolves ``Authorization: Bearer <access token>`` to a
``User``. ``require_role`` (M010) layers role authorization on top of it:
default-deny, 401 before 403, role always read from the DB row.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.errors import InvalidToken, NotAuthenticated, PermissionDenied
from src.core.security import decode_token
from src.models import User, UserRole

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


CurrentUserDep = Annotated[User, Depends(get_current_user)]
"""Any authenticated (active) user, regardless of role."""


def require_role(*roles: UserRole) -> Callable[..., Awaitable[User]]:
    """Dependency factory: allow only the listed roles (M010, default-deny).

    No hierarchy — an ``admin`` passes only if its role is named. Zero roles
    fails fast with ``ValueError`` at route-definition time. The role is read
    from the DB-backed user (never from token claims), so role changes apply
    on the next request. Returns the ``User`` so routes get authn + authz in
    a single annotation: ``user: Annotated[User, Depends(require_role(...))]``
    """
    if not roles:
        raise ValueError("require_role() needs at least one role")
    allowed = frozenset(roles)

    async def _role_check(user: CurrentUserDep) -> User:
        if user.role not in allowed:
            raise PermissionDenied()
        return user

    return _role_check


AdminUserDep = Annotated[User, Depends(require_role(UserRole.admin))]
"""Shortcut for admin-only routes (first real consumer: M052)."""
