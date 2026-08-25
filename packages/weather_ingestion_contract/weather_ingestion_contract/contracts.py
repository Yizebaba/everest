"""Typed primitive commands at the weather-ingestion ownership boundary.

These DTOs preserve the canonical weather meanings defined by meteorology and
raw provenance supplied by provider adapters. They perform only the boundary
validation needed to keep provider objects out of the owner-neutral contract;
they do not perform I/O, serialization, or persistence work.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeAlias
from uuid import UUID


PrimitiveValue: TypeAlias = str | int | float | bool | None
"""A scalar provider metadata value safe to carry across this port."""


def _validate_metadata(metadata: Mapping[str, PrimitiveValue]) -> None:
    """Reject metadata keys and values that are not exact JSON scalars.

    Existing provenance uses only scalar fields, so this boundary intentionally
    does not accept recursive containers. Exact type checks also reject
    subclasses that may carry provider behavior while appearing scalar.
    """

    allowed_types = (str, int, float, bool)
    for key, value in metadata.items():
        if type(key) is not str:  # pylint: disable=unidiomatic-typecheck
            raise TypeError("raw metadata keys must be strings")
        if value is not None and type(value) not in allowed_types:
            raise TypeError(
                "raw metadata values must be string, integer, float, boolean, "
                "or null"
            )


@dataclass(frozen=True)
class RawArtifactDescriptor:  # pylint: disable=too-many-instance-attributes
    """Immutable identity, location, and provenance of one retained artifact.

    ``metadata`` retains provider-declared scalar facts without accepting parser,
    HTTP-client, ORM, or provider-specific objects.
    """

    source_id: str
    dataset: str
    object_reference: str
    sha256: str
    retrieved_at: datetime
    data_format: str
    size_bytes: int
    source_url: str | None = None
    forecast_cycle: datetime | None = None
    forecast_lead_seconds: int | None = None
    valid_time: datetime | None = None
    metadata: Mapping[str, PrimitiveValue] | None = None

    def __post_init__(self) -> None:
        """Validate metadata before this descriptor reaches an adapter port."""

        if self.metadata is not None:
            _validate_metadata(self.metadata)


@dataclass(frozen=True)
class AuxiliaryArtifactReference:
    """One separately retained artifact that contributes record provenance.

    ``role`` is a stable, backend-interpreted provenance role. For example, the
    existing static surface-altitude evidence uses ``'static_altitude'``.
    """

    role: str
    artifact: RawArtifactDescriptor


@dataclass(frozen=True)
class CanonicalRecordInput:  # pylint: disable=too-many-instance-attributes
    """One normalized canonical record with unchanged units and QC flags.

    Field meanings, units, record types, quality flags, and source/model
    provenance are defined by ``docs/meteorology/weather-spec.md``. This DTO
    carries those values without reinterpreting, filtering, or deriving them.
    """

    record_type: str
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float
    spatial_key: str
    source: str
    model: str
    quality_flags: tuple[str, ...]
    wind_speed: float | None = None
    wind_direction: float | None = None
    temperature: float | None = None
    precipitation: float | None = None
    visibility: float | None = None
    pressure: float | None = None
    relative_humidity: float | None = None
    dew_point: float | None = None
    cloud_cover: float | None = None
    cloud_base: float | None = None
    cloud_top: float | None = None
    snowfall: float | None = None
    gust_speed: float | None = None
    forecast_cycle: datetime | None = None
    forecast_lead_seconds: int | None = None
    route_profile: str | None = None


class IngestionPort(Protocol):  # pylint: disable=too-few-public-methods
    """Persistence boundary implemented by backend-owned infrastructure."""

    def ingest(
        self,
        primary_artifact: RawArtifactDescriptor,
        records: Sequence[CanonicalRecordInput],
        auxiliary_artifacts: Sequence[AuxiliaryArtifactReference] = (),
    ) -> UUID:
        """Retain one primary artifact and append its canonical record view."""
