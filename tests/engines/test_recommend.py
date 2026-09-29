"""Recommendation engine tests (M034): pure unit coverage of the rules.

Builders mirror `test_risk.py` (raw docs → M031 normalizer → M032
health → M034 recommendations) so the whole pipeline is exercised
without a database — no `_db` fixture.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from src.engines import (
    RECOMMENDATION_CATEGORIES,
    RECOMMENDATION_ORDER,
    RECOMMENDATION_PRIORITY,
    RECOMMENDATION_SPECS,
    assess_farm_health,
    recommend_farm_actions,
)
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


def _recommend(state: NormalizedFarmState):
    return recommend_farm_actions(state, assess_farm_health(state, now=NOW), now=NOW)


def _codes(farm) -> list[str]:
    return [rec.code for rec in farm.recommendations]


def _get(farm, code: str):
    return next(rec for rec in farm.recommendations if rec.code == code)


def test_healthy_plot_gets_exactly_one_no_action_item() -> None:
    plot = _plot("Maize")
    farm = _recommend(_state([plot]))
    assert farm.farm_id == FARM_ID
    assert farm.plot_count == 1
    assert farm.computed_at == NOW
    assert _codes(farm) == ["continue_as_planned"]
    rec = farm.recommendations[0]
    assert rec.priority == "routine"
    assert rec.category == "monitoring"
    assert rec.plot_id == plot.plot_id
    assert rec.plot_name == "Plot A"
    assert farm.actionable == 0


@pytest.mark.parametrize(
    ("value", "expected_priority"),
    [(28.0, "soon"), (18.0, "urgent")],
)
def test_attention_is_soon_stress_is_urgent(value: float, expected_priority: str) -> None:
    farm = _recommend(_state([_plot("Maize")], soil={**SOIL, "soil_moisture_pct": value}))
    rec = _get(farm, "irrigate")
    assert rec.priority == expected_priority
    assert rec.priority in RECOMMENDATION_PRIORITY


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"soil": {**SOIL, "soil_moisture_pct": 18.0}}, "irrigate"),
        ({"soil": {**SOIL, "soil_moisture_pct": 90.0}}, "improve_drainage"),
        ({"soil": {**SOIL, "nitrogen_kg_ha": 15.0}}, "apply_nitrogen"),
        ({"soil": {**SOIL, "ph": 4.9}}, "raise_ph"),
        ({"soil": {**SOIL, "ph": 8.2}}, "lower_ph"),
        ({"weather": {**WEATHER, "temperature_c": 45.0}}, "heat_protection"),
        ({"weather": {**WEATHER, "temperature_c": 4.0}}, "frost_protection"),
        ({"weather": {**WEATHER, "rainfall_mm_24h": 90.0}}, "hold_field_work"),
        ({"satellite": {**SATELLITE, "ndvi": 0.20}}, "inspect_crop"),
    ],
)
def test_every_rule_row_fires(overrides: dict, expected_code: str) -> None:
    farm = _recommend(_state([_plot("Maize")], **overrides))
    rec = _get(farm, expected_code)
    assert rec.category in RECOMMENDATION_CATEGORIES
    assert rec.priority == "urgent"
    assert rec.plot_id is not None


def test_factor_detail_is_m032s_sentence() -> None:
    farm = _recommend(_state([_plot("Maize")], soil={**SOIL, "soil_moisture_pct": 18.0}))
    rec = _get(farm, "irrigate")
    assert rec.detail == "soil moisture 18.0% < 25.0% (maize)"
    assert rec.title == "Irrigate"


def test_unregistered_plot_only_gets_set_crop_plan() -> None:
    plot = _plot(None, name="Plot B")
    farm = _recommend(_state([plot]))
    assert _codes(farm) == ["set_crop_plan"]
    rec = farm.recommendations[0]
    assert rec.priority == "soon"
    assert rec.category == "record_keeping"
    assert rec.plot_id == plot.plot_id
    assert farm.actionable == 1


def test_stale_family_advises_refresh_but_never_reassures() -> None:
    stale_at = (NOW - timedelta(hours=25)).isoformat()
    farm = _recommend(_state([_plot("Maize")], weather={**WEATHER, "observed_at": stale_at}))
    assert "continue_as_planned" not in _codes(farm)
    rec = _get(farm, "refresh_signals")
    assert rec.priority == "soon"
    assert rec.plot_id is None and rec.plot_name is None
    assert rec.title == "Refresh weather signals"
    assert rec.detail == "weather signals are past the freshness window"


def test_missing_family_advises_ingestion_and_blocks_reassurance() -> None:
    farm = _recommend(_state([_plot("Maize")], soil=None))
    assert "continue_as_planned" not in _codes(farm)
    rec = _get(farm, "ingest_missing_signals")
    assert rec.priority == "soon"
    assert rec.plot_id is None
    assert rec.title == "Ingest missing soil signals"
    assert farm.actionable == 1


def test_one_plot_can_need_several_urgent_actions() -> None:
    farm = _recommend(
        _state(
            [_plot("Maize")],
            soil={**SOIL, "soil_moisture_pct": 18.0, "nitrogen_kg_ha": 15.0},
            weather={**WEATHER, "temperature_c": 45.0},
        )
    )
    assert _codes(farm) == ["irrigate", "apply_nitrogen", "heat_protection"]
    assert {rec.priority for rec in farm.recommendations} == {"urgent"}
    assert farm.actionable == 3


def test_sort_is_priority_then_code_then_name_and_is_deterministic() -> None:
    state = _state(
        [
            _plot("Maize", name="Plot B"),
            _plot("Wheat", name="Plot A"),
            _plot("Wheat", name="Plot C"),
        ],
        soil={**SOIL, "soil_moisture_pct": 32.0},
    )
    farm = _recommend(state)
    assert farm == _recommend(state)

    priorities = [rec.priority for rec in farm.recommendations]
    assert priorities == sorted(priorities, key=RECOMMENDATION_PRIORITY.index)
    assert _codes(farm) == [
        "irrigate",
        "continue_as_planned",
        "continue_as_planned",
    ]
    continues = [rec for rec in farm.recommendations if rec.code == "continue_as_planned"]
    assert [rec.plot_name for rec in continues] == ["Plot A", "Plot C"]
    assert farm.actionable == 1


def test_codes_categories_and_priorities_are_from_the_documented_tuples() -> None:
    assert set(RECOMMENDATION_ORDER) == set(RECOMMENDATION_SPECS)
    for code in RECOMMENDATION_ORDER:
        category, title = RECOMMENDATION_SPECS[code]
        assert category in RECOMMENDATION_CATEGORIES
        assert title

    farm = _recommend(
        _state(
            [_plot("Maize"), _plot(None, name="Plot B")],
            weather=None,
            satellite=None,
            soil=None,
        )
    )
    for rec in farm.recommendations:
        assert rec.code in RECOMMENDATION_ORDER
        assert rec.category in RECOMMENDATION_CATEGORIES
        assert rec.priority in RECOMMENDATION_PRIORITY


def test_farm_level_and_plot_level_items_coexist() -> None:
    farm = _recommend(_state([_plot("Maize"), _plot(None, name="Plot B")], soil=None))
    codes = _codes(farm)
    assert "ingest_missing_signals" in codes
    assert "set_crop_plan" in codes
    assert "continue_as_planned" not in codes
    farm_level = [rec for rec in farm.recommendations if rec.plot_id is None]
    plot_level = [rec for rec in farm.recommendations if rec.plot_id is not None]
    assert {rec.code for rec in farm_level} == {"ingest_missing_signals"}
    assert {rec.code for rec in plot_level} == {"set_crop_plan"}


def test_empty_farm_recommends_nothing() -> None:
    farm = _recommend(_state([]))
    assert farm.recommendations == []
    assert farm.actionable == 0
    assert farm.plot_count == 0
    assert farm.farm_id == FARM_ID


def test_health_for_another_farm_is_rejected() -> None:
    state = _state([_plot("Maize")])
    other = _state([_plot("Maize")], farm_id=uuid.uuid4())
    with pytest.raises(ValueError, match="health is for farm"):
        recommend_farm_actions(state, assess_farm_health(other, now=NOW), now=NOW)
