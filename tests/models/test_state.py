"""Farm state schema tests (M018): plot_states + farm_signal_caches.

Metadata assertions run without a database; integration tests need the
dev Postgres with the migration chain at head (fixture applies
`upgrade head` in a worker thread) and SKIP when the database is
unreachable. Cleanup is scoped to seeded users only (FK cascade clears
farmer → farms → plots → plot_states and farm_signal_caches).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date
from typing import cast

import pytest
from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Table,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import DefaultClause
from sqlalchemy.sql.schema import CallableColumnDefault
from src.core.db import get_sessionmaker
from src.models import GROWTH_STAGES, Farm, Farmer, FarmSignalCache, Plot, PlotState, User

# ---------------------------------------------------------------------------
# Metadata (no DB)
# ---------------------------------------------------------------------------


def test_plot_states_table_declared_with_expected_columns() -> None:
    table = cast(Table, PlotState.__table__)
    assert table.name == "plot_states"
    assert set(table.columns.keys()) == {
        "plot_id",
        "crop",
        "growth_stage",
        "planted_on",
        "created_at",
        "updated_at",
    }


def test_plot_states_primary_key_is_plot_id_with_cascade() -> None:
    table = cast(Table, PlotState.__table__)
    assert set(table.primary_key.columns.keys()) == {"plot_id"}
    (fk,) = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert fk.referred_table.name == "plots"
    assert fk.ondelete == "CASCADE"


def test_growth_stage_check_matches_growth_stages_constant() -> None:
    table = cast(Table, PlotState.__table__)
    (check,) = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint) and "growth_stage" in str(constraint.name or "")
    ]
    assert check.name == "plot_states_growth_stage_check"
    for stage in GROWTH_STAGES:
        assert f"'{stage}'" in check.sqltext.text, f"CHECK misses {stage!r}"
    # no stale stages hidden in the CHECK beyond the shared constant
    assert check.sqltext.text.count("'") == 2 * len(GROWTH_STAGES)


def test_growth_stages_has_the_six_canonical_values() -> None:
    assert GROWTH_STAGES == (
        "germination",
        "vegetative",
        "flowering",
        "fruiting",
        "maturation",
        "harvest",
    )


def test_farm_signal_caches_table_declared_with_expected_columns() -> None:
    table = cast(Table, FarmSignalCache.__table__)
    assert table.name == "farm_signal_caches"
    assert set(table.columns.keys()) == {
        "farm_id",
        "signals",
        "refreshed_at",
        "created_at",
        "updated_at",
    }
    assert set(table.primary_key.columns.keys()) == {"farm_id"}
    (fk,) = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert fk.referred_table.name == "farms"
    assert fk.ondelete == "CASCADE"


def test_signals_column_is_jsonb_with_empty_object_default() -> None:
    column = cast(Table, FarmSignalCache.__table__).c.signals
    assert isinstance(column.type, JSONB)
    assert column.nullable is False
    assert column.default is not None
    # SQLAlchemy wraps zero-arg defaults as ``lambda ctx: fn()`` (schema.py)
    wrapped = cast(
        "Callable[[object], dict[str, object]]",
        cast("CallableColumnDefault", column.default).arg,
    )
    assert wrapped(None) == {}
    rendered = str(cast("DefaultClause", column.server_default).arg)
    assert "{}" in rendered and "jsonb" in rendered.lower()


def test_repr_never_contains_the_signals_blob() -> None:
    cache = FarmSignalCache(farm_id=uuid.uuid4())
    cache.signals = {"weather": {"raw": "x" * 500}}
    rendered = repr(cache)
    assert "xxxx" not in rendered
    assert "weather" in rendered
    assert repr(cache.farm_id) in rendered


# ---------------------------------------------------------------------------
# Integration (dev Postgres)
# ---------------------------------------------------------------------------


async def _seed(session) -> tuple[User, Farmer, Farm, Plot]:
    """user + farmer + farm + plot; caller tracks the user id for cleanup."""
    user = User(email=f"state-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    farmer = Farmer(user_id=user.id, full_name="State Owner")
    session.add(farmer)
    await session.commit()
    farm = Farm(farmer_id=farmer.id, name="State Farm")
    session.add(farm)
    await session.commit()
    plot = Plot(farm_id=farm.id, name="State Block")
    session.add(plot)
    await session.commit()
    return user, farmer, farm, plot


async def _cleanup(session, seeded_user_ids: list[uuid.UUID]) -> None:
    """Rollback + delete ONLY seeded users (FK cascade clears the rest)."""
    await session.rollback()
    if seeded_user_ids:
        await session.execute(delete(User).where(User.id.in_(seeded_user_ids)))
    await session.commit()
    await session.close()


async def test_state_insert_and_read_round_trip(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm, plot = await _seed(session)
        seeded.append(user.id)
        session.add(
            PlotState(
                crop="Maize",
                growth_stage="vegetative",
                planted_on=date(2026, 3, 15),
                plot_id=plot.id,
            )
        )
        session.add(
            FarmSignalCache(
                farm_id=farm.id,
                signals={
                    "weather": {"temp_c": 24.5, "rain_mm": 0, "note": None},
                    "soil": {"ph": 6.4, "layers": [10, 30]},
                },
            )
        )
        await session.commit()

        state = (
            await session.execute(select(PlotState).where(PlotState.plot_id == plot.id))
        ).scalar_one()
        assert state.crop == "Maize"
        assert state.growth_stage == "vegetative"
        assert state.planted_on == date(2026, 3, 15)

        cache = (
            await session.execute(select(FarmSignalCache).where(FarmSignalCache.farm_id == farm.id))
        ).scalar_one()
        assert cache.signals["weather"]["temp_c"] == 24.5
        assert cache.signals["weather"]["note"] is None
        assert cache.signals["soil"]["layers"] == [10, 30]
        assert cache.refreshed_at is not None
    finally:
        await _cleanup(session, seeded)


async def test_duplicate_plot_state_rejected_by_primary_key(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, _farm, plot = await _seed(session)
        seeded.append(user.id)
        session.add(
            PlotState(
                crop="Maize",
                growth_stage="vegetative",
                planted_on=date(2026, 3, 15),
                plot_id=plot.id,
            )
        )
        await session.commit()
        session.add(
            PlotState(
                crop="Beans", growth_stage="flowering", planted_on=date(2026, 4, 1), plot_id=plot.id
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await _cleanup(session, seeded)


async def test_unknown_growth_stage_rejected_by_check(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, _farm, plot = await _seed(session)
        seeded.append(user.id)
        session.add(
            PlotState(
                crop="Maize", growth_stage="miracle", planted_on=date(2026, 3, 15), plot_id=plot.id
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await _cleanup(session, seeded)


async def test_unknown_plot_and_farm_ids_rejected_by_foreign_keys(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        session.add(
            PlotState(
                crop="Maize",
                growth_stage="vegetative",
                planted_on=date(2026, 3, 15),
                plot_id=uuid.uuid4(),
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()
        session.add(FarmSignalCache(farm_id=uuid.uuid4(), signals={}))
        with pytest.raises(IntegrityError):
            await session.commit()
    finally:
        await session.rollback()
        await session.close()


async def test_default_signals_is_empty_object(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm, _plot = await _seed(session)
        seeded.append(user.id)
        session.add(FarmSignalCache(farm_id=farm.id))
        await session.commit()
        cache = (
            await session.execute(select(FarmSignalCache).where(FarmSignalCache.farm_id == farm.id))
        ).scalar_one()
        assert cache.signals == {}
    finally:
        await _cleanup(session, seeded)


async def test_deleting_plot_cascades_only_its_state(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm, plot_a = await _seed(session)
        seeded.append(user.id)
        plot_b = Plot(farm_id=farm.id, name="Second Block")
        session.add(plot_b)
        await session.commit()
        session.add_all(
            [
                PlotState(
                    crop="Maize",
                    growth_stage="vegetative",
                    planted_on=date(2026, 3, 15),
                    plot_id=plot_a.id,
                ),
                PlotState(
                    crop="Beans",
                    growth_stage="flowering",
                    planted_on=date(2026, 4, 1),
                    plot_id=plot_b.id,
                ),
            ]
        )
        await session.commit()

        await session.execute(delete(Plot).where(Plot.id == plot_a.id))
        await session.commit()

        remaining = (
            (
                await session.execute(
                    select(PlotState).where(PlotState.plot_id.in_([plot_a.id, plot_b.id]))
                )
            )
            .scalars()
            .all()
        )
        assert [state.plot_id for state in remaining] == [plot_b.id]
    finally:
        await _cleanup(session, seeded)


async def test_deleting_farm_cascades_states_and_caches(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user, _farmer, farm, plot = await _seed(session)
        seeded.append(user.id)
        session.add(
            PlotState(
                crop="Maize",
                growth_stage="vegetative",
                planted_on=date(2026, 3, 15),
                plot_id=plot.id,
            )
        )
        session.add(FarmSignalCache(farm_id=farm.id, signals={"weather": {"temp_c": 20}}))
        await session.commit()

        await session.execute(delete(Farm).where(Farm.id == farm.id))
        await session.commit()

        our_state = await session.get(PlotState, plot.id)
        our_cache = await session.get(FarmSignalCache, farm.id)
        assert our_state is None  # plots -> plot_states cascaded
        assert our_cache is None  # farms -> farm_signal_caches cascaded
    finally:
        await _cleanup(session, seeded)
