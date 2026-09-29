"""Crop health analysis engine (M032): rules over the normalized twin.

Turns a :class:`~src.services.normalize.NormalizedFarmState` into an
explainable per-plot health assessment. Seven factors are always
evaluated in a fixed order; each carries its measured value, the
threshold it was judged against, and a one-line evidence string. The
plot's ``level`` is decided in two steps: ``planting`` gates it (no
crop registered, or planted in the future → ``unknown``), then the
worst non-``unknown`` signal factor picks `healthy` / `watch` /
`stressed` — so every answer traces back to exactly one rule, and
missing data can never masquerade as health.

This module is also where the platform's **staleness policy** finally
lives (M019 and M031 both deferred it): a signal family older than
:data:`STALE_AFTER_SECONDS` is not judged at all — its factors become
``unknown`` and the family is listed in ``FarmHealth.stale_families``.
The satellite threshold is 90 days because M027 measured 47-day NASA
latency at Nairobi: a tighter threshold would declare every real
reading stale.

Honest limits, by design:
- Signals are farm-level (farm centroid, M023/M026/M029), so two
  plots of the same crop on one farm score identically — per-plot
  variation comes only from the crop profile and the planting date.
- Thresholds are **demo agronomy**: documented constants, not expert
  advice, and deliberately stage-independent in M032.

Pure computation: no I/O, no database, no clock beyond the injectable
``now``. Same input + same ``now`` → identical output.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

from pydantic import BaseModel

from src.services.farm_state import PlotStateView
from src.services.normalize import NormalizedFarmState, NormalizedSignals

HEALTH_LEVELS: Final[tuple[str, ...]] = ("healthy", "watch", "stressed", "unknown")
FACTOR_STATUSES: Final[tuple[str, ...]] = ("ok", "attention", "stress", "unknown")

FACTOR_NAMES: Final[tuple[str, ...]] = (
    "planting",
    "ndvi",
    "soil_moisture",
    "soil_ph",
    "nitrogen",
    "air_temperature",
    "rainfall",
)

STALE_AFTER_SECONDS: Final[dict[str, int]] = {
    "weather": 86_400,  # 24 h: in-situ / current-hour feed
    "soil": 86_400,  # 24 h: in-situ probe
    "satellite": 90 * 86_400,  # 90 d: 16-day composite + measured 47-day latency
}

TEMPERATURE_ATTENTION: Final[tuple[float, float]] = (10.0, 35.0)
TEMPERATURE_STRESS: Final[tuple[float, float]] = (5.0, 40.0)
RAINFALL_ATTENTION_MM_PER_DAY: Final[float] = 30.0
RAINFALL_STRESS_MM_PER_DAY: Final[float] = 60.0


@dataclass(frozen=True)
class CropProfile:
    """Per-crop thresholds. Defaults are the platform's baseline
    (unknown crops use them); named crops override a subset."""

    ndvi_watch: float = 0.40
    ndvi_stress: float = 0.25
    moisture_attention_min: float = 30.0
    moisture_stress_min: float = 20.0
    moisture_attention_max: float = 70.0
    moisture_stress_max: float = 85.0
    ph_attention_min: float = 5.8
    ph_stress_min: float = 5.0
    ph_attention_max: float = 7.2
    ph_stress_max: float = 7.8
    nitrogen_attention_min: float = 40.0
    nitrogen_stress_min: float = 20.0


DEFAULT_CROP_PROFILE: Final[CropProfile] = CropProfile()

CROP_PROFILES: Final[dict[str, CropProfile]] = {
    "maize": CropProfile(
        moisture_attention_min=35.0,
        moisture_stress_min=25.0,
        nitrogen_attention_min=50.0,
        nitrogen_stress_min=20.0,
        ph_attention_min=5.8,
        ph_attention_max=7.2,
    ),
    "wheat": CropProfile(
        moisture_attention_min=30.0,
        moisture_stress_min=20.0,
        nitrogen_attention_min=40.0,
        nitrogen_stress_min=20.0,
        ph_attention_min=6.0,
        ph_attention_max=7.0,
    ),
    "beans": CropProfile(
        moisture_attention_min=35.0,
        moisture_stress_min=25.0,
        nitrogen_attention_min=30.0,
        nitrogen_stress_min=10.0,
        ph_attention_min=6.0,
        ph_attention_max=7.5,
    ),
}


class HealthFactor(BaseModel):
    """One rule's verdict: status, the value it saw, its evidence."""

    name: str
    status: str
    measured: float | None
    detail: str


class PlotHealth(BaseModel):
    """The health of one plot at one moment."""

    plot_id: uuid.UUID
    name: str
    crop: str | None
    growth_stage: str | None
    days_since_planted: int | None
    level: str
    factors: list[HealthFactor]
    factors_evaluated: int
    factor_count: int
    computed_at: datetime


class FarmHealth(BaseModel):
    """Farm rollup: worst plot level plus signal freshness."""

    farm_id: uuid.UUID
    level: str
    plots: list[PlotHealth]
    plot_count: int
    stale_families: list[str]
    computed_at: datetime


def _fmt(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def _fmt_ndvi(value: float) -> str:
    """NDVI is quoted to 2 dp — one decimal would read as `0.2 < 0.2`."""
    return _fmt(value, 2)


def _factor(name: str, status: str, measured: float | None, detail: str) -> HealthFactor:
    return HealthFactor(name=name, status=status, measured=measured, detail=detail)


def _usable(signals: NormalizedSignals, family: str) -> tuple[Any, str | None]:
    """The family payload when it exists, is timestamped and is fresh;
    otherwise ``(None, why)`` — staleness is decided here (M032)."""
    payload = getattr(signals, family)
    if payload is None:
        return None, f"no {family} signal"
    age = payload.age_seconds
    if age is None:
        return None, f"{family} signal has no observation time"
    threshold = STALE_AFTER_SECONDS[family]
    if age > threshold:
        return None, f"{family} signal stale ({age}s > {threshold}s)"
    return payload, None


def crop_profile_for(crop: str | None) -> CropProfile:
    key = (crop or "").strip().lower()
    return CROP_PROFILES.get(key, DEFAULT_CROP_PROFILE)


def crop_label_for(crop: str | None) -> str:
    return (crop or "unregistered crop").strip().lower()


def _planting_factor(plot: PlotStateView, moment: datetime) -> HealthFactor:
    if plot.crop is None:
        return _factor("planting", "unknown", None, "no crop registered for this plot")
    if plot.planted_on is None:
        return _factor("planting", "unknown", None, "no planting date for this plot")
    if plot.planted_on > moment.date():
        return _factor(
            "planting",
            "unknown",
            None,
            f"planted_on {plot.planted_on.isoformat()} is in the future",
        )
    days = plot.days_since_planted
    if days is None:
        days = (moment.date() - plot.planted_on).days
    stage = plot.growth_stage or "unknown stage"
    return _factor(
        "planting",
        "ok",
        float(days),
        f"planted {plot.planted_on.isoformat()} ({stage}, day {days})",
    )


def _ndvi_factor(signals: NormalizedSignals, profile: CropProfile, label: str) -> HealthFactor:
    payload, reason = _usable(signals, "satellite")
    if payload is None or payload.ndvi is None:
        return _factor("ndvi", "unknown", None, reason or "no ndvi reading")
    value: float = payload.ndvi
    if value < profile.ndvi_stress:
        return _factor(
            "ndvi",
            "stress",
            value,
            f"ndvi {_fmt_ndvi(value)} < {_fmt_ndvi(profile.ndvi_stress)} ({label})",
        )
    if value < profile.ndvi_watch:
        return _factor(
            "ndvi",
            "attention",
            value,
            f"ndvi {_fmt_ndvi(value)} < {_fmt_ndvi(profile.ndvi_watch)} ({label})",
        )
    return _factor(
        "ndvi",
        "ok",
        value,
        f"ndvi {_fmt_ndvi(value)} >= {_fmt_ndvi(profile.ndvi_watch)} ({label})",
    )


def _moisture_factor(signals: NormalizedSignals, profile: CropProfile, label: str) -> HealthFactor:
    name = "soil_moisture"
    payload, reason = _usable(signals, "soil")
    if payload is None or payload.soil_moisture_pct is None:
        return _factor(name, "unknown", None, reason or "no soil moisture reading")
    value: float = payload.soil_moisture_pct
    if value < profile.moisture_stress_min:
        return _factor(
            name,
            "stress",
            value,
            f"soil moisture {_fmt(value)}% < {_fmt(profile.moisture_stress_min)}% ({label})",
        )
    if value > profile.moisture_stress_max:
        return _factor(
            name,
            "stress",
            value,
            f"soil moisture {_fmt(value)}% > {_fmt(profile.moisture_stress_max)}% ({label})",
        )
    if value < profile.moisture_attention_min:
        return _factor(
            name,
            "attention",
            value,
            f"soil moisture {_fmt(value)}% < {_fmt(profile.moisture_attention_min)}% ({label})",
        )
    if value > profile.moisture_attention_max:
        return _factor(
            name,
            "attention",
            value,
            f"soil moisture {_fmt(value)}% > {_fmt(profile.moisture_attention_max)}% ({label})",
        )
    low = _fmt(profile.moisture_attention_min)
    high = _fmt(profile.moisture_attention_max)
    return _factor(name, "ok", value, f"soil moisture {_fmt(value)}% in {low}-{high}% ({label})")


def _ph_factor(signals: NormalizedSignals, profile: CropProfile, label: str) -> HealthFactor:
    name = "soil_ph"
    payload, reason = _usable(signals, "soil")
    if payload is None or payload.ph is None:
        return _factor(name, "unknown", None, reason or "no soil pH reading")
    value: float = payload.ph
    if value < profile.ph_stress_min:
        return _factor(
            name,
            "stress",
            value,
            f"soil pH {_fmt(value)} < {_fmt(profile.ph_stress_min)} ({label})",
        )
    if value > profile.ph_stress_max:
        return _factor(
            name,
            "stress",
            value,
            f"soil pH {_fmt(value)} > {_fmt(profile.ph_stress_max)} ({label})",
        )
    if value < profile.ph_attention_min:
        return _factor(
            name,
            "attention",
            value,
            f"soil pH {_fmt(value)} < {_fmt(profile.ph_attention_min)} ({label})",
        )
    if value > profile.ph_attention_max:
        return _factor(
            name,
            "attention",
            value,
            f"soil pH {_fmt(value)} > {_fmt(profile.ph_attention_max)} ({label})",
        )
    return _factor(
        name,
        "ok",
        value,
        (
            f"soil pH {_fmt(value)} in "
            f"{_fmt(profile.ph_attention_min)}-{_fmt(profile.ph_attention_max)} ({label})"
        ),
    )


def _nitrogen_factor(signals: NormalizedSignals, profile: CropProfile, label: str) -> HealthFactor:
    name = "nitrogen"
    payload, reason = _usable(signals, "soil")
    if payload is None or payload.nitrogen_kg_ha is None:
        return _factor(name, "unknown", None, reason or "no nitrogen reading")
    value: float = payload.nitrogen_kg_ha
    if value < profile.nitrogen_stress_min:
        return _factor(
            name,
            "stress",
            value,
            f"nitrogen {_fmt(value)} kg/ha < {_fmt(profile.nitrogen_stress_min)} ({label})",
        )
    if value < profile.nitrogen_attention_min:
        return _factor(
            name,
            "attention",
            value,
            f"nitrogen {_fmt(value)} kg/ha < {_fmt(profile.nitrogen_attention_min)} ({label})",
        )
    return _factor(
        name,
        "ok",
        value,
        f"nitrogen {_fmt(value)} kg/ha >= {_fmt(profile.nitrogen_attention_min)} ({label})",
    )


def _temperature_factor(signals: NormalizedSignals) -> HealthFactor:
    name = "air_temperature"
    payload, reason = _usable(signals, "weather")
    if payload is None or payload.temperature_c is None:
        return _factor(name, "unknown", None, reason or "no air temperature reading")
    value: float = payload.temperature_c
    cold, hot = TEMPERATURE_STRESS
    if value < cold:
        return _factor(name, "stress", value, f"air temperature {_fmt(value)}C < {_fmt(cold)}C")
    if value > hot:
        return _factor(name, "stress", value, f"air temperature {_fmt(value)}C > {_fmt(hot)}C")
    low, high = TEMPERATURE_ATTENTION
    if value < low:
        return _factor(name, "attention", value, f"air temperature {_fmt(value)}C < {_fmt(low)}C")
    if value > high:
        return _factor(name, "attention", value, f"air temperature {_fmt(value)}C > {_fmt(high)}C")
    return _factor(
        name, "ok", value, f"air temperature {_fmt(value)}C in {_fmt(low)}-{_fmt(high)}C"
    )


def _rainfall_factor(signals: NormalizedSignals) -> HealthFactor:
    name = "rainfall"
    payload, reason = _usable(signals, "weather")
    if payload is None:
        return _factor(name, "unknown", None, reason or "no weather signal")
    if payload.rainfall_mm is None:
        return _factor(name, "unknown", None, "no rainfall reading")
    if payload.rainfall_mm_per_day is None:
        return _factor(name, "unknown", None, "rainfall window unknown for this source")
    value: float = payload.rainfall_mm_per_day
    if value > RAINFALL_STRESS_MM_PER_DAY:
        return _factor(
            name,
            "stress",
            value,
            f"rainfall {_fmt(value)} mm/day > {_fmt(RAINFALL_STRESS_MM_PER_DAY)}",
        )
    if value > RAINFALL_ATTENTION_MM_PER_DAY:
        return _factor(
            name,
            "attention",
            value,
            f"rainfall {_fmt(value)} mm/day > {_fmt(RAINFALL_ATTENTION_MM_PER_DAY)}",
        )
    return _factor(
        name, "ok", value, f"rainfall {_fmt(value)} mm/day <= {_fmt(RAINFALL_ATTENTION_MM_PER_DAY)}"
    )


def _aggregate(factors: list[HealthFactor]) -> str:
    """Planting gates the verdict, then the worst signal factor decides.

    Nothing growing (no crop state, future planting date) means there is
    no health to report, and planting alone never proves health: with
    every signal family missing the level is ``unknown``, not
    ``healthy``.
    """
    planting, *signal_factors = factors
    if planting.status != "ok":
        return "unknown"
    statuses = {factor.status for factor in signal_factors}
    if "stress" in statuses:
        return "stressed"
    if "attention" in statuses:
        return "watch"
    if "ok" in statuses:
        return "healthy"
    return "unknown"


def assess_plot_health(
    plot: PlotStateView,
    signals: NormalizedSignals,
    *,
    now: datetime | None = None,
) -> PlotHealth:
    """Rule-evaluate one plot against the farm's normalized signals."""
    moment = now or datetime.now(UTC)
    profile = crop_profile_for(plot.crop)
    label = crop_label_for(plot.crop)
    factors = [
        _planting_factor(plot, moment),
        _ndvi_factor(signals, profile, label),
        _moisture_factor(signals, profile, label),
        _ph_factor(signals, profile, label),
        _nitrogen_factor(signals, profile, label),
        _temperature_factor(signals),
        _rainfall_factor(signals),
    ]
    return PlotHealth(
        plot_id=plot.plot_id,
        name=plot.name,
        crop=plot.crop,
        growth_stage=plot.growth_stage,
        days_since_planted=plot.days_since_planted,
        level=_aggregate(factors),
        factors=factors,
        factors_evaluated=sum(1 for factor in factors if factor.status != "unknown"),
        factor_count=len(factors),
        computed_at=moment,
    )


def _stale_families(signals: NormalizedSignals) -> list[str]:
    stale = []
    for family, threshold in STALE_AFTER_SECONDS.items():
        payload = getattr(signals, family)
        age = None if payload is None else payload.age_seconds
        if age is not None and age > threshold:
            stale.append(family)
    return sorted(stale)


def assess_farm_health(
    state: NormalizedFarmState,
    *,
    now: datetime | None = None,
) -> FarmHealth:
    """Assess every plot and roll the worst level up to the farm."""
    moment = now or datetime.now(UTC)
    plots = [assess_plot_health(plot, state.signals, now=moment) for plot in state.view.plots]
    levels = {plot.level for plot in plots}
    if "stressed" in levels:
        level = "stressed"
    elif "watch" in levels:
        level = "watch"
    elif "healthy" in levels:
        level = "healthy"
    else:
        level = "unknown"
    return FarmHealth(
        farm_id=state.view.farm_id,
        level=level,
        plots=plots,
        plot_count=len(plots),
        stale_families=_stale_families(state.signals),
        computed_at=moment,
    )


__all__ = [
    "CROP_PROFILES",
    "DEFAULT_CROP_PROFILE",
    "FACTOR_NAMES",
    "FACTOR_STATUSES",
    "CropProfile",
    "FarmHealth",
    "HEALTH_LEVELS",
    "HealthFactor",
    "PlotHealth",
    "STALE_AFTER_SECONDS",
    "assess_farm_health",
    "assess_plot_health",
    "crop_label_for",
    "crop_profile_for",
]
