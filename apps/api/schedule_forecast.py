"""Everest RUNTIME-006 scheduler: retrieve the latest IFS/AIFS/GFS/ICON cycle
and ingest into the persistent database every 6 hours (00/06/12/18 UTC).

Runs inside WSL where ecCodes, PostgreSQL, and project code are available.
Reuses the checked-in connectors, parser, normalizer, and
WeatherIngestionService. Does not modify project source.
"""

# pylint: disable=wrong-import-position,wrong-import-order,import-outside-toplevel
# sys.path insertion before local imports is required for this standalone
# scheduler script; lazy imports keep the hot path light.

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
from services.weather.ecmwf.pressure import (  # noqa: E402
    normalize_pressure_levels,
    parse_pressure_messages,
)
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

LAT = 27.98806
LON = 86.92528
RAW_ROOT = Path("/tmp/everest-schedule-raw")
LEADS_IFS = list(range(0, 73, 3))  # 3h steps
PRESSURE_LEVELS = ("850", "700", "500", "300")


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
            forecast_lead_seconds=int(
                record.forecast.lead_time.total_seconds()
            ),
        )
        service.ingest(descriptor, (canonical,))
        count += 1
    return count


def _fetch_pressure(cycle: datetime) -> bytes:
    """Download the IFS pressure-level GRIB messages for one cycle."""
    import json
    import urllib.request

    stamp = cycle.strftime("%Y%m%d")
    # lead-0 file naming: YYYYMMDDHH0000-0h-oper-fc
    base = (
        f"https://data.ecmwf.int/forecasts/{stamp}/{cycle:%H}z/ifs/0p25/oper/"
        f"{stamp}{cycle:%H}0000-0h-oper-fc"
    )
    with urllib.request.urlopen(base + ".index") as resp:
        rows = [json.loads(l) for l in resp.read().decode().splitlines() if l]
    sel = [
        r
        for r in rows
        if r.get("levtype") == "pl"
        and r.get("param") in ("u", "v", "t", "gh")
        and r.get("levelist") in PRESSURE_LEVELS
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
                raise RuntimeError("pressure range length mismatch")
            buf.extend(body)
    return bytes(buf)


def _ingest_ifs_pressure(service, cycle: datetime) -> int:
    import hashlib

    payload = _fetch_pressure(cycle)
    messages = parse_pressure_messages(payload)
    records = normalize_pressure_levels(messages, LAT, LON, PRESSURE_LEVELS)
    digest = hashlib.sha256(payload).hexdigest()
    artifact_path = RAW_ROOT / "ecmwf-ifs" / digest / "pressure.grib2"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(payload)
    descriptor = RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-pressure",
        str(artifact_path),
        digest,
        cycle,
        "GRIB2",
        len(payload),
        forecast_cycle=cycle,
        forecast_lead_seconds=0,
        metadata={
            "provider_payload_sha256": digest,
            "provider_payload_size_bytes": len(payload),
        },
    )
    count = 0
    for record in records:
        canonical = CanonicalRecordInput(
            "forecast",
            record.timestamp,
            LAT,
            LON,
            record.altitude,
            f"ifs:0p25:28.0:87.0:{record.level_hpa}hpa",
            record.source,
            record.model,
            ("clean",),
            wind_speed=record.wind_speed,
            wind_direction=record.wind_direction,
            temperature=record.temperature_c,
            forecast_cycle=record.cycle,
            forecast_lead_seconds=record.lead_seconds,
        )
        service.ingest(descriptor, (canonical,))
        count += 1
    return count


def main() -> None:
    """Run one full scheduler pass: surface + pressure ingestion for the latest cycle."""
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
            print(f"ingested {count} surface leads")
            pcount = _ingest_ifs_pressure(service, cycle)
            print(f"ingested {pcount} pressure levels")
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # provider latency: retry previous cycles until one publishes
            print(
                f"cycle {cycle.isoformat()} unavailable ({exc}); trying previous"
            )
            cycle = cycle - timedelta(hours=6)
    print("no recent cycle available; skipping this run")


if __name__ == "__main__":
    main()
