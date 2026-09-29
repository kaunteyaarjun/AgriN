"""What-if engine tests (M044): knob validity, the two-run contract,
the diff, and the freshness/provenance rules.

Pure unit: no DB, no network, clock injected — the same fixture style
as test_decision.py (raw docs through M031's normalizer).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from src.engines import WHAT_IF_KNOBS, WhatIfResult, run_analysis, simulate_what_if
from src.services.farm_state import FarmStateView, PlotStateView, SignalCacheView
from src.services.normalize import NormalizedFarmState, normalize_signals

NOW = datetime(2026, 9, 29, 12, 0, 0, tzinfo=UTC)
OBSERVED = datetime(2026, 9, 29, 11, 0, 0, tzinfo=UTC)
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
SOIL_DRY = {**SOIL, "soil_moisture_pct": 10.0}
WEATHER_STALE = {**WEATHER, "observed_at": (NOW - timedelta(days=2)).isoformat()}


def _plot(crop: str | None = "Maize", *, name: str = "Plot A") -> PlotStateView:
    return PlotStateView(
        plot_id=uuid.uuid4(),
        name=name,
        area_hectares=None,
        crop=crop,
        growth_stage="vegetative",
        planted_on=PLANTED_ON,
        days_since_planted=(NOW.date() - PLANTED_ON).days,
    )


def _state(
    plots: list[PlotStateView] | None = None,
    *,
    soil: dict | None = SOIL,
    weather: dict | None = WEATHER,
    satellite: dict | None = SATELLITE,
    signals: dict | None = None,
) -> NormalizedFarmState:
    plots = [_plot("Maize")] if plots is None else plots
    if signals is None:
        signals = {}
        if weather is not None:
            signals["weather"] = weather
        if satellite is not None:
            signals["satellite"] = satellite
        if soil is not None:
            signals["soil"] = soil
    view = FarmStateView(
        farm_id=FARM_ID,
        farmer_id=uuid.uuid4(),
        name="WhatIf Farm",
        plots=plots,
        plot_count=len(plots),
        planted_plot_count=sum(1 for plot in plots if plot.crop is not None),
        crops=sorted({plot.crop for plot in plots if plot.crop is not None}),
        signals=SignalCacheView(signals=signals, refreshed_at=OBSERVED, age_seconds=3600),
    )
    return NormalizedFarmState(
        view=view,
        signals=normalize_signals(signals, now=NOW, refreshed_at=OBSERVED),
    )


def _moved(result: WhatIfResult) -> bool:
    changes = result.changes
    return bool(
        changes.stance is not None
        or changes.health_level is not None
        or changes.risk_score_delta != 0
        or changes.risk_band is not None
        or any(changes.action_counts_delta.values())
        or changes.actions_added
        or changes.actions_removed
    )


# ---------- two-run contract ----------


def test_simulation_is_deterministic_and_its_baseline_is_run_analysis() -> None:
    state = _state()
    overrides = {"soil": {"soil_moisture_pct": 10.0}}

    first = simulate_what_if(state, overrides, now=NOW)
    second = simulate_what_if(state, overrides, now=NOW)
    assert first == second  # pure: same inputs -> same result
    assert first.baseline == run_analysis(state, now=NOW)


def test_one_clock_serves_both_runs() -> None:
    result = simulate_what_if(_state(), {"soil": {"soil_moisture_pct": 10.0}}, now=NOW)
    for analysis in (result.baseline, result.hypothetical):
        assert analysis.health.computed_at == NOW
        assert analysis.risk.computed_at == NOW
        assert analysis.recommendations.computed_at == NOW
        assert analysis.decision.computed_at == NOW
    assert result.baseline.decision.farm_id == FARM_ID
    assert result.hypothetical.state.view.farm_id == FARM_ID


def test_echoes_the_applied_overrides() -> None:
    result = simulate_what_if(
        _state(),
        {"soil": {"ph": 7.9}, "weather": {"temperature_c": 41}},
        now=NOW,
    )
    assert result.overrides_applied == {
        "soil": {"ph": 7.9},
        "weather": {"temperature_c": 41.0},  # ints normalize to float
    }
    assert result.simulated_families == ["soil", "weather"]  # sorted


# ---------- every knob must be able to move the answer ----------


@pytest.mark.parametrize(
    ("family", "field", "value"),
    [
        ("weather", "temperature_c", 45.0),
        ("weather", "rainfall_mm_24h", 0.0),
        ("soil", "soil_moisture_pct", 10.0),
        ("soil", "ph", 4.0),
        ("soil", "nitrogen_kg_ha", 1.0),
        ("satellite", "ndvi", 0.15),
    ],
)
def test_every_catalogued_knob_moves_the_answer(family: str, field: str, value: float) -> None:
    assert (family, field) in WHAT_IF_KNOBS  # the knob is catalogue-backed
    result = simulate_what_if(_state(), {family: {field: value}}, now=NOW)
    assert _moved(result), f"{family}.{field} changed nothing"


def test_a_knob_set_to_its_current_value_is_an_all_zero_diff() -> None:
    result = simulate_what_if(_state(), {"soil": {"soil_moisture_pct": 45.0}}, now=NOW)
    changes = result.changes
    assert changes.stance is None
    assert changes.health_level is None
    assert changes.risk_score_delta == 0
    assert changes.risk_band is None
    assert all(delta == 0 for delta in changes.action_counts_delta.values())
    assert changes.actions_added == []
    assert changes.actions_removed == []
    assert _moved(result) is False


def test_irrigating_a_dry_farm_drops_the_urgent_action() -> None:
    result = simulate_what_if(_state(soil=SOIL_DRY), {"soil": {"soil_moisture_pct": 45.0}}, now=NOW)
    changes = result.changes
    assert result.baseline.decision.stance == "act_now"
    assert changes.stance is not None  # the stance moved
    assert changes.action_counts_delta["urgent"] < 0
    assert changes.actions_removed
    assert all(action.priority == "urgent" for action in changes.actions_removed)


# ---------- freshness and provenance ----------


def test_a_pre_existing_family_keeps_its_source_and_is_restamped() -> None:
    result = simulate_what_if(_state(), {"weather": {"temperature_c": 36.0}}, now=NOW)
    weather = result.hypothetical.state.signals.weather
    assert weather is not None
    assert weather.source == "demo-weather-v1"  # provenance kept
    assert weather.observed_at == NOW  # re-stamped: a hypothetical is about now
    assert result.simulated_families == ["weather"]


def test_a_missing_family_is_materialized_without_invented_provenance() -> None:
    state = _state(soil=None)
    result = simulate_what_if(state, {"soil": {"soil_moisture_pct": 12.0}}, now=NOW)
    soil = result.hypothetical.state.signals.soil
    assert soil is not None
    assert soil.source is None  # never invent a source string
    assert soil.soil_moisture_pct == 12.0
    assert soil.observed_at == NOW
    assert result.simulated_families == ["soil"]


def test_restamping_clears_staleness_and_the_points_behind_it() -> None:
    stale_at = NOW - timedelta(days=2)
    state = _state(weather=WEATHER_STALE)
    assert state.signals.weather is not None
    assert state.signals.weather.age_seconds == int((NOW - stale_at).total_seconds())

    result = simulate_what_if(state, {"weather": {"temperature_c": 22.0}}, now=NOW)

    assert "weather" in result.baseline.decision.stale_families
    assert "weather" not in result.hypothetical.decision.stale_families
    assert result.changes.risk_score_delta < 0  # staleness points removed
    assert result.simulated_families == ["weather"]


# ---------- validation ----------


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({}, "no what-if overrides"),
        ({"rain": {"mm": 1.0}}, "unknown what-if family: 'rain'"),
        ({"weather": {"dew_point_c": 5.0}}, "unknown what-if knob: weather.dew_point_c"),
        ({"soil": {"ph": "6.5"}}, "weather" if False else "must be a number"),
        ({"soil": {"ph": True}}, "must be a number, got bool"),
        ({"soil": {"ph": 20.0}}, "outside the allowed range"),
        ({"satellite": {"ndvi": 2.0}}, "outside the allowed range"),
        ({"weather": {"temperature_c": 100.0}}, "outside the allowed range"),
        ({"soil": {"soil_moisture_pct": -5.0}}, "outside the allowed range"),
        ({"weather": {"rainfall_mm_24h": -1.0}}, "outside the allowed range"),
    ],
)
def test_invalid_overrides_raise_value_error(overrides: dict, fragment: str) -> None:
    with pytest.raises(ValueError, match=None) as excinfo:
        simulate_what_if(_state(), overrides, now=NOW)
    assert fragment in str(excinfo.value)


def test_malformed_family_cannot_be_simulated() -> None:
    state = _state(signals={"weather": "oops", "soil": SOIL, "satellite": SATELLITE})
    with pytest.raises(ValueError, match="malformed"):
        simulate_what_if(state, {"weather": {"temperature_c": 30.0}}, now=NOW)


def test_rainfall_needs_a_known_measurement_window() -> None:
    windowless = {"temperature_c": 22.0, "observed_at": OBSERVED.isoformat()}  # no source
    state = _state(weather=windowless)
    with pytest.raises(ValueError, match="measurement window"):
        simulate_what_if(state, {"weather": {"rainfall_mm_24h": 0.0}}, now=NOW)
