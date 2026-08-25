"""Create Phase A data-source registry configuration tables.

Revision ID: 20260821_0001
Revises:
Create Date: 2026-08-21 00:00:00 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat
# Alembic requires these revision variable names and operation proxies.

from alembic import op
import sqlalchemy as sa

revision = "20260821_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create registry, schedule, and append-only run-history tables."""
    op.create_table(
        "data_source_registry",
        sa.Column("source_id", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("access_method", sa.String(length=128), nullable=False),
        sa.Column("endpoint", sa.Text()),
        sa.Column("format", sa.String(length=64)),
        sa.Column("update_frequency", sa.String(length=128)),
        sa.Column("spatial_resolution", sa.String(length=128)),
        sa.Column("temporal_resolution", sa.String(length=128)),
        sa.Column("coverage", sa.Text()),
        sa.Column("license", sa.Text()),
        sa.Column("commercial_allowed", sa.Boolean(), nullable=False),
        sa.Column("credentials_required", sa.Boolean(), nullable=False),
        sa.Column("credential_reference", sa.String(length=255)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_failure_at", sa.DateTime(timezone=True)),
        sa.Column("health_status", sa.String(length=32), nullable=False),
        sa.Column("metadata_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "status IN ('planned', 'configured', 'connected', "
            "'verified', 'degraded', 'disabled')",
            name="ck_data_source_registry_status",
        ),
        sa.CheckConstraint(
            "health_status IN ('unknown', 'healthy', 'stale', "
            "'failed', 'degraded', 'disabled')",
            name="ck_data_source_registry_health_status",
        ),
        sa.CheckConstraint(
            "metadata_version >= 1",
            name="ck_data_source_registry_metadata_version",
        ),
        sa.CheckConstraint(
            "(credential_reference IS NULL) OR credentials_required",
            name="ck_data_source_registry_credential_reference",
        ),
    )
    op.create_index(
        "ix_data_source_registry_status", "data_source_registry", ["status"]
    )
    op.create_index(
        "ix_data_source_registry_health_status",
        "data_source_registry",
        ["health_status"],
    )
    op.create_index(
        "ix_data_source_registry_last_success_at",
        "data_source_registry",
        ["last_success_at"],
    )
    op.create_table(
        "data_source_schedule",
        sa.Column("source_id", sa.String(length=128), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=False),
        sa.Column("retry_limit", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("initial_backoff_seconds", sa.Integer(), nullable=False),
        sa.Column("max_backoff_seconds", sa.Integer(), nullable=False),
        sa.Column("misfire_grace_seconds", sa.Integer(), nullable=False),
        sa.Column("max_concurrent_runs", sa.Integer(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["data_source_registry.source_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("interval_seconds > 0", name="ck_schedule_interval"),
        sa.CheckConstraint("retry_limit >= 0", name="ck_schedule_retry_limit"),
        sa.CheckConstraint("timeout_seconds > 0", name="ck_schedule_timeout"),
        sa.CheckConstraint(
            "initial_backoff_seconds >= 0", name="ck_schedule_backoff"
        ),
        sa.CheckConstraint(
            "max_backoff_seconds >= initial_backoff_seconds",
            name="ck_schedule_max_backoff",
        ),
        sa.CheckConstraint(
            "misfire_grace_seconds >= 0", name="ck_schedule_misfire"
        ),
        sa.CheckConstraint(
            "max_concurrent_runs > 0", name="ck_schedule_concurrency"
        ),
    )
    op.create_index(
        "ix_data_source_schedule_next_run_at",
        "data_source_schedule",
        ["next_run_at"],
    )
    op.create_table(
        "data_source_run",
        sa.Column("run_id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("failure_code", sa.String(length=128)),
        sa.Column("failure_detail", sa.String(length=1024)),
        sa.Column("content_hash", sa.String(length=128)),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["data_source_registry.source_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "outcome IN ('started', 'succeeded', 'failed', " "'skipped')",
            name="ck_data_source_run_outcome",
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_data_source_run_time_order",
        ),
        sa.CheckConstraint(
            "failure_detail IS NULL OR length(failure_detail) <= 1024",
            name="ck_data_source_run_failure_detail",
        ),
    )
    op.create_index(
        "ix_data_source_run_source_id", "data_source_run", ["source_id"]
    )


def downgrade() -> None:
    """Remove Phase A registry tables in dependency-safe reverse order."""
    op.drop_index("ix_data_source_run_source_id", table_name="data_source_run")
    op.drop_table("data_source_run")
    op.drop_index(
        "ix_data_source_schedule_next_run_at", table_name="data_source_schedule"
    )
    op.drop_table("data_source_schedule")
    op.drop_index(
        "ix_data_source_registry_last_success_at",
        table_name="data_source_registry",
    )
    op.drop_index(
        "ix_data_source_registry_health_status",
        table_name="data_source_registry",
    )
    op.drop_index(
        "ix_data_source_registry_status", table_name="data_source_registry"
    )
    op.drop_table("data_source_registry")
