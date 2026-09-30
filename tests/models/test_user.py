"""User model tests (M008).

Metadata assertions run without a database; integration tests need the dev
Postgres with the migration chain at head (the fixture applies `upgrade head`
in a worker thread, since alembic's env.py runs its own event loop) and SKIP
when the database is unreachable.
"""

from __future__ import annotations

import uuid
from typing import cast

import pytest
from sqlalchemy import Enum, Table, UniqueConstraint, delete, select
from sqlalchemy.exc import IntegrityError
from src.core.db import get_sessionmaker
from src.models import User, UserRole


def test_users_table_declared_with_expected_columns() -> None:
    table = cast(Table, User.__table__)
    assert table.name == "users"
    assert set(table.columns.keys()) == {
        "id",
        "email",
        "password_hash",
        "role",
        "is_active",
        "created_at",
        "updated_at",
    }


def test_email_unique_constraint_declared_in_metadata() -> None:
    table = cast(Table, User.__table__)
    assert table.columns["email"].unique is True
    assert any(
        isinstance(constraint, UniqueConstraint) and set(constraint.columns.keys()) == {"email"}
        for constraint in table.constraints
    )


def test_role_is_db_level_check_enum_not_native_type() -> None:
    role_type = User.__table__.c.role.type
    assert isinstance(role_type, Enum)
    assert role_type.native_enum is False
    assert role_type.create_constraint is True
    assert set(role_type.enums) == {"farmer", "extension_officer", "admin"}


def test_repr_never_contains_password_hash() -> None:
    user = User(email="probe@example.com", password_hash="PLAINTEXT-SECRET")
    rendered = repr(user)
    assert "PLAINTEXT-SECRET" not in rendered
    assert "password_hash" not in rendered


async def test_insert_and_select_round_trip(_db: None) -> None:
    email = f"user-{uuid.uuid4().hex[:12]}@example.com"
    session = get_sessionmaker()()
    try:
        user = User(email=email, password_hash="stored-hash", role=UserRole.extension_officer)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        assert user.id is not None
        assert user.created_at is not None

        fetched = (await session.execute(select(User).where(User.email == email))).scalar_one()
        assert fetched.id == user.id
        assert fetched.role is UserRole.extension_officer
        assert fetched.is_active is True
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email == email))
        await session.commit()
        await session.close()


async def test_duplicate_email_rejected_at_db_level(_db: None) -> None:
    email = f"dup-{uuid.uuid4().hex[:12]}@example.com"
    session = get_sessionmaker()()
    try:
        session.add(User(email=email, password_hash="hash-one", role=UserRole.farmer))
        await session.commit()

        session.add(User(email=email, password_hash="hash-two", role=UserRole.farmer))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email == email))
        await session.commit()
        await session.close()
