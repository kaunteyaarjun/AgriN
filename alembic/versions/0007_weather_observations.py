"""weather observations history table

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-28 12:00:00.000000

Hand-written (M023, standing rule: never trust autogenerate; cross-
checked with ``alembic check`` after applying). Append-only history
of provider weather readings per farm — the cache (0006) holds the
latest snapshot, this table holds everything that was ever fetched.

- ``farm_id`` FK CASCADE: deleting a farm removes its observations.
- No ``updated_at``: rows are immutable once written.
- Index is ``(farm_id, observed_at)`` ASC — Postgres scans it
  backward for the common ``ORDER BY observed_at DESC`` (keeps the
  model metadata and DDL byte-comparable for ``alembic check``).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "weather_observations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farm_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("humidity_pct", sa.Float(), nullable=True),
        sa.Column("rainfall_mm_24h", sa.Float(), nullable=True),
        sa.Column("wind_speed_kmh", sa.Float(), nullable=True),
        sa.Column("condition", sa.String(length=40), nullable=True),
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
        "ix_weather_observations_farm_observed",
        "weather_observations",
        ["farm_id", "observed_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_weather_observations_farm_observed", table_name="weather_observations")
    op.drop_table("weather_observations")
