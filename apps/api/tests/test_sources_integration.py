"""Integration test: real source data ingested to PostgreSQL and queried via API.

Requires EVEREST_TEST_DATABASE_URL (real PostgreSQL) and the retained real raw
files under D:\\Everest-data\\raw. Skips otherwise.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from everest_api.app import create_app
from everest_api.sources.models import (
    AwsObservationModel,
    SatelliteSegmentModel,
    TerrainTileModel,
)

_DATABASE_URL_ENV = "EVEREST_TEST_DATABASE_URL"
_UTC = timezone.utc


def _db_url() -> str:
    url = os.environ.get(_DATABASE_URL_ENV)
    if not url:
        pytest.skip(f"{_DATABASE_URL_ENV} is required for PostgreSQL tests")
    return url


def _real_raw() -> dict[str, Path]:
    root = Path(os.environ.get("EVEREST_RAW_ROOT", r"D:\Everest-data\raw"))
    return {
        "terrain": root
        / "terrain"
        / "Copernicus_DSM_COG_10_N27_00_E086_00_DEM.tif",
        "aws": root / "everest-aws" / "Base Camp.csv",
        "himawari": root / "himawari" / "band03_seg001.DAT.bz2",
    }


def _require_raw() -> dict[str, Path]:
    raw = _real_raw()
    missing = [name for name, path in raw.items() if not path.exists()]
    if missing:
        pytest.skip(f"missing raw files: {missing}")
    return raw


def _ingest(session: Session) -> None:
    from everest_aws.parser import parse_rows  # type: ignore[import-not-found]
    from everest_aws.qc import run_qc as aws_qc  # type: ignore[import-not-found]
    from everest_api.sources.normalizers import (
        normalize_aws_observation,
        normalize_satellite_segment,
        normalize_terrain_tile,
    )
    from himawari.connector import sha256_of as h_sha  # type: ignore[import-not-found]
    from himawari.parser import parse_segment  # type: ignore[import-not-found]
    from terrain.connector import sha256_of as t_sha  # type: ignore[import-not-found]
    from terrain.parser import parse_tile  # type: ignore[import-not-found]
    from terrain.qc import run_qc as t_qc  # type: ignore[import-not-found]

    session.execute(
        text("TRUNCATE TABLE terrain_tile, aws_observation, satellite_segment")
    )
    raw = _require_raw()

    terrain_path = raw["terrain"]
    parsed = parse_tile(terrain_path)
    qc = t_qc(parsed)
    tile = normalize_terrain_tile(
        tile_name=terrain_path.stem,
        crs=parsed.crs,
        bounds=parsed.bounds,
        width=parsed.width,
        height=parsed.height,
        resolution=parsed.resolution,
        min_elevation=qc.min_elevation,
        max_elevation=qc.max_elevation,
        object_reference=str(terrain_path),
        sha256=t_sha(terrain_path),
        size_bytes=terrain_path.stat().st_size,
        retrieved_at=datetime(2026, 8, 24, 12, 0, tzinfo=_UTC),
    )
    session.add(TerrainTileModel(**tile.__dict__))

    aws_rows = parse_rows(raw["aws"], "Base Camp")
    if aws_rows:
        aws_qc_report = aws_qc(aws_rows, "Base Camp")
        first = aws_rows[0]
        obs = normalize_aws_observation(
            timestamp=first.timestamp,
            station="Base Camp",
            temperature_c=first.temperature_c,
            relative_humidity=first.relative_humidity,
            precipitation=first.precipitation,
            weather_code=first.weather_code,
            missing=first.missing,
            qc_flags=aws_qc_report.flags,
        )
        session.add(
            AwsObservationModel(
                timestamp=obs.timestamp,
                station=obs.station,
                source_id=obs.source_id,
                dataset=obs.dataset,
                record_type=obs.record_type,
                temperature_c=obs.temperature_c,
                relative_humidity=obs.relative_humidity,
                precipitation=obs.precipitation,
                weather_code=obs.weather_code,
                missing=obs.missing,
                quality_flags=list(obs.quality_flags),
            )
        )

    himawari_path = raw["himawari"]
    seg = parse_segment(himawari_path)
    satellite = normalize_satellite_segment(
        timestamp=datetime(2026, 8, 24, 13, 50, tzinfo=_UTC),
        band=3,
        segment=1,
        satellite_name=seg.satellite_name,
        observation_area=seg.observation_area,
        object_reference=str(himawari_path),
        sha256=h_sha(himawari_path),
        size_bytes=himawari_path.stat().st_size,
    )
    session.add(
        SatelliteSegmentModel(
            timestamp=satellite.timestamp,
            source_id=satellite.source_id,
            dataset=satellite.dataset,
            band=satellite.band,
            segment=satellite.segment,
            satellite_name=satellite.satellite_name,
            observation_area=satellite.observation_area,
            object_reference=satellite.object_reference,
            sha256=satellite.sha256,
            size_bytes=satellite.size_bytes,
        )
    )
    session.commit()


def _engine():
    return create_engine(_db_url())


def test_terrain_api_returns_tile_and_no_leak() -> None:
    engine = _engine()
    with Session(engine) as session:
        _ingest(session)
    app = create_app(lambda: Session(engine))
    client = TestClient(app)
    response = client.get(
        "/api/terrain/tile", params={"latitude": 27.9881, "longitude": 86.9250}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tile"] is not None
    assert body["tile"]["tile_name"].startswith(
        "Copernicus_DSM_COG_10_N27_00_E086"
    )
    assert body["tile"]["max_elevation"] > 8000
    assert "object_reference" not in body["tile"]
    assert "sha256" not in body["tile"]


def test_observations_api_returns_current() -> None:
    engine = _engine()
    with Session(engine) as session:
        _ingest(session)
    app = create_app(lambda: Session(engine))
    client = TestClient(app)
    response = client.get("/api/observations/current")
    assert response.status_code == 200
    observations = response.json()["observations"]
    assert "Base Camp" in observations
    assert observations["Base Camp"]["temperature_c"] is not None


def test_satellite_api_returns_segments_and_no_leak() -> None:
    engine = _engine()
    with Session(engine) as session:
        _ingest(session)
    app = create_app(lambda: Session(engine))
    client = TestClient(app)
    response = client.get("/api/satellite/segments", params={"band": 3})
    assert response.status_code == 200
    segments = response.json()["segments"]
    assert any(
        s["band"] == 3 and s["observation_area"] == "FLDK" for s in segments
    )
    assert all("object_reference" not in s for s in segments)
    assert all("sha256" not in s for s in segments)
