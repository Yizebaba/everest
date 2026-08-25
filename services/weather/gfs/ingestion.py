"""Provider-boundary adapter for passing verified GFS data to the backend.

This module deliberately depends only on the backend's provider-neutral command
contracts.  Backend composition supplies the ingestion service (or a compatible
port); this adapter never opens a database session or imports web, ORM, HTTP, or
GRIB decoding implementations.
"""

# Frozen provider-boundary DTOs intentionally expose one public data shape.
# pylint: disable=too-few-public-methods,duplicate-code

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Sequence
from uuid import UUID

from weather_ingestion_contract import (
    CanonicalRecordInput,
    IngestionPort,
    RawArtifactDescriptor,
)
from services.weather.contract import RecordType, WeatherRecord


GFS_SOURCE_ID = "noaa-gfs"
GFS_MODEL = "GFS"


@dataclass(frozen=True)
class GfsRawRetentionMetadata:  # pylint: disable=too-many-instance-attributes
    """Verified immutable retention facts for one GFS source artifact.

    ``raw_metadata`` is passed unchanged into the neutral descriptor so original
    provider metadata remains available for raw-artifact audit.
    """

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
    source_id: str = GFS_SOURCE_ID
    model: str = GFS_MODEL


@dataclass(frozen=True)
class GfsCanonicalRecord:
    """Normalized GFS record with its provider grid identity."""

    weather: WeatherRecord
    spatial_key: str
    route_profile: str | None = None


class GfsIngestionAdapter:  # pylint: disable=too-few-public-methods
    """Map verified GFS retention data to backend-neutral ingestion commands."""

    def __init__(self, ingestion_port: IngestionPort) -> None:
        """Bind the adapter to an injected backend-owned ingestion port."""

        self._ingestion_port = ingestion_port

    def ingest(
        self,
        raw: GfsRawRetentionMetadata,
        records: Sequence[GfsCanonicalRecord],
    ) -> UUID:
        """Validate provenance, map losslessly, and invoke the port once."""

        descriptor = self._descriptor(raw)
        canonical_records = tuple(
            self._canonical_record(raw, record) for record in records
        )
        return self._ingestion_port.ingest(descriptor, canonical_records)

    @staticmethod
    def _descriptor(raw: GfsRawRetentionMetadata) -> RawArtifactDescriptor:
        """Create the provider-neutral raw descriptor after GFS checks."""

        _validate_raw_provenance(raw)
        return RawArtifactDescriptor(
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
            metadata=raw.raw_metadata,
        )

    @staticmethod
    def _canonical_record(
        raw: GfsRawRetentionMetadata,
        gfs_record: GfsCanonicalRecord,
    ) -> CanonicalRecordInput:
        """Map every canonical value without coercing nulls or QC flags."""

        weather = gfs_record.weather
        _validate_record_provenance(raw, gfs_record)
        forecast = weather.forecast
        return CanonicalRecordInput(
            record_type=weather.record_type.value,
            timestamp=weather.timestamp,
            latitude=weather.latitude,
            longitude=weather.longitude,
            altitude=weather.altitude,
            spatial_key=gfs_record.spatial_key,
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
            forecast_cycle=forecast.cycle if forecast is not None else None,
            forecast_lead_seconds=(
                int(forecast.lead_time.total_seconds())
                if forecast is not None
                else None
            ),
            route_profile=gfs_record.route_profile,
        )


def compose_gfs_ingestion_adapter(
    ingestion_port: IngestionPort,
) -> GfsIngestionAdapter:
    """Return the exact backend composition entry point for the GFS adapter."""

    return GfsIngestionAdapter(ingestion_port)


def _validate_raw_provenance(raw: GfsRawRetentionMetadata) -> None:
    """Reject retention metadata that does not identify one coherent GFS run."""

    if raw.source_id != GFS_SOURCE_ID or raw.model != GFS_MODEL:
        raise ValueError("GFS raw metadata has inconsistent source or model")
    if raw.valid_time != raw.forecast_cycle + timedelta(
        seconds=_seconds(raw.forecast_lead_seconds)
    ):
        raise ValueError(
            "GFS raw metadata valid time does not match cycle and lead"
        )
    if raw.raw_metadata.get("source") != raw.source_id:
        raise ValueError("GFS raw metadata source does not match source ID")
    if raw.raw_metadata.get("model") != raw.model:
        raise ValueError("GFS raw metadata model does not match model")


def _validate_record_provenance(
    raw: GfsRawRetentionMetadata,
    gfs_record: GfsCanonicalRecord,
) -> None:
    """Reject provenance mismatches before persistence."""

    weather = gfs_record.weather
    if not gfs_record.spatial_key:
        raise ValueError("GFS canonical record requires a spatial key")
    if weather.record_type is not RecordType.FORECAST:
        raise ValueError("GFS ingestion accepts forecast records only")
    if weather.source != raw.source_id or weather.model != raw.model:
        raise ValueError(
            "GFS canonical record source or model does not match raw"
        )
    if weather.forecast is None:
        raise ValueError("GFS forecast record requires a forecast identity")
    if weather.forecast.cycle != raw.forecast_cycle:
        raise ValueError("GFS canonical record cycle does not match raw")
    if (
        _seconds(weather.forecast.lead_time.total_seconds())
        != raw.forecast_lead_seconds
    ):
        raise ValueError("GFS canonical record lead does not match raw")
    if weather.timestamp != raw.valid_time:
        raise ValueError("GFS canonical record valid time does not match raw")


def _seconds(value: float | int) -> int:
    """Accept only an exact integral number of seconds for forecast identity."""

    if int(value) != value:
        raise ValueError(
            "GFS forecast lead must be an integral number of seconds"
        )
    return int(value)
