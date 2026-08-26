"""Ingest retained real source data into the dev database for local preview.

Requires PostgreSQL (migrated) and the retained raw files under
D:\\Everest-data\\raw. Run from apps/api:
  python ingest_dev_data.py
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from everest_api.persistence.database import (
    create_session_factory,
    resolve_database_url,
)
from everest_api.registry.models import DataSourceRegistryModel
from everest_api.sources.models import (
    AwsObservationModel,
    SatelliteSegmentModel,
    TerrainTileModel,
)
from everest_api.sources.normalizers import (
    normalize_aws_observation,
    normalize_satellite_segment,
    normalize_terrain_tile,
)

_UTC = timezone.utc


def main() -> None:
    """Ingest the retained GLO-30, Everest AWS, and Himawari samples."""
    root = Path(os.environ.get("EVEREST_RAW_ROOT", r"D:\Everest-data\raw"))
    session_factory = create_session_factory(resolve_database_url())
    with session_factory() as session:
        session.execute(
            __import__("sqlalchemy").text(
                "TRUNCATE TABLE terrain_tile, aws_observation, satellite_segment"
            )
        )
        for source_id, status, access_method, commercial in (
            ("copernicus-dem", "connected", "AWS Open Data S3", True),
            ("everest-aws", "connected", "AppState portal CSV feed", False),
            ("himawari-9", "connected", "NOAA AWS S3", True),
        ):
            existing = session.scalars(
                __import__("sqlalchemy").select(DataSourceRegistryModel).where(
                    DataSourceRegistryModel.source_id == source_id
                )
            ).first()
            if existing is None:
                session.add(
                    DataSourceRegistryModel(
                        source_id=source_id,
                        name=source_id,
                        provider="Everest approved source",
                        category="terrain/observation/satellite",
                        status=status,
                        access_method=access_method,
                        commercial_allowed=commercial,
                        credentials_required=False,
                        health_status="unknown",
                        metadata_version=1,
                    )
                )
        session.flush()
        from everest_aws.parser import parse_rows
        from everest_aws.qc import run_qc as aws_qc
        from himawari.connector import sha256_of as h_sha
        from himawari.parser import parse_segment
        from terrain.connector import sha256_of as t_sha
        from terrain.parser import parse_tile
        from terrain.qc import run_qc as t_qc

        terrain_path = root / "terrain" / "Copernicus_DSM_COG_10_N27_00_E086_00_DEM.tif"
        if terrain_path.exists():
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
            print(f"terrain: {tile.tile_name}")

        aws_path = root / "everest-aws" / "Base Camp.csv"
        if aws_path.exists():
            rows = parse_rows(aws_path, "Base Camp")
            qc = aws_qc(rows, "Base Camp")
            for row in rows[:10]:
                obs = normalize_aws_observation(
                    timestamp=row.timestamp,
                    station="Base Camp",
                    temperature_c=row.temperature_c,
                    relative_humidity=row.relative_humidity,
                    precipitation=row.precipitation,
                    weather_code=row.weather_code,
                    missing=row.missing,
                    qc_flags=qc.flags,
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
            print(f"everest-aws: {len(rows[:10])} rows")

        himawari_path = root / "himawari" / "band03_seg001.DAT.bz2"
        if himawari_path.exists():
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
            print(f"himawari: {satellite.band} band segment {satellite.segment}")
        session.commit()
    print("ingest done")


if __name__ == "__main__":
    main()
