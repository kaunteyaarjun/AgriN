"""Batch concurrency contract (M056): bounded, actually concurrent, knob-wired.

The three ``ingest_*_for_all`` loops share one shape (one point query →
bounded-concurrent fetch → serial persist), so the full contract is
proven on satellite — in-flight never exceeds the bound, a bound > 1
really overlaps, ``concurrency=1`` is strictly sequential, and the
settings default applies when no kwarg is given — while weather and
soil get a wiring smoke check for the same knob.

DB-backed (SKIP when unreachable); cleanup rides the FK cascade from the
seeded user (M012/M054 pattern).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, func, text
from src.core.config import get_settings
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.ingestion.satellite import ingest_satellite_for_all
from src.ingestion.soil import ingest_soil_for_all
from src.ingestion.weather import ingest_weather_for_all
from src.models import Farm, Farmer, User
from src.providers.satellite import SatelliteProvider, SatelliteReading
from src.providers.soil import SoilProvider, SoilReading
from src.providers.weather import WeatherProvider, WeatherReading

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 28, 12, 0, 0, tzinfo=UTC)
DELAY_S = 0.05

POLYGON: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [36.75, -1.29],
            [36.76, -1.29],
            [36.76, -1.28],
            [36.75, -1.29],
        ]
    ],
}


async def _db_reachable() -> bool:
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _alembic_config() -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return cfg


@pytest.fixture
async def _db() -> AsyncGenerator[None, None]:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    await dispose_engine()


async def _seed_farms(session, count: int) -> uuid.UUID:
    """farmer user + profile + ``count`` farms with geo → user id for cleanup."""
    user = User(email=f"conc-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    farmer = Farmer(user_id=user.id, full_name="Conc Owner")
    session.add(farmer)
    await session.commit()
    for index in range(count):
        farm = Farm(farmer_id=farmer.id, name=f"Conc Farm {index}", area_hectares=1)
        farm.geo = func.ST_GeomFromGeoJSON(json.dumps(POLYGON))
        session.add(farm)
    await session.commit()
    return user.id


async def _cleanup(session, user_id: uuid.UUID) -> None:
    await session.rollback()
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    await session.close()


class SlowSatellite(SatelliteProvider):
    """Sleeps in fetch while recording peak in-flight concurrency."""

    mode = "demo"
    name = "slow-satellite"

    def __init__(self) -> None:
        self.in_flight = 0
        self.max_in_flight = 0

    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(DELAY_S)
        finally:
            self.in_flight -= 1
        return SatelliteReading(fetched_at=NOW, source=self.name, ndvi=0.5)


class SlowWeather(WeatherProvider):
    mode = "demo"
    name = "slow-weather"

    def __init__(self) -> None:
        self.in_flight = 0
        self.max_in_flight = 0

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(DELAY_S)
        finally:
            self.in_flight -= 1
        return WeatherReading(
            fetched_at=NOW,
            source=self.name,
            temperature_c=24.0,
            humidity_pct=61.0,
            rainfall_mm_24h=3.2,
            wind_speed_kmh=14.0,
            condition="light_rain",
        )


class SlowSoil(SoilProvider):
    mode = "demo"
    name = "slow-soil"

    def __init__(self) -> None:
        self.in_flight = 0
        self.max_in_flight = 0

    async def fetch(self, lat: float, lon: float) -> SoilReading:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(DELAY_S)
        finally:
            self.in_flight -= 1
        return SoilReading(
            fetched_at=NOW,
            source=self.name,
            soil_moisture_pct=33.3,
            ph=6.6,
            soil_temperature_c=18.8,
            nitrogen_kg_ha=66.0,
        )


async def test_fetches_really_run_up_to_the_bound(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id = await _seed_farms(session, 6)
        provider = SlowSatellite()
        summary = await ingest_satellite_for_all(session, provider=provider, concurrency=2)
        assert summary.ingested == 6
        # overlapped (not sequential) AND never above the bound
        assert provider.max_in_flight == 2
    finally:
        await _cleanup(session, user_id)


async def test_concurrency_one_is_strictly_sequential(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id = await _seed_farms(session, 3)
        provider = SlowSatellite()
        summary = await ingest_satellite_for_all(session, provider=provider, concurrency=1)
        assert summary.ingested == 3
        assert provider.max_in_flight == 1
    finally:
        await _cleanup(session, user_id)


async def test_settings_default_applies_when_no_kwarg(
    _db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "ingest_concurrency", 1)
    session = get_sessionmaker()()
    try:
        user_id = await _seed_farms(session, 3)
        provider = SlowSatellite()
        summary = await ingest_satellite_for_all(session, provider=provider)
        assert summary.ingested == 3
        assert provider.max_in_flight == 1
    finally:
        await _cleanup(session, user_id)


async def test_weather_and_soil_wire_the_same_bound(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id = await _seed_farms(session, 4)
        weather, soil = SlowWeather(), SlowSoil()
        w_summary = await ingest_weather_for_all(session, provider=weather, concurrency=1)
        s_summary = await ingest_soil_for_all(session, provider=soil, concurrency=2)
        assert w_summary.ingested == 4
        assert weather.max_in_flight == 1
        assert s_summary.ingested == 4
        assert soil.max_in_flight == 2
    finally:
        await _cleanup(session, user_id)
