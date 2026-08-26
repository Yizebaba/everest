"""Himawari satellite package (EV-SAT-001, meteorology + gis-3d owned)."""

from services.satellite.himawari.connector import (
    FlDkTimeSlot,
    download_segment,
    latest_ten_minute_slot,
    segment_key,
    segment_url,
    sha256_of,
)
from services.satellite.himawari.parser import SegmentInfo, parse_segment
from services.satellite.himawari.qc import HimawariQcReport, run_qc

__all__ = [
    "FlDkTimeSlot",
    "HimawariQcReport",
    "SegmentInfo",
    "download_segment",
    "latest_ten_minute_slot",
    "parse_segment",
    "run_qc",
    "segment_key",
    "segment_url",
    "sha256_of",
]
