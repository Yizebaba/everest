"""Invariant validation for registry contracts, independent of persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from everest_api.registry.contracts import (
    HealthStatus,
    ScheduleDefinition,
    SourceDefinition,
    SourceHealth,
)
from everest_api.registry.redaction import contains_secret_pattern

_MAX_FAILURE_DETAIL_LENGTH = 1_024
_RESERVED_EVIDENCE_STATUSES = frozenset({"connected", "verified"})
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "planned": frozenset({"configured", "disabled"}),
    "configured": frozenset({"degraded", "disabled"}),
    "connected": frozenset({"degraded", "disabled"}),
    "verified": frozenset({"degraded", "disabled"}),
    "degraded": frozenset({"configured", "connected", "disabled"}),
    "disabled": frozenset({"planned", "configured"}),
}


def validate_source_definition(definition: SourceDefinition) -> None:
    """Validate source identity and metadata without calling a provider."""
    required_values = {
        "source_id": definition.source_id,
        "name": definition.name,
        "provider": definition.provider,
        "category": definition.category,
        "access_method": definition.access_method,
    }
    empty_fields = [
        name for name, value in required_values.items() if not value
    ]
    if empty_fields:
        raise ValueError(
            f'Required fields are empty: {", ".join(empty_fields)}'
        )
    if definition.metadata_version < 1:
        raise ValueError("metadata_version must be at least one")
    if definition.credential_reference and not definition.credentials_required:
        raise ValueError("credential_reference requires credentials_required")
    if definition.status.value not in {"planned", "configured"}:
        raise ValueError(
            "New registry sources must begin planned or configured"
        )


def validate_status_transition(current: str, target: str) -> None:
    """Reject unsupported lifecycle changes without connector evidence."""
    if target in _RESERVED_EVIDENCE_STATUSES:
        raise ValueError(
            f"{target} requires future connector acceptance evidence and is "
            "not available in Phase A"
        )
    if current == target:
        return
    if target not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise ValueError(f"Invalid lifecycle transition: {current} -> {target}")


def validate_schedule(schedule: ScheduleDefinition) -> None:
    """Validate a complete declarative schedule before it reaches a transaction."""
    values = {
        "interval_seconds": schedule.interval_seconds,
        "retry_limit": schedule.retry_limit,
        "timeout_seconds": schedule.timeout_seconds,
        "initial_backoff_seconds": schedule.initial_backoff_seconds,
        "max_backoff_seconds": schedule.max_backoff_seconds,
        "misfire_grace_seconds": schedule.misfire_grace_seconds,
        "max_concurrent_runs": schedule.max_concurrent_runs,
    }
    negative = [name for name, value in values.items() if value < 0]
    if negative:
        raise ValueError(
            f'Schedule values cannot be negative: {", ".join(negative)}'
        )
    if not schedule.source_id:
        raise ValueError("source_id is required")
    if schedule.interval_seconds < 1 or schedule.timeout_seconds < 1:
        raise ValueError(
            "interval_seconds and timeout_seconds must be positive"
        )
    if schedule.max_concurrent_runs < 1:
        raise ValueError("max_concurrent_runs must be positive")
    if schedule.initial_backoff_seconds > schedule.max_backoff_seconds:
        raise ValueError(
            "initial_backoff_seconds cannot exceed max_backoff_seconds"
        )
    _validate_utc(schedule.next_run_at, "next_run_at")


def validate_health(health: SourceHealth) -> None:
    """Validate bounded safe health data and its UTC occurrence time."""
    _validate_utc(health.occurred_at, "occurred_at")
    if (
        health.failure_detail
        and len(health.failure_detail) > _MAX_FAILURE_DETAIL_LENGTH
    ):
        raise ValueError("failure_detail exceeds 1024 characters")
    if (
        health.health_status is HealthStatus.FAILED
        and not health.failure_detail
    ):
        raise ValueError("failed health requires safe failure_detail")
    if health.failure_detail and contains_secret_pattern(health.failure_detail):
        raise ValueError("failure_detail contains a common credential pattern")


def _validate_utc(value: datetime | None, field_name: str) -> None:
    """Require timezone-aware values normalized to UTC when present."""
    if value is not None and (
        value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value)
    ):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
