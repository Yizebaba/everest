"""PostgreSQL persistence tests for Phase C weather ingestion semantics."""

# SQLAlchemy's dynamic ``func`` namespace is intentionally callable.
# pylint: disable=not-callable

from collections.abc import Callable
from datetime import UTC, datetime
import importlib.util

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session, sessionmaker

from weather_ingestion_contract import (
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

from everest_api.registry.models import DataSourceRegistryModel
from everest_api.raw_storage import RawStoragePolicy
from everest_api.weather.contracts import StaticAltitudeArtifactReference
from everest_api.weather.models import (
    RawArtifactAuditEventModel,
    WeatherRawArtifactModel,
    WeatherRecordModel,
    WeatherRecordRawArtifactModel,
)
from everest_api.weather.service import WeatherIngestionService

_RawFixtureWriter = Callable[[str, bytes], tuple[str, int]]


@pytest.mark.real_data
@pytest.mark.skipif(
    importlib.util.find_spec("eccodes") is None,
    reason="native ecCodes Python binding is unavailable in this environment",
)
def test_ecmwf_real_data_smoke_handoff_is_native_ready() -> None:
    """Require native ecCodes before a connector invokes this backend port.

    The connector-owned retrieval and parsing smoke remains in services/weather;
    this explicitly marked backend boundary test prevents a false real-data claim
    when the local native parser dependency is unavailable.
    """
    assert importlib.util.find_spec("eccodes") is not None


def _artifact(write_raw_fixture: _RawFixtureWriter) -> RawArtifactDescriptor:
    """Return a safe, provider-neutral descriptor matching the IFS handoff."""
    now = datetime(2026, 8, 20, tzinfo=UTC)
    object_reference = "sha256/a9/raw.grib2"
    sha256, size_bytes = write_raw_fixture(
        object_reference, b"synthetic-ifs-zero-hour-fixture\n"
    )
    return RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-oper",
        object_reference,
        sha256,
        now,
        "GRIB2",
        size_bytes,
        forecast_cycle=now,
        forecast_lead_seconds=0,
        valid_time=now,
        metadata={"parser_version": "test"},
    )


def _descriptor_with_metadata(
    metadata: dict[str, str | int],
) -> RawArtifactDescriptor:
    """Return one descriptor for backend consistency validation tests."""
    now = datetime(2026, 8, 20, tzinfo=UTC)
    return RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-oper",
        "sha256/a9/raw.grib2",
        "a" * 64,
        now,
        "GRIB2",
        16,
        metadata=metadata,
    )


@pytest.mark.parametrize("projected_hash", ["b" * 64, "invalid-hash"])
def test_projected_payload_hash_mismatch_is_rejected(
    projected_hash: str,
) -> None:
    """Reject malformed or divergent scalar payload hash projections."""
    descriptor = _descriptor_with_metadata(
        {"provider_payload_sha256": projected_hash}
    )
    with pytest.raises(ValueError, match="Projected payload SHA-256"):
        WeatherIngestionService._validate_artifact_descriptor(  # pylint: disable=protected-access
            descriptor
        )


def test_projected_payload_size_mismatch_is_rejected() -> None:
    """Reject a scalar payload-size projection that diverges from descriptor."""
    descriptor = _descriptor_with_metadata({"provider_payload_size_bytes": 15})
    with pytest.raises(ValueError, match="Projected payload size"):
        WeatherIngestionService._validate_artifact_descriptor(  # pylint: disable=protected-access
            descriptor
        )


def test_valid_projected_payload_descriptor_is_accepted() -> None:
    """Accept exact generic hash and byte-size projections."""
    descriptor = _descriptor_with_metadata(
        {
            "provider_payload_sha256": "a" * 64,
            "provider_payload_size_bytes": 16,
        }
    )
    WeatherIngestionService._validate_artifact_descriptor(  # pylint: disable=protected-access
        descriptor
    )


def _record() -> CanonicalRecordInput:
    """Return a minimal clean IFS canonical record with a provider grid key."""
    now = datetime(2026, 8, 20, tzinfo=UTC)
    return CanonicalRecordInput(
        "forecast",
        now,
        28.0,
        87.0,
        6008.05,
        "ifs:0p25:28.0:87.0",
        "ecmwf-ifs",
        "IFS",
        ("missing_value",),
        wind_speed=0.68,
        temperature=-3.61,
        forecast_cycle=now,
        forecast_lead_seconds=0,
        route_profile="SUMMIT",
    )


def _three_hour_artifact(
    write_raw_fixture: _RawFixtureWriter,
) -> RawArtifactDescriptor:
    """Return the factual retained IFS three-hour dynamic artifact descriptor."""
    cycle = datetime(2026, 8, 20, tzinfo=UTC)
    object_reference = "sha256/7d4b/dynamic-3h.grib2"
    sha256, size_bytes = write_raw_fixture(
        object_reference, b"synthetic-ifs-three-hour-dynamic-fixture\n"
    )
    return RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-oper",
        object_reference,
        sha256,
        cycle,
        "GRIB2",
        size_bytes,
        forecast_cycle=cycle,
        forecast_lead_seconds=10800,
        valid_time=datetime(2026, 8, 20, 3, tzinfo=UTC),
        metadata={"model": "IFS"},
    )


def _static_altitude(
    write_raw_fixture: _RawFixtureWriter,
) -> StaticAltitudeArtifactReference:
    """Return the factual same-cycle step-zero surface-z artifact descriptor."""
    cycle = datetime(2026, 8, 20, tzinfo=UTC)
    object_reference = "sha256/529c/static-z-0h.grib2"
    sha256, size_bytes = write_raw_fixture(
        object_reference, b"synthetic-ifs-static-altitude-fixture\n"
    )
    return StaticAltitudeArtifactReference(
        RawArtifactDescriptor(
            "ecmwf-ifs",
            "ifs-oper",
            object_reference,
            sha256,
            cycle,
            "GRIB2",
            size_bytes,
            forecast_cycle=cycle,
            forecast_lead_seconds=0,
            valid_time=cycle,
            metadata={
                "parameter": "z",
                "level_type": "sfc",
                "step_seconds": 0,
                "spatial_key": "ifs:0p25:28.0:87.0",
                "model": "IFS",
            },
        )
    )


def _three_hour_record() -> CanonicalRecordInput:
    """Return the factual canonical 3-hour forecast with static-z altitude."""
    cycle = datetime(2026, 8, 20, tzinfo=UTC)
    return CanonicalRecordInput(
        "forecast",
        datetime(2026, 8, 20, 3, tzinfo=UTC),
        28.0,
        87.0,
        6008.053905863623,
        "ifs:0p25:28.0:87.0",
        "ecmwf-ifs",
        "IFS",
        ("missing_value",),
        wind_speed=0.8584101751271469,
        wind_direction=171.95415714345518,
        temperature=-1.3635162353515398,
        precipitation=0.003814697265625,
        forecast_cycle=cycle,
        forecast_lead_seconds=10800,
        route_profile="SUMMIT",
    )


def _seed(session: Session) -> None:
    """Seed only the registered approved IFS source required by the FK."""
    session.add(
        DataSourceRegistryModel(
            source_id="ecmwf-ifs",
            name="IFS",
            provider="ECMWF",
            category="forecast",
            status="configured",
            access_method="connector",
            commercial_allowed=False,
            credentials_required=False,
            health_status="unknown",
            metadata_version=1,
        )
    )
    session.commit()


def test_raw_survives_canonical_failure_and_never_verifies(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """Raw retention commits even when canonical validation/insert fails later."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    bad = _record().__dict__.copy()
    bad["source"] = "wrong-source"
    with pytest.raises(ValueError):
        WeatherIngestionService(factory, raw_storage_policy).ingest(
            _artifact(write_raw_fixture), [CanonicalRecordInput(**bad)]
        )
    with factory() as session:
        assert (
            session.scalar(  # pylint: disable=not-callable
                select(func.count()).select_from(WeatherRawArtifactModel)
            )
            == 1
        )
        assert (
            session.scalar(  # pylint: disable=not-callable
                select(func.count()).select_from(WeatherRecordModel)
            )
            == 0
        )
        assert (
            session.get(DataSourceRegistryModel, "ecmwf-ifs").status
            == "configured"
        )


def test_accepted_raw_has_classification_and_append_only_audit(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """New acceptance persists approved retention facts and an audit event."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    WeatherIngestionService(factory, raw_storage_policy).ingest(
        _artifact(write_raw_fixture), [_record()]
    )
    with factory() as session:
        artifact = session.scalar(select(WeatherRawArtifactModel))
        event = session.scalar(select(RawArtifactAuditEventModel))
        assert artifact.retention_class == "operational_raw"
        assert artifact.retention_owner == "Everest Manager"
        assert artifact.retention_due_at is not None
        assert event.event_type == "accepted"
        assert event.result == "success"


def test_audit_rows_and_all_weather_tables_fail_with_p0001(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """0005 dispatches immutable tables to SQLSTATE P0001, never 42703."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    service = WeatherIngestionService(factory, raw_storage_policy)
    service.ingest(_artifact(write_raw_fixture), [_record()])
    with factory() as session:
        raw = session.scalar(select(WeatherRawArtifactModel))
        event = session.scalar(select(RawArtifactAuditEventModel))
        event.result = "failure"
        with pytest.raises(ProgrammingError) as error:
            session.commit()
        assert getattr(error.value.orig, "sqlstate", None) == "P0001"
        session.rollback()
        with pytest.raises(ProgrammingError) as error:
            session.execute(
                text("UPDATE weather_record SET temperature = temperature")
            )
        assert getattr(error.value.orig, "sqlstate", None) == "P0001"
        session.rollback()
        with pytest.raises(ProgrammingError) as error:
            raw.disposition_state = "blocked"
            session.flush()
        assert getattr(error.value.orig, "sqlstate", None) == "P0001"
        session.rollback()


def test_disposition_requires_expiry_and_prior_approval(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """Completion cannot bypass expiry, approval, or the persisted state."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    service = WeatherIngestionService(factory, raw_storage_policy)
    artifact_id = service.ingest(_artifact(write_raw_fixture), [_record()])
    with pytest.raises(ValueError, match="requires expiry"):
        service.transition_retention_state(
            artifact_id,
            disposition_state="approved",
            actor_id="retention-owner",
            actor_role="retention_authority",
        )
    with factory() as session:
        session.execute(text("SET LOCAL everest.retention_transition = 'on'"))
        session.execute(
            text(
                "UPDATE weather_raw_artifact SET retention_due_at = "
                "CURRENT_TIMESTAMP - INTERVAL '1 second'"
            )
        )
        session.commit()
    with pytest.raises(ValueError, match="prior approval"):
        service.transition_retention_state(
            artifact_id,
            disposition_state="completed",
            actor_id="retention-owner",
            actor_role="retention_authority",
        )
    service.transition_retention_state(
        artifact_id,
        disposition_state="approved",
        actor_id="retention-owner",
        actor_role="retention_authority",
    )
    service.transition_retention_state(
        artifact_id,
        disposition_state="completed",
        actor_id="retention-owner",
        actor_role="retention_authority",
    )


def test_hold_release_and_completion_cannot_be_combined(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """One call cannot manufacture a release and disposition completion."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    service = WeatherIngestionService(factory, raw_storage_policy)
    artifact_id = service.ingest(_artifact(write_raw_fixture), [_record()])
    with pytest.raises(ValueError, match="cannot be combined"):
        service.transition_retention_state(
            artifact_id,
            hold_state="released",
            disposition_state="completed",
            actor_id="retention-owner",
            actor_role="retention_authority",
        )


def test_migration_creates_weather_provenance_table(
    migrated_postgres_engine: object,
) -> None:
    """The post-0002 migration creates the internal provenance association."""
    assert (
        "weather_record_raw_artifact"
        in inspect(migrated_postgres_engine).get_table_names()
    )


def test_ingestion_deduplicates_and_weather_rows_are_immutable(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """The source hash and canonical identity are unique and DB rows cannot mutate."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    service = WeatherIngestionService(factory, raw_storage_policy)
    service.ingest(_artifact(write_raw_fixture), [_record()])
    with factory() as session:
        row = session.scalar(select(WeatherRecordModel))
        row.temperature = 1.0
        with pytest.raises(ProgrammingError) as error:
            session.commit()
        assert getattr(error.value.orig, "sqlstate", None) == "P0001"
        session.rollback()


def test_static_altitude_provenance_is_factual_and_idempotent(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """Persist a distinct 0-hour surface-z artifact only as auxiliary provenance."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    service = WeatherIngestionService(factory, raw_storage_policy)
    dynamic = _three_hour_artifact(write_raw_fixture)
    static_altitude = _static_altitude(write_raw_fixture)
    record = _three_hour_record()
    service.ingest(dynamic, [record], static_altitude)
    service.ingest(dynamic, [record], static_altitude)
    with factory() as session:
        persisted = session.scalar(select(WeatherRecordModel))
        association = session.scalar(select(WeatherRecordRawArtifactModel))
        assert persisted.raw_artifact_id != association.raw_artifact_id
        assert association.provenance_role == "static_altitude"
        assert (
            session.scalar(
                select(func.count()).select_from(WeatherRecordRawArtifactModel)
            )
            == 1
        )
        association.provenance_role = "other"
        with pytest.raises(ProgrammingError) as error:
            session.commit()
        assert getattr(error.value.orig, "sqlstate", None) == "P0001"
        session.rollback()


def test_static_altitude_requires_step_zero_surface_z_metadata(
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """Reject unsupported auxiliary evidence before it can become provenance."""
    descriptor = _static_altitude(write_raw_fixture).descriptor
    invalid = RawArtifactDescriptor(
        **{**descriptor.__dict__, "metadata": {"parameter": "z"}}
    )
    with pytest.raises(ValueError, match="step-zero surface z"):
        WeatherIngestionService._validate_static_altitude_descriptor(  # pylint: disable=protected-access
            _three_hour_artifact(write_raw_fixture),
            invalid,
            [_three_hour_record()],
        )


def test_auxiliary_raw_artifact_survives_canonical_rollback(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """Retain both facts if a later canonical-record validation fails."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        _seed(session)
    invalid = _three_hour_record().__dict__.copy()
    invalid["source"] = "incorrect-source"
    with pytest.raises(ValueError, match="Canonical record source"):
        WeatherIngestionService(factory, raw_storage_policy).ingest(
            _three_hour_artifact(write_raw_fixture),
            [CanonicalRecordInput(**invalid)],
            _static_altitude(write_raw_fixture),
        )
    with factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(WeatherRawArtifactModel)
            )
            == 2
        )
        assert (
            session.scalar(select(func.count()).select_from(WeatherRecordModel))
            == 0
        )
        assert (
            session.scalar(
                select(func.count()).select_from(WeatherRecordRawArtifactModel)
            )
            == 0
        )
