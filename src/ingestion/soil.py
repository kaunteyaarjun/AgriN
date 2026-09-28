"""Soil ingestion service (M029): provider reading → storage.

Mirrors :mod:`src.ingestion.weather` and :mod:`src.ingestion.satellite`
family-for-family (shared result types live in
:mod:`src.ingestion._shared`): M021 pattern → M028 demo provider →
M019 cache write path.

Per farm: fetch a :class:`SoilReading` (default: settings-selected
provider), append a :class:`SoilObservation` history row, then merge
the reading into the farm signal cache under the ``soil`` key —
**preserving every other family key** (``weather``, ``satellite``).

Failure policy: the provider call happens *before* any write, so
``ProviderError`` leaves the database untouched (status
``provider_error``, logged, counted). The observation insert commits
before the cache merge (two-step by design — a crash in between is
healed by the next run; documented in M029's spec).

``observed_at`` = ``reading.fetched_at`` — soil is in-situ (no
separate scene time).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFound
from src.ingestion._shared import IngestResult, IngestSummary
from src.models import Farm, FarmSignalCache, SoilObservation
from src.providers.errors import ProviderError
from src.providers.soil import SoilProvider, SoilReading, get_soil_provider
from src.services.farm_state import put_signals

logger = logging.getLogger("agrin.ingestion.soil")


def soil_signals_doc(reading: SoilReading) -> dict[str, Any]:
    """Family document for the cache — payload fields as fetched."""
    return {
        "soil": {
            "soil_moisture_pct": reading.soil_moisture_pct,
            "ph": reading.ph,
            "soil_temperature_c": reading.soil_temperature_c,
            "nitrogen_kg_ha": reading.nitrogen_kg_ha,
            "observed_at": reading.fetched_at.isoformat(),
            "source": reading.source,
        }
    }


async def ingest_soil_for_farm(
    session: AsyncSession,
    farm_id: uuid.UUID,
    *,
    provider: SoilProvider | None = None,
) -> IngestResult:
    """Fetch, store and cache one farm's soil reading. Raises ``NotFound``
    for an unknown farm; provider failures are returned as a status."""
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

    soil_provider = provider or get_soil_provider()
    try:
        reading = await soil_provider.fetch(record.lat, record.lon)
    except ProviderError as exc:
        logger.warning("soil provider error farm=%s: %s", farm_id, exc)
        return IngestResult(farm_id=farm_id, status="provider_error", detail=str(exc))

    observation = SoilObservation(
        farm_id=farm_id,
        provider=reading.source,
        observed_at=reading.fetched_at,
        soil_moisture_pct=reading.soil_moisture_pct,
        ph=reading.ph,
        soil_temperature_c=reading.soil_temperature_c,
        nitrogen_kg_ha=reading.nitrogen_kg_ha,
    )
    session.add(observation)
    await session.commit()

    existing = await session.get(FarmSignalCache, farm_id)
    signals: dict[str, Any] = {} if existing is None else dict(existing.signals)
    signals.update(soil_signals_doc(reading))
    await put_signals(session, farm_id, signals=signals, refreshed_at=reading.fetched_at)

    return IngestResult(farm_id=farm_id, status="ingested", observation_id=observation.id)


async def ingest_soil_for_all(
    session: AsyncSession,
    *,
    provider: SoilProvider | None = None,
) -> IngestSummary:
    """Ingest every farm sequentially; per-farm failures never abort the batch."""
    farm_ids = (await session.execute(select(Farm.id).order_by(Farm.id))).scalars().all()
    summary = IngestSummary()
    for farm_id in farm_ids:
        try:
            result = await ingest_soil_for_farm(session, farm_id, provider=provider)
        except Exception as exc:  # noqa: BLE001 — batch isolation is the contract
            await session.rollback()
            logger.warning("soil ingest failed farm=%s: %s", farm_id, type(exc).__name__)
            result = IngestResult(
                farm_id=farm_id,
                status="failed",
                detail=f"unexpected {type(exc).__name__}",
            )
        summary.record(result)
    return summary
