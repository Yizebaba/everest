"""Conservative, documented sanitization for persisted failure diagnostics.

This policy detects common credential-bearing formats only. It is not an
exhaustive secret-detection system; callers must never submit raw provider
responses, headers, environment dumps, or URLs with credentials as diagnostics.
"""

from __future__ import annotations

import re

_REDACTED = "[REDACTED]"
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+"),
    re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|"
        r"refresh[_-]?token|authorization)\s*([:=])\s*[^\s,;]+",
    ),
    re.compile(r"(?i)(https?://[^\s/@:]+:)[^\s/@]+@"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def redact_failure_detail(detail: str) -> str:
    """Remove common credential patterns before a detail can be persisted.

    The function intentionally provides no assurance that all secret formats are
    detected. Future connector code must produce short, structured error codes
    rather than provider response bodies.
    """
    redacted = detail
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_replacement, redacted)
    return redacted


def contains_secret_pattern(detail: str) -> bool:
    """Return whether the documented common-pattern policy found a credential."""
    return any(pattern.search(detail) for pattern in _SECRET_PATTERNS)


def _replacement(match: re.Match[str]) -> str:
    """Keep a key name or URL prefix only when it improves safe diagnostics."""
    value = match.group(0)
    if value.lower().startswith(("http://", "https://")):
        return f"{match.group(1)}{_REDACTED}@"
    if "=" in value:
        return f'{value.split("=", maxsplit=1)[0]}={_REDACTED}'
    if ":" in value and not value.lower().startswith("bearer"):
        return f'{value.split(":", maxsplit=1)[0]}:{_REDACTED}'
    return _REDACTED
