"""Farm State API (M020): HTTP surface for the Farm Digital Twin.

Four routes wired to M019's service. Every route starts with M014's
authorization helpers (``_authorized_farm`` / ``_authorized_plot``)
*before* the service is touched — the service itself does no authz
(M019 contract). Matrix: admin everything; owner farmer own farms;
extension officer read-only (writes → 403); non-owner farmer → 404
(no existence oracle); anon → 401.

No date policy: ``planted_on`` may be a future plan (M019 decision —
``days_since_planted`` is exposed as-is, possibly negative).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

from src.api.deps import CurrentUserDep, SessionDep
from src.api.v1.farms import _authorized_farm
from src.api.v1.plots import _authorized_plot
from src.models import GROWTH_STAGES
from src.services.farm_state import (
    FarmStateView,
    clear_plot_state,
    get_farm_state,
    put_signals,
    set_plot_state,
)

router = APIRouter(prefix="/farms", tags=["farm-state"])

MAX_SIGNAL_JSON_CHARS = 50_000
MAX_CROP_CHARS = 80  # mirrors the plot_states.crop String(80) column


class PlotStateUpsert(BaseModel):
    """Body for PUT .../plots/{plot_id}/state."""

    crop: str = Field(min_length=1, max_length=MAX_CROP_CHARS)
    growth_stage: str
    planted_on: date

    @field_validator("growth_stage")
    @classmethod
    def _stage_known(cls, value: str) -> str:
        if value not in GROWTH_STAGES:
            raise ValueError(f"growth_stage must be one of: {', '.join(GROWTH_STAGES)}")
        return value


class SignalsUpsert(BaseModel):
    """Body for PUT .../signals. Size-capped, tz-safe."""

    signals: dict[str, Any]
    refreshed_at: datetime | None = None

    @field_validator("signals")
    @classmethod
    def _size_cap(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(json.dumps(value)) > MAX_SIGNAL_JSON_CHARS:
            raise ValueError(f"signals document exceeds {MAX_SIGNAL_JSON_CHARS} characters")
        return value

    @field_validator("refreshed_at")
    @classmethod
    def _attach_utc(cls, value: datetime | None) -> datetime | None:
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=UTC)


@router.get("/{farm_id}/state", response_model=FarmStateView)
async def read_farm_state(
    farm_id: uuid.UUID, session: SessionDep, current: CurrentUserDep
) -> FarmStateView:
    """The twin view (plots + crop state + signal cache). Read matrix."""
    await _authorized_farm(session, farm_id, current, for_write=False)
    return await get_farm_state(session, farm_id)


@router.put("/{farm_id}/plots/{plot_id}/state", status_code=status.HTTP_204_NO_CONTENT)
async def upsert_plot_state(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    payload: PlotStateUpsert,
    session: SessionDep,
    current: CurrentUserDep,
) -> None:
    """Set a plot's crop facts (owner/admin; officer → 403; else 404)."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=True)
    await set_plot_state(
        session,
        plot_id,
        crop=payload.crop,
        growth_stage=payload.growth_stage,
        planted_on=payload.planted_on,
    )


@router.delete("/{farm_id}/plots/{plot_id}/state", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot_state(
    farm_id: uuid.UUID, plot_id: uuid.UUID, session: SessionDep, current: CurrentUserDep
) -> None:
    """Clear a plot's crop facts; idempotent 204 either way."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=True)
    await clear_plot_state(session, plot_id)


@router.put("/{farm_id}/signals", status_code=status.HTTP_204_NO_CONTENT)
async def upsert_farm_signals(
    farm_id: uuid.UUID,
    payload: SignalsUpsert,
    session: SessionDep,
    current: CurrentUserDep,
) -> None:
    """Replace the farm's signal cache wholesale (owner/admin; officer → 403)."""
    await _authorized_farm(session, farm_id, current, for_write=True)
    await put_signals(session, farm_id, signals=payload.signals, refreshed_at=payload.refreshed_at)
