"""Satellite ingestion tests (M026): provider → observation row → cache
merge, skip/error paths, batch isolation, worker entry.

Against dev Postgres (SKIP when unreachable); cleanup scoped to seeded
users (FK cascade clears farmers → farms → satellite observations/caches).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select
from src.core.db import get_sessionmaker
from src.core.errors import NotFound
from src.ingestion.satellite import (
    ingest_satellite_for_all,
    ingest_satellite_for_farm,
    satellite_signals_doc,
)
from src.models import Farm, Farmer, FarmSignalCache, SatelliteObservation, User
from src.providers.errors import ProviderUnavailable
from src.providers.satellite import SatelliteProvider, SatelliteReading

NOW_FETCH = datetime(2026, 9, 28, 6, 0, 0, tzinfo=UTC)
NOW_CAPTURE = datetime(2026, 9, 28, 5, 30, 0, tzinfo=UTC)  # scene seen earlier

POLYGON_A: dict[str, object] = {  # around 36.75, -1.29
    "type": "Polygon",
    "coordinates": [[[36.75, -1.29], [36.76, -1.29], [36.76, -1.28], [36.75, -1.29]]],
}
POLYGON_B: dict[str, object] = {  # around 37.5, -1.3
    "type": "Polygon",
    "coordinates": [[[37.5, -1.3], [37.51, -1.3], [37.51, -1.29], [37.5, -1.3]]],
}


class FakeSatellite(SatelliteProvider):
    """Compliant fake: one fixed scene, records what it was asked for."""

    mode = "demo"
    name = "fake-ingest"

    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []

    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        self.calls.append((lat, lon))
        return SatelliteReading(
            fetched_at=NOW_FETCH,
            captured_at=NOW_CAPTURE,
            source=self.name,
            ndvi=0.62,
            cloud_cover_pct=12.0,
        )


class DownSatellite(SatelliteProvider):
    mode = "demo"
    name = "down-ingest"

    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        raise ProviderUnavailable("demo upstream down")


class BoomSatellite(SatelliteProvider):
    """Raises a NON-ProviderError for eastern points — batch isolation probe."""

    mode = "demo"
    name = "boom-ingest"

    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        if lon > 37.0:
            raise RuntimeError("kaboom")
        return SatelliteReading(fetched_at=NOW_FETCH, source=self.name, ndvi=0.41)


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[str, User], None]:
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    user = User(email=f"ings-{uuid.uuid4().hex[:10]}@example.com", password_hash="stored-hash")
    session.add(user)
    users["alpha"] = user
    await session.commit()
    session.add(Farmer(user_id=user.id, full_name="Sat Ingest Owner"))
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


async def _observations(farm_id: uuid.UUID) -> list[SatelliteObservation]:
    session = get_sessionmaker()()
    try:
        rows = (
            (
                await session.execute(
                    select(SatelliteObservation)
                    .where(SatelliteObservation.farm_id == farm_id)
                    .order_by(SatelliteObservation.created_at, SatelliteObservation.id)
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


def test_satellite_signals_doc_mapping() -> None:
    reading = SatelliteReading(
        fetched_at=NOW_FETCH,
        captured_at=NOW_CAPTURE,
        source="demo-satellite-v1",
        ndvi=0.62,
        cloud_cover_pct=12.0,
    )
    doc = satellite_signals_doc(reading)
    assert set(doc) == {"satellite"}
    sat = doc["satellite"]
    assert sat["ndvi"] == 0.62
    assert sat["cloud_cover_pct"] == 12.0
    assert sat["observed_at"] == NOW_CAPTURE.isoformat()  # scene time, not fetch time
    assert sat["source"] == "demo-satellite-v1"


def test_satellite_signals_doc_falls_back_to_fetched_at() -> None:
    reading = SatelliteReading(fetched_at=NOW_FETCH, captured_at=None, source="no-scene-time")
    doc = satellite_signals_doc(reading)
    assert doc["satellite"]["observed_at"] == NOW_FETCH.isoformat()
    assert doc["satellite"]["ndvi"] is None  # omitted payload stays in the doc


# ---------- happy path + merge ----------


async def test_ingest_stores_observation_and_merges_cache(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Sat Ingest A", POLYGON_A)
    session = get_sessionmaker()()
    try:
        # pre-existing weather key must survive the satellite merge
        from src.services.farm_state import put_signals

        await put_signals(session, farm_id, signals={"weather": {"temperature_c": 20.0}})

        provider = FakeSatellite()
        result = await ingest_satellite_for_farm(session, farm_id, provider=provider)

        assert result.status == "ingested"
        assert result.observation_id is not None

        observations = await _observations(farm_id)
        assert len(observations) == 1
        row = observations[0]
        assert row.provider == "fake-ingest"
        assert row.observed_at == NOW_CAPTURE  # scene capture time stored
        assert row.ndvi == 0.62
        assert row.cloud_cover_pct == 12.0
        assert provider.calls and all(
            -90 <= lat <= 90 and -180 <= lon <= 180 for lat, lon in provider.calls
        )

        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None
        assert set(cache.signals) == {"satellite", "weather"}  # merged, not replaced
        assert cache.signals["weather"] == {"temperature_c": 20.0}
        assert cache.signals["satellite"]["ndvi"] == 0.62
        assert cache.refreshed_at == NOW_FETCH  # fetch time, per M019 semantics
    finally:
        await session.close()


async def test_ingest_uses_default_settings_provider(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Sat Ingest Default", POLYGON_A)
    session = get_sessionmaker()()
    try:
        result = await ingest_satellite_for_farm(session, farm_id)  # no provider= — settings path
        assert result.status == "ingested"
        rows = await _observations(farm_id)
        assert rows[0].provider == "demo-satellite-v1"  # M025 registered demo
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None and "satellite" in cache.signals
    finally:
        await session.close()


async def test_repeated_ingest_appends_history(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Sat Ingest Twice", POLYGON_A)
    session = get_sessionmaker()()
    try:
        first = await ingest_satellite_for_farm(session, farm_id, provider=FakeSatellite())
        second = await ingest_satellite_for_farm(session, farm_id, provider=FakeSatellite())
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
    farm_id = await _seed_farm(_users, "Sat Ingest NoGeo", None)
    session = get_sessionmaker()()
    try:
        result = await ingest_satellite_for_farm(session, farm_id, provider=FakeSatellite())
        assert result.status == "skipped_no_geo"
        assert await _observations(farm_id) == []
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is None
    finally:
        await session.close()


async def test_provider_failure_writes_nothing(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Sat Ingest Down", POLYGON_A)
    session = get_sessionmaker()()
    try:
        result = await ingest_satellite_for_farm(session, farm_id, provider=DownSatellite())
        assert result.status == "provider_error"
        assert result.detail == "demo upstream down"
        assert await _observations(farm_id) == []
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is None  # fetch happens BEFORE any write
    finally:
        await session.close()


async def test_unknown_farm_raises_not_found(_db: None) -> None:
    # _db required (M023 house rule): its teardown disposes the engine —
    # otherwise a pooled connection outlives this test's event loop and
    # the NEXT test's reachability probe fails with a misleading skip.
    session = get_sessionmaker()()
    try:
        with pytest.raises(NotFound):
            await ingest_satellite_for_farm(session, uuid.uuid4(), provider=FakeSatellite())
    finally:
        await session.close()


# ---------- batch ----------


async def test_ingest_for_all_counts_every_status(_users: dict[str, User]) -> None:
    with_geo = await _seed_farm(_users, "Sat Batch A", POLYGON_A)
    with_geo_2 = await _seed_farm(_users, "Sat Batch B", POLYGON_B)
    no_geo = await _seed_farm(_users, "Sat Batch NoGeo", None)
    session = get_sessionmaker()()
    try:
        summary = await ingest_satellite_for_all(session, provider=FakeSatellite())
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
    west = await _seed_farm(_users, "Sat Iso West", POLYGON_A)  # lon < 37 → ok
    east = await _seed_farm(_users, "Sat Iso East", POLYGON_B)  # lon > 37 → boom
    session = get_sessionmaker()()
    try:
        summary = await ingest_satellite_for_all(session, provider=BoomSatellite())
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
    from workers.satellite_ingest import _run

    farm_id = await _seed_farm(_users, "Sat Worker Farm", POLYGON_A)
    exit_code = await _run(farm_id)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(farm_id) in captured.out
    assert "ingested" in captured.out
    rows = await _observations(farm_id)
    assert len(rows) == 1
