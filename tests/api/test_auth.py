"""API tests for authentication (M009): login, refresh, get_current_user.

Needs the dev Postgres (skip-if-unreachable `_db` fixture, which every test
in this module requests so its dispose teardown always runs — M008 lesson).
"""

from __future__ import annotations

import asyncio
import functools
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import jwt as pyjwt
import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI
from sqlalchemy import delete, text, update
from src.api.deps import get_current_user
from src.core import security
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import hash_password
from src.main import create_app
from src.models import User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_PATH = "/_test_protected"
LOGIN_PATH = "/api/v1/auth/login"
REFRESH_PATH = "/api/v1/auth/refresh"
PASSWORD = "Sup3rSecret-Pass!"


async def _db_reachable() -> bool:
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _alembic_config() -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return cfg


def _app_with_protected_route() -> FastAPI:
    app = create_app()

    @app.get(PROTECTED_PATH, dependencies=[Depends(get_current_user)])
    async def _protected() -> dict[str, str]:
        return {"status": "ok"}

    return app


async def _client(app: FastAPI | None = None) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app or _app_with_protected_route())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def _db() -> AsyncGenerator[None, None]:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    await dispose_engine()


@functools.lru_cache(maxsize=1)
def _seed_password_hash() -> str:
    """One bcrypt hash per test process; reused for every seeded user."""
    return hash_password(PASSWORD)


@pytest.fixture
async def _user(_db: None) -> AsyncGenerator[tuple[str, str], None]:
    """Seeded active farmer: yields (email, password); always cleaned up."""
    email = f"auth-{uuid.uuid4().hex[:10]}@example.com"
    session = get_sessionmaker()()
    session.add(User(email=email, password_hash=_seed_password_hash(), role=UserRole.farmer))
    await session.commit()
    try:
        yield (email, PASSWORD)
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email == email))
        await session.commit()
        await session.close()


async def _login(client: httpx.AsyncClient, email: str, password: str) -> dict[str, Any]:
    response = await client.post(LOGIN_PATH, json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


async def _set_active(email: str, active: bool) -> None:
    session = get_sessionmaker()()
    try:
        await session.execute(update(User).where(User.email == email).values(is_active=active))
        await session.commit()
    finally:
        await session.close()


async def _delete_user(email: str) -> None:
    session = get_sessionmaker()()
    try:
        await session.execute(delete(User).where(User.email == email))
        await session.commit()
    finally:
        await session.close()


def _tamper(token: str) -> str:
    mid = 10
    flipped = "A" if token[mid] != "A" else "B"
    return token[:mid] + flipped + token[mid + 1 :]


async def test_login_success_returns_decodable_token_pair(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        body = await _login(client, email, password)
    assert body["token_type"] == "bearer"
    access = security.decode_token(body["access_token"], "access")
    refresh = security.decode_token(body["refresh_token"], "refresh")
    uuid.UUID(str(access["sub"]))
    uuid.UUID(str(refresh["sub"]))
    assert access["sub"] == refresh["sub"]


async def test_unknown_email_and_wrong_password_return_identical_401(
    _user: tuple[str, str],
) -> None:
    email, password = _user
    async with await _client() as client:
        unknown = await client.post(
            LOGIN_PATH, json={"email": "no-such-user@example.com", "password": password}
        )
        wrong_pw = await client.post(
            LOGIN_PATH, json={"email": email, "password": "wrong-password-x"}
        )
    assert unknown.status_code == 401
    assert wrong_pw.status_code == 401
    assert unknown.json() == wrong_pw.json()
    assert unknown.json()["error_code"] == "invalid_credentials"


async def test_login_inactive_account_forbidden_after_password_check(
    _user: tuple[str, str],
) -> None:
    email, password = _user
    await _set_active(email, active=False)
    async with await _client() as client:
        response = await client.post(LOGIN_PATH, json={"email": email, "password": password})
    assert response.status_code == 403
    assert response.json()["error_code"] == "account_disabled"


async def test_refresh_returns_new_access_token(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        response = await client.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["refresh_token"] == tokens["refresh_token"]
    claims = security.decode_token(body["access_token"], "access")
    assert claims["sub"] == security.decode_token(tokens["access_token"], "access")["sub"]


async def test_access_token_rejected_at_refresh(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        response = await client.post(REFRESH_PATH, json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"


async def test_refresh_token_rejected_as_access_token(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        response = await client.get(
            PROTECTED_PATH, headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"


async def test_valid_access_token_opens_protected_route(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        response = await client.get(
            PROTECTED_PATH, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_missing_auth_header_is_401_not_403(_db: None) -> None:
    async with await _client() as client:
        response = await client.get(PROTECTED_PATH)
    assert response.status_code == 401
    assert response.json()["error_code"] == "not_authenticated"


async def test_wrong_scheme_and_garbage_tokens_are_401(_db: None) -> None:
    async with await _client() as client:
        basic = await client.get(
            PROTECTED_PATH, headers={"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}
        )
        garbage = await client.get(PROTECTED_PATH, headers={"Authorization": "Bearer not.a.token"})
    assert basic.status_code == 401
    assert basic.json()["error_code"] == "not_authenticated"
    assert garbage.status_code == 401
    assert garbage.json()["error_code"] == "invalid_token"


async def test_expired_access_token_is_401(_db: None) -> None:
    now = datetime.now(UTC) - timedelta(hours=1)
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=1)).timestamp()),
    }
    expired = pyjwt.encode(payload, security.get_jwt_secret(), algorithm=security.JWT_ALGORITHM)
    async with await _client() as client:
        response = await client.get(PROTECTED_PATH, headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"


async def test_tampered_access_token_is_401(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        response = await client.get(
            PROTECTED_PATH,
            headers={"Authorization": f"Bearer {_tamper(tokens['access_token'])}"},
        )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"


async def test_valid_token_of_deleted_user_is_401(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        await _delete_user(email)
        response = await client.get(
            PROTECTED_PATH, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"


async def test_valid_token_of_disabled_user_is_401(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        await _set_active(email, active=False)
        response = await client.get(
            PROTECTED_PATH, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"


async def test_refresh_after_user_deleted_is_401(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        await _delete_user(email)
        response = await client.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token"
