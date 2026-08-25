"""Deterministic unit tests for the provider-to-backend GFS adapter."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

from weather_ingestion_contract import (
    CanonicalRecordInput,
    RawArtifactDescriptor,
)
from services.weather.contract import (
    ForecastIdentity,
    RecordType,
    WeatherRecord,
)
from services.weather.gfs.ingestion import (
    GfsCanonicalRecord,
    GfsRawRetentionMetadata,
    compose_gfs_ingestion_adapter,
)


class FakeIngestionPort:  # pylint: disable=too-few-public-methods
    """Capture neutral commands without importing backend implementations."""

    def __init__(self) -> None:
        """Create an empty command capture."""

        self.calls: list[
            tuple[RawArtifactDescriptor, tuple[CanonicalRecordInput, ...]]
        ] = []

    def ingest(
        self,
        artifact: RawArtifactDescriptor,
        records: tuple[CanonicalRecordInput, ...],
    ) -> UUID:
        """Capture one command and return a deterministic artifact ID."""

        self.calls.append((artifact, records))
        return UUID("12345678-1234-5678-1234-567812345678")


def _raw() -> GfsRawRetentionMetadata:
    """Return one coherent, verified GFS raw artifact fixture."""

    cycle = datetime(2026, 8, 20, tzinfo=timezone.utc)
    return GfsRawRetentionMetadata(
        dataset="GFS pgrb2.0p25",
        object_reference="raw/noaa-gfs/aabb.grib2",
        sha256="a" * 64,
        retrieved_at=datetime(2026, 8, 21, tzinfo=timezone.utc),
        data_format="GRIB2",
        size_bytes=2937483,
        source_url="https://nomads.ncep.noaa.gov/example.grib2",
        forecast_cycle=cycle,
        forecast_lead_seconds=10800,
        valid_time=cycle + timedelta(hours=3),
        raw_metadata={"source": "noaa-gfs", "model": "GFS", "kept": None},
    )


def _record() -> GfsCanonicalRecord:
    """Return a normalized record with QC and nullable fields for forwarding."""

    raw = _raw()
    return GfsCanonicalRecord(
        weather=WeatherRecord(
            record_type=RecordType.FORECAST,
            timestamp=raw.valid_time,
            latitude=27.9881,
            longitude=86.9250,
            altitude=5917.819375,
            wind_speed=2.0,
            wind_direction=235.0,
            temperature=-3.2,
            precipitation=None,
            visibility=None,
            source="noaa-gfs",
            model="GFS",
            forecast=ForecastIdentity(raw.forecast_cycle, timedelta(hours=3)),
            quality_flags=frozenset({"missing_value", "stale"}),
        ),
        spatial_key="gfs:0p25:28.0:87.0",
    )


def test_adapter_maps_descriptor_and_canonical_record_losslessly() -> None:
    """The neutral command preserves artifact, identity, null, and weather data."""

    port = FakeIngestionPort()
    result = compose_gfs_ingestion_adapter(port).ingest(_raw(), (_record(),))
    descriptor, records = port.calls[0]
    record = records[0]
    assert result == UUID("12345678-1234-5678-1234-567812345678")
    assert descriptor.dataset == "GFS pgrb2.0p25"
    assert descriptor.object_reference == "raw/noaa-gfs/aabb.grib2"
    assert descriptor.sha256 == "a" * 64
    assert descriptor.source_url == "https://nomads.ncep.noaa.gov/example.grib2"
    assert descriptor.forecast_cycle == _raw().forecast_cycle
    assert descriptor.forecast_lead_seconds == 10800
    assert descriptor.valid_time == _raw().valid_time
    assert descriptor.metadata == {
        "source": "noaa-gfs",
        "model": "GFS",
        "kept": None,
    }
    assert record.spatial_key == "gfs:0p25:28.0:87.0"
    assert record.precipitation is None
    assert record.visibility is None
    assert record.forecast_cycle == _raw().forecast_cycle
    assert record.forecast_lead_seconds == 10800


def test_adapter_forwards_qc_flags_exactly() -> None:
    """QC flags are not supplemented, sorted, dropped, or otherwise rewritten."""

    port = FakeIngestionPort()
    weather = _record().weather
    expected_flags = tuple(weather.quality_flags)
    compose_gfs_ingestion_adapter(port).ingest(_raw(), (_record(),))
    assert port.calls[0][1][0].quality_flags == expected_flags


def test_adapter_rejects_mismatched_provenance_before_port_call() -> None:
    """A cycle mismatch fails before the backend can retain the raw artifact."""

    port = FakeIngestionPort()
    inconsistent = GfsCanonicalRecord(
        weather=WeatherRecord(
            **{
                **_record().weather.__dict__,
                "forecast": ForecastIdentity(
                    _raw().forecast_cycle + timedelta(hours=6),
                    timedelta(hours=3),
                ),
            }
        ),
        spatial_key="gfs:0p25:28.0:87.0",
    )
    with pytest.raises(ValueError, match="cycle"):
        compose_gfs_ingestion_adapter(port).ingest(_raw(), (inconsistent,))
    assert not port.calls


def test_adapter_uses_owner_neutral_contract_only() -> None:
    """The provider adapter must not depend on backend application modules."""

    source = Path(__file__).parents[1].joinpath("gfs", "ingestion.py")
    text = source.read_text(encoding="utf-8")
    assert "everest_api" not in text
    assert "apps.api" not in text
    assert "weather_ingestion_contract" in text
