"""Owner-neutral weather-ingestion DTOs and persistence port.

The package deliberately depends only on the Python standard library. Provider
adapters construct these commands and backend infrastructure implements the
port; neither owner imports the other through this boundary.
"""

from weather_ingestion_contract.contracts import (
    AuxiliaryArtifactReference,
    CanonicalRecordInput,
    IngestionPort,
    PrimitiveValue,
    RawArtifactDescriptor,
)

__all__ = [
    "AuxiliaryArtifactReference",
    "CanonicalRecordInput",
    "IngestionPort",
    "PrimitiveValue",
    "RawArtifactDescriptor",
]
