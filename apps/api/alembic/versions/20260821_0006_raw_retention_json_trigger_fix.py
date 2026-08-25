"""Fix PostgreSQL JSON comparison in the retention transition trigger.

Revision ID: 20260821_0006
Revises: 20260821_0005
"""

# pylint: disable=invalid-name,no-member,wrong-import-order

from alembic import op

revision = "20260821_0006"
down_revision = "20260821_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Compare JSON metadata through PostgreSQL's valid text equality."""
    op.execute(
        """CREATE OR REPLACE FUNCTION
        allow_weather_raw_retention_transition() RETURNS trigger AS $$
        BEGIN
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
             AND OLD.forecast_lead_seconds IS NOT DISTINCT FROM
                 NEW.forecast_lead_seconds
             AND OLD.valid_time IS NOT DISTINCT FROM NEW.valid_time
             AND OLD.metadata_json::text IS NOT DISTINCT FROM
                 NEW.metadata_json::text
          THEN RETURN NEW;
          END IF;
          RAISE EXCEPTION 'weather persistence is append-only'
            USING ERRCODE = 'P0001';
        END; $$ LANGUAGE plpgsql"""
    )


def downgrade() -> None:
    """Restore the pre-0006 function for a complete reviewed downgrade."""
    op.execute(
        """CREATE OR REPLACE FUNCTION
        allow_weather_raw_retention_transition() RETURNS trigger AS $$
        BEGIN
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
             AND OLD.forecast_lead_seconds IS NOT DISTINCT FROM
                 NEW.forecast_lead_seconds
             AND OLD.valid_time IS NOT DISTINCT FROM NEW.valid_time
             AND OLD.metadata_json IS NOT DISTINCT FROM NEW.metadata_json
          THEN RETURN NEW;
          END IF;
          RAISE EXCEPTION 'weather persistence is append-only'
            USING ERRCODE = 'P0001';
        END; $$ LANGUAGE plpgsql"""
    )
