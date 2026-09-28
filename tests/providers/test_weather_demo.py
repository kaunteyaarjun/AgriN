"""Weather demo provider tests (M022): registration through the normal
M021 path, determinism, documented value ranges, coordinate guard.

Pure unit — the demo provider has no I/O by design.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from src.providers import (
    DemoWeatherProvider,
    WeatherProvider,
    WeatherReading,
    get_provider,
    get_weather_provider,
)
from src.providers.weather_demo import CONDITIONS, DEMO_NAME, _seed

NAIROBI = (-1.2921, 36.8219)
MOMBASA = (-4.0435, 39.6682)

# documented ranges (spec: M022)
TEMP_RANGE = (18.0, 32.9)
HUMIDITY_RANGE = (40.0, 90.0)
RAINFALL_RANGE = (0.0, 11.9)
WIND_RANGE = (1.0, 45.0)


def test_registered_through_normal_settings_path() -> None:
    provider = get_provider("weather")  # settings default: demo
    assert isinstance(provider, DemoWeatherProvider)
    typed = get_weather_provider()
    assert isinstance(typed, WeatherProvider)
    assert typed.family == "weather"
    assert typed.mode == "demo"
    assert typed.name == DEMO_NAME
    assert provider is typed  # registry caches the same instance


async def test_same_point_is_deterministic() -> None:
    provider = DemoWeatherProvider()
    first = await provider.fetch(*NAIROBI)
    second = await provider.fetch(*NAIROBI)
    dump1 = first.model_dump(exclude={"fetched_at"})
    dump2 = second.model_dump(exclude={"fetched_at"})
    assert dump1 == dump2
    assert isinstance(first, WeatherReading)


async def test_different_points_differ() -> None:
    provider = DemoWeatherProvider()
    nairobi = (await provider.fetch(*NAIROBI)).model_dump(exclude={"fetched_at", "source"})
    mombasa = (await provider.fetch(*MOMBASA)).model_dump(exclude={"fetched_at", "source"})
    assert nairobi != mombasa


@pytest.mark.parametrize("lat,lon", [NAIROBI, MOMBASA, (0.0, 0.0), (51.5, -0.12), (-33.9, 151.2)])
async def test_values_within_documented_ranges(lat: float, lon: float) -> None:
    reading = await DemoWeatherProvider().fetch(lat, lon)
    temp, humidity = reading.temperature_c, reading.humidity_pct
    rain, wind = reading.rainfall_mm_24h, reading.wind_speed_kmh
    assert temp is not None and TEMP_RANGE[0] <= temp <= TEMP_RANGE[1]
    assert humidity is not None and HUMIDITY_RANGE[0] <= humidity <= HUMIDITY_RANGE[1]
    assert rain is not None and RAINFALL_RANGE[0] <= rain <= RAINFALL_RANGE[1]
    assert wind is not None and WIND_RANGE[0] <= wind <= WIND_RANGE[1]
    assert reading.condition in CONDITIONS
    assert reading.source == DEMO_NAME
    assert reading.fetched_at.tzinfo is not None


async def test_fetched_at_is_recent_utc() -> None:
    reading = await DemoWeatherProvider().fetch(*NAIROBI)
    now = datetime.now(UTC)
    assert abs((now - reading.fetched_at).total_seconds()) < 60


@pytest.mark.parametrize("lat,lon", [(91.0, 0.0), (-90.1, 0.0), (0.0, 181.0), (0.0, -180.1)])
async def test_out_of_range_coordinates_raise_value_error(lat: float, lon: float) -> None:
    with pytest.raises(ValueError, match="WGS84"):
        await DemoWeatherProvider().fetch(lat, lon)


def test_seed_is_stable_and_local() -> None:
    # stable across processes (plain sha256 of the rounded coordinates)
    assert _seed(*NAIROBI) == _seed(-1.2921, 36.8219)
    assert _seed(*NAIROBI) != _seed(*MOMBASA)
    # 4-decimal rounding: tiny jitter below the precision floor is ignored
    assert _seed(*NAIROBI) == _seed(-1.29214, 36.82186)
