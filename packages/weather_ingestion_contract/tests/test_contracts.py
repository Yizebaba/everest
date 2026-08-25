"""Tests for the owner-neutral weather-ingestion DTOs."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from weather_ingestion_contract import RawArtifactDescriptor


def _descriptor(**overrides: object) -> RawArtifactDescriptor:
    """Build a minimal raw-artifact descriptor for contract tests."""

    values: dict[str, object] = {
        "source_id": "test-source",
        "dataset": "test-dataset",
        "object_reference": "raw/test.bin",
        "sha256": "a" * 64,
        "retrieved_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "data_format": "bin",
        "size_bytes": 1,
    }
    values.update(overrides)
    return RawArtifactDescriptor(**values)  # type: ignore[arg-type]


def test_scalar_metadata_preserves_nulls_and_json_scalars() -> None:
    """Scalar provenance remains unchanged at the contract boundary."""

    metadata = {
        "source": "test-source",
        "attempt": 2,
        "temperature": -8.5,
        "verified": True,
        "optional": None,
    }

    assert _descriptor(metadata=metadata).metadata == metadata


@dataclass
class ProviderObject:
    """A provider-owned object that must not cross the contract boundary."""

    value: str


@pytest.mark.parametrize(
    "metadata",
    [
        {"parser": ProviderObject("parser")},
        {"nested": {"source": "test-source"}},
        {1: "non-string key"},
    ],
)
def test_non_scalar_metadata_is_rejected_before_port_invocation(
    metadata: object,
) -> None:
    """Unsupported provenance fails while constructing the DTO."""

    with pytest.raises(TypeError, match="metadata|keys"):
        _descriptor(metadata=metadata)
