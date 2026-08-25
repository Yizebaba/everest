"""Transaction-safe application service for the Phase A registry."""

from __future__ import annotations

from typing import Callable

from everest_api.registry.contracts import (
    ScheduleDefinition,
    SourceDefinition,
    SourceHealth,
    SourceStatus,
)
from everest_api.registry.repository import RegistryUnitOfWork
from everest_api.registry.validation import (
    validate_health,
    validate_schedule,
    validate_source_definition,
    validate_status_transition,
)


class RegistryService:
    """Coordinates validated registry writes without scheduling or I/O."""

    def __init__(self, unit_of_work_factory: Callable[[], RegistryUnitOfWork]):
        """Create a service using a factory that supplies isolated transactions."""
        self._unit_of_work_factory = unit_of_work_factory

    def register(self, definition: SourceDefinition) -> None:
        """Idempotently register an identical source or reject conflicting metadata."""
        validate_source_definition(definition)
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_source_definition(
                definition.source_id
            )
            if existing is not None:
                if existing == definition:
                    return
                raise ValueError(
                    f"Source already registered: {definition.source_id}"
                )
            unit_of_work.repository.add_source(definition)
            unit_of_work.commit()

    def change_status(self, source_id: str, target: SourceStatus) -> None:
        """Apply one validated lifecycle transition to an existing source."""
        with self._unit_of_work_factory() as unit_of_work:
            current = unit_of_work.repository.get_source_status(source_id)
            if current is None:
                raise LookupError(f"Unknown source: {source_id}")
            validate_status_transition(current, target.value)
            unit_of_work.repository.update_status(source_id, target.value)
            unit_of_work.commit()

    def record_health(self, source_id: str, health: SourceHealth) -> None:
        """Record operational health independently of source lifecycle state."""
        validate_health(health)
        with self._unit_of_work_factory() as unit_of_work:
            if unit_of_work.repository.get_source_status(source_id) is None:
                raise LookupError(f"Unknown source: {source_id}")
            unit_of_work.repository.update_health(source_id, health)
            unit_of_work.commit()

    def configure_schedule(self, schedule: ScheduleDefinition) -> None:
        """Atomically persist a full validated schedule; it never executes a job."""
        validate_schedule(schedule)
        with self._unit_of_work_factory() as unit_of_work:
            if (
                unit_of_work.repository.get_source_status(schedule.source_id)
                is None
            ):
                raise LookupError(f"Unknown source: {schedule.source_id}")
            unit_of_work.repository.replace_schedule(schedule)
            unit_of_work.commit()
