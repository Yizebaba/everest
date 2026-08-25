"""Create append-only auxiliary raw provenance for weather records.

Revision ID: 20260821_0003
Revises: 20260821_0002
Create Date: 2026-08-21 00:00:02 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order
# Alembic requires these revision variable names and operation proxies.

from alembic import op
import sqlalchemy as sa

revision = "20260821_0003"
down_revision = "20260821_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the static-altitude-only, append-only provenance association."""
    op.create_table(
        "weather_record_raw_artifact",
        sa.Column("weather_record_id", sa.Uuid(), nullable=False),
        sa.Column("raw_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("provenance_role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["weather_record_id"],
            ["weather_record.record_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["raw_artifact_id"],
            ["weather_raw_artifact.artifact_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "weather_record_id", "raw_artifact_id", "provenance_role"
        ),
        sa.CheckConstraint(
            "provenance_role = 'static_altitude'",
            name="ck_weather_record_raw_artifact_role",
        ),
    )
    op.create_index(
        "ix_weather_record_raw_artifact_reverse",
        "weather_record_raw_artifact",
        ["raw_artifact_id", "weather_record_id"],
    )
    op.execute(
        """CREATE TRIGGER weather_record_raw_artifact_immutable
        BEFORE UPDATE OR DELETE ON weather_record_raw_artifact
        FOR EACH ROW EXECUTE FUNCTION prevent_weather_mutation()"""
    )


def downgrade() -> None:
    """Remove the provenance table while retaining pre-existing weather tables."""
    op.drop_index(
        "ix_weather_record_raw_artifact_reverse",
        table_name="weather_record_raw_artifact",
    )
    op.drop_table("weather_record_raw_artifact")
