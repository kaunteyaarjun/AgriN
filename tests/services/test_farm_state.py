"""Farm State service tests (M019): view assembly, derived math, upserts,
NotFound/validation paths, and the 3-query performance contract.

All DB-backed against the dev Postgres (SKIP when unreachable). Cleanup
is scoped to seeded users (FK cascade clears farmer → farms → plots →
plot_states and farm_signal_caches).
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, event, select, text
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.errors import NotFound, ValidationFailed
from src.models import Farm, Farmer, FarmSignalCache, Plot, PlotState, User
from src.services.farm_state import (
    clear_plot_state,
    get_farm_state,
    put_signals,
    set_plot_state,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 28, 12, 0, 0, tzinfo=UTC)


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


async def _seed(session, seeded: list[uuid.UUID]) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """user + farmer + farm + plot A + plot B → (user_id, farm_id, plot_b_id).

    The user id joins ``seeded`` immediately after its commit, so a later
    failure in this helper still leaves the row tracked for cleanup
    (lesson from the M019 pollution incident: untracked partial seeds
    leak and break unrelated list/count tests).
    """
    user = User(email=f"fs-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    seeded.append(user.id)
    farmer = Farmer(user_id=user.id, full_name="FS Owner")
    session.add(farmer)
    await session.commit()
    farm = Farm(farmer_id=farmer.id, name="FS Farm")
    session.add(farm)
    await session.commit()
    session.add(Plot(farm_id=farm.id, name="Block A"))
    session.add(Plot(farm_id=farm.id, name="Block B"))
    await session.commit()
    plot_b = (
        await session.execute(
            select(Plot.id).where(Plot.farm_id == farm.id, Plot.name == "Block B")
        )
    ).scalar_one()
    return user.id, farm.id, plot_b


async def _cleanup(session, seeded_user_ids: list[uuid.UUID]) -> None:
    await session.rollback()
    if seeded_user_ids:
        await session.execute(delete(User).where(User.id.in_(seeded_user_ids)))
    await session.commit()
    await session.close()


async def _plot_id(session, farm_id: uuid.UUID, name: str) -> uuid.UUID:
    row = await session.execute(select(Plot.id).where(Plot.farm_id == farm_id, Plot.name == name))
    return row.scalar_one()


async def test_get_farm_state_assembles_full_view(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _plot_b = await _seed(session, seeded)
        plot_a = await _plot_id(session, farm_id, "Block A")
        await set_plot_state(
            session,
            plot_a,
            crop="Maize",
            growth_stage="vegetative",
            planted_on=date(2026, 9, 18),  # 10 days before NOW
        )
        await put_signals(
            session,
            farm_id,
            signals={"weather": {"temp_c": 26.0}},
            refreshed_at=NOW - timedelta(minutes=90),
        )

        view = await get_farm_state(session, farm_id, now=NOW)

        assert view.farm_id == farm_id
        assert view.name == "FS Farm"
        assert view.plot_count == 2
        assert view.planted_plot_count == 1
        assert view.crops == ["Maize"]
        planted = next(p for p in view.plots if p.crop is not None)
        unplanted = next(p for p in view.plots if p.crop is None)
        assert planted.crop == "Maize"
        assert planted.growth_stage == "vegetative"
        assert planted.days_since_planted == 10
        assert unplanted.crop is None
        assert unplanted.days_since_planted is None
        assert view.signals.signals == {"weather": {"temp_c": 26.0}}
        assert view.signals.refreshed_at == NOW - timedelta(minutes=90)
        assert view.signals.age_seconds == 90 * 60
    finally:
        await _cleanup(session, seeded)


async def test_get_farm_state_empty_farm_is_all_zeros(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        # remove both plots so only the farm remains
        await session.execute(delete(Plot).where(Plot.farm_id == farm_id))
        await session.commit()

        view = await get_farm_state(session, farm_id, now=NOW)

        assert view.plots == []
        assert view.plot_count == 0
        assert view.planted_plot_count == 0
        assert view.crops == []
        assert view.signals.signals == {}
        assert view.signals.refreshed_at is None
        assert view.signals.age_seconds is None
    finally:
        await _cleanup(session, seeded)


async def test_get_farm_state_unknown_farm_raises_not_found(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        with pytest.raises(NotFound):
            await get_farm_state(session, uuid.uuid4())
    finally:
        await session.close()


async def test_negative_days_and_future_refresh_are_exposed_as_is(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        plot_a = await _plot_id(session, farm_id, "Block A")
        await set_plot_state(
            session,
            plot_a,
            crop="Beans",
            growth_stage="germination",
            planted_on=date(2026, 10, 5),  # future plan
        )
        await put_signals(
            session, farm_id, signals={"soil": {}}, refreshed_at=NOW + timedelta(hours=1)
        )

        view = await get_farm_state(session, farm_id, now=NOW)

        planted = next(p for p in view.plots if p.plot_id == plot_a)
        assert planted.days_since_planted == -7  # documented, not clamped
        assert view.signals.age_seconds == -3600
    finally:
        await _cleanup(session, seeded)


async def test_get_farm_state_runs_exactly_three_queries(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    statements: list[str] = []

    def _count(
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    engine = get_engine().sync_engine
    event.listen(engine, "before_cursor_execute", _count)
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        statements.clear()
        await get_farm_state(session, farm_id, now=NOW)
        twin_queries = [
            s
            for s in statements
            if any(
                needle in s
                for needle in (
                    "FROM farms",
                    "FROM plots",
                    "FROM plot_states",
                    "FROM farm_signal_caches",
                )
            )
        ]
        assert len(twin_queries) == 3, twin_queries
    finally:
        event.remove(engine, "before_cursor_execute", _count)
        await _cleanup(session, seeded)


async def test_set_plot_state_upserts_idempotently(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        plot_a = await _plot_id(session, farm_id, "Block A")

        await set_plot_state(
            session, plot_a, crop="Maize", growth_stage="vegetative", planted_on=date(2026, 9, 1)
        )
        await set_plot_state(
            session, plot_a, crop="Wheat", growth_stage="flowering", planted_on=date(2026, 9, 10)
        )

        rows = (
            (await session.execute(select(PlotState).where(PlotState.plot_id == plot_a)))
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].crop == "Wheat"
        assert rows[0].growth_stage == "flowering"
        assert rows[0].planted_on == date(2026, 9, 10)
    finally:
        await _cleanup(session, seeded)


async def test_set_plot_state_validation_and_not_found(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        plot_a = await _plot_id(session, farm_id, "Block A")

        with pytest.raises(ValidationFailed):
            await set_plot_state(
                session, plot_a, crop="Maize", growth_stage="miracle", planted_on=date(2026, 9, 1)
            )
        with pytest.raises(ValidationFailed):
            await set_plot_state(
                session, plot_a, crop="   ", growth_stage="vegetative", planted_on=date(2026, 9, 1)
            )
        with pytest.raises(NotFound):
            await set_plot_state(
                session,
                uuid.uuid4(),
                crop="Maize",
                growth_stage="vegetative",
                planted_on=date(2026, 9, 1),
            )
        # nothing was written by the rejected calls
        count = (
            (await session.execute(select(PlotState).where(PlotState.plot_id == plot_a)))
            .scalars()
            .all()
        )
        assert count == []
    finally:
        await _cleanup(session, seeded)


async def test_clear_plot_state_is_idempotent(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        plot_a = await _plot_id(session, farm_id, "Block A")
        await set_plot_state(
            session, plot_a, crop="Maize", growth_stage="vegetative", planted_on=date(2026, 9, 1)
        )

        await clear_plot_state(session, plot_a)
        await clear_plot_state(session, plot_a)  # second call: no error

        rows = (
            (await session.execute(select(PlotState).where(PlotState.plot_id == plot_a)))
            .scalars()
            .all()
        )
        assert rows == []
    finally:
        await _cleanup(session, seeded)


async def test_put_signals_upserts_and_validates_farm(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)

        await put_signals(session, farm_id, signals={"weather": {"a": 1}}, refreshed_at=NOW)
        await put_signals(
            session,
            farm_id,
            signals={"satellite": {"ndvi": 0.62}},
            refreshed_at=NOW + timedelta(minutes=5),
        )

        rows = (
            (
                await session.execute(
                    select(FarmSignalCache).where(FarmSignalCache.farm_id == farm_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].farm_id == farm_id
        assert rows[0].signals == {"satellite": {"ndvi": 0.62}}  # wholesale replace
        assert rows[0].refreshed_at == NOW + timedelta(minutes=5)

        with pytest.raises(NotFound):
            await put_signals(session, uuid.uuid4(), signals={})
    finally:
        await _cleanup(session, seeded)


async def test_set_plot_state_stores_numeric_areas_and_reads_back(_db: None) -> None:
    """Sanity: Decimal area survives the view assembly (M020 will serve it)."""
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        user_id, farm_id, _ = await _seed(session, seeded)
        plot_a = await _plot_id(session, farm_id, "Block A")
        await session.execute(
            text("UPDATE plots SET area_hectares = :area WHERE id = :pid"),
            {"area": Decimal("2.50"), "pid": plot_a},
        )
        await session.commit()

        view = await get_farm_state(session, farm_id, now=NOW)
        target = next(p for p in view.plots if p.plot_id == plot_a)
        assert target.area_hectares == Decimal("2.50")
    finally:
        await _cleanup(session, seeded)
