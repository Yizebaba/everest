"""Ingest the retained immutable IFS raw artifact into the running database.

Reads the approved external raw root artifact recorded in docs/data-sources.md
(cycle 2026-08-24 00Z, lead 0, variables z/10u/10v/2t) rather than re-downloading
from ECMWF. Parses with ecCodes, normalizes to the canonical weather model, and
persists raw + canonical records through WeatherIngestionService. Run inside WSL
with the project venv: /tmp/everest-venv/bin/python apps/api/ingest_retained_ifs.py
"""

# pylint: disable=wrong-import-position,wrong-import-order,import-outside-toplevel
# sys.path insertion before local imports is required for this standalone
# script; lazy imports keep the hot path light.

from __future__ import annotations

import hashlib
import sys
from datetime import timedelta
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
from services.weather.ecmwf import normalize_messages, parse_grib_bytes  # noqa: E402
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

LAT = 27.98806
LON = 86.92528
RAW_ROOT = Path("/mnt/d/Everest-data/raw")
ARTIFACT_DIR = (
    RAW_ROOT
    / "ecmwf-ifs"
    / "638a075b6ba11c52131c6bc4ad05e49b2c8932d7026c99c3be6658d5315e1650"
)
PAYLOAD = ARTIFACT_DIR / "20260824000000-0h-oper-fc.grib2"
CYCLE = "2026-08-24T00:00:00Z"
LEAD_HOURS = 0
DB_URL = resolve_database_url()


def _seed(session) -> None:
    """Ensure the ecmwf-ifs registry row exists before ingestion."""
    if session.get(DataSourceRegistryModel, "ecmwf-ifs") is None:
        session.add(
            DataSourceRegistryModel(
                source_id="ecmwf-ifs",
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


def main() -> None:
    """Parse the retained IFS payload and persist raw + canonical records."""
    if not PAYLOAD.exists():
        raise SystemExit(f"retained IFS payload missing: {PAYLOAD}")
    payload = PAYLOAD.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    print(f"payload: {len(payload)} bytes, sha256={digest[:16]}...")

    messages = parse_grib_bytes(payload)
    record = normalize_messages(messages, LAT, LON)
    print(
        f"normalized: alt={record.altitude:.1f} m, "
        f"temp={record.temperature:.1f} C, wind={record.wind_speed:.1f} m/s"
    )

    policy = RawStoragePolicy(RAW_ROOT, Path("/mnt/d/Everest"))
    engine = create_engine(DB_URL)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = WeatherIngestionService(factory, policy)

    with factory() as session:
        _seed(session)

    descriptor = RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-oper",
        str(PAYLOAD),
        digest,
        record.timestamp,
        "GRIB2",
        len(payload),
        forecast_cycle=record.forecast.cycle,
        forecast_lead_seconds=0,
        valid_time=record.timestamp + timedelta(hours=LEAD_HOURS),
        metadata={
            "provider_payload_sha256": digest,
            "provider_payload_size_bytes": len(payload),
            "provider_lead_seconds": 0,
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
    print("ingest OK")


if __name__ == "__main__":
    main()
