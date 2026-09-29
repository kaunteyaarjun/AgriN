"""Signal normalization layer (M031): raw cache document → canonical models.

The ingestion layer (M023/M026/M029) stores each provider family's
payload *as fetched* — raw units, raw timestamps, one key per family —
and M019's cache is the shared home for all of them. This module is the
single read-side place where those raw documents become canonical
before any engine looks at them:

- **Units** are coerced (JSONB numbers only) and checked against
  *physical* ranges; an impossible value is not data and becomes
  ``None``. Agronomic thresholds are decision logic and stay in M032+.
- **Timeframes** are converted through :data:`SOURCE_PROFILES`: a known
  ``source`` label tells us what the number's window means (hourly vs
  24-hour rainfall, single overpass vs 16-day NDVI composite). An
  unknown source converts to ``None`` — never a guess.
- **Provenance** survives: every family keeps its ``source``,
  ``observed_at`` and a policy-free ``age_seconds`` (staleness
  *thresholds* belong to the engines, per M019).

No database access, no I/O: callers pass the signals document (or the
:class:`~src.services.farm_state.FarmStateView`) they already have.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

from pydantic import BaseModel

from src.services.farm_state import FarmStateView

CANONICAL_CONDITIONS: Final[tuple[str, ...]] = (
    "clear",
    "partly_cloudy",
    "cloudy",
    "light_rain",
    "thunderstorm",
)

FAMILY_KEYS: Final[tuple[str, ...]] = ("weather", "satellite", "soil")

EARTH_TEMPERATURE_RANGE: Final[tuple[float | None, float | None]] = (-90.0, 60.0)
PERCENT_RANGE: Final[tuple[float | None, float | None]] = (0.0, 100.0)
NDVI_RANGE: Final[tuple[float | None, float | None]] = (-1.0, 1.0)
PH_RANGE: Final[tuple[float | None, float | None]] = (0.0, 14.0)


@dataclass(frozen=True)
class SourceProfile:
    """What a known source's numbers *mean* — timeframe facts only.

    Fields are ``None`` when the source has no such quantity (or the
    source is unknown, where every fact is ``None``: no conversion
    without knowing the window).
    """

    rainfall_window_hours: int | None = None
    ndvi_support_days: int | None = None


SOURCE_PROFILES: Final[dict[str, SourceProfile]] = {
    "demo-weather-v1": SourceProfile(rainfall_window_hours=24),
    "open-meteo-v1": SourceProfile(rainfall_window_hours=1),
    "demo-satellite-v1": SourceProfile(ndvi_support_days=1),
    "ornl-daac-modis-mod13q1": SourceProfile(ndvi_support_days=16),
    "demo-soil-v1": SourceProfile(),
}

UNKNOWN_SOURCE_PROFILE: Final[SourceProfile] = SourceProfile()


class NormalizedWeather(BaseModel):
    """Canonical weather family: deg C, %, km/h, rainfall with its window."""

    source: str | None
    observed_at: datetime | None
    age_seconds: int | None
    temperature_c: float | None
    humidity_pct: float | None
    rainfall_mm: float | None
    rainfall_window_hours: int | None
    rainfall_mm_per_day: float | None
    wind_speed_kmh: float | None
    condition: str | None


class NormalizedSatellite(BaseModel):
    """Canonical satellite family: unitless NDVI plus its temporal support."""

    source: str | None
    observed_at: datetime | None
    age_seconds: int | None
    ndvi: float | None
    ndvi_support_days: int | None
    cloud_cover_pct: float | None


class NormalizedSoil(BaseModel):
    """Canonical soil family: %, pH, deg C, kg/ha."""

    source: str | None
    observed_at: datetime | None
    age_seconds: int | None
    soil_moisture_pct: float | None
    ph: float | None
    soil_temperature_c: float | None
    nitrogen_kg_ha: float | None


class NormalizedSignals(BaseModel):
    """The whole cache document, normalized; absent family → ``None``."""

    weather: NormalizedWeather | None
    satellite: NormalizedSatellite | None
    soil: NormalizedSoil | None
    refreshed_at: datetime | None
    refreshed_age_seconds: int | None
    unknown_families: list[str]
    malformed_families: list[str]


class NormalizedFarmState(BaseModel):
    """Farm State view + its normalized signals: the engines' entry point."""

    view: FarmStateView
    signals: NormalizedSignals


def _timestamp(value: Any) -> datetime | None:
    """ISO-8601 text → aware UTC. Naive is assumed UTC; anything else is
    not a timestamp."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _age(moment: datetime, stamp: datetime | None) -> int | None:
    """Seconds from ``stamp`` to ``moment``; negative is allowed (clock
    skew is data, not an error) and a missing stamp has no age."""
    if stamp is None:
        return None
    return int((moment - stamp).total_seconds())


def _aware(value: datetime | None) -> datetime | None:
    """An aware UTC moment; a naive one is assumed UTC (documented)."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _number(value: Any, bounds: tuple[float | None, float | None]) -> float | None:
    """JSONB number inside its physical range, else ``None``."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    low, high = bounds
    if low is not None and number < low:
        return None
    if high is not None and number > high:
        return None
    return number


def _source(raw: Mapping[str, Any]) -> str | None:
    value = raw.get("source")
    if not isinstance(value, str) or not value:
        return None
    return value


def _base(
    raw: Mapping[str, Any], moment: datetime
) -> tuple[str | None, datetime | None, int | None]:
    source = _source(raw)
    observed_at = _timestamp(raw.get("observed_at"))
    return source, observed_at, _age(moment, observed_at)


def _weather_family(raw: Any, moment: datetime) -> NormalizedWeather | None:
    if not isinstance(raw, Mapping):
        return None
    source, observed_at, age = _base(raw, moment)
    profile = SOURCE_PROFILES.get(source or "", UNKNOWN_SOURCE_PROFILE)
    rainfall_mm = _number(raw.get("rainfall_mm_24h"), (0.0, None))
    window = profile.rainfall_window_hours
    condition = raw.get("condition")
    return NormalizedWeather(
        source=source,
        observed_at=observed_at,
        age_seconds=age,
        temperature_c=_number(raw.get("temperature_c"), EARTH_TEMPERATURE_RANGE),
        humidity_pct=_number(raw.get("humidity_pct"), PERCENT_RANGE),
        rainfall_mm=rainfall_mm,
        rainfall_window_hours=window,
        rainfall_mm_per_day=(
            None if rainfall_mm is None or window is None else rainfall_mm * 24.0 / window
        ),
        wind_speed_kmh=_number(raw.get("wind_speed_kmh"), (0.0, None)),
        condition=condition if condition in CANONICAL_CONDITIONS else None,
    )


def _satellite_family(raw: Any, moment: datetime) -> NormalizedSatellite | None:
    if not isinstance(raw, Mapping):
        return None
    source, observed_at, age = _base(raw, moment)
    profile = SOURCE_PROFILES.get(source or "", UNKNOWN_SOURCE_PROFILE)
    return NormalizedSatellite(
        source=source,
        observed_at=observed_at,
        age_seconds=age,
        ndvi=_number(raw.get("ndvi"), NDVI_RANGE),
        ndvi_support_days=profile.ndvi_support_days,
        cloud_cover_pct=_number(raw.get("cloud_cover_pct"), PERCENT_RANGE),
    )


def _soil_family(raw: Any, moment: datetime) -> NormalizedSoil | None:
    if not isinstance(raw, Mapping):
        return None
    source, observed_at, age = _base(raw, moment)
    return NormalizedSoil(
        source=source,
        observed_at=observed_at,
        age_seconds=age,
        soil_moisture_pct=_number(raw.get("soil_moisture_pct"), PERCENT_RANGE),
        ph=_number(raw.get("ph"), PH_RANGE),
        soil_temperature_c=_number(raw.get("soil_temperature_c"), EARTH_TEMPERATURE_RANGE),
        nitrogen_kg_ha=_number(raw.get("nitrogen_kg_ha"), (0.0, None)),
    )


def normalize_signals(
    signals: Mapping[str, Any],
    *,
    now: datetime | None = None,
    refreshed_at: datetime | None = None,
) -> NormalizedSignals:
    """Normalize a raw signals document. Pure; no I/O.

    Family keys that are absent (or hold anything but a mapping) yield
    ``None``; unrecognized keys are reported sorted in
    ``unknown_families``, family keys holding a non-mapping in
    ``malformed_families``.
    """
    moment = now or datetime.now(UTC)
    unknown = sorted(key for key in signals if key not in FAMILY_KEYS)
    malformed = sorted(
        key for key in FAMILY_KEYS if key in signals and not isinstance(signals[key], Mapping)
    )
    stamp = _aware(refreshed_at)
    return NormalizedSignals(
        weather=_weather_family(signals.get("weather"), moment),
        satellite=_satellite_family(signals.get("satellite"), moment),
        soil=_soil_family(signals.get("soil"), moment),
        refreshed_at=stamp,
        refreshed_age_seconds=_age(moment, stamp),
        unknown_families=unknown,
        malformed_families=malformed,
    )


def normalize_farm_state(
    state: FarmStateView,
    *,
    now: datetime | None = None,
) -> NormalizedFarmState:
    """Bundle a Farm State view with its normalized signals (one call
    for the engines: plots from M019, signals from this layer)."""
    moment = now or datetime.now(UTC)
    return NormalizedFarmState(
        view=state,
        signals=normalize_signals(
            state.signals.signals, now=moment, refreshed_at=state.signals.refreshed_at
        ),
    )
