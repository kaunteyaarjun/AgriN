"""Farm model: a farmer's field with a PostGIS boundary (M013, decision D7).

``geo`` is ``geometry(Geometry, 4326)`` — WGS84 Polygon/MultiPolygon,
NULL until the boundary is mapped, GIST-indexed for the overlay queries
coming in M018+. Payload validation of GeoJSON is an API concern (M014).
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


class Farm(Base):
    """One farm/field. Name is unique per farmer (DB-enforced)."""

    __tablename__ = "farms"
    __table_args__ = (UniqueConstraint("farmer_id", "name", name="farms_farmer_id_name_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
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
        return f"Farm(id={self.id!r}, farmer_id={self.farmer_id!r}, name={self.name!r})"
