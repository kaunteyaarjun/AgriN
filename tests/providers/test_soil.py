"""Soil demo provider tests (M028): registration through the normal
M021 path, determinism, documented value ranges, coordinate guard —
plus the rule-of-three extraction (shared ``point_seed``/``check_wgs84``
now back weather + satellite + soil demos).

Pure unit — the demo provider has no I/O by design.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from src.providers import (
    DemoSoilProvider,
    SoilProvider,
    SoilReading,
    get_provider,
    get_soil_provider,
)
from src.providers._demo import check_wgs84, point_seed
from src.providers.soil_demo import DEMO_NAME

NAIROBI = (-1.2921, 36.8219)
MOMBASA = (-4.0435, 39.6682)

# documented ranges (spec: M028)
MOISTURE_RANGE = (20.0, 60.0)
PH_RANGE = (5.5, 7.5)
TEMP_RANGE = (12.0, 28.0)
NITROGEN_RANGE = (20.0, 120.0)


def test_registered_through_normal_settings_path() -> None:
    provider = get_provider("soil")  # settings default: demo
    assert isinstance(provider, DemoSoilProvider)
    typed = get_soil_provider()
    assert isinstance(typed, SoilProvider)
    assert typed.family == "soil"
    assert typed.mode == "demo"
    assert typed.name == DEMO_NAME
    assert provider is typed  # registry caches the same instance


async def test_same_point_is_deterministic() -> None:
    provider = DemoSoilProvider()
    first = await provider.fetch(*NAIROBI)
    second = await provider.fetch(*NAIROBI)
    dump1 = first.model_dump(exclude={"fetched_at"})
    dump2 = second.model_dump(exclude={"fetched_at"})
    assert dump1 == dump2
    assert isinstance(first, SoilReading)


async def test_different_points_differ() -> None:
    provider = DemoSoilProvider()
    nairobi = (await provider.fetch(*NAIROBI)).model_dump(exclude={"fetched_at", "source"})
    mombasa = (await provider.fetch(*MOMBASA)).model_dump(exclude={"fetched_at", "source"})
    assert nairobi != mombasa


@pytest.mark.parametrize("lat,lon", [NAIROBI, MOMBASA, (0.0, 0.0), (51.5, -0.12), (-33.9, 151.2)])
async def test_values_within_documented_ranges(lat: float, lon: float) -> None:
    reading = await DemoSoilProvider().fetch(lat, lon)
    moisture, ph = reading.soil_moisture_pct, reading.ph
    temp, nitrogen = reading.soil_temperature_c, reading.nitrogen_kg_ha
    assert moisture is not None and MOISTURE_RANGE[0] <= moisture <= MOISTURE_RANGE[1]
    assert round(moisture, 1) == moisture
    assert ph is not None and PH_RANGE[0] <= ph <= PH_RANGE[1]
    assert round(ph, 1) == ph
    assert temp is not None and TEMP_RANGE[0] <= temp <= TEMP_RANGE[1]
    assert round(temp, 1) == temp
    assert nitrogen is not None and NITROGEN_RANGE[0] <= nitrogen <= NITROGEN_RANGE[1]
    assert nitrogen.is_integer()
    assert reading.source == DEMO_NAME
    assert reading.fetched_at.tzinfo is not None


async def test_fetched_at_is_recent_utc() -> None:
    reading = await DemoSoilProvider().fetch(*NAIROBI)
    now = datetime.now(UTC)
    assert abs((now - reading.fetched_at).total_seconds()) < 60


@pytest.mark.parametrize("lat,lon", [(91.0, 0.0), (-90.1, 0.0), (0.0, 181.0), (0.0, -180.1)])
async def test_out_of_range_coordinates_raise_value_error(lat: float, lon: float) -> None:
    with pytest.raises(ValueError, match="WGS84"):
        await DemoSoilProvider().fetch(lat, lon)


def test_point_seed_is_stable_and_local() -> None:
    # stable across processes (plain sha256 of the rounded coordinates)
    assert point_seed(*NAIROBI) == point_seed(-1.2921, 36.8219)
    assert point_seed(*NAIROBI) != point_seed(*MOMBASA)
    # 4-decimal rounding: tiny jitter below the precision floor is ignored
    assert point_seed(*NAIROBI) == point_seed(-1.29214, 36.82186)


def test_shared_helpers_cover_all_three_families() -> None:
    # the M028 extraction: weather/satellite/soil demos all route through
    # the same seed + guard (previously two verbatim copies)
    from src.providers import DemoSatelliteProvider, DemoWeatherProvider
    from src.providers.satellite_demo import DEMO_NAME as SAT_NAME
    from src.providers.weather_demo import DEMO_NAME as WEATHER_NAME

    assert WEATHER_NAME and SAT_NAME and DEMO_NAME  # all three registered
    assert DemoWeatherProvider.family == "weather"
    assert DemoSatelliteProvider.family == "satellite"
    assert DemoSoilProvider.family == "soil"
    with pytest.raises(ValueError, match="WGS84"):
        check_wgs84(91.0, 0.0)
