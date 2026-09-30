"""Farmer model tests (M011).

Metadata assertions run without a database; integration tests need the dev
Postgres with the migration chain at head (the fixture applies `upgrade head`
in a worker thread, since alembic's env.py runs its own event loop) and SKIP
when the database is unreachable.
"""

from __future__ import annotations

import uuid
from typing import cast

import pytest
from sqlalchemy import ForeignKeyConstraint, Table, delete, select
from sqlalchemy.exc import IntegrityError
from src.core.db import get_sessionmaker
from src.models import Farmer, User


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


async def _seed_user(session) -> User:
    user = User(
        email=f"farmer-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="stored-hash",
    )
    session.add(user)
    await session.commit()
    return user


async def _cleanup(session, seeded_user_ids: list[uuid.UUID]) -> None:
    """Rollback + delete ONLY rows this test seeded (FK cascade removes
    their farmer rows). Never truncate — an unscoped DELETE FROM users
    wiped the dev DB's accounts during M011's gate (finding)."""
    await session.rollback()
    if seeded_user_ids:
        await session.execute(delete(User).where(User.id.in_(seeded_user_ids)))
    await session.commit()
    await session.close()


async def test_insert_and_select_round_trip(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user = await _seed_user(session)
        seeded.append(user.id)
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
        await _cleanup(session, seeded)


async def test_duplicate_user_id_rejected_at_db_level(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user = await _seed_user(session)
        seeded.append(user.id)
        session.add(Farmer(user_id=user.id, full_name="First"))
        await session.commit()

        session.add(Farmer(user_id=user.id, full_name="Second"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await _cleanup(session, seeded)


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
    seeded: list[uuid.UUID] = []
    try:
        user = await _seed_user(session)
        seeded.append(user.id)
        session.add(Farmer(user_id=user.id, full_name="Cascade Target"))
        await session.commit()

        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()

        remaining = (
            await session.execute(select(Farmer).where(Farmer.user_id == user.id))
        ).scalar_one_or_none()
        assert remaining is None
    finally:
        await _cleanup(session, seeded)
