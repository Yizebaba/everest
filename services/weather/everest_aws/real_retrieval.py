"""Everest AWS real-data retrieval: download, parse, QC, report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from everest_aws import download_station, parse_rows, run_qc, summary_lines


def main(argv: list[str] | None = None) -> int:
    """Run a real Everest AWS retrieval for one or all stations."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--station",
        default="all",
        choices=("Base Camp", "Camp 2", "South Col", "all"),
    )
    parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args(argv)

    stations = (
        ["Base Camp", "Camp 2", "South Col"]
        if args.station == "all"
        else [args.station]
    )
    failed = False
    for station in stations:
        destination = args.raw_root / "everest-aws" / f"{station}.csv"
        print(f"station: {station}")
        try:
            path = download_station(station, destination)
        except Exception as error:  # pragma: no cover - network errors
            print(f"download failed: {error}")
            failed = True
            continue
        print(f"downloaded: {path} ({path.stat().st_size} bytes)")
        rows, skipped = _parse_with_count(path, station)
        report = run_qc(rows, station, skipped_rows=skipped)
        print("\n".join(summary_lines(report)))
        failed = failed or not report.passed
    return 1 if failed else 0


def _parse_with_count(path: Path, station: str) -> tuple[list, int]:
    """Parse rows and count skipped lines for QC reporting."""
    rows = parse_rows(path, station)
    total = 0
    with path.open(encoding="utf-8", errors="replace") as stream:
        total = sum(1 for _ in stream) - 1  # minus header
    return rows, max(0, total - len(rows))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
