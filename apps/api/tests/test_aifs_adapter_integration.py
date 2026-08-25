"""Offline retained-AIFS to PostgreSQL/API integration tests.

The real-data case never retrieves data. It requires the approved retained
artifact beneath ``EVEREST_RAW_ROOT``, a working native ecCodes runtime, and a
disposable PostgreSQL URL. Missing prerequisites are reported as skips; changed
retained evidence is a test failure, never a skip.
"""

from __future__ import annotations

# SQLAlchemy's dynamic ``func`` namespace is intentionally callable. Tests also
# exercise connector integrity methods to verify the retained sidecar boundary.
# Pytest fixture parameters intentionally match their fixture declaration.
# pylint: disable=not-callable,protected-access,redefined-outer-name

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from services.weather.aifs import (
    AifsCanonicalRecord,
    AifsRawRetentionMetadata,
    aifs_raw_retention_metadata_from_retrieval,
    compose_aifs_ingestion_adapter,
    normalize_messages,
    provider_spatial_key,
    validate_decoded_inventory,
)
from services.weather.aifs.connector import EcmwfAifsConnector, RawRetrieval
from services.weather.aifs.normalizer import nearest_grid_index
from services.weather.aifs.parser import ParsedMessage, parse_grib_bytes

from everest_api.app import create_app
from everest_api.raw_storage import RawStoragePolicy
from everest_api.registry.models import DataSourceRegistryModel
from everest_api.weather.models import (
    RawArtifactAuditEventModel,
    WeatherRawArtifactModel,
    WeatherRecordModel,
)
from everest_api.weather.service import WeatherIngestionService


_RAW_ROOT_ENVIRONMENT_VARIABLE = "EVEREST_RAW_ROOT"
_OBJECT_REFERENCE = (
    "ecmwf-aifs/"
    "46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5/"
    "20260821000000-0h-oper-fc.grib2"
)
_PAYLOAD_SHA256 = (
    "46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5"
)
_METADATA_SHA256 = (
    "86e77f9d36058c40495d3641ff1afce38343c61deb89901cd3435ec702cb9b01"
)
_SIDECAR_SHA256 = (
    "62f264fe043978e39936e0a51e71385e8c95f8916e7bd342bc90d456fa0ee78e"
)
_SOURCE_URL = (
    "https://data.ecmwf.int/forecasts/20260821/00z/aifs-single/0p25/oper/"
    "20260821000000-0h-oper-fc.grib2"
)
_INDEX_URL = _SOURCE_URL.removesuffix(".grib2") + ".index"
_SPATIAL_KEY = "aifs-single:0p25:1440x721:358188"
_EVEREST_LATITUDE = 27.98806
_EVEREST_LONGITUDE = 86.92528
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_RawFixtureWriter = Callable[[str, bytes], tuple[str, int]]


class _NetworkForbiddenSession:  # pylint: disable=too-few-public-methods
    """Fail immediately if this offline test reaches connector transport."""

    @staticmethod
    def get(_url: str, **_kwargs: Any) -> None:
        """Reject every attempted HTTP request."""
        raise AssertionError("offline retained-AIFS test must not use HTTP")


def _sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest of retained bytes."""
    return hashlib.sha256(payload).hexdigest()


def _require_eccodes() -> None:
    """Skip only when the Python binding or native ecCodes runtime is absent."""
    try:
        from eccodes import (  # pylint: disable=import-outside-toplevel
            codes_get_api_version,
        )

        if not codes_get_api_version():
            raise RuntimeError("ecCodes returned no API version")
    except (ImportError, RuntimeError, OSError) as error:
        pytest.skip(
            f"compatible native ecCodes environment is required: {error}"
        )


def _load_retained_aifs() -> tuple[RawStoragePolicy, RawRetrieval, bytes]:
    """Load and integrity-check approved retained connector output offline."""
    configured_root = os.environ.get(_RAW_ROOT_ENVIRONMENT_VARIABLE)
    if not configured_root:
        pytest.skip(
            f"{_RAW_ROOT_ENVIRONMENT_VARIABLE} is required for retained AIFS"
        )
    raw_root = Path(configured_root)
    if not raw_root.is_absolute() or not raw_root.is_dir():
        pytest.skip(
            f"{_RAW_ROOT_ENVIRONMENT_VARIABLE} must be an available absolute directory"
        )
    policy = RawStoragePolicy(raw_root, _WORKSPACE_ROOT)
    payload_path = policy.resolve_object_reference(_OBJECT_REFERENCE)
    metadata_path = payload_path.with_name("metadata.json")
    sidecar_path = payload_path.with_name("metadata.json.sha256")
    missing = [
        path.name
        for path in (payload_path, metadata_path, sidecar_path)
        if not path.is_file()
    ]
    if missing:
        pytest.skip(f"approved retained AIFS artifacts are absent: {missing}")

    payload = payload_path.read_bytes()
    metadata_bytes = metadata_path.read_bytes()
    sidecar_bytes = sidecar_path.read_bytes()
    assert len(payload) == 3_061_386
    assert _sha256(payload) == _PAYLOAD_SHA256
    assert len(metadata_bytes) == 1_116
    assert _sha256(metadata_bytes) == _METADATA_SHA256
    assert sidecar_bytes == f"{_METADATA_SHA256}\n".encode("ascii")
    assert len(sidecar_bytes) == 65
    assert _sha256(sidecar_bytes) == _SIDECAR_SHA256

    metadata = json.loads(metadata_bytes.decode("utf-8"))
    connector = EcmwfAifsConnector(
        session=_NetworkForbiddenSession(),
        environment={_RAW_ROOT_ENVIRONMENT_VARIABLE: str(policy.raw_root)},
        repository_root=_WORKSPACE_ROOT,
    )
    connector._verify_metadata(metadata_path, sidecar_path, metadata)
    mismatched = dict(metadata)
    mismatched["model"] = "IFS"
    with pytest.raises(ValueError, match="provenance mismatch"):
        connector._verify_metadata(metadata_path, sidecar_path, mismatched)

    assert metadata == {
        "aifs_version": "2",
        "aoi_id": "everest-south-route",
        "aoi_scope_id": "everest-south-route-v1.0-default-100km",
        "aoi_version": "everest-south-route-v1.0",
        "cycle": "2026-08-21T00:00:00+00:00",
        "dataset": "AIFS Single Open Data 0.25 degree",
        "format": "GRIB2",
        "index_url": _INDEX_URL,
        "lead_hours": 0,
        "model": "AIFS",
        "parameters": ["z", "10u", "10v", "2t", "tp"],
        "provider": "ECMWF",
        "provider_model": "aifs-single",
        "ranges": [
            {"length": 802_648, "offset": 16_865_591, "parameter": "z"},
            {"length": 821_931, "offset": 89_067_274, "parameter": "10u"},
            {"length": 824_820, "offset": 3_123_280, "parameter": "10v"},
            {"length": 611_763, "offset": 5_780_158, "parameter": "2t"},
            {"length": 224, "offset": 32_006_373, "parameter": "tp"},
        ],
        "requested_coordinate": [_EVEREST_LATITUDE, _EVEREST_LONGITUDE],
        "retrieved_at": "2026-08-21T10:09:58.234370+00:00",
        "sha256": _PAYLOAD_SHA256,
        "size_bytes": 3_061_386,
        "source": "ecmwf-aifs",
        "url": _SOURCE_URL,
        "valid_time": "2026-08-21T00:00:00+00:00",
    }
    retrieval = RawRetrieval(
        payload_path=payload_path,
        metadata_path=metadata_path,
        url=_SOURCE_URL,
        index_url=_INDEX_URL,
        sha256=_PAYLOAD_SHA256,
        size_bytes=3_061_386,
        cycle=datetime(2026, 8, 21, tzinfo=UTC),
        lead_hours=0,
        parameters=("z", "10u", "10v", "2t", "tp"),
    )
    return policy, retrieval, payload


@pytest.fixture
def retained_aifs() -> Iterator[tuple[RawStoragePolicy, RawRetrieval, bytes]]:
    """Provide verified retained output after proving ecCodes availability."""
    _require_eccodes()
    yield _load_retained_aifs()


def _assert_actual_messages(
    messages: tuple[ParsedMessage, ...], record: AifsCanonicalRecord
) -> None:
    """Assert actual decoded messages and exact selected Everest-grid values."""
    assert len(messages) == 5
    assert [message.parameter for message in messages] == [
        "z",
        "10u",
        "10v",
        "2t",
        "tp",
    ]
    assert {message.generating_process_identifier for message in messages} == {
        5
    }
    assert all(message.grid_type == "regular_ll" for message in messages)
    assert all((message.ni, message.nj) == (1440, 721) for message in messages)
    assert all(len(message.values) == 1_038_240 for message in messages)
    index = nearest_grid_index(
        messages[0], _EVEREST_LATITUDE, _EVEREST_LONGITUDE
    )
    assert index == 358_188
    assert messages[0].latitudes[index] == pytest.approx(28.0)
    assert messages[0].longitudes[index] == pytest.approx(87.0)
    values = {message.parameter: message.values[index] for message in messages}
    assert values == pytest.approx(
        {
            "z": 52_429.552001953125,
            "10u": -0.16060638427734375,
            "10v": -0.009899139404296875,
            "2t": 273.6058654785156,
            "tp": 0.0,
        }
    )
    assert record.spatial_key == _SPATIAL_KEY
    assert record.weather.source == "ecmwf-aifs"
    assert record.weather.model == "AIFS"
    assert record.weather.latitude == pytest.approx(28.0)
    assert record.weather.longitude == pytest.approx(87.0)
    assert record.weather.altitude == pytest.approx(5346.3264215561)
    assert record.weather.temperature == pytest.approx(0.45586547851564774)
    assert record.weather.wind_speed == pytest.approx(0.16091116689523915)
    assert record.weather.wind_direction == pytest.approx(86.4729776688032)
    assert record.weather.precipitation == pytest.approx(0.0)
    assert record.weather.visibility is None
    assert record.weather.quality_flags == frozenset({"missing_value"})


def _factory(engine: Engine) -> sessionmaker:
    """Create the backend-owned session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed(session: Session) -> None:
    """Seed configured/unknown lifecycle state in the disposable database."""
    session.add(
        DataSourceRegistryModel(
            source_id="ecmwf-aifs",
            name="AIFS",
            provider="ECMWF",
            category="forecast",
            status="configured",
            access_method="connector",
            commercial_allowed=True,
            credentials_required=False,
            health_status="unknown",
            metadata_version=1,
        )
    )
    session.commit()


@pytest.mark.real_data
# The end-to-end assertion keeps all boundary outputs visible in one test.
# pylint: disable-next=too-many-locals,too-many-statements
def test_retained_aifs_grib_to_postgres_and_bounded_public_forecast(
    retained_aifs: tuple[RawStoragePolicy, RawRetrieval, bytes],
    migrated_postgres_engine: Engine,
) -> None:
    """Parse, normalize, adapt, persist, and query retained AIFS end to end."""
    policy, retrieval, payload = retained_aifs
    messages = parse_grib_bytes(payload)
    weather = normalize_messages(
        messages, _EVEREST_LATITUDE, _EVEREST_LONGITUDE
    )
    canonical = AifsCanonicalRecord(
        weather=weather,
        spatial_key=provider_spatial_key(
            messages[0],
            nearest_grid_index(
                messages[0], _EVEREST_LATITUDE, _EVEREST_LONGITUDE
            ),
        ),
    )
    _assert_actual_messages(messages, canonical)
    raw = aifs_raw_retention_metadata_from_retrieval(retrieval)
    assert raw.sha256 == _PAYLOAD_SHA256
    assert raw.size_bytes == 3_061_386
    assert raw.metadata_sha256 == _METADATA_SHA256
    assert raw.sidecar_sha256 == _SIDECAR_SHA256
    assert raw.model == "AIFS"
    assert raw.source_id == "ecmwf-aifs"

    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed(session)
        source = session.get(DataSourceRegistryModel, "ecmwf-aifs")
        assert source.status == "configured"
        assert source.health_status == "unknown"

    adapter = compose_aifs_ingestion_adapter(
        WeatherIngestionService(factory, policy)
    )
    adapter.ingest(raw, (canonical,))

    with factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(WeatherRawArtifactModel)
            )
            == 1
        )
        assert (
            session.scalar(select(func.count()).select_from(WeatherRecordModel))
            == 1
        )
        assert (
            session.scalar(
                select(func.count()).select_from(RawArtifactAuditEventModel)
            )
            == 1
        )
        artifact = session.scalar(select(WeatherRawArtifactModel))
        record = session.scalar(select(WeatherRecordModel))
        source = session.get(DataSourceRegistryModel, "ecmwf-aifs")
        assert artifact.sha256 == _PAYLOAD_SHA256
        assert artifact.size_bytes == 3_061_386
        assert (
            artifact.metadata_json["provider_payload_sha256"] == _PAYLOAD_SHA256
        )
        assert (
            artifact.metadata_json["provider_payload_size_bytes"] == 3_061_386
        )
        assert (
            artifact.metadata_json["provider_metadata_sha256"]
            == _METADATA_SHA256
        )
        assert (
            artifact.metadata_json["provider_sidecar_sha256"] == _SIDECAR_SHA256
        )
        assert artifact.metadata_json["provider_model"] == "AIFS"
        assert record.source_id == "ecmwf-aifs"
        assert record.model == "AIFS"
        assert record.model != "IFS"
        assert record.spatial_key == _SPATIAL_KEY
        assert record.latitude == pytest.approx(28.0)
        assert record.longitude == pytest.approx(87.0)
        assert record.altitude == pytest.approx(5346.3264215561)
        assert record.temperature == pytest.approx(0.45586547851564774)
        assert record.wind_speed == pytest.approx(0.16091116689523915)
        assert record.wind_direction == pytest.approx(86.4729776688032)
        assert record.precipitation == pytest.approx(0.0)
        assert source.status == "verified"
        assert source.health_status == "healthy"
        assert source.last_success_at == raw.retrieved_at

    query = (
        "/api/weather/forecast?source=ecmwf-aifs&"
        "start=2026-08-21T00%3A00%3A00Z&end=2026-08-21T00%3A00%3A00Z"
    )
    with TestClient(create_app(factory)) as client:
        response = client.get(query)
    assert response.status_code == 200
    response_payload = response.json()
    assert len(response_payload["records"]) == 1
    public_record = response_payload["records"][0]
    assert set(public_record) == {
        "record_type",
        "timestamp",
        "latitude",
        "longitude",
        "altitude",
        "spatial_key",
        "wind_speed",
        "wind_direction",
        "temperature",
        "precipitation",
        "visibility",
        "source",
        "model",
        "forecast_cycle",
        "forecast_lead_time",
        "quality_flags",
    }
    assert public_record["source"] == "ecmwf-aifs"
    assert public_record["model"] == "AIFS"
    assert public_record["model"] != "IFS"
    assert public_record["spatial_key"] == _SPATIAL_KEY
    public_json = json.dumps(response_payload)
    for private_value in (
        str(policy.raw_root),
        _OBJECT_REFERENCE,
        _SOURCE_URL,
        _INDEX_URL,
        "data.ecmwf.int",
        _PAYLOAD_SHA256,
        _METADATA_SHA256,
        _SIDECAR_SHA256,
        "retention_owner",
        "raw_artifact",
        "audit_event",
    ):
        assert private_value not in public_json


def _synthetic_messages(cycle: datetime) -> tuple[ParsedMessage, ...]:
    """Build complete AIFS-shaped messages for backend failure-path tests."""
    facts = (
        ("z", 52_429.552001953125, "m**2 s**-2", "surface", 0.0),
        (
            "10u",
            -0.16060638427734375,
            "m s**-1",
            "heightAboveGround",
            10.0,
        ),
        (
            "10v",
            -0.009899139404296875,
            "m s**-1",
            "heightAboveGround",
            10.0,
        ),
        ("2t", 273.6058654785156, "K", "heightAboveGround", 2.0),
        ("tp", 0.0, "kg m**-2", "surface", 0.0),
    )
    return tuple(
        ParsedMessage(
            parameter=parameter,
            valid_time=cycle,
            cycle=cycle,
            lead_hours=0,
            values=(value,),
            latitudes=(28.0,),
            longitudes=(87.0,),
            units=units,
            level_type=level_type,
            level=level,
            grid_type="regular_ll",
            ni=1,
            nj=1,
            generating_process_identifier=5,
        )
        for parameter, value, units, level_type, level in facts
    )


def _synthetic_raw(
    write_raw_fixture: _RawFixtureWriter,
) -> AifsRawRetentionMetadata:
    """Retain deterministic bytes and return consistent AIFS scalar facts."""
    cycle = datetime(2026, 8, 21, tzinfo=UTC)
    object_reference = "ecmwf-aifs/test/canonical-failure.grib2"
    sha256, size_bytes = write_raw_fixture(
        object_reference, b"synthetic-aifs-canonical-failure-fixture\n"
    )
    return AifsRawRetentionMetadata(
        dataset="AIFS Single Open Data 0.25 degree",
        object_reference=object_reference,
        sha256=sha256,
        retrieved_at=cycle,
        data_format="GRIB2",
        size_bytes=size_bytes,
        source_url=_SOURCE_URL,
        forecast_cycle=cycle,
        forecast_lead_seconds=0,
        valid_time=cycle,
        metadata_sha256="e" * 64,
        sidecar_sha256="d" * 64,
        aoi_id="everest-south-route",
        aoi_version="everest-south-route-v1.0",
        aoi_scope_id="everest-south-route-v1.0-default-100km",
    )


def test_synthetic_messages_satisfy_hardened_aifs_inventory() -> None:
    """Keep negative-path fixtures valid before each intended mutation."""
    messages = _synthetic_messages(datetime(2026, 8, 21, tzinfo=UTC))
    validate_decoded_inventory(messages)
    assert tuple(
        (message.parameter, message.level_type, message.level)
        for message in messages
    ) == (
        ("z", "surface", 0.0),
        ("10u", "heightAboveGround", 10.0),
        ("10v", "heightAboveGround", 10.0),
        ("2t", "heightAboveGround", 2.0),
        ("tp", "surface", 0.0),
    )
    assert {message.generating_process_identifier for message in messages} == {
        5
    }


def test_aifs_adapter_rejects_ifs_conflation_before_raw_persistence(
    migrated_postgres_engine: Engine,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """An IFS-labelled canonical record cannot persist or promote AIFS."""
    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed(session)
    raw = _synthetic_raw(write_raw_fixture)
    messages = _synthetic_messages(raw.forecast_cycle)
    validate_decoded_inventory(messages)
    weather = replace(
        normalize_messages(messages, _EVEREST_LATITUDE, _EVEREST_LONGITUDE),
        model="IFS",
    )
    canonical = AifsCanonicalRecord(
        weather=weather,
        spatial_key=provider_spatial_key(messages[0], 0),
    )
    adapter = compose_aifs_ingestion_adapter(
        WeatherIngestionService(factory, raw_storage_policy)
    )
    with pytest.raises(ValueError, match="source or model identity mismatch"):
        adapter.ingest(raw, (canonical,))
    with factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(WeatherRawArtifactModel)
            )
            == 0
        )
        assert (
            session.scalar(select(func.count()).select_from(WeatherRecordModel))
            == 0
        )
        source = session.get(DataSourceRegistryModel, "ecmwf-aifs")
        assert source.status == "configured"
        assert source.health_status == "unknown"


def test_aifs_canonical_failure_is_raw_first_without_escalation(
    migrated_postgres_engine: Engine,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """A canonical database rejection retains raw and leaves status unknown."""
    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed(session)
    raw = _synthetic_raw(write_raw_fixture)
    messages = _synthetic_messages(raw.forecast_cycle)
    validate_decoded_inventory(messages)
    weather = replace(
        normalize_messages(messages, _EVEREST_LATITUDE, _EVEREST_LONGITUDE),
        wind_speed=-1.0,
    )
    canonical = AifsCanonicalRecord(
        weather=weather,
        spatial_key=provider_spatial_key(messages[0], 0),
    )
    with pytest.raises(IntegrityError):
        compose_aifs_ingestion_adapter(
            WeatherIngestionService(factory, raw_storage_policy)
        ).ingest(raw, (canonical,))
    with factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(WeatherRawArtifactModel)
            )
            == 1
        )
        assert (
            session.scalar(select(func.count()).select_from(WeatherRecordModel))
            == 0
        )
        assert (
            session.scalar(
                select(func.count()).select_from(RawArtifactAuditEventModel)
            )
            == 2
        )
        source = session.get(DataSourceRegistryModel, "ecmwf-aifs")
        assert source.status == "configured"
        assert source.health_status == "unknown"
