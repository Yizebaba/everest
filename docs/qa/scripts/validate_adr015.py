"""ADR-015 endpoint evidence validation harness (disposable, retained data).

QA tool that proves the five ADR-015 routes return real canonical
PostgreSQL/provider data over HTTP using only retained raw payloads; no
external provider is contacted and no raw payload is mutated. It reuses the
production ingestion service, the pressure-level normalizer, the route-profile
interpolation, and the scheduler's profile helpers; it contains no business
logic of its own.

Evidence records: `docs/management/decisions.md` ADR-021,
`docs/qa/adr015-disposable-evidence-2026-08-28.json`, and the QA record
`EV-DATA-001-ADR015-VALIDATE-2026-08-28` in `docs/qa/test-plan.md`.

Execution (inside WSL with the project venv, ecCodes, and a disposable,
already-migrated PostgreSQL)::

    export EVEREST_DATABASE_URL="postgresql+psycopg://user:pass@\
        127.0.0.1:PORT/db"
    export EVEREST_RAW_ROOT=/mnt/d/Everest-data/raw
    /tmp/everest-venv/bin/python docs/qa/scripts/validate_adr015.py
"""

# pylint: disable=wrong-import-position,wrong-import-order,import-outside-toplevel,protected-access
# sys.path insertion before local imports is required for this standalone QA
# script. Protected access intentionally reuses the production scheduler's
# pressure/profile helpers so the evidence path matches production exactly.

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")
sys.path.insert(0, "/mnt/d/Everest/packages/weather_ingestion_contract")

from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import schedule_forecast  # noqa: E402

from everest_api.app import create_app  # noqa: E402
from everest_api.persistence.database import (
    create_session_factory,
)  # noqa: E402
from everest_api.raw_storage import RawStoragePolicy  # noqa: E402
from everest_api.registry.models import DataSourceRegistryModel  # noqa: E402
from everest_api.weather.models import WeatherRecordModel  # noqa: E402
from everest_api.weather.service import WeatherIngestionService  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from services.weather.ecmwf import (
    normalize_messages,
    parse_grib_bytes,
)  # noqa: E402
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
RAW_ROOT = Path(os.environ.get("EVEREST_RAW_ROOT", "/mnt/d/Everest-data/raw"))
REPO_ROOT = Path("/mnt/d/Everest")

IFS_SURFACE_PAYLOAD = (
    RAW_ROOT
    / "ecmwf-ifs"
    / "638a075b6ba11c52131c6bc4ad05e49b2c8932d7026c99c3be6658d5315e1650"
    / "20260824000000-0h-oper-fc.grib2"
)
IFS_PRESSURE_PAYLOAD = (
    RAW_ROOT
    / "ecmwf-ifs"
    / "00741f3867fc303f676830ec4a6fb755aaf2bf313c54688f7e6dff326b9843ff"
    / "pressure.grib2"
)


def _seed_registry(session) -> None:
    """Seed the four approved forecast sources with their documented facts."""
    sources = {
        "ecmwf-ifs": ("ECMWF IFS", "ECMWF", "configured", "unknown"),
        "noaa-gfs": ("NOAA GFS", "NOAA", "configured", "unknown"),
        "dwd-icon": ("DWD ICON", "DWD", "configured", "unknown"),
        "ecmwf-aifs": ("ECMWF AIFS", "ECMWF", "connected", "unknown"),
    }
    for source_id, (name, provider, status, health) in sources.items():
        if session.get(DataSourceRegistryModel, source_id) is None:
            session.add(
                DataSourceRegistryModel(
                    source_id=source_id,
                    name=name,
                    provider=provider,
                    category="forecast",
                    status=status,
                    access_method="connector",
                    commercial_allowed=False,
                    credentials_required=False,
                    health_status=health,
                    metadata_version=1,
                )
            )
    session.commit()


def _ingest_surface(service) -> dict[str, object]:
    """Persist the retained IFS surface record (current + forecast evidence)."""
    if not IFS_SURFACE_PAYLOAD.exists():
        raise SystemExit(
            f"retained IFS surface payload missing: {IFS_SURFACE_PAYLOAD}"
        )
    payload = IFS_SURFACE_PAYLOAD.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    messages = parse_grib_bytes(payload)
    record = normalize_messages(messages, LAT, LON)
    descriptor = RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-oper",
        str(IFS_SURFACE_PAYLOAD),
        digest,
        record.timestamp,
        "GRIB2",
        len(payload),
        forecast_cycle=record.forecast.cycle,
        forecast_lead_seconds=0,
        valid_time=record.timestamp,
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
    return {
        "payload": str(IFS_SURFACE_PAYLOAD),
        "sha256": digest,
        "size_bytes": len(payload),
        "valid_time": record.timestamp.isoformat(),
        "altitude_m": record.altitude,
        "wind_speed": record.wind_speed,
        "temperature_c": record.temperature,
    }


def _ingest_pressure_and_profiles(service) -> dict[str, object]:
    """Persist retained IFS pressure levels and interpolated route profiles."""
    if not IFS_PRESSURE_PAYLOAD.exists():
        raise SystemExit(
            f"retained IFS pressure payload missing: {IFS_PRESSURE_PAYLOAD}"
        )
    payload = IFS_PRESSURE_PAYLOAD.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    messages = parse_pressure_messages(payload)
    records = normalize_pressure_levels(messages, LAT, LON)
    if not records:
        raise SystemExit("no pressure levels normalized from retained payload")
    cycle = records[0].cycle
    descriptor = RawArtifactDescriptor(
        "ecmwf-ifs",
        "ifs-pressure",
        str(IFS_PRESSURE_PAYLOAD),
        digest,
        cycle,
        "GRIB2",
        len(payload),
        forecast_cycle=cycle,
        forecast_lead_seconds=records[0].lead_seconds,
        valid_time=records[0].timestamp,
        metadata={
            "provider_payload_sha256": digest,
            "provider_payload_size_bytes": len(payload),
            "provider_lead_seconds": records[0].lead_seconds,
        },
    )
    level_count = 0
    for record in records:
        canonical = CanonicalRecordInput(
            "forecast",
            record.timestamp,
            record.latitude,
            record.longitude,
            record.altitude,
            f"ifs:0p25:{record.latitude:.1f}:{record.longitude:.1f}"
            f":{record.level_hpa}hpa",
            record.source,
            record.model,
            schedule_forecast._pressure_quality_flags(record),
            wind_speed=record.wind_speed,
            wind_direction=record.wind_direction,
            temperature=record.temperature_c,
            forecast_cycle=record.cycle,
            forecast_lead_seconds=record.lead_seconds,
        )
        service.ingest(descriptor, (canonical,))
        level_count += 1
    profile_count = schedule_forecast._ingest_route_profiles(
        service, descriptor, records
    )
    return {
        "payload": str(IFS_PRESSURE_PAYLOAD),
        "sha256": digest,
        "size_bytes": len(payload),
        "cycle": cycle.isoformat(),
        "lead_seconds": records[0].lead_seconds,
        "valid_time": records[0].timestamp.isoformat(),
        "levels_ingested": level_count,
        "profiles_ingested": profile_count,
    }


def _bounded_sample(body: dict[str, object]) -> dict[str, object] | None:
    """Return the first record's bounded public fields, or the body shape."""
    records = body.get("records")
    if isinstance(records, list) and records:
        first = records[0]
        if isinstance(first, dict):
            return {
                "record_type": first.get("record_type"),
                "timestamp": first.get("timestamp"),
                "altitude": first.get("altitude"),
                "wind_speed": first.get("wind_speed"),
                "temperature": first.get("temperature"),
                "source": first.get("source"),
                "model": first.get("model"),
                "route_profile": first.get("route_profile"),
                "spatial_key": first.get("spatial_key"),
            }
    return {"keys": sorted(body.keys())}


def _evidence(client: TestClient) -> list[dict[str, object]]:
    """Call the five ADR-015 routes and capture bounded HTTP evidence."""
    calls = [
        ("/api/weather/forecast", None),
        ("/api/weather/current", None),
        ("/api/weather/profile", {"profile": "SUMMIT"}),
        ("/api/weather/sources", None),
        ("/api/data-health", None),
    ]
    rows: list[dict[str, object]] = []
    for path, params in calls:
        response = client.get(path, params=params or {})
        body = response.json()
        rows.append(
            {
                "route": path,
                "params": params or {},
                "status_code": response.status_code,
                "correlation_id": response.headers.get("X-Correlation-ID"),
                "record_count": len(body.get("records", [])),
                "source_count": len(body.get("sources", [])),
                "profile": body.get("profile"),
                "sample": _bounded_sample(body),
            }
        )
    return rows


def main() -> None:
    """Run the disposable retained-data validation and print evidence JSON."""
    db_url = os.environ.get("EVEREST_DATABASE_URL")
    if not db_url:
        raise SystemExit("EVEREST_DATABASE_URL is required")
    run_started_at = datetime.now(UTC).isoformat()

    policy = RawStoragePolicy(RAW_ROOT, REPO_ROOT)
    engine = create_engine(db_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = WeatherIngestionService(factory, policy)

    with factory() as session:
        _seed_registry(session)

    surface = _ingest_surface(service)
    print("surface:", json.dumps(surface))
    pressure = _ingest_pressure_and_profiles(service)
    print("pressure:", json.dumps(pressure))

    app = create_app(create_session_factory(db_url))
    with TestClient(app) as client:
        evidence = _evidence(client)

    with factory() as session:
        total = session.scalar(
            select(func.count()).select_from(  # pylint: disable=not-callable
                WeatherRecordModel
            )
        )
        registry_statuses = {
            row.source_id: {"status": row.status, "health": row.health_status}
            for row in session.scalars(select(DataSourceRegistryModel)).all()
        }

    result = {
        "run_started_at": run_started_at,
        "run_finished_at": datetime.now(UTC).isoformat(),
        "database_url": db_url.replace("everest:everest@", "everest:***@"),
        "source": "retained-only (no external retrieval)",
        "surface": surface,
        "pressure": pressure,
        "total_weather_records": total,
        "registry_statuses": registry_statuses,
        "routes": evidence,
    }
    print("EVIDENCE_JSON_BEGIN")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("EVIDENCE_JSON_END")


if __name__ == "__main__":
    main()
