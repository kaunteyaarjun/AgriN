"""Farmer model tests (M011).

Metadata assertions run without a database; integration tests need the dev
Postgres with the migration chain at head (the fixture applies `upgrade head`
in a worker thread, since alembic's env.py runs its own event loop) and SKIP
when the database is unreachable.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import ForeignKeyConstraint, Table, delete, select, text
from sqlalchemy.exc import IntegrityError
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.models import Farmer, User

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_farmers_table_declared_with_expected_columns() -> None:
    table = cast(Table, Farmer.__table__)
    assert table.name == "farmers"
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "full_name",
        "phone",
        "village",
        "district",
        "created_at",
        "updated_at",
    }


def test_user_id_unique_constraint_declared_in_metadata() -> None:
    table = cast(Table, Farmer.__table__)
    assert table.columns["user_id"].unique is True


def test_user_id_foreign_key_cascade_declared_in_metadata() -> None:
    table = cast(Table, Farmer.__table__)
    (fk,) = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert fk.referred_table.name == "users"
    assert fk.ondelete == "CASCADE"


def test_repr_never_contains_pii() -> None:
    farmer = Farmer(
        user_id=uuid.uuid4(),
        full_name="Asha Mwangi",
        phone="+255712345678",
        village="Mwanga",
        district="Kilimanjaro",
    )
    rendered = repr(farmer)
    assert "+255712345678" not in rendered
    assert "Mwanga" not in rendered
    assert "Kilimanjaro" not in rendered
    assert "Asha Mwangi" in rendered


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
    # alembic/env.py calls asyncio.run internally, so it must run off the
    # test's event loop; ensures `farmers` exists regardless of test ordering.
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    await dispose_engine()


async def _seed_user(session) -> User:
    user = User(
        email=f"farmer-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="stored-hash",
    )
    session.add(user)
    await session.commit()
    return user


async def test_insert_and_select_round_trip(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user = await _seed_user(session)
        farmer = Farmer(user_id=user.id, full_name="Asha Mwangi")
        session.add(farmer)
        await session.commit()
        await session.refresh(farmer)
        assert farmer.id is not None
        assert farmer.phone is None
        assert farmer.village is None
        assert farmer.district is None
        assert farmer.created_at is not None

        fetched = (
            await session.execute(select(Farmer).where(Farmer.user_id == user.id))
        ).scalar_one()
        assert fetched.id == farmer.id
        assert fetched.full_name == "Asha Mwangi"
    finally:
        await session.rollback()
        await session.execute(delete(Farmer))
        await session.execute(delete(User))
        await session.commit()
        await session.close()


async def test_duplicate_user_id_rejected_at_db_level(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user = await _seed_user(session)
        session.add(Farmer(user_id=user.id, full_name="First"))
        await session.commit()

        session.add(Farmer(user_id=user.id, full_name="Second"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await session.rollback()
        await session.execute(delete(Farmer))
        await session.execute(delete(User))
        await session.commit()
        await session.close()


async def test_unknown_user_id_rejected_by_foreign_key(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        session.add(Farmer(user_id=uuid.uuid4(), full_name="Orphan"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await session.rollback()
        await session.close()


async def test_deleting_user_cascades_to_farmer(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user = await _seed_user(session)
        session.add(Farmer(user_id=user.id, full_name="Cascade Target"))
        await session.commit()

        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()

        remaining = (
            await session.execute(select(Farmer).where(Farmer.user_id == user.id))
        ).scalar_one_or_none()
        assert remaining is None
    finally:
        await session.rollback()
        await session.execute(delete(Farmer))
        await session.execute(delete(User))
        await session.commit()
        await session.close()
