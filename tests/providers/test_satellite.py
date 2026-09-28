"""Satellite/NDVI demo provider tests (M025): registration through the
normal M021 path, determinism, documented value ranges, coordinate guard,
demo time semantics.

Pure unit — the demo provider has no I/O by design.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from src.providers import (
    DemoSatelliteProvider,
    SatelliteProvider,
    SatelliteReading,
    get_provider,
    get_satellite_provider,
)
from src.providers.satellite_demo import DEMO_NAME, _seed

NAIROBI = (-1.2921, 36.8219)
MOMBASA = (-4.0435, 39.6682)

# documented ranges (spec: M025)
NDVI_RANGE = (0.10, 0.90)
CLOUD_RANGE = (0.0, 100.0)

TIME_FIELDS = {"fetched_at", "captured_at"}


def test_registered_through_normal_settings_path() -> None:
    provider = get_provider("satellite")  # settings default: demo
    assert isinstance(provider, DemoSatelliteProvider)
    typed = get_satellite_provider()
    assert isinstance(typed, SatelliteProvider)
    assert typed.family == "satellite"
    assert typed.mode == "demo"
    assert typed.name == DEMO_NAME
    assert provider is typed  # registry caches the same instance


async def test_same_point_is_deterministic() -> None:
    provider = DemoSatelliteProvider()
    first = await provider.fetch(*NAIROBI)
    second = await provider.fetch(*NAIROBI)
    dump1 = first.model_dump(exclude=TIME_FIELDS)
    dump2 = second.model_dump(exclude=TIME_FIELDS)
    assert dump1 == dump2
    assert isinstance(first, SatelliteReading)


async def test_different_points_differ() -> None:
    provider = DemoSatelliteProvider()
    nairobi = (await provider.fetch(*NAIROBI)).model_dump(exclude=TIME_FIELDS | {"source"})
    mombasa = (await provider.fetch(*MOMBASA)).model_dump(exclude=TIME_FIELDS | {"source"})
    assert nairobi != mombasa


@pytest.mark.parametrize("lat,lon", [NAIROBI, MOMBASA, (0.0, 0.0), (51.5, -0.12), (-33.9, 151.2)])
async def test_values_within_documented_ranges(lat: float, lon: float) -> None:
    reading = await DemoSatelliteProvider().fetch(lat, lon)
    ndvi, cloud = reading.ndvi, reading.cloud_cover_pct
    assert ndvi is not None and NDVI_RANGE[0] <= ndvi <= NDVI_RANGE[1]
    assert round(ndvi, 2) == ndvi  # documented 2-decimal precision
    assert cloud is not None and CLOUD_RANGE[0] <= cloud <= CLOUD_RANGE[1]
    assert cloud.is_integer()
    assert reading.source == DEMO_NAME
    assert reading.fetched_at.tzinfo is not None


async def test_demo_times_are_fresh_utc_and_equal() -> None:
    # demo semantics: scene just overflown → captured_at == fetched_at
    reading = await DemoSatelliteProvider().fetch(*NAIROBI)
    now = datetime.now(UTC)
    assert reading.captured_at is not None
    assert reading.captured_at == reading.fetched_at
    assert reading.captured_at.tzinfo is not None
    assert abs((now - reading.fetched_at).total_seconds()) < 60


@pytest.mark.parametrize("lat,lon", [(91.0, 0.0), (-90.1, 0.0), (0.0, 181.0), (0.0, -180.1)])
async def test_out_of_range_coordinates_raise_value_error(lat: float, lon: float) -> None:
    with pytest.raises(ValueError, match="WGS84"):
        await DemoSatelliteProvider().fetch(lat, lon)


def test_seed_is_stable_and_local() -> None:
    # stable across processes (plain sha256 of the rounded coordinates)
    assert _seed(*NAIROBI) == _seed(-1.2921, 36.8219)
    assert _seed(*NAIROBI) != _seed(*MOMBASA)
    # 4-decimal rounding: tiny jitter below the precision floor is ignored
    assert _seed(*NAIROBI) == _seed(-1.29214, 36.82186)
