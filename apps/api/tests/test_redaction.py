"""Tests for the explicitly limited persisted failure-detail policy."""

from datetime import UTC, datetime

import pytest

from everest_api.registry.contracts import HealthStatus, SourceHealth
from everest_api.registry.models import DataSourceRunModel
from everest_api.registry.redaction import redact_failure_detail
from everest_api.registry.validation import validate_health


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("password=hunter2 rejected", "password=[REDACTED] rejected"),
        ("Authorization: Bearer abc.def_123", "Authorization:[REDACTED]"),
        (
            "request https://alice:hunter2@example.test failed",
            "request https://alice:[REDACTED]@example.test failed",
        ),
        (
            "AWS key AKIAABCDEFGHIJKLMNOP rejected",
            "AWS key [REDACTED] rejected",
        ),
    ],
)
def test_redaction_removes_common_credential_patterns(
    detail: str, expected: str
) -> None:
    """Regression-test the stated common-pattern redaction policy."""
    assert redact_failure_detail(detail) == expected


def test_health_command_rejects_secret_bearing_failure_detail() -> None:
    """Health commands fail closed instead of persisting a raw secret."""
    health = SourceHealth(
        health_status=HealthStatus.FAILED,
        occurred_at=datetime.now(UTC),
        failure_detail="access_token=not-safe",
    )

    with pytest.raises(ValueError, match="credential pattern"):
        validate_health(health)


def test_run_model_redacts_known_tokens_before_session_persistence() -> None:
    """The ORM model provides a second defensive redaction boundary."""
    run = DataSourceRunModel(
        source_id="example-source",
        outcome="failed",
        started_at=datetime.now(UTC),
        retryable=False,
        failure_detail="api_key=must-not-reach-the-database",
    )

    assert run.failure_detail == "api_key=[REDACTED]"
