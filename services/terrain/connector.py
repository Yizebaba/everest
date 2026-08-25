"""GLO-30 terrain connector: retrieve Copernicus DEM tiles from AWS Open Data."""

from __future__ import annotations

import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path

BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"


@dataclass(frozen=True)
class TerrainTileRef:
    """Identity of one GLO-30 tile (1x1 degree)."""

    tile_name: str

    def object_key(self) -> str:
        """Return the S3 object key for this tile."""
        return f"{self.tile_name}/{self.tile_name}.tif"

    def url(self) -> str:
        """Return the official public URL for this tile."""
        return f"{BASE_URL}/{self.object_key()}"


def tile_for_lat_lon(latitude: float, longitude: float) -> TerrainTileRef:
    """Return the 1-degree GLO-30 tile covering the given coordinate.

    GLO-30 tiles are named Copernicus_DSM_COG_10_Nxx_00_Exxx_00_DEM.
    """
    lat_ns = "N" if latitude >= 0 else "S"
    lon_ew = "E" if longitude >= 0 else "W"
    lat_deg = int(abs(latitude))
    lon_deg = int(abs(longitude))
    name = (
        f"Copernicus_DSM_COG_10_{lat_ns}{lat_deg:02d}_00_"
        f"{lon_ew}{lon_deg:03d}_00_DEM"
    )
    return TerrainTileRef(name)


def sha256_of(path: Path) -> str:
    """Return the SHA-256 of a file, chunked for large files."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_tile(
    tile: TerrainTileRef, destination: Path, timeout: int = 300
) -> tuple[Path, str]:
    """Download a GLO-30 tile to destination; return (path, sha256).

    Downloads to a temporary ``.part`` file and atomically renames it so a
    truncated download is never reused as if complete.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        part = destination.with_suffix(destination.suffix + ".part")
        with urllib.request.urlopen(tile.url(), timeout=timeout) as response:
            with part.open("wb") as out:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
        part.replace(destination)
    return destination, sha256_of(destination)
