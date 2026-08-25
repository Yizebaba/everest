"""Unit tests for the pressure-level risk assessment bridge (EV-RISK-001)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from everest_api.weather.models import WeatherRecordModel
from risk_assess import _to_weather_record


def _row() -> WeatherRecordModel:
    ts = datetime(2026, 8, 24, tzinfo=UTC)
    return WeatherRecordModel(
        record_id=uuid4(),
        raw_artifact_id=uuid4(),
        source_id="ecmwf-ifs",
        dataset="ifs-pressure",
        record_type="forecast",
        timestamp=ts,
        latitude=27.98806,
        longitude=86.92528,
        altitude=9797.0,
        spatial_key="ifs:0p25:28.0:87.0:300hpa",
        model="IFS",
        forecast_cycle=ts,
        forecast_lead_seconds=0,
        quality_flags=["clean"],
        wind_speed=8.8,
        wind_direction=90.0,
        temperature=-24.1,
    )


def test_pressure_row_maps_to_weather_record() -> None:
    """A persisted pressure-level row maps to a WeatherRecord for the engine."""
    record = _to_weather_record(_row())
    assert record.altitude == pytest.approx(9797.0)
    assert record.wind_speed == pytest.approx(8.8)
    assert record.temperature == pytest.approx(-24.1)
    assert record.source == "ecmwf-ifs"
    assert record.forecast is not None
    assert record.forecast.lead_time == timedelta(0)
    assert record.record_type.value == "forecast"
    assert {f.value for f in record.quality_flags} == {"clean"}


def test_quality_flags_mapped() -> None:
    """Quality flags translate into canonical QualityFlag values."""
    row = _row()
    row.quality_flags = ["clean", "missing_value"]
    record = _to_weather_record(row)
    assert {f.value for f in record.quality_flags} == {
        "clean",
        "missing_value",
    }
