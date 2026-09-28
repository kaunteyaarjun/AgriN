"""SatelliteObservation model: append-only NDVI history per farm (M026).

One row per successful ingest. The farm signal cache
(:class:`~src.models.farm_signal_cache.FarmSignalCache`) keeps only the
latest snapshot; this table is the NDVI timeline crop-health views
(M047+) and M031's quality gating read from. Rows are immutable — no
``updated_at``, no updates through the service.

``observed_at`` is the SCENE CAPTURE time (``captured_at`` from the
provider reading, falling back to ``fetched_at``), not the fetch time.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SatelliteObservation(Base):
    """One fetched satellite scene for one farm."""

    __tablename__ = "satellite_observations"
    __table_args__ = (Index("ix_satellite_observations_farm_observed", "farm_id", "observed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    cloud_cover_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"SatelliteObservation(farm_id={self.farm_id!r}, provider={self.provider!r}, "
            f"observed_at={self.observed_at!r}, ndvi={self.ndvi!r})"
        )
