"""Concrete, disabled-by-default forecast provider scheduler jobs.

All provider imports are lazy so importing the base API does not require the
optional GRIB/retrieval extras.  Factories accept deterministic seams for tests.
"""

# Provider imports are intentionally lazy, and composition helpers keep every
# provenance value explicit at the ingestion trust boundary.
# pylint: disable=import-outside-toplevel,too-many-arguments
# pylint: disable=too-many-positional-arguments,too-many-locals

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from everest_api.scheduler.runner import FailedLead, ProviderRunResult


GFS_SURFACE_INVENTORY = (
    "TMP:2 m above ground",
    "UGRD:10 m above ground",
    "VGRD:10 m above ground",
    "APCP:surface",
    "HGT:surface",
    "VIS:surface",
)
AIFS_SURFACE_INVENTORY = ("z", "10u", "10v", "2t", "tp")
APPROVED_HERBIE_PRIORITY = ("aws", "google", "nomads")
APPROVED_HERBIE_SOURCES = frozenset(APPROVED_HERBIE_PRIORITY)
DEFAULT_LEADS = tuple(range(0, 73, 3))
DEFAULT_LOOKBACK_CYCLES = 8
EVEREST_LATITUDE = 27.98806
EVEREST_LONGITUDE = 86.92528


class ProviderJobConfigurationError(RuntimeError):
    """A provider job cannot safely prove its required configuration."""


def create_gfs_job(  # pylint: disable=too-many-arguments
    service: Any,
    raw_root: str | Path,
    *,
    client_factory: Callable[[], Any] | None = None,
    parser: Callable[[bytes], Sequence[Any]] | None = None,
    normalizer: Callable[..., Any] | None = None,
    adapter_factory: Callable[[Any], Any] | None = None,
    now: Callable[[], datetime] | None = None,
    leads: Sequence[int] = DEFAULT_LEADS,
    lookback_cycles: int = DEFAULT_LOOKBACK_CYCLES,
) -> Callable[[], int]:
    """Build a bounded GFS job using Herbie and the existing GFS pipeline."""
    bounded_leads = _bounded_leads(leads)
    root = Path(raw_root)

    def _run() -> int:
        nonlocal parser, normalizer, adapter_factory
        if client_factory is None:
            client = _official_gfs_client()
        else:
            client = client_factory()
        _validate_herbie_client(client, require_resolved=False)
        if parser is None:
            from services.weather.gfs.parser import parse_grib_bytes

            parser = parse_grib_bytes
        if normalizer is None:
            from services.weather.gfs.normalizer import normalize_messages

            normalizer = normalize_messages
        if adapter_factory is None:
            from services.weather.gfs.ingestion import (
                compose_gfs_ingestion_adapter,
            )

            adapter_factory = compose_gfs_ingestion_adapter
        adapter = adapter_factory(service)
        return _run_with_cycle_lookback(
            lambda cycle, lead: _ingest_gfs_lead(
                client, adapter, root, cycle, lead, parser, normalizer
            ),
            now=now,
            leads=bounded_leads,
            lookback_cycles=lookback_cycles,
        )

    return _run


def create_aifs_job(  # pylint: disable=too-many-arguments
    service: Any,
    raw_root: str | Path,
    *,
    client_factory: Callable[[], Any] | None = None,
    parser: Callable[[bytes], Sequence[Any]] | None = None,
    normalizer: Callable[..., Any] | None = None,
    spatial_key_factory: Callable[[Any, int], str] | None = None,
    nearest_index: Callable[..., int] | None = None,
    now: Callable[[], datetime] | None = None,
    leads: Sequence[int] = DEFAULT_LEADS,
    lookback_cycles: int = DEFAULT_LOOKBACK_CYCLES,
) -> Callable[[], int]:
    """Build a bounded AIFS job with a direct provider-safe descriptor."""
    bounded_leads = _bounded_leads(leads)
    root = Path(raw_root)

    def _run() -> int:
        nonlocal parser, normalizer, spatial_key_factory, nearest_index
        if client_factory is None:
            from services.weather.aifs.opendata_client import (
                EcmwfAifsOpenDataClient,
            )

            client = EcmwfAifsOpenDataClient()
        else:
            client = client_factory()
        if parser is None:
            from services.weather.aifs.parser import parse_grib_bytes

            parser = parse_grib_bytes
        if (
            normalizer is None
            or spatial_key_factory is None
            or nearest_index is None
        ):
            from services.weather.aifs.normalizer import (
                nearest_grid_index,
                normalize_messages,
                provider_spatial_key,
            )

            normalizer = normalizer or normalize_messages
            spatial_key_factory = spatial_key_factory or provider_spatial_key
            nearest_index = nearest_index or nearest_grid_index
        return _run_with_cycle_lookback(
            lambda cycle, lead: _ingest_aifs_lead(
                client,
                service,
                root,
                cycle,
                lead,
                parser,
                normalizer,
                spatial_key_factory,
                nearest_index,
            ),
            now=now,
            leads=bounded_leads,
            lookback_cycles=lookback_cycles,
        )

    return _run


def create_icon_job(  # pylint: disable=too-many-arguments
    service: Any,
    *,
    connector_factory: Callable[[], Any] | None = None,
    parser: Callable[[bytes], Sequence[Any]] | None = None,
    normalizer: Callable[..., Any] | None = None,
    raw_metadata_factory: Callable[[Any], Any] | None = None,
    adapter_factory: Callable[[Any], Any] | None = None,
    now: Callable[[], datetime] | None = None,
    leads: Sequence[int] = DEFAULT_LEADS,
    lookback_cycles: int = DEFAULT_LOOKBACK_CYCLES,
) -> Callable[[], int]:
    """Build a bounded ICON job around the official DWD retained pipeline."""
    bounded_leads = _bounded_leads(leads)

    def _run() -> int:
        nonlocal parser, normalizer, raw_metadata_factory, adapter_factory
        if connector_factory is None:
            from services.weather.icon.connector import DwdIconConnector

            connector = DwdIconConnector()
        else:
            connector = connector_factory()
        if parser is None:
            from services.weather.icon.parser import parse_grib_bytes

            parser = parse_grib_bytes
        if normalizer is None:
            from services.weather.icon.normalizer import (
                normalize_canonical_record,
            )

            normalizer = normalize_canonical_record
        if raw_metadata_factory is None or adapter_factory is None:
            from services.weather.icon.ingestion import (
                compose_icon_ingestion_adapter,
                icon_raw_retention_metadata_from_retrieval,
            )

            raw_metadata_factory = (
                raw_metadata_factory
                or icon_raw_retention_metadata_from_retrieval
            )
            adapter_factory = adapter_factory or compose_icon_ingestion_adapter
        adapter = adapter_factory(service)
        return _run_with_cycle_lookback(
            lambda cycle, lead: _ingest_icon_lead(
                connector,
                adapter,
                cycle,
                lead,
                parser,
                normalizer,
                raw_metadata_factory,
            ),
            now=now,
            leads=bounded_leads,
            lookback_cycles=lookback_cycles,
        )

    return _run


def _ingest_gfs_lead(
    client, adapter, root, cycle, lead, parser, normalizer
) -> int:
    from services.weather.gfs.ingestion import (
        GfsCanonicalRecord,
        GfsRawRetentionMetadata,
    )
    from services.weather.retrieval import RetrievalRequest

    request = RetrievalRequest(
        cycle, lead, GFS_SURFACE_INVENTORY, root / "noaa-gfs"
    )
    artifact = client.retrieve(request)
    _validate_artifact(artifact, "noaa-gfs", request)
    _validate_herbie_client(client, require_resolved=True)
    resolved_source = getattr(client, "resolved_source", None)
    weather = normalizer(
        tuple(parser(artifact.path.read_bytes())),
        EVEREST_LATITUDE,
        EVEREST_LONGITUDE,
    )
    valid_time = cycle + timedelta(hours=lead)
    raw = GfsRawRetentionMetadata(
        dataset="GFS pgrb2 0.25 degree",
        object_reference=str(artifact.path),
        sha256=artifact.sha256,
        retrieved_at=datetime.now(UTC),
        data_format="GRIB2",
        size_bytes=artifact.size_bytes,
        source_url=(f"herbie://{resolved_source}" if resolved_source else None),
        forecast_cycle=cycle,
        forecast_lead_seconds=lead * 3600,
        valid_time=valid_time,
        raw_metadata={
            "source": "noaa-gfs",
            "model": "GFS",
            "herbie_source": resolved_source or "approved-priority",
        },
    )
    record = GfsCanonicalRecord(
        weather, f"gfs:0p25:{weather.latitude:.5f}:{weather.longitude:.5f}"
    )
    adapter.ingest(raw, (record,))
    return 1


def _ingest_aifs_lead(
    client,
    service,
    root,
    cycle,
    lead,
    parser,
    normalizer,
    spatial_key_factory,
    nearest_index,
) -> int:
    from services.weather.retrieval import RetrievalRequest
    from weather_ingestion_contract import RawArtifactDescriptor

    request = RetrievalRequest(
        cycle, lead, AIFS_SURFACE_INVENTORY, root / "ecmwf-aifs"
    )
    artifact = client.retrieve(request)
    _validate_artifact(artifact, "ecmwf-aifs", request)
    messages = tuple(parser(artifact.path.read_bytes()))
    weather = normalizer(messages, EVEREST_LATITUDE, EVEREST_LONGITUDE)
    _validate_weather_identity(weather, "ecmwf-aifs", "AIFS")
    _validate_forecast_identity(weather, cycle, lead)
    index = nearest_index(messages[0], EVEREST_LATITUDE, EVEREST_LONGITUDE)
    valid_time = cycle + timedelta(hours=lead)
    descriptor = RawArtifactDescriptor(
        source_id="ecmwf-aifs",
        dataset="AIFS Single Open Data 0.25 degree",
        object_reference=str(artifact.path),
        sha256=artifact.sha256,
        retrieved_at=datetime.now(UTC),
        data_format="GRIB2",
        size_bytes=artifact.size_bytes,
        forecast_cycle=cycle,
        forecast_lead_seconds=lead * 3600,
        valid_time=valid_time,
        metadata={
            "provider_source_id": "ecmwf-aifs",
            "provider_name": "ECMWF",
            "provider_model": "AIFS",
            "provider_payload_sha256": artifact.sha256,
            "provider_payload_size_bytes": artifact.size_bytes,
        },
    )
    canonical = _canonical_input(
        weather, spatial_key_factory(messages[0], index)
    )
    service.ingest(descriptor, (canonical,))
    return 1


def _ingest_icon_lead(
    connector, adapter, cycle, lead, parser, normalizer, raw_metadata_factory
) -> int:
    retrieval = connector.retrieve(cycle, lead_hours=lead)
    messages = tuple(parser(retrieval.payload_path.read_bytes()))
    record = normalizer(messages, EVEREST_LATITUDE, EVEREST_LONGITUDE)
    _validate_weather_identity(record.weather, "dwd-icon", "ICON")
    raw = raw_metadata_factory(retrieval)
    if (raw.source_id, raw.model) != ("dwd-icon", "ICON"):
        raise ValueError("ICON raw source or model identity mismatch")
    adapter.ingest(raw, (record,))
    return 1


def _canonical_input(weather: Any, spatial_key: str):
    from weather_ingestion_contract import CanonicalRecordInput

    forecast = weather.forecast
    return CanonicalRecordInput(
        record_type=weather.record_type.value,
        timestamp=weather.timestamp,
        latitude=weather.latitude,
        longitude=weather.longitude,
        altitude=weather.altitude,
        spatial_key=spatial_key,
        source=weather.source,
        model=weather.model,
        quality_flags=tuple(weather.quality_flags),
        wind_speed=weather.wind_speed,
        wind_direction=weather.wind_direction,
        temperature=weather.temperature,
        precipitation=weather.precipitation,
        visibility=weather.visibility,
        pressure=weather.pressure,
        relative_humidity=weather.relative_humidity,
        dew_point=weather.dew_point,
        cloud_cover=weather.cloud_cover,
        cloud_base=weather.cloud_base,
        cloud_top=weather.cloud_top,
        snowfall=weather.snowfall,
        gust_speed=weather.gust_speed,
        forecast_cycle=forecast.cycle,
        forecast_lead_seconds=int(forecast.lead_time.total_seconds()),
    )


def _run_with_cycle_lookback(
    ingest_lead: Callable[[datetime, int], int],
    *,
    now: Callable[[], datetime] | None,
    leads: tuple[int, ...],
    lookback_cycles: int,
) -> int | ProviderRunResult:
    if lookback_cycles < 1 or lookback_cycles > 16:
        raise ValueError("provider lookback must be between 1 and 16 cycles")
    current = (now or (lambda: datetime.now(UTC)))()
    cycle = _latest_cycle(current)
    last_error: Exception | None = None
    for _ in range(lookback_cycles):
        try:
            count = ingest_lead(cycle, leads[0])
        except ProviderJobConfigurationError:
            raise
        except Exception as error:  # pylint: disable=broad-exception-caught
            last_error = error
            cycle -= timedelta(hours=6)
            continue
        failed_leads: list[FailedLead] = []
        for lead in leads[1:]:
            try:
                count += ingest_lead(cycle, lead)
            except Exception as error:  # pylint: disable=broad-exception-caught
                failed_leads.append(
                    FailedLead(
                        lead,
                        error.__class__.__name__[:128],
                        _bounded_failure_detail(error),
                    )
                )
                continue
        if count == 0:
            raise RuntimeError(
                f"provider cycle {cycle.isoformat()} yielded no records"
            )
        if failed_leads:
            return ProviderRunResult(count, tuple(failed_leads))
        return count
    raise RuntimeError(
        "no recent published provider cycle available"
    ) from last_error


def _latest_cycle(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "scheduler clock must return a timezone-aware datetime"
        )
    value = value.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    return value.replace(hour=value.hour - value.hour % 6)


def _bounded_failure_detail(error: Exception) -> str:
    """Keep per-lead diagnostics bounded and free of obvious credentials."""
    from everest_api.registry.redaction import redact_failure_detail

    detail = str(error).replace("\n", " ").strip()
    return redact_failure_detail((detail or error.__class__.__name__)[:256])


def _bounded_leads(leads: Sequence[int]) -> tuple[int, ...]:
    values = tuple(leads)
    if not values or values[0] != 0 or len(values) > 49:
        raise ValueError(
            "provider leads must start at zero and contain at most 49 values"
        )
    if any(
        value.__class__ is not int or value < 0 or value > 240
        for value in values
    ):
        raise ValueError("provider leads must be integer hours in [0, 240]")
    if tuple(sorted(set(values))) != values:
        raise ValueError("provider leads must be unique and increasing")
    return values


def _validate_herbie_client(client: Any, *, require_resolved: bool) -> None:
    priority = tuple(getattr(client, "source_priority", ()))
    if priority != APPROVED_HERBIE_PRIORITY:
        raise ProviderJobConfigurationError(
            "Herbie source priority must use the approved official default"
        )
    resolved = getattr(client, "resolved_source", None)
    if (resolved is not None and resolved not in APPROVED_HERBIE_SOURCES) or (
        require_resolved and resolved is None
    ):
        raise ProviderJobConfigurationError(
            "Herbie source cannot be verified as an official approved source"
        )


def _official_gfs_client() -> Any:
    """Compose Herbie while exposing the source selected for each download."""
    from services.weather.gfs.herbie_client import HerbieGfsClient

    state: dict[str, str | None] = {"resolved_source": None}

    def factory(*args: Any, **kwargs: Any) -> Any:
        try:
            from herbie import Herbie
        except ImportError as error:
            raise ProviderJobConfigurationError(
                "GFS scheduler requires the optional Herbie dependency"
            ) from error
        herbie = Herbie(*args, **kwargs)

        class _VerifiedDownload:  # pylint: disable=too-few-public-methods
            def download(
                self, *download_args: Any, **download_kwargs: Any
            ) -> Any:
                """Download once and capture Herbie's selected source."""
                result = herbie.download(*download_args, **download_kwargs)
                source = getattr(herbie, "SOURCE", None)
                state["resolved_source"] = (
                    source.lower() if isinstance(source, str) else None
                )
                return result

        return _VerifiedDownload()

    client = HerbieGfsClient(herbie_factory=factory)

    class _OfficialClient:  # pylint: disable=too-few-public-methods
        source_priority = client.source_priority

        @property
        def resolved_source(self) -> str | None:
            """Return the concrete source selected by the last download."""
            return state["resolved_source"]

        def retrieve(self, request: Any) -> Any:
            """Delegate retrieval through the official-source observer."""
            return client.retrieve(request)

    return _OfficialClient()


def _validate_artifact(artifact: Any, provider: str, request: Any) -> None:
    if artifact.provider != provider or artifact.request != request:
        raise ValueError(f"{provider} retrieval identity mismatch")
    from services.weather.retrieval import RetrievedArtifact

    verified = RetrievedArtifact.from_path(artifact.path, provider, request)
    if (
        verified.sha256 != artifact.sha256
        or verified.size_bytes != artifact.size_bytes
    ):
        raise ValueError(f"{provider} retrieval integrity mismatch")


def _validate_weather_identity(weather: Any, source: str, model: str) -> None:
    if (weather.source, weather.model) != (source, model):
        raise ValueError(
            f"{source} normalized source or model identity mismatch"
        )


def _validate_forecast_identity(
    weather: Any, cycle: datetime, lead_hours: int
) -> None:
    """Require normalized forecast time to match the requested run exactly."""
    forecast = weather.forecast
    expected_valid_time = cycle + timedelta(hours=lead_hours)
    if forecast is None or forecast.cycle != cycle:
        raise ValueError("normalized forecast cycle does not match request")
    if forecast.lead_time != timedelta(hours=lead_hours):
        raise ValueError("normalized forecast lead does not match request")
    if weather.timestamp != expected_valid_time:
        raise ValueError(
            "normalized forecast valid time does not match request"
        )


__all__ = [
    "AIFS_SURFACE_INVENTORY",
    "GFS_SURFACE_INVENTORY",
    "ProviderJobConfigurationError",
    "create_aifs_job",
    "create_gfs_job",
    "create_icon_job",
]
