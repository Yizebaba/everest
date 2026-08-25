"""GLO-30 real-data retrieval: download, parse, QC, report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from terrain import (
    download_tile,
    parse_tile,
    run_qc,
    summary_lines,
    tile_for_lat_lon,
)


def main(argv: list[str] | None = None) -> int:
    """Run one real GLO-30 retrieval for the Everest AOI center."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, default=27.9881)
    parser.add_argument("--lon", type=float, default=86.9250)
    parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args(argv)

    tile = tile_for_lat_lon(args.lat, args.lon)
    destination = args.raw_root / "terrain" / f"{tile.tile_name}.tif"
    print(f"tile: {tile.tile_name}")
    print(f"url: {tile.url()}")
    path, sha = download_tile(tile, destination)
    print(f"downloaded: {path} ({path.stat().st_size} bytes)")
    print(f"sha256: {sha}")
    parsed = parse_tile(path)
    report = run_qc(parsed)
    print("\n".join(summary_lines(report)))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
