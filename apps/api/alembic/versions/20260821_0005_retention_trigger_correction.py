"""Correct retention trigger dispatch without rewriting executed revision 0004.

Revision ID: 20260821_0005
Revises: 20260821_0004
"""

# pylint: disable=invalid-name,no-member,wrong-import-order

from alembic import op

revision = "20260821_0005"
down_revision = "20260821_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Use table-specific retention and generic immutable trigger functions."""
    op.execute(
        """CREATE OR REPLACE FUNCTION prevent_weather_mutation() RETURNS trigger
        AS $$ BEGIN
          RAISE EXCEPTION 'weather persistence is append-only' USING ERRCODE = 'P0001';
        END; $$ LANGUAGE plpgsql"""
    )
    op.execute(
        """CREATE FUNCTION allow_weather_raw_retention_transition() RETURNS trigger
        AS $$ BEGIN
          IF TG_OP = 'UPDATE'
             AND current_setting('everest.retention_transition', true) = 'on'
             AND OLD.source_id = NEW.source_id
             AND OLD.dataset = NEW.dataset
             AND OLD.object_reference = NEW.object_reference
             AND OLD.sha256 = NEW.sha256
             AND OLD.retrieved_at = NEW.retrieved_at
             AND OLD.data_format = NEW.data_format
             AND OLD.size_bytes = NEW.size_bytes
             AND OLD.source_url IS NOT DISTINCT FROM NEW.source_url
             AND OLD.forecast_cycle IS NOT DISTINCT FROM NEW.forecast_cycle
             AND OLD.forecast_lead_seconds IS NOT DISTINCT FROM NEW.forecast_lead_seconds
             AND OLD.valid_time IS NOT DISTINCT FROM NEW.valid_time
             AND OLD.metadata_json IS NOT DISTINCT FROM NEW.metadata_json
          THEN RETURN NEW;
          END IF;
          RAISE EXCEPTION 'weather persistence is append-only'
            USING ERRCODE = 'P0001';
        END; $$ LANGUAGE plpgsql"""
    )
    op.execute(
        """CREATE FUNCTION prevent_weather_raw_delete() RETURNS trigger
        AS $$ BEGIN
          RAISE EXCEPTION 'weather persistence is append-only'
            USING ERRCODE = 'P0001';
        END; $$ LANGUAGE plpgsql"""
    )
    op.execute(
        """CREATE FUNCTION validate_raw_audit_details() RETURNS trigger
        AS $$ DECLARE item jsonb; BEGIN
          IF jsonb_typeof(NEW.details::jsonb) <> 'object' THEN
            RAISE EXCEPTION 'audit details must be a JSON object'
              USING ERRCODE = 'P0001';
          END IF;
          IF octet_length(NEW.details::text) > 4096 THEN
            RAISE EXCEPTION 'audit details exceed bound' USING ERRCODE = 'P0001';
          END IF;
          FOR item IN SELECT value FROM jsonb_each(NEW.details::jsonb) LOOP
            IF jsonb_typeof(item) NOT IN ('string', 'number', 'boolean', 'null')
            THEN RAISE EXCEPTION 'audit details must contain scalars'
              USING ERRCODE = 'P0001'; END IF;
          END LOOP;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql"""
    )
    op.execute(
        """CREATE TRIGGER raw_artifact_audit_details_valid
        BEFORE INSERT ON raw_artifact_audit_event FOR EACH ROW
        EXECUTE FUNCTION validate_raw_audit_details()"""
    )
    op.execute(
        "DROP TRIGGER weather_raw_artifact_immutable ON weather_raw_artifact"
    )
    op.execute(
        """CREATE TRIGGER weather_raw_artifact_immutable
        BEFORE UPDATE ON weather_raw_artifact FOR EACH ROW
        EXECUTE FUNCTION allow_weather_raw_retention_transition()"""
    )
    op.execute(
        """CREATE TRIGGER weather_raw_artifact_delete_immutable
        BEFORE DELETE ON weather_raw_artifact FOR EACH ROW
        EXECUTE FUNCTION prevent_weather_raw_delete()"""
    )


def downgrade() -> None:
    """Restore revision-0004 trigger behavior when downgrading."""
    op.execute(
        "DROP TRIGGER raw_artifact_audit_details_valid "
        "ON raw_artifact_audit_event"
    )
    op.execute("DROP FUNCTION validate_raw_audit_details()")
    op.execute(
        "DROP TRIGGER weather_raw_artifact_immutable ON weather_raw_artifact"
    )
    op.execute(
        "DROP TRIGGER weather_raw_artifact_delete_immutable "
        "ON weather_raw_artifact"
    )
    op.execute(
        """CREATE TRIGGER weather_raw_artifact_immutable
        BEFORE UPDATE OR DELETE ON weather_raw_artifact FOR EACH ROW
        EXECUTE FUNCTION prevent_weather_mutation()"""
    )
    op.execute("DROP FUNCTION prevent_weather_raw_delete()")
    op.execute("DROP FUNCTION allow_weather_raw_retention_transition()")
