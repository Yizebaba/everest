"""Unit tests for the source normalizers (terrain / observations / satellite)."""

from __future__ import annotations

from datetime import datetime, timezone

from everest_api.sources.normalizers import (
    normalize_aws_observation,
    normalize_satellite_segment,
    normalize_terrain_tile,
)

_UTC = timezone.utc


def test_normalize_terrain_tile() -> None:
    """Normalize a GLO-30 terrain tile descriptor into canonical form."""
    record = normalize_terrain_tile(
        tile_name="Copernicus_DSM_COG_10_N27_00_E086_00_DEM",
        crs="EPSG:4326",
        bounds=(85.999861111, 27.000138888, 86.999861111, 28.000138888),
        width=3600,
        height=3600,
        resolution=(0.0002777777777777778, 0.0002777777777777778),
        min_elevation=187.5,
        max_elevation=8737.8,
        object_reference="terrain/Copernicus_DSM_COG_10_N27_00_E086_00_DEM.tif",
        sha256="4dfc87a0dec44a8a037164ddade45dd24bb53187176b5a14175c265bd6d20e76",
        size_bytes=43039634,
        retrieved_at=datetime(2026, 8, 24, 12, 0, tzinfo=_UTC),
    )
    assert record.source_id == "copernicus-dem"
    assert record.dataset == "glo30"
    assert record.max_elevation == 8737.8
    assert record.west < record.east


def test_normalize_aws_observation() -> None:
    """Normalize an Everest AWS station observation into canonical form."""
    record = normalize_aws_observation(
        timestamp=datetime(2025, 10, 23, 6, 15, tzinfo=_UTC),
        station="Base Camp",
        temperature_c=-4.833,
        relative_humidity=61.82,
        precipitation=1001.0,
        weather_code="NP",
        missing=True,
        qc_flags=("precipitation_anomaly",),
    )
    assert record.record_type == "observation"
    assert record.source_id == "everest-aws"
    assert record.quality_flags == ("precipitation_anomaly",)
    assert record.missing is True


def test_normalize_satellite_segment() -> None:
    """Normalize a Himawari satellite segment into canonical form."""
    record = normalize_satellite_segment(
        timestamp=datetime(2026, 8, 24, 13, 50, tzinfo=_UTC),
        band=3,
        segment=1,
        satellite_name="Himawari",
        observation_area="FLDK",
        object_reference="AHI-L1b-FLDK/2026/08/24/1350/HS_H09_..._S0110.DAT.bz2",
        sha256="0" * 64,
        size_bytes=9816761,
    )
    assert record.source_id == "himawari-9"
    assert record.dataset == "ahi-l1b-fldk"
    assert record.band == 3
    assert record.segment == 1
