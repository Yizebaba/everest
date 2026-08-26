"""Actual NOAA GFS GRIB2 parsing using ecCodes."""

# GRIB decoding is intentionally parallel to the independent ECMWF parser.
# pylint: disable=duplicate-code

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)
class ParsedMessage:  # pylint: disable=too-many-instance-attributes
    """One decoded GFS message and its provider grid."""

    parameter: str
    valid_time: datetime
    cycle: datetime
    lead_hours: int
    values: tuple[float, ...]
    latitudes: tuple[float, ...]
    longitudes: tuple[float, ...]
    units: str
    level_type: str


def parse_grib_bytes(payload: bytes) -> tuple[ParsedMessage, ...]:
    """Decode messages; fail if ecCodes or input is invalid."""
    try:
        from eccodes import (  # pylint: disable=import-outside-toplevel
            codes_get,
            codes_get_array,
            codes_grib_new_from_file,
            codes_release,
        )
    except (ImportError, RuntimeError) as error:
        raise RuntimeError(
            "ecCodes runtime library is required for GFS"
        ) from error
    messages = []
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
                    cycle = datetime.strptime(
                        f"{int(codes_get(handle, 'dataDate')):08d}"
                        f"{int(codes_get(handle, 'dataTime')):04d}",
                        "%Y%m%d%H%M",
                    ).replace(tzinfo=timezone.utc)
                    lead = int(codes_get(handle, "step"))
                    messages.append(
                        ParsedMessage(
                            str(codes_get(handle, "shortName")),
                            cycle + timedelta(hours=lead),
                            cycle,
                            lead,
                            tuple(
                                map(float, codes_get_array(handle, "values"))
                            ),
                            tuple(
                                map(float, codes_get_array(handle, "latitudes"))
                            ),
                            tuple(
                                map(
                                    float, codes_get_array(handle, "longitudes")
                                )
                            ),
                            str(codes_get(handle, "units")),
                            str(codes_get(handle, "typeOfLevel")),
                        )
                    )
                finally:
                    codes_release(handle)
    if not messages:
        raise ValueError("payload did not contain a GRIB message")
    return tuple(messages)
