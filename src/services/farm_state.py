"""Farm State service (M019): the single read/write entry point for the
Farm Digital Twin tables (``plot_states`` + ``farm_signal_caches``).

**Authorization is deliberately NOT done here.** Callers must authorize
the farm first — M020's API uses M014's ``_authorized_farm`` before
calling ``get_farm_state`` (standing rule; enforced by M020's tests).

Query shape (performance contract asserted in tests):
- ``get_farm_state`` = exactly 3 queries regardless of plot count
  (farm row, plots LEFT JOIN plot_states, signal cache).
- Writes are single-statement ``INSERT ... ON CONFLICT`` upserts; the
  service commits (one pattern for all callers — M020, M054 seed).

Derived fields are deterministic and policy-free: ``days_since_planted``
may be negative (future planting dates are legitimate plans) and
``age_seconds`` may be negative (ingestion may supply its own clock);
staleness *thresholds* are intentionally left to the engines (M032+).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFound, ValidationFailed
from src.models import GROWTH_STAGES, Farm, FarmSignalCache, Plot, PlotState


class PlotStateView(BaseModel):
    """One plot of the twin: identity + crop facts (None when unset)."""

    plot_id: uuid.UUID
    name: str
    area_hectares: Decimal | None
    crop: str | None
    growth_stage: str | None
    planted_on: date | None
    days_since_planted: int | None


class SignalCacheView(BaseModel):
    """Latest provider snapshot for the farm (empty when never filled)."""

    signals: dict[str, Any]
    refreshed_at: datetime | None
    age_seconds: int | None


class FarmStateView(BaseModel):
    """The assembled Farm Digital Twin view of one farm."""

    farm_id: uuid.UUID
    farmer_id: uuid.UUID
    name: str
    plots: list[PlotStateView]
    plot_count: int
    planted_plot_count: int
    crops: list[str]
    signals: SignalCacheView


async def get_farm_state(
    session: AsyncSession,
    farm_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> FarmStateView:
    """Assemble the twin view. Raises ``NotFound`` for an unknown farm.

    3 queries, constant in plot count. No authz — callers authorize first.
    """
    moment = now or datetime.now(UTC)

    farm = await session.get(Farm, farm_id)  # query 1
    if farm is None:
        raise NotFound("Farm not found.")

    rows = (
        await session.execute(
            select(
                Plot.id,
                Plot.name,
                Plot.area_hectares,
                PlotState.crop,
                PlotState.growth_stage,
                PlotState.planted_on,
            )
            .outerjoin(PlotState, PlotState.plot_id == Plot.id)
            .where(Plot.farm_id == farm_id)
            .order_by(Plot.created_at, Plot.id)
        )
    ).all()  # query 2

    cache = await session.get(FarmSignalCache, farm_id)  # query 3

    plots = [
        PlotStateView(
            plot_id=row.id,
            name=row.name,
            area_hectares=row.area_hectares,
            crop=row.crop,
            growth_stage=row.growth_stage,
            planted_on=row.planted_on,
            days_since_planted=(
                None if row.planted_on is None else (moment.date() - row.planted_on).days
            ),
        )
        for row in rows
    ]
    planted = [plot for plot in plots if plot.crop is not None]
    return FarmStateView(
        farm_id=farm.id,
        farmer_id=farm.farmer_id,
        name=farm.name,
        plots=plots,
        plot_count=len(plots),
        planted_plot_count=len(planted),
        crops=sorted({plot.crop for plot in planted if plot.crop is not None}),
        signals=SignalCacheView(
            signals={} if cache is None else dict(cache.signals),
            refreshed_at=None if cache is None else cache.refreshed_at,
            age_seconds=(
                None
                if cache is None or cache.refreshed_at is None
                else int((moment - cache.refreshed_at).total_seconds())
            ),
        ),
    )


async def set_plot_state(
    session: AsyncSession,
    plot_id: uuid.UUID,
    *,
    crop: str,
    growth_stage: str,
    planted_on: date,
) -> None:
    """Idempotent upsert of a plot's crop facts. Commits."""
    if growth_stage not in GROWTH_STAGES:
        raise ValidationFailed(f"growth_stage must be one of: {', '.join(GROWTH_STAGES)}")
    if not crop.strip():
        raise ValidationFailed("crop must not be empty.")
    if await session.get(Plot, plot_id) is None:
        raise NotFound("Plot not found.")

    stmt = pg_insert(PlotState).values(
        plot_id=plot_id, crop=crop, growth_stage=growth_stage, planted_on=planted_on
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[PlotState.plot_id],
        set_={
            "crop": stmt.excluded.crop,
            "growth_stage": stmt.excluded.growth_stage,
            "planted_on": stmt.excluded.planted_on,
            "updated_at": func.now(),
        },
    )
    await session.execute(stmt)
    await session.commit()


async def clear_plot_state(session: AsyncSession, plot_id: uuid.UUID) -> None:
    """Idempotent: succeeds whether or not a state row existed. Commits."""
    await session.execute(delete(PlotState).where(PlotState.plot_id == plot_id))
    await session.commit()


async def put_signals(
    session: AsyncSession,
    farm_id: uuid.UUID,
    *,
    signals: dict[str, Any],
    refreshed_at: datetime | None = None,
) -> None:
    """Upsert the farm's signal cache, replacing the document wholesale
    (per-provider merging is the ingestion layer's job, M023+). Commits."""
    if await session.get(Farm, farm_id) is None:
        raise NotFound("Farm not found.")

    stmt = pg_insert(FarmSignalCache).values(
        farm_id=farm_id,
        signals=signals,
        refreshed_at=refreshed_at or datetime.now(UTC),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[FarmSignalCache.farm_id],
        set_={
            "signals": stmt.excluded.signals,
            "refreshed_at": stmt.excluded.refreshed_at,
            "updated_at": func.now(),
        },
    )
    await session.execute(stmt)
    await session.commit()
