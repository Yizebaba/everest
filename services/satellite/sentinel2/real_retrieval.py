"""Sentinel-2 real-data retrieval: AOI true-colour RGB build + report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sentinel2 import (
    Sentinel2Scene,
    build_rgb,
    summarize,
    write_png,
)

# Everest AOI window (WGS84): a small sub-region around the south-route area.
_EVEREST_BOUNDS = (86.8, 27.85, 87.05, 28.05)


def main(argv: list[str] | None = None) -> int:
    """Build a true-colour RGB image for the Everest AOI from Sentinel-2 L1C."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026/8/24", help="scene date YYYY/M/D")
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument(
        "--size",
        type=int,
        default=512,
        help="output RGB size (square), defaults 512",
    )
    args = parser.parse_args(argv)

    scene = Sentinel2Scene(
        utm_zone="45R",
        latitude_band="VL",
        date=args.date,
        num="0",
        crs="EPSG:32645",
    )
    print(f"scene: {scene.prefix}")
    print(f"bounds: {_EVEREST_BOUNDS}")

    # Prefer locally retained band files when present; otherwise read via
    # vsicurl (best-effort; large-band remote reads may fail).
    band_dir = args.raw_root / "sentinel2" / "45R_VL_20260824"
    band_files: dict[int, str] | None = None
    if band_dir.is_dir():
        band_files = {
            b: str(band_dir / f"B{b:02d}.jp2") for b in (2, 3, 4)
        }
    rgb = build_rgb(scene, _EVEREST_BOUNDS, (args.size, args.size), band_files)
    print("\n".join(summarize(scene, rgb)))

    destination = args.raw_root / "sentinel2" / f"everest-rgb-{args.size}.png"
    write_png(rgb.rgb, destination)
    print(f"wrote: {destination} ({destination.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
