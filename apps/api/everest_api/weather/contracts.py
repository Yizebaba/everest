"""Compatibility exports for the shared weather-ingestion contract.

New composition code must import DTOs from ``weather_ingestion_contract``.
``StaticAltitudeArtifactReference`` remains as a narrow compatibility wrapper
for callers that used the pre-ADR-009 backend API.
"""

from __future__ import annotations

from dataclasses import dataclass

from weather_ingestion_contract import (
    AuxiliaryArtifactReference,
    CanonicalRecordInput,
    IngestionPort,
    PrimitiveValue,
    RawArtifactDescriptor,
)


@dataclass(frozen=True)
class StaticAltitudeArtifactReference:
    """Explicit same-cycle step-zero surface-geopotential provenance input.

    The referenced descriptor is persisted as an independent immutable raw
    artifact and associated internally with records whose altitude it supports.
    """

    descriptor: RawArtifactDescriptor


__all__ = [
    "AuxiliaryArtifactReference",
    "CanonicalRecordInput",
    "IngestionPort",
    "PrimitiveValue",
    "RawArtifactDescriptor",
    "StaticAltitudeArtifactReference",
]
