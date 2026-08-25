"""Executable PostgreSQL migration, persistence, constraint, and rollback tests."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from everest_api.registry.contracts import SourceDefinition, SourceStatus
from everest_api.registry.models import (
    DataSourceRegistryModel,
    DataSourceRunModel,
)
from everest_api.registry.sqlalchemy_repository import (
    SqlAlchemyRegistryUnitOfWork,
)


def _source(source_id: str = "postgres-example") -> SourceDefinition:
    """Return valid source metadata for persistence integration tests."""
    return SourceDefinition(
        source_id=source_id,
        name="PostgreSQL example",
        provider="Example",
        category="forecast",
        status=SourceStatus.PLANNED,
        access_method="future-connector",
        endpoint=None,
        data_format=None,
        update_frequency=None,
        spatial_resolution=None,
        temporal_resolution=None,
        coverage=None,
        license_name=None,
        commercial_allowed=False,
        credentials_required=False,
    )


def test_migration_creates_required_tables(
    migrated_postgres_engine: object,
) -> None:
    """The fixture executes the matching migration downgrade during cleanup."""
    names = inspect(migrated_postgres_engine).get_table_names()
    assert {
        "data_source_registry",
        "data_source_schedule",
        "data_source_run",
    } <= set(names)


def test_repository_commit_and_implicit_rollback(
    postgres_session: Session,
) -> None:
    """Only explicit unit-of-work commits retain registry data."""
    with SqlAlchemyRegistryUnitOfWork(postgres_session) as unit_of_work:
        unit_of_work.repository.add_source(_source())
        unit_of_work.commit()
    assert postgres_session.get(DataSourceRegistryModel, "postgres-example")

    with SqlAlchemyRegistryUnitOfWork(postgres_session) as unit_of_work:
        unit_of_work.repository.add_source(_source("rolled-back-source"))
        postgres_session.flush()
    assert (
        postgres_session.get(DataSourceRegistryModel, "rolled-back-source")
        is None
    )


def test_constraints_and_model_redaction(postgres_session: Session) -> None:
    """PostgreSQL checks apply and known token patterns cannot persist verbatim."""
    postgres_session.add(
        DataSourceRegistryModel(
            source_id="constraint-source",
            name="Constraint source",
            provider="Example",
            category="forecast",
            status="planned",
            access_method="future-connector",
            commercial_allowed=False,
            credentials_required=False,
            health_status="unknown",
            metadata_version=1,
        )
    )
    postgres_session.commit()
    run = DataSourceRunModel(
        source_id="constraint-source",
        outcome="failed",
        started_at=datetime.now(UTC),
        retryable=False,
        failure_detail="access_token=should-not-persist",
    )
    postgres_session.add(run)
    postgres_session.commit()
    assert run.failure_detail == "access_token=[REDACTED]"

    postgres_session.add(
        DataSourceRegistryModel(
            source_id="invalid-status",
            name="Invalid",
            provider="Example",
            category="forecast",
            status="invalid",
            access_method="test",
            commercial_allowed=False,
            credentials_required=False,
            health_status="unknown",
            metadata_version=1,
        )
    )
    with pytest.raises(IntegrityError):
        postgres_session.commit()
    postgres_session.rollback()
