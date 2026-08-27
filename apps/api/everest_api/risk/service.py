"""Read-only canonical-weather adapter for the existing risk engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.risk.engine import assess  # pylint: disable=import-error
from services.weather.contract import (  # pylint: disable=import-error
    ForecastIdentity,
    RecordType,
    WeatherRecord,
)
from everest_api.weather.models import WeatherRecordModel


_MAX_CANDIDATES = 100
_MAX_FACTORS = 16


def _as_utc(value: datetime) -> datetime:
    return (
        value.replace(tzinfo=UTC)
        if value.tzinfo is None
        else value.astimezone(UTC)
    )


def to_weather_record(row: WeatherRecordModel) -> WeatherRecord:
    """Convert one persisted canonical model to the engine's canonical type."""
    timestamp = _as_utc(row.timestamp)
    forecast = None
    if row.forecast_cycle is not None:
        lead_seconds = row.forecast_lead_seconds
        if lead_seconds is None:
            lead_seconds = int(
                (timestamp - _as_utc(row.forecast_cycle)).total_seconds()
            )
        forecast = ForecastIdentity(
            _as_utc(row.forecast_cycle), timedelta(seconds=lead_seconds)
        )
    return WeatherRecord(
        record_type=RecordType(row.record_type),
        timestamp=timestamp,
        latitude=row.latitude,
        longitude=row.longitude,
        altitude=row.altitude,
        wind_speed=row.wind_speed,
        wind_direction=row.wind_direction,
        temperature=row.temperature,
        precipitation=row.precipitation,
        visibility=row.visibility,
        source=row.source_id,
        model=row.model,
        forecast=forecast,
        pressure=row.pressure,
        relative_humidity=row.relative_humidity,
        dew_point=row.dew_point,
        cloud_cover=row.cloud_cover,
        cloud_base=row.cloud_base,
        cloud_top=row.cloud_top,
        snowfall=row.snowfall,
        gust_speed=row.gust_speed,
        quality_flags=frozenset(row.quality_flags or ()),
    )


def _unknown() -> dict[str, Any]:
    return {
        "level": "unknown",
        "confidence": 0.0,
        "valid_time": None,
        "profile": "SUMMIT",
        "altitude_metres": None,
        "factors": [],
        "inputs": {},
        "basis": "no_persisted_record",
    }


def _public_result(result: Any) -> dict[str, Any]:
    """Project only bounded non-secret engine output fields."""
    inputs = result.inputs if isinstance(result.inputs, dict) else {}
    return {
        "level": result.level.value,
        "confidence": max(0.0, min(float(result.confidence), 1.0)),
        "valid_time": _as_utc(result.valid_time)
        .isoformat()
        .replace("+00:00", "Z"),
        "profile": "SUMMIT",
        "altitude_metres": result.altitude_metres,
        "factors": list(result.factors)[:_MAX_FACTORS],
        "inputs": {
            key: inputs[key]
            for key in ("source", "model", "cycle", "lead_s")
            if key in inputs
        },
        "basis": "persisted_canonical_weather",
    }


def assess_summit_window(session: Session) -> dict[str, Any]:
    """Assess the best persisted summit basis without provider-side I/O."""
    statement = (
        select(WeatherRecordModel)
        .where(
            WeatherRecordModel.record_type == "forecast",
            WeatherRecordModel.route_profile == "SUMMIT",
        )
        .order_by(WeatherRecordModel.timestamp.desc())
        .limit(_MAX_CANDIDATES)
    )
    candidates = [
        row
        for row in session.scalars(statement).all()
        if row.route_profile == "SUMMIT"
    ]
    if not candidates:
        return _unknown()
    selected = max(candidates, key=lambda row: _as_utc(row.timestamp))
    result = assess(to_weather_record(selected), profile="SUMMIT")
    return _public_result(result)
