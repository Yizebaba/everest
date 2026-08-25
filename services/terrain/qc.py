"""GLO-30 terrain quality control: flag anomalies without deleting data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from terrain.parser import ParsedTile


@dataclass(frozen=True)
class TerrainQcReport:
    """QC findings for one parsed tile."""

    tile_name: str
    crs: str
    width: int
    height: int
    resolution: tuple[float, float]
    min_elevation: float
    max_elevation: float
    mean_elevation: float
    valid_pixels: int
    nodata_pixels: int
    flags: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """True when no blocking flags are raised."""
        return not self.flags


def _is_valid(elevation: np.ndarray, nodata: float | None) -> np.ndarray:
    if nodata is None:
        return np.isfinite(elevation)
    return np.isfinite(elevation) & (elevation != nodata)


def run_qc(parsed: ParsedTile) -> TerrainQcReport:
    """Run QC checks over a parsed tile and return findings.

    Checks: CRS is EPSG:4326; 1-degree tile size; nodata mask; finite values;
    plausible elevation range for the Everest AOI (-500 m to 9,000 m).
    """
    flags: list[str] = []
    elevation = parsed.elevation
    valid = _is_valid(elevation, parsed.nodata)
    nodata_pixels = int((~valid).sum())
    valid_values = elevation[valid]
    if parsed.crs != "EPSG:4326":
        flags.append("unexpected_crs")
    if parsed.width != 3600 or parsed.height != 3600:
        flags.append("unexpected_tile_size")
    if nodata_pixels > 0:
        flags.append("has_nodata")
    if valid_values.size == 0:
        flags.append("no_valid_pixels")
        return TerrainQcReport(
            tile_name=parsed.path.stem,
            crs=parsed.crs,
            width=parsed.width,
            height=parsed.height,
            resolution=parsed.resolution,
            min_elevation=0.0,
            max_elevation=0.0,
            mean_elevation=0.0,
            valid_pixels=0,
            nodata_pixels=nodata_pixels,
            flags=tuple(flags),
        )
    min_elevation = float(valid_values.min())
    max_elevation = float(valid_values.max())
    mean_elevation = float(valid_values.mean())
    if min_elevation < -500.0:
        flags.append("below_plausible_elevation")
    if max_elevation > 9000.0:
        flags.append("above_plausible_elevation")
    return TerrainQcReport(
        tile_name=parsed.path.stem,
        crs=parsed.crs,
        width=parsed.width,
        height=parsed.height,
        resolution=parsed.resolution,
        min_elevation=min_elevation,
        max_elevation=max_elevation,
        mean_elevation=mean_elevation,
        valid_pixels=int(valid.sum()),
        nodata_pixels=nodata_pixels,
        flags=tuple(flags),
    )


def summary_lines(report: TerrainQcReport) -> Sequence[str]:
    """Render a QC report as stable text lines for evidence logs."""
    return (
        f"tile: {report.tile_name}",
        f"crs: {report.crs} size: {report.width}x{report.height} "
        f"res: {report.resolution[0]:.7f}",
        f"elevation: min={report.min_elevation:.1f} "
        f"max={report.max_elevation:.1f} mean={report.mean_elevation:.1f}",
        f"pixels: valid={report.valid_pixels} nodata={report.nodata_pixels}",
        f"flags: {','.join(report.flags) or 'none'}",
        f"qc: {'PASS' if report.passed else 'FAIL'}",
    )
