"""DWD ICON messages to the provider-neutral canonical weather contract."""

# Explicit provider mappings intentionally parallel the accepted IFS/GFS shape.
# The local import avoids the runtime ingestion/normalizer circular dependency.
# pylint: disable=duplicate-code,import-outside-toplevel

from __future__ import annotations

from dataclasses import replace
from datetime import timezone
import math
from typing import TYPE_CHECKING

from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
    validate_record,
)
from services.weather.icon.parser import ParsedMessage

if TYPE_CHECKING:
    from services.weather.icon.ingestion import IconCanonicalRecord


EXPECTED_UNITS = {
    "t_2m": "K",
    "u_10m": "m s**-1",
    "v_10m": "m s**-1",
    "hsurf": "m",
}
PARAMETER_ALIASES = {
    "2t": "t_2m",
    "10u": "u_10m",
    "10v": "v_10m",
    "clat": "clat",
    "clon": "clon",
}


def normalize_messages(
    messages: tuple[ParsedMessage, ...],
    latitude: float,
    longitude: float,
) -> WeatherRecord:
    """Select ICON's nearest native grid cell and explicitly convert units."""
    if not messages:
        raise ValueError("at least one parsed message is required")
    _validate_times(messages)
    anchor = max(messages, key=lambda message: message.valid_time)
    _validate_requested_coordinates(latitude, longitude)
    index = nearest_grid_index(anchor, latitude, longitude)
    values, flags = _values_and_flags(messages, index)
    if "hsurf" not in values:
        flags.add(QualityFlag.MISSING_VALUE.value)
    u_wind = values.get("u_10m")
    v_wind = values.get("v_10m")
    speed = (
        math.hypot(u_wind, v_wind)
        if u_wind is not None and v_wind is not None
        else None
    )
    direction = (
        (math.degrees(math.atan2(-u_wind, -v_wind)) + 360) % 360
        if speed
        else None
    )
    record = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=anchor.valid_time.astimezone(timezone.utc),
        latitude=anchor.latitudes[index],
        longitude=anchor.longitudes[index],
        altitude=values.get("hsurf"),
        wind_speed=speed,
        wind_direction=direction,
        temperature=(values["t_2m"] - 273.15 if "t_2m" in values else None),
        precipitation=None,
        visibility=None,
        source="dwd-icon",
        model="ICON",
        forecast=ForecastIdentity(
            anchor.cycle.astimezone(timezone.utc),
            anchor.valid_time.astimezone(timezone.utc)
            - anchor.cycle.astimezone(timezone.utc),
        ),
        quality_flags=frozenset(flags),
    )
    return replace(record, quality_flags=validate_record(record))


def normalize_canonical_record(
    messages: tuple[ParsedMessage, ...],
    latitude: float,
    longitude: float,
    route_profile: str | None = None,
) -> "IconCanonicalRecord":
    """Normalize ICON and preserve its native UUID/index identity."""
    from services.weather.icon.ingestion import IconCanonicalRecord

    weather = normalize_messages(messages, latitude, longitude)
    anchor = max(messages, key=lambda message: message.valid_time)
    index = nearest_grid_index(anchor, latitude, longitude)
    return IconCanonicalRecord(
        weather=weather,
        spatial_key=provider_spatial_key(anchor, index),
        route_profile=route_profile,
    )


def nearest_grid_index(
    message: ParsedMessage,
    latitude: float,
    longitude: float,
) -> int:
    """Return the exact nearest DWD native-grid point index."""
    _validate_requested_coordinates(latitude, longitude)
    if not message.latitudes or not message.longitudes:
        raise ValueError("ICON message lacks native grid coordinates")
    return min(
        range(len(message.values)),
        key=lambda item: (message.latitudes[item] - latitude) ** 2
        + (message.longitudes[item] - longitude) ** 2,
    )


def _validate_requested_coordinates(
    latitude: float,
    longitude: float,
) -> None:
    """Reject invalid requested coordinates before native-grid selection."""
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValueError("ICON requested coordinates must be finite")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("ICON requested latitude is outside [-90, 90]")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("ICON requested longitude is outside [-180, 180]")


def provider_spatial_key(message: ParsedMessage, index: int) -> str:
    """Build a stable DWD grid identity, not a rounded coordinate key."""
    if message.grid_type != "unstructured_grid" or not message.grid_uuid:
        raise ValueError("ICON message lacks unstructured-grid provenance")
    if not 0 <= index < len(message.values):
        raise ValueError("ICON provider grid index is outside message values")
    return f"icon:{message.grid_uuid}:{index}"


def _values_and_flags(
    messages: tuple[ParsedMessage, ...],
    index: int,
) -> tuple[dict[str, float], set[str]]:
    """Keep unit-validated values and flag invalid units."""
    values: dict[str, float] = {}
    flags: set[str] = set()
    for message in messages:
        parameter = PARAMETER_ALIASES.get(
            message.parameter.lower(), message.parameter.lower()
        )
        expected = EXPECTED_UNITS.get(parameter)
        if expected is not None and message.units != expected:
            flags.add(QualityFlag.INVALID_UNIT.value)
            continue
        value = message.values[index]
        if not math.isfinite(value):
            flags.add(QualityFlag.MISSING_VALUE.value)
            continue
        values[parameter] = value
    return values, flags


def _validate_times(messages: tuple[ParsedMessage, ...]) -> None:
    """Reject naive provider timestamps; aware offsets normalize to UTC."""
    for message in messages:
        if message.valid_time.tzinfo is None or message.cycle.tzinfo is None:
            raise ValueError("ICON cycle and valid time must be timezone-aware")
