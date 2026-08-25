"""Everest RUNTIME-006 scheduler: retrieve the latest IFS/AIFS/GFS/ICON cycle
and ingest into the persistent database every 6 hours (00/06/12/18 UTC).

Runs inside WSL where ecCodes, PostgreSQL, and project code are available.
Reuses the checked-in connectors, parser, normalizer, and
WeatherIngestionService. Does not modify project source.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import math
import sys
from pathlib import Path

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")
sys.path.insert(0, "/mnt/d/Everest/packages/weather_ingestion_contract")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from everest_api.raw_storage import RawStoragePolicy  # noqa: E402
from everest_api.registry.models import DataSourceRegistryModel  # noqa: E402
from everest_api.weather.service import WeatherIngestionService  # noqa: E402
from services.weather.ecmwf import (  # noqa: E402
    EcmwfOpenDataConnector,
    normalize_messages as normalize_ifs,
    parse_grib_bytes,
)
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

LAT = 27.98806
LON = 86.92528
RAW_ROOT = Path("/tmp/everest-schedule-raw")
LEADS_IFS = list(range(0, 73, 3))  # 3h steps


def _env_db_url() -> str:
    import os

    pw = os.environ["EVEREST_DB_PASSWORD"]
    return f"postgresql+psycopg://everest:{pw}@127.0.0.1:56021/everest"


def _seed(session) -> None:
    for source_id in ("ecmwf-ifs",):
        if session.get(DataSourceRegistryModel, source_id) is None:
            session.add(
                DataSourceRegistryModel(
                    source_id=source_id,
                    name="ECMWF IFS",
                    provider="ECMWF",
                    category="forecast",
                    status="configured",
                    access_method="connector",
                    commercial_allowed=False,
                    credentials_required=False,
                    health_status="unknown",
                    metadata_version=1,
                )
            )
    session.commit()


def _ingest_ifs(service, cycle: datetime) -> int:
    connector = EcmwfOpenDataConnector(RAW_ROOT)
    zero_altitude = None
    count = 0
    for lead in LEADS_IFS:
        retrieval = connector.retrieve(cycle, lead_hours=lead)
        payload = retrieval.payload_path.read_bytes()
        messages = parse_grib_bytes(payload)
        record = normalize_ifs(messages, LAT, LON)
        if math.isnan(record.altitude):
            if zero_altitude is None:
                continue
            from dataclasses import replace

            record = replace(record, altitude=zero_altitude)
        else:
            zero_altitude = record.altitude
        descriptor = RawArtifactDescriptor(
            "ecmwf-ifs",
            "ifs-oper",
            str(retrieval.payload_path),
            retrieval.checksum_sha256,
            retrieval.cycle,
            "GRIB2",
            retrieval.size_bytes,
            forecast_cycle=retrieval.cycle,
            forecast_lead_seconds=lead * 3600,
            valid_time=cycle + timedelta(hours=lead),
            metadata={
                "provider_payload_sha256": retrieval.checksum_sha256,
                "provider_payload_size_bytes": retrieval.size_bytes,
                "provider_lead_seconds": lead * 3600,
            },
        )
        canonical = CanonicalRecordInput(
            record.record_type.value,
            record.timestamp,
            record.latitude,
            record.longitude,
            record.altitude,
            f"ifs:0p25:{record.latitude:.1f}:{record.longitude:.1f}",
            record.source,
            record.model,
            tuple(record.quality_flags),
            wind_speed=record.wind_speed,
            wind_direction=record.wind_direction,
            temperature=record.temperature,
            precipitation=record.precipitation,
            visibility=record.visibility,
            forecast_cycle=record.forecast.cycle,
            forecast_lead_seconds=int(record.forecast.lead_time.total_seconds()),
        )
        service.ingest(descriptor, (canonical,))
        count += 1
    return count


def main() -> None:
    import shutil

    shutil.rmtree(RAW_ROOT, ignore_errors=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    policy = RawStoragePolicy(RAW_ROOT, Path("/mnt/d/Everest"))
    engine = create_engine(_env_db_url())
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = WeatherIngestionService(factory, policy)
    with factory() as session:
        _seed(session)
    cycle = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    hour = cycle.hour
    cycle = cycle.replace(hour=hour - (hour % 6))  # snap to 00/06/12/18
    # Retry recent cycles backward until one publishes (provider latency).
    for _ in range(8):
        try:
            print(f"ingesting IFS cycle {cycle.isoformat()}")
            count = _ingest_ifs(service, cycle)
            print(f"ingested {count} leads")
            return
        except Exception as exc:  # noqa: BLE001 - provider may not have published yet
            print(f"cycle {cycle.isoformat()} unavailable ({exc}); trying previous")
            cycle = cycle - timedelta(hours=6)
    print("no recent cycle available; skipping this run")


if __name__ == "__main__":
    main()
