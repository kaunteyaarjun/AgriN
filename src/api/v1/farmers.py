"""Farmer profile CRUD endpoints (M012).

Authorization (default-deny, M010 dependencies + server-side ownership):
- POST: admin creates a profile for any ``role=farmer`` user; a farmer
  creates their own only (mismatched ``user_id`` → 403).
- GET list: admin + extension_officer, bounded pagination.
- GET/PATCH: admin and officer can read all; farmers only their own —
  non-owned rows are 404 (no existence oracle, logged for M017).
- PATCH: admin or the owning farmer; officer → 403.
- DELETE: admin only (owner-farmer/officer → 403 after read authorization).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.api.deps import CurrentUserDep, SessionDep, require_role
from src.core.errors import Conflict, NotFound, PermissionDenied, ValidationFailed
from src.models import Farmer, User, UserRole

router = APIRouter(prefix="/farmers", tags=["farmers"])

PHONE_PATTERN = r"^\+?[0-9()\s-]{5,32}$"


class FarmerCreate(BaseModel):
    """Creation body. ``user_id`` is the admin's target account; a farmer's
    self-create forces own id (mismatch → 403)."""

    user_id: uuid.UUID | None = None
    full_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    village: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)


class FarmerPatch(BaseModel):
    """Partial update; at least one field must be provided."""

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    village: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)

    @model_validator(mode="before")
    @classmethod
    def _at_least_one_field(cls, data: object) -> object:
        if not isinstance(data, dict) or not data:
            raise ValueError("at least one field must be provided")
        return data


class FarmerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    phone: str | None
    village: str | None
    district: str | None
    created_at: datetime
    updated_at: datetime


class FarmerList(BaseModel):
    items: list[FarmerRead]
    total: int
    limit: int
    offset: int


async def _authorize_read(session: SessionDep, farmer_id: uuid.UUID, current: User) -> Farmer:
    """Row + read authorization: non-owner farmers get 404 (no existence leak)."""
    farmer = await session.get(Farmer, farmer_id)
    if farmer is None:
        raise NotFound("Farmer profile not found.")
    if current.role in (UserRole.admin, UserRole.extension_officer):
        return farmer
    if farmer.user_id == current.id:
        return farmer
    raise NotFound("Farmer profile not found.")


async def _authorize_write(session: SessionDep, farmer_id: uuid.UUID, current: User) -> Farmer:
    """Row + write authorization: officer reads but never writes; farmer
    non-owner disappears behind 404."""
    farmer = await session.get(Farmer, farmer_id)
    if farmer is None:
        raise NotFound("Farmer profile not found.")
    if current.role is UserRole.admin:
        return farmer
    if current.role is UserRole.extension_officer:
        raise PermissionDenied()
    if farmer.user_id != current.id:
        raise NotFound("Farmer profile not found.")
    return farmer


@router.post("", response_model=FarmerRead, status_code=status.HTTP_201_CREATED)
async def create_farmer(
    payload: FarmerCreate, session: SessionDep, current: CurrentUserDep
) -> Farmer:
    """Create a farmer profile (admin: any farmer account; farmer: own)."""
    if current.role is UserRole.farmer:
        if payload.user_id is not None and payload.user_id != current.id:
            raise PermissionDenied("You may only create a profile for yourself.")
        target_id = current.id
    elif current.role is UserRole.admin:
        if payload.user_id is None:
            raise ValidationFailed("user_id is required.")
        target = await session.get(User, payload.user_id)
        if target is None:
            raise NotFound("No user with that id.")
        if target.role is not UserRole.farmer:
            raise Conflict("That account is not a farmer.")
        target_id = target.id
    else:
        raise PermissionDenied()

    existing = await session.scalar(select(Farmer).where(Farmer.user_id == target_id))
    if existing is not None:
        raise Conflict("That account already has a farmer profile.")

    farmer = Farmer(
        user_id=target_id,
        full_name=payload.full_name,
        phone=payload.phone,
        village=payload.village,
        district=payload.district,
    )
    session.add(farmer)
    try:
        await session.commit()
    except IntegrityError:
        # Concurrent create raced past the pre-check: UNIQUE(user_id) decided.
        await session.rollback()
        raise Conflict("That account already has a farmer profile.") from None
    await session.refresh(farmer)
    return farmer


@router.get("", response_model=FarmerList)
async def list_farmers(
    session: SessionDep,
    _: Annotated[User, Depends(require_role(UserRole.admin, UserRole.extension_officer))],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FarmerList:
    """List farmer profiles (admin + extension_officer), paginated."""
    total = await session.scalar(select(func.count()).select_from(Farmer)) or 0
    rows = (
        (
            await session.execute(
                select(Farmer).order_by(Farmer.created_at, Farmer.id).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return FarmerList(
        items=[FarmerRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{farmer_id}", response_model=FarmerRead)
async def get_farmer(
    farmer_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUserDep,
) -> Farmer:
    """Fetch one profile (admin/officer any; farmer own only, else 404)."""
    return await _authorize_read(session, farmer_id, current)


@router.patch("/{farmer_id}", response_model=FarmerRead)
async def patch_farmer(
    farmer_id: uuid.UUID,
    payload: FarmerPatch,
    session: SessionDep,
    current: CurrentUserDep,
) -> Farmer:
    """Partial update (admin any; owning farmer own; officer → 403)."""
    farmer = await _authorize_write(session, farmer_id, current)
    for field_name in payload.model_fields_set:
        setattr(farmer, field_name, getattr(payload, field_name))
    await session.commit()
    await session.refresh(farmer)
    return farmer


@router.delete("/{farmer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farmer(
    farmer_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUserDep,
) -> None:
    """Delete a profile (admin only; owner-farmer/officer → 403)."""
    farmer = await _authorize_write(session, farmer_id, current)
    if current.role is not UserRole.admin:
        raise PermissionDenied()
    await session.delete(farmer)
    await session.commit()
