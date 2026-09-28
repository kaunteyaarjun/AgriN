"""FarmSignalCache model: latest external conditions per farm (M018).

Weather, satellite/NDVI and soil signals are fetched for a farm's
location once and shared by all its plots, so the cache lives at farm
grain: PK ``farm_id`` (FK CASCADE), one JSONB ``signals`` document
keyed by provider family (``weather`` / ``satellite`` / ``soil`` — the
ingestion services from M023/M026/M029 write here), plus
``refreshed_at`` recording when the sources were last pulled.

No GIN index on ``signals``: the access pattern is a PK point lookup
and whole-document read/write. Revisit in M056 if a containment
(``@>``) query ever appears.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class FarmSignalCache(Base):
    """One row per farm holding the newest provider signal snapshot."""

    __tablename__ = "farm_signal_caches"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    signals: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
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

    def __repr__(self) -> str:  # never dump the signals blob
        keys = ",".join(sorted(self.signals)) if isinstance(self.signals, dict) else "?"
        return f"FarmSignalCache(farm_id={self.farm_id!r}, signals_keys={keys!r})"
