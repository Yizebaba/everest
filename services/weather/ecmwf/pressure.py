"""IFS pressure-level retrieval and canonical normalization (pressure levels).

Retrieves u/v/t/gh at configured pressure levels (e.g. 300 hPa ~ summit),
parses them with ecCodes, and produces one canonical record per level with
altitude taken from the level's geopotential height. Independent of the surface
connector; reuses the official ECMWF Open Data index/range flow. The parser is
local to this module so it can retain the pressure level (the surface parser
does not expose ``level``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
import math
from tempfile import NamedTemporaryFile

# GRIB decoding dataclasses carry many schema fields and locals by design.
# pylint: disable=too-many-instance-attributes,too-many-locals

LEVELS_DEFAULT = ("850", "700", "600", "500", "400", "300")
PARAMS = ("u", "v", "t", "gh")
G = 9.80665


@dataclass(frozen=True)
class ParsedPressureMessage:
    """One decoded pressure-level message with its level retained."""

    parameter: str
    level_hpa: str
    valid_time: datetime
    cycle: datetime
    lead_hours: int
    values: tuple[float, ...]
    latitudes: tuple[float, ...]
    longitudes: tuple[float, ...]


@dataclass(frozen=True)
class PressureLevelRecord:
    """One canonical record at a pressure level, altitude from geopotential."""

    level_hpa: str
    timestamp: datetime
    cycle: datetime
    lead_seconds: int
    altitude: float
    temperature_c: float
    wind_speed: float
    wind_direction: float
    # The signed components are retained alongside speed/direction so a vertical
    # interpolation between levels can average vectors; averaging bearings in
    # degrees would turn 350 deg and 10 deg into a southerly wind.
    u_wind: float = math.nan
    v_wind: float = math.nan
    latitude: float = math.nan
    longitude: float = math.nan
    source: str = "ecmwf-ifs"
    model: str = "IFS"


def parse_pressure_messages(
    payload: bytes,
) -> tuple[ParsedPressureMessage, ...]:
    """Decode pressure-level GRIB2 messages, retaining the pressure level."""
    from eccodes import (  # pylint: disable=import-outside-toplevel
        codes_get,
        codes_get_array,
        codes_grib_new_from_file,
        codes_release,
    )

    messages: list[ParsedPressureMessage] = []
    with NamedTemporaryFile(suffix=".grib2") as temporary:
        temporary.write(payload)
        temporary.flush()
        with open(temporary.name, "rb") as stream:
            while True:
                try:
                    handle = codes_grib_new_from_file(stream)
                except (ValueError, RuntimeError):
                    # Already the contract's error type: keep the message.
                    raise
                except Exception as error:  # pylint: disable=broad-except
                    # ecCodes raises platform-specific errors (e.g.
                    # PrematureEndOfFileError) for bytes that are not a GRIB
                    # stream. Translate them so callers see the contract's
                    # ValueError instead of a gribapi internal error.
                    raise ValueError(
                        "payload is not a readable GRIB2 stream"
                    ) from error
                if handle is None:
                    break
                try:
                    date = int(codes_get(handle, "dataDate"))
                    clock = int(codes_get(handle, "dataTime"))
                    cycle = datetime.strptime(
                        f"{date:08d}{clock:04d}", "%Y%m%d%H%M"
                    ).replace(tzinfo=timezone.utc)
                    lead = int(codes_get(handle, "step"))
                    messages.append(
                        ParsedPressureMessage(
                            parameter=str(codes_get(handle, "shortName")),
                            level_hpa=str(int(codes_get(handle, "level"))),
                            valid_time=cycle + timedelta(hours=lead),
                            cycle=cycle,
                            lead_hours=lead,
                            values=tuple(
                                float(value)
                                for value in codes_get_array(handle, "values")
                            ),
                            latitudes=tuple(
                                float(value)
                                for value in codes_get_array(
                                    handle, "latitudes"
                                )
                            ),
                            longitudes=tuple(
                                float(value)
                                for value in codes_get_array(
                                    handle, "longitudes"
                                )
                            ),
                        )
                    )
                finally:
                    codes_release(handle)
    if not messages:
        raise ValueError("payload did not contain a GRIB message")
    return tuple(messages)


def _nearest_index(lats, lons, tlat: float, tlon: float) -> int:
    return min(
        range(len(lats)),
        key=lambda i: (lats[i] - tlat) ** 2 + (lons[i] - tlon) ** 2,
    )


def normalize_pressure_levels(
    messages: tuple[ParsedPressureMessage, ...],
    latitude: float,
    longitude: float,
    levels: tuple[str, ...] = LEVELS_DEFAULT,
) -> list[PressureLevelRecord]:
    """Select the nearest grid point and build one record per pressure level."""
    by_level: dict[str, dict[str, ParsedPressureMessage]] = {}
    for msg in messages:
        by_level.setdefault(msg.level_hpa, {})[msg.parameter] = msg

    records: list[PressureLevelRecord] = []
    for lvl in levels:
        group = by_level.get(lvl, {})
        u = group.get("u")
        v = group.get("v")
        t = group.get("t")
        gh = group.get("gh")
        if u is None or v is None or t is None or gh is None:
            continue  # incomplete level is skipped, never fabricated
        if len({m.valid_time for m in (u, v, t, gh)}) != 1:
            continue  # mixed lead times at one level would falsify the record
        idx = _nearest_index(u.latitudes, u.longitudes, latitude, longitude)
        altitude = float(gh.values[idx])  # geopotential height (gpm ~ metres)
        temperature_c = float(t.values[idx]) - 273.15
        u_wind = float(u.values[idx])
        v_wind = float(v.values[idx])
        speed = math.hypot(u_wind, v_wind)
        direction = (math.degrees(math.atan2(-u_wind, -v_wind)) + 360) % 360
        lead_seconds = int((u.valid_time - u.cycle).total_seconds())
        records.append(
            PressureLevelRecord(
                level_hpa=lvl,
                timestamp=u.valid_time.astimezone(UTC),
                cycle=u.cycle.astimezone(UTC),
                lead_seconds=lead_seconds,
                altitude=altitude,
                temperature_c=temperature_c,
                wind_speed=speed,
                wind_direction=direction,
                u_wind=u_wind,
                v_wind=v_wind,
                latitude=float(u.latitudes[idx]),
                longitude=float(u.longitudes[idx]),
            )
        )
    return records
