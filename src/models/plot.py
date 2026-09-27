"""Plot model: a sub-field boundary inside a farm (M015, decision D7).

``geo`` is ``geometry(Geometry, 4326)`` — WGS84 Polygon/MultiPolygon,
NULL until mapped, GIST-indexed for the overlay queries (M018+).
Name is unique per farm (DB-enforced). Plot-in-farm containment checks
belong to the M016 service layer, not here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Plot(Base):
    """One plot/field unit of a farm."""

    __tablename__ = "plots"
    __table_args__ = (UniqueConstraint("farm_id", "name", name="plots_farm_id_name_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    area_hectares: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=None
    )
    geo: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="Geometry", srid=4326, spatial_index=True),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:  # never dump the geo blob (can be large)
        return f"Plot(id={self.id!r}, farm_id={self.farm_id!r}, name={self.name!r})"
