"""Canonical source models for terrain, observations, and satellite (ADR-019)."""

from .models import AwsObservationModel, SatelliteSegmentModel, TerrainTileModel
from .normalizers import (
    CanonicalAwsObservation,
    CanonicalSatelliteSegment,
    CanonicalTerrainTile,
    normalize_aws_observation,
    normalize_satellite_segment,
    normalize_terrain_tile,
)

__all__ = [
    "AwsObservationModel",
    "CanonicalAwsObservation",
    "CanonicalSatelliteSegment",
    "CanonicalTerrainTile",
    "SatelliteSegmentModel",
    "TerrainTileModel",
    "normalize_aws_observation",
    "normalize_satellite_segment",
    "normalize_terrain_tile",
]
