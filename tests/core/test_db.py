"""Integration tests for src.core.db (M003).

These require the docker-compose dev Postgres. If it is unreachable they
SKIP rather than fail, so the non-DB quality gate stays green without Docker.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import cast

import pytest
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from src.core.db import dispose_engine, get_db, get_engine, get_sessionmaker

from tests.conftest import _db_reachable


def _checked_out() -> int:
    """Number of connections currently checked out of the pool."""
    return cast(QueuePool, get_engine().pool).checkedout()


@pytest.fixture(autouse=True)
async def _db_or_skip() -> AsyncGenerator[None, None]:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    yield
    await dispose_engine()


async def test_select_one_round_trip() -> None:
    async for session in get_db():
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


async def test_session_closed_even_on_exception() -> None:
    agen = get_db()
    session = await agen.__anext__()
    await session.execute(text("SELECT 1"))
    await agen.aclose()  # what the framework does when the request ends/raises
    assert not session.in_transaction()
    assert _checked_out() == 0


async def test_no_connection_leak_over_many_sessions() -> None:
    await dispose_engine()
    for _ in range(100):
        async for session in get_db():
            await session.execute(text("SELECT 1"))
    assert _checked_out() == 0


async def test_sessionmaker_is_cached() -> None:
    assert get_sessionmaker() is get_sessionmaker()
    assert get_engine() is get_engine()
