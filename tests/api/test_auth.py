"""API tests for authentication (M009): login, refresh, get_current_user.

Needs the dev Postgres (skip-if-unreachable `_db` fixture, which every test
in this module requests so its dispose teardown always runs — M008 lesson).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt as pyjwt
import pytest
from fastapi import Depends, FastAPI
from sqlalchemy import delete, update
from src.api.deps import get_current_user
from src.core import security
from src.core.db import get_sessionmaker
from src.main import create_app
from src.models import User, UserRole

from tests.conftest import PASSWORD, _seed_password_hash

PROTECTED_PATH = "/_test_protected"
LOGIN_PATH = "/api/v1/auth/login"
REFRESH_PATH = "/api/v1/auth/refresh"


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


async def test_refresh_rotates_the_refresh_token(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        response = await client.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    # M055 rotation: a NEW refresh token with a NEW jti comes back
    assert body["refresh_token"] != tokens["refresh_token"]
    old_jti = security.decode_token(tokens["refresh_token"], "refresh")["jti"]
    new_jti = security.decode_token(body["refresh_token"], "refresh")["jti"]
    assert new_jti != old_jti
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


# ---------- M055: revocation lifecycle ----------

LOGOUT_PATH = "/api/v1/auth/logout"
LOGOUT_ALL_PATH = "/api/v1/auth/logout-all"


def _bearer(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_refresh_reuse_detection_revokes_the_whole_family(
    _user: tuple[str, str],
) -> None:
    email, password = _user
    async with await _client() as client:
        first = await _login(client, email, password)
        second = await client.post(REFRESH_PATH, json={"refresh_token": first["refresh_token"]})
        assert second.status_code == 200
        rotated = second.json()

        replay = await client.post(REFRESH_PATH, json={"refresh_token": first["refresh_token"]})
        assert replay.status_code == 401  # the revoked token came back

        # reuse detection kills the attacker's freshly rotated sibling too
        dead = await client.post(REFRESH_PATH, json={"refresh_token": rotated["refresh_token"]})
        assert dead.status_code == 401

        # revocation is not a ban: a fresh login still works
        fresh = await client.post(LOGIN_PATH, json={"email": email, "password": password})
        assert fresh.status_code == 200


async def test_logout_revokes_the_presented_token(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        out = await client.post(LOGOUT_PATH, json={"refresh_token": tokens["refresh_token"]})
        assert out.status_code == 200
        assert out.json() == {"logged_out": True}

        dead = await client.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})
        assert dead.status_code == 401

        # idempotent: revoking again still succeeds (no existence oracle)
        again = await client.post(LOGOUT_PATH, json={"refresh_token": tokens["refresh_token"]})
        assert again.status_code == 200


async def test_logout_all_revokes_every_active_token(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        session_one = await _login(client, email, password)
        session_two = await _login(client, email, password)

        out = await client.post(LOGOUT_ALL_PATH, headers=_bearer(session_one))
        assert out.status_code == 200
        assert out.json() == {"revoked": 2}

        for tokens in (session_one, session_two):
            dead = await client.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})
            assert dead.status_code == 401


async def test_logout_all_requires_an_access_token(_user: tuple[str, str]) -> None:
    email, password = _user
    async with await _client() as client:
        tokens = await _login(client, email, password)
        anon = await client.post(LOGOUT_ALL_PATH)
        wrong = await client.post(LOGOUT_ALL_PATH, headers=_bearer({"access_token": "garbage"}))
        valid = await client.post(LOGOUT_ALL_PATH, headers=_bearer(tokens))
    assert anon.status_code == 401
    assert anon.json()["error_code"] == "not_authenticated"
    assert wrong.status_code == 401
    assert valid.status_code == 200
    assert valid.json()["revoked"] == 1  # this session's token, exactly


# ---------- M055: rate limiting ----------


async def test_login_rate_limit_answers_429_envelope(
    _db: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    from src.core.config import get_settings

    monkeypatch.setattr(get_settings(), "auth_rate_limit_per_minute", 2)
    caplog.set_level(logging.INFO, logger="agrin.audit")
    async with await _client() as client:
        for _ in range(2):  # counted attempts, both plain 401s
            response = await client.post(
                LOGIN_PATH, json={"email": "nobody@example.com", "password": "wrong-pass"}
            )
            assert response.status_code == 401
        blocked = await client.post(
            LOGIN_PATH, json={"email": "nobody@example.com", "password": "wrong-pass"}
        )
        unaffected = await client.get("/")  # limiter is per-bucket, not global
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["error_code"] == "rate_limited"
    assert "detail" not in body
    assert int(blocked.headers["Retry-After"]) >= 1
    assert unaffected.status_code == 200
    blocked_events = [
        record
        for record in caplog.records
        if record.name == "agrin.audit" and record.event == "rate_limited.blocked"  # type: ignore[attr-defined]
    ]
    assert blocked_events and blocked_events[0].outcome == "blocked"  # type: ignore[attr-defined]


async def test_refresh_rate_limit_is_a_separate_bucket(
    _db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.config import get_settings

    monkeypatch.setattr(get_settings(), "auth_rate_limit_per_minute", 1)
    async with await _client() as client:
        first = await client.post(REFRESH_PATH, json={"refresh_token": "garbage"})
        second = await client.post(REFRESH_PATH, json={"refresh_token": "garbage"})
    assert first.status_code == 401  # bucket allows one; the token itself is bad
    assert second.status_code == 429


# ---------- M055: audit events ----------


async def test_auth_lifecycle_emits_audit_events(
    _user: tuple[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    email, password = _user
    caplog.set_level(logging.INFO, logger="agrin.audit")
    async with await _client() as client:
        tokens = await _login(client, email, password)
        await client.post(LOGIN_PATH, json={"email": email, "password": "wrong"})
        await client.post(REFRESH_PATH, json={"refresh_token": "garbage"})
        await client.post(LOGOUT_PATH, json={"refresh_token": tokens["refresh_token"]})
        await client.post(LOGOUT_ALL_PATH, headers=_bearer(tokens))

    events = [record for record in caplog.records if record.name == "agrin.audit"]
    names = {record.event for record in events}  # type: ignore[attr-defined]
    assert "auth.login.success" in names
    assert "auth.login.failure" in names
    assert "auth.refresh.failure" in names
    assert "auth.logout" in names
    assert "auth.logout_all" in names
    for record in events:
        assert record.outcome in {"success", "failure", "blocked"}  # type: ignore[attr-defined]
        assert hasattr(record, "ip")  # every auth event carries the client ip
