"""plots table (sub-field boundaries of a farm)

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-27 13:40:00.000000

Hand-written (M015, standing rule: never trust autogenerate). Same D7
geometry treatment as ``farms``. The PostGIS extension is owned by
revision 0004 (always applied first in the chain), so this migration
does not re-create it. ``ix_plots_farm_id`` supports M016's list-by-farm
queries; GeoAlchemy2's create_table hook emits the GIST spatial index.
Downgrade drops the table (indexes go with it).
"""

from collections.abc import Sequence
from typing import Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "plots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farm_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("area_hectares", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "geo",
            geoalchemy2.types.Geometry(geometry_type="Geometry", srid=4326),
            nullable=True,
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("farm_id", "name", name="plots_farm_id_name_key"),
    )
    op.create_index(op.f("ix_plots_farm_id"), "plots", ["farm_id"], unique=False)
    # GeoAlchemy2's create_table hook emitted the GIST spatial index.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("plots")
