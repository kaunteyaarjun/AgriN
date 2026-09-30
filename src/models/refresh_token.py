"""RefreshToken model: persistent refresh-token state (M055).

One row per issued refresh token, keyed by the token's ``jti`` claim.
The row is what makes revocation possible: login inserts, refresh
**rotates** (revokes the old row and issues a new token), logout
revokes, and presenting a revoked row means the token leaked — its
whole user's active rows get revoked (reuse detection).

Access tokens stay stateless (M009 design, unchanged).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class RefreshToken(Base):
    """One issued (and possibly revoked) refresh token."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:  # no token material, ever
        return (
            f"RefreshToken(id={self.id!r}, user_id={self.user_id!r}, "
            f"revoked_at={self.revoked_at!r})"
        )
