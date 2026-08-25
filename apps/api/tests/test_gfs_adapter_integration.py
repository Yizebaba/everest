"""PostgreSQL/API composition tests for the checked-in NOAA GFS adapter.

These tests require ``EVEREST_TEST_DATABASE_URL`` and use the existing Alembic
fixture. They deliberately do not retrieve a file or call the network. A small
deterministic payload under the temporary approved raw root exercises backend
composition without making a new real-data success claim.
"""

# SQLAlchemy's dynamic ``func`` namespace is intentionally callable.
# pylint: disable=not-callable

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

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
from everest_api.app import create_app
from everest_api.raw_storage import RawStoragePolicy
from everest_api.registry.models import DataSourceRegistryModel
from everest_api.weather.models import (
    WeatherRawArtifactModel,
    WeatherRecordModel,
)
from everest_api.weather.service import WeatherIngestionService

_RawFixtureWriter = Callable[[str, bytes], tuple[str, int]]


def _factual_raw(
    write_raw_fixture: _RawFixtureWriter,
) -> GfsRawRetentionMetadata:
    """Return GFS metadata with a verifiable synthetic test payload."""
    cycle = datetime(2026, 8, 20, tzinfo=UTC)
    object_reference = "raw/noaa-gfs/synthetic-composition.grib2"
    sha256, size_bytes = write_raw_fixture(
        object_reference, b"synthetic-gfs-composition-fixture\n"
    )
    return GfsRawRetentionMetadata(
        dataset="GFS pgrb2.0p25",
        object_reference=object_reference,
        sha256=sha256,
        retrieved_at=datetime(2026, 8, 21, 2, 3, 40, 349485, tzinfo=UTC),
        data_format="GRIB2",
        size_bytes=size_bytes,
        source_url=(
            "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
            "gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000"
        ),
        forecast_cycle=cycle,
        forecast_lead_seconds=0,
        valid_time=cycle,
        raw_metadata={"source": "noaa-gfs", "model": "GFS"},
    )


def _factual_record(
    cycle: datetime,
    wind_speed: float = 2.0815467554532674,
) -> GfsCanonicalRecord:
    """Return the normalized documented Everest-grid record for the artifact."""
    return GfsCanonicalRecord(
        weather=WeatherRecord(
            record_type=RecordType.FORECAST,
            timestamp=cycle,
            latitude=27.9881,
            longitude=86.9250,
            altitude=5917.819375,
            wind_speed=wind_speed,
            wind_direction=235.34425831717988,
            temperature=-3.243212890625,
            precipitation=None,
            visibility=None,
            source="noaa-gfs",
            model="GFS",
            forecast=ForecastIdentity(cycle, timedelta(0)),
            quality_flags=frozenset({"missing_value"}),
        ),
        spatial_key="gfs:0p25:28.0:87.0",
    )


def _seed_gfs(session: Session) -> None:
    """Seed the configured, operationally unknown source required by raw FK."""
    session.add(
        DataSourceRegistryModel(
            source_id="noaa-gfs",
            name="GFS",
            provider="NOAA/NCEP",
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


def _factory(engine: Engine) -> sessionmaker:
    """Create the backend-owned session factory for an Alembic-migrated engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_gfs_adapter_persists_factual_record_and_public_forecast(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """Compose GFS adapter with API service and expose canonical data only."""
    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed_gfs(session)
        source = session.get(DataSourceRegistryModel, "noaa-gfs")
        assert source.status == "configured"
        assert source.health_status == "unknown"

    adapter = compose_gfs_ingestion_adapter(
        WeatherIngestionService(factory, raw_storage_policy)
    )
    raw = _factual_raw(write_raw_fixture)
    adapter.ingest(raw, (_factual_record(raw.forecast_cycle),))

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
        source = session.get(DataSourceRegistryModel, "noaa-gfs")
        assert source.status == "verified"
        assert source.health_status == "healthy"
        assert source.last_success_at == raw.retrieved_at
        record = session.scalar(select(WeatherRecordModel))
        assert record.model == "GFS"
        assert record.forecast_cycle == raw.forecast_cycle
        assert record.forecast_lead_seconds == 0
        assert record.spatial_key == "gfs:0p25:28.0:87.0"
        assert record.latitude == pytest.approx(27.9881)
        assert record.longitude == pytest.approx(86.9250)
        assert record.altitude == pytest.approx(5917.819375)
        assert record.temperature == pytest.approx(-3.243212890625)
        assert record.wind_speed == pytest.approx(2.0815467554532674)
        assert record.wind_direction == pytest.approx(235.34425831717988)
        assert set(record.quality_flags) == {"missing_value"}

    with TestClient(create_app(factory)) as client:
        response = client.get("/api/weather/forecast?source=noaa-gfs")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["records"]) == 1
    public_record = payload["records"][0]
    assert public_record["source"] == "noaa-gfs"
    assert public_record["model"] == "GFS"
    assert public_record["forecast_cycle"] == "2026-08-20T00:00:00Z"
    assert public_record["forecast_lead_time"] == 0
    assert public_record["latitude"] == pytest.approx(27.9881)
    assert public_record["longitude"] == pytest.approx(86.9250)
    assert public_record["altitude"] == pytest.approx(5917.819375)
    assert public_record["temperature"] == pytest.approx(-3.243212890625)
    assert public_record["precipitation"] is None
    assert public_record["visibility"] is None
    public_json = json.dumps(payload)
    assert "raw/noaa-gfs" not in public_json
    assert "nomads.ncep.noaa.gov" not in public_json
    assert raw.sha256 not in public_json


def test_gfs_adapter_retains_raw_when_canonical_commit_fails(
    migrated_postgres_engine: object,
    raw_storage_policy: RawStoragePolicy,
    write_raw_fixture: _RawFixtureWriter,
) -> None:
    """A database rejection retains raw evidence and does not verify the source."""
    factory = _factory(migrated_postgres_engine)
    with factory() as session:
        _seed_gfs(session)

    adapter = compose_gfs_ingestion_adapter(
        WeatherIngestionService(factory, raw_storage_policy)
    )
    raw = _factual_raw(write_raw_fixture)
    record = _factual_record(raw.forecast_cycle)
    with pytest.raises(IntegrityError):
        adapter.ingest(
            raw,
            (
                replace(
                    record,
                    weather=replace(record.weather, wind_speed=-1.0),
                ),
            ),
        )

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
        source = session.get(DataSourceRegistryModel, "noaa-gfs")
        assert source.status == "configured"
        assert source.health_status == "unknown"
