"""AIFS Single messages to canonical weather normalization and QC."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timezone
import math

from services.weather.aifs.parser import (
    ParsedMessage,
    validate_decoded_inventory,
)
from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
    validate_record,
)


EXPECTED_UNITS = {
    "z": "m**2 s**-2",
    "10u": "m s**-1",
    "10v": "m s**-1",
    "2t": "K",
    "tp": "kg m**-2",
}


@dataclass(frozen=True)
class AifsQualityEvidence:
    """Deterministic source-specific evidence contributing additive QC."""

    source_identity_valid: bool = True
    checksum_valid: bool = True
    inventory_valid: bool = True
    stale: bool = False
    duplicate: bool = False


def normalize_messages(
    messages: tuple[ParsedMessage, ...],
    latitude: float,
    longitude: float,
    evidence: AifsQualityEvidence | None = None,
) -> WeatherRecord:
    """Select the nearest provider cell and convert explicit AIFS units."""
    _validate_request(latitude, longitude)
    if not messages:
        raise ValueError("at least one AIFS message is required")
    validate_decoded_inventory(messages)
    anchor = messages[0]
    index = nearest_grid_index(anchor, latitude, longitude)
    values, flags = _values_and_flags(messages, index)
    flags.update(_source_quality_flags(evidence or AifsQualityEvidence()))
    u_wind = values.get("10u")
    v_wind = values.get("10v")
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
    geopotential = values.get("z")
    record = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=anchor.valid_time.astimezone(timezone.utc),
        latitude=anchor.latitudes[index],
        longitude=_canonical_longitude(anchor.longitudes[index]),
        altitude=(
            geopotential / 9.80665 if geopotential is not None else math.nan
        ),
        wind_speed=speed,
        wind_direction=direction,
        temperature=(values["2t"] - 273.15 if "2t" in values else None),
        precipitation=values.get("tp"),
        visibility=None,
        source="ecmwf-aifs",
        model="AIFS",
        forecast=ForecastIdentity(
            anchor.cycle.astimezone(timezone.utc),
            anchor.valid_time.astimezone(timezone.utc)
            - anchor.cycle.astimezone(timezone.utc),
        ),
        quality_flags=frozenset(flags),
    )
    return replace(record, quality_flags=validate_record(record))


def nearest_grid_index(
    message: ParsedMessage, latitude: float, longitude: float
) -> int:
    """Return the exact flat index of the nearest provider grid cell."""
    _validate_request(latitude, longitude)
    return min(
        range(len(message.values)),
        key=lambda item: (message.latitudes[item] - latitude) ** 2
        + (_longitude_distance(message.longitudes[item], longitude)) ** 2,
    )


def provider_spatial_key(message: ParsedMessage, index: int) -> str:
    """Build AIFS regular-grid identity from dimensions and flat index."""
    if message.grid_type != "regular_ll" or not 0 <= index < len(
        message.values
    ):
        raise ValueError("AIFS message lacks valid regular-grid provenance")
    return f"aifs-single:0p25:{message.ni}x{message.nj}:{index}"


def _values_and_flags(
    messages: tuple[ParsedMessage, ...], index: int
) -> tuple[dict[str, float], set[str]]:
    """Keep finite, unit-validated values and add non-destructive QC."""
    values: dict[str, float] = {}
    flags: set[str] = set()
    for message in messages:
        expected = EXPECTED_UNITS.get(message.parameter)
        if expected is not None and message.units != expected:
            flags.add(QualityFlag.INVALID_UNIT.value)
            continue
        value = message.values[index]
        if not math.isfinite(value):
            flags.add(QualityFlag.MISSING_VALUE.value)
            continue
        values[message.parameter] = value
    return values, flags


def _validate_request(latitude: float, longitude: float) -> None:
    """Reject non-finite or out-of-range WGS 84 request coordinates."""
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValueError("AIFS requested coordinates must be finite")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("AIFS requested coordinates are outside WGS 84 ranges")


def _source_quality_flags(evidence: AifsQualityEvidence) -> set[str]:
    """Map explicit source/checksum/inventory/stale/duplicate evidence to QC."""
    flags: set[str] = set()
    if not (
        evidence.source_identity_valid
        and evidence.checksum_valid
        and evidence.inventory_valid
    ):
        flags.add(QualityFlag.PROVENANCE_ERROR.value)
    if evidence.stale:
        flags.add(QualityFlag.STALE.value)
    if evidence.duplicate:
        flags.add(QualityFlag.DUPLICATE.value)
    return flags


def _canonical_longitude(longitude: float) -> float:
    """Represent provider 0..360 longitude in canonical -180..180 form."""
    return longitude - 360 if longitude > 180 else longitude


def _longitude_distance(provider: float, requested: float) -> float:
    """Return shortest angular longitude distance without changing identity."""
    return ((_canonical_longitude(provider) - requested + 180) % 360) - 180
