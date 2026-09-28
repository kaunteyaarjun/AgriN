"""soil observations history table

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-28 19:30:00.000000

Hand-written (M029, standing rule: never trust autogenerate; cross-
checked with ``alembic check`` after applying). Append-only history
of provider soil readings per farm — the cache (0006) holds the
latest snapshot, this table holds everything that was ever fetched.

- ``farm_id`` FK CASCADE: deleting a farm removes its observations.
- ``observed_at`` = ``fetched_at`` (in-situ measurement; no separate
  scene time like satellite's 0008).
- No ``updated_at``: rows are immutable once written.
- No ``raw_units`` column (same rationale as 0007/0008): units are
  encoded in the column names (``_pct`` / ``_c`` / ``_kg_ha``).
- Index is ``(farm_id, observed_at)`` ASC — Postgres scans it
  backward for the common ``ORDER BY observed_at DESC`` (keeps the
  model metadata and DDL byte-comparable for ``alembic check``).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "soil_observations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farm_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("soil_moisture_pct", sa.Float(), nullable=True),
        sa.Column("ph", sa.Float(), nullable=True),
        sa.Column("soil_temperature_c", sa.Float(), nullable=True),
        sa.Column("nitrogen_kg_ha", sa.Float(), nullable=True),
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
        "ix_soil_observations_farm_observed",
        "soil_observations",
        ["farm_id", "observed_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_soil_observations_farm_observed", table_name="soil_observations")
    op.drop_table("soil_observations")
