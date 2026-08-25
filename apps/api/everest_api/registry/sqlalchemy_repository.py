"""SQLAlchemy implementation of the registry repository and transaction port."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from everest_api.registry.contracts import (
    ScheduleDefinition,
    SourceDefinition,
    SourceHealth,
    SourceStatus,
)
from everest_api.registry.models import (
    DataSourceRegistryModel,
    DataSourceScheduleModel,
)


class SqlAlchemyRegistryRepository:
    """Persist registry commands using the transaction-owned SQLAlchemy session."""

    def __init__(self, session: Session):
        """Bind repository operations to one active database session."""
        self._session = session

    def get_source_status(self, source_id: str) -> str | None:
        """Fetch the lifecycle value without materializing all registry metadata."""
        statement = select(DataSourceRegistryModel.status).where(
            DataSourceRegistryModel.source_id == source_id
        )
        return self._session.scalar(statement)

    def get_source_definition(self, source_id: str) -> SourceDefinition | None:
        """Load non-secret metadata used to make registration retries safe."""
        source = self._session.get(DataSourceRegistryModel, source_id)
        if source is None:
            return None
        return SourceDefinition(
            source_id=source.source_id,
            name=source.name,
            provider=source.provider,
            category=source.category,
            status=SourceStatus(source.status),
            access_method=source.access_method,
            endpoint=source.endpoint,
            data_format=source.data_format,
            update_frequency=source.update_frequency,
            spatial_resolution=source.spatial_resolution,
            temporal_resolution=source.temporal_resolution,
            coverage=source.coverage,
            license_name=source.license_name,
            commercial_allowed=source.commercial_allowed,
            credentials_required=source.credentials_required,
            credential_reference=source.credential_reference,
            metadata_version=source.metadata_version,
        )

    def add_source(self, definition: SourceDefinition) -> None:
        """Insert the validated definition using an unknown operational health state."""
        self._session.add(
            DataSourceRegistryModel(
                source_id=definition.source_id,
                name=definition.name,
                provider=definition.provider,
                category=definition.category,
                status=definition.status.value,
                access_method=definition.access_method,
                endpoint=definition.endpoint,
                data_format=definition.data_format,
                update_frequency=definition.update_frequency,
                spatial_resolution=definition.spatial_resolution,
                temporal_resolution=definition.temporal_resolution,
                coverage=definition.coverage,
                license_name=definition.license_name,
                commercial_allowed=definition.commercial_allowed,
                credentials_required=definition.credentials_required,
                credential_reference=definition.credential_reference,
                metadata_version=definition.metadata_version,
                health_status="unknown",
            )
        )

    def update_status(self, source_id: str, status: str) -> None:
        """Update an existing source status after application-layer validation."""
        source = self._session.get(DataSourceRegistryModel, source_id)
        if source is None:
            raise LookupError(f"Unknown source: {source_id}")
        source.status = status

    def update_health(self, source_id: str, health: SourceHealth) -> None:
        """Update health and the appropriate evidence timestamp atomically."""
        source = self._session.get(DataSourceRegistryModel, source_id)
        if source is None:
            raise LookupError(f"Unknown source: {source_id}")
        source.health_status = health.health_status.value
        if health.health_status.value == "healthy":
            source.last_success_at = health.occurred_at
        elif health.health_status.value in {"failed", "degraded", "stale"}:
            source.last_failure_at = health.occurred_at

    def replace_schedule(self, schedule: ScheduleDefinition) -> None:
        """Replace all schedule fields only after whole-document validation."""
        model = self._session.get(DataSourceScheduleModel, schedule.source_id)
        if model is None:
            model = DataSourceScheduleModel(source_id=schedule.source_id)
            self._session.add(model)
        model.enabled = schedule.enabled
        model.interval_seconds = schedule.interval_seconds
        model.retry_limit = schedule.retry_limit
        model.timeout_seconds = schedule.timeout_seconds
        model.initial_backoff_seconds = schedule.initial_backoff_seconds
        model.max_backoff_seconds = schedule.max_backoff_seconds
        model.misfire_grace_seconds = schedule.misfire_grace_seconds
        model.max_concurrent_runs = schedule.max_concurrent_runs
        model.next_run_at = schedule.next_run_at


class SqlAlchemyRegistryUnitOfWork:
    """Context-managed unit of work that rolls back unless explicitly committed."""

    def __init__(self, session: Session):
        """Create a transaction boundary around an open SQLAlchemy session."""
        self._session = session
        self.repository = SqlAlchemyRegistryRepository(session)
        self._committed = False

    def __enter__(self) -> "SqlAlchemyRegistryUnitOfWork":
        """Enter the transaction boundary."""
        return self

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> None:
        """Commit only on explicit success; otherwise restore the prior state."""
        if not self._committed:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        """Flush and commit all writes associated with this application command."""
        self._session.commit()
        self._committed = True

    def rollback(self) -> None:
        """Explicitly restore transaction state after an application failure."""
        self._session.rollback()
