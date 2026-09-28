"""WeatherObservation model: append-only weather history per farm (M023).

One row per successful ingest. The farm signal cache
(:class:`~src.models.farm_signal_cache.FarmSignalCache`) keeps only the
latest snapshot; this table is the timeline M031's normalization and
any future trend views read from. Rows are immutable — no
``updated_at``, no updates through the service.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class WeatherObservation(Base):
    """One fetched weather reading for one farm."""

    __tablename__ = "weather_observations"
    __table_args__ = (Index("ix_weather_observations_farm_observed", "farm_id", "observed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_mm_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    condition: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"WeatherObservation(farm_id={self.farm_id!r}, provider={self.provider!r}, "
            f"observed_at={self.observed_at!r}, temp={self.temperature_c!r})"
        )
