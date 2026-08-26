"""PostgreSQL read-query tests for the canonical weather projections."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from conftest import (  # pylint: disable=import-error
    _refuse_served_database,  # pylint: disable=protected-access
)
from everest_api.registry.models import DataSourceRegistryModel
from everest_api.weather.models import (
    WeatherRawArtifactModel,
    WeatherRecordModel,
)
from everest_api.weather.service import WeatherQueryService

NOW = datetime(2026, 8, 26, 12, tzinfo=UTC)


def _seed_artifact(session: Session, source_id: str) -> object:
    """Create the registry row and one raw artifact records can hang from."""
    if session.get(DataSourceRegistryModel, source_id) is None:
        session.add(
            DataSourceRegistryModel(
                source_id=source_id,
                name=source_id,
                provider="provider",
                category="forecast",
                status="configured",
                access_method="connector",
                commercial_allowed=False,
                credentials_required=False,
                health_status="unknown",
                metadata_version=1,
            )
        )
    artifact = WeatherRawArtifactModel(
        artifact_id=uuid4(),
        source_id=source_id,
        dataset=f"{source_id}-oper",
        object_reference=f"sha256/{source_id}/raw.grib2",
        sha256=uuid4().hex + uuid4().hex,
        retrieved_at=NOW,
        data_format="GRIB2",
        size_bytes=16,
        retention_class="legacy_unclassified",
        disposition_state="retained",
        hold_state="none",
    )
    session.add(artifact)
    session.commit()
    return artifact.artifact_id


def _record(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    artifact_id: object,
    source_id: str,
    spatial_key: str,
    lead_hours: float,
    *,
    altitude: float,
    visibility: float | None = None,
) -> WeatherRecordModel:
    """Build one forecast record valid ``lead_hours`` from the fixed NOW."""
    return WeatherRecordModel(
        raw_artifact_id=artifact_id,
        source_id=source_id,
        dataset=f"{source_id}-oper",
        record_type="forecast",
        timestamp=NOW + timedelta(hours=lead_hours),
        latitude=27.98806,
        longitude=86.92528,
        altitude=altitude,
        spatial_key=spatial_key,
        model="test-model",
        quality_flags=["clean"],
        temperature=-5.0,
        visibility=visibility,
    )


def test_current_returns_one_row_per_series_nearest_the_present(
    postgres_session: Session,
) -> None:
    """Each spatial series contributes its most recent already-valid record.

    The projection used to be the hundred newest valid times, which meant a
    cycle's furthest-out pressure levels crowded out every surface field.
    """
    ifs = _seed_artifact(postgres_session, "ecmwf-ifs")
    for lead in (-6, -3, 0, 24, 72):
        postgres_session.add(
            _record(ifs, "ecmwf-ifs", "ifs:300hpa", lead, altitude=9781.0)
        )
        postgres_session.add(
            _record(ifs, "ecmwf-ifs", "ifs:850hpa", lead, altitude=1539.0)
        )
    postgres_session.commit()

    rows = WeatherQueryService(postgres_session).current(now=NOW)

    assert [row.spatial_key for row in rows] == ["ifs:850hpa", "ifs:300hpa"]
    assert {row.timestamp for row in rows} == {NOW}


def test_current_keeps_a_surface_series_a_far_lead_would_have_hidden(
    postgres_session: Session,
) -> None:
    """A surface record survives alongside deeper-lead pressure rows.

    This is the visibility regression: GFS is the only configured provider that
    publishes surface visibility, and its short-lead rows sorted below three
    days of IFS pressure levels under the old timestamp ordering.
    """
    ifs = _seed_artifact(postgres_session, "ecmwf-ifs")
    gfs = _seed_artifact(postgres_session, "noaa-gfs")
    for lead in range(0, 73, 3):
        postgres_session.add(
            _record(
                ifs, "ecmwf-ifs", f"ifs:{lead}:300hpa", lead, altitude=9781.0
            )
        )
    postgres_session.add(
        _record(
            gfs, "noaa-gfs", "gfs:surface", 0, altitude=5918.0, visibility=40.0
        )
    )
    postgres_session.commit()

    rows = WeatherQueryService(postgres_session).current(now=NOW)

    assert [row.visibility for row in rows if row.visibility is not None] == [
        40.0
    ]
    # Ground-up within the same distance from now, so the surface row precedes
    # the pressure level above it.
    assert rows[0].spatial_key == "gfs:surface"


def test_current_falls_back_to_the_soonest_future_row_for_a_future_series(
    postgres_session: Session,
) -> None:
    """A series with nothing valid yet reports its next record, not nothing."""
    ifs = _seed_artifact(postgres_session, "ecmwf-ifs")
    for lead in (6, 12):
        postgres_session.add(
            _record(ifs, "ecmwf-ifs", "ifs:300hpa", lead, altitude=9781.0)
        )
    postgres_session.commit()

    rows = WeatherQueryService(postgres_session).current(now=NOW)

    assert [row.timestamp for row in rows] == [NOW + timedelta(hours=6)]


def test_current_filters_by_source(postgres_session: Session) -> None:
    """The source filter narrows the series set without changing the ranking."""
    ifs = _seed_artifact(postgres_session, "ecmwf-ifs")
    gfs = _seed_artifact(postgres_session, "noaa-gfs")
    postgres_session.add(
        _record(ifs, "ecmwf-ifs", "ifs:300hpa", 0, altitude=9781.0)
    )
    postgres_session.add(
        _record(gfs, "noaa-gfs", "gfs:surface", 0, altitude=5918.0)
    )
    postgres_session.commit()

    rows = WeatherQueryService(postgres_session).current("noaa-gfs", now=NOW)

    assert [row.source_id for row in rows] == ["noaa-gfs"]


def test_test_database_guard_refuses_the_served_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A test URL naming the deployment's own database is rejected outright.

    The PostgreSQL fixture ends with ``downgrade base``, so a collision here
    destroys operational data instead of failing a test. This asserts the guard
    with synthetic values rather than by pointing a real run at a real store.
    """
    monkeypatch.setenv("EVEREST_DATABASE_URL", "")
    monkeypatch.setenv("EVEREST_DB_USER", "user")
    monkeypatch.setenv("EVEREST_DB_PASSWORD", "secret")
    monkeypatch.setenv("EVEREST_DB_NAME", "served_db")
    monkeypatch.setenv("EVEREST_DB_PORT", "5432")
    monkeypatch.setenv("EVEREST_DB_HOST", "127.0.0.1")

    with pytest.raises(pytest.fail.Exception, match="deployment serves"):
        _refuse_served_database(
            "postgresql+psycopg://user:secret@127.0.0.1:5432/served_db"
        )
    # A different database on the same server is an acceptable target.
    _refuse_served_database(
        "postgresql+psycopg://user:secret@127.0.0.1:5432/scratch_db"
    )


def test_test_database_guard_passes_when_no_deployment_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no resolvable deployment target there is nothing to collide with."""
    for name in (
        "EVEREST_DATABASE_URL",
        "EVEREST_DB_USER",
        "EVEREST_DB_PASSWORD",
        "EVEREST_DB_NAME",
        "EVEREST_DB_PORT",
    ):
        monkeypatch.delenv(name, raising=False)

    _refuse_served_database("postgresql+psycopg://u:p@127.0.0.1:5432/anything")
