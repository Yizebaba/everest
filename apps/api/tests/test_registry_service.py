"""Application-service idempotency tests without a database dependency."""

from contextlib import AbstractContextManager

import pytest

from everest_api.registry.contracts import SourceDefinition, SourceStatus
from everest_api.registry.service import RegistryService


def _source(name: str = "Example source") -> SourceDefinition:
    """Return minimal valid source metadata for registry service tests."""
    return SourceDefinition(
        source_id="example-source",
        name=name,
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


class _Repository:
    """In-memory repository spy implementing registration operations."""

    def __init__(self, existing: SourceDefinition | None = None):
        """Initialize the spy with optional persisted metadata."""
        self.existing = existing
        self.added: SourceDefinition | None = None

    def get_source_definition(self, source_id: str) -> SourceDefinition | None:
        """Return metadata for deterministic registration behavior."""
        del source_id
        return self.existing

    def add_source(self, definition: SourceDefinition) -> None:
        """Record an insertion request."""
        self.added = definition


class _UnitOfWork(AbstractContextManager["_UnitOfWork"]):
    """Transaction spy that records explicit commits."""

    def __init__(self, repository: _Repository):
        """Create a unit of work around the repository spy."""
        self.repository = repository
        self.committed = False

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> None:
        """Implement the service-required context-manager protocol."""

    def commit(self) -> None:
        """Record a command commit."""
        self.committed = True

    def rollback(self) -> None:
        """Provide the transaction port's rollback operation."""


def test_register_retry_is_idempotent() -> None:
    """An identical retry performs no duplicate write or commit."""
    existing = _source()
    unit_of_work = _UnitOfWork(_Repository(existing))

    RegistryService(lambda: unit_of_work).register(existing)

    assert unit_of_work.repository.added is None
    assert not unit_of_work.committed


def test_register_rejects_conflicting_existing_metadata() -> None:
    """A stable source ID cannot be silently repointed to new metadata."""
    unit_of_work = _UnitOfWork(_Repository(_source()))

    with pytest.raises(ValueError, match="already registered"):
        RegistryService(lambda: unit_of_work).register(_source("Conflicting"))
