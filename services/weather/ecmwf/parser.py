"""Actual ECMWF GRIB2 parsing using ecCodes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class ParsedMessage:  # pylint: disable=too-many-instance-attributes
    """Decoded one GRIB message, including its source grid."""

    # GRIB messages naturally have many schema attributes.

    parameter: str
    valid_time: datetime
    cycle: datetime
    lead_hours: int
    values: tuple[float, ...]
    latitudes: tuple[float, ...]
    longitudes: tuple[float, ...]
    units: str
    level_type: str


def parse_grib_bytes(  # pylint: disable=too-many-locals
    payload: bytes,
) -> tuple[ParsedMessage, ...]:
    """Decode all GRIB messages from bytes; fail rather than fabricate data."""
    try:
        from eccodes import (  # pylint: disable=import-outside-toplevel
            codes_get,
            codes_grib_new_from_file,
            codes_get_array,
            codes_release,
        )
    except (ImportError, RuntimeError) as error:
        raise RuntimeError(
            "ecCodes runtime library is required to parse GRIB2"
        ) from error
    messages: list[ParsedMessage] = []
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
                    latitudes = tuple(
                        float(value)
                        for value in codes_get_array(handle, "latitudes")
                    )
                    longitudes = tuple(
                        float(value)
                        for value in codes_get_array(handle, "longitudes")
                    )
                    messages.append(
                        ParsedMessage(
                            str(codes_get(handle, "shortName")),
                            cycle + timedelta(hours=lead),
                            cycle,
                            lead,
                            tuple(
                                float(value)
                                for value in codes_get_array(handle, "values")
                            ),
                            latitudes,
                            longitudes,
                            str(codes_get(handle, "units")),
                            str(codes_get(handle, "typeOfLevel")),
                        )
                    )
                finally:
                    codes_release(handle)
    if not messages:
        raise ValueError("payload did not contain a GRIB message")
    return tuple(messages)
