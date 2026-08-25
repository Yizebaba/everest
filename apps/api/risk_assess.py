"""Assess the Summit Window risk from the IFS 300 hPa (summit-height) record.

Reuses the EV-RISK-001 engine with the highest pressure level (300 hPa ~
9797 m) that approximates the summit, instead of the grid-point surface value.
"""

# sys.path insertion before local imports is required for this standalone
# script; pylint import-order rules are not applicable to the execution layout.
# pylint: disable=wrong-import-position,wrong-import-order,missing-function-docstring

from __future__ import annotations

import os
import sys

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")
sys.path.insert(0, "/mnt/d/Everest/packages/weather_ingestion_contract")

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from everest_api.weather.models import WeatherRecordModel  # noqa: E402
from services.risk import DEFAULT_THRESHOLDS, assess  # noqa: E402
from services.weather.contract import (  # noqa: E402
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
)


def db_url() -> str:
    pw = os.environ["EVEREST_DB_PASSWORD"]
    return f"postgresql+psycopg://everest:{pw}@127.0.0.1:56021/everest"


def _to_weather_record(row: WeatherRecordModel) -> WeatherRecord:
    flags = frozenset(QualityFlag(f) for f in (row.quality_flags or []))
    forecast = (
        ForecastIdentity(row.forecast_cycle, row.timestamp - row.forecast_cycle)
        if row.forecast_cycle is not None
        else None
    )
    return WeatherRecord(
        record_type=RecordType(row.record_type),
        timestamp=row.timestamp,
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
        quality_flags=flags,
    )


def main() -> None:
    engine = create_engine(db_url())
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        # Highest retained pressure level (300 hPa ~ summit) for ECMWF IFS.
        row = (
            session.execute(
                select(WeatherRecordModel)
                .where(
                    WeatherRecordModel.source_id == "ecmwf-ifs",
                    WeatherRecordModel.spatial_key.like("%hpa"),
                )
                .order_by(WeatherRecordModel.altitude.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if row is None:
            print("no pressure-level record found; ingest pressure first")
            return
        print(
            f"assessing {row.spatial_key} alt={row.altitude:.0f}m "
            f"wind={row.wind_speed:.1f} t={row.temperature:.1f}C"
        )
        record = _to_weather_record(row)
        result = assess(record, DEFAULT_THRESHOLDS)
        print("=" * 40)
        print(f"level:       {result.level.value}")
        print(f"confidence:  {result.confidence:.2f}")
        print(f"factors:     {result.factors}")


if __name__ == "__main__":
    main()
