"""Farm risk engine (M033): a deterministic, additive risk score.

Risk here is a **tally, not a forecast**: hazard points read the
:class:`~src.engines.health.HealthFactor` verdicts M032 already
produced (so thresholds live in exactly one place), visibility points
cover what the platform cannot see, and every point in the total is an
item you can point at. `score = min(100, sum(items))` and each hazard
keeps its *worst* severity across plots.

What is deliberately **not** scored: the crop's response (M032's
health levels). A farm whose soil is dry gets its points from the dry
soil, not again from the wilting it causes — health and risk are shown
side by side in M048 precisely because they are two views of the same
conditions.

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
    crop_profile_for,
)
from src.services.normalize import FAMILY_KEYS, NormalizedFarmState

RISK_BANDS: Final[tuple[str, ...]] = ("low", "moderate", "high")
BAND_THRESHOLDS: Final[tuple[int, int]] = (25, 60)
MAX_SCORE: Final[int] = 100

SEVERITY_POINTS: Final[dict[str, int]] = {"attention": 15, "stress": 30}
MISSING_SIGNAL_POINTS: Final[int] = 15
STALE_SIGNAL_POINTS: Final[int] = 10
UNREGISTERED_PLOT_POINTS: Final[int] = 10

HAZARD_FACTORS: Final[tuple[str, ...]] = (
    "ndvi",
    "soil_moisture",
    "soil_ph",
    "nitrogen",
    "air_temperature",
    "rainfall",
)

RISK_ORDER: Final[tuple[str, ...]] = (
    "drought",
    "waterlogging",
    "heat",
    "cold",
    "heavy_rain",
    "nutrient_shortfall",
    "soil_ph",
    "low_vigor",
    "unregistered_plots",
    "stale_signals",
    "missing_signals",
)


class RiskItem(BaseModel):
    """One named contribution to the farm's score."""

    name: str
    points: int
    detail: str


class FarmRisk(BaseModel):
    """Farm-level risk: score, band, and every point that made it."""

    farm_id: uuid.UUID
    score: int
    band: str
    items: list[RiskItem]
    hazard_readings_evaluated: int
    hazard_readings_total: int
    plot_count: int
    computed_at: datetime


def risk_band(score: int) -> str:
    """`low` < 25 ≤ `moderate` < 60 ≤ `high` (documented thresholds)."""
    low_max, moderate_max = BAND_THRESHOLDS
    if score < low_max:
        return "low"
    if score < moderate_max:
        return "moderate"
    return "high"


def _hazard_for(factor_name: str, measured: float, profile: CropProfile) -> str | None:
    """Direction matters: dry soil is not wet soil with a sign flipped.

    Only called for hazard factors M032 already judged `attention` or
    `stress`, so the reading is outside the attention band by
    construction.
    """
    if factor_name == "ndvi":
        return "low_vigor"
    if factor_name == "soil_ph":
        return "soil_ph"
    if factor_name == "nitrogen":
        return "nutrient_shortfall"
    if factor_name == "rainfall":
        return "heavy_rain"
    if factor_name == "air_temperature":
        return "heat" if measured > TEMPERATURE_ATTENTION[1] else "cold"
    if factor_name == "soil_moisture":
        return "drought" if measured < profile.moisture_attention_min else "waterlogging"
    return None


def _hazard_readings(health: FarmHealth, points: dict[str, int], details: dict[str, str]) -> int:
    """Worst severity per hazard across plots; returns readings used."""
    evaluated = 0
    for plot_health in health.plots:
        profile = crop_profile_for(plot_health.crop)
        for factor in plot_health.factors:
            if factor.name not in HAZARD_FACTORS or factor.status == "unknown":
                continue
            if factor.measured is None:
                continue
            evaluated += 1
            gain = SEVERITY_POINTS.get(factor.status, 0)
            hazard = _hazard_for(factor.name, factor.measured, profile)
            if gain == 0 or hazard is None:
                continue
            if gain > points[hazard]:
                points[hazard] = gain
                details[hazard] = factor.detail
    return evaluated


def _visibility_penalties(
    state: NormalizedFarmState,
    health: FarmHealth,
    points: dict[str, int],
    details: dict[str, str],
) -> None:
    unregistered = sum(1 for plot in health.plots if plot.crop is None)
    if unregistered:
        points["unregistered_plots"] = UNREGISTERED_PLOT_POINTS
        details["unregistered_plots"] = (
            f"{unregistered} of {len(health.plots)} plots have no crop state"
        )

    if health.stale_families:
        points["stale_signals"] = STALE_SIGNAL_POINTS * len(health.stale_families)
        details["stale_signals"] = "stale: " + ", ".join(health.stale_families)

    missing = [family for family in FAMILY_KEYS if getattr(state.signals, family) is None]
    if missing:
        points["missing_signals"] = MISSING_SIGNAL_POINTS * len(missing)
        details["missing_signals"] = "never ingested: " + ", ".join(missing)


def assess_farm_risk(
    state: NormalizedFarmState,
    health: FarmHealth,
    *,
    now: datetime | None = None,
) -> FarmRisk:
    """Score one farm's risk from its normalized state and health.

    Raises ``ValueError`` when the two describe different farms — a
    caller bug worth failing loudly on, not scoring silently.
    """
    moment = now or datetime.now(UTC)
    if health.farm_id != state.view.farm_id:
        raise ValueError(
            f"health is for farm {health.farm_id}, state is for farm {state.view.farm_id}"
        )

    points: dict[str, int] = dict.fromkeys(RISK_ORDER, 0)
    details: dict[str, str] = {}
    evaluated = _hazard_readings(health, points, details)
    _visibility_penalties(state, health, points, details)

    items = [
        RiskItem(name=name, points=points[name], detail=details[name])
        for name in RISK_ORDER
        if points[name] > 0
    ]
    score = min(MAX_SCORE, sum(points.values()))
    plot_count = len(health.plots)
    return FarmRisk(
        farm_id=state.view.farm_id,
        score=score,
        band=risk_band(score),
        items=items,
        hazard_readings_evaluated=evaluated,
        hazard_readings_total=len(HAZARD_FACTORS) * plot_count,
        plot_count=plot_count,
        computed_at=moment,
    )


__all__ = [
    "BAND_THRESHOLDS",
    "HAZARD_FACTORS",
    "MAX_SCORE",
    "MISSING_SIGNAL_POINTS",
    "RISK_BANDS",
    "RISK_ORDER",
    "SEVERITY_POINTS",
    "STALE_SIGNAL_POINTS",
    "UNREGISTERED_PLOT_POINTS",
    "FarmRisk",
    "RiskItem",
    "assess_farm_risk",
    "risk_band",
]
