"""Fetch the latest published IFS and GFS forecasts and ingest them.

Pulls real data from the official providers (no fabricated values):
- ECMWF IFS Open Data, latest published cycle (default 2026-08-25 06Z),
  leads 0/3/6/12/24/48/72 h, variables z/10u/10v/2t/tp.
- NOAA GFS, latest published cycle (default 2026-08-25 12Z),
  leads f000/f003/f006/f024, variables TMP/UGRD/VGRD/VIS/APCP.
Normalizes to the canonical weather model and persists raw + canonical records
through WeatherIngestionService. Run inside WSL with the project venv:
  /tmp/everest-venv/bin/python apps/api/ingest_latest_forecast.py
"""

# pylint: disable=wrong-import-position,wrong-import-order,import-outside-toplevel
# sys.path insertion before local imports is required for this standalone
# script; lazy imports keep the hot path light.

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")
sys.path.insert(0, "/mnt/d/Everest/packages/weather_ingestion_contract")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from everest_api.persistence.database import resolve_database_url  # noqa: E402
from everest_api.raw_storage import RawStoragePolicy  # noqa: E402
from everest_api.registry.models import DataSourceRegistryModel  # noqa: E402
from everest_api.weather.service import WeatherIngestionService  # noqa: E402
from services.weather.ecmwf import (  # noqa: E402
    EcmwfOpenDataConnector,
    normalize_messages as normalize_ifs,
    parse_grib_bytes as parse_ifs,
)
from services.weather.gfs.connector import GfsNcepConnector  # noqa: E402
from services.weather.gfs.normalizer import (  # noqa: E402
    normalize_messages as normalize_gfs,
)
from services.weather.gfs.parser import (  # noqa: E402
    parse_grib_bytes as parse_gfs,
)
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

LAT = 27.98806
LON = 86.92528
IFS_CYCLE = datetime(2026, 8, 25, 6, 0, tzinfo=timezone.utc)
GFS_CYCLE = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
IFS_LEADS = (0, 3, 6, 12, 24, 48, 72)
GFS_LEADS = (3, 6, 24)
DB_URL = resolve_database_url()
RAW_ROOT = Path("/mnt/d/Everest-data/raw")


def _seed(session) -> None:
    """Ensure registry rows exist for every source before ingestion."""
    for source_id, name in (
        ("ecmwf-ifs", "ECMWF IFS"),
        ("noaa-gfs", "NOAA GFS"),
    ):
        if session.get(DataSourceRegistryModel, source_id) is None:
            session.add(
                DataSourceRegistryModel(
                    source_id=source_id,
                    name=name,
                    provider="official forecast provider",
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


def _ingest_ifs(service) -> int:
    """Fetch and ingest the latest IFS cycle at several leads."""
    connector = EcmwfOpenDataConnector(RAW_ROOT)
    count = 0
    zero_altitude = None
    for lead in IFS_LEADS:
        retrieval = connector.retrieve(IFS_CYCLE, lead_hours=lead)
        payload = retrieval.payload_path.read_bytes()
        messages = parse_ifs(payload)
        record = normalize_ifs(messages, LAT, LON)
        if record.altitude != record.altitude:  # NaN check
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
            valid_time=IFS_CYCLE + timedelta(hours=lead),
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
        print(f"  IFS lead {lead:3d}h: alt={record.altitude:.0f} m, "
              f"t={record.temperature:.1f} C, p={record.precipitation}, "
              f"vis={record.visibility}")
    return count


def _ingest_gfs(service) -> int:
    """Fetch and ingest the latest GFS cycle at several leads."""
    connector = GfsNcepConnector(RAW_ROOT)
    count = 0
    for lead in GFS_LEADS:
        retrieval = connector.retrieve(GFS_CYCLE, lead_hours=lead)
        payload = retrieval.payload_path.read_bytes()
        messages = parse_gfs(payload)
        record = normalize_gfs(messages, LAT, LON)
        descriptor = RawArtifactDescriptor(
            "noaa-gfs",
            "gfs-oper",
            str(retrieval.payload_path),
            retrieval.sha256,
            retrieval.cycle,
            "GRIB2",
            retrieval.size_bytes,
            forecast_cycle=retrieval.cycle,
            forecast_lead_seconds=lead * 3600,
            valid_time=GFS_CYCLE + timedelta(hours=lead),
            metadata={
                "provider_payload_sha256": retrieval.sha256,
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
            f"gfs:0p25:{record.latitude:.1f}:{record.longitude:.1f}",
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
        print(f"  GFS lead {lead:3d}h: alt={record.altitude:.0f} m, "
              f"t={record.temperature:.1f} C, p={record.precipitation}, "
              f"vis={record.visibility}")
    return count


def main() -> None:
    """Run one full forecast refresh pass."""
    policy = RawStoragePolicy(RAW_ROOT, Path("/mnt/d/Everest"))
    engine = create_engine(DB_URL)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = WeatherIngestionService(factory, policy)
    with factory() as session:
        _seed(session)
    try:
        print(f"IFS cycle {IFS_CYCLE.isoformat()} ...")
        n = _ingest_ifs(service)
        print(f"IFS ingested {n} records")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"IFS ingestion failed: {exc}")
    try:
        print(f"GFS cycle {GFS_CYCLE.isoformat()} ...")
        n = _ingest_gfs(service)
        print(f"GFS ingested {n} records")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"GFS ingestion failed: {exc}")
    print("done")


if __name__ == "__main__":
    main()
