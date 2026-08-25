"""Deterministic tests for the DWD ICON provider-to-backend adapter."""

# Provider-boundary test fixtures intentionally parallel the GFS adapter suite.
# pylint: disable=duplicate-code

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
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
from services.weather.icon import (
    IconCanonicalRecord,
    IconRawRetentionMetadata,
    compose_icon_ingestion_adapter,
    icon_raw_retention_metadata_from_retrieval,
)
from services.weather.icon.connector import RawRetrieval


class FakeIngestionPort:  # pylint: disable=too-few-public-methods
    """Capture neutral backend commands."""

    def __init__(self) -> None:
        """Initialize call capture."""
        self.calls: list[
            tuple[RawArtifactDescriptor, tuple[CanonicalRecordInput, ...]]
        ] = []

    def ingest(
        self,
        artifact: RawArtifactDescriptor,
        records: tuple[CanonicalRecordInput, ...],
    ) -> UUID:
        """Capture one command without backend behavior."""
        self.calls.append((artifact, records))
        return UUID("12345678-1234-5678-1234-567812345678")


def _raw() -> IconRawRetentionMetadata:
    """Return coherent factual-shaped raw metadata."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    return IconRawRetentionMetadata(
        dataset="ICON global",
        object_reference="raw/dwd-icon/aabb.grib2",
        sha256="a" * 64,
        retrieved_at=cycle,
        data_format="GRIB2",
        size_bytes=12,
        source_url="https://opendata.dwd.de/example.grib2.bz2",
        forecast_cycle=cycle,
        forecast_lead_seconds=10800,
        valid_time=cycle + timedelta(hours=3),
        raw_metadata={
            "source": "dwd-icon",
            "provider": "DWD",
            "model": "ICON",
            "aoi_id": "everest-south-route",
            "aoi_version": "everest-south-route-v1.0",
            "aoi_scope_id": "everest-south-route-v1.0-expanded-2000km",
            "urls": ["must remain in raw sidecar"],
        },
        metadata_sha256="b" * 64,
        sidecar_sha256="c" * 64,
        backend_policy_facts={
            "backend_retention_owner": "Everest Manager",
            "backend_retention_class": "operational_raw",
            "backend_retention_period": "24 months from acquisition",
            "backend_disposition_state": "retained",
            "backend_hold_state": "none",
        },
    )


def _record() -> IconCanonicalRecord:
    """Return a normalized native-grid forecast fixture."""
    raw = _raw()
    return IconCanonicalRecord(
        WeatherRecord(
            record_type=RecordType.FORECAST,
            timestamp=raw.valid_time,
            latitude=27.99,
            longitude=86.93,
            altitude=6012.0,
            wind_speed=2.0,
            wind_direction=180.0,
            temperature=-5.0,
            precipitation=None,
            visibility=None,
            source="dwd-icon",
            model="ICON",
            forecast=ForecastIdentity(raw.forecast_cycle, timedelta(hours=3)),
            quality_flags=frozenset({"missing_value"}),
        ),
        spatial_key="icon:a27b8de618c411e4820ab5b098c6a5c0:818403",
    )


def test_adapter_maps_losslessly_to_neutral_contract() -> None:
    """Preserve raw/grid identity, nullable fields, and QC."""
    raw = _raw()
    port = FakeIngestionPort()
    result = compose_icon_ingestion_adapter(port).ingest(raw, (_record(),))
    descriptor, records = port.calls[0]
    assert result == UUID("12345678-1234-5678-1234-567812345678")
    assert descriptor.source_id == "dwd-icon"
    assert descriptor.metadata["provider_name"] == "DWD"
    assert descriptor.metadata["provider_payload_sha256"] == "a" * 64
    assert descriptor.metadata["provider_aoi_scope_id"] == (
        "everest-south-route-v1.0-expanded-2000km"
    )
    assert descriptor.metadata["backend_hold_state"] == "none"
    assert descriptor.metadata["provenance_reference"] == raw.object_reference
    assert "urls" not in descriptor.metadata
    assert all(
        not isinstance(value, (dict, list))
        for value in descriptor.metadata.values()
    )
    assert records[0].spatial_key == (
        "icon:a27b8de618c411e4820ab5b098c6a5c0:818403"
    )
    assert records[0].precipitation is None
    assert records[0].quality_flags == ("missing_value",)


def test_adapter_does_not_forward_nested_sidecar_unchanged() -> None:
    """Provider arrays remain in retained sidecar, not the neutral DTO."""
    raw = _raw()
    raw.raw_metadata["provider_object"] = {"vendor": "DWD"}
    port = FakeIngestionPort()
    compose_icon_ingestion_adapter(port).ingest(raw, (_record(),))
    assert "provider_object" not in port.calls[0][0].metadata


def _retrieval(tmp_path: Path) -> RawRetrieval:
    """Create filesystem output with the exact connector return shape."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    valid = cycle + timedelta(hours=3)
    payload = b"GRIB connector-shaped payload"
    payload_path = tmp_path / "icon_2026082100_003.grib2"
    metadata_path = tmp_path / "metadata.json"
    payload_path.write_bytes(payload)
    payload_sha256 = hashlib.sha256(payload).hexdigest()
    url = "https://opendata.dwd.de/example.grib2.bz2"
    metadata = {
        "source": "dwd-icon",
        "provider": "DWD",
        "dataset": "ICON global",
        "model": "ICON",
        "cycle": cycle.isoformat(),
        "lead_hours": 3,
        "valid_time": valid.isoformat(),
        "valid_time_epoch": int(valid.timestamp()),
        "urls": [url],
        "format": "GRIB2",
        "fields": ["T_2M"],
        "aoi_id": "everest-south-route",
        "aoi_version": "everest-south-route-v1.0",
        "aoi_scope_id": "everest-south-route-v1.0-expanded-2000km",
        "size_bytes": len(payload),
        "sha256": payload_sha256,
        "retrieved_at": "2026-08-21T01:02:03+00:00",
        "provider_provenance": {
            "directory_listing": {"advertised": True},
            "requested_fields": ["T_2M"],
        },
    }
    encoded = (
        json.dumps(
            metadata,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    metadata_path.write_bytes(encoded)
    metadata_path.with_name("metadata.json.sha256").write_bytes(
        (hashlib.sha256(encoded).hexdigest() + "\n").encode("ascii")
    )
    return RawRetrieval(
        payload_path=payload_path,
        metadata_path=metadata_path,
        url=url,
        sha256=payload_sha256,
        size_bytes=len(payload),
        cycle=cycle,
        lead_hours=3,
        fields=("T_2M",),
    )


def _record_for(raw: IconRawRetentionMetadata) -> IconCanonicalRecord:
    """Return a canonical record coherent with converted connector output."""
    original = _record()
    return replace(
        original,
        weather=replace(
            original.weather,
            timestamp=raw.valid_time,
            forecast=ForecastIdentity(
                raw.forecast_cycle,
                timedelta(seconds=raw.forecast_lead_seconds),
            ),
        ),
    )


def test_connector_output_conversion_verifies_and_projects_scalars(
    tmp_path: Path,
) -> None:
    """Convert RawRetrieval-shaped files through the authoritative path."""
    retrieval = _retrieval(tmp_path)
    raw = icon_raw_retention_metadata_from_retrieval(
        retrieval,
        backend_policy_facts={"backend_hold_state": "none"},
    )
    assert raw.sha256 == retrieval.sha256
    assert (
        raw.metadata_sha256
        == hashlib.sha256(retrieval.metadata_path.read_bytes()).hexdigest()
    )
    sidecar = retrieval.metadata_path.with_name("metadata.json.sha256")
    assert (
        raw.sidecar_sha256 == hashlib.sha256(sidecar.read_bytes()).hexdigest()
    )
    assert raw.valid_time == datetime(2026, 8, 21, 3, tzinfo=timezone.utc)
    assert raw.raw_metadata["provider_provenance"]["directory_listing"] == {
        "advertised": True
    }
    port = FakeIngestionPort()
    compose_icon_ingestion_adapter(port).ingest(raw, (_record_for(raw),))
    projected = port.calls[0][0].metadata
    assert projected["provider_aoi_scope_id"] == (
        "everest-south-route-v1.0-expanded-2000km"
    )
    assert projected["provider_metadata_sha256"] == raw.metadata_sha256
    assert projected["provider_sidecar_sha256"] == raw.sidecar_sha256
    assert projected["backend_hold_state"] == "none"
    assert "provider_provenance" not in projected


def test_connector_output_conversion_does_not_require_backend_policy(
    tmp_path: Path,
) -> None:
    """Provider output converts without fabricating backend retention facts."""
    raw = icon_raw_retention_metadata_from_retrieval(_retrieval(tmp_path))
    port = FakeIngestionPort()
    compose_icon_ingestion_adapter(port).ingest(raw, (_record_for(raw),))
    projected = port.calls[0][0].metadata
    assert not any(key.startswith("backend_") for key in projected)
    assert "hold_state" not in projected


def test_connector_output_conversion_reads_historical_epoch_without_rewrite(
    tmp_path: Path,
) -> None:
    """Immutable old sidecars remain readable while current output stays ISO."""
    retrieval = _retrieval(tmp_path)
    metadata = json.loads(retrieval.metadata_path.read_text(encoding="utf-8"))
    epoch = metadata.pop("valid_time_epoch")
    metadata["valid_time"] = float(epoch)
    encoded = (
        json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    retrieval.metadata_path.write_bytes(encoded)
    retrieval.metadata_path.with_name("metadata.json.sha256").write_bytes(
        (hashlib.sha256(encoded).hexdigest() + "\n").encode("ascii")
    )
    raw = icon_raw_retention_metadata_from_retrieval(retrieval)
    assert raw.valid_time == datetime(2026, 8, 21, 3, tzinfo=timezone.utc)
    assert isinstance(raw.raw_metadata["valid_time"], float)


def test_connector_output_conversion_rejects_provider_policy_vocabulary(
    tmp_path: Path,
) -> None:
    """Only explicitly backend-prefixed policy keys may cross composition."""
    with pytest.raises(ValueError, match="backend-prefixed"):
        icon_raw_retention_metadata_from_retrieval(
            _retrieval(tmp_path),
            backend_policy_facts={"hold_state": "not_held"},
        )


@pytest.mark.parametrize("missing", ("payload", "metadata", "sidecar"))
def test_connector_output_conversion_rejects_missing_artifact(
    tmp_path: Path, missing: str
) -> None:
    """Conversion fails closed when any connector-retained file is absent."""
    retrieval = _retrieval(tmp_path)
    paths = {
        "payload": retrieval.payload_path,
        "metadata": retrieval.metadata_path,
        "sidecar": retrieval.metadata_path.with_name("metadata.json.sha256"),
    }
    paths[missing].unlink()
    with pytest.raises(ValueError, match="missing"):
        icon_raw_retention_metadata_from_retrieval(retrieval)


@pytest.mark.parametrize("target", ("payload", "metadata", "sidecar"))
def test_connector_output_conversion_rejects_hash_mismatch(
    tmp_path: Path, target: str
) -> None:
    """Integrity-check payload, metadata declaration, and sidecar bytes."""
    retrieval = _retrieval(tmp_path)
    if target == "payload":
        retrieval.payload_path.write_bytes(b"GRIB changed")
    elif target == "metadata":
        retrieval.metadata_path.write_bytes(b'{"changed":true}\n')
    else:
        retrieval.metadata_path.with_name("metadata.json.sha256").write_text(
            "0" * 64 + "\n", encoding="ascii"
        )
    with pytest.raises(ValueError, match="checksum|size"):
        icon_raw_retention_metadata_from_retrieval(retrieval)


def test_connector_output_conversion_rejects_noncanonical_sidecar(
    tmp_path: Path,
) -> None:
    """Even a correct declaration fails when sidecar bytes were modified."""
    retrieval = _retrieval(tmp_path)
    sidecar = retrieval.metadata_path.with_name("metadata.json.sha256")
    sidecar.write_bytes(sidecar.read_bytes().rstrip(b"\n") + b" \n")
    with pytest.raises(ValueError, match="sidecar is not canonical"):
        icon_raw_retention_metadata_from_retrieval(retrieval)


def test_adapter_rejects_unsupported_projected_value_before_port() -> None:
    """A required projected object is rejected before backend invocation."""
    raw = _raw()
    raw.raw_metadata["aoi_id"] = {"id": "everest-south-route"}
    port = FakeIngestionPort()
    with pytest.raises(TypeError, match="aoi_id"):
        compose_icon_ingestion_adapter(port).ingest(raw, (_record(),))
    assert not port.calls


def test_adapter_rejects_provenance_before_backend_retention() -> None:
    """Reject cycle mismatch before a descriptor reaches the backend port."""
    port = FakeIngestionPort()
    invalid = IconCanonicalRecord(
        WeatherRecord(
            **{
                **_record().weather.__dict__,
                "forecast": ForecastIdentity(
                    _raw().forecast_cycle + timedelta(hours=6),
                    timedelta(hours=3),
                ),
            }
        ),
        spatial_key="icon:a27b8de618c411e4820ab5b098c6a5c0:818403",
    )
    with pytest.raises(ValueError, match="cycle"):
        compose_icon_ingestion_adapter(port).ingest(_raw(), (invalid,))
    assert not port.calls


@pytest.mark.parametrize(
    "mutator",
    [
        lambda raw, record: replace(record.weather, source="other"),
        lambda raw, record: replace(record.weather, model="other"),
        lambda raw, record: replace(
            record.weather, record_type=RecordType.OBSERVATION
        ),
        lambda raw, record: replace(record.weather, forecast=None),
        lambda raw, record: replace(
            record.weather,
            forecast=ForecastIdentity(
                raw.forecast_cycle + timedelta(hours=1),
                timedelta(hours=3),
            ),
        ),
        lambda raw, record: replace(
            record.weather,
            forecast=ForecastIdentity(raw.forecast_cycle, timedelta(hours=1)),
        ),
        lambda raw, record: replace(
            record.weather, timestamp=raw.valid_time + timedelta(hours=1)
        ),
        lambda raw, record: replace(record, spatial_key=""),
    ],
    ids=(
        "source",
        "model",
        "record-type",
        "forecast-identity",
        "cycle",
        "lead",
        "valid-time",
        "native-key",
    ),
)
def test_adapter_rejects_complete_provenance_matrix_before_port(
    mutator,
) -> None:
    """Every provider identity mismatch is rejected before backend retention."""
    raw = _raw()
    original = _record()
    changed = mutator(raw, original)
    if isinstance(changed, WeatherRecord):
        changed = replace(original, weather=changed)
    port = FakeIngestionPort()
    with pytest.raises(ValueError):
        compose_icon_ingestion_adapter(port).ingest(raw, (changed,))
    assert not port.calls


def test_adapter_uses_owner_neutral_contract_only() -> None:
    """The provider adapter must not depend on backend application modules."""

    source = Path(__file__).parents[1].joinpath("icon", "ingestion.py")
    text = source.read_text(encoding="utf-8")
    assert "everest_api" not in text
    assert "apps.api" not in text
    assert "weather_ingestion_contract" in text


def test_conversion_has_one_definition_and_public_package_export() -> None:
    """Concurrent changes cannot split the implementation and public export."""
    icon_directory = Path(__file__).parents[1] / "icon"
    ingestion = (icon_directory / "ingestion.py").read_text(encoding="utf-8")
    package = (icon_directory / "__init__.py").read_text(encoding="utf-8")
    function_name = "icon_raw_retention_metadata_from_retrieval"
    assert ingestion.count(f"def {function_name}(") == 1
    assert package.count(f'"{function_name}"') == 1
    assert function_name in package
