"""Generate Cesium 3D Tiles from the retained GLO-30 tile.

Reads the GeoTIFF, downsamples to an ~600x600 grid, writes .xyz, and calls
py3dtiles convert to produce a 3D Tiles tileset under an output directory.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio

SRC = Path("/mnt/d/Everest-data/raw/terrain/Copernicus_DSM_COG_10_N27_00_E086_00_DEM.tif")
WORK = Path("/mnt/d/Everest-data/tiles/xyz")
OUT = Path("/mnt/d/Everest-data/tiles/3dtiles")
STEP = 6  # every 6th pixel -> ~600x600 grid


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    xyz_path = WORK / "everest-terrain.xyz"

    with rasterio.open(SRC) as ds:
        arr = ds.read(1)
        height, width = arr.shape
        rows = list(range(0, height, STEP))
        cols = list(range(0, width, STEP))
        ys = np.arange(height)[rows]
        xs = np.arange(width)[cols]
        X, Y = np.meshgrid(xs, ys)
        Z = arr[rows][:, cols].astype(np.float64)

        # pixel -> lon/lat using affine
        aff = ds.transform
        lons = aff.c + X * aff.a
        lats = aff.f + Y * aff.e

        valid = np.isfinite(Z)
        with xyz_path.open("w", encoding="utf-8") as fh:
            for lon, lat, z in zip(
                lons[valid], lats[valid], Z[valid], strict=True
            ):
                fh.write(f"{lon:.6f} {lat:.6f} {z:.2f}\n")

    print(f"xyz points written: {xyz_path} ({sum(1 for _ in open(xyz_path))} lines)")

    result = subprocess.run(
        [
            "py3dtiles", "convert",
            str(xyz_path),
            "--out", str(OUT),
            "--overwrite",
            "--srs_in", "4326",
            "--srs_out", "4978",
            "--jobs", "4",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout[-2000:] if result.stdout else "")
    if result.returncode != 0:
        print("py3dtiles stderr:", result.stderr[-2000:])
        sys.exit(result.returncode)
    tileset = OUT / "tileset.json"
    print("tileset:", tileset.exists(), tileset.stat().st_size if tileset.exists() else "")


if __name__ == "__main__":
    main()
