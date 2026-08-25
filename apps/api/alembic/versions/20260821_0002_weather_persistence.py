"""Create immutable Phase C weather raw and canonical record tables.

Revision ID: 20260821_0002
Revises: 20260821_0001
Create Date: 2026-08-21 00:00:01 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat
# Alembic requires these revision variable names and operation proxies.

from alembic import op
import sqlalchemy as sa

revision = "20260821_0002"
down_revision = "20260821_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create only raw-artifact and append-only canonical-record persistence."""
    op.create_table(
        "weather_raw_artifact",
        sa.Column("artifact_id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("object_reference", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_format", sa.String(length=32), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("forecast_cycle", sa.DateTime(timezone=True)),
        sa.Column("forecast_lead_seconds", sa.Integer()),
        sa.Column("valid_time", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["data_source_registry.source_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_weather_raw_size"),
        sa.CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_weather_raw_sha256"
        ),
        sa.UniqueConstraint(
            "source_id", "sha256", name="uq_weather_raw_source_hash"
        ),
    )
    op.create_index(
        "ix_weather_raw_source_cycle",
        "weather_raw_artifact",
        ["source_id", "forecast_cycle"],
    )
    op.create_table(
        "weather_record",
        sa.Column("record_id", sa.Uuid(), primary_key=True),
        sa.Column("raw_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("record_type", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=False),
        sa.Column("spatial_key", sa.String(length=255), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("forecast_cycle", sa.DateTime(timezone=True)),
        sa.Column("forecast_lead_seconds", sa.Integer()),
        sa.Column("route_profile", sa.String(length=16)),
        sa.Column("quality_flags", sa.JSON(), nullable=False),
        sa.Column("wind_speed", sa.Float()),
        sa.Column("wind_direction", sa.Float()),
        sa.Column("temperature", sa.Float()),
        sa.Column("precipitation", sa.Float()),
        sa.Column("visibility", sa.Float()),
        sa.Column("pressure", sa.Float()),
        sa.Column("relative_humidity", sa.Float()),
        sa.Column("dew_point", sa.Float()),
        sa.Column("cloud_cover", sa.Float()),
        sa.Column("cloud_base", sa.Float()),
        sa.Column("cloud_top", sa.Float()),
        sa.Column("snowfall", sa.Float()),
        sa.Column("gust_speed", sa.Float()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["raw_artifact_id"],
            ["weather_raw_artifact.artifact_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "record_type IN ('forecast', 'observation', 'satellite', 'derived')",
            name="ck_weather_record_type",
        ),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90", name="ck_weather_latitude"
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_weather_longitude",
        ),
        sa.CheckConstraint(
            "wind_speed IS NULL OR wind_speed >= 0",
            name="ck_weather_wind_speed",
        ),
        sa.CheckConstraint(
            "wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction < 360)",
            name="ck_weather_wind_direction",
        ),
        sa.CheckConstraint(
            "precipitation IS NULL OR precipitation >= 0",
            name="ck_weather_precipitation",
        ),
        sa.CheckConstraint(
            "visibility IS NULL OR visibility >= 0",
            name="ck_weather_visibility",
        ),
        sa.CheckConstraint(
            "route_profile IS NULL OR route_profile IN ('EBC', 'C1', 'C2', 'C3', 'C4', 'SUMMIT')",
            name="ck_weather_route_profile",
        ),
    )
    op.create_index(
        "uq_weather_record_identity",
        "weather_record",
        [
            "source_id",
            "dataset",
            "timestamp",
            "spatial_key",
            "forecast_cycle",
            "forecast_lead_seconds",
        ],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
    op.create_index(
        "ix_weather_record_query",
        "weather_record",
        ["source_id", "timestamp", "forecast_cycle"],
    )
    op.create_index(
        "ix_weather_record_profile",
        "weather_record",
        ["route_profile", "timestamp"],
    )
    op.execute(
        """
        CREATE FUNCTION prevent_weather_mutation() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'weather persistence is append-only'; END; $$
        LANGUAGE plpgsql
    """
    )
    for table in ("weather_raw_artifact", "weather_record"):
        op.execute(
            f"""CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION prevent_weather_mutation()"""
        )


def downgrade() -> None:
    """Remove Phase C weather persistence in dependency-safe reverse order."""
    op.drop_index("ix_weather_record_profile", table_name="weather_record")
    op.drop_index("ix_weather_record_query", table_name="weather_record")
    op.drop_index("uq_weather_record_identity", table_name="weather_record")
    op.drop_table("weather_record")
    op.drop_index(
        "ix_weather_raw_source_cycle", table_name="weather_raw_artifact"
    )
    op.drop_table("weather_raw_artifact")
    op.execute("DROP FUNCTION prevent_weather_mutation()")
