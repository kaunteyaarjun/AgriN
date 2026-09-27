"""Farmer profile model: domain-facing row 1:1 with a farmer account (M011).

``users`` (M008) stays auth-only; demographics and the surrogate ``farmer_id``
that farms (M013) reference live here. The ``user_id`` UNIQUE constraint is
the 1:1 link (one profile per account), FK ON DELETE CASCADE so profiles
never outlive their account.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Farmer(Base):
    """A farmer's profile. PII: repr exposes id + full_name only."""

    __tablename__ = "farmers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True, default=None)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:  # never include phone/village/district (PII)
        return f"Farmer(id={self.id!r}, user_id={self.user_id!r}, full_name={self.full_name!r})"
