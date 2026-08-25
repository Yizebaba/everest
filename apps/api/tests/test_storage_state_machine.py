"""Deterministic unit tests for the B2 SVC-05 storage state machine."""

from __future__ import annotations

# Test fakes intentionally implement single-method ports.
# pylint: disable=too-few-public-methods

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from everest_api.weather.storage import (
    Clock,
    DisabledHoldDispositionResult,
    ObjectVersionRetentionPort,
    StorageCommandRejected,
    StorageStateMachine,
    StorageVersionRepository,
)

_NOW = datetime(2026, 8, 25, tzinfo=UTC)


class _FixedClock(Clock):
    def now(self) -> datetime:
        return _NOW


@dataclass
class _FakeRetentionPort(ObjectVersionRetentionPort):
    """A fake exact-version retention reader for deterministic tests."""

    mode: str = "GOVERNANCE"
    retain_until: datetime = _NOW + timedelta(days=180)
    legal_hold: str = "OFF"
    error: Exception | None = None
    extend_ignored: bool = False

    def get_exact_version_retention(self, bucket, key, version_id):
        if self.error:
            raise self.error
        return self.mode, self.retain_until

    def extend_to(self, bucket, key, version_id, retain_until):
        if not self.extend_ignored:
            self.retain_until = retain_until
        return self.retain_until

    def get_exact_version_legal_hold(self, bucket, key, version_id):
        return self.legal_hold

    def enumerate_versions(self, bucket, prefix):
        return []


class _Repo(StorageVersionRepository):
    def __init__(self) -> None:
        self.state = "uploaded"
        self.observed_mode = None
        self.observed_until = None
        self.events: list[tuple[str, str]] = []

    def transition(self, storage_version_id, expected_state, new_state):
        if self.state != expected_state:
            raise StorageCommandRejected("expected-state mismatch")
        self.state = new_state

    def record_event(self, event_type, result, **facts):
        self.events.append((event_type, result))

    def observe(self, storage_version_id, mode, retain_until, legal_hold):
        self.observed_mode = mode
        self.observed_until = retain_until


def _machine(repo=None, port=None, approval=None):
    repo = repo or _Repo()
    port = port or _FakeRetentionPort()
    return StorageStateMachine(
        repository=repo,
        retention_port=port,
        clock=_FixedClock(),
        approval_repository=approval,
    )


def test_rejects_missing_identity() -> None:
    """Every command rejects missing bucket/key/version/correlation facts."""
    machine = _machine()
    with pytest.raises(StorageCommandRejected):
        machine.observe_version(
            storage_version_id="id",
            bucket="",  # empty bucket
            key="k",
            version_id="v",
            actor="svc",
            correlation_id="c",
            provider="ECMWF",
            kms_key_arn="arn",
            policy_version="2026-08-24.b2.v1",
        )


def test_uploaded_to_default_lock_verified() -> None:
    """A verified default GOVERNANCE 180d retention moves to verified state."""
    repo = _Repo()
    machine = _machine(repo=repo)
    machine.observe_version(
        storage_version_id="id",
        bucket="b",
        key="k",
        version_id="v",
        actor="svc",
        correlation_id="c",
        provider="ECMWF",
        kms_key_arn="arn:aws:kms:ap-south-1:982408502231:key/x",
        policy_version="2026-08-24.b2.v1",
    )
    assert repo.state == "default_lock_verified_180d"
    assert ("default_lock_verified", "success") in repo.events


def test_default_lock_verified_to_failed_retained() -> None:
    """A 180d Governance default is compatible with failed_retained_180d."""
    repo = _Repo()
    repo.state = "default_lock_verified_180d"
    machine = _machine(repo=repo)
    machine.classify_failed_retained(
        storage_version_id="id", actor="svc", correlation_id="c"
    )
    assert repo.state == "failed_retained_180d"


def test_operational_extension_to_730d() -> None:
    """An approved 730-day extension moves to operational_retained_730d."""
    repo = _Repo()
    repo.state = "operational_extension_pending"
    port = _FakeRetentionPort()
    machine = _machine(repo=repo, port=port)
    machine.approve_operational_extension(
        storage_version_id="id",
        bucket="b",
        key="k",
        version_id="v",
        actor="svc",
        correlation_id="c",
        acquired_at=_NOW,
    )
    assert repo.state == "operational_retained_730d"
    assert port.retain_until == _NOW + timedelta(days=730)
    assert ("extension_succeeded", "success") in repo.events


def test_drift_blocks_when_readback_short() -> None:
    """A readback retain-until shorter than the 730d target blocks the move."""
    repo = _Repo()
    repo.state = "operational_extension_pending"
    # Extend is ignored by S3: readback still returns the short 180d date.
    port = _FakeRetentionPort(
        retain_until=_NOW + timedelta(days=180),
        extend_ignored=True,
    )
    machine = _machine(repo=repo, port=port)
    with pytest.raises(StorageCommandRejected):
        machine.approve_operational_extension(
            storage_version_id="id",
            bucket="b",
            key="k",
            version_id="v",
            actor="svc",
            correlation_id="c",
            acquired_at=_NOW,
        )
    assert repo.state == "drift_blocked"
    assert ("drift_detected", "blocked") in repo.events


def test_hold_is_disabled_result() -> None:
    """Hold placement returns a typed disabled result; no port call."""
    repo = _Repo()
    port = _FakeRetentionPort()
    machine = _machine(repo=repo, port=port)
    result = machine.place_hold(
        storage_version_id="id",
        bucket="b",
        key="k",
        version_id="v",
        actor="svc",
        correlation_id="c",
        reason="legal",
    )
    assert isinstance(result, DisabledHoldDispositionResult)
    assert repo.state == "uploaded"  # unchanged
    assert port.retain_until == _NOW + timedelta(days=180)  # untouched


def test_disposition_is_disabled_result() -> None:
    """Disposition returns a typed disabled result; no delete is attempted."""
    repo = _Repo()
    machine = _machine(repo=repo)
    result = machine.approve_disposition(
        storage_version_id="id",
        actor="svc",
        correlation_id="c",
    )
    assert isinstance(result, DisabledHoldDispositionResult)


def test_missing_readback_blocks() -> None:
    """A missing/inaccessible retention readback blocks with lock_failed."""
    repo = _Repo()
    port = _FakeRetentionPort(error=RuntimeError("s3 unreachable"))
    machine = _machine(repo=repo, port=port)
    with pytest.raises(StorageCommandRejected):
        machine.observe_version(
            storage_version_id="id",
            bucket="b",
            key="k",
            version_id="v",
            actor="svc",
            correlation_id="c",
            provider="ECMWF",
            kms_key_arn="arn",
            policy_version="2026-08-24.b2.v1",
        )
    assert repo.state == "kms_access_blocked"
