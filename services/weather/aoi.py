"""Area-of-interest subsetting for rectilinear and curvilinear xarray grids."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class AreaOfInterest:
    """Inclusive geographic bounds expressed in degrees east and north."""

    south: float
    north: float
    west: float
    east: float

    def __post_init__(self) -> None:
        if not -90 <= self.south <= self.north <= 90:
            raise ValueError(
                "AOI latitude bounds must satisfy -90 <= south <= north <= 90"
            )
        if not all(math.isfinite(value) for value in (self.west, self.east)):
            raise ValueError("AOI longitude bounds must be finite")
        if not all(-360 <= value <= 360 for value in (self.west, self.east)):
            raise ValueError(
                "AOI longitude bounds must each be between -360 and 360"
            )


def normalize_longitude(longitude: Any) -> Any:
    """Normalize scalar or array-like longitudes to [-180, 180)."""
    return (longitude + 180) % 360 - 180


# Regional wind-grid AOI (authoritative, docs/design/regional-wind-field.md):
# the Everest massif and South Col route, inside the approved 100 km AOI of
# docs/everest-aoi.md. Both forecast wind-field materializations (ECMWF IFS
# and NOAA GFS) clip native u/v grids to this envelope without interpolation.
REGIONAL_GRID_AOI = AreaOfInterest(
    south=27.5,
    north=28.5,
    west=86.4,
    east=87.4,
)


def subset_dataset(
    dataset: Any,
    area: AreaOfInterest,
    *,
    variables: tuple[str, ...],
    latitude_name: str | None = None,
    longitude_name: str | None = None,
) -> Any:
    """Select explicit fields and retain only grid cells intersecting ``area``.

    One-dimensional coordinates are filtered independently, preserving their
    native order (including north-to-south latitude). Two-dimensional
    coordinates are masked together, then empty outer rows and columns are
    dropped. Source longitude labels are preserved; normalization is used only
    for comparisons.
    """
    selected = _select_variables(dataset, variables)
    latitude_name = latitude_name or _coordinate_name(
        selected, ("latitude", "lat")
    )
    longitude_name = longitude_name or _coordinate_name(
        selected, ("longitude", "lon")
    )
    latitude = selected.coords[latitude_name]
    longitude = selected.coords[longitude_name]
    if latitude.ndim not in (1, 2) or longitude.ndim != latitude.ndim:
        raise ValueError(
            "latitude and longitude must both be 1-D or both be 2-D"
        )
    if latitude.ndim == 2 and latitude.dims != longitude.dims:
        raise ValueError(
            "curvilinear latitude and longitude dimensions must match"
        )

    latitude_mask = (latitude >= area.south) & (latitude <= area.north)
    normalized = normalize_longitude(longitude)
    west = normalize_longitude(area.west)
    east = normalize_longitude(area.east)
    if area.east - area.west == 360:
        longitude_mask = longitude.notnull()
    elif west <= east:
        longitude_mask = (normalized >= west) & (normalized <= east)
    else:
        longitude_mask = (normalized >= west) | (normalized <= east)
    mask = latitude_mask & longitude_mask
    if not _has_matches(mask):
        raise ValueError("AOI does not intersect the dataset grid")
    if latitude.ndim == 1:
        return selected.where(latitude_mask, drop=True).where(
            longitude_mask, drop=True
        )
    return selected.where(mask, drop=True)


def _select_variables(dataset: Any, variables: tuple[str, ...]) -> Any:
    """Return only the requested data variables after strict validation."""
    if not variables:
        raise ValueError("variable selection requires at least one variable")
    if len(set(variables)) != len(variables):
        raise ValueError("variable selection must be unique")
    missing = tuple(
        variable for variable in variables if variable not in dataset.data_vars
    )
    if missing:
        raise KeyError(f"dataset is missing requested variables: {missing}")
    return dataset[list(variables)]


def _coordinate_name(dataset: Any, candidates: tuple[str, ...]) -> str:
    """Resolve the first conventional coordinate name present."""
    for candidate in candidates:
        if candidate in dataset.coords:
            return candidate
    raise KeyError(f"dataset lacks a coordinate named one of {candidates}")


def _has_matches(mask: Any) -> bool:
    """Materialize one scalar truth value for eager or lazy xarray masks."""
    value = mask.any()
    return bool(value.item() if hasattr(value, "item") else value)


__all__ = [
    "AreaOfInterest",
    "normalize_longitude",
    "REGIONAL_GRID_AOI",
    "subset_dataset",
]
