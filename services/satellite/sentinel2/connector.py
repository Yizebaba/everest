"""Sentinel-2 L1C connector: AWS public bucket, AOI-window read (EV-SAT-002)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds

_WGS84 = CRS.from_epsg(4326)

BUCKET = "sentinel-s2-l1c"
BUCKET_BASE = f"https://{BUCKET}.s3.amazonaws.com"

# True-colour bands (Sentinel-2 L1C): B04=red, B03=green, B02=blue.
RGB_BANDS = (4, 3, 2)


@dataclass(frozen=True)
class Sentinel2Scene:
    """Identity and location of one Sentinel-2 L1C tile."""

    utm_zone: str  # e.g. "45R"
    latitude_band: str  # e.g. "VK"
    date: str  # YYYY/MM/DD
    num: str  # grid number (0/1)
    crs: str  # e.g. EPSG:32645

    @property
    def prefix(self) -> str:
        """Return the S3 key prefix (no leading slash)."""
        return f"tiles/{self.utm_zone}/{self.latitude_band}/{self.date}/{self.num}"

    def band_url(self, band: int) -> str:
        """Return the official public URL for one band JPEG2000."""
        return f"{BUCKET_BASE}/{self.prefix}/B{band:02d}.jp2"


def _read_band_window(
    url: str, bounds: tuple[float, float, float, float], out_shape: tuple[int, int]
) -> np.ndarray:
    """Read one band clipped to a lon/lat window.

    ``url`` may be a remote vsicurl URL or a local file path. ``bounds`` are
    WGS84 (west, south, east, north); rasterio reprojects the requested
    geographic window to the band's CRS and reads only that region.
    """
    with rasterio.open(url) as ds:
        # Convert WGS84 bounds into the band CRS (UTM) and read that window.
        crs_bounds = transform_bounds(_WGS84, ds.crs, *bounds)
        window = from_bounds(*crs_bounds, transform=ds.transform)
        src = ds.read(1, window=window)
        # Reproject the UTM window into a WGS84 grid aligned to `bounds`
        # so the output is georeferenced in lon/lat.
        dst = np.empty(out_shape, dtype="float32")
        reproject(
            source=src,
            destination=dst,
            src_transform=rasterio.windows.transform(window, ds.transform),
            src_crs=ds.crs,
            dst_crs=_WGS84,
            dst_transform=rasterio.transform.from_bounds(*bounds, *out_shape),
            resampling=Resampling.bilinear,
        )
        return dst


def _scale_uint8(band: np.ndarray) -> np.ndarray:
    """Normalize a reflectance/radiance band to 8-bit for display (2-98th percentile)."""
    finite = band[np.isfinite(band)]
    if finite.size == 0:
        return np.zeros(band.shape, dtype=np.uint8)
    low, high = np.percentile(finite, (2, 98))
    if high <= low:
        high = low + 1.0
    scaled = np.clip((band - low) / (high - low) * 255, 0, 255)
    return scaled.astype(np.uint8)


@dataclass(frozen=True)
class RgbScene:
    """Synthesized true-colour RGB image and provenance."""

    scene: Sentinel2Scene
    timestamp: datetime
    rgb: np.ndarray  # (height, width, 3) uint8
    width: int
    height: int
    sha256: str


def build_rgb(
    scene: Sentinel2Scene,
    bounds: tuple[float, float, float, float],
    out_shape: tuple[int, int] = (512, 512),
    band_files: dict[int, str] | None = None,
) -> RgbScene:
    """Read B04/B03/B02 in the AOI window and synthesize true-colour RGB.

    ``band_files`` optionally maps band number -> local path (or vsicurl URL).
    When absent, official S3 URLs are used.
    """
    channels = []
    for b in RGB_BANDS:
        source = band_files[b] if band_files and b in band_files else scene.band_url(b)
        channels.append(_read_band_window(source, bounds, out_shape))
    rgb = np.dstack([_scale_uint8(ch) for ch in channels])
    encoded = rgb.tobytes()
    digest = hashlib.sha256(encoded).hexdigest()
    timestamp = datetime.now(timezone.utc)
    return RgbScene(
        scene=scene,
        timestamp=timestamp,
        rgb=rgb,
        width=out_shape[1],
        height=out_shape[0],
        sha256=digest,
    )


def write_png(rgb: np.ndarray, destination: Path) -> None:
    """Persist the synthesized RGB image as an 8-bit PNG."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image  # imported lazily to keep connector import-light

    Image.fromarray(rgb, mode="RGB").save(destination, format="PNG")


def summarize(scene: Sentinel2Scene, rgb: RgbScene) -> list[str]:
    """Return human-readable summary lines for QC/reporting."""
    return [
        f"sentinel2 scene: {scene.prefix}",
        f"crs: {scene.crs}",
        f"bands: {','.join(f'B{b}' for b in RGB_BANDS)}",
        f"rgb: {rgb.width}x{rgb.height}",
        f"sha256: {rgb.sha256[:16]}...",
    ]
