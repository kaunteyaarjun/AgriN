"""API tests for the health/readiness probes (M007).

``/ready``'s success path needs the dev Postgres and SKIPs without it (same
pattern as ``tests/core/test_db.py``); all failure/hang paths use fakes or an
unreachable port and run without Docker.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import cast

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from src.api import health
from src.core.config import get_settings
from src.core.db import dispose_engine, get_engine
from src.main import create_app

READY_BODY_UNAVAILABLE = {"status": "unavailable"}


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def _db_reachable() -> bool:
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


class _FailingEngine:
    """Engine whose connect() raises — simulates an unreachable database."""

    def connect(self) -> _FailingConnection:
        return _FailingConnection()


class _FailingConnection:
    async def __aenter__(self) -> _FailingConnection:
        raise OSError("boom: connection refused")

    async def __aexit__(self, *_: object) -> None:
        return None


class _HangingEngine:
    """Engine whose connect() never completes — simulates a hung database."""

    def connect(self) -> _HangingConnection:
        return _HangingConnection()


class _HangingConnection:
    async def __aenter__(self) -> _HangingConnection:
        await asyncio.sleep(60)
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def execute(self, *_args: object, **_kwargs: object) -> None:
        return None


async def test_health_returns_200_without_touching_db(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode() -> None:
        raise AssertionError("/health must not touch the database")

    monkeypatch.setattr(health, "get_engine", _explode)
    async with await _client() as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_body_has_no_internal_detail() -> None:
    async with await _client() as client:
        response = await client.get("/health")
    assert response.json() == {"status": "ok"}


async def test_ready_returns_200_when_db_up() -> None:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    async with await _client() as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    await dispose_engine()


async def test_ready_returns_503_on_db_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "get_engine", _FailingEngine)
    async with await _client() as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json() == READY_BODY_UNAVAILABLE
    assert "boom" not in response.text
    assert "Traceback" not in response.text
    assert "OSError" not in response.text


async def test_ready_returns_503_quickly_on_db_hang(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "get_engine", _HangingEngine)
    async with await _client() as client:
        started = time.monotonic()
        response = await client.get("/ready")
        elapsed = time.monotonic() - started
    assert response.status_code == 503
    assert response.json() == READY_BODY_UNAVAILABLE
    # Bounded by READY_TIMEOUT_S (2.0s) plus slack; a hang must not hang us.
    assert elapsed >= health.READY_TIMEOUT_S - 0.05
    assert elapsed < health.READY_TIMEOUT_S + 2.5


async def test_ready_503_when_engine_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise() -> None:
        raise RuntimeError("database_url is not configured")

    monkeypatch.setattr(health, "get_engine", _raise)
    async with await _client() as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json() == READY_BODY_UNAVAILABLE


async def test_ready_failure_logged_detail_kept_server_side(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(health, "get_engine", _FailingEngine)
    with caplog.at_level(logging.WARNING, logger="agrin.health"):
        async with await _client() as client:
            response = await client.get("/ready")
    assert response.status_code == 503
    assert any("readiness_check_failed" in m for m in caplog.messages)
    assert any(getattr(r, "error_type", None) == "OSError" for r in caplog.records)
    # ...while the client only ever sees the status.
    assert response.json() == READY_BODY_UNAVAILABLE


async def test_ready_unreachable_db_leaves_no_checked_out_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real engine, refused TCP connection: 503 and pool stays clean."""
    settings = get_settings()
    await dispose_engine()
    unreachable = "postgresql+asyncpg://agrin:agrin@127.0.0.1:1/agrin"
    monkeypatch.setattr(settings, "database_url", unreachable)
    try:
        async with await _client() as client:
            response = await client.get("/ready")
        assert response.status_code == 503
        assert response.json() == READY_BODY_UNAVAILABLE
        assert cast(QueuePool, get_engine().pool).checkedout() == 0
    finally:
        await dispose_engine()
        # monkeypatch restores database_url; dispose cleared the caches.


async def test_probes_listed_in_openapi() -> None:
    async with await _client() as client:
        response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/ready" in paths


@pytest.fixture(autouse=True)
async def _restore_engine() -> AsyncGenerator[None, None]:
    yield
    await dispose_engine()
