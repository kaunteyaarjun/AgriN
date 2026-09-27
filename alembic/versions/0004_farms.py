"""farms table + PostGIS extension

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-27 18:05:00.000000

Hand-written (M013, standing rule: never trust autogenerate).
Decision D7: geometry stored as a real PostGIS column
``geometry(Geometry, 4326)`` (not JSONB). The extension is created
idempotently (``IF NOT EXISTS``) — on an existing volume the postgis
image's init scripts do not run, so the migration owns the CREATE.
Downgrade drops the table only; the extension stays (re-created
idempotently on the next upgrade).
"""

from collections.abc import Sequence
from typing import Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "farms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farmer_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("farmer_id", "name", name="farms_farmer_id_name_key"),
    )
    # GeoAlchemy2's create_table hook emitted the GIST spatial index.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("farms")
