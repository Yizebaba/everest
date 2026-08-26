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
from services.weather.contract import (  # noqa: E402
    ForecastIdentity,
    RecordType,
    WeatherRecord,
    validate_record,
)
from services.weather.ecmwf import (  # noqa: E402
    EcmwfOpenDataConnector,
    normalize_messages as normalize_ifs,
    parse_grib_bytes,
)
from services.weather.ecmwf.pressure import (  # noqa: E402
    normalize_pressure_levels,
    parse_pressure_messages,
)
from services.weather.route_profile import (  # noqa: E402
    ROUTE_PROFILE_ELEVATIONS,
    interpolate_route_profiles,
)
from weather_ingestion_contract import (  # noqa: E402
    CanonicalRecordInput,
    RawArtifactDescriptor,
)

LAT = 27.98806
LON = 86.92528
RAW_ROOT = Path("/tmp/everest-schedule-raw")
LEADS_IFS = list(range(0, 73, 3))  # 3h steps
# 400 hPa (~7600 m) and 300 hPa (~9800 m) bracket the 8848 m summit, so the
# summit level can be interpolated instead of guessed; 850-500 cover the route
# from the valley up through Camp 3.
PRESSURE_LEVELS = ("850", "700", "600", "500", "400", "300")
# Pressure levels are fetched at 6h steps rather than every surface lead: one
# lead costs ~15 MB of byte-range downloads, and a 6h vertical cadence is enough
# to resolve a summit window.
PRESSURE_LEADS = tuple(range(0, 73, 6))


def _env_db_url() -> str:
    """Resolve the same database URL the API reads, from one shared resolver."""
    from everest_api.persistence.database import resolve_database_url

    return resolve_database_url()


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
    """Ingest the near-surface IFS fields for every published lead of a cycle.

    These are 10 m winds, 2 m temperature and surface precipitation over the
    model's smoothed 0.25 deg orography (~6008 m at this grid point). They
    describe conditions just above that ground, not free-air conditions at
    6008 m, and never summit conditions - hence the ``:sfc`` key suffix. Summit
    and camp-height values come from the pressure-level path.
    """
    connector = EcmwfOpenDataConnector(RAW_ROOT)
    orography = None  # model orography is time-invariant within a cycle
    count = 0
    for lead in LEADS_IFS:
        try:
            retrieval = connector.retrieve(cycle, lead_hours=lead)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            if lead == 0:
                raise  # no lead 0 means the cycle itself is not published
            # A later lead the provider has not published yet must not discard
            # the leads already ingested for this cycle.
            print(f"  surface +{lead}h unavailable ({exc}); skipping lead")
            continue
        payload = retrieval.payload_path.read_bytes()
        messages = parse_grib_bytes(payload)
        record = normalize_ifs(messages, LAT, LON)
        if math.isnan(record.altitude):
            if orography is None:
                print(f"  surface +{lead}h has no orography yet; skipping lead")
                continue
            # Reuse the orography decoded at lead 0: the model's surface height
            # does not change across leads of one cycle, so this is the same
            # measured value rather than a substituted one.
            from dataclasses import replace

            record = replace(record, altitude=orography)
        else:
            orography = record.altitude
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
            f"ifs:0p25:{record.latitude:.1f}:{record.longitude:.1f}:sfc",
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


def _fetch_pressure(cycle: datetime, lead_hours: int = 0) -> bytes:
    """Download the IFS pressure-level GRIB messages for one cycle and lead."""
    import json
    import urllib.request

    stamp = cycle.strftime("%Y%m%d")
    base = (
        f"https://data.ecmwf.int/forecasts/{stamp}/{cycle:%H}z/ifs/0p25/oper/"
        f"{stamp}{cycle:%H}0000-{lead_hours}h-oper-fc"
    )
    with urllib.request.urlopen(base + ".index", timeout=60) as resp:
        rows = [json.loads(l) for l in resp.read().decode().splitlines() if l]
    sel = [
        r
        for r in rows
        if r.get("levtype") == "pl"
        and r.get("param") in ("u", "v", "t", "gh")
        and r.get("levelist") in PRESSURE_LEVELS
    ]
    if not sel:
        raise RuntimeError(
            f"pressure index for {cycle:%Y%m%d%H}z +{lead_hours}h has no "
            "requested levels"
        )
    sel.sort(key=lambda r: r["_offset"])
    buf = bytearray()
    for r in sel:
        end = r["_offset"] + r["_length"] - 1
        req = urllib.request.Request(
            base + ".grib2", headers={"Range": f"bytes={r['_offset']}-{end}"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
            if len(body) != r["_length"]:
                raise RuntimeError("pressure range length mismatch")
            buf.extend(body)
    return bytes(buf)


def _pressure_quality_flags(record) -> tuple[str, ...]:
    """Run the real contract validator over one pressure-level record.

    The pressure path used to hard-code ``("clean",)``, which stamped every
    record as validated without ever running QC. Pressure levels carry no
    precipitation or visibility, so the honest outcome is ``missing_value``.
    """
    probe = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=record.timestamp,
        latitude=record.latitude,
        longitude=record.longitude,
        altitude=record.altitude,
        wind_speed=record.wind_speed,
        wind_direction=record.wind_direction,
        temperature=record.temperature_c,
        precipitation=None,
        visibility=None,
        source=record.source,
        model=record.model,
        forecast=ForecastIdentity(
            record.cycle, timedelta(seconds=record.lead_seconds)
        ),
    )
    return tuple(sorted(validate_record(probe)))


def _profile_quality_flags(
    sample, cycle: datetime, lead_seconds: int, latitude: float, longitude: float
) -> tuple[str, ...]:
    """Run the contract validator over one interpolated camp-height sample."""
    probe = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=cycle + timedelta(seconds=lead_seconds),
        latitude=latitude,
        longitude=longitude,
        altitude=sample.elevation,
        wind_speed=sample.wind_speed,
        wind_direction=sample.wind_direction,
        temperature=sample.temperature_c,
        precipitation=None,
        visibility=None,
        source="ecmwf-ifs",
        model="IFS",
        pressure=sample.pressure_hpa,
        forecast=ForecastIdentity(cycle, timedelta(seconds=lead_seconds)),
    )
    return tuple(sorted(validate_record(probe)))


def _ingest_route_profiles(service, descriptor, records) -> int:
    """Ingest one record per named camp, interpolated to its true elevation.

    Without this, ``route_profile`` was NULL on every row, so
    ``/api/weather/profile?profile=SUMMIT`` returned an empty list and the
    vertical dimension existed in the database but not in the product. Tagging a
    raw pressure level with a camp name instead would have misstated its height
    by hundreds of metres, so each camp is interpolated between the two levels
    that bracket it and the source levels are recorded in ``spatial_key``.
    """
    count = 0
    by_time: dict[datetime, list] = {}
    for record in records:
        by_time.setdefault(record.timestamp, []).append(record)
    for timestamp, column in sorted(by_time.items()):
        anchor = column[0]
        for sample in interpolate_route_profiles(
            column, ROUTE_PROFILE_ELEVATIONS
        ):
            canonical = CanonicalRecordInput(
                "forecast",
                timestamp,
                anchor.latitude,
                anchor.longitude,
                # The camp's surveyed elevation, which is what the values were
                # interpolated to - not the height of either source level.
                sample.elevation,
                f"ifs:0p25:{anchor.latitude:.1f}:{anchor.longitude:.1f}"
                f":{sample.profile}@{sample.elevation:.0f}m"
                f":interp{sample.lower_level_hpa}-{sample.upper_level_hpa}hpa",
                anchor.source,
                anchor.model,
                _profile_quality_flags(
                    sample,
                    anchor.cycle,
                    anchor.lead_seconds,
                    anchor.latitude,
                    anchor.longitude,
                ),
                wind_speed=sample.wind_speed,
                wind_direction=sample.wind_direction,
                temperature=sample.temperature_c,
                pressure=sample.pressure_hpa,
                forecast_cycle=anchor.cycle,
                forecast_lead_seconds=anchor.lead_seconds,
                route_profile=sample.profile,
            )
            service.ingest(descriptor, (canonical,))
            count += 1
    return count


def _ingest_ifs_pressure(service, cycle: datetime, leads=PRESSURE_LEADS) -> int:
    """Ingest the vertical profile at every requested lead, not just lead 0.

    Fetching only lead 0 gave a vertical snapshot at cycle time and no vertical
    forecast at all, so nothing above the model surface could be shown for any
    future hour.
    """
    import hashlib

    count = 0
    for lead in leads:
        try:
            payload = _fetch_pressure(cycle, lead)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # A lead that the provider has not published yet must not discard
            # the leads that are already available.
            print(f"  pressure +{lead}h unavailable ({exc}); skipping lead")
            continue
        messages = parse_pressure_messages(payload)
        records = normalize_pressure_levels(
            messages, LAT, LON, PRESSURE_LEVELS
        )
        digest = hashlib.sha256(payload).hexdigest()
        artifact_path = RAW_ROOT / "ecmwf-ifs" / digest / "pressure.grib2"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        if not artifact_path.exists():
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
            forecast_lead_seconds=lead * 3600,
            valid_time=cycle + timedelta(hours=lead),
            metadata={
                "provider_payload_sha256": digest,
                "provider_payload_size_bytes": len(payload),
                "provider_lead_seconds": lead * 3600,
                # Joined rather than a list: the contract boundary accepts only
                # JSON scalars, and passing a list raised a TypeError that the
                # cycle loop then reported as "cycle unavailable", so no
                # pressure record was ever ingested.
                "provider_levels_hpa": ",".join(PRESSURE_LEVELS),
            },
        )
        for record in records:
            canonical = CanonicalRecordInput(
                "forecast",
                record.timestamp,
                # The grid point actually sampled, not the summit coordinates:
                # storing LAT/LON here claimed a value had been produced for a
                # location the model never evaluated.
                record.latitude,
                record.longitude,
                record.altitude,
                f"ifs:0p25:{record.latitude:.1f}:{record.longitude:.1f}"
                f":{record.level_hpa}hpa",
                record.source,
                record.model,
                _pressure_quality_flags(record),
                wind_speed=record.wind_speed,
                wind_direction=record.wind_direction,
                temperature=record.temperature_c,
                forecast_cycle=record.cycle,
                forecast_lead_seconds=record.lead_seconds,
            )
            service.ingest(descriptor, (canonical,))
            count += 1
        profiles = _ingest_route_profiles(service, descriptor, records)
        count += profiles
        print(f"  pressure +{lead}h: {len(records)} levels, {profiles} camps")
    return count


def main() -> int:
    """Run one scheduler pass: surface + pressure ingestion for the latest cycle.

    Returns a process exit status. Every failure path used to return 0, so
    systemd recorded ``Result=success`` even when nothing was ingested and
    ``Restart=on-failure`` could never fire.
    """
    # RAW_ROOT is not wiped here: weather_raw_artifact.object_reference rows
    # point into it, and deleting the tree on every run left the database
    # referencing files that no longer existed.
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
    # ECMWF publishes a cycle roughly 6-8 h after its nominal time, so the two
    # most recent cycles are normally still absent. Walking back finds the
    # newest published one; the timer is phased so that is usually cycle-8h.
    for _ in range(8):
        try:
            print(f"ingesting IFS cycle {cycle.isoformat()}")
            count = _ingest_ifs(service, cycle)
            print(f"ingested {count} surface leads")
            pcount = _ingest_ifs_pressure(service, cycle)
            print(f"ingested {pcount} pressure records")
            if count == 0 and pcount == 0:
                print(f"cycle {cycle.isoformat()} yielded no records")
                return 1
            return 0
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # provider latency: retry previous cycles until one publishes
            print(
                f"cycle {cycle.isoformat()} unavailable ({exc}); trying previous"
            )
            cycle = cycle - timedelta(hours=6)
    print("no recent cycle available in the last 48 h; this run ingested nothing")
    return 1


if __name__ == "__main__":
    sys.exit(main())
