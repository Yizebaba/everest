"""GLO-30 terrain parser: read a COG GeoTIFF tile with rasterio."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import rasterio


@dataclass(frozen=True)
class ParsedTile:
    """Parsed DEM tile metadata and the elevation array."""

    path: Path
    crs: str
    bounds: tuple[float, float, float, float]
    width: int
    height: int
    resolution: tuple[float, float]
    dtype: str
    nodata: float | None
    elevation: np.ndarray = field(repr=False)


def parse_tile(path: Path) -> ParsedTile:
    """Parse a GLO-30 COG tile into metadata plus the raw elevation array."""
    with rasterio.open(str(path)) as dataset:
        if dataset.count != 1:
            raise ValueError(f"unexpected band count: {dataset.count}")
        elevation = dataset.read(1)
        return ParsedTile(
            path=path,
            crs=str(dataset.crs),
            bounds=tuple(dataset.bounds),
            width=dataset.width,
            height=dataset.height,
            resolution=tuple(dataset.res),
            dtype=dataset.dtypes[0],
            nodata=dataset.nodata,
            elevation=elevation,
        )
