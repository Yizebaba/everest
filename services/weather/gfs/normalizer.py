"""NOAA GFS messages to the canonical weather contract."""

# Provider mappings remain explicit and independently testable.
# pylint: disable=duplicate-code

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
from services.weather.gfs.parser import ParsedMessage

EXPECTED_UNITS = {
    "tmp": "K",
    "ugrd": "m s**-1",
    "vgrd": "m s**-1",
    "apcp": "kg m**-2",
    "hgt": "gpm",
    "orog": "m",
    "vis": "m",
}


def normalize_messages(
    messages: tuple[ParsedMessage, ...], latitude: float, longitude: float
) -> WeatherRecord:
    """Select the nearest provider cell and apply explicit GFS unit mappings."""
    if not messages:
        raise ValueError("at least one parsed message is required")
    anchor = max(messages, key=lambda message: message.valid_time)
    index = min(
        range(len(anchor.values)),
        key=lambda item: (anchor.latitudes[item] - latitude) ** 2
        + (anchor.longitudes[item] - longitude) ** 2,
    )
    values: dict[str, float] = {}
    flags: set[str] = set()
    for message in messages:
        parameter = message.parameter.lower()
        # ecCodes reports GFS APCP as shortName "tp" and HGT as "gh"; without
        # these two entries the precipitation and geopotential-height branches
        # below were unreachable and precipitation was always None.
        parameter = {
            "2t": "tmp",
            "10u": "ugrd",
            "10v": "vgrd",
            "orog": "orog",
            "tp": "apcp",
            "gh": "hgt",
        }.get(parameter, parameter)
        if (
            parameter in EXPECTED_UNITS
            and message.units != EXPECTED_UNITS[parameter]
        ):
            flags.add(QualityFlag.INVALID_UNIT.value)
        else:
            values[parameter] = message.values[index]
    u_wind, v_wind = values.get("ugrd"), values.get("vgrd")
    speed = (
        math.hypot(u_wind, v_wind)
        if u_wind is not None and v_wind is not None
        else None
    )
    direction = (
        (math.degrees(math.atan2(-u_wind, -v_wind)) + 360) % 360
        if speed is not None
        else None
    )
    record = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=anchor.valid_time.astimezone(timezone.utc),
        latitude=anchor.latitudes[index],
        longitude=anchor.longitudes[index],
        altitude=(values["hgt"] if "hgt" in values else values.get("orog", math.nan)),
        wind_speed=speed,
        wind_direction=direction,
        temperature=values["tmp"] - 273.15 if "tmp" in values else None,
        precipitation=values["apcp"] if "apcp" in values else None,
        visibility=values["vis"] if "vis" in values else None,
        source="noaa-gfs",
        model="GFS",
        forecast=ForecastIdentity(
            anchor.cycle, anchor.valid_time - anchor.cycle
        ),
        quality_flags=frozenset(flags),
    )
    return replace(record, quality_flags=validate_record(record))
