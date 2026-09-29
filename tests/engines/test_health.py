"""Crop health engine tests (M032): pure unit coverage of the rules.

Inputs are raw signals docs run through M031's normalizer (the engine
never sees raw documents), so these tests double as the M031→M032
seam. No database access — no `_db` fixture.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from src.engines import (
    CROP_PROFILES,
    DEFAULT_CROP_PROFILE,
    FACTOR_NAMES,
    HEALTH_LEVELS,
    STALE_AFTER_SECONDS,
    assess_farm_health,
    assess_plot_health,
)
from src.services.farm_state import FarmStateView, PlotStateView, SignalCacheView
from src.services.normalize import NormalizedFarmState, NormalizedSignals, normalize_signals

NOW = datetime(2026, 9, 29, 12, 0, 0, tzinfo=UTC)
OBSERVED = datetime(2026, 9, 29, 11, 0, 0, tzinfo=UTC)  # 1 h old — fresh for every family
PLANTED_ON = date(2026, 9, 1)
FARM_ID = uuid.UUID("00000000-0000-0000-0000-00000000f00d")

WEATHER = {
    "temperature_c": 22.0,
    "humidity_pct": 55.0,
    "rainfall_mm_24h": 5.0,
    "wind_speed_kmh": 10.0,
    "condition": "clear",
    "observed_at": OBSERVED.isoformat(),
    "source": "demo-weather-v1",
}
SATELLITE = {
    "ndvi": 0.62,
    "cloud_cover_pct": 10.0,
    "observed_at": OBSERVED.isoformat(),
    "source": "demo-satellite-v1",
}
SOIL = {
    "soil_moisture_pct": 45.0,
    "ph": 6.5,
    "soil_temperature_c": 18.0,
    "nitrogen_kg_ha": 60.0,
    "observed_at": OBSERVED.isoformat(),
    "source": "demo-soil-v1",
}


def _signals(
    weather: dict | None = WEATHER,
    satellite: dict | None = SATELLITE,
    soil: dict | None = SOIL,
) -> NormalizedSignals:
    doc: dict = {}
    if weather is not None:
        doc["weather"] = weather
    if satellite is not None:
        doc["satellite"] = satellite
    if soil is not None:
        doc["soil"] = soil
    return normalize_signals(doc, now=NOW, refreshed_at=NOW - timedelta(hours=1))


def _plot(
    crop: str | None = "Maize",
    *,
    plot_id: uuid.UUID | None = None,
    name: str = "Plot A",
    planted_on: date | None = PLANTED_ON,
    growth_stage: str | None = "vegetative",
) -> PlotStateView:
    days = None if planted_on is None else (NOW.date() - planted_on).days
    return PlotStateView(
        plot_id=plot_id or uuid.uuid4(),
        name=name,
        area_hectares=None,
        crop=crop,
        growth_stage=growth_stage,
        planted_on=planted_on,
        days_since_planted=days,
    )


def _state(
    plots: list[PlotStateView],
    *,
    weather: dict | None = WEATHER,
    satellite: dict | None = SATELLITE,
    soil: dict | None = SOIL,
) -> NormalizedFarmState:
    doc: dict = {}
    if weather is not None:
        doc["weather"] = weather
    if satellite is not None:
        doc["satellite"] = satellite
    if soil is not None:
        doc["soil"] = soil
    view = FarmStateView(
        farm_id=FARM_ID,
        farmer_id=uuid.uuid4(),
        name="Demo Farm",
        plots=plots,
        plot_count=len(plots),
        planted_plot_count=sum(1 for plot in plots if plot.crop is not None),
        crops=sorted({plot.crop for plot in plots if plot.crop is not None}),
        signals=SignalCacheView(
            signals=doc, refreshed_at=NOW - timedelta(hours=1), age_seconds=3600
        ),
    )
    return NormalizedFarmState(
        view=view,
        signals=normalize_signals(doc, now=NOW, refreshed_at=NOW - timedelta(hours=1)),
    )


def _factor(result, name: str):
    return next(factor for factor in result.factors if factor.name == name)


def test_fresh_maize_plot_is_healthy_with_all_seven_factors() -> None:
    health = assess_plot_health(_plot("Maize"), _signals(), now=NOW)
    assert health.level == "healthy"
    assert health.level in HEALTH_LEVELS
    assert [factor.name for factor in health.factors] == list(FACTOR_NAMES)
    assert all(factor.status == "ok" for factor in health.factors)
    assert health.factors_evaluated == 7
    assert health.factor_count == 7
    assert health.computed_at == NOW
    assert health.crop == "Maize"
    assert health.growth_stage == "vegetative"
    assert health.days_since_planted == (NOW.date() - PLANTED_ON).days
    assert _factor(health, "planting").detail.startswith("planted 2026-09-01 (vegetative, day")
    assert _factor(health, "ndvi").measured == 0.62


def test_ndvi_attention_puts_the_plot_on_watch() -> None:
    health = assess_plot_health(
        _plot("Maize"), _signals(satellite={**SATELLITE, "ndvi": 0.35}), now=NOW
    )
    assert health.level == "watch"
    ndvi = _factor(health, "ndvi")
    assert ndvi.status == "attention"
    assert ndvi.measured == 0.35
    assert "0.40" in ndvi.detail
    assert "maize" in ndvi.detail
    assert health.factors_evaluated == 7


def test_ndvi_below_stress_threshold_is_stressed() -> None:
    health = assess_plot_health(
        _plot("Maize"), _signals(satellite={**SATELLITE, "ndvi": 0.20}), now=NOW
    )
    assert health.level == "stressed"
    assert _factor(health, "ndvi").status == "stress"
    assert "0.25" in _factor(health, "ndvi").detail


def test_worst_factor_wins_over_attention() -> None:
    health = assess_plot_health(
        _plot("Maize"),
        _signals(soil={**SOIL, "soil_moisture_pct": 18.0, "nitrogen_kg_ha": 35.0}),
        now=NOW,
    )
    assert _factor(health, "soil_moisture").status == "stress"
    assert _factor(health, "nitrogen").status == "attention"
    assert health.level == "stressed"


def test_crop_registered_but_no_signals_is_unknown() -> None:
    health = assess_plot_health(_plot("Maize"), _signals(None, None, None), now=NOW)
    assert health.level == "unknown"
    assert health.factors_evaluated == 1
    assert _factor(health, "planting").status == "ok"
    assert _factor(health, "ndvi").detail == "no satellite signal"
    assert _factor(health, "soil_moisture").detail == "no soil signal"
    assert _factor(health, "air_temperature").detail == "no weather signal"


def test_no_crop_registered_never_reports_health() -> None:
    health = assess_plot_health(_plot(None), _signals(), now=NOW)
    assert health.level == "unknown"
    assert health.crop is None
    planting = _factor(health, "planting")
    assert planting.status == "unknown"
    assert planting.detail == "no crop registered for this plot"
    assert health.factors_evaluated == 6


def test_future_planting_date_never_reports_health() -> None:
    health = assess_plot_health(_plot("Maize", planted_on=date(2026, 11, 1)), _signals(), now=NOW)
    assert health.level == "unknown"
    planting = _factor(health, "planting")
    assert planting.status == "unknown"
    assert "2026-11-01 is in the future" in planting.detail
    assert health.days_since_planted is not None and health.days_since_planted < 0


def test_stale_satellite_is_not_judged_and_is_reported() -> None:
    stale_at = (NOW - timedelta(days=91)).isoformat()
    state = _state([_plot("Maize")], satellite={**SATELLITE, "observed_at": stale_at})
    farm = assess_farm_health(state, now=NOW)
    plot = farm.plots[0]
    ndvi = _factor(plot, "ndvi")
    assert ndvi.status == "unknown"
    assert ndvi.measured is None
    assert "stale" in ndvi.detail
    assert str(STALE_AFTER_SECONDS["satellite"]) in ndvi.detail
    assert farm.stale_families == ["satellite"]
    assert plot.level == "healthy"
    assert plot.factors_evaluated == 6


def test_fresh_satellite_threshold_is_not_16_days() -> None:
    thirteen_weeks = (NOW - timedelta(days=90) + timedelta(seconds=1)).isoformat()
    state = _state([_plot("Maize")], satellite={**SATELLITE, "observed_at": thirteen_weeks})
    farm = assess_farm_health(state, now=NOW)
    assert farm.stale_families == []
    assert _factor(farm.plots[0], "ndvi").status == "ok"


def test_stale_weather_knocks_out_only_its_own_factors() -> None:
    stale_at = (NOW - timedelta(hours=25)).isoformat()
    state = _state([_plot("Maize")], weather={**WEATHER, "observed_at": stale_at})
    farm = assess_farm_health(state, now=NOW)
    plot = farm.plots[0]
    assert _factor(plot, "air_temperature").status == "unknown"
    assert _factor(plot, "rainfall").status == "unknown"
    assert _factor(plot, "soil_moisture").status == "ok"
    assert farm.stale_families == ["weather"]


def test_missing_observation_time_is_unknown_but_not_stale() -> None:
    weather = {key: value for key, value in WEATHER.items() if key != "observed_at"}
    state = _state([_plot("Maize")], weather=weather)
    farm = assess_farm_health(state, now=NOW)
    assert farm.stale_families == []
    factor = _factor(farm.plots[0], "air_temperature")
    assert factor.status == "unknown"
    assert "no observation time" in factor.detail


def test_unknown_source_leaves_rainfall_window_unknown() -> None:
    health = assess_plot_health(
        _plot("Maize"),
        _signals(weather={**WEATHER, "source": "mystery-weather-v9"}),
        now=NOW,
    )
    rainfall = _factor(health, "rainfall")
    assert rainfall.status == "unknown"
    assert rainfall.detail == "rainfall window unknown for this source"
    assert _factor(health, "air_temperature").status == "ok"
    assert health.level == "healthy"


def test_missing_payload_values_are_unknown_not_zero() -> None:
    health = assess_plot_health(
        _plot("Maize"),
        _signals(
            weather={**WEATHER, "temperature_c": None, "rainfall_mm_24h": None},
            soil={**SOIL, "ph": None},
        ),
        now=NOW,
    )
    assert _factor(health, "air_temperature").detail == "no air temperature reading"
    assert _factor(health, "rainfall").detail == "no rainfall reading"
    assert _factor(health, "soil_ph").detail == "no soil pH reading"
    assert _factor(health, "soil_ph").measured is None
    assert health.level == "healthy"
    assert health.factors_evaluated == 4


@pytest.mark.parametrize(
    ("value", "status", "needle"),
    [
        (18.0, "stress", "< 25.0%"),
        (28.0, "attention", "< 35.0%"),
        (75.0, "attention", "> 70.0%"),
        (90.0, "stress", "> 85.0%"),
    ],
)
def test_soil_moisture_bounds(value: float, status: str, needle: str) -> None:
    health = assess_plot_health(
        _plot("Maize"), _signals(soil={**SOIL, "soil_moisture_pct": value}), now=NOW
    )
    factor = _factor(health, "soil_moisture")
    assert factor.status == status
    assert needle in factor.detail


@pytest.mark.parametrize(
    ("value", "status", "needle"),
    [(5.6, "attention", "< 5.8"), (4.9, "stress", "< 5.0"), (7.5, "attention", "> 7.2")],
)
def test_soil_ph_bounds(value: float, status: str, needle: str) -> None:
    health = assess_plot_health(_plot("Maize"), _signals(soil={**SOIL, "ph": value}), now=NOW)
    factor = _factor(health, "soil_ph")
    assert factor.status == status
    assert needle in factor.detail


@pytest.mark.parametrize(
    ("value", "status", "needle"),
    [(35.0, "attention", "< 50.0"), (15.0, "stress", "< 20.0")],
)
def test_nitrogen_bounds_for_maize(value: float, status: str, needle: str) -> None:
    health = assess_plot_health(
        _plot("Maize"), _signals(soil={**SOIL, "nitrogen_kg_ha": value}), now=NOW
    )
    factor = _factor(health, "nitrogen")
    assert factor.status == status
    assert needle in factor.detail


@pytest.mark.parametrize(
    ("value", "status", "needle"),
    [
        (42.0, "stress", "> 40.0C"),
        (8.0, "attention", "< 10.0C"),
        (-3.0, "stress", "< 5.0C"),
    ],
)
def test_air_temperature_bounds(value: float, status: str, needle: str) -> None:
    health = assess_plot_health(
        _plot("Maize"), _signals(weather={**WEATHER, "temperature_c": value}), now=NOW
    )
    factor = _factor(health, "air_temperature")
    assert factor.status == status
    assert needle in factor.detail


@pytest.mark.parametrize(
    ("value", "status", "needle"),
    [(45.0, "attention", "> 30.0"), (70.0, "stress", "> 60.0"), (5.0, "ok", "<= 30.0")],
)
def test_rainfall_bounds_per_day(value: float, status: str, needle: str) -> None:
    health = assess_plot_health(
        _plot("Maize"), _signals(weather={**WEATHER, "rainfall_mm_24h": value}), now=NOW
    )
    factor = _factor(health, "rainfall")
    assert factor.status == status
    assert needle in factor.detail


def test_rainfall_is_scaled_by_the_source_window() -> None:
    hourly = assess_plot_health(
        _plot("Maize"),
        _signals(weather={**WEATHER, "source": "open-meteo-v1", "rainfall_mm_24h": 2.0}),
        now=NOW,
    )
    factor = _factor(hourly, "rainfall")
    assert factor.measured == 48.0
    assert factor.status == "attention"


def test_crop_profiles_disagree_on_the_same_signals() -> None:
    signals = _signals(soil={**SOIL, "nitrogen_kg_ha": 45.0})
    maize = assess_plot_health(_plot("Maize"), signals, now=NOW)
    wheat = assess_plot_health(_plot("Wheat"), signals, now=NOW)
    beans = assess_plot_health(_plot("Beans"), signals, now=NOW)
    assert maize.level == "watch"
    assert _factor(maize, "nitrogen").status == "attention"
    assert wheat.level == "healthy"
    assert beans.level == "healthy"


def test_unknown_crop_falls_back_to_the_default_profile() -> None:
    assert "sorghum" not in CROP_PROFILES
    signals = _signals(soil={**SOIL, "nitrogen_kg_ha": 45.0})
    sorghum = assess_plot_health(_plot("Sorghum"), signals, now=NOW)
    assert sorghum.level == "healthy"
    assert CROP_PROFILES.get("sorghum", DEFAULT_CROP_PROFILE) is DEFAULT_CROP_PROFILE


def test_crop_lookup_is_case_insensitive() -> None:
    signals = _signals(soil={**SOIL, "nitrogen_kg_ha": 45.0})
    assert assess_plot_health(_plot("MAIZE"), signals, now=NOW).level == "watch"
    assert assess_plot_health(_plot("Maize"), signals, now=NOW).level == "watch"


def test_farm_level_is_the_worst_plot() -> None:
    plots = [
        _plot("Maize", plot_id=uuid.uuid4(), name="A"),
        _plot("Wheat", plot_id=uuid.uuid4(), name="B"),
    ]
    state = _state(plots, soil={**SOIL, "nitrogen_kg_ha": 15.0})
    farm = assess_farm_health(state, now=NOW)
    assert farm.farm_id == FARM_ID
    assert farm.plot_count == 2
    assert farm.level == "stressed"
    assert [plot.name for plot in farm.plots] == ["A", "B"]
    assert all(plot.computed_at == NOW for plot in farm.plots)


def test_farm_with_no_plots_is_unknown() -> None:
    farm = assess_farm_health(_state([]), now=NOW)
    assert farm.level == "unknown"
    assert farm.plots == []
    assert farm.plot_count == 0


def test_stale_families_are_sorted_and_reported_once() -> None:
    past_25h = (NOW - timedelta(hours=25)).isoformat()
    past_91d = (NOW - timedelta(days=91)).isoformat()
    state = _state(
        [_plot("Maize")],
        weather={**WEATHER, "observed_at": past_25h},
        satellite={**SATELLITE, "observed_at": past_91d},
    )
    farm = assess_farm_health(state, now=NOW)
    assert farm.stale_families == ["satellite", "weather"]
    assert _factor(farm.plots[0], "ndvi").status == "unknown"
    assert _factor(farm.plots[0], "air_temperature").status == "unknown"
    assert _factor(farm.plots[0], "soil_moisture").status == "ok"


def test_assessment_is_deterministic() -> None:
    state = _state([_plot("Maize")])
    assert assess_farm_health(state, now=NOW) == assess_farm_health(state, now=NOW)


def test_no_clock_is_read_when_now_is_given() -> None:
    health = assess_plot_health(_plot("Maize"), _signals(), now=NOW)
    assert health.computed_at == NOW


def test_every_level_is_in_the_documented_vocabulary() -> None:
    assert set(HEALTH_LEVELS) == {"healthy", "watch", "stressed", "unknown"}
    plots = [
        assess_plot_health(_plot("Maize"), _signals(), now=NOW),
        assess_plot_health(
            _plot("Maize"), _signals(satellite={**SATELLITE, "ndvi": 0.20}), now=NOW
        ),
        assess_plot_health(_plot(None), _signals(), now=NOW),
        assess_plot_health(_plot("Maize"), _signals(None, None, None), now=NOW),
    ]
    assert {plot.level for plot in plots} == {"healthy", "stressed", "unknown"}
