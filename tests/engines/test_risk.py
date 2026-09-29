"""Farm risk engine tests (M033): pure unit coverage of the tally.

Builders mirror `test_health.py` (raw docs → M031 normalizer → M032
health → M033 risk) so the whole engine pipeline is exercised without
a database — no `_db` fixture.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from src.engines import (
    HAZARD_FACTORS,
    RISK_BANDS,
    RISK_ORDER,
    SEVERITY_POINTS,
    assess_farm_health,
    assess_farm_risk,
    risk_band,
)
from src.engines.health import assess_plot_health
from src.services.farm_state import FarmStateView, PlotStateView, SignalCacheView
from src.services.normalize import NormalizedFarmState, NormalizedSignals, normalize_signals

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
    plots: list[PlotStateView],
    *,
    farm_id: uuid.UUID = FARM_ID,
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
        farm_id=farm_id,
        farmer_id=uuid.uuid4(),
        name="Demo Farm",
        plots=plots,
        plot_count=len(plots),
        planted_plot_count=sum(1 for plot in plots if plot.crop is not None),
        crops=sorted({plot.crop for plot in plots if plot.crop is not None}),
        signals=SignalCacheView(signals=doc, refreshed_at=OBSERVED, age_seconds=3600),
    )
    return NormalizedFarmState(
        view=view,
        signals=normalize_signals(doc, now=NOW, refreshed_at=OBSERVED),
    )


def _risk(state: NormalizedFarmState, *, now: datetime = NOW):
    health = assess_farm_health(state, now=now)
    return assess_farm_risk(state, health, now=now)


def _item(risk, name: str):
    return next(item for item in risk.items if item.name == name)


def test_fresh_farm_scores_zero() -> None:
    risk = _risk(_state([_plot("Maize")]))
    assert risk.farm_id == FARM_ID
    assert risk.score == 0
    assert risk.band == "low"
    assert risk.items == []
    assert risk.hazard_readings_evaluated == len(HAZARD_FACTORS)
    assert risk.hazard_readings_total == len(HAZARD_FACTORS)
    assert risk.plot_count == 1
    assert risk.computed_at == NOW


@pytest.mark.parametrize(
    ("value", "expected_points", "expected_band"),
    [(28.0, SEVERITY_POINTS["attention"], "low"), (18.0, SEVERITY_POINTS["stress"], "moderate")],
)
def test_drought_scales_with_severity(
    value: float, expected_points: int, expected_band: str
) -> None:
    state = _state([_plot("Maize")], soil={**SOIL, "soil_moisture_pct": value})
    risk = _risk(state)
    assert [item.name for item in risk.items] == ["drought"]
    assert risk.items[0].points == expected_points
    assert risk.band == expected_band
    assert risk.score == expected_points


def test_drought_detail_is_m032s_evidence() -> None:
    state = _state([_plot("Maize")], soil={**SOIL, "soil_moisture_pct": 18.0})
    risk = _risk(state)
    assert _item(risk, "drought").detail == "soil moisture 18.0% < 25.0% (maize)"


def test_waterlogging_is_not_drought() -> None:
    state = _state([_plot("Maize")], soil={**SOIL, "soil_moisture_pct": 90.0})
    risk = _risk(state)
    assert [item.name for item in risk.items] == ["waterlogging"]
    assert risk.items[0].points == SEVERITY_POINTS["stress"]
    assert risk.band == "moderate"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(42.0, "heat"), (8.0, "cold")],
)
def test_temperature_direction(value: float, expected: str) -> None:
    state = _state([_plot("Maize")], weather={**WEATHER, "temperature_c": value})
    risk = _risk(state)
    assert [item.name for item in risk.items] == [expected]


def test_heavy_rain_risk() -> None:
    state = _state([_plot("Maize")], weather={**WEATHER, "rainfall_mm_24h": 70.0})
    risk = _risk(state)
    assert [item.name for item in risk.items] == ["heavy_rain"]
    assert risk.items[0].points == SEVERITY_POINTS["stress"]
    assert "70.0 mm/day" in risk.items[0].detail


def test_remaining_hazards_map_from_health_factors() -> None:
    state = _state(
        [_plot("Maize")],
        satellite={**SATELLITE, "ndvi": 0.20},
        soil={**SOIL, "ph": 4.9, "nitrogen_kg_ha": 15.0},
    )
    risk = _risk(state)
    assert [item.name for item in risk.items] == [
        "nutrient_shortfall",
        "soil_ph",
        "low_vigor",
    ]
    assert all(item.points == SEVERITY_POINTS["stress"] for item in risk.items)
    assert _item(risk, "low_vigor").detail.startswith("ndvi 0.20 < 0.25")


def test_worst_severity_across_plots_wins() -> None:
    state = _state(
        [_plot("Maize"), _plot("Wheat", name="Plot B")],
        soil={**SOIL, "soil_moisture_pct": 18.0},
    )
    wheat_state = _state([_plot("Wheat")], soil={**SOIL, "soil_moisture_pct": 25.0})
    wheat_risk = _risk(wheat_state)
    assert [item.name for item in wheat_risk.items] == ["drought"]
    assert wheat_risk.items[0].points == SEVERITY_POINTS["attention"]

    risk = _risk(state)
    droughts = [item for item in risk.items if item.name == "drought"]
    assert len(droughts) == 1
    assert droughts[0].points == SEVERITY_POINTS["stress"]
    assert risk.score == SEVERITY_POINTS["stress"]


def test_missing_family_is_a_visibility_penalty() -> None:
    risk = _risk(_state([_plot("Maize")], soil=None))
    assert _item(risk, "missing_signals").points == 15
    assert _item(risk, "missing_signals").detail == "never ingested: soil"
    assert risk.score == 15
    assert risk.band == "low"
    assert risk.hazard_readings_evaluated == 3
    assert risk.hazard_readings_total == len(HAZARD_FACTORS)


def test_stale_family_costs_less_than_a_missing_one() -> None:
    stale_at = (NOW - timedelta(hours=25)).isoformat()
    risk = _risk(_state([_plot("Maize")], weather={**WEATHER, "observed_at": stale_at}))
    assert _item(risk, "stale_signals").points == 10
    assert _item(risk, "stale_signals").detail == "stale: weather"
    assert "missing_signals" not in [item.name for item in risk.items]
    assert risk.score == 10
    assert risk.band == "low"


def test_unregistered_plot_is_visible_risk() -> None:
    risk = _risk(_state([_plot("Maize"), _plot(None, name="Plot B")]))
    item = _item(risk, "unregistered_plots")
    assert item.points == 10
    assert item.detail == "1 of 2 plots have no crop state"
    assert risk.score == 10


def test_visibility_penalties_stack() -> None:
    state = _state(
        [_plot(None)],
        weather=None,
        satellite=None,
        soil=None,
    )
    risk = _risk(state)
    assert [item.name for item in risk.items] == ["unregistered_plots", "missing_signals"]
    assert _item(risk, "missing_signals").points == 45
    assert risk.score == 55
    assert risk.band == "moderate"


def test_score_is_capped_at_100() -> None:
    state = _state(
        [_plot("Maize")],
        satellite={
            **SATELLITE,
            "ndvi": 0.10,
            "observed_at": (NOW - timedelta(days=91)).isoformat(),
        },
        weather={**WEATHER, "temperature_c": 45.0, "rainfall_mm_24h": 90.0},
        soil={**SOIL, "soil_moisture_pct": 10.0, "ph": 4.0, "nitrogen_kg_ha": 5.0},
    )
    risk = _risk(state)
    assert risk.score == 100
    assert risk.band == "high"


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0, "low"), (24, "low"), (25, "moderate"), (59, "moderate"), (60, "high"), (100, "high")],
)
def test_bands(score: int, expected: str) -> None:
    assert risk_band(score) == expected
    assert expected in RISK_BANDS


def test_items_follow_the_documented_order_and_omit_zero_points() -> None:
    stale_at = (NOW - timedelta(days=91)).isoformat()
    state = _state(
        [_plot("Maize"), _plot(None, name="Plot B")],
        weather={**WEATHER, "temperature_c": 45.0},
        satellite={**SATELLITE, "observed_at": stale_at},
        soil={**SOIL, "soil_moisture_pct": 90.0},
    )
    risk = _risk(state)
    names = [item.name for item in risk.items]
    assert names == [name for name in RISK_ORDER if name in names]
    assert set(names) == {"heat", "waterlogging", "stale_signals", "unregistered_plots"}
    assert all(item.points > 0 for item in risk.items)


def test_assessment_is_deterministic() -> None:
    state = _state([_plot("Maize")])
    assert _risk(state) == _risk(state)


def test_no_clock_is_read_when_now_is_given() -> None:
    risk = _risk(_state([_plot("Maize")]))
    assert risk.computed_at == NOW


def test_health_for_another_farm_is_rejected() -> None:
    state = _state([_plot("Maize")])
    other = _state([_plot("Maize")], farm_id=uuid.uuid4())
    health = assess_farm_health(other, now=NOW)
    with pytest.raises(ValueError, match="health is for farm"):
        assess_farm_risk(state, health, now=NOW)


def test_severity_points_are_documented() -> None:
    assert SEVERITY_POINTS == {"attention": 15, "stress": 30}


def test_plot_without_signals_contributes_no_hazard_readings() -> None:
    empty: NormalizedSignals = normalize_signals({}, now=NOW)
    plot = assess_plot_health(_plot("Maize"), empty, now=NOW)
    assert all(
        factor.status == "unknown" for factor in plot.factors if factor.name in HAZARD_FACTORS
    )
    assert plot.factors_evaluated == 1
