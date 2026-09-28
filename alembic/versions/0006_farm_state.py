"""farm state: plot_states + farm_signal_caches

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-28 09:00:00.000000

Hand-written (M018, standing rule: never trust autogenerate; cross-
checked with ``alembic check`` after applying). Two tables:

- ``plot_states`` — crop facts per plot (``plot_id`` is PK + FK to
  ``plots`` with CASCADE, which is what enforces the 1:1). The stage
  CHECK mirrors ``GROWTH_STAGES`` in ``src/models/plot_state.py``.
- ``farm_signal_caches`` — latest weather/satellite/soil snapshot per
  farm (JSONB document; PK + FK to ``farms`` with CASCADE).

No GIN index on ``signals`` (PK point lookups only — re-check M056).
Downgrade drops both tables (children before parents is irrelevant
here: both are leaf tables).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GROWTH_STAGES = (
    "germination",
    "vegetative",
    "flowering",
    "fruiting",
    "maturation",
    "harvest",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "plot_states",
        sa.Column("plot_id", sa.UUID(), nullable=False),
        sa.Column("crop", sa.String(length=80), nullable=False),
        sa.Column("growth_stage", sa.String(length=40), nullable=False),
        sa.Column("planted_on", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plot_id"], ["plots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plot_id"),
        sa.CheckConstraint(
            "growth_stage IN ({})".format(", ".join(f"'{stage}'" for stage in GROWTH_STAGES)),
            name="plot_states_growth_stage_check",
        ),
    )

    op.create_table(
        "farm_signal_caches",
        sa.Column("farm_id", sa.UUID(), nullable=False),
        sa.Column(
            "signals",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "refreshed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("farm_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("farm_signal_caches")
    op.drop_table("plot_states")
