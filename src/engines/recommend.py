"""Crop recommendation engine (M034): verdicts → concrete actions.

Where M032 answers *what state is the plot in* and M033 *how bad is the
farm's exposure*, this module answers *what should the farmer do* — one
recommendation per bad factor, each carrying the very sentence M032
used as its evidence (`HealthFactor.detail`), so the action and its
justification can never disagree.

Rules are mappings, not thresholds: direction (drought vs waterlogging,
heat vs cold) comes from the plot's own :class:`CropProfile`, exactly as
M033 does it. Farm-level items (stale or missing signal families) are
how the engine says *why* advice is thin; a plot with any unknown
hazard factor never receives `continue_as_planned` — absence of
evidence is never evidence that nothing needs doing.

Pure computation: no I/O, no database, no clock beyond the injectable
``now``. Same inputs → same output.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final

from pydantic import BaseModel

from src.engines.health import (
    TEMPERATURE_ATTENTION,
    CropProfile,
    FarmHealth,
    PlotHealth,
    crop_profile_for,
)
from src.services.normalize import FAMILY_KEYS, NormalizedFarmState

RECOMMENDATION_PRIORITY: Final[tuple[str, ...]] = ("urgent", "soon", "routine")

RECOMMENDATION_CATEGORIES: Final[tuple[str, ...]] = (
    "irrigation",
    "drainage",
    "fertility",
    "soil_amendment",
    "weather_protection",
    "field_operation",
    "scouting",
    "record_keeping",
    "data_quality",
    "monitoring",
)

RECOMMENDATION_ORDER: Final[tuple[str, ...]] = (
    "set_crop_plan",
    "irrigate",
    "improve_drainage",
    "apply_nitrogen",
    "raise_ph",
    "lower_ph",
    "heat_protection",
    "frost_protection",
    "hold_field_work",
    "inspect_crop",
    "refresh_signals",
    "ingest_missing_signals",
    "continue_as_planned",
)

RECOMMENDATION_SPECS: Final[dict[str, tuple[str, str]]] = {
    "set_crop_plan": ("record_keeping", "Register this plot's crop"),
    "irrigate": ("irrigation", "Irrigate"),
    "improve_drainage": ("drainage", "Improve drainage"),
    "apply_nitrogen": ("fertility", "Apply nitrogen"),
    "raise_ph": ("soil_amendment", "Raise soil pH"),
    "lower_ph": ("soil_amendment", "Lower soil pH"),
    "heat_protection": ("weather_protection", "Protect from heat"),
    "frost_protection": ("weather_protection", "Protect from cold"),
    "hold_field_work": ("field_operation", "Postpone field work"),
    "inspect_crop": ("scouting", "Inspect the crop"),
    "refresh_signals": ("data_quality", "Refresh {family} signals"),
    "ingest_missing_signals": ("data_quality", "Ingest missing {family} signals"),
    "continue_as_planned": ("monitoring", "No action needed"),
}

PRIORITY_BY_STATUS: Final[dict[str, str]] = {"stress": "urgent", "attention": "soon"}


class Recommendation(BaseModel):
    """One actionable item; ``plot_id is None`` marks a farm-level item."""

    code: str
    category: str
    priority: str
    title: str
    detail: str
    plot_id: uuid.UUID | None = None
    plot_name: str | None = None


class FarmRecommendations(BaseModel):
    """Flat, ordered advice for one farm."""

    farm_id: uuid.UUID
    recommendations: list[Recommendation]
    actionable: int
    plot_count: int
    computed_at: datetime


def _build(code: str, detail: str, *, priority: str, family: str | None = None) -> Recommendation:
    category, title_template = RECOMMENDATION_SPECS[code]
    return Recommendation(
        code=code,
        category=category,
        priority=priority,
        title=title_template.format(family=family) if family else title_template,
        detail=detail,
    )


def _code_for(factor_name: str, measured: float, profile: CropProfile) -> str | None:
    """Map a judged factor to its action — direction from the profile."""
    if factor_name == "ndvi":
        return "inspect_crop"
    if factor_name == "soil_ph":
        return "raise_ph" if measured < profile.ph_attention_min else "lower_ph"
    if factor_name == "nitrogen":
        return "apply_nitrogen"
    if factor_name == "rainfall":
        return "hold_field_work"
    if factor_name == "air_temperature":
        if measured > TEMPERATURE_ATTENTION[1]:
            return "heat_protection"
        return "frost_protection"
    if factor_name == "soil_moisture":
        if measured < profile.moisture_attention_min:
            return "irrigate"
        return "improve_drainage"
    return None


def _plot_recommendations(plot_health: PlotHealth, out: list[Recommendation]) -> None:
    plot_id = plot_health.plot_id
    plot_name = plot_health.name

    if plot_health.crop is None:
        rec = _build(
            "set_crop_plan",
            "no crop state for this plot",
            priority="soon",
        )
        out.append(rec.model_copy(update={"plot_id": plot_id, "plot_name": plot_name}))
        return

    profile = crop_profile_for(plot_health.crop)
    blind = False
    for factor in plot_health.factors:
        if factor.status == "unknown" or factor.measured is None:
            blind = True
            continue
        priority = PRIORITY_BY_STATUS.get(factor.status)
        if priority is None:
            continue
        code = _code_for(factor.name, factor.measured, profile)
        if code is None:
            continue
        rec = _build(code, factor.detail, priority=priority)
        out.append(rec.model_copy(update={"plot_id": plot_id, "plot_name": plot_name}))

    if plot_health.level == "healthy" and not blind:
        rec = _build(
            "continue_as_planned",
            "healthy with fresh signals",
            priority="routine",
        )
        out.append(rec.model_copy(update={"plot_id": plot_id, "plot_name": plot_name}))


def _farm_recommendations(
    state: NormalizedFarmState, health: FarmHealth, out: list[Recommendation]
) -> None:
    for family in health.stale_families:
        out.append(
            _build(
                "refresh_signals",
                f"{family} signals are past the freshness window",
                priority="soon",
                family=family,
            )
        )
    for family in FAMILY_KEYS:
        if getattr(state.signals, family) is None:
            out.append(
                _build(
                    "ingest_missing_signals",
                    f"no {family} signals have ever been ingested",
                    priority="soon",
                    family=family,
                )
            )


def _sort_key(rec: Recommendation) -> tuple[int, int, str]:
    return (
        RECOMMENDATION_PRIORITY.index(rec.priority),
        RECOMMENDATION_ORDER.index(rec.code),
        rec.plot_name or "",
    )


def recommend_farm_actions(
    state: NormalizedFarmState,
    health: FarmHealth,
    *,
    now: datetime | None = None,
) -> FarmRecommendations:
    """Recommend actions for one farm from its normalized state + health.

    Raises ``ValueError`` when the two describe different farms.
    """
    moment = now or datetime.now(UTC)
    if health.farm_id != state.view.farm_id:
        raise ValueError(
            f"health is for farm {health.farm_id}, state is for farm {state.view.farm_id}"
        )

    out: list[Recommendation] = []
    for plot_health in health.plots:
        _plot_recommendations(plot_health, out)
    _farm_recommendations(state, health, out)
    out.sort(key=_sort_key)

    return FarmRecommendations(
        farm_id=state.view.farm_id,
        recommendations=out,
        actionable=sum(1 for rec in out if rec.code != "continue_as_planned"),
        plot_count=len(health.plots),
        computed_at=moment,
    )


__all__ = [
    "PRIORITY_BY_STATUS",
    "RECOMMENDATION_CATEGORIES",
    "RECOMMENDATION_ORDER",
    "RECOMMENDATION_PRIORITY",
    "RECOMMENDATION_SPECS",
    "FarmRecommendations",
    "Recommendation",
    "recommend_farm_actions",
]
