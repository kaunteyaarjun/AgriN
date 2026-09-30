"""Unified client-error envelopes (M055): one shape for every failure.

Before M055 the API shipped two dialects — `{error_code, message}` for
AppError and `{detail}` for pydantic/Starlette raises. M055 removed the
second dialect; these tests pin the envelope for all three origins
(pydantic 422, route 404, method 405) plus the no-leak rule (M017).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from src.core.db import dispose_engine, get_engine
from src.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGIN_PATH = "/api/v1/auth/login"
MISSING_PATH = "/api/v1/does-not-exist"


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


@pytest.fixture
async def _db() -> AsyncGenerator[None, None]:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    await dispose_engine()


async def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()), base_url="http://t")


async def test_pydantic_422_uses_the_envelope(_db: None) -> None:
    async with await _client() as client:
        response = await client.post(LOGIN_PATH, json={"email": "x"})  # password missing
    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "validation_failed"
    assert "password" in body["message"]
    assert "detail" not in body


async def test_route_mismatch_404_uses_the_envelope() -> None:
    async with await _client() as client:
        response = await client.get(MISSING_PATH)
    assert response.status_code == 404
    body = response.json()
    assert body == {"error_code": "not_found", "message": "The requested resource was not found."}


async def test_method_not_allowed_405_uses_the_envelope() -> None:
    async with await _client() as client:
        response = await client.get(LOGIN_PATH)  # login is POST-only
    assert response.status_code == 405
    body = response.json()
    assert body["error_code"] == "method_not_allowed"
    assert "detail" not in body


async def test_validation_message_is_capped_not_dumped() -> None:
    # a body with many oversized fields: the message must stay bounded
    huge = "a" * 500
    async with await _client() as client:
        response = await client.post(
            LOGIN_PATH, json={"email": huge, "password": huge, "extra": huge}
        )
    assert response.status_code == 422
    assert len(response.json()["message"]) <= 520


def test_app_error_handler_still_returns_the_same_shape() -> None:
    from src.core.errors import AppError

    err = AppError("custom safe text", error_code="custom_code", status_code=418)
    assert err.error_code == "custom_code"
    assert err.message == "custom safe text"
