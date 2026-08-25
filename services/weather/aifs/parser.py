"""Actual AIFS Single GRIB2 parsing with explicit model identity."""

# AIFS parsing remains independent so IFS cannot obscure provider identity.
# pylint: disable=duplicate-code

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from typing import BinaryIO, Iterator


EXPECTED_PARAMETERS = ("z", "10u", "10v", "2t", "tp")
EXPECTED_LEVELS = {
    "z": ("surface", 0.0),
    "10u": ("heightAboveGround", 10.0),
    "10v": ("heightAboveGround", 10.0),
    "2t": ("heightAboveGround", 2.0),
    "tp": ("surface", 0.0),
}
EXPECTED_PROCESS_IDENTIFIER = 5


@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class ParsedMessage:  # pylint: disable=too-many-instance-attributes
    """One decoded AIFS message and provider regular-grid identity."""

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
    ni: int
    nj: int
    generating_process_identifier: int
    level: float | None = None


def parse_grib_bytes(payload: bytes) -> tuple[ParsedMessage, ...]:
    """Parse real AIFS GRIB2 messages; fail rather than fabricate data."""
    try:
        from eccodes import (  # pylint: disable=import-outside-toplevel
            codes_get,
            codes_get_array,
            codes_grib_new_from_file,
            codes_release,
        )
    except (ImportError, RuntimeError) as error:
        raise RuntimeError("ecCodes is required to parse AIFS GRIB2") from error
    messages: list[ParsedMessage] = []
    with _temporary_grib(payload) as path:
        with path.open("rb") as stream:
            while handle := codes_grib_new_from_file(stream):
                try:
                    cycle = datetime.strptime(
                        f'{int(codes_get(handle, "dataDate")):08d}'
                        f'{int(codes_get(handle, "dataTime")):04d}',
                        "%Y%m%d%H%M",
                    ).replace(tzinfo=timezone.utc)
                    valid = datetime.strptime(
                        f'{int(codes_get(handle, "validityDate")):08d}'
                        f'{int(codes_get(handle, "validityTime")):04d}',
                        "%Y%m%d%H%M",
                    ).replace(tzinfo=timezone.utc)
                    lead_seconds = (valid - cycle).total_seconds()
                    if lead_seconds < 0 or lead_seconds % 3600:
                        raise ValueError("AIFS lead is not a whole hour")
                    process = int(
                        codes_get(handle, "generatingProcessIdentifier")
                    )
                    messages.append(
                        ParsedMessage(
                            parameter=str(codes_get(handle, "shortName")),
                            valid_time=valid,
                            cycle=cycle,
                            lead_hours=int(lead_seconds // 3600),
                            values=tuple(
                                map(float, codes_get_array(handle, "values"))
                            ),
                            latitudes=tuple(
                                map(float, codes_get_array(handle, "latitudes"))
                            ),
                            longitudes=tuple(
                                map(
                                    float, codes_get_array(handle, "longitudes")
                                )
                            ),
                            units=str(codes_get(handle, "units")),
                            level_type=str(codes_get(handle, "typeOfLevel")),
                            level=float(codes_get(handle, "level")),
                            grid_type=str(codes_get(handle, "gridType")),
                            ni=int(codes_get(handle, "Ni")),
                            nj=int(codes_get(handle, "Nj")),
                            generating_process_identifier=process,
                        )
                    )
                finally:
                    codes_release(handle)
    if not messages:
        raise ValueError("payload did not contain an AIFS GRIB message")
    decoded = tuple(messages)
    validate_decoded_inventory(decoded)
    _validate_common_grid(decoded)
    return decoded


def validate_decoded_inventory(messages: tuple[ParsedMessage, ...]) -> None:
    """Require the exact retained AIFS field inventory and native levels."""
    parameters = tuple(message.parameter for message in messages)
    unexpected = sorted(set(parameters) - set(EXPECTED_PARAMETERS))
    missing = sorted(set(EXPECTED_PARAMETERS) - set(parameters))
    duplicates = sorted(
        parameter
        for parameter in set(parameters)
        if parameters.count(parameter) != 1
    )
    if (
        unexpected
        or missing
        or duplicates
        or len(messages) != len(EXPECTED_PARAMETERS)
    ):
        raise ValueError(
            "AIFS decoded inventory mismatch: "
            f"missing={missing}, duplicates={duplicates}, "
            f"unexpected={unexpected}"
        )
    for message in messages:
        expected_type, expected_level = EXPECTED_LEVELS[message.parameter]
        if (
            message.level_type != expected_type
            or message.level != expected_level
        ):
            raise ValueError(
                "AIFS decoded level mismatch for "
                f"{message.parameter}: expected "
                f"{expected_type}/{expected_level:g}, got "
                f"{message.level_type}/{message.level}"
            )
        if message.generating_process_identifier != EXPECTED_PROCESS_IDENTIFIER:
            raise ValueError(
                "AIFS decoded process identifier mismatch for "
                f"{message.parameter}"
            )


def _validate_common_grid(messages: tuple[ParsedMessage, ...]) -> None:
    """Require every selected field to share one complete provider grid."""
    anchor = messages[0]
    expected_length = anchor.ni * anchor.nj
    if anchor.grid_type != "regular_ll" or expected_length <= 0:
        raise ValueError(
            "AIFS Open Data must use a regular latitude/longitude grid"
        )
    for message in messages:
        grid_mismatch = (
            message.grid_type != anchor.grid_type
            or message.ni != anchor.ni
            or message.nj != anchor.nj
        )
        array_mismatch = (
            len(message.values) != expected_length
            or len(message.latitudes) != expected_length
            or len(message.longitudes) != expected_length
        )
        time_mismatch = (
            message.cycle != anchor.cycle
            or message.valid_time != anchor.valid_time
        )
        if grid_mismatch or array_mismatch or time_mismatch:
            raise ValueError("AIFS selected messages do not share one grid/run")


@contextmanager
def _temporary_grib(payload: bytes) -> Iterator[Path]:
    """Expose closed temporary bytes to ecCodes and always unlink them."""
    descriptor, name = tempfile.mkstemp(suffix=".grib2")
    path = Path(name)
    try:
        writer: BinaryIO = os.fdopen(descriptor, "wb")
        with writer:
            writer.write(payload)
            writer.flush()
            os.fsync(writer.fileno())
        yield path
    finally:
        path.unlink(missing_ok=True)
