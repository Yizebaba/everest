"""Persist real ADR-019 source data into the persistent Everest database."""

from __future__ import annotations

from datetime import UTC, datetime
import sys
from pathlib import Path

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")
sys.path.insert(0, "/mnt/d/Everest/packages/weather_ingestion_contract")
sys.path.insert(0, "/mnt/d/Everest/services")
sys.path.insert(0, "/mnt/d/Everest/services/weather")
sys.path.insert(0, "/mnt/d/Everest/services/satellite")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from everest_api.sources.models import (  # noqa: E402
    AwsObservationModel,
    SatelliteSegmentModel,
    TerrainTileModel,
)
from everest_api.sources.normalizers import (  # noqa: E402
    normalize_aws_observation,
    normalize_satellite_segment,
    normalize_terrain_tile,
)
from services.weather.everest_aws.parser import parse_rows  # noqa: E402
from services.weather.everest_aws.qc import run_qc as aws_qc  # noqa: E402
from services.satellite.himawari.connector import (
    sha256_of as h_sha,
)  # noqa: E402
from services.satellite.himawari.parser import parse_segment  # noqa: E402
from services.terrain.connector import sha256_of as t_sha  # noqa: E402
from services.terrain.parser import parse_tile  # noqa: E402
from services.terrain.qc import run_qc as t_qc  # noqa: E402

RAW = Path("/mnt/d/Everest-data/raw")
_UTC = UTC
NOW = datetime.now(_UTC)


def db_url() -> str:
    from everest_api.persistence.database import resolve_database_url

    return resolve_database_url()


def ingest_terrain(session: Session) -> None:
    terrain_path = (
        RAW / "terrain" / "Copernicus_DSM_COG_10_N27_00_E086_00_DEM.tif"
    )
    if not terrain_path.exists():
        print("terrain file missing; skip")
        return
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
        retrieved_at=NOW,
    )
    session.add(TerrainTileModel(**tile.__dict__))
    print(
        f"terrain: {tile.tile_name} crs={tile.crs} "
        f"{tile.width}x{tile.height} elev {tile.min_elevation}-{tile.max_elevation}m"
    )


def ingest_aws(session: Session) -> None:
    for station in ("Base Camp", "Camp 2", "South Col"):
        path = RAW / "everest-aws" / f"{station}.csv"
        if not path.exists():
            print(f"aws {station}: missing; skip")
            continue
        rows = parse_rows(path, station)
        if not rows:
            print(f"aws {station}: no rows")
            continue
        qc_report = aws_qc(rows, station)
        first = rows[0]
        obs = normalize_aws_observation(
            timestamp=first.timestamp,
            station=station,
            temperature_c=first.temperature_c,
            relative_humidity=first.relative_humidity,
            precipitation=first.precipitation,
            weather_code=first.weather_code,
            missing=first.missing,
            qc_flags=qc_report.flags,
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
        print(
            f"aws {station}: first row {first.timestamp} t={first.temperature_c}C"
        )


def ingest_himawari(session: Session) -> None:
    path = RAW / "himawari" / "band03_seg001.DAT.bz2"
    if not path.exists():
        print("himawari file missing; skip")
        return
    seg = parse_segment(path)
    satellite = normalize_satellite_segment(
        timestamp=NOW,
        band=3,
        segment=1,
        satellite_name=seg.satellite_name,
        observation_area=seg.observation_area,
        object_reference=str(path),
        sha256=h_sha(path),
        size_bytes=path.stat().st_size,
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
    print(
        f"himawari: {seg.satellite_name} {seg.observation_area} "
        f"sha={satellite.sha256[:12]}"
    )


def main() -> None:
    engine = create_engine(db_url())
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        ingest_terrain(session)
        ingest_aws(session)
        ingest_himawari(session)
        session.commit()
    print("ADR-019 sources persisted to persistent database")


if __name__ == "__main__":
    main()
