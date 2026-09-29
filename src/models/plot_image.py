"""Plot image record: one uploaded photo attached to a plot (M035).

The bytes live on disk under ``settings.upload_dir`` with a
server-generated name; this row is the source of truth for *who may
read it* (plot ownership), *what it claims to be* (sniffed content
type) and *where it is* (``stored_name``). ``original_name`` is
display-only — it never touches the filesystem path.

Deleting a plot cascades its rows (the on-disk files are orphaned —
documented limitation, cleanup is a later milestone).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PlotImage(Base):
    """Metadata for one stored upload."""

    __tablename__ = "plot_images"
    __table_args__ = (UniqueConstraint("stored_name", name="plot_images_stored_name_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    stored_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # stored_name is server-generated, safe to log
        return (
            f"PlotImage(id={self.id!r}, plot_id={self.plot_id!r}, "
            f"content_type={self.content_type!r})"
        )
