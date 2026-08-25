"""Add B2 exact-version storage projection and append-only events (DB-04).

Revision ID: 20260825_0008
Revises: 20260824_0007
Create Date: 2026-08-25 00:00:00 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat,not-callable
# Alembic requires these revision variable names and operation proxies.

from alembic import op
import sqlalchemy as sa

revision = "20260825_0008"
down_revision = "20260824_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the exact-version storage mapping and append-only event tables."""
    op.create_table(
        "raw_artifact_storage_version",
        sa.Column("storage_version_id", sa.Uuid(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.Uuid(),
            sa.ForeignKey(
                "weather_raw_artifact.artifact_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("bucket_name", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("version_id", sa.String(length=255), nullable=False),
        sa.Column("etag", sa.String(length=255), nullable=True),
        sa.Column("checksum_algorithm", sa.String(length=32), nullable=True),
        sa.Column("checksum_value", sa.String(length=128), nullable=True),
        sa.Column("kms_key_arn", sa.String(length=512), nullable=False),
        sa.Column(
            "observed_retention_mode",
            sa.String(length=16),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column(
            "observed_retain_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "observed_legal_hold",
            sa.String(length=16),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column(
            "storage_state",
            sa.String(length=48),
            nullable=False,
            server_default="storage_unclassified",
        ),
        sa.Column(
            "first_verified_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "last_verified_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "bucket_name <> '' AND object_key <> '' AND version_id <> ''",
            name="ck_storage_identity_nonempty",
        ),
        sa.CheckConstraint(
            "observed_retention_mode IN "
            "('GOVERNANCE', 'COMPLIANCE', 'UNKNOWN')",
            name="ck_storage_retention_mode",
        ),
        sa.CheckConstraint(
            "observed_legal_hold IN ('ON', 'OFF', 'UNKNOWN')",
            name="ck_storage_legal_hold",
        ),
        sa.CheckConstraint(
            "NOT (observed_retention_mode <> 'UNKNOWN' AND "
            "observed_retain_until IS NULL)",
            name="ck_storage_retain_until_required",
        ),
        sa.CheckConstraint(
            "(checksum_algorithm IS NULL AND checksum_value IS NULL) OR "
            "(checksum_algorithm IS NOT NULL AND checksum_value IS NOT NULL)",
            name="ck_storage_checksum_pair",
        ),
        sa.UniqueConstraint(
            "bucket_name",
            "object_key",
            "version_id",
            name="uq_storage_exact_version",
        ),
    )
    op.create_index(
        "ix_storage_artifact_state",
        "raw_artifact_storage_version",
        ["artifact_id", "storage_state"],
    )
    op.create_index(
        "ix_storage_last_verified",
        "raw_artifact_storage_version",
        ["last_verified_at"],
    )
    op.create_index(
        "ix_storage_retain_until",
        "raw_artifact_storage_version",
        ["observed_retain_until"],
    )

    op.create_table(
        "raw_artifact_storage_event",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column(
            "storage_version_id",
            sa.Uuid(),
            sa.ForeignKey(
                "raw_artifact_storage_version.storage_version_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("bucket_name", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("version_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column(
            "event_time",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("details", sa.String(length=1024), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("s3_request_id", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('version_observed','default_lock_verified',"
            "'extension_requested','extension_succeeded','extension_blocked',"
            "'hold_requested','hold_succeeded','hold_released','hold_blocked',"
            "'drift_detected','kms_access_blocked','lock_failed',"
            "'disposition_requested','disposition_approved',"
            "'delete_requested','delete_succeeded','delete_blocked',"
            "'version_absence_verified','delete_marker_observed')",
            name="ck_storage_event_type",
        ),
        sa.CheckConstraint(
            "result IN ('success', 'failure', 'blocked', 'skipped')",
            name="ck_storage_event_result",
        ),
        sa.CheckConstraint(
            "bucket_name <> '' AND object_key <> '' AND version_id <> ''",
            name="ck_storage_event_identity_nonempty",
        ),
    )
    op.create_index(
        "ix_storage_event_version",
        "raw_artifact_storage_event",
        ["storage_version_id", "event_time"],
    )
    op.create_index(
        "ix_storage_event_type",
        "raw_artifact_storage_event",
        ["event_type", "event_time"],
    )
    op.execute(
        """CREATE TRIGGER raw_artifact_storage_event_immutable
        BEFORE UPDATE OR DELETE ON raw_artifact_storage_event
        FOR EACH ROW EXECUTE FUNCTION prevent_weather_mutation()"""
    )


def downgrade() -> None:
    """Drop the B2 storage projection tables (additive reverse)."""
    op.execute(
        """DROP TRIGGER IF EXISTS raw_artifact_storage_event_immutable
        ON raw_artifact_storage_event"""
    )
    op.drop_table("raw_artifact_storage_event")
    op.drop_table("raw_artifact_storage_version")
