"""Provider-independent contracts for the Phase A data-source registry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Mapping


class SourceStatus(StrEnum):
    """Lifecycle state of a configured data source."""

    PLANNED = "planned"
    CONFIGURED = "configured"
    CONNECTED = "connected"
    VERIFIED = "verified"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class HealthStatus(StrEnum):
    """Current operational health, distinct from lifecycle verification."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    STALE = "stale"
    FAILED = "failed"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class RunOutcome(StrEnum):
    """Terminal or in-progress outcome of an append-only source attempt."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class SourceDefinition:  # pylint: disable=too-many-instance-attributes
    """Complete non-secret registry definition for one stable source ID."""

    source_id: str
    name: str
    provider: str
    category: str
    status: SourceStatus
    access_method: str
    endpoint: str | None
    data_format: str | None
    update_frequency: str | None
    spatial_resolution: str | None
    temporal_resolution: str | None
    coverage: str | None
    license_name: str | None
    commercial_allowed: bool
    credentials_required: bool
    credential_reference: str | None = None
    metadata_version: int = 1


@dataclass(frozen=True, slots=True)
class SourceHealth:
    """Operational health command payload; failure detail must already be safe."""

    health_status: HealthStatus
    occurred_at: datetime
    failure_detail: str | None = None


@dataclass(frozen=True, slots=True)
class ScheduleDefinition:  # pylint: disable=too-many-instance-attributes
    """Declarative configuration for a future, externally owned scheduler."""

    source_id: str
    enabled: bool
    interval_seconds: int
    retry_limit: int
    timeout_seconds: int
    initial_backoff_seconds: int
    max_backoff_seconds: int
    misfire_grace_seconds: int
    max_concurrent_runs: int
    next_run_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SourceRun:  # pylint: disable=too-many-instance-attributes
    """Safe append-only audit record for an eventual source execution attempt."""

    source_id: str
    outcome: RunOutcome
    started_at: datetime
    finished_at: datetime | None
    retryable: bool
    failure_code: str | None = None
    failure_detail: str | None = None
    content_hash: str | None = None


SourceMetadata = Mapping[str, str]
