"""B2 SVC-05 framework-neutral storage-version state machine.

The S3 exact-version authority is behind ports. This module imports no AWS SDK,
ORM, HTTP, or FastAPI types; adapters live in a later backend-owned layer.

Command methods carry the full exact-version identity, actor, and correlation
per the DB-04/SVC-05 contract; disabled hold/disposition commands keep the
signature for interface consistency though their arguments are intentionally
unused in this authorization.
"""

# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=unused-argument

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

EXACT_VERSION_730D = timedelta(days=730)
DEFAULT_180D = timedelta(days=180)


class StorageCommandRejected(Exception):
    """A storage command failed a fail-closed guard or expected-state check."""


@dataclass(frozen=True)
class DisabledHoldDispositionResult:
    """Typed disabled result for hold/disposition commands in this authorization."""

    command: str
    reason: str = "disabled in this authorization"


class Clock(Protocol):  # pylint: disable=too-few-public-methods
    """Injectable time source; current wall time alone never proves expiry."""

    def now(self) -> datetime:
        """Return the current UTC instant."""


class ObjectVersionRetentionPort(Protocol):
    """Exact-version S3 retention authority (adapter implements it)."""

    def get_exact_version_retention(
        self, bucket: str, key: str, version_id: str
    ) -> tuple[str, datetime]:
        """Return (mode, retain_until) for one exact version; raise on error."""

    def extend_to(
        self, bucket: str, key: str, version_id: str, retain_until: datetime
    ) -> datetime:
        """Extend one exact version's retention to the requested date."""

    def get_exact_version_legal_hold(
        self, bucket: str, key: str, version_id: str
    ) -> str:
        """Return the exact version's legal-hold status (ON/OFF/UNKNOWN)."""

    def enumerate_versions(
        self, bucket: str, prefix: str
    ) -> Sequence[tuple[str, str]]:
        """Return (key, version_id) pairs for reconciliation."""


class StorageVersionRepository(Protocol):
    """Compare-and-set storage-version state and append-only events."""

    def transition(
        self,
        storage_version_id: str,
        expected_state: str,
        new_state: str,
    ) -> None:
        """Move one storage version state only if the expected state matches."""

    def record_event(
        self, event_type: str, result: str, **facts: object
    ) -> None:
        """Append one bounded, immutable storage event."""

    def observe(
        self,
        storage_version_id: str,
        mode: str,
        retain_until: datetime,
        legal_hold: str,
    ) -> None:
        """Persist the observed exact-version facts."""


class StorageStateMachine:
    """Fail-closed transitions for one exact S3 version (SVC-05)."""

    def __init__(
        self,
        repository: StorageVersionRepository,
        retention_port: ObjectVersionRetentionPort,
        clock: Clock,
        approval_repository: Callable[[str, str], bool] | None = None,
    ) -> None:
        """Bind the repository, retention port, clock, and optional approvals."""
        self._repository = repository
        self._port = retention_port
        self._clock = clock
        self._approval = approval_repository

    @staticmethod
    def _require_identity(
        *,
        bucket: str,
        key: str,
        version_id: str,
        correlation_id: str,
    ) -> None:
        """Reject empty or missing exact-version identity facts."""
        if not bucket or not key or not version_id or not correlation_id:
            raise StorageCommandRejected(
                "exact-version bucket/key/version_id and correlation are required"
            )

    def observe_version(
        self,
        *,
        storage_version_id: str,
        bucket: str,
        key: str,
        version_id: str,
        actor: str,
        correlation_id: str,
        provider: str,
        kms_key_arn: str,
        policy_version: str,
    ) -> None:
        """Verify the default lock and record the observed 180-day state."""
        self._require_identity(
            bucket=bucket,
            key=key,
            version_id=version_id,
            correlation_id=correlation_id,
        )
        if not provider or not kms_key_arn or not policy_version:
            raise StorageCommandRejected(
                "provider, kms_key_arn, and policy_version are required"
            )
        try:
            mode, retain_until = self._port.get_exact_version_retention(
                bucket, key, version_id
            )
            hold = self._port.get_exact_version_legal_hold(
                bucket, key, version_id
            )
        except (
            Exception
        ) as error:  # noqa: BLE001 - fail closed on any port error
            self._repository.transition(
                storage_version_id, "uploaded", "kms_access_blocked"
            )
            self._repository.record_event(
                "kms_access_blocked", "blocked", reason=str(error)
            )
            raise StorageCommandRejected("retention readback failed") from error
        if (
            mode != "GOVERNANCE"
            or retain_until < self._clock.now() + DEFAULT_180D
        ):
            self._repository.transition(
                storage_version_id, "uploaded", "drift_blocked"
            )
            self._repository.record_event(
                "drift_detected",
                "blocked",
                mode=mode,
                retain_until=str(retain_until),
            )
            raise StorageCommandRejected(
                "default GOVERNANCE 180d not satisfied"
            )
        self._repository.observe(storage_version_id, mode, retain_until, hold)
        self._repository.transition(
            storage_version_id, "uploaded", "default_lock_verified_180d"
        )
        self._repository.record_event(
            "default_lock_verified", "success", retain_until=str(retain_until)
        )

    def classify_failed_retained(
        self, *, storage_version_id: str, actor: str, correlation_id: str
    ) -> None:
        """Move a verified 180d default to the failed/rejected retained class."""
        self._repository.transition(
            storage_version_id,
            "default_lock_verified_180d",
            "failed_retained_180d",
        )
        self._repository.record_event(
            "version_observed",
            "success",
            actor=actor,
            correlation_id=correlation_id,
        )

    def approve_operational_extension(
        self,
        *,
        storage_version_id: str,
        bucket: str,
        key: str,
        version_id: str,
        actor: str,
        correlation_id: str,
        acquired_at: datetime,
    ) -> None:
        """Extend an exact version to the approved 730-day operational retention."""
        self._require_identity(
            bucket=bucket,
            key=key,
            version_id=version_id,
            correlation_id=correlation_id,
        )
        if self._approval is not None and not self._approval(
            correlation_id, "operational_extension"
        ):
            raise StorageCommandRejected("operational extension not approved")
        target = max(
            self._clock.now() + EXACT_VERSION_730D,
            acquired_at + EXACT_VERSION_730D,
        )
        try:
            # Extend first, then read back; success is only claimed after the
            # exact-version readback confirms the extended retain-until.
            self._port.extend_to(bucket, key, version_id, target)
            _, retain_until = self._port.get_exact_version_retention(
                bucket, key, version_id
            )
        except Exception as error:  # noqa: BLE001 - fail closed
            self._repository.transition(
                storage_version_id,
                "operational_extension_pending",
                "kms_access_blocked",
            )
            self._repository.record_event(
                "kms_access_blocked", "blocked", reason=str(error)
            )
            raise StorageCommandRejected("retention readback failed") from error
        if retain_until < target:
            self._repository.transition(
                storage_version_id,
                "operational_extension_pending",
                "drift_blocked",
            )
            self._repository.record_event(
                "drift_detected",
                "blocked",
                current=str(retain_until),
                target=str(target),
            )
            raise StorageCommandRejected("retain-until below 730-day target")
        # S3 success is recorded only after exact-version readback above.
        self._repository.transition(
            storage_version_id,
            "operational_extension_pending",
            "operational_retained_730d",
        )
        self._repository.record_event(
            "extension_succeeded", "success", retain_until=str(retain_until)
        )

    def place_hold(
        self,
        *,
        storage_version_id: str,
        bucket: str,
        key: str,
        version_id: str,
        actor: str,
        correlation_id: str,
        reason: str,
    ) -> DisabledHoldDispositionResult:
        """Return a typed disabled result; hold is not authorized."""
        return DisabledHoldDispositionResult(
            command="place_hold",
            reason="legal authority not assigned",
        )

    def approve_disposition(
        self,
        *,
        storage_version_id: str,
        actor: str,
        correlation_id: str,
    ) -> DisabledHoldDispositionResult:
        """Return a typed disabled result; disposition is not authorized."""
        return DisabledHoldDispositionResult(
            command="approve_disposition",
            reason="disposition disabled in this authorization",
        )
