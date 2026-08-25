"""Offline retained-ICON to PostgreSQL/API integration tests.

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

from services.weather.icon import (
    IconCanonicalRecord,
    IconRawRetentionMetadata,
    compose_icon_ingestion_adapter,
    icon_raw_retention_metadata_from_retrieval,
)
from services.weather.icon.connector import DwdIconConnector, RawRetrieval
from services.weather.icon.normalizer import (
    nearest_grid_index,
    normalize_canonical_record,
)
from services.weather.icon.parser import ParsedMessage, parse_grib_bytes

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
    "dwd-icon/e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57/"
    "icon_2026082100_000.grib2"
)
_PAYLOAD_SHA256 = (
    "e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57"
)
_METADATA_SHA256 = (
    "cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf"
)
_SIDECAR_SHA256 = (
    "0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46"
)
_SPATIAL_KEY = "icon:a27b8de618c411e4820ab5b098c6a5c0:818403"
_EVEREST_LATITUDE = 27.98806
_EVEREST_LONGITUDE = 86.92528
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_RawFixtureWriter = Callable[[str, bytes], tuple[str, int]]
_SOURCE_URLS = [
    "https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/"
    "icon_global_icosahedral_single-level_2026082100_000_T_2M.grib2.bz2",
    "https://opendata.dwd.de/weather/nwp/icon/grib/00/u_10m/"
    "icon_global_icosahedral_single-level_2026082100_000_U_10M.grib2.bz2",
    "https://opendata.dwd.de/weather/nwp/icon/grib/00/v_10m/"
    "icon_global_icosahedral_single-level_2026082100_000_V_10M.grib2.bz2",
    "https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/"
    "icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2",
    "https://opendata.dwd.de/weather/nwp/icon/grib/00/clat/"
    "icon_global_icosahedral_time-invariant_2026082100_CLAT.grib2.bz2",
    "https://opendata.dwd.de/weather/nwp/icon/grib/00/clon/"
    "icon_global_icosahedral_time-invariant_2026082100_CLON.grib2.bz2",
]


class _NetworkForbiddenSession:  # pylint: disable=too-few-public-methods
    """Fail immediately if this offline test reaches connector transport."""

    @staticmethod
    def get(_url: str, **_kwargs: Any) -> None:
        """Reject every attempted HTTP request."""
        raise AssertionError("offline retained-ICON test must not use HTTP")


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


def _load_retained_icon() -> tuple[RawStoragePolicy, RawRetrieval, bytes]:
    """Load and integrity-check approved retained connector output offline."""
    configured_root = os.environ.get(_RAW_ROOT_ENVIRONMENT_VARIABLE)
    if not configured_root:
        pytest.skip(
            f"{_RAW_ROOT_ENVIRONMENT_VARIABLE} is required for retained ICON"
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
        str(path.name)
        for path in (payload_path, metadata_path, sidecar_path)
        if not path.is_file()
    ]
    if missing:
        pytest.skip(f"approved retained ICON artifacts are absent: {missing}")

    payload = payload_path.read_bytes()
    metadata_bytes = metadata_path.read_bytes()
    sidecar_bytes = sidecar_path.read_bytes()
    assert len(payload) == 17_624_861
    assert _sha256(payload) == _PAYLOAD_SHA256
    assert _sha256(metadata_bytes) == _METADATA_SHA256
    assert sidecar_bytes == f"{_METADATA_SHA256}\n".encode("ascii")
    assert _sha256(sidecar_bytes) == _SIDECAR_SHA256

    metadata = json.loads(metadata_bytes.decode("utf-8"))
    connector = DwdIconConnector(
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
        "aoi_id": "everest-south-route",
        "aoi_scope_id": "everest-south-route-v1.0-expanded-2000km",
        "aoi_version": "everest-south-route-v1.0",
        "compressed_size_bytes": [
            3_338_757,
            3_876_736,
            3_885_537,
            1_313_525,
            1_264_300,
            1_398_235,
        ],
        "compression": "bzip2",
        "cycle": "2026-08-21T00:00:00+00:00",
        "dataset": "ICON global",
        "fields": ["T_2M", "U_10M", "V_10M", "HSURF", "CLAT", "CLON"],
        "format": "GRIB2",
        "lead_hours": 0,
        "model": "ICON",
        "provider": "DWD",
        "requested_coordinate": [_EVEREST_LATITUDE, _EVEREST_LONGITUDE],
        "retrieved_at": "2026-08-21T03:59:32.333262+00:00",
        "sha256": _PAYLOAD_SHA256,
        "size_bytes": 17_624_861,
        "source": "dwd-icon",
        "urls": _SOURCE_URLS,
        "valid_time": 1_787_270_400.0,
    }
    assert len(metadata["urls"]) == 6
    retrieval = RawRetrieval(
        payload_path=payload_path,
        metadata_path=metadata_path,
        url=",".join(metadata["urls"]),
        sha256=metadata["sha256"],
        size_bytes=metadata["size_bytes"],
        cycle=datetime.fromisoformat(metadata["cycle"]),
        lead_hours=metadata["lead_hours"],
        fields=tuple(metadata["fields"]),
    )
    return policy, retrieval, payload


@pytest.fixture
def retained_icon() -> Iterator[tuple[RawStoragePolicy, RawRetrieval, bytes]]:
    """Provide verified retained output after proving ecCodes availability."""
    _require_eccodes()
    yield _load_retained_icon()


def _raw_from_retention(retrieval: RawRetrieval) -> IconRawRetentionMetadata:
    """Use the authoritative connector-output conversion."""
    return icon_raw_retention_metadata_from_retrieval(retrieval)


def _assert_actual_messages(
    messages: tuple[ParsedMessage, ...], record: IconCanonicalRecord
) -> None:
    """Assert actual decoded native messages and selected Everest point values."""
    assert len(messages) == 6
    by_parameter = {message.parameter.lower(): message for message in messages}
    assert set(by_parameter) == {"2t", "10u", "10v", "hsurf", "tlat", "tlon"}
    anchor = by_parameter["2t"]
    index = nearest_grid_index(anchor, _EVEREST_LATITUDE, _EVEREST_LONGITUDE)
    assert index == 818_403
    assert all(len(message.values) == 2_949_120 for message in messages)
    assert anchor.latitudes[index] == pytest.approx(27.926742553710938)
    assert anchor.longitudes[index] == pytest.approx(86.921875)
    assert by_parameter["2t"].values[index] == pytest.approx(269.77911376953125)
    assert by_parameter["10u"].values[index] == pytest.approx(
        1.9642753601074225
    )
    assert by_parameter["10v"].values[index] == pytest.approx(
        -0.5655250549316396
    )
    assert by_parameter["hsurf"].values[index] == pytest.approx(
        5830.964752197266
    )
    assert record.spatial_key == _SPATIAL_KEY
    assert record.weather.latitude == pytest.approx(27.926742553710938)
    assert record.weather.longitude == pytest.approx(86.921875)
    assert record.weather.altitude == pytest.approx(5830.964752197266)
    assert record.weather.temperature == pytest.approx(-3.3708862304687273)
    assert record.weather.wind_speed == pytest.approx(2.0440636678148207)
    assert record.weather.wind_direction == pytest.approx(286.0613838292081)


def _factory(engine: Engine) -> sessionmaker:
    """Create the backend-owned session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed(session: Session, status: str = "configured") -> None:
    """Seed configured/unknown lifecycle state in the disposable database."""
    session.add(
        DataSourceRegistryModel(
            source_id="dwd-icon",
            name="ICON",
            provider="DWD",
            category="forecast",
            status=status,
            access_method="connector",
            commercial_allowed=False,
            credentials_required=False,
            health_status="unknown",
            metadata_version=1,
        )
    )
    session.commit()


@pytest.mark.real_data
# The end-to-end assertion keeps all boundary outputs visible in one test.
# pylint: disable-next=too-many-locals
def test_retained_icon_grib_to_postgres_and_public_forecast(
    retained_icon: tuple[RawStoragePolicy, RawRetrieval, bytes],
    migrated_postgres_engine: Engine,
) -> None:
    """Parse, normalize, adapt, persist, and query retained ICON end to end."""
    policy, retrieval, payload = retained_icon
    messages = parse_grib_bytes(payload)
    canonical = normalize_canonical_record(
        messages, _EVEREST_LATITUDE, _EVEREST_LONGITUDE
    )
    _assert_actual_messages(messages, canonical)
    raw = _raw_from_retention(retrieval)
    assert raw.sha256 == _PAYLOAD_SHA256
    assert raw.metadata_sha256 == _METADATA_SHA256
    assert raw.sidecar_sha256 == _SIDECAR_SHA256

    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed(session)
    adapter = compose_icon_ingestion_adapter(
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
        source = session.get(DataSourceRegistryModel, "dwd-icon")
        assert artifact.sha256 == _PAYLOAD_SHA256
        assert (
            artifact.metadata_json["provider_metadata_sha256"]
            == _METADATA_SHA256
        )
        assert (
            artifact.metadata_json["provider_sidecar_sha256"] == _SIDECAR_SHA256
        )
        assert record.spatial_key == _SPATIAL_KEY
        assert record.temperature == pytest.approx(-3.3708862304687273)
        assert record.wind_speed == pytest.approx(2.0440636678148207)
        assert source.status == "verified"
        assert source.health_status == "healthy"
        assert source.last_success_at == raw.retrieved_at

    with TestClient(create_app(factory)) as client:
        response = client.get("/api/weather/forecast?source=dwd-icon")
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
    assert public_record["source"] == "dwd-icon"
    assert public_record["model"] == "ICON"
    assert public_record["spatial_key"] == _SPATIAL_KEY
    public_json = json.dumps(response_payload)
    for private_value in (
        str(policy.raw_root),
        _OBJECT_REFERENCE,
        "opendata.dwd.de",
        _PAYLOAD_SHA256,
        _METADATA_SHA256,
        _SIDECAR_SHA256,
        "retention_owner",
        "raw_artifact",
        "audit_event",
    ):
        assert private_value not in public_json

    mismatched = replace(
        canonical,
        weather=replace(canonical.weather, model="IFS"),
    )
    with pytest.raises(ValueError, match="source or model does not match raw"):
        adapter.ingest(raw, (mismatched,))
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


def test_icon_canonical_failure_retains_classified_raw_without_escalation(
    migrated_postgres_engine: Engine,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """A canonical database rejection retains raw and leaves status unknown."""
    cycle = datetime(2026, 8, 21, tzinfo=UTC)
    object_reference = "dwd-icon/test/failure.grib2"
    sha256, size_bytes = write_raw_fixture(
        object_reference, b"synthetic-icon-canonical-failure-fixture\n"
    )
    raw = IconRawRetentionMetadata(
        dataset="ICON global",
        object_reference=object_reference,
        sha256=sha256,
        retrieved_at=cycle,
        data_format="GRIB2",
        size_bytes=size_bytes,
        source_url=None,
        forecast_cycle=cycle,
        forecast_lead_seconds=0,
        valid_time=cycle,
        raw_metadata={
            "source": "dwd-icon",
            "provider": "DWD",
            "model": "ICON",
            "aoi_id": "everest-south-route",
            "aoi_version": "everest-south-route-v1.0",
            "aoi_scope_id": "everest-south-route-v1.0-expanded-2000km",
        },
        metadata_sha256="e" * 64,
        sidecar_sha256="d" * 64,
    )
    messages = (
        ParsedMessage(
            "2t",
            cycle,
            cycle,
            0,
            (273.15,),
            (27.9881,),
            (86.925,),
            "K",
            "heightAboveGround",
            "unstructured_grid",
            "a27b8de618c411e4820ab5b098c6a5c0",
        ),
    )
    canonical = normalize_canonical_record(messages, 27.9881, 86.925)
    canonical = replace(
        canonical,
        weather=replace(canonical.weather, wind_speed=-1.0),
    )
    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed(session)
    with pytest.raises(IntegrityError):
        compose_icon_ingestion_adapter(
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
        source = session.get(DataSourceRegistryModel, "dwd-icon")
        assert source.status == "configured"
        assert source.health_status == "unknown"
