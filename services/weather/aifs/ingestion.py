"""Thin AIFS adapter from verified provider facts to neutral ingestion DTOs."""

# Neutral DTO mapping is explicit and provider-local by architecture decision.
# pylint: disable=duplicate-code

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Sequence
from uuid import UUID

from weather_ingestion_contract import (
    CanonicalRecordInput,
    IngestionPort,
    RawArtifactDescriptor,
)
from services.weather.aifs.connector import (
    AOI_ID,
    AOI_SCOPE_ID,
    AOI_VERSION,
    MODEL,
    RAW_ROOT_ENVIRONMENT_VARIABLE,
    RawRetrieval,
    SOURCE_ID,
    EVEREST_LATITUDE,
    EVEREST_LONGITUDE,
)
from services.weather.aifs.parser import (
    EXPECTED_PARAMETERS,
    EXPECTED_PROCESS_IDENTIFIER,
    ParsedMessage,
    parse_grib_bytes,
    validate_decoded_inventory,
)
from services.weather.contract import RecordType, WeatherRecord


@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class AifsRawRetentionMetadata:  # pylint: disable=too-many-instance-attributes
    """Verified scalar AIFS retention facts for backend composition."""

    dataset: str
    object_reference: str
    sha256: str
    retrieved_at: datetime
    data_format: str
    size_bytes: int
    source_url: str
    forecast_cycle: datetime
    forecast_lead_seconds: int
    valid_time: datetime
    metadata_sha256: str
    sidecar_sha256: str
    aoi_id: str
    aoi_version: str
    aoi_scope_id: str
    decoded_parameters: tuple[str, ...] = EXPECTED_PARAMETERS
    decoded_process_identifier: int = EXPECTED_PROCESS_IDENTIFIER
    decoded_level_bindings: tuple[str, ...] = (
        "z:surface:0",
        "10u:heightAboveGround:10",
        "10v:heightAboveGround:10",
        "2t:heightAboveGround:2",
        "tp:surface:0",
    )
    source_id: str = SOURCE_ID
    model: str = MODEL


@dataclass(frozen=True)
class AifsCanonicalRecord:
    """One normalized AIFS record with provider-native grid identity."""

    weather: WeatherRecord
    spatial_key: str
    route_profile: str | None = None


def aifs_raw_retention_metadata_from_retrieval(
    retrieval: RawRetrieval,
) -> AifsRawRetentionMetadata:
    """Convert a retained artifact without trusting caller-supplied facts.

    ``RawRetrieval`` is a transport DTO and is not an authority: URL, hashes,
    sizes, cycle, lead, and parameters are all reconstructed from the three
    retained files.  Runtime conversion deliberately requires the approved
    ``EVEREST_RAW_ROOT`` instead of accepting a caller-provided root.
    """
    return aifs_raw_retention_metadata_from_artifact(
        retrieval.payload_path, retrieval
    )


# pylint: disable=too-many-locals
def aifs_raw_retention_metadata_from_artifact(
    payload_path: Path,
    retrieval: RawRetrieval | None = None,
) -> AifsRawRetentionMetadata:
    """Authoritatively reconstruct AIFS provenance from a retained artifact."""
    raw_root = _approved_raw_root()
    payload_path = _safe_artifact_path(payload_path, raw_root, "payload")
    artifact_dir = payload_path.parent
    metadata_path = artifact_dir / "metadata.json"
    sidecar_path = artifact_dir / "metadata.json.sha256"
    metadata_path = _safe_artifact_path(metadata_path, raw_root, "metadata")
    sidecar_path = _safe_artifact_path(sidecar_path, raw_root, "sidecar")
    if (
        payload_path.parent != metadata_path.parent
        or payload_path.parent != sidecar_path.parent
    ):
        raise ValueError(
            "AIFS payload, metadata, and sidecar must share one directory"
        )
    digest_from_path = payload_path.parent.name
    payload = _required_file(payload_path, "payload")
    metadata_bytes = _required_file(metadata_path, "metadata")
    sidecar = _required_file(sidecar_path, "metadata checksum sidecar")
    payload_digest = _sha256(payload)
    metadata_digest = _sha256(metadata_bytes)
    if payload_digest != digest_from_path:
        raise ValueError(
            "AIFS payload integrity hash does not match "
            "content-addressed directory"
        )
    if sidecar != f"{metadata_digest}\n".encode("ascii"):
        raise ValueError("AIFS metadata checksum sidecar mismatch")
    metadata = _canonical_metadata(metadata_bytes)
    if retrieval is None:
        raise ValueError("AIFS decoded validation requires retrieval context")
    decoded_messages = parse_grib_bytes(payload)
    validate_decoded_inventory(decoded_messages)
    _validate_decoded_binding(
        decoded_messages,
        retrieval,
        metadata,
        _metadata_datetime(metadata, "cycle"),
        _metadata_datetime(metadata, "valid_time"),
    )
    _validate_metadata_identity(metadata, payload, payload_digest)
    cycle = _metadata_datetime(metadata, "cycle")
    valid_time = _metadata_datetime(metadata, "valid_time")
    retrieved_at = _metadata_datetime(metadata, "retrieved_at")
    lead_seconds = _required_integer(metadata, "lead_hours") * 3600
    expected = {
        "source": SOURCE_ID,
        "model": MODEL,
        "provider_model": "aifs-single",
        "aoi_id": AOI_ID,
        "aoi_version": AOI_VERSION,
        "aoi_scope_id": AOI_SCOPE_ID,
        "sha256": payload_digest,
        "size_bytes": len(payload),
        "cycle": cycle.isoformat(),
        "lead_hours": _required_integer(metadata, "lead_hours"),
        "url": _required_string(metadata, "url"),
        "index_url": _required_string(metadata, "index_url"),
        "parameters": metadata.get("parameters"),
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"AIFS connector metadata {key} mismatch")
    if valid_time != cycle + timedelta(seconds=lead_seconds):
        raise ValueError("AIFS metadata valid time mismatch")
    return AifsRawRetentionMetadata(
        dataset=_required_string(metadata, "dataset"),
        object_reference=str(payload_path),
        sha256=payload_digest,
        retrieved_at=retrieved_at,
        data_format=_required_string(metadata, "format"),
        size_bytes=len(payload),
        source_url=_required_string(metadata, "url"),
        forecast_cycle=cycle,
        forecast_lead_seconds=lead_seconds,
        valid_time=valid_time,
        metadata_sha256=metadata_digest,
        sidecar_sha256=_sha256(sidecar),
        aoi_id=_required_string(metadata, "aoi_id"),
        aoi_version=_required_string(metadata, "aoi_version"),
        aoi_scope_id=_required_string(metadata, "aoi_scope_id"),
        decoded_parameters=tuple(
            message.parameter for message in decoded_messages
        ),
        decoded_process_identifier=(
            decoded_messages[0].generating_process_identifier
        ),
        decoded_level_bindings=tuple(
            _decoded_level_binding(message) for message in decoded_messages
        ),
    )


def _approved_raw_root() -> Path:
    """Return the existing absolute root authorized for retained artifacts."""
    configured = os.environ.get(RAW_ROOT_ENVIRONMENT_VARIABLE)
    if not configured:
        raise ValueError(f"{RAW_ROOT_ENVIRONMENT_VARIABLE} must be configured")
    root = Path(configured)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("AIFS approved raw root must be an absolute directory")
    return root.resolve()


def _safe_artifact_path(path: Path, raw_root: Path, label: str) -> Path:
    """Require a regular, non-symlink file beneath the approved root."""
    resolved = path.resolve()
    if not resolved.is_relative_to(raw_root):
        raise ValueError(f"AIFS {label} escapes approved raw root")
    if resolved.parent.parent == raw_root:
        raise ValueError(
            "AIFS artifact must be beneath a source/hash directory"
        )
    if resolved.parent.is_symlink() or not resolved.parent.is_dir():
        raise ValueError(
            "AIFS artifact directory must be regular and non-symlink"
        )
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"AIFS {label} must be a regular non-symlink file")
    if len(resolved.parent.name) != 64 or any(
        character not in "0123456789abcdef"
        for character in resolved.parent.name
    ):
        raise ValueError("AIFS artifact directory must be a SHA-256 digest")
    return resolved


def _validate_metadata_identity(
    metadata: dict[str, object], payload: bytes, payload_digest: str
) -> None:
    """Validate immutable provider identity, AOI, ranges, and inventory."""
    expected = {
        "provider": "ECMWF",
        "aifs_version": "2",
        "format": "GRIB2",
        "source": SOURCE_ID,
        "model": MODEL,
        "sha256": payload_digest,
        "size_bytes": len(payload),
        "aoi_id": AOI_ID,
        "aoi_version": AOI_VERSION,
        "aoi_scope_id": AOI_SCOPE_ID,
        "requested_coordinate": [EVEREST_LATITUDE, EVEREST_LONGITUDE],
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"AIFS metadata {key} mismatch")
    if metadata.get("dataset") not in {
        "AIFS Single",
        "AIFS Single Open Data 0.25 degree",
    }:
        raise ValueError("AIFS metadata dataset mismatch")
    parameters = metadata.get("parameters")
    ranges = metadata.get("ranges")
    if not isinstance(parameters, list) or not isinstance(ranges, list):
        raise ValueError("AIFS metadata inventory is missing")
    if len(parameters) != len(ranges) or len(set(parameters)) != len(
        parameters
    ):
        raise ValueError("AIFS metadata inventory is inconsistent")
    if not all(
        isinstance(item.get("offset"), int)
        and isinstance(item.get("length"), int)
        and item["offset"] >= 0
        and item["length"] > 0
        for item in ranges
        if isinstance(item, dict)
    ):
        raise ValueError("AIFS metadata range inventory is malformed")
    offsets = [item["offset"] for item in ranges]
    if len(set(offsets)) != len(offsets):
        raise ValueError("AIFS metadata ranges contain duplicate offsets")
    if sum(item["length"] for item in ranges) != len(payload):
        raise ValueError("AIFS metadata ranges do not cover payload")
    for parameter, item in zip(parameters, ranges):
        if not isinstance(parameter, str) or not isinstance(item, dict):
            raise ValueError("AIFS metadata range inventory is malformed")
        if item.get("parameter") != parameter or item.get("offset", -1) < 0:
            raise ValueError("AIFS metadata range inventory is inconsistent")


class AifsIngestionAdapter:  # pylint: disable=too-few-public-methods
    """Validate AIFS identity before invoking the owner-neutral port."""

    def __init__(self, ingestion_port: IngestionPort) -> None:
        self._ingestion_port = ingestion_port

    def ingest(
        self,
        raw: AifsRawRetentionMetadata,
        records: Sequence[AifsCanonicalRecord],
    ) -> UUID:
        """Project verified scalars and canonical records without conflation."""
        _validate_raw(raw)
        canonical = tuple(_canonical(raw, record) for record in records)
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
            metadata={
                "provider_source_id": raw.source_id,
                "provider_name": "ECMWF",
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
                "provider_decoded_inventory": ",".join(raw.decoded_parameters),
                "provider_generating_process_identifier": (
                    raw.decoded_process_identifier
                ),
                "provider_decoded_level_bindings": ",".join(
                    raw.decoded_level_bindings
                ),
                "provider_aoi_id": raw.aoi_id,
                "provider_aoi_version": raw.aoi_version,
                "provider_aoi_scope_id": raw.aoi_scope_id,
                "provenance_reference": raw.object_reference,
            },
        )
        return self._ingestion_port.ingest(descriptor, canonical)


def compose_aifs_ingestion_adapter(
    ingestion_port: IngestionPort,
) -> AifsIngestionAdapter:
    """Return the sole AIFS-to-backend composition entry point."""
    return AifsIngestionAdapter(ingestion_port)


def _validate_raw(raw: AifsRawRetentionMetadata) -> None:
    """Reject raw identity or forecast-time mismatch before port invocation."""
    if raw.source_id != SOURCE_ID or raw.model != MODEL:
        raise ValueError("AIFS raw source or model identity mismatch")
    if raw.valid_time != raw.forecast_cycle + timedelta(
        seconds=raw.forecast_lead_seconds
    ):
        raise ValueError("AIFS raw valid time does not match cycle and lead")
    if raw.decoded_parameters != EXPECTED_PARAMETERS:
        raise ValueError("AIFS raw decoded inventory mismatch")
    if raw.decoded_process_identifier != EXPECTED_PROCESS_IDENTIFIER:
        raise ValueError("AIFS raw decoded process identifier mismatch")
    expected_levels = (
        "z:surface:0",
        "10u:heightAboveGround:10",
        "10v:heightAboveGround:10",
        "2t:heightAboveGround:2",
        "tp:surface:0",
    )
    if raw.decoded_level_bindings != expected_levels:
        raise ValueError("AIFS raw decoded level binding mismatch")


def _validate_decoded_binding(
    messages: tuple[ParsedMessage, ...],
    retrieval: RawRetrieval,
    metadata: dict[str, object],
    cycle: datetime,
    valid_time: datetime,
) -> None:
    """Bind decoded run and inventory facts to retained metadata."""
    decoded_parameters = tuple(message.parameter for message in messages)
    if decoded_parameters != tuple(retrieval.parameters):
        raise ValueError("AIFS decoded inventory does not match retrieval")
    if list(decoded_parameters) != metadata.get("parameters"):
        raise ValueError("AIFS decoded inventory does not match metadata")
    expected_lead = retrieval.lead_hours
    for message in messages:
        if message.cycle != cycle or message.cycle != retrieval.cycle:
            raise ValueError("AIFS decoded cycle does not match metadata")
        if message.lead_hours != expected_lead:
            raise ValueError("AIFS decoded lead does not match metadata")
        if message.valid_time != valid_time:
            raise ValueError("AIFS decoded valid time does not match metadata")
        if message.generating_process_identifier != EXPECTED_PROCESS_IDENTIFIER:
            raise ValueError("AIFS decoded process does not match metadata")


def _decoded_level_binding(message: ParsedMessage) -> str:
    """Serialize one validated decoded level as a stable scalar fact."""
    level = message.level
    if level is None:
        raise ValueError("AIFS decoded level is missing")
    level_text = f"{level:g}"
    return f"{message.parameter}:{message.level_type}:{level_text}"


def _canonical(
    raw: AifsRawRetentionMetadata, record: AifsCanonicalRecord
) -> CanonicalRecordInput:
    """Map canonical values losslessly after complete provenance validation."""
    weather = record.weather
    if not record.spatial_key:
        raise ValueError("AIFS canonical record requires a spatial key")
    if (
        weather.record_type is not RecordType.FORECAST
        or weather.forecast is None
    ):
        raise ValueError("AIFS ingestion accepts identified forecasts only")
    if weather.source != SOURCE_ID or weather.model != MODEL:
        raise ValueError("AIFS canonical source or model identity mismatch")
    if weather.forecast.cycle != raw.forecast_cycle:
        raise ValueError("AIFS canonical cycle mismatch")
    lead_seconds = weather.forecast.lead_time.total_seconds()
    if int(lead_seconds) != lead_seconds or int(lead_seconds) != (
        raw.forecast_lead_seconds
    ):
        raise ValueError("AIFS canonical lead mismatch")
    if weather.timestamp != raw.valid_time:
        raise ValueError("AIFS canonical valid time mismatch")
    return CanonicalRecordInput(
        record_type=weather.record_type.value,
        timestamp=weather.timestamp,
        latitude=weather.latitude,
        longitude=weather.longitude,
        altitude=weather.altitude,
        spatial_key=record.spatial_key,
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
        forecast_cycle=weather.forecast.cycle,
        forecast_lead_seconds=int(lead_seconds),
        route_profile=record.route_profile,
    )


def _required_file(path: Path, label: str) -> bytes:
    """Read one exact connector artifact or fail closed."""
    try:
        if not path.is_file():
            raise ValueError(f"AIFS connector {label} is missing")
        return path.read_bytes()
    except OSError as error:
        raise ValueError(f"AIFS connector {label} cannot be read") from error


def _sha256(value: bytes) -> str:
    """Return SHA-256 for exact retained bytes."""
    return hashlib.sha256(value).hexdigest()


def _canonical_metadata(encoded: bytes) -> dict[str, object]:
    """Decode only canonical deterministic JSON object metadata."""
    try:
        value = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("AIFS metadata is not UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("AIFS metadata must be an object")
    canonical = (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")
    if canonical != encoded:
        raise ValueError("AIFS metadata is not canonical JSON")
    return value


def _required_string(metadata: dict[str, object], key: str) -> str:
    """Return one required nonempty string fact."""
    value = metadata.get(key)
    # Exact types prevent behavior-bearing subclasses crossing this boundary.
    if value.__class__ is not str or not value:
        raise ValueError(f"AIFS metadata requires string {key}")
    return value


def _required_integer(metadata: dict[str, object], key: str) -> int:
    """Return one required nonnegative integer fact."""
    value = metadata.get(key)
    if value.__class__ is not int or value < 0:
        raise ValueError(f"AIFS metadata requires integer {key}")
    return value


def _metadata_datetime(metadata: dict[str, object], key: str) -> datetime:
    """Parse one timezone-aware UTC ISO-8601 metadata fact."""
    try:
        value = datetime.fromisoformat(_required_string(metadata, key))
    except ValueError as error:
        raise ValueError(f"AIFS metadata {key} is not ISO-8601") from error
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"AIFS metadata {key} must be UTC")
    return value
