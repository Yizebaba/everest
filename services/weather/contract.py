"""Typed, provider-neutral canonical weather contract.

This module performs contract/QC validation only. It has no I/O and no source
connector dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math
from typing import Optional


class RecordType(str, Enum):
    """Permitted canonical record types."""

    FORECAST = "forecast"
    OBSERVATION = "observation"
    SATELLITE = "satellite"
    DERIVED = "derived"


class QualityFlag(str, Enum):
    """Non-destructive QC outcomes."""

    CLEAN = "clean"
    MISSING_VALUE = "missing_value"
    OUT_OF_RANGE = "out_of_range"
    INVALID_TIMESTAMP = "invalid_timestamp"
    INVALID_COORDINATE = "invalid_coordinate"
    INVALID_UNIT = "invalid_unit"
    DUPLICATE = "duplicate"
    STALE = "stale"
    PROVENANCE_ERROR = "provenance_error"
    CYCLE_TIME_MISMATCH = "cycle_time_mismatch"


@dataclass(frozen=True)
class ForecastIdentity:
    """Identity of a model forecast run."""

    cycle: datetime
    lead_time: timedelta


# The flat canonical record intentionally exposes each schema field directly;
# this scoped exception keeps the contract readable and serializable.
@dataclass(frozen=True)
class WeatherRecord:  # pylint: disable=too-many-instance-attributes
    """One normalized weather record in canonical units."""

    record_type: RecordType
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    temperature: Optional[float]
    precipitation: Optional[float]
    visibility: Optional[float]
    source: str
    model: str
    forecast: Optional[ForecastIdentity] = None
    pressure: Optional[float] = None
    relative_humidity: Optional[float] = None
    dew_point: Optional[float] = None
    cloud_cover: Optional[float] = None
    cloud_base: Optional[float] = None
    cloud_top: Optional[float] = None
    snowfall: Optional[float] = None
    gust_speed: Optional[float] = None
    quality_flags: frozenset[str] = field(default_factory=frozenset)


def _finite(value: Optional[float]) -> bool:
    """Return whether an optional numeric value is finite."""

    return value is None or math.isfinite(value)


def validate_record(  # pylint: disable=too-many-branches
    record: WeatherRecord,
) -> frozenset[str]:
    """Return additive QC flags without mutating or deleting the record."""

    flags = set(record.quality_flags)
    if record.timestamp.tzinfo is None or record.timestamp.utcoffset() != (
        timedelta(0)
    ):
        flags.add(QualityFlag.INVALID_TIMESTAMP.value)
    if not _finite(record.latitude) or not _finite(record.longitude):
        flags.add(QualityFlag.INVALID_COORDINATE.value)
    elif (
        not -90 <= record.latitude <= 90 or not -180 <= record.longitude <= 180
    ):
        flags.add(QualityFlag.INVALID_COORDINATE.value)
    numeric_values = (
        record.altitude,
        record.wind_speed,
        record.wind_direction,
        record.temperature,
        record.precipitation,
        record.visibility,
        record.pressure,
        record.relative_humidity,
        record.dew_point,
        record.cloud_cover,
        record.cloud_base,
        record.cloud_top,
        record.snowfall,
        record.gust_speed,
    )
    if not all(_finite(value) for value in numeric_values):
        flags.add(QualityFlag.OUT_OF_RANGE.value)
    non_negative = (
        record.wind_speed,
        record.precipitation,
        record.visibility,
        record.cloud_base,
        record.cloud_top,
        record.snowfall,
        record.gust_speed,
    )
    if any(value is not None and value < 0 for value in non_negative):
        flags.add(QualityFlag.OUT_OF_RANGE.value)
    if (
        record.wind_direction is not None
        and not 0 <= record.wind_direction < 360
    ):
        flags.add(QualityFlag.OUT_OF_RANGE.value)
    if any(
        value is not None and not 0 <= value <= 100
        for value in (record.relative_humidity, record.cloud_cover)
    ):
        flags.add(QualityFlag.OUT_OF_RANGE.value)
    if not record.source or not record.model:
        flags.add(QualityFlag.PROVENANCE_ERROR.value)
    if record.record_type is RecordType.FORECAST:
        if record.forecast is None:
            flags.add(QualityFlag.PROVENANCE_ERROR.value)
        elif (
            record.timestamp
            != record.forecast.cycle + record.forecast.lead_time
        ):
            flags.add(QualityFlag.CYCLE_TIME_MISMATCH.value)
    elif record.forecast is not None:
        flags.add(QualityFlag.PROVENANCE_ERROR.value)
    if any(
        value is None
        for value in (
            record.wind_speed,
            record.temperature,
            record.visibility,
        )
    ):
        flags.add(QualityFlag.MISSING_VALUE.value)
    flags.discard(QualityFlag.CLEAN.value)
    if not flags:
        flags.add(QualityFlag.CLEAN.value)
    return frozenset(flags)
