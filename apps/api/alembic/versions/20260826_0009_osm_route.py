"""Create the OSM (Overpass) route and camp feature table (EV-OSM-002).

Revision ID: 20260826_0009
Revises: 20260825_0008
Create Date: 2026-08-26 00:00:00 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat,not-callable
# Alembic requires these revision variable names and operation proxies.

from alembic import op
import sqlalchemy as sa

revision = "20260826_0009"
down_revision = "20260825_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the idempotent OSM feature table for camps and route vertices."""
    op.create_table(
        "osm_feature",
        sa.Column("feature_id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=32), nullable=False),
        sa.Column("feature_kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128)),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("elevation_m", sa.Float()),
        sa.Column("osm_ref", sa.String(length=64)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "feature_kind IN ('camp', 'route')", name="ck_osm_feature_kind"
        ),
        sa.CheckConstraint(
            "sequence >= 0", name="ck_osm_feature_sequence"
        ),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90", name="ck_osm_latitude"
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180", name="ck_osm_longitude"
        ),
        sa.UniqueConstraint(
            "source_id",
            "dataset",
            "feature_kind",
            "name",
            "sequence",
            name="uq_osm_feature_identity",
        ),
    )
    op.create_index(
        "ix_osm_feature_kind", "osm_feature", ["feature_kind", "sequence"]
    )


def downgrade() -> None:
    """Drop the OSM feature table (additive reverse)."""
    op.drop_index("ix_osm_feature_kind", table_name="osm_feature")
    op.drop_table("osm_feature")
