"""Weather ingestion tests (M023): provider → observation row → cache
merge, skip/error paths, batch isolation, worker entry.

Against dev Postgres (SKIP when unreachable); cleanup scoped to seeded
users (FK cascade clears farmers → farms → observations/caches).
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
from sqlalchemy import delete, func, select, text
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.errors import NotFound
from src.ingestion.weather import (
    ingest_weather_for_all,
    ingest_weather_for_farm,
    weather_signals_doc,
)
from src.models import Farm, Farmer, FarmSignalCache, User, WeatherObservation
from src.providers.errors import ProviderUnavailable
from src.providers.weather import WeatherProvider, WeatherReading

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 28, 6, 0, 0, tzinfo=UTC)

POLYGON_A: dict[str, object] = {  # around 36.75, -1.29
    "type": "Polygon",
    "coordinates": [[[36.75, -1.29], [36.76, -1.29], [36.76, -1.28], [36.75, -1.29]]],
}
POLYGON_B: dict[str, object] = {  # around 37.5, -1.3
    "type": "Polygon",
    "coordinates": [[[37.5, -1.3], [37.51, -1.3], [37.51, -1.29], [37.5, -1.3]]],
}


class FakeWeather(WeatherProvider):
    """Compliant fake: one fixed reading, records what it was asked for."""

    mode = "demo"
    name = "fake-ingest"

    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        self.calls.append((lat, lon))
        return WeatherReading(
            fetched_at=NOW,
            source=self.name,
            temperature_c=24.0,
            humidity_pct=61.0,
            rainfall_mm_24h=3.2,
            wind_speed_kmh=14.0,
            condition="light_rain",
        )


class DownWeather(WeatherProvider):
    mode = "demo"
    name = "down-ingest"

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        raise ProviderUnavailable("demo upstream down")


class BoomWeather(WeatherProvider):
    """Raises a NON-ProviderError for eastern points — batch isolation probe."""

    mode = "demo"
    name = "boom-ingest"

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        if lon > 37.0:
            raise RuntimeError("kaboom")
        return WeatherReading(fetched_at=NOW, source=self.name, temperature_c=20.0)


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


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[str, User], None]:
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    user = User(email=f"ingw-{uuid.uuid4().hex[:10]}@example.com", password_hash="stored-hash")
    session.add(user)
    users["alpha"] = user
    await session.commit()
    session.add(Farmer(user_id=user.id, full_name="Ingest Owner"))
    await session.commit()
    try:
        yield users
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email.in_([u.email for u in users.values()])))
        await session.commit()
        await session.close()


async def _seed_farm(users: dict[str, User], name: str, geo: dict[str, object] | None) -> uuid.UUID:
    session = get_sessionmaker()()
    try:
        profile_id = await session.scalar(
            select(Farmer.id).where(Farmer.user_id == users["alpha"].id)
        )
        assert profile_id is not None
        farm = Farm(farmer_id=profile_id, name=name, area_hectares=1)
        if geo is not None:
            farm.geo = func.ST_GeomFromGeoJSON(json.dumps(geo))
        session.add(farm)
        await session.commit()
        return farm.id
    finally:
        await session.close()


async def _observations(farm_id: uuid.UUID) -> list[WeatherObservation]:
    session = get_sessionmaker()()
    try:
        rows = (
            (
                await session.execute(
                    select(WeatherObservation)
                    .where(WeatherObservation.farm_id == farm_id)
                    .order_by(WeatherObservation.created_at, WeatherObservation.id)
                )
            )
            .scalars()
            .all()
        )
        session.expunge_all()
        return list(rows)
    finally:
        await session.close()


# ---------- mapping ----------


def test_weather_signals_doc_mapping() -> None:
    reading = WeatherReading(
        fetched_at=NOW,
        source="demo-weather-v1",
        temperature_c=24.0,
        humidity_pct=61.0,
        rainfall_mm_24h=3.2,
        wind_speed_kmh=14.0,
        condition="light_rain",
    )
    doc = weather_signals_doc(reading)
    assert set(doc) == {"weather"}
    weather = doc["weather"]
    assert weather["temperature_c"] == 24.0  # raw units — M031 normalizes later
    assert weather["observed_at"] == NOW.isoformat()
    assert weather["source"] == "demo-weather-v1"


# ---------- happy path + merge ----------


async def test_ingest_stores_observation_and_merges_cache(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_farm(_users, "Ingest A", POLYGON_A)
    session = get_sessionmaker()()
    try:
        # pre-existing satellite key must survive the weather merge
        from src.services.farm_state import put_signals

        await put_signals(session, farm_id, signals={"satellite": {"ndvi": 0.55}})

        provider = FakeWeather()
        result = await ingest_weather_for_farm(session, farm_id, provider=provider)

        assert result.status == "ingested"
        assert result.observation_id is not None

        observations = await _observations(farm_id)
        assert len(observations) == 1
        row = observations[0]
        assert row.provider == "fake-ingest"
        assert row.observed_at == NOW
        assert row.temperature_c == 24.0
        assert provider.calls and all(
            -90 <= lat <= 90 and -180 <= lon <= 180 for lat, lon in provider.calls
        )

        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None
        assert set(cache.signals) == {"satellite", "weather"}  # merged, not replaced
        assert cache.signals["satellite"] == {"ndvi": 0.55}
        assert cache.signals["weather"]["temperature_c"] == 24.0
        assert cache.refreshed_at == NOW
    finally:
        await session.close()


async def test_ingest_uses_default_settings_provider(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Ingest Default", POLYGON_A)
    session = get_sessionmaker()()
    try:
        result = await ingest_weather_for_farm(session, farm_id)  # no provider= — settings path
        assert result.status == "ingested"
        rows = await _observations(farm_id)
        assert rows[0].provider == "demo-weather-v1"  # M022 registered demo
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None and "weather" in cache.signals
    finally:
        await session.close()


async def test_repeated_ingest_appends_history(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Ingest Twice", POLYGON_A)
    session = get_sessionmaker()()
    try:
        first = await ingest_weather_for_farm(session, farm_id, provider=FakeWeather())
        second = await ingest_weather_for_farm(session, farm_id, provider=FakeWeather())
        assert first.status == second.status == "ingested"
        assert first.observation_id != second.observation_id
        rows = await _observations(farm_id)
        assert len(rows) == 2  # append-only, no dedup
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None  # still exactly one cache row (PK)
    finally:
        await session.close()


# ---------- skip / error paths ----------


async def test_farm_without_geo_is_skipped_without_provider_call(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_farm(_users, "Ingest NoGeo", None)
    session = get_sessionmaker()()
    try:
        result = await ingest_weather_for_farm(session, farm_id, provider=FakeWeather())
        assert result.status == "skipped_no_geo"
        assert await _observations(farm_id) == []
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is None
    finally:
        await session.close()


async def test_provider_failure_writes_nothing(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Ingest Down", POLYGON_A)
    session = get_sessionmaker()()
    try:
        result = await ingest_weather_for_farm(session, farm_id, provider=DownWeather())
        assert result.status == "provider_error"
        assert result.detail == "demo upstream down"
        assert await _observations(farm_id) == []
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is None  # fetch happens BEFORE any write
    finally:
        await session.close()


async def test_unknown_farm_raises_not_found(_db: None) -> None:
    # _db is required even without _users: its teardown disposes the
    # engine — without it a pooled connection outlives this test's
    # event loop and the NEXT test's reachability probe fails (lesson).
    session = get_sessionmaker()()
    try:
        with pytest.raises(NotFound):
            await ingest_weather_for_farm(session, uuid.uuid4(), provider=FakeWeather())
    finally:
        await session.close()


# ---------- batch ----------


async def test_ingest_for_all_counts_every_status(_users: dict[str, User]) -> None:
    with_geo = await _seed_farm(_users, "Batch A", POLYGON_A)
    with_geo_2 = await _seed_farm(_users, "Batch B", POLYGON_B)
    no_geo = await _seed_farm(_users, "Batch NoGeo", None)
    session = get_sessionmaker()()
    try:
        summary = await ingest_weather_for_all(session, provider=FakeWeather())
        assert summary.ingested == 2
        assert summary.skipped_no_geo == 1
        assert summary.provider_error == 0
        assert summary.failed == 0
        assert len(summary.results) == 3
        by_farm = {r.farm_id: r.status for r in summary.results}
        assert by_farm[with_geo] == "ingested"
        assert by_farm[with_geo_2] == "ingested"
        assert by_farm[no_geo] == "skipped_no_geo"
    finally:
        await session.close()


async def test_ingest_for_all_isolates_unexpected_failures(
    _users: dict[str, User],
) -> None:
    west = await _seed_farm(_users, "Iso West", POLYGON_A)  # lon < 37 → ok
    east = await _seed_farm(_users, "Iso East", POLYGON_B)  # lon > 37 → boom
    session = get_sessionmaker()()
    try:
        summary = await ingest_weather_for_all(session, provider=BoomWeather())
        assert summary.ingested == 1
        assert summary.failed == 1  # batch continued past the kaboom
        by_farm = {r.farm_id: r for r in summary.results}
        assert by_farm[west].status == "ingested"
        assert by_farm[east].status == "failed"
        assert by_farm[east].detail == "unexpected RuntimeError"
        assert await _observations(east) == []  # rolled back, no partial row
    finally:
        await session.close()


# ---------- worker entry ----------


async def test_worker_single_farm_prints_status(
    _users: dict[str, User], capsys: pytest.CaptureFixture[str]
) -> None:
    from workers.weather_ingest import _run

    farm_id = await _seed_farm(_users, "Worker Farm", POLYGON_A)
    exit_code = await _run(farm_id)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(farm_id) in captured.out
    assert "ingested" in captured.out
    rows = await _observations(farm_id)
    assert len(rows) == 1
