"""Contract-level tests for lifecycle, health, and schedule safeguards."""

from datetime import UTC, datetime

import pytest

from everest_api.registry.contracts import (
    HealthStatus,
    ScheduleDefinition,
    SourceDefinition,
    SourceHealth,
    SourceStatus,
)
from everest_api.registry.validation import (
    validate_health,
    validate_schedule,
    validate_source_definition,
    validate_status_transition,
)


def _source(status: SourceStatus = SourceStatus.PLANNED) -> SourceDefinition:
    """Return minimal valid non-secret source metadata for unit tests."""
    return SourceDefinition(
        source_id="example-source",
        name="Example source",
        provider="Example",
        category="forecast",
        status=status,
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


def test_new_source_cannot_claim_connected_status() -> None:
    """Registration preserves the evidence boundary for connector lifecycle states."""
    with pytest.raises(ValueError, match="planned or configured"):
        validate_source_definition(_source(SourceStatus.CONNECTED))


def test_lifecycle_transition_enforces_approved_state_graph() -> None:
    """A planned source cannot claim evidence-bearing states in Phase A."""
    with pytest.raises(ValueError, match="connector acceptance evidence"):
        validate_status_transition("planned", "connected")


@pytest.mark.parametrize(
    "target", [SourceStatus.CONNECTED, SourceStatus.VERIFIED]
)
def test_evidence_states_are_unavailable_to_routine_commands(
    target: SourceStatus,
) -> None:
    """Only a future connector-evidence workflow may assert these states."""
    with pytest.raises(ValueError, match="connector acceptance evidence"):
        validate_status_transition("configured", target.value)


def test_schedule_rejects_invalid_backoff_document() -> None:
    """Incomplete-safe validation rejects an invalid configuration before writes."""
    schedule = ScheduleDefinition(
        source_id="example-source",
        enabled=True,
        interval_seconds=300,
        retry_limit=2,
        timeout_seconds=30,
        initial_backoff_seconds=60,
        max_backoff_seconds=30,
        misfire_grace_seconds=0,
        max_concurrent_runs=1,
    )
    with pytest.raises(ValueError, match="cannot exceed"):
        validate_schedule(schedule)


def test_failed_health_requires_bounded_safe_detail() -> None:
    """Failure health cannot silently discard the operational failure reason."""
    health = SourceHealth(
        health_status=HealthStatus.FAILED,
        occurred_at=datetime.now(UTC),
    )
    with pytest.raises(ValueError, match="requires safe failure_detail"):
        validate_health(health)
