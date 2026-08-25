"""Unit coverage for backend retention decisions and safe audit details."""

from datetime import UTC, datetime, timedelta

import pytest

from everest_api.weather.retention import (
    FAILED_SECONDS,
    OPERATIONAL_SECONDS,
    RetentionDecision,
    validate_audit_details,
)


def test_approved_defaults_are_explicit_and_due_dates_are_deterministic() -> (
    None
):
    """The backend, not a provider, supplies approved retention facts."""
    acquired = datetime(2026, 8, 21, tzinfo=UTC)
    decision = RetentionDecision()
    assert decision.period_seconds == OPERATIONAL_SECONDS
    assert decision.due_at(acquired) == acquired + timedelta(
        seconds=OPERATIONAL_SECONDS
    )


def test_failed_classification_uses_approved_short_period() -> None:
    """Failed canonical processing retains classified raw for 180 days."""
    assert (
        RetentionDecision.failed_or_rejected().period_seconds == FAILED_SECONDS
    )


def test_unclassified_and_unbounded_details_fail_closed() -> None:
    """Incomplete retention and unbounded audit facts cannot be accepted."""
    with pytest.raises(ValueError):
        RetentionDecision(retention_class="legacy_unclassified").due_at(
            datetime.now(UTC)
        )
    with pytest.raises(ValueError):
        validate_audit_details({"x": "a" * 5000})
