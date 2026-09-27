"""Integration tests for the Alembic migration chain (M004).

Runs upgrade -> downgrade -> upgrade against the configured dev database.
SKIPS (does not fail) when the database is unreachable, so the non-DB quality
gate stays green without Docker. Sync tests on purpose: alembic/env.py calls
``asyncio.run`` internally and cannot run inside an async test's event loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from src.core.db import dispose_engine, get_engine

REPO_ROOT = Path(__file__).resolve().parents[1]


def _db_reachable() -> bool:
    async def _probe() -> bool:
        try:
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await dispose_engine()

    return asyncio.run(_probe())


def _config() -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return cfg


@pytest.fixture(autouse=True)
def _db_or_skip() -> Generator[None, None, None]:
    if not _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    yield


def _current_revision() -> str | None:
    from alembic.runtime.migration import MigrationContext

    async def _read() -> str | None:
        try:
            async with get_engine().connect() as conn:
                return await conn.run_sync(
                    lambda sync_conn: MigrationContext.configure(sync_conn).get_current_revision()
                )
        finally:
            await dispose_engine()

    return asyncio.run(_read())


def test_upgrade_downgrade_upgrade_round_trip() -> None:
    cfg = _config()
    command.upgrade(cfg, "head")
    assert _current_revision() == "0001"

    command.downgrade(cfg, "base")
    assert _current_revision() is None

    command.upgrade(cfg, "head")
    assert _current_revision() == "0001"


def test_upgrade_head_is_idempotent() -> None:
    cfg = _config()
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
    assert _current_revision() == "0001"
