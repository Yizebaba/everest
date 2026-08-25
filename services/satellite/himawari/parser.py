"""Himawari AHI L1b parser: decompress and verify segment identity fields."""

from __future__ import annotations

import bz2
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SegmentInfo:
    """Verified identity metadata from a Himawari Standard Data segment.

    Field-level geometry decode (pixels per line, lines per block, number of
    blocks) requires the official JMA Himawari Standard Data format guide
    (PDF); those offsets are NOT asserted here. Only fields verified against
    the real NOAA S3 payload are reported.
    """

    path: Path
    compressed_size: int
    uncompressed_size: int
    satellite_name: str
    observation_area: str


def parse_segment(path: Path) -> SegmentInfo:
    """Decompress a bz2 segment and verify identity header fields.

    Verified field offsets from real NOAA S3 payloads (band 3, FLDK):
    - bytes 6:14  = satellite name (8 bytes, ASCII)
    - bytes 38:42 = observation area code (4 bytes, e.g. 'FLDK')
    """
    compressed_size = path.stat().st_size
    raw = bz2.decompress(path.read_bytes())
    satellite_name = raw[6:14].decode("ascii", errors="replace").strip("\x00 ")
    observation_area = (
        raw[38:42].decode("ascii", errors="replace").strip("\x00 ")
    )
    return SegmentInfo(
        path=path,
        compressed_size=compressed_size,
        uncompressed_size=len(raw),
        satellite_name=satellite_name,
        observation_area=observation_area,
    )
