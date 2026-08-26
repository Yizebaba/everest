"""Himawari real-data retrieval: download, parse, QC, report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from services.satellite.himawari import (
    download_segment,
    latest_ten_minute_slot,
    parse_segment,
    run_qc,
    segment_url,
)


def main(argv: list[str] | None = None) -> int:
    """Retrieve one real Himawari-9 band-3 segment and run QC."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--band", type=int, default=3)
    parser.add_argument("--segment", type=int, default=1)
    parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args(argv)

    slot = latest_ten_minute_slot()
    print(f"time slot: {slot.timestamp.isoformat()}")
    destination = (
        args.raw_root
        / "himawari"
        / f"band{args.band:02d}_seg{args.segment:03d}.DAT.bz2"
    )
    try:
        url = segment_url(slot, args.band, args.segment)
    except FileNotFoundError as error:
        print(f"segment unavailable: {error}")
        return 1
    print(f"url: {url}")
    try:
        path, sha = download_segment(slot, args.band, args.segment, destination)
    except Exception as error:  # pragma: no cover - network errors
        print(f"download failed: {error}")
        return 1
    print(f"downloaded: {path} ({path.stat().st_size} bytes)")
    print(f"sha256: {sha}")
    info = parse_segment(path)
    report = run_qc(info, args.band, args.segment)
    print(
        f"segment: band={report.band} segment={report.segment} "
        f"satellite={report.satellite_name} area={report.observation_area}"
    )
    print(
        f"compressed: {info.compressed_size} "
        f"uncompressed: {info.uncompressed_size}"
    )
    print(f"flags: {','.join(report.flags) or 'none'}")
    print(f"qc: {'PASS' if report.passed else 'FAIL'}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
