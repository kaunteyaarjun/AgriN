"""Deterministic demo seed tests (M054): fixed ids, upsert semantics,
and a demo world the engines can actually analyze.

DB tests SKIP when dev Postgres is unreachable (same pattern as
test_analysis), with cleanup scoped to the seed's fixed users — the
FK cascade from ``users`` removes every row the seed created (M019
lesson: never blind TRUNCATE).
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from pydantic import SecretStr
from sqlalchemy import delete, func, select
from src.core.config import Settings
from src.core.db import dispose_engine, get_sessionmaker
from src.core.security import verify_password
from src.models import Farm, Farmer, FarmSignalCache, Plot, PlotState, User, UserRole
from src.services.analysis import analyze_farm
from src.services.demo_seed import (
    DEV_DEMO_PASSWORD,
    SEED_NAMESPACE,
    resolve_demo_password,
    seed_demo,
)
from src.services.farm_state import get_farm_state

from tests.conftest import _alembic_config, _db_reachable

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=UTC)
ROLE_BY_EMAIL = {
    "admin@agrin.demo": UserRole.admin,
    "officer@agrin.demo": UserRole.extension_officer,
    "maria@agrin.demo": UserRole.farmer,
    "joseph@agrin.demo": UserRole.farmer,
}
EAST_FARM_ID = uuid.uuid5(SEED_NAMESPACE, "farm:east")
_FIXED_USER_IDS = [
    uuid.uuid5(SEED_NAMESPACE, f"user:{key}") for key in ("admin", "officer", "maria", "joseph")
]


@pytest.fixture
async def _db() -> AsyncGenerator[None, None]:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    session = get_sessionmaker()()
    try:
        await session.execute(delete(User).where(User.id.in_(_FIXED_USER_IDS)))
        await session.commit()
    finally:
        await session.close()
    await dispose_engine()


async def _count(session, model) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


# ---------- password resolution (pure) ----------


def test_dev_falls_back_to_documented_default() -> None:
    assert resolve_demo_password(Settings(env="dev")) == DEV_DEMO_PASSWORD


def test_explicit_password_wins() -> None:
    settings = Settings(env="dev", demo_password=SecretStr("chosen-secret"))
    assert resolve_demo_password(settings) == "chosen-secret"


def test_prod_refuses_to_guess() -> None:
    settings = Settings(
        env="prod",
        jwt_secret=SecretStr("x" * 64),
        database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
    )
    with pytest.raises(ValueError, match="demo_password"):
        resolve_demo_password(settings)


def test_prod_accepts_explicit_password() -> None:
    settings = Settings(
        env="prod",
        jwt_secret=SecretStr("x" * 64),
        database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
        demo_password=SecretStr("prod-secret"),
    )
    assert resolve_demo_password(settings) == "prod-secret"


# ---------- the seeded world (DB) ----------


async def test_seed_is_deterministic_and_idempotent(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        first = await seed_demo(session, password="pw-one", now=NOW)
        assert (first.users, first.farmers, first.farms, first.plots) == (4, 2, 2, 4)
        run1_ids = {
            email: uid
            for email, uid in (
                (row.email, row.id)
                for row in (await session.scalars(select(User))).all()
                if row.email.endswith("@agrin.demo")
            )
        }
        assert set(run1_ids) == set(ROLE_BY_EMAIL)
        run1_farm_ids = {
            f.id
            for f in (await session.scalars(select(Farm).where(Farm.name.like("Demo Farm%")))).all()
        }

        second = await seed_demo(session, password="pw-one", now=NOW)
        run2_ids = {
            email: uid
            for email, uid in (
                (row.email, row.id)
                for row in (await session.scalars(select(User))).all()
                if row.email.endswith("@agrin.demo")
            )
        }
        run2_farm_ids = {
            f.id
            for f in (await session.scalars(select(Farm).where(Farm.name.like("Demo Farm%")))).all()
        }

        assert run2_ids == run1_ids  # fixed uuid5 keys, byte-identical ids
        assert run2_farm_ids == run1_farm_ids
        assert (await _count(session, User)) == 4  # no duplicates on re-run
        assert (await _count(session, Farmer)) == 2
        assert (await _count(session, Farm)) == 2
        assert (await _count(session, Plot)) == 4
        assert (await _count(session, PlotState)) == 4
        assert (await _count(session, FarmSignalCache)) == 2
        assert (second.signal_caches, second.plot_states) == (2, 4)
    finally:
        await session.close()


async def test_roles_and_password_are_right(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        await seed_demo(session, password="correct horse", now=NOW)
        rows = (
            await session.scalars(select(User).where(User.email.in_(list(ROLE_BY_EMAIL))))
        ).all()
        assert len(rows) == 4
        for row in rows:
            assert row.role == ROLE_BY_EMAIL[row.email]
            assert row.is_active
            assert verify_password("correct horse", row.password_hash)
            assert not verify_password("wrong", row.password_hash)
    finally:
        await session.close()


async def test_seeded_world_is_analyzed_not_blind(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        await seed_demo(session, password="pw", now=NOW)
        state = await get_farm_state(session, EAST_FARM_ID, now=NOW)
        assert state.plot_count == 2
        assert state.planted_plot_count == 2
        assert state.crops == ["Maize", "Wheat"]
        assert set(state.signals.signals) == {"weather", "satellite", "soil"}
        assert all(doc["source"].startswith("demo-") for doc in state.signals.signals.values())
        assert state.signals.refreshed_at == NOW - timedelta(minutes=30)
        analysis = await analyze_farm(session, EAST_FARM_ID, now=NOW)
        assert analysis.decision.plots_with_unknown_factors == 0
    finally:
        await session.close()


async def test_reseed_updates_password_in_place(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        await seed_demo(session, password="first-pass", now=NOW)
        summary = await seed_demo(session, password="second-pass", now=NOW)
        assert summary.users == 4
        assert (await _count(session, User)) == 4  # upsert, not duplicate
        rows = (await session.scalars(select(User))).all()
        for row in rows:
            assert verify_password("second-pass", row.password_hash)
            assert not verify_password("first-pass", row.password_hash)
    finally:
        await session.close()
