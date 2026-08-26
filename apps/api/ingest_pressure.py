"""Retrieve IFS pressure levels for the Everest grid point and persist them.

Produces one canonical weather record per pressure level (altitude from
geopotential height), enabling true vertical-profile wind/temperature at the
summit (300 hPa ~ 9800 m) instead of grid-point surface approximation.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")
sys.path.insert(0, "/mnt/d/Everest/packages/weather_ingestion_contract")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from everest_api.raw_storage import RawStoragePolicy  # noqa: E402
from everest_api.registry.models import DataSourceRegistryModel  # noqa: E402
from everest_api.weather.service import WeatherIngestionService  # noqa: E402
from services.weather.ecmwf.pressure import (  # noqa: E402
    normalize_pressure_levels,
    parse_pressure_messages,
)
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

CYCLE = "20260824"
LEAD = 0
LAT = 27.98806
LON = 86.92528
RAW_ROOT = Path("/tmp/everest-pressure-raw")


def db_url() -> str:
    from everest_api.persistence.database import resolve_database_url

    return resolve_database_url()


def fetch_pressure() -> bytes:
    base = (
        f"https://data.ecmwf.int/forecasts/{CYCLE}/00z/ifs/0p25/oper/"
        f"{CYCLE}000000-{LEAD}h-oper-fc"
    )
    with urllib.request.urlopen(base + ".index") as resp:
        rows = [json.loads(l) for l in resp.read().decode().splitlines() if l]
    sel = [
        r
        for r in rows
        if r.get("levtype") == "pl"
        and r.get("param") in ("u", "v", "t", "gh")
        and r.get("levelist") in ("850", "700", "500", "300")
    ]
    sel.sort(key=lambda r: r["_offset"])
    buf = bytearray()
    for r in sel:
        end = r["_offset"] + r["_length"] - 1
        req = urllib.request.Request(
            base + ".grib2", headers={"Range": f"bytes={r['_offset']}-{end}"}
        )
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            if len(body) != r["_length"]:
                raise RuntimeError("range length mismatch")
            buf.extend(body)
    return bytes(buf)


def main() -> None:
    import shutil

    shutil.rmtree(RAW_ROOT, ignore_errors=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    policy = RawStoragePolicy(RAW_ROOT, Path("/mnt/d/Everest"))
    engine = create_engine(db_url())
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = WeatherIngestionService(factory, policy)

    payload = fetch_pressure()
    messages = parse_pressure_messages(payload)
    records = normalize_pressure_levels(messages, LAT, LON)
    print(f"pressure records: {len(records)}")

    digest = hashlib.sha256(payload).hexdigest()
    artifact_path = RAW_ROOT / "ecmwf-ifs" / digest / "pressure.grib2"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(payload)

    with factory() as session:
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

    from datetime import UTC, datetime

    cycle = datetime(2026, 8, 24, tzinfo=UTC)
    for r in records:
        descriptor = RawArtifactDescriptor(
            "ecmwf-ifs",
            "ifs-pressure",
            str(artifact_path),
            digest,
            cycle,
            "GRIB2",
            len(payload),
            forecast_cycle=r.cycle,
            forecast_lead_seconds=r.lead_seconds,
            metadata={
                "provider_payload_sha256": digest,
                "provider_payload_size_bytes": len(payload),
                "provider_lead_seconds": r.lead_seconds,
            },
        )
        canonical = CanonicalRecordInput(
            "forecast",
            r.timestamp,
            LAT,
            LON,
            r.altitude,
            f"ifs:0p25:28.0:87.0:{r.level_hpa}hpa",
            r.source,
            r.model,
            ("clean",),
            wind_speed=r.wind_speed,
            wind_direction=r.wind_direction,
            temperature=r.temperature_c,
            forecast_cycle=r.cycle,
            forecast_lead_seconds=r.lead_seconds,
        )
        service.ingest(descriptor, (canonical,))
        print(
            f"ingested {r.level_hpa}hPa alt={r.altitude:.0f}m "
            f"wind={r.wind_speed:.1f} t={r.temperature_c:.1f}C"
        )

    from sqlalchemy import func, select  # noqa: PLC0415

    from everest_api.weather.models import WeatherRecordModel  # noqa: PLC0415

    with factory() as session:
        total = session.scalar(select(func.count()).select_from(WeatherRecordModel))
        print(f"total weather records now: {total}")


if __name__ == "__main__":
    main()
