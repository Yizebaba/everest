"""Configuration-neutral one-pass provider job orchestration."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from everest_api.registry.redaction import redact_failure_detail


ProviderCallable = Callable[[], int]


class RunStatus(str, Enum):
    """Aggregate state for exactly the enabled jobs in one pass."""

    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILURE = "failure"


@dataclass(frozen=True)
class ProviderJob:
    """One independently enabled provider ingestion callable."""

    source_id: str
    call: ProviderCallable
    enabled: bool = True


@dataclass(frozen=True)
class ProviderOutcome:  # pylint: disable=too-many-instance-attributes
    """Bounded terminal outcome for one attempted provider."""

    source_id: str
    outcome: str
    started_at: datetime
    finished_at: datetime
    records_ingested: int = 0
    retryable: bool = False
    failure_code: str | None = None
    failure_detail: str | None = None


@dataclass(frozen=True)
class SchedulerResult:
    """Aggregate result that never implies unconfigured source coverage."""

    status: RunStatus
    outcomes: tuple[ProviderOutcome, ...]
    skipped_sources: tuple[str, ...]

    @property
    def attempted_sources(self) -> tuple[str, ...]:
        """Return only sources that were enabled and actually attempted."""
        return tuple(item.source_id for item in self.outcomes)

    @property
    def succeeded_sources(self) -> tuple[str, ...]:
        """Return exact source IDs whose callables completed successfully."""
        return tuple(
            item.source_id
            for item in self.outcomes
            if item.outcome == "succeeded"
        )

    @property
    def failed_sources(self) -> tuple[str, ...]:
        """Return exact source IDs whose callables failed."""
        return tuple(
            item.source_id for item in self.outcomes if item.outcome == "failed"
        )

    @property
    def records_ingested(self) -> int:
        """Sum successful provider counts without estimating skipped sources."""
        return sum(item.records_ingested for item in self.outcomes)


OutcomeRecorder = Callable[[ProviderOutcome], None]


def _safe_failure_detail(error: Exception) -> str:
    """Return bounded diagnostics without provider bodies or credential values."""
    message = str(error).replace("\n", " ").strip()
    detail = message[:512] if message else error.__class__.__name__
    return redact_failure_detail(detail)


def _record(recorder: OutcomeRecorder | None, outcome: ProviderOutcome) -> None:
    """Keep optional audit persistence from changing provider outcomes."""
    if recorder is None:
        return
    try:
        recorder(outcome)
    except Exception:  # pylint: disable=broad-exception-caught
        # Recording is best-effort because a registry outage must not turn a
        # completed provider ingestion into a false provider failure.
        return


def run_once(
    jobs: Iterable[ProviderJob], recorder: OutcomeRecorder | None = None
) -> SchedulerResult:
    """Execute every enabled provider once with independent failure accounting."""
    outcomes: list[ProviderOutcome] = []
    skipped: list[str] = []
    for job in jobs:
        if not job.enabled:
            skipped.append(job.source_id)
            continue
        started_at = datetime.now(UTC)
        try:
            count = job.call()
            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
            ):
                raise ValueError(
                    "provider job returned an invalid record count"
                )
            outcome = ProviderOutcome(
                source_id=job.source_id,
                outcome="succeeded",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                records_ingested=count,
            )
        except Exception as error:  # pylint: disable=broad-exception-caught
            outcome = ProviderOutcome(
                source_id=job.source_id,
                outcome="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                retryable=True,
                failure_code=error.__class__.__name__[:128],
                failure_detail=_safe_failure_detail(error),
            )
        outcomes.append(outcome)
        _record(recorder, outcome)

    successes = sum(item.outcome == "succeeded" for item in outcomes)
    failures = len(outcomes) - successes
    if successes and not failures:
        status = RunStatus.SUCCESS
    elif successes and failures:
        status = RunStatus.DEGRADED
    else:
        status = RunStatus.FAILURE
    return SchedulerResult(status, tuple(outcomes), tuple(skipped))
