"""Actual DWD ICON GRIB2 parsing using ecCodes."""

# Independent provider parsing intentionally repeats the accepted GRIB boundary.
# pylint: disable=duplicate-code

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import tempfile
from typing import BinaryIO, Iterator


@dataclass(frozen=True)
class ParsedMessage:  # pylint: disable=too-many-instance-attributes
    """A DWD ICON GRIB message including native unstructured grid metadata."""

    parameter: str
    valid_time: datetime
    cycle: datetime
    lead_hours: int
    values: tuple[float, ...]
    latitudes: tuple[float, ...]
    longitudes: tuple[float, ...]
    units: str
    level_type: str
    grid_type: str
    grid_uuid: str


def parse_grib_bytes(payload: bytes) -> tuple[ParsedMessage, ...]:
    """Parse GRIB2 messages using ecCodes, or fail without fabrication."""
    try:
        from eccodes import (  # pylint: disable=import-outside-toplevel
            codes_get,
            codes_get_array,
            codes_grib_new_from_file,
            codes_release,
        )
    except (ImportError, RuntimeError) as error:
        raise RuntimeError(
            "ecCodes runtime library is required for ICON"
        ) from error
    messages: list[ParsedMessage] = []
    with _temporary_grib_path(payload) as temporary_path:
        with temporary_path.open("rb") as stream:
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
                        f'{int(codes_get(handle, "dataDate")):08d}'
                        f'{int(codes_get(handle, "dataTime")):04d}',
                        "%Y%m%d%H%M",
                    ).replace(tzinfo=timezone.utc)
                    valid_time = datetime.strptime(
                        f'{int(codes_get(handle, "validityDate")):08d}'
                        f'{int(codes_get(handle, "validityTime")):04d}',
                        "%Y%m%d%H%M",
                    ).replace(tzinfo=timezone.utc)
                    lead_seconds = (valid_time - cycle).total_seconds()
                    if lead_seconds < 0 or lead_seconds % 3600:
                        raise ValueError(
                            "ICON valid time does not encode a whole-hour lead"
                        )
                    lead = int(lead_seconds // 3600)
                    messages.append(
                        ParsedMessage(
                            str(codes_get(handle, "shortName")),
                            valid_time,
                            cycle,
                            lead,
                            tuple(
                                map(float, codes_get_array(handle, "values"))
                            ),
                            (),
                            (),
                            str(codes_get(handle, "units")),
                            str(codes_get(handle, "typeOfLevel")),
                            str(codes_get(handle, "gridType")),
                            str(codes_get(handle, "uuidOfHGrid")),
                        )
                    )
                finally:
                    codes_release(handle)
    if not messages:
        raise ValueError("payload did not contain a GRIB message")
    return _with_native_coordinates(tuple(messages))


@contextmanager
def _temporary_grib_path(payload: bytes) -> Iterator[Path]:
    """Write payload to a closed, cleanup-guaranteed path for ecCodes.

    ecCodes consumes a separately opened Python file object. Closing the writer
    before yielding the path avoids Windows sharing conflicts. The explicit
    finally block removes the file after successful parsing and all failures.
    """
    descriptor, path_text = tempfile.mkstemp(suffix=".grib2")
    path = Path(path_text)
    try:
        try:
            writer: BinaryIO = os.fdopen(descriptor, "wb")
        except (OSError, ValueError):
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
        with writer:
            writer.write(payload)
            writer.flush()
            os.fsync(writer.fileno())
        yield path
    finally:
        path.unlink(missing_ok=True)


def _with_native_coordinates(
    messages: tuple[ParsedMessage, ...],
) -> tuple[ParsedMessage, ...]:
    """Attach DWD's separately published unstructured-grid CLAT/CLON values."""
    coordinates = {message.parameter.lower(): message for message in messages}
    # DWD filenames call these CLAT/CLON; ecCodes decodes them as TLAT/TLON.
    latitude_message = coordinates.get("tlat")
    longitude_message = coordinates.get("tlon")
    if latitude_message is None or longitude_message is None:
        raise ValueError(
            "ICON payload lacks required native CLAT/CLON grid fields: "
            f"{sorted(coordinates)}"
        )
    if (
        latitude_message.units != "Degree N"
        or longitude_message.units != "Degree E"
    ):
        raise ValueError("ICON CLAT/CLON fields must declare native degrees")
    if len(latitude_message.values) != len(longitude_message.values):
        raise ValueError("ICON CLAT/CLON grid field lengths differ")
    latitudes = latitude_message.values
    longitudes = longitude_message.values
    if not latitudes:
        raise ValueError("ICON CLAT/CLON grid fields are empty")
    if any(
        not math.isfinite(value) or not -90 <= value <= 90
        for value in latitudes
    ):
        raise ValueError("ICON CLAT values are outside latitude range")
    if any(
        not math.isfinite(value) or not -180 <= value <= 180
        for value in longitudes
    ):
        raise ValueError("ICON CLON values are outside longitude range")
    if (
        latitude_message.grid_type != "unstructured_grid"
        or longitude_message.grid_type != "unstructured_grid"
    ):
        raise ValueError("ICON CLAT/CLON fields must use unstructured_grid")
    if (
        not latitude_message.grid_uuid
        or latitude_message.grid_uuid != longitude_message.grid_uuid
    ):
        raise ValueError("ICON CLAT/CLON grid identities differ")
    if any(
        message.grid_type != latitude_message.grid_type
        or message.grid_uuid != latitude_message.grid_uuid
        for message in messages
    ):
        raise ValueError(
            "ICON messages do not share the CLAT/CLON grid identity"
        )
    if any(len(message.values) != len(latitudes) for message in messages):
        raise ValueError("ICON message and coordinate array lengths differ")
    return tuple(
        replace(message, latitudes=latitudes, longitudes=longitudes)
        for message in messages
    )
