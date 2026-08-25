"""Provider-boundary adapter from retained DWD ICON data to neutral commands."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from weather_ingestion_contract import (
    CanonicalRecordInput,
    IngestionPort,
    RawArtifactDescriptor,
)
from services.weather.contract import RecordType, WeatherRecord
from services.weather.icon.connector import (
    AOI_ID,
    AOI_SCOPE_ID,
    AOI_VERSION,
    RawRetrieval,
)


ICON_SOURCE_ID = "dwd-icon"
ICON_MODEL = "ICON"
_SCALAR_TYPES = (str, int, float, bool)
_BACKEND_POLICY_KEYS = frozenset(
    {
        "backend_retention_owner",
        "backend_retention_class",
        "backend_retention_period",
        "backend_disposition_state",
        "backend_hold_state",
    }
)


@dataclass(frozen=True)
class IconRawRetentionMetadata:  # pylint: disable=too-many-instance-attributes
    """Verified immutable DWD ICON raw-artifact facts."""

    dataset: str
    object_reference: str
    sha256: str
    retrieved_at: datetime
    data_format: str
    size_bytes: int
    source_url: str | None
    forecast_cycle: datetime
    forecast_lead_seconds: int
    valid_time: datetime
    raw_metadata: dict[str, Any]
    metadata_sha256: str
    sidecar_sha256: str
    backend_policy_facts: (
        Mapping[str, str | int | float | bool | None] | None
    ) = None
    source_id: str = ICON_SOURCE_ID
    model: str = ICON_MODEL


@dataclass(frozen=True)
class IconCanonicalRecord:
    """Normalized ICON record and parser-preserved native grid identity."""

    weather: WeatherRecord
    spatial_key: str
    route_profile: str | None = None


# Integrity verification keeps all three exact byte streams and digests local.
# pylint: disable=too-many-locals
def icon_raw_retention_metadata_from_retrieval(
    retrieval: RawRetrieval,
    backend_policy_facts: (
        Mapping[str, str | int | float | bool | None] | None
    ) = None,
) -> IconRawRetentionMetadata:
    """Verify connector output and return authoritative adapter metadata."""
    payload = _required_file(retrieval.payload_path, "payload")
    metadata_bytes = _required_file(retrieval.metadata_path, "metadata")
    sidecar_path = retrieval.metadata_path.with_name(
        f"{retrieval.metadata_path.name}.sha256"
    )
    sidecar_bytes = _required_file(sidecar_path, "metadata checksum sidecar")
    payload_sha256 = _sha256(payload)
    metadata_sha256 = _sha256(metadata_bytes)
    sidecar_sha256 = _sha256(sidecar_bytes)
    if not hmac.compare_digest(payload_sha256, retrieval.sha256):
        raise ValueError("ICON connector payload checksum mismatch")
    if len(payload) != retrieval.size_bytes:
        raise ValueError("ICON connector payload size mismatch")
    try:
        declared_metadata_sha256 = sidecar_bytes.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise ValueError(
            "ICON metadata checksum sidecar is not ASCII"
        ) from error
    if not hmac.compare_digest(metadata_sha256, declared_metadata_sha256):
        raise ValueError("ICON metadata checksum mismatch")
    if sidecar_bytes != f"{metadata_sha256}\n".encode("ascii"):
        raise ValueError("ICON metadata checksum sidecar is not canonical")
    metadata = _canonical_metadata(metadata_bytes)
    cycle = _metadata_datetime(metadata, "cycle")
    valid_time = _valid_time_datetime(metadata)
    retrieved_at = _metadata_datetime(metadata, "retrieved_at")
    lead_seconds = _required_integer(metadata, "lead_hours") * 3600
    _validate_connector_facts(
        retrieval,
        metadata,
        payload_sha256,
        cycle,
        valid_time,
        lead_seconds,
    )
    policy = _validate_backend_policy_facts(backend_policy_facts)
    return IconRawRetentionMetadata(
        dataset=_required_string(metadata, "dataset"),
        object_reference=str(retrieval.payload_path),
        sha256=payload_sha256,
        retrieved_at=retrieved_at,
        data_format=_required_string(metadata, "format"),
        size_bytes=len(payload),
        source_url=retrieval.url or None,
        forecast_cycle=cycle,
        forecast_lead_seconds=lead_seconds,
        valid_time=valid_time,
        raw_metadata=metadata,
        metadata_sha256=metadata_sha256,
        sidecar_sha256=sidecar_sha256,
        backend_policy_facts=policy,
    )


class IconIngestionAdapter:  # pylint: disable=too-few-public-methods
    """Validate ICON provenance and project sidecar facts to scalars."""

    def __init__(self, ingestion_port: IngestionPort) -> None:
        """Bind the thin meteorology adapter to a backend-owned port."""
        self._ingestion_port = ingestion_port

    def ingest(
        self,
        raw: IconRawRetentionMetadata,
        records: Sequence[IconCanonicalRecord],
    ) -> UUID:
        """Reject inconsistent provenance before raw retention."""
        _validate_raw(raw)
        canonical = tuple(_to_canonical(raw, record) for record in records)
        descriptor = RawArtifactDescriptor(
            source_id=raw.source_id,
            dataset=raw.dataset,
            object_reference=raw.object_reference,
            sha256=raw.sha256,
            retrieved_at=raw.retrieved_at,
            data_format=raw.data_format,
            size_bytes=raw.size_bytes,
            source_url=raw.source_url,
            forecast_cycle=raw.forecast_cycle,
            forecast_lead_seconds=raw.forecast_lead_seconds,
            valid_time=raw.valid_time,
            metadata=_project_metadata(raw),
        )
        return self._ingestion_port.ingest(descriptor, canonical)


def compose_icon_ingestion_adapter(
    ingestion_port: IngestionPort,
) -> IconIngestionAdapter:
    """Return ICON's exact backend-composition entry point."""
    return IconIngestionAdapter(ingestion_port)


def _validate_raw(raw: IconRawRetentionMetadata) -> None:
    """Verify one coherent ICON raw artifact before constructing a command."""
    for label, value in (
        ("cycle", raw.forecast_cycle),
        ("valid time", raw.valid_time),
        ("retrieval time", raw.retrieved_at),
    ):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError(f"ICON {label} must be timezone-aware UTC")
    if raw.source_id != ICON_SOURCE_ID or raw.model != ICON_MODEL:
        raise ValueError("ICON raw metadata has inconsistent source or model")
    if raw.valid_time != raw.forecast_cycle + timedelta(
        seconds=_seconds(raw.forecast_lead_seconds)
    ):
        raise ValueError("ICON raw valid time does not match cycle and lead")
    if raw.raw_metadata.get("source") != raw.source_id:
        raise ValueError("ICON raw metadata source does not match source ID")
    if raw.raw_metadata.get("model") != raw.model:
        raise ValueError("ICON raw metadata model does not match model")
    if raw.raw_metadata.get("aoi_scope_id") is None:
        raise ValueError("ICON raw metadata requires aoi_scope_id")


def _project_metadata(
    raw: IconRawRetentionMetadata,
) -> dict[str, str | int | float | bool | None]:
    """Project selected sidecar facts into the scalar-only shared DTO."""
    values: dict[str, str | int | float | bool | None] = {
        "provider_source_id": raw.source_id,
        "provider_name": _required_scalar(raw, "provider"),
        "provider_dataset": raw.dataset,
        "provider_model": raw.model,
        "provider_format": raw.data_format,
        "provider_cycle": raw.forecast_cycle.isoformat(),
        "provider_lead_seconds": raw.forecast_lead_seconds,
        "provider_valid_time": raw.valid_time.isoformat(),
        "provider_retrieved_at": raw.retrieved_at.isoformat(),
        "provider_payload_size_bytes": raw.size_bytes,
        "provider_payload_sha256": raw.sha256,
        "provider_metadata_sha256": raw.metadata_sha256,
        "provider_sidecar_sha256": raw.sidecar_sha256,
        "provider_aoi_id": _required_scalar(raw, "aoi_id"),
        "provider_aoi_version": _required_scalar(raw, "aoi_version"),
        "provider_aoi_scope_id": _required_scalar(raw, "aoi_scope_id"),
        "provenance_reference": raw.object_reference,
    }
    if raw.backend_policy_facts is not None:
        values.update(raw.backend_policy_facts)
    return values


def _required_scalar(
    raw: IconRawRetentionMetadata,
    key: str,
) -> str | int | float | bool | None:
    """Return one required scalar sidecar fact, rejecting unsafe values."""
    value = raw.raw_metadata.get(key)
    if value is None:
        raise ValueError(f"ICON raw metadata requires scalar {key}")
    if type(value) not in _SCALAR_TYPES:
        raise TypeError(f"ICON raw metadata {key} must be scalar")
    return value


def _required_file(path: Path, label: str) -> bytes:
    """Read one required connector output file or fail closed."""
    try:
        if not path.is_file():
            raise ValueError(f"ICON connector {label} is missing")
        return path.read_bytes()
    except OSError as error:
        raise ValueError(f"ICON connector {label} cannot be read") from error


def _sha256(value: bytes) -> str:
    """Return the SHA-256 hexadecimal digest of exact retained bytes."""
    return hashlib.sha256(value).hexdigest()


def _canonical_metadata(encoded: bytes) -> dict[str, Any]:
    """Decode and verify connector canonical JSON metadata bytes."""
    try:
        value = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ICON metadata is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("ICON metadata must be a JSON object")
    canonical = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    if canonical != encoded:
        raise ValueError("ICON metadata is not canonical deterministic JSON")
    return value


def _metadata_datetime(metadata: dict[str, Any], key: str) -> datetime:
    """Parse one required UTC ISO-8601 metadata value."""
    value = _required_string(metadata, key)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"ICON metadata {key} is not ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"ICON metadata {key} must be UTC")
    return parsed.astimezone(timezone.utc)


def _valid_time_datetime(metadata: dict[str, Any]) -> datetime:
    """Read current ISO valid time or immutable historical epoch metadata."""
    value = metadata.get("valid_time")
    if value.__class__ is str:
        return _metadata_datetime(metadata, "valid_time")
    if value.__class__ in (int, float):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as error:
            raise ValueError(
                "ICON metadata valid_time epoch is invalid"
            ) from error
    raise ValueError("ICON metadata valid_time must be UTC ISO-8601")


def _required_string(metadata: dict[str, Any], key: str) -> str:
    """Return a nonempty exact string metadata fact."""
    value = metadata.get(key)
    if value.__class__ is not str or not value:
        raise ValueError(f"ICON metadata requires string {key}")
    return value


def _required_integer(metadata: dict[str, Any], key: str) -> int:
    """Return an exact nonnegative integer metadata fact."""
    value = metadata.get(key)
    if value.__class__ is not int or value < 0:
        raise ValueError(f"ICON metadata requires nonnegative integer {key}")
    return value


# Each independent connector return fact is explicit at this integrity boundary.
# pylint: disable=too-many-arguments,too-many-positional-arguments
def _validate_connector_facts(
    retrieval: RawRetrieval,
    metadata: dict[str, Any],
    payload_sha256: str,
    cycle: datetime,
    valid_time: datetime,
    lead_seconds: int,
) -> None:
    """Require the sidecar to describe the exact connector return value."""
    if (
        retrieval.cycle.tzinfo is None
        or retrieval.cycle.utcoffset() != timedelta(0)
    ):
        raise ValueError("ICON connector retrieval cycle must be UTC")
    expected = {
        "source": ICON_SOURCE_ID,
        "provider": "DWD",
        "model": ICON_MODEL,
        "aoi_id": AOI_ID,
        "aoi_version": AOI_VERSION,
        "aoi_scope_id": AOI_SCOPE_ID,
        "sha256": payload_sha256,
        "size_bytes": retrieval.size_bytes,
        "cycle": retrieval.cycle.astimezone(timezone.utc).isoformat(),
        "lead_hours": retrieval.lead_hours,
        "fields": list(retrieval.fields),
        "urls": retrieval.url.split(",") if retrieval.url else [],
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"ICON connector metadata {key} mismatch")
    if cycle != retrieval.cycle.astimezone(timezone.utc):
        raise ValueError("ICON connector metadata cycle mismatch")
    if lead_seconds != retrieval.lead_hours * 3600:
        raise ValueError("ICON connector metadata lead mismatch")
    if valid_time != cycle + timedelta(seconds=lead_seconds):
        raise ValueError("ICON connector metadata valid_time mismatch")
    epoch = metadata.get("valid_time_epoch")
    if epoch is not None and epoch != int(valid_time.timestamp()):
        raise ValueError("ICON connector metadata valid_time_epoch mismatch")


def _validate_backend_policy_facts(
    facts: Mapping[str, str | int | float | bool | None] | None,
) -> Mapping[str, str | int | float | bool | None] | None:
    """Validate explicit backend-owned policy facts without inventing them."""
    if facts is None:
        return None
    copied = dict(facts)
    if not set(copied).issubset(_BACKEND_POLICY_KEYS):
        raise ValueError(
            "ICON backend policy facts require backend-prefixed keys"
        )
    for key, value in copied.items():
        if value is not None and type(value) not in _SCALAR_TYPES:
            raise TypeError(f"ICON backend policy fact {key} must be scalar")
    return copied


def _to_canonical(
    raw: IconRawRetentionMetadata,
    icon_record: IconCanonicalRecord,
) -> CanonicalRecordInput:
    """Map canonical values without filtering nulls or QC flags."""
    weather = icon_record.weather
    if not icon_record.spatial_key:
        raise ValueError("ICON canonical record requires a spatial key")
    if weather.record_type is not RecordType.FORECAST:
        raise ValueError("ICON ingestion accepts forecast records only")
    if weather.source != raw.source_id or weather.model != raw.model:
        raise ValueError(
            "ICON canonical record source or model does not match raw"
        )
    if weather.forecast is None:
        raise ValueError("ICON forecast record requires a forecast identity")
    if weather.forecast.cycle != raw.forecast_cycle:
        raise ValueError("ICON canonical record cycle does not match raw")
    if (
        _seconds(weather.forecast.lead_time.total_seconds())
        != raw.forecast_lead_seconds
    ):
        raise ValueError("ICON canonical record lead does not match raw")
    if weather.timestamp != raw.valid_time:
        raise ValueError("ICON canonical record valid time does not match raw")
    forecast = weather.forecast
    return CanonicalRecordInput(
        record_type=weather.record_type.value,
        timestamp=weather.timestamp,
        latitude=weather.latitude,
        longitude=weather.longitude,
        altitude=weather.altitude,
        spatial_key=icon_record.spatial_key,
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
        forecast_lead_seconds=_seconds(forecast.lead_time.total_seconds()),
        route_profile=icon_record.route_profile,
    )


def _seconds(value: float | int) -> int:
    """Accept only whole forecast lead seconds."""
    if int(value) != value:
        raise ValueError(
            "ICON forecast lead must be an integral number of seconds"
        )
    return int(value)
