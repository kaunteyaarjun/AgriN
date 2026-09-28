"""PlotState model: the crop facts of the Farm Digital Twin (M018).

One row per plot (``plot_id`` is the PK *and* FK to ``plots`` with
CASCADE — the 1:1 is enforced by the database, not convention).
Growth stage is constrained by a DB CHECK against ``GROWTH_STAGES``
below; M020's API and M054's seed script reuse that tuple so the
schema, validation and demo data cannot drift apart.

``planted_on`` is a plain date with no "not in the future" DB check:
planting dates can legitimately be planned ahead — that validation
belongs to the API layer (M020).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base

GROWTH_STAGES: tuple[str, ...] = (
    "germination",
    "vegetative",
    "flowering",
    "fruiting",
    "maturation",
    "harvest",
)
"""Canonical stage vocabulary (mirrors the DB CHECK in revision 0006)."""

_STAGE_CHECK_SQL = "growth_stage IN ({})".format(", ".join(f"'{stage}'" for stage in GROWTH_STAGES))


class PlotState(Base):
    """What is growing on a plot: crop, stage, planting date."""

    __tablename__ = "plot_states"
    __table_args__ = (CheckConstraint(_STAGE_CHECK_SQL, name="plot_states_growth_stage_check"),)

    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    crop: Mapped[str] = mapped_column(String(80), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(40), nullable=False)
    planted_on: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"PlotState(plot_id={self.plot_id!r}, crop={self.crop!r}, "
            f"growth_stage={self.growth_stage!r}, planted_on={self.planted_on!r})"
        )
