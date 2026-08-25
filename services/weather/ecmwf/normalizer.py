"""IFS GRIB message to canonical weather-record normalization."""

from __future__ import annotations

from dataclasses import replace
from datetime import timezone
import math

from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
    validate_record,
)
from services.weather.ecmwf.parser import ParsedMessage


_EXPECTED_UNITS = {
    "z": "m**2 s**-2",
    "10u": "m s**-1",
    "10v": "m s**-1",
    "2t": "K",
    "tp": "m",
}


def normalize_messages(
    messages: tuple[ParsedMessage, ...],
    latitude: float,
    longitude: float,
) -> WeatherRecord:
    """Select provider grid point and normalize declared IFS units."""
    if not messages:
        raise ValueError("at least one parsed message is required")
    anchor = max(messages, key=lambda message: message.valid_time)
    index = min(
        range(len(anchor.values)),
        key=lambda item: (anchor.latitudes[item] - latitude) ** 2
        + (anchor.longitudes[item] - longitude) ** 2,
    )
    values, flags = _values_and_unit_flags(messages, index)
    altitude = _value(values, "z")
    u_wind = _value(values, "10u")
    v_wind = _value(values, "10v")
    speed = (
        math.hypot(u_wind, v_wind)
        if u_wind is not None and v_wind is not None
        else None
    )
    direction = _wind_direction(u_wind, v_wind, speed)
    record = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=anchor.valid_time.astimezone(timezone.utc),
        latitude=anchor.latitudes[index],
        longitude=anchor.longitudes[index],
        altitude=altitude / 9.80665 if altitude is not None else math.nan,
        wind_speed=speed,
        wind_direction=direction,
        temperature=_kelvin_to_celsius(_value(values, "2t")),
        precipitation=_metres_to_millimetres(_value(values, "tp")),
        visibility=None,
        source="ecmwf-ifs",
        model="IFS",
        forecast=ForecastIdentity(
            anchor.cycle, anchor.valid_time - anchor.cycle
        ),
        quality_flags=frozenset(flags),
    )
    return replace(record, quality_flags=validate_record(record))


def _values_and_unit_flags(
    messages: tuple[ParsedMessage, ...],
    index: int,
) -> tuple[dict[str, float], set[str]]:
    """Return raw values and invalid-unit flags without guessing units."""
    values: dict[str, float] = {}
    flags: set[str] = set()
    for message in messages:
        expected = _EXPECTED_UNITS.get(message.parameter)
        if expected is not None and message.units != expected:
            flags.add(QualityFlag.INVALID_UNIT.value)
            continue
        values[message.parameter] = message.values[index]
    return values, flags


def _value(values: dict[str, float], name: str) -> float | None:
    """Return one raw provider value without substituting a missing value."""
    return values.get(name)


def _kelvin_to_celsius(value: float | None) -> float | None:
    """Convert a declared Kelvin value to Celsius."""
    return value - 273.15 if value is not None else None


def _metres_to_millimetres(value: float | None) -> float | None:
    """Convert declared precipitation metres to millimetres."""
    return value * 1000 if value is not None else None


def _wind_direction(
    u_wind: float | None,
    v_wind: float | None,
    speed: float | None,
) -> float | None:
    """Convert east/north vector components into true-north wind direction."""
    if u_wind is None or v_wind is None or not speed:
        return None
    return (math.degrees(math.atan2(-u_wind, -v_wind)) + 360) % 360
