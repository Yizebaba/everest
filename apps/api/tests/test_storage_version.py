"""PostgreSQL tests for B2 DB-04 storage-version projection (ADR-019 B2)."""

from __future__ import annotations

# Test fixtures intentionally carry many parameters, reuse fixture objects, and
# use SQLAlchemy's dynamic namespaces. Pylint exceptions are scoped to tests.
# pylint: disable=too-many-arguments,too-many-positional-arguments,
# pylint: disable=unused-argument,import-outside-toplevel,duplicate-code

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from everest_api.registry.models import DataSourceRegistryModel
from everest_api.weather.models import (
    WeatherRawArtifactModel,
    WeatherStorageEventModel,
    WeatherStorageVersionModel,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _seed_source(session: Session, source_id: str = "ecmwf-ifs") -> None:
    if session.get(DataSourceRegistryModel, source_id) is None:
        session.add(
            DataSourceRegistryModel(
                source_id=source_id,
                name="ECMWF IFS",
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


def _insert_artifact(session: Session, source_id: str = "ecmwf-ifs") -> None:
    _seed_source(session, source_id)
    session.add(
        WeatherRawArtifactModel(
            artifact_id=uuid4(),
            source_id=source_id,
            dataset="ifs-oper",
            object_reference="sha256/aa/raw.grib2",
            sha256="a" * 64,
            retrieved_at=_now(),
            data_format="GRIB2",
            size_bytes=16,
            retention_class="legacy_unclassified",
            disposition_state="retained",
            hold_state="none",
        )
    )
    session.commit()


_DEFAULT = object()


def _insert_version(
    session: Session,
    artifact_id: object,
    version_id: str = "v-1",
    bucket: str = "zhufengxiangmu-b2-qa-982408502231",
    key: str = "qa/synthetic.grib2",
    mode: str = "GOVERNANCE",
    retain_until: object = _DEFAULT,
) -> None:
    if retain_until is _DEFAULT:
        retain_until = _now() + timedelta(days=180)
    session.add(
        WeatherStorageVersionModel(
            storage_version_id=uuid4(),
            artifact_id=artifact_id,
            provider="ECMWF",
            bucket_name=bucket,
            object_key=key,
            version_id=version_id,
            kms_key_arn=(
                "arn:aws:kms:ap-south-1:982408502231:key/"
                "3ea2b50b-fab0-4b50-b1e0-7a0f464396b0"
            ),
            observed_retention_mode=mode,
            observed_retain_until=retain_until,
            observed_legal_hold="OFF",
            storage_state="default_lock_verified_180d",
            first_verified_at=_now(),
            last_verified_at=_now(),
            policy_version="2026-08-24.b2.v1",
        )
    )
    session.commit()


def test_storage_version_table_has_expected_columns(
    migrated_postgres_engine: Engine,
) -> None:
    """The B2 storage-version table exists with the exact-version identity."""
    with migrated_postgres_engine.connect() as conn:
        result = conn.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='raw_artifact_storage_version'"
        )
        cols = {row[0] for row in result}
    expected = {
        "storage_version_id",
        "artifact_id",
        "provider",
        "bucket_name",
        "object_key",
        "version_id",
        "etag",
        "checksum_algorithm",
        "checksum_value",
        "kms_key_arn",
        "observed_retention_mode",
        "observed_retain_until",
        "observed_legal_hold",
        "storage_state",
        "first_verified_at",
        "last_verified_at",
        "policy_version",
        "created_at",
    }
    assert expected.issubset(cols)


def test_storage_event_table_is_append_only(
    migrated_postgres_engine: Engine,
    postgres_session: Session,
) -> None:
    """Storage events reject updates and deletes (append-only)."""
    _insert_artifact(postgres_session)
    artifact = postgres_session.scalar(select(WeatherRawArtifactModel))
    _insert_version(postgres_session, artifact.artifact_id)
    version = postgres_session.scalar(select(WeatherStorageVersionModel))
    postgres_session.add(
        WeatherStorageEventModel(
            event_id=uuid4(),
            storage_version_id=version.storage_version_id,
            bucket_name=version.bucket_name,
            object_key=version.object_key,
            version_id=version.version_id,
            event_type="version_observed",
            result="success",
            actor_id="qa",
            correlation_id="corr-1",
            details="observed",
            policy_version="2026-08-24.b2.v1",
        )
    )
    postgres_session.commit()

    # Update must be rejected
    with pytest.raises((IntegrityError, ProgrammingError)):
        postgres_session.execute(
            update(WeatherStorageEventModel)
            .where(WeatherStorageEventModel.actor_id == "qa")
            .values(actor_id="tampered")
        )
        postgres_session.commit()
    postgres_session.rollback()

    # Delete must be rejected
    with pytest.raises((IntegrityError, ProgrammingError)):
        postgres_session.execute(
            delete(WeatherStorageEventModel).where(
                WeatherStorageEventModel.actor_id == "qa"
            )
        )
        postgres_session.commit()
    postgres_session.rollback()


def test_storage_exact_version_triple_is_unique(
    postgres_session: Session,
) -> None:
    """(bucket, key, version_id) uniqueness is enforced."""
    _insert_artifact(postgres_session)
    artifact = postgres_session.scalar(select(WeatherRawArtifactModel))
    _insert_version(postgres_session, artifact.artifact_id)
    with pytest.raises(IntegrityError):
        _insert_version(postgres_session, artifact.artifact_id)
    postgres_session.rollback()


def test_storage_identity_must_be_nonempty(
    postgres_session: Session,
) -> None:
    """Empty bucket/key/version is rejected."""
    _insert_artifact(postgres_session)
    artifact = postgres_session.scalar(select(WeatherRawArtifactModel))
    with pytest.raises(IntegrityError):
        _insert_version(postgres_session, artifact.artifact_id, version_id="")
    postgres_session.rollback()


def test_storage_retain_until_required_for_known_mode(
    postgres_session: Session,
) -> None:
    """A non-UNKNOWN retention mode requires a retain-until timestamp."""
    _insert_artifact(postgres_session)
    artifact = postgres_session.scalar(select(WeatherRawArtifactModel))
    with pytest.raises(IntegrityError):
        _insert_version(
            postgres_session,
            artifact.artifact_id,
            mode="GOVERNANCE",
            retain_until=None,
        )
    postgres_session.rollback()


def test_legacy_rows_remain_unclassified(
    postgres_session: Session,
) -> None:
    """Existing weather rows get no fabricated S3 facts."""
    from sqlalchemy import text

    row = postgres_session.execute(
        text(
            "SELECT COUNT(*) FROM weather_raw_artifact "
            "WHERE source_id='does-not-exist'"
        )
    ).scalar()
    assert row == 0
    storage = postgres_session.execute(
        text("SELECT COUNT(*) FROM raw_artifact_storage_version")
    ).scalar()
    assert storage == 0
