"""Satellite ingestion service (M026): provider reading → storage.

Mirrors :mod:`src.ingestion.weather` family-for-family:
M021 pattern → M025 demo provider → M019 cache write path.

Per farm: fetch a :class:`SatelliteReading` (default: settings-selected
provider), append a :class:`SatelliteObservation` history row, then
merge the reading into the farm signal cache under the ``satellite``
key — **preserving every other family key** (that per-provider merging
is this layer's job, per M019's contract).

Failure policy: the provider call happens *before* any write, so
``ProviderError`` leaves the database untouched (status
``provider_error``, logged, counted). The observation insert commits
before the cache merge (two-step by design — a crash in between is
healed by the next run; documented in M026's spec).

Batch path (``ingest_satellite_for_all``, M056): one point query,
fetches overlap up to ``settings.ingest_concurrency`` in-flight
calls, persistence stays serial on the caller's session.

``observed_at`` = scene capture time (``captured_at`` or ``fetched_at``
fallback) — the moment the satellite saw the farm, not the moment the
provider answered.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.errors import NotFound
from src.ingestion._shared import IngestResult, IngestSummary
from src.models import Farm, FarmSignalCache, SatelliteObservation
from src.providers.errors import ProviderError
from src.providers.satellite import SatelliteProvider, SatelliteReading, get_satellite_provider
from src.services.farm_state import put_signals

logger = logging.getLogger("agrin.ingestion.satellite")


def satellite_signals_doc(reading: SatelliteReading) -> dict[str, Any]:
    """Family document for the cache — payload fields as fetched."""
    observed_at = reading.captured_at or reading.fetched_at
    return {
        "satellite": {
            "ndvi": reading.ndvi,
            "cloud_cover_pct": reading.cloud_cover_pct,
            "observed_at": observed_at.isoformat(),
            "source": reading.source,
        }
    }


async def _persist_reading(
    session: AsyncSession,
    farm_id: uuid.UUID,
    reading: SatelliteReading,
) -> IngestResult:
    """Append the observation, then merge into the cache (M019 path) —
    shared by the single-farm and batch entry points (M056)."""
    observation = SatelliteObservation(
        farm_id=farm_id,
        provider=reading.source,
        observed_at=reading.captured_at or reading.fetched_at,
        ndvi=reading.ndvi,
        cloud_cover_pct=reading.cloud_cover_pct,
    )
    session.add(observation)
    await session.commit()

    existing = await session.get(FarmSignalCache, farm_id)
    signals: dict[str, Any] = {} if existing is None else dict(existing.signals)
    signals.update(satellite_signals_doc(reading))
    await put_signals(session, farm_id, signals=signals, refreshed_at=reading.fetched_at)

    return IngestResult(farm_id=farm_id, status="ingested", observation_id=observation.id)


async def ingest_satellite_for_farm(
    session: AsyncSession,
    farm_id: uuid.UUID,
    *,
    provider: SatelliteProvider | None = None,
) -> IngestResult:
    """Fetch, store and cache one farm's satellite scene. Raises
    ``NotFound`` for an unknown farm; provider failures are returned as
    a status."""
    record = (
        await session.execute(
            select(
                Farm.id,
                func.ST_X(func.ST_Centroid(Farm.geo)).label("lon"),
                func.ST_Y(func.ST_Centroid(Farm.geo)).label("lat"),
            ).where(Farm.id == farm_id)
        )
    ).one_or_none()
    if record is None:
        raise NotFound("Farm not found.")
    if record.lat is None or record.lon is None:
        return IngestResult(farm_id=farm_id, status="skipped_no_geo", detail="farm has no geometry")

    satellite_provider = provider or get_satellite_provider()
    try:
        reading = await satellite_provider.fetch(record.lat, record.lon)
    except ProviderError as exc:
        logger.warning("satellite provider error farm=%s: %s", farm_id, exc)
        return IngestResult(farm_id=farm_id, status="provider_error", detail=str(exc))

    return await _persist_reading(session, farm_id, reading)


async def ingest_satellite_for_all(
    session: AsyncSession,
    *,
    provider: SatelliteProvider | None = None,
    concurrency: int | None = None,
) -> IngestSummary:
    """Ingest every farm: one point query, bounded-concurrent provider
    fetches, serial persistence; per-farm failures never abort the batch.

    M056: the fetch phase is the slow part (live: seconds per farm), so
    it overlaps up to ``concurrency`` (default
    ``settings.ingest_concurrency``) in-flight calls; the caller's
    session is only ever used serially — an ``AsyncSession`` is not
    concurrency-safe, so the persist phase never runs concurrently.
    """
    points = (
        await session.execute(
            select(
                Farm.id,
                func.ST_X(func.ST_Centroid(Farm.geo)).label("lon"),
                func.ST_Y(func.ST_Centroid(Farm.geo)).label("lat"),
            ).order_by(Farm.id)
        )
    ).all()
    limit = concurrency if concurrency is not None else get_settings().ingest_concurrency
    satellite_provider = provider or get_satellite_provider()
    semaphore = asyncio.Semaphore(limit)

    async def _fetch(
        farm_id: uuid.UUID, lat: float | None, lon: float | None
    ) -> SatelliteReading | IngestResult:
        if lat is None or lon is None:
            return IngestResult(
                farm_id=farm_id, status="skipped_no_geo", detail="farm has no geometry"
            )
        async with semaphore:
            try:
                return await satellite_provider.fetch(lat, lon)
            except ProviderError as exc:
                logger.warning("satellite provider error farm=%s: %s", farm_id, exc)
                return IngestResult(farm_id=farm_id, status="provider_error", detail=str(exc))
            except Exception as exc:  # noqa: BLE001 — batch isolation is the contract
                logger.warning("satellite fetch failed farm=%s: %s", farm_id, type(exc).__name__)
                return IngestResult(
                    farm_id=farm_id, status="failed", detail=f"unexpected {type(exc).__name__}"
                )

    outcomes = await asyncio.gather(*(_fetch(p.id, p.lat, p.lon) for p in points))

    summary = IngestSummary()
    for point, outcome in zip(points, outcomes, strict=True):
        try:
            result = (
                outcome
                if isinstance(outcome, IngestResult)
                else await _persist_reading(session, point.id, outcome)
            )
        except Exception as exc:  # noqa: BLE001 — batch isolation is the contract
            await session.rollback()
            logger.warning("satellite ingest failed farm=%s: %s", point.id, type(exc).__name__)
            result = IngestResult(
                farm_id=point.id,
                status="failed",
                detail=f"unexpected {type(exc).__name__}",
            )
        summary.record(result)
    return summary
