"""Create canonical terrain, observation, and satellite tables (ADR-019).

Revision ID: 20260824_0007
Revises: 20260821_0006
Create Date: 2026-08-24 00:00:00 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat
# Alembic requires these revision variable names and operation proxies.

from alembic import op
import sqlalchemy as sa

revision = "20260824_0007"
down_revision = "20260821_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create append-only canonical source tables for the three ADR-019 lines."""
    op.create_table(
        "terrain_tile",
        sa.Column("tile_id", sa.Uuid(), primary_key=True),
        sa.Column("tile_name", sa.String(length=128), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=32), nullable=False),
        sa.Column("crs", sa.String(length=32), nullable=False),
        sa.Column("west", sa.Float(), nullable=False),
        sa.Column("south", sa.Float(), nullable=False),
        sa.Column("east", sa.Float(), nullable=False),
        sa.Column("north", sa.Float(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("resolution_degrees", sa.Float(), nullable=False),
        sa.Column("min_elevation", sa.Float(), nullable=False),
        sa.Column("max_elevation", sa.Float(), nullable=False),
        sa.Column("object_reference", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "west < east AND south < north", name="ck_terrain_bounds"
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_terrain_size"),
        sa.CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_terrain_sha256"
        ),
        sa.UniqueConstraint("tile_name", "sha256", name="uq_terrain_tile_hash"),
    )
    op.create_index(
        "ix_terrain_bounds", "terrain_tile", ["west", "south", "east", "north"]
    )

    op.create_table(
        "aws_observation",
        sa.Column("observation_id", sa.Uuid(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("station", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=32), nullable=False),
        sa.Column("record_type", sa.String(length=16), nullable=False),
        sa.Column("temperature_c", sa.Float()),
        sa.Column("relative_humidity", sa.Float()),
        sa.Column("precipitation", sa.Float()),
        sa.Column("weather_code", sa.String(length=8)),
        sa.Column("missing", sa.Boolean(), nullable=False),
        sa.Column("quality_flags", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "station IN ('Base Camp', 'Camp 2', 'South Col')",
            name="ck_aws_observation_station",
        ),
        sa.CheckConstraint(
            "record_type = 'observation'", name="ck_aws_observation_type"
        ),
        sa.CheckConstraint(
            "temperature_c IS NULL OR (temperature_c >= -60 AND temperature_c <= 60)",
            name="ck_aws_observation_temperature",
        ),
        sa.CheckConstraint(
            "relative_humidity IS NULL OR (relative_humidity >= 0 AND "
            "relative_humidity <= 100)",
            name="ck_aws_observation_humidity",
        ),
        sa.CheckConstraint(
            "precipitation IS NULL OR precipitation >= 0",
            name="ck_aws_observation_precipitation",
        ),
        sa.UniqueConstraint(
            "source_id",
            "dataset",
            "timestamp",
            "station",
            name="uq_aws_observation_identity",
        ),
    )
    op.create_index(
        "ix_aws_observation_time", "aws_observation", ["station", "timestamp"]
    )

    op.create_table(
        "satellite_segment",
        sa.Column("segment_id", sa.Uuid(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=32), nullable=False),
        sa.Column("band", sa.Integer(), nullable=False),
        sa.Column("segment", sa.Integer(), nullable=False),
        sa.Column("satellite_name", sa.String(length=16), nullable=False),
        sa.Column("observation_area", sa.String(length=8), nullable=False),
        sa.Column("object_reference", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "band >= 1 AND band <= 16", name="ck_satellite_band"
        ),
        sa.CheckConstraint(
            "segment >= 1 AND segment <= 10", name="ck_satellite_segment"
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_satellite_size"),
        sa.CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_satellite_sha256"
        ),
        sa.UniqueConstraint(
            "source_id",
            "dataset",
            "timestamp",
            "band",
            "segment",
            name="uq_satellite_segment_identity",
        ),
    )
    op.create_index(
        "ix_satellite_segment_time", "satellite_segment", ["timestamp", "band"]
    )


def downgrade() -> None:
    """Drop the three source tables in reverse order."""
    op.drop_index("ix_satellite_segment_time", table_name="satellite_segment")
    op.drop_table("satellite_segment")
    op.drop_index("ix_aws_observation_time", table_name="aws_observation")
    op.drop_table("aws_observation")
    op.drop_index("ix_terrain_bounds", table_name="terrain_tile")
    op.drop_table("terrain_tile")
