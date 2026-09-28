"""Weather ingestion service (M023): provider reading → storage.

The first full vertical of the platform:
M021 pattern → M022 demo provider → M019 cache write path.

Per farm: fetch a :class:`WeatherReading` (default: settings-selected
provider), append a :class:`WeatherObservation` history row, then merge
the reading into the farm signal cache under the ``weather`` key —
**preserving every other family key** (that per-provider merging is
this layer's job, per M019's contract; M031 later normalizes the raw
units stored here).

Failure policy: the provider call happens *before* any write, so
``ProviderError`` leaves the database untouched (status
``provider_error``, logged, counted). The observation insert commits
before the cache merge (two-step by design — a crash in between is
healed by the next run; documented in M023's spec).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFound
from src.models import Farm, FarmSignalCache, WeatherObservation
from src.providers.errors import ProviderError
from src.providers.weather import WeatherProvider, WeatherReading, get_weather_provider
from src.services.farm_state import put_signals

logger = logging.getLogger("agrin.ingestion.weather")

IngestStatus = Literal["ingested", "skipped_no_geo", "provider_error", "failed"]


class IngestResult(BaseModel):
    """Outcome of one farm's ingestion attempt."""

    farm_id: uuid.UUID
    status: IngestStatus
    observation_id: uuid.UUID | None = None
    detail: str | None = None


class IngestSummary(BaseModel):
    """Aggregate outcome of a batch run."""

    ingested: int = 0
    skipped_no_geo: int = 0
    provider_error: int = 0
    failed: int = 0
    results: list[IngestResult] = []

    def record(self, result: IngestResult) -> None:
        self.results.append(result)
        setattr(self, result.status, getattr(self, result.status) + 1)


def weather_signals_doc(reading: WeatherReading) -> dict[str, Any]:
    """Family document for the cache — RAW provider units (M031 normalizes)."""
    return {
        "weather": {
            "temperature_c": reading.temperature_c,
            "humidity_pct": reading.humidity_pct,
            "rainfall_mm_24h": reading.rainfall_mm_24h,
            "wind_speed_kmh": reading.wind_speed_kmh,
            "condition": reading.condition,
            "observed_at": reading.fetched_at.isoformat(),
            "source": reading.source,
        }
    }


async def ingest_weather_for_farm(
    session: AsyncSession,
    farm_id: uuid.UUID,
    *,
    provider: WeatherProvider | None = None,
) -> IngestResult:
    """Fetch, store and cache one farm's weather. Raises ``NotFound``
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

    weather_provider = provider or get_weather_provider()
    try:
        reading = await weather_provider.fetch(record.lat, record.lon)
    except ProviderError as exc:
        logger.warning("weather provider error farm=%s: %s", farm_id, exc)
        return IngestResult(farm_id=farm_id, status="provider_error", detail=str(exc))

    observation = WeatherObservation(
        farm_id=farm_id,
        provider=reading.source,
        observed_at=reading.fetched_at,
        temperature_c=reading.temperature_c,
        humidity_pct=reading.humidity_pct,
        rainfall_mm_24h=reading.rainfall_mm_24h,
        wind_speed_kmh=reading.wind_speed_kmh,
        condition=reading.condition,
    )
    session.add(observation)
    await session.commit()

    existing = await session.get(FarmSignalCache, farm_id)
    signals: dict[str, Any] = {} if existing is None else dict(existing.signals)
    signals.update(weather_signals_doc(reading))
    await put_signals(session, farm_id, signals=signals, refreshed_at=reading.fetched_at)

    return IngestResult(farm_id=farm_id, status="ingested", observation_id=observation.id)


async def ingest_weather_for_all(
    session: AsyncSession,
    *,
    provider: WeatherProvider | None = None,
) -> IngestSummary:
    """Ingest every farm sequentially; per-farm failures never abort the batch."""
    farm_ids = (await session.execute(select(Farm.id).order_by(Farm.id))).scalars().all()
    summary = IngestSummary()
    for farm_id in farm_ids:
        try:
            result = await ingest_weather_for_farm(session, farm_id, provider=provider)
        except Exception as exc:  # noqa: BLE001 — batch isolation is the contract
            await session.rollback()
            logger.warning("weather ingest failed farm=%s: %s", farm_id, type(exc).__name__)
            result = IngestResult(
                farm_id=farm_id,
                status="failed",
                detail=f"unexpected {type(exc).__name__}",
            )
        summary.record(result)
    return summary
