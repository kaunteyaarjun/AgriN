"""SoilObservation model: append-only soil history per farm (M029).

One row per successful ingest. The farm signal cache
(:class:`~src.models.farm_signal_cache.FarmSignalCache`) keeps only the
latest snapshot; this table is the soil timeline M031's quality
gating and any trend views read from. Rows are immutable — no
``updated_at``, no updates through the service.

``observed_at`` = ``fetched_at`` — soil is an in-situ measurement at
the farm's point (no separate scene time, unlike satellite).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SoilObservation(Base):
    """One fetched soil reading for one farm."""

    __tablename__ = "soil_observations"
    __table_args__ = (Index("ix_soil_observations_farm_observed", "farm_id", "observed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    soil_moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    nitrogen_kg_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"SoilObservation(farm_id={self.farm_id!r}, provider={self.provider!r}, "
            f"observed_at={self.observed_at!r}, moisture={self.soil_moisture_pct!r})"
        )
