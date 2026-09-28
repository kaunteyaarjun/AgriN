"""Plot model tests (M015): geometry, unique-per-farm, FK cascade.

Metadata assertions run without a database; integration tests need the dev
Postgres with the migration chain at head (fixture applies `upgrade head`
in a worker thread) and SKIP when the database is unreachable.
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
from src.models import Farm, Farmer, Plot, User

REPO_ROOT = Path(__file__).resolve().parents[2]
PLOT_WKT = "POLYGON((0 0,5 0,5 5,0 5,0 0))"


def test_plots_table_declared_with_expected_columns() -> None:
    table = cast(Table, Plot.__table__)
    assert table.name == "plots"
    assert set(table.columns.keys()) == {
        "id",
        "farm_id",
        "name",
        "area_hectares",
        "geo",
        "created_at",
        "updated_at",
    }


def test_unique_farm_and_name_declared_in_metadata() -> None:
    table = cast(Table, Plot.__table__)
    assert any(
        isinstance(constraint, UniqueConstraint)
        and set(constraint.columns.keys()) == {"farm_id", "name"}
        for constraint in table.constraints
    )


def test_farm_id_foreign_key_cascade_declared_in_metadata() -> None:
    table = cast(Table, Plot.__table__)
    (fk,) = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert fk.referred_table.name == "farms"
    assert fk.ondelete == "CASCADE"


def test_farm_id_btree_index_declared_in_metadata() -> None:
    table = cast(Table, Plot.__table__)
    assert any(
        index.name == "ix_plots_farm_id" and set(index.columns.keys()) == {"farm_id"}
        for index in table.indexes
    )


def test_geo_column_is_srid_4326() -> None:
    geo_type = cast("Geometry", Plot.__table__.c.geo.type)
    assert geo_type.srid == 4326
    assert geo_type.geometry_type == "GEOMETRY"


def test_repr_never_contains_geo_blob() -> None:
    plot = Plot(farm_id=uuid.uuid4(), name="Block A")
    plot.geo = "POLYGON(" + "0 0," * 100 + "0 0)"
    rendered = repr(plot)
    assert "POLYGON" not in rendered
    assert "Block A" in rendered


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


async def _seed_farm(session) -> tuple[User, Farmer, Farm]:
    """New user + farmer + farm; caller tracks the user id for cleanup."""
    user = User(email=f"plot-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    farmer = Farmer(user_id=user.id, full_name="Plot Owner")
    session.add(farmer)
    await session.commit()
    farm = Farm(farmer_id=farmer.id, name="Home Farm")
    session.add(farm)
    await session.commit()
    return user, farmer, farm


async def _cleanup(session, seeded_user_ids: list[uuid.UUID]) -> None:
    """Rollback + delete ONLY seeded users (FK cascade clears farmer/farms/plots)."""
    await session.rollback()
    if seeded_user_ids:
        await session.execute(delete(User).where(User.id.in_(seeded_user_ids)))
    await session.commit()
    await session.close()


async def test_geometry_round_trip_via_wkt(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm = await _seed_farm(session)
        seeded.append(user.id)
        session.add(
            Plot(
                farm_id=farm.id,
                name="Block A",
                area_hectares=Decimal("5.25"),
                geo=WKTElement(PLOT_WKT, srid=4326),
            )
        )
        await session.commit()

        back = await session.scalar(select(func.ST_AsText(Plot.geo)).where(Plot.farm_id == farm.id))
        assert back == PLOT_WKT
        srid = await session.scalar(select(func.ST_SRID(Plot.geo)).where(Plot.farm_id == farm.id))
        assert srid == 4326

        fetched = (
            await session.execute(
                select(Plot).where(Plot.farm_id == farm.id, Plot.name == "Block A")
            )
        ).scalar_one()
        assert fetched.area_hectares == Decimal("5.25")
    finally:
        await _cleanup(session, seeded)


async def test_duplicate_name_per_farm_rejected(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm = await _seed_farm(session)
        seeded.append(user.id)
        session.add(Plot(farm_id=farm.id, name="Block A"))
        await session.commit()

        session.add(Plot(farm_id=farm.id, name="Block A"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await _cleanup(session, seeded)


async def test_same_name_for_other_farm_allowed(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_a, _farmer_a, farm_a = await _seed_farm(session)
        user_b, _farmer_b, farm_b = await _seed_farm(session)
        seeded.extend([user_a.id, user_b.id])
        session.add(Plot(farm_id=farm_a.id, name="Block A"))
        session.add(Plot(farm_id=farm_b.id, name="Block A"))
        await session.commit()
    finally:
        await _cleanup(session, seeded)


async def test_unknown_farm_id_rejected_by_foreign_key(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        session.add(Plot(farm_id=uuid.uuid4(), name="Orphan Block"))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await session.rollback()
        await session.close()


async def test_deleting_farm_cascades_to_plots(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm = await _seed_farm(session)
        seeded.append(user.id)
        session.add(Plot(farm_id=farm.id, name="Block A"))
        await session.commit()

        await session.execute(delete(Farm).where(Farm.id == farm.id))
        await session.commit()

        remaining = (
            await session.execute(
                select(Plot).where(Plot.farm_id == farm.id, Plot.name == "Block A")
            )
        ).scalar_one_or_none()
        assert remaining is None
    finally:
        await _cleanup(session, seeded)
