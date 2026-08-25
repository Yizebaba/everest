"""Backend-owned retention decisions and bounded audit input validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from collections.abc import Mapping
from typing import Any

OPERATIONAL_SECONDS = 63_072_000
FAILED_SECONDS = 15_552_000
AUDIT_SECONDS = 94_608_000
POLICY_VERSION = "2026-08-21.v1"
ALLOWED_ACTOR_ROLES = frozenset(
    {"service", "operator", "retention_authority", "audit_authority"}
)


@dataclass(frozen=True)
class RetentionDecision:
    """Scalar backend retention classification supplied by trusted callers."""

    retention_class: str = "operational_raw"
    owner: str = "Everest Manager"
    period_seconds: int = OPERATIONAL_SECONDS
    policy_version: str = POLICY_VERSION

    def due_at(self, acquired_at: datetime) -> datetime:
        """Return the due time without inferring facts from a provider."""
        if self.retention_class not in {
            "operational_raw",
            "failed_or_rejected_raw",
        }:
            raise ValueError(
                "new artifacts require a classified retention class"
            )
        if (
            not self.owner
            or self.period_seconds <= 0
            or not self.policy_version
        ):
            raise ValueError("retention decision is incomplete")
        return acquired_at + timedelta(seconds=self.period_seconds)

    @classmethod
    def failed_or_rejected(cls) -> "RetentionDecision":
        """Return the approved short-lived class for failed ingestion."""
        return cls(
            retention_class="failed_or_rejected_raw",
            period_seconds=FAILED_SECONDS,
        )


def validate_audit_details(details: Mapping[str, Any] | None) -> dict[str, Any]:
    """Accept only bounded, redacted JSON scalar audit details."""
    value = {} if details is None else dict(details)
    scalar_types = (str, int, float, bool)
    for key, item in value.items():
        if type(  # pylint: disable=unidiomatic-typecheck
            key
        ) is not str or key.lower() in {
            "authorization",
            "credential",
            "password",
            "token",
            "raw_url",
            "object_reference",
        }:
            raise ValueError("audit details contain an unsafe key")
        # Exact scalar types prevent provider objects/subclasses crossing the
        # audit boundary; isinstance() would admit behavior-bearing subclasses.
        if (
            item is not None and type(item) not in scalar_types
        ):  # pylint: disable=unidiomatic-typecheck
            raise TypeError("audit details must contain only JSON scalars")
    encoded = repr(sorted(value.items())).encode("utf-8")
    if len(encoded) > 4096:
        raise ValueError("audit details exceed the 4096-byte bound")
    return value
