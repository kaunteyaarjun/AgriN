"""Shared test fixtures and helpers (M055, extended M056, consolidated M057).

Three things live here. Process-wide state resets: the in-process rate
limiter (src/core/ratelimit, M055) and the MODIS calendar cache
(src/providers/satellite_live, M056) would otherwise leak across test
cases (M055 note: add future process-wide state resets alongside
these). The `_db` fixture: schema setup (alembic upgrade) + engine
disposal, requested explicitly by DB-touching tests. The plain helpers
(`_db_reachable`, `_alembic_config`, `_client`, `_headers`,
`_seed_password_hash`, `PASSWORD`): until M057 every test file carried
its own byte-identical copy; they are called as functions, so tests
import them with `from tests.conftest import ...` (tests is a package
since M057).

Deliberately NOT here (M057 spec): `_users` (every body differs —
email prefixes, profile seeding, key types — and fixture params would
multiply test counts), auth/rbac/hardening's custom `_client` apps,
demo_seed's `_db` (fixed-user wipe teardown; shadows this fixture),
query_budgets' `_headers(user_id)`.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from src.core.db import dispose_engine, get_engine
from src.core.ratelimit import limiter
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import User

REPO_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "Sup3rSecret-Pass!"


@pytest.fixture(autouse=True)
async def _reset_rate_limiter() -> AsyncGenerator[None, None]:
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _reset_modis_calendar() -> Generator[None, None]:
    from src.providers.satellite_live import reset_calendar_cache

    reset_calendar_cache()
    yield
    reset_calendar_cache()


async def _db_reachable() -> bool:
    """Probe the dev database without skipping (usable outside fixtures)."""
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
    """Upgrade to head before the test, dispose the engine after.

    alembic/env.py calls asyncio.run internally, so the upgrade runs off
    the test's event loop (via asyncio.to_thread); this guarantees every
    table exists regardless of test ordering.
    """
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    await dispose_engine()


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@functools.lru_cache(maxsize=1)
def _seed_password_hash() -> str:
    """One bcrypt hash per test process; reused for every seeded user."""
    return hash_password(PASSWORD)
