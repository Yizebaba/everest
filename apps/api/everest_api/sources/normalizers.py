"""Canonical normalizers for terrain, observations, and satellite sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CanonicalTerrainTile:
    """Canonical record for one retained GLO-30 tile."""

    tile_name: str
    source_id: str
    dataset: str
    crs: str
    west: float
    south: float
    east: float
    north: float
    width: int
    height: int
    resolution_degrees: float
    min_elevation: float
    max_elevation: float
    object_reference: str
    sha256: str
    size_bytes: int
    retrieved_at: datetime


@dataclass(frozen=True)
class CanonicalAwsObservation:
    """Canonical observation record for one Everest AWS station row."""

    timestamp: datetime
    station: str
    temperature_c: float | None
    relative_humidity: float | None
    precipitation: float | None
    weather_code: str | None
    missing: bool
    quality_flags: tuple[str, ...]
    source_id: str = "everest-aws"
    dataset: str = "hourly-station"
    record_type: str = "observation"


@dataclass(frozen=True)
class CanonicalSatelliteSegment:
    """Canonical record for one retained Himawari band segment."""

    timestamp: datetime
    band: int
    segment: int
    satellite_name: str
    observation_area: str
    object_reference: str
    sha256: str
    size_bytes: int
    source_id: str = "himawari-9"
    dataset: str = "ahi-l1b-fldk"


def normalize_terrain_tile(
    tile_name: str,
    crs: str,
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
    resolution: tuple[float, float],
    min_elevation: float,
    max_elevation: float,
    object_reference: str,
    sha256: str,
    size_bytes: int,
    retrieved_at: datetime,
) -> CanonicalTerrainTile:
    """Normalize parsed GLO-30 tile metadata to a canonical record."""
    return CanonicalTerrainTile(
        tile_name=tile_name,
        source_id="copernicus-dem",
        dataset="glo30",
        crs=crs,
        west=bounds[0],
        south=bounds[1],
        east=bounds[2],
        north=bounds[3],
        width=width,
        height=height,
        resolution_degrees=resolution[0],
        min_elevation=min_elevation,
        max_elevation=max_elevation,
        object_reference=object_reference,
        sha256=sha256,
        size_bytes=size_bytes,
        retrieved_at=retrieved_at,
    )


def normalize_aws_observation(
    timestamp: datetime,
    station: str,
    temperature_c: float | None,
    relative_humidity: float | None,
    precipitation: float | None,
    weather_code: str | None,
    missing: bool,
    qc_flags: tuple[str, ...],
) -> CanonicalAwsObservation:
    """Normalize a parsed Everest AWS row to a canonical observation."""
    return CanonicalAwsObservation(
        timestamp=timestamp,
        station=station,
        temperature_c=temperature_c,
        relative_humidity=relative_humidity,
        precipitation=precipitation,
        weather_code=weather_code,
        missing=missing,
        quality_flags=qc_flags,
    )


def normalize_satellite_segment(
    timestamp: datetime,
    band: int,
    segment: int,
    satellite_name: str,
    observation_area: str,
    object_reference: str,
    sha256: str,
    size_bytes: int,
) -> CanonicalSatelliteSegment:
    """Normalize a parsed Himawari segment to a canonical record."""
    return CanonicalSatelliteSegment(
        timestamp=timestamp,
        band=band,
        segment=segment,
        satellite_name=satellite_name,
        observation_area=observation_area,
        object_reference=object_reference,
        sha256=sha256,
        size_bytes=size_bytes,
    )
