"""Bounded, native-grid wind-field projections and derived storage.

This module projects an already-subset xarray Dataset. It never interpolates,
downloads, or parses provider data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any


SCHEMA_VERSION = 1
_DEFAULT_MAX_AXIS = 1_000
_DEFAULT_MAX_POINTS = 250_000
_DEFAULT_MAX_BYTES = 16 * 1024 * 1024
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class WindFieldLimits:
    """Hard limits applied before and after frame serialization."""

    max_latitudes: int = _DEFAULT_MAX_AXIS
    max_longitudes: int = _DEFAULT_MAX_AXIS
    max_points: int = _DEFAULT_MAX_POINTS
    max_serialized_bytes: int = _DEFAULT_MAX_BYTES

    def __post_init__(self) -> None:
        if (
            min(
                self.max_latitudes,
                self.max_longitudes,
                self.max_points,
                self.max_serialized_bytes,
            )
            <= 0
        ):
            raise ValueError("wind-field limits must be positive")


@dataclass(frozen=True)
# A frame is deliberately an explicit, versioned wire schema.
# pylint: disable=too-many-instance-attributes
class WindFieldFrame:
    """JSON-safe vectors on the source dataset's native rectilinear grid."""

    source: str
    model: str
    cycle: str
    valid_time: str
    lead_seconds: int
    level: float
    level_units: str
    bounds: dict[str, float]
    latitude: list[float]
    longitude: list[float]
    u: list[float | None]
    v: list[float | None]
    shape: list[int]
    order: str
    units: str
    minimum: dict[str, float | None]
    maximum: dict[str, float | None]
    quality_flags: list[str]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-compatible representation."""
        return asdict(self)


def build_wind_field_frame(
    dataset: Any,
    *,
    source: str,
    model: str,
    cycle: datetime,
    valid_time: datetime,
    lead: timedelta,
    level: float,
    level_units: str,
    bounds: tuple[float, float, float, float],
    u_name: str = "u",
    v_name: str = "v",
    latitude_name: str = "latitude",
    longitude_name: str = "longitude",
    units: str = "m s-1",
    limits: WindFieldLimits | None = None,
) -> WindFieldFrame:
    """Project native U/V arrays from one bounded rectilinear AOI Dataset."""
    # Projection metadata is explicit at the boundary rather than inferred from
    # provider-specific dataset attributes.
    # pylint: disable=too-many-arguments,too-many-locals
    active_limits = limits or WindFieldLimits()
    source = _required_identifier(source, "source")
    model = _required_identifier(model, "model")
    level_units = _required_text(level_units, "level_units")
    units = _required_text(units, "units")
    cycle = _utc_datetime(cycle, "cycle")
    valid_time = _utc_datetime(valid_time, "valid_time")
    lead_seconds = _lead_seconds(lead)
    if valid_time != cycle + timedelta(seconds=lead_seconds):
        raise ValueError("valid_time must equal cycle plus lead")
    if not math.isfinite(level):
        raise ValueError("level must be finite")

    west, south, east, north = _validated_bounds(bounds)
    latitude = _coordinate(dataset, latitude_name)
    longitude = _coordinate(dataset, longitude_name)
    _validate_axis_limits(latitude, longitude, active_limits)
    _validate_coordinate_bounds(latitude, longitude, west, south, east, north)

    u_values = _wind_values(
        dataset, u_name, latitude_name, longitude_name, latitude, longitude
    )
    v_values = _wind_values(
        dataset, v_name, latitude_name, longitude_name, latitude, longitude
    )
    u_flat, u_minimum, u_maximum, u_missing = _flatten(u_values)
    v_flat, v_minimum, v_maximum, v_missing = _flatten(v_values)
    flags = ["missing_values"] if u_missing or v_missing else []

    return WindFieldFrame(
        source=source,
        model=model,
        cycle=_utc_z(cycle),
        valid_time=_utc_z(valid_time),
        lead_seconds=lead_seconds,
        level=float(level),
        level_units=level_units,
        bounds={"west": west, "south": south, "east": east, "north": north},
        latitude=latitude,
        longitude=longitude,
        u=u_flat,
        v=v_flat,
        shape=[len(latitude), len(longitude)],
        order="latitude_longitude_c",
        units=units,
        minimum={"u": u_minimum, "v": v_minimum},
        maximum={"u": u_maximum, "v": v_maximum},
        quality_flags=flags,
    )


def materialize_wind_field_frame(
    frame: WindFieldFrame,
    derived_root: Path | str,
    *,
    limits: WindFieldLimits | None = None,
) -> Path:
    """Atomically store canonical JSON by digest and update latest."""
    active_limits = limits or WindFieldLimits()
    payload = _canonical_json(frame.to_dict())
    if len(payload) > active_limits.max_serialized_bytes:
        raise ValueError("serialized wind-field frame exceeds byte limit")
    digest = hashlib.sha256(payload).hexdigest()
    root = Path(derived_root)
    if not root.is_absolute():
        raise ValueError("derived_root must be an absolute external path")
    directory = root / "wind-field"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{digest}.json"
    if not target.exists():
        _atomic_write(target, payload)
    pointer = _canonical_json({"sha256": digest})
    latest = directory / "latest.json"
    if not latest.exists() or latest.read_bytes() != pointer:
        _atomic_write(latest, pointer)
    return target


def _coordinate(dataset: Any, name: str) -> list[float]:
    if name not in dataset.coords:
        raise KeyError(f"dataset is missing coordinate: {name}")
    coordinate = dataset.coords[name]
    if coordinate.ndim != 1 or coordinate.dims != (name,):
        raise ValueError(f"{name} must be a 1-D coordinate on its own dimension")
    values = [float(value) for value in coordinate.values.tolist()]
    if not values:
        raise ValueError(f"{name} coordinate must not be empty")
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{name} coordinate values must be finite")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} coordinate values must be unique")
    return values


def _wind_values(
    dataset: Any,
    name: str,
    latitude_name: str,
    longitude_name: str,
    latitude: list[float],
    longitude: list[float],
) -> Any:
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    if name not in dataset.data_vars:
        raise KeyError(f"dataset is missing wind variable: {name}")
    variable = dataset[name]
    expected_dimensions = {latitude_name, longitude_name}
    if variable.ndim != 2 or set(variable.dims) != expected_dimensions:
        raise ValueError("u and v must use the same two dimensions as coordinates")
    ordered = variable.transpose(latitude_name, longitude_name)
    if ordered.shape != (len(latitude), len(longitude)):
        raise ValueError("wind variable shape does not match coordinates")
    return ordered.values


def _flatten(
    values: Any,
) -> tuple[list[float | None], float | None, float | None, bool]:
    result: list[float | None] = []
    present: list[float] = []
    missing = False
    for raw_value in values.ravel(order="C"):
        value = float(raw_value)
        if math.isnan(value):
            result.append(None)
            missing = True
        elif not math.isfinite(value):
            raise ValueError("wind values must be finite or NaN")
        else:
            result.append(value)
            present.append(value)
    return (
        result,
        min(present) if present else None,
        max(present) if present else None,
        missing,
    )


def _validate_axis_limits(
    latitude: list[float], longitude: list[float], limits: WindFieldLimits
) -> None:
    if len(latitude) > limits.max_latitudes:
        raise ValueError("wind-field latitude dimension exceeds limit")
    if len(longitude) > limits.max_longitudes:
        raise ValueError("wind-field longitude dimension exceeds limit")
    if len(latitude) * len(longitude) > limits.max_points:
        raise ValueError("wind-field grid exceeds point limit")


def _validated_bounds(
    bounds: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    if len(bounds) != 4:
        raise ValueError("bounds must be west, south, east, north")
    west, south, east, north = (float(value) for value in bounds)
    if not all(math.isfinite(value) for value in (west, south, east, north)):
        raise ValueError("bounds must be finite")
    if not -180 <= west < east <= 180:
        raise ValueError("longitude bounds must satisfy -180 <= west < east <= 180")
    if not -90 <= south <= north <= 90:
        raise ValueError("latitude bounds must satisfy -90 <= south <= north <= 90")
    return west, south, east, north


def _validate_coordinate_bounds(
    latitude: list[float],
    longitude: list[float],
    west: float,
    south: float,
    east: float,
    north: float,
) -> None:
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    if min(latitude) < south or max(latitude) > north:
        raise ValueError("latitude coordinate is outside declared bounds")
    if min(longitude) < west or max(longitude) > east:
        raise ValueError("longitude coordinate is outside declared bounds")


def _required_text(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 128:
        raise ValueError(f"{name} must contain 1..128 characters")
    return normalized


def _required_identifier(value: str, name: str) -> str:
    normalized = value.strip()
    if not _IDENTIFIER.fullmatch(normalized):
        raise ValueError(f"{name} must be a bounded identifier")
    return normalized


def _utc_datetime(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _lead_seconds(value: timedelta) -> int:
    seconds = value.total_seconds()
    if seconds < 0 or not seconds.is_integer():
        raise ValueError("lead must be a non-negative whole number of seconds")
    return int(seconds)


def _utc_z(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _atomic_write(target: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = [
    "SCHEMA_VERSION",
    "WindFieldFrame",
    "WindFieldLimits",
    "build_wind_field_frame",
    "materialize_wind_field_frame",
]
