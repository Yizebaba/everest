"""Everest RUNTIME-006 configuration-driven one-pass forecast scheduler.

Runs inside WSL where ecCodes, PostgreSQL, and project code are available.
IFS is enabled by default and retains its latest-cycle fallback. GFS, AIFS, and
ICON have concrete lazy jobs but remain disabled unless explicitly enabled.
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
from everest_api.scheduler import (  # noqa: E402
    FailedLead,
    ProviderJob,
    ProviderRunResult,
    RunStatus,
    SchedulerConfig,
    run_once,
)
from everest_api.scheduler.recording import DataSourceRunRecorder  # noqa: E402
from everest_api.weather.service import WeatherIngestionService  # noqa: E402
from services.weather.contract import (  # noqa: E402
    ForecastIdentity,
    RecordType,
    WeatherRecord,
    validate_record,
)
from services.weather.aoi import AreaOfInterest, subset_dataset  # noqa: E402
from services.weather.ecmwf import (  # noqa: E402
    EcmwfOpenDataConnector,
    normalize_messages as normalize_ifs,
    parse_grib_bytes,
)
from services.weather.ecmwf.pressure import (  # noqa: E402
    normalize_pressure_levels,
    parse_pressure_messages,
)
from services.weather.retrieval import open_grib_dataset  # noqa: E402
from services.weather.route_profile import (  # noqa: E402
    ROUTE_PROFILE_ELEVATIONS,
    interpolate_route_profiles,
)
from services.weather.wind_field import (  # noqa: E402
    build_wind_field_frame,
    materialize_wind_field_frame,
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
# WGS84 envelope of the approved 100 km geodesic AOI around the project
# center. These are the west/south/east/north extrema at cardinal bearings;
# the source grid is clipped to this envelope without interpolation.
WIND_FIELD_AOI = AreaOfInterest(
    south=27.085630960770477,
    north=28.890370597450392,
    west=85.90876137741341,
    east=87.94179862258659,
)
WIND_FIELD_LEVEL_HPA = 400.0


def _env_db_url() -> str:
    """Resolve the same database URL the API reads, from one shared resolver."""
    from everest_api.persistence.database import resolve_database_url

    return resolve_database_url()


def _seed(session) -> None:
    known_sources = (
        ("ecmwf-ifs", "ECMWF IFS", "ECMWF"),
        ("noaa-gfs", "NOAA GFS", "NOAA"),
        ("ecmwf-aifs", "ECMWF AIFS", "ECMWF"),
        ("dwd-icon", "DWD ICON", "DWD"),
    )
    for source_id, name, provider in known_sources:
        if session.get(DataSourceRegistryModel, source_id) is None:
            session.add(
                DataSourceRegistryModel(
                    source_id=source_id,
                    name=name,
                    provider=provider,
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


def _ingest_ifs(service, cycle: datetime) -> int | ProviderRunResult:
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
    failed_leads: list[FailedLead] = []
    for lead in LEADS_IFS:
        try:
            retrieval = connector.retrieve(cycle, lead_hours=lead)
        except Exception as error:  # pylint: disable=broad-exception-caught
            if lead == 0:
                raise  # no lead 0 means the cycle itself is not published
            # A later lead the provider has not published yet must not discard
            # the leads already ingested for this cycle.
            print(f"  surface +{lead}h unavailable; skipping lead")
            failed_leads.append(_failed_lead(lead, error))
            continue
        payload = retrieval.payload_path.read_bytes()
        messages = parse_grib_bytes(payload)
        record = normalize_ifs(messages, LAT, LON)
        if math.isnan(record.altitude):
            if orography is None:
                print(f"  surface +{lead}h has no orography yet; skipping lead")
                failed_leads.append(
                    FailedLead(
                        lead, "MissingOrography", "orography unavailable"
                    )
                )
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
    return _provider_result(count, failed_leads)


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
    sample,
    cycle: datetime,
    lead_seconds: int,
    latitude: float,
    longitude: float,
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


def _materialize_ifs_wind_field(
    artifact_path: Path,
    cycle: datetime,
    lead_hours: int,
    *,
    derived_root: str | Path | None = None,
    opener=None,
):
    """Publish one native-grid 400 hPa U/V frame from retained GRIB.

    This path is optional and never invents a field from point records. The
    retained pressure artifact is decoded with cfgrib, clipped to the approved
    AOI envelope, loaded before the source Dataset closes, and materialized to
    external derived storage. No provider call occurs here.
    """
    # The explicit locals preserve the data-contract fields at this trust
    # boundary; collapsing them would obscure source versus derived metadata.
    # pylint: disable=too-many-locals
    import os

    root = derived_root or os.environ.get("EVEREST_WIND_FIELD_DERIVED_ROOT")
    if not root:
        return None
    with open_grib_dataset(
        artifact_path,
        filter_by_keys={
            "typeOfLevel": "isobaricInhPa",
            "level": int(WIND_FIELD_LEVEL_HPA),
        },
        opener=opener,
    ) as dataset:
        subset = subset_dataset(
            dataset,
            WIND_FIELD_AOI,
            variables=("u", "v"),
        ).load()
        frame = build_wind_field_frame(
            subset,
            source="ecmwf-ifs",
            model="IFS",
            cycle=cycle,
            valid_time=cycle + timedelta(hours=lead_hours),
            lead=timedelta(hours=lead_hours),
            level=WIND_FIELD_LEVEL_HPA,
            level_units="hPa",
            bounds=(
                WIND_FIELD_AOI.west,
                WIND_FIELD_AOI.south,
                WIND_FIELD_AOI.east,
                WIND_FIELD_AOI.north,
            ),
        )
    target_root = root if lead_hours == 0 else Path(root) / "forecast-leads"
    return materialize_wind_field_frame(
        frame, target_root, excluded_roots=(RAW_ROOT,)
    )


def _ingest_ifs_pressure(  # pylint: disable=too-many-locals
    service, cycle: datetime, leads=PRESSURE_LEADS
) -> int | ProviderRunResult:
    """Ingest the vertical profile at every requested lead, not just lead 0.

    Fetching only lead 0 gave a vertical snapshot at cycle time and no vertical
    forecast at all, so nothing above the model surface could be shown for any
    future hour.
    """
    import hashlib

    count = 0
    failed_leads: list[FailedLead] = []
    for lead in leads:
        try:
            payload = _fetch_pressure(cycle, lead)
        except Exception as error:  # pylint: disable=broad-exception-caught
            # A lead that the provider has not published yet must not discard
            # the leads that are already available.
            print(f"  pressure +{lead}h unavailable; skipping lead")
            failed_leads.append(_failed_lead(lead, error))
            continue
        messages = parse_pressure_messages(payload)
        records = normalize_pressure_levels(messages, LAT, LON, PRESSURE_LEVELS)
        digest = hashlib.sha256(payload).hexdigest()
        artifact_path = RAW_ROOT / "ecmwf-ifs" / digest / "pressure.grib2"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        if not artifact_path.exists():
            artifact_path.write_bytes(payload)
        try:
            wind_path = _materialize_ifs_wind_field(artifact_path, cycle, lead)
            if wind_path is not None:
                print(f"  wind field +{lead}h: {wind_path.name}")
        except Exception:  # pylint: disable=broad-exception-caught
            # Wind visualization is an additive derived product. A decoder or
            # materialization failure must not roll back canonical weather that
            # was already retrieved and can still serve every existing API.
            print(f"  wind field +{lead}h unavailable; continuing")
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
    return _provider_result(count, failed_leads)


def _run_ifs_with_fallback(service) -> int | ProviderRunResult:
    """Run the existing IFS ingestion, retaining its previous-cycle fallback."""
    cycle = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    hour = cycle.hour
    cycle = cycle.replace(hour=hour - (hour % 6))  # snap to 00/06/12/18
    # ECMWF publishes a cycle roughly 6-8 h after its nominal time, so the two
    # most recent cycles are normally still absent. Walking back finds the
    # newest published one; the timer is phased so that is usually cycle-8h.
    last_error: Exception | None = None
    for _ in range(8):
        try:
            print(f"ingesting IFS cycle {cycle.isoformat()}")
            surface = _as_provider_result(_ingest_ifs(service, cycle))
            print(f"ingested {surface.records_ingested} surface leads")
            pressure = _as_provider_result(_ingest_ifs_pressure(service, cycle))
            print(f"ingested {pressure.records_ingested} pressure records")
            total = surface.records_ingested + pressure.records_ingested
            if total == 0:
                # Preserve the prior behavior: an available cycle that yielded
                # nothing is a failed IFS job, not a reason to ingest an older
                # cycle and report the pass as current.
                raise _EmptyIfsCycle(
                    f"IFS cycle {cycle.isoformat()} yielded no records"
                )
            failed_leads = surface.failed_leads + pressure.failed_leads
            return (
                ProviderRunResult(total, failed_leads)
                if failed_leads
                else total
            )
        except _EmptyIfsCycle:
            raise
        except Exception as exc:  # pylint: disable=broad-exception-caught
            last_error = exc
            print(f"cycle {cycle.isoformat()} unavailable; trying previous")
            cycle = cycle - timedelta(hours=6)
    raise RuntimeError(
        "no recent IFS cycle available in the last 48 h"
    ) from last_error


class _EmptyIfsCycle(RuntimeError):
    """An available IFS cycle completed but produced no canonical records."""


def _failed_lead(lead: int, error: Exception) -> FailedLead:
    """Create bounded partial-failure facts for scheduler reporting."""
    from everest_api.registry.redaction import redact_failure_detail

    detail = str(error).replace("\n", " ").strip()
    return FailedLead(
        lead,
        error.__class__.__name__[:128],
        redact_failure_detail((detail or error.__class__.__name__)[:256]),
    )


def _provider_result(count: int, failures: list[FailedLead]):
    """Retain integer compatibility when every requested lead succeeded."""
    return ProviderRunResult(count, tuple(failures)) if failures else count


def _as_provider_result(result: int | ProviderRunResult) -> ProviderRunResult:
    """Normalize legacy integer provider results for aggregation."""
    return (
        result
        if isinstance(result, ProviderRunResult)
        else ProviderRunResult(result)
    )


def create_gfs_job(service, raw_root):
    """Lazily import and compose the concrete GFS scheduler job."""
    from everest_api.scheduler.provider_jobs import create_gfs_job as factory

    return factory(service, raw_root)


def create_aifs_job(service, raw_root):
    """Lazily import and compose the concrete AIFS scheduler job."""
    from everest_api.scheduler.provider_jobs import create_aifs_job as factory

    return factory(service, raw_root)


def create_icon_job(service):
    """Lazily import and compose the concrete ICON scheduler job."""
    from everest_api.scheduler.provider_jobs import create_icon_job as factory

    return factory(service)


def build_provider_jobs(  # pylint: disable=too-many-arguments
    config: SchedulerConfig,
    ifs_job,
    service=None,
    *,
    gfs_job=None,
    aifs_job=None,
    icon_job=None,
) -> tuple[ProviderJob, ...]:
    """Compose lazy concrete jobs while retaining injectable test seams."""
    if service is None and any(
        (config.gfs_enabled, config.aifs_enabled, config.icon_enabled)
    ):
        raise RuntimeError(
            "enabled optional provider jobs require ingestion service"
        )
    # Import only when an enabled job needs its default implementation. This
    # keeps the base API environment independent of optional weather extras.
    if config.gfs_enabled and gfs_job is None:
        gfs_job = create_gfs_job(service, RAW_ROOT)
    if config.aifs_enabled and aifs_job is None:
        aifs_job = create_aifs_job(service, RAW_ROOT)
    if config.icon_enabled and icon_job is None:
        icon_job = create_icon_job(service)
    return (
        ProviderJob("ecmwf-ifs", ifs_job, config.ifs_enabled),
        ProviderJob(
            "noaa-gfs",
            gfs_job or (lambda: 0),
            config.gfs_enabled,
        ),
        ProviderJob(
            "ecmwf-aifs",
            aifs_job or (lambda: 0),
            config.aifs_enabled,
        ),
        ProviderJob(
            "dwd-icon",
            icon_job or (lambda: 0),
            config.icon_enabled,
        ),
    )


def main() -> int:
    """Run one configured provider pass with source-specific accounting.

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
    config = SchedulerConfig.from_environment()
    jobs = build_provider_jobs(
        config, lambda: _run_ifs_with_fallback(service), service
    )
    result = run_once(jobs, recorder=DataSourceRunRecorder(factory))
    print(
        f"scheduler {result.status.value}: attempted={result.attempted_sources} "
        f"succeeded={result.succeeded_sources} "
        f"degraded={result.degraded_sources} failed={result.failed_sources} "
        f"skipped={result.skipped_sources} records={result.records_ingested}"
    )
    if result.status is RunStatus.SUCCESS:
        return 0
    if result.status is RunStatus.DEGRADED:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
