"""Unit tests for the GLO-30 terrain connector, parser, and QC."""

from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from terrain.connector import tile_for_lat_lon
from terrain.parser import parse_tile
from terrain.qc import run_qc


def _synthetic_tile(tmp_path, elevation: np.ndarray, crs="EPSG:4326") -> str:
    """Write a small synthetic single-band GeoTIFF and return its path."""
    path = tmp_path / "synthetic.tif"
    transform = from_origin(85.0, 28.0, 0.01, 0.01)
    with rasterio.open(
        str(path),
        "w",
        driver="GTiff",
        width=elevation.shape[1],
        height=elevation.shape[0],
        count=1,
        dtype=elevation.dtype,
        crs=CRS.from_epsg(4326) if crs == "EPSG:4326" else crs,
        transform=transform,
    ) as dst:
        dst.write(elevation, 1)
    return str(path)


def test_tile_for_lat_lon_everest() -> None:
    tile = tile_for_lat_lon(27.9881, 86.9250)
    assert tile.tile_name == "Copernicus_DSM_COG_10_N27_00_E086_00_DEM"
    assert tile.object_key().endswith(".tif")


def test_tile_for_lat_lon_southern_hemisphere() -> None:
    tile = tile_for_lat_lon(-33.0, -70.0)
    assert tile.tile_name == "Copernicus_DSM_COG_10_S33_00_W070_00_DEM"


def test_parse_and_qc_pass(tmp_path) -> None:
    elevation = np.full((3600, 3600), 3000.0, dtype=np.float32)
    elevation[1800, 1800] = 8737.0
    path = _synthetic_tile(tmp_path, elevation)
    parsed = parse_tile(tmp_path / "synthetic.tif")
    assert parsed.crs == "EPSG:4326"
    report = run_qc(parsed)
    assert report.passed
    assert report.max_elevation == pytest.approx(8737.0)
    assert report.valid_pixels == 3600 * 3600


def test_qc_flags_wrong_crs_and_extreme(tmp_path) -> None:
    elevation = np.full((100, 100), 15000.0, dtype=np.float32)
    path = _synthetic_tile(tmp_path, elevation, crs="EPSG:3857")
    parsed = parse_tile(tmp_path / "synthetic.tif")
    report = run_qc(parsed)
    assert not report.passed
    assert "unexpected_crs" in report.flags
    assert "above_plausible_elevation" in report.flags
