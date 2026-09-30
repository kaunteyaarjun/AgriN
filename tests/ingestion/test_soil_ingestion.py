"""Soil ingestion tests (M029): provider → observation row → cache
merge, skip/error paths, batch isolation, worker entry — plus the
rule-of-three extraction guard (shared result types).

Against dev Postgres (SKIP when unreachable); cleanup scoped to seeded
users (FK cascade clears farmers → farms → soil observations/caches).
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
from src.ingestion.soil import (
    ingest_soil_for_all,
    ingest_soil_for_farm,
    soil_signals_doc,
)
from src.models import Farm, Farmer, FarmSignalCache, SoilObservation, User
from src.providers.errors import ProviderUnavailable
from src.providers.soil import SoilProvider, SoilReading

NOW = datetime(2026, 9, 28, 6, 0, 0, tzinfo=UTC)

POLYGON_A: dict[str, object] = {  # around 36.75, -1.29
    "type": "Polygon",
    "coordinates": [[[36.75, -1.29], [36.76, -1.29], [36.76, -1.28], [36.75, -1.29]]],
}
POLYGON_B: dict[str, object] = {  # around 37.5, -1.3
    "type": "Polygon",
    "coordinates": [[[37.5, -1.3], [37.51, -1.3], [37.51, -1.29], [37.5, -1.3]]],
}


class FakeSoil(SoilProvider):
    """Compliant fake: one fixed reading, records what it was asked for."""

    mode = "demo"
    name = "fake-ingest"

    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []

    async def fetch(self, lat: float, lon: float) -> SoilReading:
        self.calls.append((lat, lon))
        return SoilReading(
            fetched_at=NOW,
            source=self.name,
            soil_moisture_pct=33.3,
            ph=6.6,
            soil_temperature_c=18.8,
            nitrogen_kg_ha=66.0,
        )


class DownSoil(SoilProvider):
    mode = "demo"
    name = "down-ingest"

    async def fetch(self, lat: float, lon: float) -> SoilReading:
        raise ProviderUnavailable("demo upstream down")


class BoomSoil(SoilProvider):
    """Raises a NON-ProviderError for eastern points — batch isolation probe."""

    mode = "demo"
    name = "boom-ingest"

    async def fetch(self, lat: float, lon: float) -> SoilReading:
        if lon > 37.0:
            raise RuntimeError("kaboom")
        return SoilReading(fetched_at=NOW, source=self.name, ph=6.0)


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[str, User], None]:
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    user = User(email=f"ingso-{uuid.uuid4().hex[:10]}@example.com", password_hash="stored-hash")
    session.add(user)
    users["alpha"] = user
    await session.commit()
    session.add(Farmer(user_id=user.id, full_name="Soil Ingest Owner"))
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


async def _observations(farm_id: uuid.UUID) -> list[SoilObservation]:
    session = get_sessionmaker()()
    try:
        rows = (
            (
                await session.execute(
                    select(SoilObservation)
                    .where(SoilObservation.farm_id == farm_id)
                    .order_by(SoilObservation.created_at, SoilObservation.id)
                )
            )
            .scalars()
            .all()
        )
        session.expunge_all()
        return list(rows)
    finally:
        await session.close()


# ---------- shared extraction (rule of three) ----------


def test_shared_result_types_used_by_all_families() -> None:
    from typing import get_args

    from src.ingestion import satellite, soil, weather
    from src.ingestion._shared import IngestResult, IngestStatus, IngestSummary

    assert weather.IngestResult is IngestResult
    assert satellite.IngestResult is IngestResult
    assert soil.IngestResult is IngestResult
    assert weather.IngestSummary is IngestSummary
    assert satellite.IngestSummary is IngestSummary
    assert set(get_args(IngestStatus)) == {
        "ingested",
        "skipped_no_geo",
        "provider_error",
        "failed",
    }


# ---------- mapping ----------


def test_soil_signals_doc_mapping() -> None:
    reading = SoilReading(
        fetched_at=NOW,
        source="demo-soil-v1",
        soil_moisture_pct=33.3,
        ph=6.6,
        soil_temperature_c=18.8,
        nitrogen_kg_ha=66.0,
    )
    doc = soil_signals_doc(reading)
    assert set(doc) == {"soil"}
    soil_doc = doc["soil"]
    assert soil_doc["soil_moisture_pct"] == 33.3
    assert soil_doc["ph"] == 6.6
    assert soil_doc["soil_temperature_c"] == 18.8
    assert soil_doc["nitrogen_kg_ha"] == 66.0
    assert soil_doc["observed_at"] == NOW.isoformat()  # in-situ time = fetched_at
    assert soil_doc["source"] == "demo-soil-v1"


# ---------- happy path + merge ----------


async def test_ingest_stores_observation_and_merges_cache(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Soil Ingest A", POLYGON_A)
    session = get_sessionmaker()()
    try:
        # pre-existing weather + satellite keys must survive the soil merge
        from src.services.farm_state import put_signals

        await put_signals(
            session,
            farm_id,
            signals={"weather": {"temperature_c": 20.0}, "satellite": {"ndvi": 0.55}},
        )

        provider = FakeSoil()
        result = await ingest_soil_for_farm(session, farm_id, provider=provider)

        assert result.status == "ingested"
        assert result.observation_id is not None

        observations = await _observations(farm_id)
        assert len(observations) == 1
        row = observations[0]
        assert row.provider == "fake-ingest"
        assert row.observed_at == NOW  # in-situ: fetched_at stored
        assert row.soil_moisture_pct == 33.3
        assert row.ph == 6.6
        assert row.soil_temperature_c == 18.8
        assert row.nitrogen_kg_ha == 66.0
        assert provider.calls and all(
            -90 <= lat <= 90 and -180 <= lon <= 180 for lat, lon in provider.calls
        )

        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None
        assert set(cache.signals) == {"soil", "satellite", "weather"}  # merged, not replaced
        assert cache.signals["weather"] == {"temperature_c": 20.0}
        assert cache.signals["satellite"] == {"ndvi": 0.55}
        assert cache.signals["soil"]["ph"] == 6.6
        assert cache.refreshed_at == NOW
    finally:
        await session.close()


async def test_ingest_uses_default_settings_provider(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Soil Ingest Default", POLYGON_A)
    session = get_sessionmaker()()
    try:
        result = await ingest_soil_for_farm(session, farm_id)  # no provider= — settings path
        assert result.status == "ingested"
        rows = await _observations(farm_id)
        assert rows[0].provider == "demo-soil-v1"  # M028 registered demo
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is not None and "soil" in cache.signals
    finally:
        await session.close()


async def test_repeated_ingest_appends_history(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Soil Ingest Twice", POLYGON_A)
    session = get_sessionmaker()()
    try:
        first = await ingest_soil_for_farm(session, farm_id, provider=FakeSoil())
        second = await ingest_soil_for_farm(session, farm_id, provider=FakeSoil())
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
    farm_id = await _seed_farm(_users, "Soil Ingest NoGeo", None)
    session = get_sessionmaker()()
    try:
        result = await ingest_soil_for_farm(session, farm_id, provider=FakeSoil())
        assert result.status == "skipped_no_geo"
        assert await _observations(farm_id) == []
        cache = await session.get(FarmSignalCache, farm_id)
        assert cache is None
    finally:
        await session.close()


async def test_provider_failure_writes_nothing(_users: dict[str, User]) -> None:
    farm_id = await _seed_farm(_users, "Soil Ingest Down", POLYGON_A)
    session = get_sessionmaker()()
    try:
        result = await ingest_soil_for_farm(session, farm_id, provider=DownSoil())
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
            await ingest_soil_for_farm(session, uuid.uuid4(), provider=FakeSoil())
    finally:
        await session.close()


# ---------- batch ----------


async def test_ingest_for_all_counts_every_status(_users: dict[str, User]) -> None:
    with_geo = await _seed_farm(_users, "Soil Batch A", POLYGON_A)
    with_geo_2 = await _seed_farm(_users, "Soil Batch B", POLYGON_B)
    no_geo = await _seed_farm(_users, "Soil Batch NoGeo", None)
    session = get_sessionmaker()()
    try:
        summary = await ingest_soil_for_all(session, provider=FakeSoil())
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
    west = await _seed_farm(_users, "Soil Iso West", POLYGON_A)  # lon < 37 → ok
    east = await _seed_farm(_users, "Soil Iso East", POLYGON_B)  # lon > 37 → boom
    session = get_sessionmaker()()
    try:
        summary = await ingest_soil_for_all(session, provider=BoomSoil())
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
    from workers.soil_ingest import _run

    farm_id = await _seed_farm(_users, "Soil Worker Farm", POLYGON_A)
    exit_code = await _run(farm_id)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(farm_id) in captured.out
    assert "ingested" in captured.out
    rows = await _observations(farm_id)
    assert len(rows) == 1
