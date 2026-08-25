"""Static migration contract tests when disposable PostgreSQL is unavailable."""

from pathlib import Path

_MIGRATION = (
    Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "20260821_0001_data_source_registry.py"
)
_RETENTION_CORRECTION = (
    Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "20260821_0005_retention_trigger_correction.py"
)
_JSON_CORRECTION = (
    Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "20260821_0006_raw_retention_json_trigger_fix.py"
)


def test_initial_migration_creates_all_phase_a_tables_and_downgrade() -> None:
    """Require explicit reviewed upgrade and reverse-order downgrade operations."""
    migration = _MIGRATION.read_text(encoding="utf-8")

    assert '"data_source_registry"' in migration
    assert '"data_source_schedule"' in migration
    assert '"data_source_run"' in migration
    assert 'op.drop_table("data_source_run")' in migration
    assert 'op.drop_table("data_source_schedule")' in migration
    assert 'op.drop_table("data_source_registry")' in migration


def test_initial_migration_enforces_lifecycle_and_health_values() -> None:
    """Keep lifecycle and operational health enumerations distinct in the DDL."""
    migration = _MIGRATION.read_text(encoding="utf-8")

    assert "ck_data_source_registry_status" in migration
    assert "ck_data_source_registry_health_status" in migration
    assert "ck_schedule_interval" in migration
    assert "ck_data_source_run_outcome" in migration


def test_retention_correction_has_table_safe_p0001_triggers() -> None:
    """Revision 0005 corrects trigger dispatch without editing 0004."""
    migration = _RETENTION_CORRECTION.read_text(encoding="utf-8")
    assert 'revision = "20260821_0005"' in migration
    assert 'down_revision = "20260821_0004"' in migration
    assert "TG_OP = 'UPDATE'" in migration
    assert "ERRCODE = 'P0001'" in migration
    assert "allow_weather_raw_retention_transition" in migration


def test_json_trigger_correction_uses_postgresql_valid_comparison() -> None:
    """0006 must not use PostgreSQL json equality."""
    migration = _JSON_CORRECTION.read_text(encoding="utf-8")
    upgrade = migration.split("def downgrade()", maxsplit=1)[0]
    assert 'revision = "20260821_0006"' in migration
    assert 'down_revision = "20260821_0005"' in migration
    assert "metadata_json::text IS NOT DISTINCT FROM" in upgrade
    assert "metadata_json IS NOT DISTINCT FROM" not in upgrade
