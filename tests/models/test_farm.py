"""Farm model tests (M013): PostGIS geometry, unique/fk/cascade.

Metadata assertions run without a database; integration tests need the dev
Postgres with the migration chain at head (the fixture applies `upgrade head`
in a worker thread, since alembic/env.py runs its own event loop) and SKIP
when the database is unreachable.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from sqlalchemy import ForeignKeyConstraint, Table, UniqueConstraint, delete, func, select, text
from sqlalchemy.exc import IntegrityError
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.models import Farm, Farmer, User

REPO_ROOT = Path(__file__).resolve().parents[2]
POLYGON_WKT = "POLYGON((0 0,10 0,10 10,0 10,0 0))"


def test_farms_table_declared_with_expected_columns() -> None:
    table = cast(Table, Farm.__table__)
    assert table.name == "farms"
    assert set(table.columns.keys()) == {
        "id",
        "farmer_id",
        "name",
        "area_hectares",
        "geo",
        "created_at",
        "updated_at",
    }


def test_unique_farmer_and_name_declared_in_metadata() -> None:
    table = cast(Table, Farm.__table__)
    assert any(
        isinstance(constraint, UniqueConstraint)
        and set(constraint.columns.keys()) == {"farmer_id", "name"}
        for constraint in table.constraints
    )


def test_farmer_id_foreign_key_cascade_declared_in_metadata() -> None:
    table = cast(Table, Farm.__table__)
    (fk,) = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert fk.referred_table.name == "farmers"
    assert fk.ondelete == "CASCADE"


def test_geo_column_is_srid_4326() -> None:
    geo_type = cast("Geometry", Farm.__table__.c.geo.type)
    assert geo_type.srid == 4326
    assert geo_type.geometry_type == "GEOMETRY"


def test_repr_never_contains_geo_blob() -> None:
    farm = Farm(farmer_id=uuid.uuid4(), name="North 40")
    farm.geo = "POLYGON(" + "0 0," * 100 + "0 0)"
    rendered = repr(farm)
    assert "POLYGON" not in rendered
    assert "North 40" in rendered


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


async def _seed_farmer(session) -> tuple[User, Farmer]:
    """New user + farmer row; caller tracks the user id for cleanup."""
    user = User(email=f"farm-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    farmer = Farmer(user_id=user.id, full_name="Farm Owner")
    session.add(farmer)
    await session.commit()
    return user, farmer


async def _cleanup(session, seeded_user_ids: list[uuid.UUID]) -> None:
    """Rollback + delete ONLY seeded users (FK cascade clears farmer/farms)."""
    await session.rollback()
    if seeded_user_ids:
        await session.execute(delete(User).where(User.id.in_(seeded_user_ids)))
    await session.commit()
    await session.close()


async def test_postgis_extension_available(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        version = await session.scalar(select(func.postgis_version()))
        assert version is not None and version.startswith("3.")
    finally:
        await session.close()


async def test_geometry_round_trip_via_wkt(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, farmer = await _seed_farmer(session)
        seeded.append(user.id)
        farm = Farm(
            farmer_id=farmer.id,
            name="North 40",
            area_hectares=Decimal("40.50"),
            geo=WKTElement(POLYGON_WKT, srid=4326),
        )
        session.add(farm)
        await session.commit()

        back = await session.scalar(
            select(func.ST_AsText(Farm.geo)).where(Farm.farmer_id == farmer.id)
        )
        assert back == POLYGON_WKT
        srid = await session.scalar(
            select(func.ST_SRID(Farm.geo)).where(Farm.farmer_id == farmer.id)
        )
        assert srid == 4326

        fetched = (await session.execute(select(Farm).where(Farm.name == "North 40"))).scalar_one()
        assert fetched.area_hectares == Decimal("40.50")
    finally:
        await _cleanup(session, seeded)


async def test_duplicate_name_per_farmer_rejected(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, farmer = await _seed_farmer(session)
        seeded.append(user.id)
        session.add(Farm(farmer_id=farmer.id, name="North 40"))
        await session.commit()

        session.add(Farm(farmer_id=farmer.id, name="North 40"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await _cleanup(session, seeded)


async def test_same_name_for_other_farmer_allowed(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_a, farmer_a = await _seed_farmer(session)
        user_b, farmer_b = await _seed_farmer(session)
        seeded.extend([user_a.id, user_b.id])
        session.add(Farm(farmer_id=farmer_a.id, name="North 40"))
        session.add(Farm(farmer_id=farmer_b.id, name="North 40"))
        await session.commit()
    finally:
        await _cleanup(session, seeded)


async def test_unknown_farmer_id_rejected_by_foreign_key(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        session.add(Farm(farmer_id=uuid.uuid4(), name="Orphan Field"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await session.rollback()
        await session.close()


async def test_deleting_farmer_cascades_to_farms(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, farmer = await _seed_farmer(session)
        seeded.append(user.id)
        session.add(Farm(farmer_id=farmer.id, name="Cascade Field"))
        await session.commit()

        await session.execute(delete(Farmer).where(Farmer.id == farmer.id))
        await session.commit()

        remaining = (
            await session.execute(select(Farm).where(Farm.name == "Cascade Field"))
        ).scalar_one_or_none()
        assert remaining is None
    finally:
        await _cleanup(session, seeded)
