"""Fetch latest IFS/GFS GRIB bytes and ingest with current QC.

Reads provider files over HTTP byte ranges (same official endpoints as the
connectors), parses with ecCodes, normalizes, and persists raw + canonical
records. Unlike the connectors this does not reuse a metadata sidecar cache,
so a refresh pass never trips a "checksum sidecar is inconsistent" error from
an earlier run's embedded retrieved_at timestamp.

Run inside WSL:
  /tmp/everest-venv/bin/python apps/api/ingest_refresh.py          # both
  /tmp/everest-venv/bin/python apps/api/ingest_refresh.py gfs      # one
"""

# pylint: disable=wrong-import-position,wrong-import-order,import-outside-toplevel
# sys.path insertion before local imports is required for this standalone
# script; lazy imports keep the hot path light.

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
import hashlib
import json
import sys
import urllib.request
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
from services.weather.ecmwf.normalizer import normalize_messages as normalize_ifs  # noqa: E402
from services.weather.ecmwf.parser import parse_grib_bytes as parse_ifs  # noqa: E402
from services.weather.gfs.normalizer import normalize_messages as normalize_gfs  # noqa: E402
from services.weather.gfs.parser import parse_grib_bytes as parse_gfs  # noqa: E402
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

LAT = 27.98806
LON = 86.92528
IFS_LEADS = (0, 3, 6, 12, 24, 48, 72)
GFS_LEADS = (3, 6, 24)
# How far back to walk looking for a published cycle. Providers post a cycle a
# few hours after its nominal time, so "now" is normally not yet available.
CYCLE_SEARCH_STEPS = 8
DB_URL = resolve_database_url()
RAW_ROOT = Path("/mnt/d/Everest-data/raw")


def _get(url: str, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def _range(url: str, start: int, length: int) -> bytes:
    end = start + length - 1
    body = _get(
        url,
        {"Range": f"bytes={start}-{end}", "User-Agent": "everest-refresh/1.0"},
    )
    if len(body) != length:
        raise ValueError(f"range length mismatch at {start}")
    return body


def _available(url: str) -> bool:
    """Report whether a provider index exists, without downloading the field."""
    try:
        _get(url, {"Range": "bytes=0-0", "User-Agent": "everest-refresh/1.0"})
    except OSError:
        return False
    return True


def _six_hourly_cycles() -> list[datetime]:
    """Candidate cycles, newest first, from the last two days."""
    now = datetime.now(timezone.utc)
    latest = now.replace(
        hour=now.hour - now.hour % 6, minute=0, second=0, microsecond=0
    )
    return [latest - timedelta(hours=6 * step) for step in range(CYCLE_SEARCH_STEPS)]


def _ifs_base(cycle: datetime, lead: int) -> str:
    """Provider path for one IFS 0.25 degree operational forecast field set."""
    return (
        f"https://data.ecmwf.int/forecasts/{cycle:%Y%m%d}/{cycle:%H}z/ifs/"
        f"0p25/oper/{cycle:%Y%m%d%H%M%S}-{lead}h-oper-fc"
    )


def _gfs_base(cycle: datetime, lead: int) -> str:
    """Provider path for one GFS 0.25 degree pgrb2 forecast file."""
    return (
        f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
        f"gfs.{cycle:%Y%m%d}/{cycle:%H}/atmos/gfs.t{cycle:%H}z.pgrb2.0p25."
        f"f{lead:03d}"
    )


def _latest_cycle(base: Callable[[datetime, int], str], suffix: str) -> datetime:
    """Newest published cycle for a provider.

    The cycles used to be frozen module constants, which meant the script
    stopped working as soon as the provider expired that day's run rather than
    fetching what is actually current.
    """
    for cycle in _six_hourly_cycles():
        if _available(base(cycle, 0) + suffix):
            return cycle
    raise ValueError("no published cycle found in the last two days")


def _fetch_ifs(cycle: datetime, lead: int) -> tuple[bytes, str, int]:
    base = _ifs_base(cycle, lead)
    rows = [
        json.loads(line)
        for line in _get(
            base + ".index", {"User-Agent": "everest-refresh/1.0"}
        )
        .decode()
        .splitlines()
        if line
    ]
    wanted = {"z", "10u", "10v", "2t", "tp"}
    sel = [
        r
        for r in rows
        if r.get("levtype") == "sfc"
        and r.get("param") in wanted
        and r.get("_length", 0) > 224
    ]
    if not sel:
        raise ValueError(f"IFS lead {lead}: no surface messages")
    buf = bytearray()
    for r in sel:
        buf.extend(_range(base + ".grib2", r["_offset"], r["_length"]))
    digest = hashlib.sha256(bytes(buf)).hexdigest()
    return bytes(buf), digest, len(buf)


def _fetch_gfs(cycle: datetime, lead: int) -> tuple[bytes, str, int]:
    base = _gfs_base(cycle, lead)
    idx = _get(base + ".idx", {"User-Agent": "everest-refresh/1.0"}).decode()
    idx_lines = idx.splitlines()
    parsed_idx = []
    for line in idx_lines:
        parts = line.split(":")
        if len(parts) >= 5:
            parsed_idx.append((int(parts[1]), parts[3], parts[4]))
    wanted = {
        "TMP": "2 m above ground",
        "UGRD": "10 m above ground",
        "VGRD": "10 m above ground",
        "VIS": "surface",
        "APCP": "surface",
        "HGT": "surface",
    }
    # Keep the LAST occurrence of each (param, level); every message's end
    # offset is the next raw idx row, so APCP surface (followed by ACPCP,
    # a different code) still resolves.
    matches = [
        (start, param, level)
        for start, param, level in parsed_idx
        if param in wanted and level == wanted[param]
    ]
    matches.reverse()
    seen = set()
    unique = []
    for start, param, level in matches:
        key = (param, level)
        if key in seen:
            continue
        seen.add(key)
        unique.append((start, param, level))
    unique.reverse()
    selected = []
    for start, param, level in unique:
        end = None
        for nxt_start, _, _ in parsed_idx:
            if nxt_start > start:
                end = nxt_start - 1
                break
        if end is None:
            raise ValueError(f"GFS {param}/{level} has no terminal offset")
        selected.append((start, end))
    if not selected:
        raise ValueError(f"GFS lead {lead}: no wanted messages")
    buf = bytearray()
    for start, end in selected:
        buf.extend(_range(base, start, end - start + 1))
    digest = hashlib.sha256(bytes(buf)).hexdigest()
    return bytes(buf), digest, len(buf)


def _persist(service, source_id, dataset, cycle, lead, payload, digest):
    """Store raw bytes and one canonical record through the ingestion service."""
    artifact_dir = RAW_ROOT / source_id / digest
    artifact_dir.mkdir(parents=True, exist_ok=True)
    object_reference = artifact_dir / f"{cycle:%Y%m%d%H%M%S}-{lead}h.grib2"
    if not object_reference.exists():
        object_reference.write_bytes(payload)
    descriptor = RawArtifactDescriptor(
        source_id,
        dataset,
        str(object_reference),
        digest,
        cycle,
        "GRIB2",
        len(payload),
        forecast_cycle=cycle,
        forecast_lead_seconds=lead * 3600,
        valid_time=cycle + timedelta(hours=lead),
        metadata={
            "provider_payload_sha256": digest,
            "provider_payload_size_bytes": len(payload),
            "provider_lead_seconds": lead * 3600,
        },
    )
    return descriptor


def _canonical(source_id, record, lead, cycle):
    """Build the canonical record input from the normalized record."""
    return CanonicalRecordInput(
        record.record_type.value,
        record.timestamp,
        record.latitude,
        record.longitude,
        record.altitude,
        f"{source_id}:0p25:{record.latitude:.1f}:{record.longitude:.1f}",
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


def _seed(session) -> None:
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


def _ingest_ifs(service) -> None:
    """Ingest the newest published IFS surface leads."""
    cycle = _latest_cycle(_ifs_base, ".index")
    print(f"IFS cycle {cycle:%Y-%m-%dT%H:%M}Z")
    zero_altitude = None
    for lead in IFS_LEADS:
        payload, digest, _size = _fetch_ifs(cycle, lead)
        messages = parse_ifs(payload)
        record = normalize_ifs(messages, LAT, LON)
        altitude = record.altitude
        if altitude != altitude:  # NaN
            if zero_altitude is None:
                continue
            altitude = zero_altitude
        else:
            zero_altitude = altitude
        record = replace(record, altitude=altitude)
        descriptor = _persist(
            service, "ecmwf-ifs", "ifs-oper", cycle, lead, payload, digest
        )
        canonical = _canonical("ecmwf-ifs", record, lead, cycle)
        service.ingest(descriptor, (canonical,))
        print(
            f"  IFS lead {lead:3d}h: t={record.temperature:.1f} C "
            f"precip={record.precipitation} vis={record.visibility} "
            f"flags={sorted(record.quality_flags)}"
        )


def _ingest_gfs(service) -> None:
    """Ingest the newest published GFS leads.

    GFS is the only configured provider that publishes surface visibility: IFS
    open data has no visibility parameter at all, so without this pass the
    canonical ``visibility`` column stays empty for every record.
    """
    cycle = _latest_cycle(_gfs_base, ".idx")
    print(f"GFS cycle {cycle:%Y-%m-%dT%H:%M}Z")
    for lead in GFS_LEADS:
        payload, digest, _size = _fetch_gfs(cycle, lead)
        messages = parse_gfs(payload)
        record = normalize_gfs(messages, LAT, LON)
        descriptor = _persist(
            service, "noaa-gfs", "gfs-oper", cycle, lead, payload, digest
        )
        canonical = _canonical("noaa-gfs", record, lead, cycle)
        service.ingest(descriptor, (canonical,))
        print(
            f"  GFS lead {lead:3d}h: t={record.temperature:.1f} C "
            f"precip={record.precipitation} vis={record.visibility} "
            f"flags={sorted(record.quality_flags)}"
        )


def main(providers: Sequence[str] = ("ifs", "gfs")) -> None:
    """Fetch and ingest the newest published forecasts with current QC."""
    policy = RawStoragePolicy(RAW_ROOT, Path("/mnt/d/Everest"))
    engine = create_engine(DB_URL)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = WeatherIngestionService(factory, policy)
    with factory() as session:
        _seed(session)

    for provider, ingest in (("ifs", _ingest_ifs), ("gfs", _ingest_gfs)):
        if provider not in providers:
            continue
        try:
            ingest(service)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # One provider being unpublished or unreachable must not discard the
            # other's records, which is why each pass is isolated.
            print(f"{provider.upper()} refresh failed: {exc}")
    print("refresh done")


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("ifs", "gfs"))
