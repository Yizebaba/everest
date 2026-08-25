"""Repository and unit-of-work interfaces for registry application services."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from everest_api.registry.contracts import (
    ScheduleDefinition,
    SourceDefinition,
    SourceHealth,
)


class RegistryRepository(Protocol):
    """Persistence operations that the registry application service requires."""

    def get_source_status(self, source_id: str) -> str | None:
        """Return a source lifecycle value, or None when it does not exist."""

    def get_source_definition(self, source_id: str) -> SourceDefinition | None:
        """Return non-secret metadata for idempotent registration checks."""

    def add_source(self, definition: SourceDefinition) -> None:
        """Add a new registry source."""

    def update_status(self, source_id: str, status: str) -> None:
        """Persist a validated lifecycle change."""

    def update_health(self, source_id: str, health: SourceHealth) -> None:
        """Persist a validated operational health command."""

    def replace_schedule(self, schedule: ScheduleDefinition) -> None:
        """Atomically insert or replace the complete schedule for one source."""


class RegistryUnitOfWork(
    AbstractContextManager["RegistryUnitOfWork"], Protocol
):
    """Transaction boundary for a complete registry command."""

    repository: RegistryRepository

    def commit(self) -> None:
        """Commit all changes made by this command."""

    def rollback(self) -> None:
        """Roll back all changes made by this command."""
