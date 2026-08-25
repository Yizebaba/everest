"""Tests for the executable canonical weather contract."""

from datetime import datetime, timedelta, timezone

from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
    validate_record,
)


def _record(**overrides: object) -> WeatherRecord:
    """Build a valid observation fixture with explicit nullable fields."""

    values = {
        "record_type": RecordType.OBSERVATION,
        "timestamp": datetime(2026, 8, 21, tzinfo=timezone.utc),
        "latitude": 27.9881,
        "longitude": 86.9250,
        "altitude": 5364.0,
        "wind_speed": 4.0,
        "wind_direction": 90.0,
        "temperature": -8.0,
        "precipitation": 0.0,
        "visibility": 10000.0,
        "source": "test-source",
        "model": "instrument-v1",
    }
    values.update(overrides)
    return WeatherRecord(**values)


def test_valid_observation_is_clean() -> None:
    """A complete observation passes without a warning flag."""

    assert validate_record(_record()) == frozenset({QualityFlag.CLEAN.value})


def test_forecast_requires_consistent_identity() -> None:
    """A forecast cycle and lead must reproduce its valid timestamp."""

    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    record = _record(
        record_type=RecordType.FORECAST,
        forecast=ForecastIdentity(cycle, timedelta(hours=6)),
        timestamp=cycle + timedelta(hours=7),
    )
    assert QualityFlag.CYCLE_TIME_MISMATCH.value in validate_record(record)


def test_qc_flags_invalid_values_without_deletion() -> None:
    """Invalid values are flagged and remain present on the frozen record."""

    record = _record(latitude=95.0, wind_speed=-1.0, temperature=None)
    flags = validate_record(record)
    assert QualityFlag.INVALID_COORDINATE.value in flags
    assert QualityFlag.OUT_OF_RANGE.value in flags
    assert QualityFlag.MISSING_VALUE.value in flags
    assert record.temperature is None
