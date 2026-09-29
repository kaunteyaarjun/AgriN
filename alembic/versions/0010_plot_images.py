"""plot images table (M035)

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-29 13:00:00.000000

Hand-written (M035, standing rule: never trust autogenerate; cross-
checked with ``alembic check`` after applying). One row per uploaded
photo; the bytes live on disk under ``settings.upload_dir``.

- ``plot_id`` FK CASCADE: deleting a plot removes its image rows (the
  files themselves are orphaned - documented limitation).
- ``uploaded_by`` FK SET NULL: the uploader may be deleted later; the
  record of the picture stays with the plot.
- ``content_type`` is the SNIFFED type (JPEG/PNG/WebP), never the one
  the client declared.
- ``stored_name`` is server-generated ``{uuid}.{ext}`` (unique) - the
  client's filename never reaches the path.
- Index on ``plot_id``: the list endpoint scans by plot.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "plot_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("stored_name", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plot_id"], ["plots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_name", name="plot_images_stored_name_key"),
    )
    op.create_index("ix_plot_images_plot_id", "plot_images", ["plot_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_plot_images_plot_id", table_name="plot_images")
    op.drop_table("plot_images")
