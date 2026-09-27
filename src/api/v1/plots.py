"""Plot CRUD endpoints nested under farms (M016).

Every verb starts with M014's ``_authorized_farm`` on the URL's
``farm_id`` — plots inherit the parent farm's ownership rules (owner
farmer / admin / officer-read; non-owner farmer → 404, no oracle).
Plot ids are always scoped to the URL farm (cross-farm → 404).
Containment: when a plot boundary is provided and the farm boundary
exists, ``ST_Covers(farm.geo, plot.geo)`` must hold or → 422.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from src.api.deps import CurrentUserDep, SessionDep
from src.api.v1.farms import (
    MAX_AREA_HECTARES,
    _authorized_farm,
    _geo_value,
    _validate_geojson,
)
from src.core.errors import Conflict, NotFound, PermissionDenied, ValidationFailed
from src.models import Farm, Plot, User, UserRole

router = APIRouter(prefix="/farms/{farm_id}/plots", tags=["plots"])


class PlotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    area_hectares: Decimal | None = Field(
        default=None, ge=0, le=MAX_AREA_HECTARES, max_digits=10, decimal_places=2
    )
    geo: dict[str, Any] | None = None

    @field_validator("geo")
    @classmethod
    def _geo_valid(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else _validate_geojson(value)


class PlotPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    area_hectares: Decimal | None = Field(
        default=None, ge=0, le=MAX_AREA_HECTARES, max_digits=10, decimal_places=2
    )
    geo: dict[str, Any] | None = None

    @field_validator("geo")
    @classmethod
    def _geo_valid(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else _validate_geojson(value)

    @model_validator(mode="before")
    @classmethod
    def _at_least_one_field(cls, data: object) -> object:
        if not isinstance(data, dict) or not data:
            raise ValueError("at least one field must be provided")
        return data


class PlotRead(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID
    name: str
    area_hectares: Decimal | None
    geo: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class PlotList(BaseModel):
    items: list[PlotRead]
    total: int
    limit: int
    offset: int


_SELECT_PLOT_ROW = (
    Plot.id,
    Plot.farm_id,
    Plot.name,
    Plot.area_hectares,
    Plot.created_at,
    Plot.updated_at,
    func.ST_AsGeoJSON(Plot.geo).label("geo_json"),
)


def _row_to_read(record: Any) -> PlotRead:
    return PlotRead(
        id=record.id,
        farm_id=record.farm_id,
        name=record.name,
        area_hectares=record.area_hectares,
        geo=json.loads(record.geo_json) if record.geo_json else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


async def _assert_within_farm(session: SessionDep, farm_id: uuid.UUID, geo: Any) -> None:
    """Containment gate: plot boundary must be covered by the farm boundary.

    Skipped when the plot has no geo or the farm boundary is NULL
    (nothing to enforce against).
    """
    if geo is None:
        return
    covered = await session.scalar(
        select(func.ST_Covers(Farm.geo, _geo_value(geo))).where(Farm.id == farm_id)
    )
    if covered is False:
        raise ValidationFailed("The plot boundary must lie within the farm boundary.")


async def _select_row(
    session: SessionDep, farm_id: uuid.UUID, plot_id: uuid.UUID
) -> PlotRead | None:
    record = (
        await session.execute(
            select(*_SELECT_PLOT_ROW).where(Plot.id == plot_id, Plot.farm_id == farm_id)
        )
    ).one_or_none()
    return None if record is None else _row_to_read(record)


async def _authorized_plot(
    session: SessionDep,
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    current: User,
    *,
    for_write: bool,
) -> PlotRead:
    """Parent-farm authz first, then the plot scoped to that farm."""
    await _authorized_farm(session, farm_id, current, for_write=for_write)
    plot = await _select_row(session, farm_id, plot_id)
    if plot is None:
        raise NotFound("Plot not found.")
    return plot


@router.post("", response_model=PlotRead, status_code=status.HTTP_201_CREATED)
async def create_plot(
    farm_id: uuid.UUID, payload: PlotCreate, session: SessionDep, current: CurrentUserDep
) -> PlotRead:
    """Create a plot in the given farm (owner/admin; officer → 403,
    non-owner farmer → 404 via parent-farm authz)."""
    await _authorized_farm(session, farm_id, current, for_write=True)
    await _assert_within_farm(session, farm_id, payload.geo)
    plot = Plot(farm_id=farm_id, name=payload.name, area_hectares=payload.area_hectares)
    if payload.geo is not None:
        plot.geo = _geo_value(payload.geo)
    session.add(plot)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise Conflict("A plot with that name already exists for this farm.") from None
    created = await _select_row(session, farm_id, plot.id)
    if created is None:  # unreachable: the row was just committed
        raise NotFound("Plot not found.")
    return created


@router.get("", response_model=PlotList)
async def list_plots(
    farm_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PlotList:
    """List a farm's plots (same read authz as the farm itself)."""
    await _authorized_farm(session, farm_id, current, for_write=False)
    total = (
        await session.scalar(select(func.count()).select_from(Plot).where(Plot.farm_id == farm_id))
        or 0
    )
    records = (
        await session.execute(
            select(*_SELECT_PLOT_ROW)
            .where(Plot.farm_id == farm_id)
            .order_by(Plot.created_at, Plot.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return PlotList(
        items=[_row_to_read(record) for record in records],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{plot_id}", response_model=PlotRead)
async def get_plot(
    farm_id: uuid.UUID, plot_id: uuid.UUID, session: SessionDep, current: CurrentUserDep
) -> PlotRead:
    """Fetch one plot (parent-farm read authz; cross-farm id → 404)."""
    return await _authorized_plot(session, farm_id, plot_id, current, for_write=False)


@router.patch("/{plot_id}", response_model=PlotRead)
async def patch_plot(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    payload: PlotPatch,
    session: SessionDep,
    current: CurrentUserDep,
) -> PlotRead:
    """Partial update (admin/owner; officer → 403; non-owner → 404).
    ``farm_id`` is the URL — never mutable."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=True)
    if "geo" in payload.model_fields_set:
        await _assert_within_farm(session, farm_id, payload.geo)
    values: dict[str, Any] = {}
    if "name" in payload.model_fields_set:
        values["name"] = payload.name
    if "area_hectares" in payload.model_fields_set:
        values["area_hectares"] = payload.area_hectares
    if "geo" in payload.model_fields_set:
        values["geo"] = _geo_value(payload.geo)
    await session.execute(
        update(Plot).where(Plot.id == plot_id, Plot.farm_id == farm_id).values(**values)
    )
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise Conflict("A plot with that name already exists for this farm.") from None
    updated = await _select_row(session, farm_id, plot_id)
    if updated is None:  # unreachable: the row was just updated
        raise NotFound("Plot not found.")
    return updated


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot(
    farm_id: uuid.UUID, plot_id: uuid.UUID, session: SessionDep, current: CurrentUserDep
) -> None:
    """Delete a plot (admin only; owner/officer → 403 after authz,
    non-owner → 404)."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=True)
    if current.role is not UserRole.admin:
        raise PermissionDenied()
    await session.execute(delete(Plot).where(Plot.id == plot_id, Plot.farm_id == farm_id))
    await session.commit()
