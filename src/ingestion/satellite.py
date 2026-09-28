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

``observed_at`` = scene capture time (``captured_at`` or ``fetched_at``
fallback) — the moment the satellite saw the farm, not the moment the
provider answered.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def ingest_satellite_for_all(
    session: AsyncSession,
    *,
    provider: SatelliteProvider | None = None,
) -> IngestSummary:
    """Ingest every farm sequentially; per-farm failures never abort the batch."""
    farm_ids = (await session.execute(select(Farm.id).order_by(Farm.id))).scalars().all()
    summary = IngestSummary()
    for farm_id in farm_ids:
        try:
            result = await ingest_satellite_for_farm(session, farm_id, provider=provider)
        except Exception as exc:  # noqa: BLE001 — batch isolation is the contract
            await session.rollback()
            logger.warning("satellite ingest failed farm=%s: %s", farm_id, type(exc).__name__)
            result = IngestResult(
                farm_id=farm_id,
                status="failed",
                detail=f"unexpected {type(exc).__name__}",
            )
        summary.record(result)
    return summary
