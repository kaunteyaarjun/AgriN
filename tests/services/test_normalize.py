"""Signal normalization tests (M031): raw document → canonical model.

Pure unit coverage — the layer has no I/O, so there is no `_db`
fixture and no database dependency. Bodies are derived from the three
ingestion signals docs (M023/M026/M029) as written.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from src.providers.weather_demo import CONDITIONS as DEMO_CONDITIONS
from src.providers.weather_live import _condition
from src.services.farm_state import FarmStateView, SignalCacheView
from src.services.normalize import (
    CANONICAL_CONDITIONS,
    SOURCE_PROFILES,
    NormalizedSignals,
    SourceProfile,
    normalize_farm_state,
    normalize_signals,
)

NOW = datetime(2026, 9, 29, 12, 0, 0, tzinfo=UTC)
OBSERVED = datetime(2026, 9, 29, 9, 0, 0, tzinfo=UTC)
OBSERVED_ISO = OBSERVED.isoformat()
AGE_AT_NOW = 3 * 3600


def _normalize(signals: dict, *, refreshed_at: datetime | None = None) -> NormalizedSignals:
    return normalize_signals(signals, now=NOW, refreshed_at=refreshed_at)


def test_empty_document_yields_no_families() -> None:
    result = _normalize({})
    assert result.weather is None
    assert result.satellite is None
    assert result.soil is None
    assert result.refreshed_at is None
    assert result.refreshed_age_seconds is None
    assert result.unknown_families == []
    assert result.malformed_families == []


def test_demo_document_round_trips_canonically() -> None:
    result = _normalize(
        {
            "weather": {
                "temperature_c": 22.4,
                "humidity_pct": 48.0,
                "rainfall_mm_24h": 3.5,
                "wind_speed_kmh": 12.0,
                "condition": "clear",
                "observed_at": OBSERVED_ISO,
                "source": "demo-weather-v1",
            },
            "satellite": {
                "ndvi": 0.62,
                "cloud_cover_pct": 10.0,
                "observed_at": OBSERVED_ISO,
                "source": "demo-satellite-v1",
            },
            "soil": {
                "soil_moisture_pct": 35.5,
                "ph": 6.5,
                "soil_temperature_c": 18.0,
                "nitrogen_kg_ha": 40,
                "observed_at": OBSERVED_ISO,
                "source": "demo-soil-v1",
            },
        }
    )
    assert result.weather is not None and result.satellite is not None
    assert result.soil is not None
    assert result.weather.temperature_c == 22.4
    assert result.weather.humidity_pct == 48.0
    assert result.weather.wind_speed_kmh == 12.0
    assert result.weather.condition == "clear"
    assert result.weather.observed_at == OBSERVED
    assert result.weather.age_seconds == AGE_AT_NOW
    assert result.satellite.ndvi == 0.62
    assert result.satellite.cloud_cover_pct == 10.0
    assert result.soil.soil_moisture_pct == 35.5
    assert result.soil.ph == 6.5
    assert result.soil.soil_temperature_c == 18.0
    assert result.soil.nitrogen_kg_ha == 40.0
    assert result.soil.age_seconds == AGE_AT_NOW
    assert result.unknown_families == []
    assert result.malformed_families == []


def test_missing_source_is_not_an_error() -> None:
    result = _normalize({"weather": {"temperature_c": 20.0, "observed_at": OBSERVED_ISO}})
    assert result.weather is not None
    assert result.weather.source is None
    assert result.weather.rainfall_window_hours is None
    assert result.weather.rainfall_mm_per_day is None


def test_demo_rainfall_is_a_24_hour_amount() -> None:
    result = _normalize(
        {
            "weather": {
                "rainfall_mm_24h": 12.0,
                "source": "demo-weather-v1",
                "observed_at": OBSERVED_ISO,
            }
        }
    )
    assert result.weather is not None
    assert result.weather.rainfall_mm == 12.0
    assert result.weather.rainfall_window_hours == 24
    assert result.weather.rainfall_mm_per_day == 12.0


def test_open_meteo_rainfall_is_hourly_and_scales_to_a_day() -> None:
    result = _normalize(
        {
            "weather": {
                "rainfall_mm_24h": 0.5,
                "source": "open-meteo-v1",
                "observed_at": OBSERVED_ISO,
            }
        }
    )
    assert result.weather is not None
    assert result.weather.rainfall_mm == 0.5
    assert result.weather.rainfall_window_hours == 1
    assert result.weather.rainfall_mm_per_day == 12.0


def test_unknown_source_converts_nothing() -> None:
    result = _normalize(
        {
            "weather": {
                "rainfall_mm_24h": 4.0,
                "source": "mystery-weather-v9",
                "observed_at": OBSERVED_ISO,
            },
            "satellite": {"ndvi": 0.5, "source": "mystery-sat-v9", "observed_at": OBSERVED_ISO},
        }
    )
    assert result.weather is not None and result.satellite is not None
    assert result.weather.rainfall_mm == 4.0
    assert result.weather.rainfall_window_hours is None
    assert result.weather.rainfall_mm_per_day is None
    assert result.satellite.ndvi_support_days is None


@pytest.mark.parametrize(
    ("source", "support_days"),
    [("demo-satellite-v1", 1), ("ornl-daac-modis-mod13q1", 16), (None, None), ("other-sat", None)],
)
def test_ndvi_temporal_support_comes_from_the_source_profile(source, support_days) -> None:
    family = {"ndvi": 0.5, "observed_at": OBSERVED_ISO}
    if source is not None:
        family["source"] = source
    result = _normalize({"satellite": family})
    assert result.satellite is not None
    assert result.satellite.ndvi_support_days == support_days


def test_source_profiles_are_documented_for_the_known_sources() -> None:
    assert SOURCE_PROFILES["demo-weather-v1"] == SourceProfile(rainfall_window_hours=24)
    assert SOURCE_PROFILES["open-meteo-v1"] == SourceProfile(rainfall_window_hours=1)
    assert SOURCE_PROFILES["demo-satellite-v1"] == SourceProfile(ndvi_support_days=1)
    assert SOURCE_PROFILES["ornl-daac-modis-mod13q1"] == SourceProfile(ndvi_support_days=16)
    assert SOURCE_PROFILES["demo-soil-v1"] == SourceProfile()


def test_condition_vocabulary_matches_both_weather_providers() -> None:
    assert CANONICAL_CONDITIONS == DEMO_CONDITIONS
    for code in range(0, 100):
        assert _condition(code) in CANONICAL_CONDITIONS


@pytest.mark.parametrize("condition", [None, "hail", "SUNNY", 42])
def test_non_canonical_condition_normalizes_to_none(condition) -> None:
    result = _normalize({"weather": {"condition": condition}})
    assert result.weather is not None
    assert result.weather.condition is None


@pytest.mark.parametrize("condition", list(CANONICAL_CONDITIONS))
def test_canonical_conditions_pass_through(condition) -> None:
    result = _normalize({"weather": {"condition": condition}})
    assert result.weather is not None
    assert result.weather.condition == condition


@pytest.mark.parametrize(
    ("family", "field", "value"),
    [
        ("weather", "temperature_c", 999.0),
        ("weather", "temperature_c", -120.0),
        ("weather", "humidity_pct", 150.0),
        ("weather", "humidity_pct", -1.0),
        ("weather", "rainfall_mm_24h", -5.0),
        ("weather", "wind_speed_kmh", -1.0),
        ("satellite", "ndvi", 1.5),
        ("satellite", "ndvi", -2.0),
        ("satellite", "cloud_cover_pct", 101.0),
        ("satellite", "cloud_cover_pct", -5.0),
        ("soil", "soil_moisture_pct", 120.0),
        ("soil", "ph", 15.0),
        ("soil", "soil_temperature_c", 900.0),
        ("soil", "nitrogen_kg_ha", -3.0),
    ],
)
def test_out_of_physical_range_is_not_data(family: str, field: str, value: float) -> None:
    result = _normalize({family: {field: value, "observed_at": OBSERVED_ISO, "source": "x"}})
    payload = getattr(result, family)
    assert payload is not None
    assert getattr(payload, field if field != "rainfall_mm_24h" else "rainfall_mm") is None


@pytest.mark.parametrize(
    "value",
    [True, False, "22.4", None, float("nan"), float("inf"), float("-inf"), [1.0], {"a": 1}],
)
def test_non_jsonb_numbers_are_rejected(value) -> None:
    result = _normalize({"weather": {"temperature_c": value}})
    assert result.weather is not None
    assert result.weather.temperature_c is None


def test_wind_speed_has_no_ceiling() -> None:
    result = _normalize({"weather": {"wind_speed_kmh": 450.0}})
    assert result.weather is not None
    assert result.weather.wind_speed_kmh == 450.0


def test_nan_infinity_and_bounds_compose() -> None:
    assert math.isfinite(float("inf")) is False
    result = _normalize({"soil": {"ph": float("nan")}})
    assert result.soil is not None
    assert result.soil.ph is None


def test_aware_timestamp_is_kept() -> None:
    result = _normalize({"weather": {"observed_at": OBSERVED_ISO}})
    assert result.weather is not None
    assert result.weather.observed_at == OBSERVED
    assert result.weather.age_seconds == AGE_AT_NOW


def test_naive_timestamp_is_assumed_utc() -> None:
    naive = OBSERVED.replace(tzinfo=None).isoformat()
    result = _normalize({"weather": {"observed_at": naive}})
    assert result.weather is not None
    assert result.weather.observed_at == OBSERVED
    assert result.weather.age_seconds == AGE_AT_NOW


def test_timestamp_with_offset_is_converted_to_utc() -> None:
    shifted = OBSERVED.astimezone(timezone(timedelta(hours=2))).isoformat()
    result = _normalize({"weather": {"observed_at": shifted}})
    assert result.weather is not None
    assert result.weather.observed_at == OBSERVED


@pytest.mark.parametrize("stamp", ["not-a-date", "", 1759156800, None])
def test_unreadable_timestamp_leaves_no_age(stamp) -> None:
    result = _normalize({"weather": {"observed_at": stamp}})
    assert result.weather is not None
    assert result.weather.observed_at is None
    assert result.weather.age_seconds is None


def test_future_observation_yields_a_negative_age() -> None:
    future = (NOW + timedelta(hours=6)).isoformat()
    result = _normalize({"weather": {"observed_at": future}})
    assert result.weather is not None
    assert result.weather.age_seconds == -6 * 3600


def test_refreshed_at_age_is_computed_from_the_cache_timestamp() -> None:
    result = _normalize({}, refreshed_at=NOW - timedelta(minutes=30))
    assert result.refreshed_at == NOW - timedelta(minutes=30)
    assert result.refreshed_age_seconds == 1800


def test_refreshed_at_accepts_a_naive_datetime() -> None:
    naive = NOW.replace(tzinfo=None)
    result = _normalize({}, refreshed_at=naive)
    assert result.refreshed_at == NOW
    assert result.refreshed_age_seconds == 0


def test_unrecognized_keys_are_reported_sorted() -> None:
    result = _normalize({"weather": {}, "zeta": 1, "alpha": 2})
    assert result.unknown_families == ["alpha", "zeta"]
    assert result.malformed_families == []
    assert result.weather is not None


@pytest.mark.parametrize("malformed", [[1, 2], "weather", 7, None])
def test_family_key_holding_a_non_mapping_is_malformed(malformed) -> None:
    result = _normalize({"weather": malformed})
    assert result.weather is None
    assert result.malformed_families == ["weather"]
    assert result.unknown_families == []


def _view(signals: dict, *, refreshed_at: datetime | None = None) -> FarmStateView:
    return FarmStateView(
        farm_id=uuid.uuid4(),
        farmer_id=uuid.uuid4(),
        name="Kibera Farm",
        plots=[],
        plot_count=0,
        planted_plot_count=0,
        crops=[],
        signals=SignalCacheView(signals=signals, refreshed_at=refreshed_at, age_seconds=0),
    )


def test_normalize_farm_state_bundles_view_and_signals() -> None:
    signals = {
        "weather": {"temperature_c": 22.4, "observed_at": OBSERVED_ISO, "source": "demo-weather-v1"}
    }
    state = normalize_farm_state(_view(signals, refreshed_at=NOW - timedelta(hours=1)), now=NOW)
    assert state.view.name == "Kibera Farm"
    assert state.view.plots == []
    assert state.signals.weather is not None
    assert state.signals.weather.temperature_c == 22.4
    assert state.signals.weather.age_seconds == AGE_AT_NOW
    assert state.signals.refreshed_age_seconds == 3600


def test_normalize_farm_state_with_an_empty_cache() -> None:
    state = normalize_farm_state(_view({}), now=NOW)
    assert state.signals.weather is None
    assert state.signals.satellite is None
    assert state.signals.soil is None
    assert state.signals.refreshed_age_seconds is None


def test_normalize_farm_state_with_a_never_filled_cache() -> None:
    state = normalize_farm_state(
        FarmStateView(
            farm_id=uuid.uuid4(),
            farmer_id=uuid.uuid4(),
            name="Empty",
            plots=[],
            plot_count=0,
            planted_plot_count=0,
            crops=[],
            signals=SignalCacheView(signals={}, refreshed_at=None, age_seconds=None),
        ),
        now=NOW,
    )
    assert state.signals.refreshed_at is None
    assert state.signals.refreshed_age_seconds is None
