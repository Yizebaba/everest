"""Canonical weather contract package."""

from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
    validate_record,
)

__all__ = [
    "ForecastIdentity",
    "QualityFlag",
    "RecordType",
    "WeatherRecord",
    "validate_record",
]
