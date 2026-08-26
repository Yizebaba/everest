"""Himawari AHI segment QC: verify identity fields and non-empty payload."""

from __future__ import annotations

from dataclasses import dataclass

from services.satellite.himawari.parser import SegmentInfo

EXPECTED_SATELLITE = "Himawari"
EXPECTED_AREAS = {"FLDK", "JP01", "TA01"}


@dataclass(frozen=True)
class HimawariQcReport:
    """QC findings for one downloaded segment."""

    band: int
    segment: int
    satellite_name: str
    observation_area: str
    flags: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """True when no blocking flags are raised."""
        return not self.flags


def run_qc(info: SegmentInfo, band: int, segment: int) -> HimawariQcReport:
    """Run QC over a parsed segment.

    Checks the satellite name, observation area, and that the payload is not
    empty. Field-level geometry verification is deferred until the official
    JMA format guide is aligned.
    """
    flags: list[str] = []
    if info.satellite_name != EXPECTED_SATELLITE:
        flags.append("unexpected_satellite")
    if info.observation_area not in EXPECTED_AREAS:
        flags.append("unexpected_observation_area")
    if info.uncompressed_size == 0:
        flags.append("empty_payload")
    return HimawariQcReport(
        band=band,
        segment=segment,
        satellite_name=info.satellite_name,
        observation_area=info.observation_area,
        flags=tuple(flags),
    )
