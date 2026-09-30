"""API tests for RBAC (M010): require_role, CurrentUserDep, default-deny.

Needs the dev Postgres (skip-if-unreachable `_db` fixture, requested by the
`_users` fixture so its dispose teardown always runs — M008 lesson).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, cast

import httpx
import pytest
from fastapi import Depends, FastAPI
from sqlalchemy import delete, update
from src.api.deps import CurrentUserDep, require_role
from src.core.db import get_sessionmaker
from src.core.errors import PermissionDenied
from src.main import create_app
from src.models import User, UserRole

from tests.conftest import PASSWORD, _seed_password_hash

ANY_PATH = "/_test_any"
ADMIN_PATH = "/_test_admin"
STAFF_PATH = "/_test_staff"
LOGIN_PATH = "/api/v1/auth/login"
ROLES = (UserRole.farmer, UserRole.extension_officer, UserRole.admin)
FORBIDDEN_BODY = {
    "error_code": "permission_denied",
    "message": "You do not have permission to perform this action.",
}


def _app_with_gated_routes() -> FastAPI:
    app = create_app()

    @app.get(ANY_PATH)
    async def _any(user: CurrentUserDep) -> dict[str, str]:
        return {"role": user.role}

    @app.get(ADMIN_PATH)
    async def _admin(
        user: Annotated[User, Depends(require_role(UserRole.admin))],
    ) -> dict[str, str]:
        return {"role": user.role}

    @app.get(STAFF_PATH)
    async def _staff(
        user: Annotated[User, Depends(require_role(UserRole.extension_officer, UserRole.admin))],
    ) -> dict[str, str]:
        return {"role": user.role}

    return app


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=_app_with_gated_routes())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[UserRole, str], None]:
    """Seeded farmer/extension_officer/admin; yields {role: email}; cleaned up."""
    emails = {role: f"rbac-{role}-{uuid.uuid4().hex[:8]}@example.com" for role in ROLES}
    session = get_sessionmaker()()
    for role, email in emails.items():
        session.add(User(email=email, password_hash=_seed_password_hash(), role=role))
    await session.commit()
    try:
        yield emails
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email.in_(emails.values())))
        await session.commit()
        await session.close()


async def _token(client: httpx.AsyncClient, email: str) -> str:
    response = await client.post(LOGIN_PATH, json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def _get(client: httpx.AsyncClient, path: str, token: str | None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return await client.get(path, headers=headers)


async def _set_role(email: str, role: UserRole) -> None:
    session = get_sessionmaker()()
    try:
        await session.execute(update(User).where(User.email == email).values(role=role))
        await session.commit()
    finally:
        await session.close()


async def _set_active(email: str, active: bool) -> None:
    session = get_sessionmaker()()
    try:
        await session.execute(update(User).where(User.email == email).values(is_active=active))
        await session.commit()
    finally:
        await session.close()


def test_require_role_without_arguments_fails_fast() -> None:
    with pytest.raises(ValueError, match="at least one role"):
        require_role()


async def test_require_role_accepts_plain_strings_and_checks_membership() -> None:
    # cast only silences mypy: the value really is a str at runtime, proving
    # StrEnum equality ("farmer" == UserRole.farmer) makes plain strings work.
    dep = require_role(cast(UserRole, "farmer"))
    user = User(
        email="unit@example.com",
        password_hash=_seed_password_hash(),
        role=UserRole.farmer,
    )
    assert await dep(user) is user
    wrong = User(
        email="unit2@example.com",
        password_hash=_seed_password_hash(),
        role=UserRole.admin,
    )
    with pytest.raises(PermissionDenied):
        await dep(wrong)


async def test_any_route_requires_authentication() -> None:
    async with await _client() as client:
        response = await _get(client, ANY_PATH, token=None)
    assert response.status_code == 401
    assert response.json()["error_code"] == "not_authenticated"


async def test_admin_route_farmer_forbidden_with_static_body(
    _users: dict[UserRole, str],
) -> None:
    async with await _client() as client:
        token = await _token(client, _users[UserRole.farmer])
        response = await _get(client, ADMIN_PATH, token)
    assert response.status_code == 403
    assert response.json() == FORBIDDEN_BODY


async def test_admin_route_admin_allowed(_users: dict[UserRole, str]) -> None:
    async with await _client() as client:
        token = await _token(client, _users[UserRole.admin])
        response = await _get(client, ADMIN_PATH, token)
    assert response.status_code == 200
    assert response.json() == {"role": "admin"}


async def test_staff_route_officer_allowed(_users: dict[UserRole, str]) -> None:
    async with await _client() as client:
        token = await _token(client, _users[UserRole.extension_officer])
        response = await _get(client, STAFF_PATH, token)
    assert response.status_code == 200
    assert response.json() == {"role": "extension_officer"}


async def test_staff_route_admin_also_allowed(_users: dict[UserRole, str]) -> None:
    async with await _client() as client:
        token = await _token(client, _users[UserRole.admin])
        response = await _get(client, STAFF_PATH, token)
    assert response.status_code == 200


async def test_staff_route_farmer_forbidden(_users: dict[UserRole, str]) -> None:
    async with await _client() as client:
        token = await _token(client, _users[UserRole.farmer])
        response = await _get(client, STAFF_PATH, token)
    assert response.status_code == 403
    assert response.json() == FORBIDDEN_BODY


async def test_wrong_scheme_header_is_401(_users: dict[UserRole, str]) -> None:
    async with await _client() as client:
        response = await client.get(ADMIN_PATH, headers={"Authorization": "Basic dXNlcjpwdw=="})
    assert response.status_code == 401
    assert response.json()["error_code"] == "not_authenticated"


async def test_role_change_applies_to_same_token(
    _users: dict[UserRole, str],
) -> None:
    """Role is DB-backed: promoting the user must open the gate immediately."""
    email = _users[UserRole.farmer]
    async with await _client() as client:
        token = await _token(client, email)
        before = await _get(client, ADMIN_PATH, token)
        assert before.status_code == 403
        await _set_role(email, UserRole.admin)
        try:
            after = await _get(client, ADMIN_PATH, token)
        finally:
            await _set_role(email, UserRole.farmer)
    assert after.status_code == 200
    assert after.json() == {"role": "admin"}


async def test_deactivated_user_token_rejected_on_gated_route(
    _users: dict[UserRole, str],
) -> None:
    email = _users[UserRole.admin]
    async with await _client() as client:
        token = await _token(client, email)
        await _set_active(email, False)
        try:
            response = await _get(client, ADMIN_PATH, token)
        finally:
            await _set_active(email, True)
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"
