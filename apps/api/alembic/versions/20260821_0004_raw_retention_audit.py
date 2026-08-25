"""Add backend-owned raw retention classification and audit events.

Revision ID: 20260821_0004
Revises: 20260821_0003
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat

from alembic import op
import sqlalchemy as sa

revision = "20260821_0004"
down_revision = "20260821_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Expand raw rows, classify legacy rows explicitly, and add audit log."""
    columns = (
        sa.Column("retention_owner", sa.String(128)),
        sa.Column("retention_class", sa.String(32)),
        sa.Column("retention_period_seconds", sa.BigInteger()),
        sa.Column("acquired_at", sa.DateTime(timezone=True)),
        sa.Column("retention_due_at", sa.DateTime(timezone=True)),
        sa.Column("disposition_state", sa.String(24)),
        sa.Column("hold_state", sa.String(24)),
        sa.Column("hold_details", sa.JSON()),
        sa.Column("retention_policy_version", sa.String(64)),
    )
    for column in columns:
        op.add_column("weather_raw_artifact", column)

    # Preserve append-only provenance while permitting only an explicitly
    # authorized backend retention transition.  The application sets the
    # transaction-local GUC after its external IAM boundary has authorized it.
    op.execute(
        """CREATE OR REPLACE FUNCTION prevent_weather_mutation() RETURNS trigger
        AS $$
        BEGIN
          IF TG_TABLE_NAME = 'weather_raw_artifact'
             AND TG_OP = 'UPDATE'
             AND current_setting('everest.retention_transition', true) = 'on'
             AND OLD.source_id = NEW.source_id
             AND OLD.dataset = NEW.dataset
             AND OLD.object_reference = NEW.object_reference
             AND OLD.sha256 = NEW.sha256
             AND OLD.retrieved_at = NEW.retrieved_at
             AND OLD.data_format = NEW.data_format
             AND OLD.size_bytes = NEW.size_bytes
             AND OLD.metadata_json IS NOT DISTINCT FROM NEW.metadata_json
          THEN RETURN NEW;
          END IF;
          RAISE EXCEPTION 'weather persistence is append-only';
        END; $$ LANGUAGE plpgsql"""
    )

    # Existing rows have no defensible retention facts.  They are explicitly
    # marked legacy rather than receiving an invented owner, period, or due date.
    op.execute("SET LOCAL everest.retention_transition = 'on'")
    op.execute(
        """UPDATE weather_raw_artifact
        SET retention_class = 'legacy_unclassified',
            disposition_state = 'retained', hold_state = 'unknown',
            retention_policy_version = 'legacy-unclassified-v1'
        WHERE retention_class IS NULL"""
    )
    op.alter_column("weather_raw_artifact", "retention_class", nullable=False)
    op.alter_column("weather_raw_artifact", "disposition_state", nullable=False)
    op.alter_column("weather_raw_artifact", "hold_state", nullable=False)
    op.create_check_constraint(
        "ck_weather_raw_retention_class",
        "weather_raw_artifact",
        "retention_class IN ('operational_raw', 'failed_or_rejected_raw', "
        "'legacy_unclassified')",
    )
    op.create_check_constraint(
        "ck_weather_raw_retention_period",
        "weather_raw_artifact",
        "retention_class = 'legacy_unclassified' OR "
        "(retention_owner IS NOT NULL AND retention_period_seconds > 0 "
        "AND acquired_at IS NOT NULL AND retention_due_at IS NOT NULL "
        "AND retention_policy_version IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_weather_raw_disposition",
        "weather_raw_artifact",
        "disposition_state IN ('retained', 'approved', 'completed', 'blocked')",
    )
    op.create_check_constraint(
        "ck_weather_raw_hold",
        "weather_raw_artifact",
        "hold_state IN ('none', 'held', 'released', 'unknown') AND "
        "(hold_state <> 'held' OR hold_details IS NOT NULL)",
    )

    op.create_table(
        "raw_artifact_audit_event",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("actor_role", sa.String(32), nullable=False),
        sa.Column("correlation_id", sa.String(128), nullable=False),
        sa.Column(
            "event_time",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("audit_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            ["weather_raw_artifact.artifact_id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "event_type IN ('accepted', 'read', 'reused', 'integrity_failure', "
            "'access_change', 'hold_placed', 'hold_released', "
            "'disposition_approved', 'disposition_completed')",
            name="ck_raw_audit_event_type",
        ),
        sa.CheckConstraint(
            "result IN ('success', 'failure', 'blocked')",
            name="ck_raw_audit_result",
        ),
        sa.CheckConstraint(
            "actor_role IN ('service', 'operator', 'retention_authority', "
            "'audit_authority')",
            name="ck_raw_audit_actor_role",
        ),
        sa.CheckConstraint("length(actor_id) > 0", name="ck_raw_audit_actor"),
        sa.CheckConstraint(
            "octet_length(details::text) <= 4096",
            name="ck_raw_audit_details_size",
        ),
    )
    op.create_index(
        "ix_raw_audit_artifact_time",
        "raw_artifact_audit_event",
        ["artifact_id", "event_time"],
    )
    op.create_index(
        "ix_raw_audit_due", "raw_artifact_audit_event", ["audit_due_at"]
    )
    op.execute(
        """CREATE TRIGGER raw_artifact_audit_event_immutable
        BEFORE UPDATE OR DELETE ON raw_artifact_audit_event
        FOR EACH ROW EXECUTE FUNCTION prevent_weather_mutation()"""
    )


def downgrade() -> None:
    """Remove audit storage and retention columns."""
    op.drop_index("ix_raw_audit_due", table_name="raw_artifact_audit_event")
    op.drop_index(
        "ix_raw_audit_artifact_time", table_name="raw_artifact_audit_event"
    )
    op.drop_table("raw_artifact_audit_event")
    for name in (
        "ck_weather_raw_hold",
        "ck_weather_raw_disposition",
        "ck_weather_raw_retention_period",
        "ck_weather_raw_retention_class",
    ):
        op.drop_constraint(name, "weather_raw_artifact", type_="check")
    for name in (
        "retention_policy_version",
        "hold_details",
        "hold_state",
        "disposition_state",
        "retention_due_at",
        "acquired_at",
        "retention_period_seconds",
        "retention_class",
        "retention_owner",
    ):
        op.drop_column("weather_raw_artifact", name)
