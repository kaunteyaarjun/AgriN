"""Farm CRUD endpoints with GeoJSON boundaries (M014).

Ownership mirrors M012: farmers act only on farms of their **own**
farmer profile (resolved server-side via ``farmers.user_id``), admins do
everything, extension officers read. Non-owner farmers get 404 — no
existence oracle (M017 input). GeoJSON is validated in pydantic, written
with ``ST_GeomFromGeoJSON`` and read back with ``ST_AsGeoJSON`` in the
same SELECT (no N+1).
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
from src.core.errors import Conflict, NotFound, PermissionDenied, ValidationFailed
from src.models import Farm, Farmer, User, UserRole

router = APIRouter(prefix="/farms", tags=["farms"])

MAX_GEOJSON_CHARS = 200_000
MAX_AREA_HECTARES = 1_000_000


def _validate_geojson(value: dict[str, Any]) -> dict[str, Any]:
    """Structural GeoJSON checks for Polygon/MultiPolygon (WGS84)."""
    if value.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("geo must be a GeoJSON Polygon or MultiPolygon")
    if len(json.dumps(value)) > MAX_GEOJSON_CHARS:
        raise ValueError(f"geo payload exceeds {MAX_GEOJSON_CHARS} characters")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("geo.coordinates must be a non-empty array")
    polygons = [coordinates] if value["type"] == "Polygon" else coordinates
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise ValueError("each polygon needs at least one ring")
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                raise ValueError("each ring needs at least 4 positions")
            if ring[0] != ring[-1]:
                raise ValueError("rings must be closed (first position == last)")
            for position in ring:
                if not isinstance(position, list) or len(position) < 2:
                    raise ValueError("positions must be [lon, lat] pairs")
                lon, lat = position[0], position[1]
                if isinstance(lon, bool) or not isinstance(lon, (int, float)):
                    raise ValueError("longitude must be numeric")
                if isinstance(lat, bool) or not isinstance(lat, (int, float)):
                    raise ValueError("latitude must be numeric")
                if not -180 <= lon <= 180 or not -90 <= lat <= 90:
                    raise ValueError("coordinates out of WGS84 bounds")
    return value


def _geo_value(payload_geo: dict[str, Any] | None) -> Any:
    if payload_geo is None:
        return None
    return func.ST_GeomFromGeoJSON(json.dumps(payload_geo))


class FarmCreate(BaseModel):
    """Creation body. ``farmer_id`` = admin target profile; a farmer's
    self-create forces their own profile (mismatch → 403)."""

    farmer_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    area_hectares: Decimal | None = Field(
        default=None, ge=0, le=MAX_AREA_HECTARES, max_digits=10, decimal_places=2
    )
    geo: dict[str, Any] | None = None

    @field_validator("geo")
    @classmethod
    def _geo_valid(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else _validate_geojson(value)


class FarmPatch(BaseModel):
    """Partial update; at least one field; farmer_id is immutable."""

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


class FarmRead(BaseModel):
    id: uuid.UUID
    farmer_id: uuid.UUID
    name: str
    area_hectares: Decimal | None
    geo: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class FarmList(BaseModel):
    items: list[FarmRead]
    total: int
    limit: int
    offset: int


_SELECT_FARM_ROW = (
    Farm.id,
    Farm.farmer_id,
    Farm.name,
    Farm.area_hectares,
    Farm.created_at,
    Farm.updated_at,
    func.ST_AsGeoJSON(Farm.geo).label("geo_json"),
)


def _row_to_read(record: Any) -> FarmRead:
    return FarmRead(
        id=record.id,
        farmer_id=record.farmer_id,
        name=record.name,
        area_hectares=record.area_hectares,
        geo=json.loads(record.geo_json) if record.geo_json else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


async def _select_row(session: SessionDep, farm_id: uuid.UUID) -> FarmRead | None:
    record = (
        await session.execute(select(*_SELECT_FARM_ROW).where(Farm.id == farm_id))
    ).one_or_none()
    return None if record is None else _row_to_read(record)


async def _authorized_farm(
    session: SessionDep, farm_id: uuid.UUID, current: User, *, for_write: bool
) -> FarmRead:
    """One joined SELECT: row + owner (farmer.user_id) → authz per matrix."""
    record = (
        await session.execute(
            select(*_SELECT_FARM_ROW, Farmer.user_id.label("owner_user_id"))
            .join(Farmer, Farm.farmer_id == Farmer.id)
            .where(Farm.id == farm_id)
        )
    ).one_or_none()
    if record is None:
        raise NotFound("Farm not found.")
    if current.role is UserRole.admin:
        return _row_to_read(record)
    if current.role is UserRole.extension_officer:
        if for_write:
            raise PermissionDenied()
        return _row_to_read(record)
    if record.owner_user_id != current.id:
        raise NotFound("Farm not found.")
    return _row_to_read(record)


@router.post("", response_model=FarmRead, status_code=status.HTTP_201_CREATED)
async def create_farm(
    payload: FarmCreate, session: SessionDep, current: CurrentUserDep
) -> FarmRead:
    """Create a farm (farmer: own profile; admin: any farmer profile)."""
    if current.role is UserRole.farmer:
        own_profile_id = await session.scalar(select(Farmer.id).where(Farmer.user_id == current.id))
        if own_profile_id is None:
            raise Conflict("Create your farmer profile before adding farms.")
        if payload.farmer_id is not None and payload.farmer_id != own_profile_id:
            raise PermissionDenied("You may only add farms to your own profile.")
        farmer_id = own_profile_id
    elif current.role is UserRole.admin:
        if payload.farmer_id is None:
            raise ValidationFailed("farmer_id is required.")
        if await session.get(Farmer, payload.farmer_id) is None:
            raise NotFound("No farmer profile with that id.")
        farmer_id = payload.farmer_id
    else:
        raise PermissionDenied()

    farm = Farm(farmer_id=farmer_id, name=payload.name, area_hectares=payload.area_hectares)
    if payload.geo is not None:
        farm.geo = _geo_value(payload.geo)
    session.add(farm)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise Conflict("A farm with that name already exists for this farmer.") from None
    created = await _select_row(session, farm.id)
    if created is None:  # unreachable: the row was just committed
        raise NotFound("Farm not found.")
    return created


@router.get("", response_model=FarmList)
async def list_farms(
    session: SessionDep,
    current: CurrentUserDep,
    farmer_id: Annotated[uuid.UUID | None, Query(description="admin/officer filter")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FarmList:
    """List farms: farmer auto-scoped to own profile; admin/officer all."""
    conditions = []
    if current.role is UserRole.farmer:
        own_profile_id = await session.scalar(select(Farmer.id).where(Farmer.user_id == current.id))
        if own_profile_id is None:
            return FarmList(items=[], total=0, limit=limit, offset=offset)
        conditions.append(Farm.farmer_id == own_profile_id)
    elif farmer_id is not None:
        conditions.append(Farm.farmer_id == farmer_id)

    count_stmt = select(func.count()).select_from(Farm)
    list_stmt = select(*_SELECT_FARM_ROW).order_by(Farm.created_at, Farm.id)
    if conditions:
        count_stmt = count_stmt.where(*conditions)
        list_stmt = list_stmt.where(*conditions)
    total = await session.scalar(count_stmt) or 0
    records = (await session.execute(list_stmt.limit(limit).offset(offset))).all()
    return FarmList(
        items=[_row_to_read(record) for record in records],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{farm_id}", response_model=FarmRead)
async def get_farm(farm_id: uuid.UUID, session: SessionDep, current: CurrentUserDep) -> FarmRead:
    """Fetch one farm (admin/officer any; owner farmer own; else 404)."""
    return await _authorized_farm(session, farm_id, current, for_write=False)


@router.patch("/{farm_id}", response_model=FarmRead)
async def patch_farm(
    farm_id: uuid.UUID, payload: FarmPatch, session: SessionDep, current: CurrentUserDep
) -> FarmRead:
    """Partial update (admin/owner; officer → 403; non-owner → 404)."""
    await _authorized_farm(session, farm_id, current, for_write=True)
    values: dict[str, Any] = {}
    if "name" in payload.model_fields_set:
        values["name"] = payload.name
    if "area_hectares" in payload.model_fields_set:
        values["area_hectares"] = payload.area_hectares
    if "geo" in payload.model_fields_set:
        values["geo"] = _geo_value(payload.geo)
    await session.execute(update(Farm).where(Farm.id == farm_id).values(**values))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise Conflict("A farm with that name already exists for this farmer.") from None
    updated = await _select_row(session, farm_id)
    if updated is None:  # unreachable: the row was just updated
        raise NotFound("Farm not found.")
    return updated


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(farm_id: uuid.UUID, session: SessionDep, current: CurrentUserDep) -> None:
    """Delete a farm (admin only; owner/officer → 403 after authz, else 404)."""
    await _authorized_farm(session, farm_id, current, for_write=True)
    if current.role is not UserRole.admin:
        raise PermissionDenied()
    await session.execute(delete(Farm).where(Farm.id == farm_id))
    await session.commit()
