"""satellite observations history table

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-28 18:45:00.000000

Hand-written (M026, standing rule: never trust autogenerate; cross-
checked with ``alembic check`` after applying). Append-only history
of provider satellite scenes per farm — the cache (0006) holds the
latest snapshot, this table holds everything that was ever fetched.

- ``farm_id`` FK CASCADE: deleting a farm removes its observations.
- ``observed_at`` = scene capture time (provider ``captured_at``,
  falling back to ``fetched_at``).
- No ``updated_at``: rows are immutable once written.
- No ``raw_units`` column (deliberate deviation from 0007): NDVI is
  unitless, cloud is explicitly pct — the payload lives in columns.
- Index is ``(farm_id, observed_at)`` ASC — Postgres scans it
  backward for the common ``ORDER BY observed_at DESC`` (keeps the
  model metadata and DDL byte-comparable for ``alembic check``).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "satellite_observations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farm_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ndvi", sa.Float(), nullable=True),
        sa.Column("cloud_cover_pct", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_satellite_observations_farm_observed",
        "satellite_observations",
        ["farm_id", "observed_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_satellite_observations_farm_observed", table_name="satellite_observations")
    op.drop_table("satellite_observations")
