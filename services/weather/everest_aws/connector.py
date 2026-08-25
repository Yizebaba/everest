"""Everest AWS observation connector: retrieve station CSVs."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/G-w-e-n-d-o-l-y-n/MetData_/main"
STATIONS = ("Base Camp", "Camp 2", "South Col")


@dataclass(frozen=True)
class StationFeed:
    """One Everest AWS station CSV feed."""

    station: str

    def filename(self) -> str:
        """Return the CSV filename on the official feed repo."""
        return self.station.replace(" ", "%20") + ".csv"

    def url(self) -> str:
        """Return the official public CSV URL."""
        return f"{BASE_URL}/{self.filename()}"


def download_station(
    station: str, destination: Path, timeout: int = 120
) -> Path:
    """Download one station CSV to destination; return the path.

    Downloads to a temporary ``.part`` file and atomically renames it so a
    truncated download is never reused as if complete.
    """
    if station not in STATIONS:
        raise ValueError(f"unknown station: {station}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        part = destination.with_suffix(destination.suffix + ".part")
        with urllib.request.urlopen(
            StationFeed(station).url(), timeout=timeout
        ) as response:
            with part.open("wb") as out:
                out.write(response.read())
        part.replace(destination)
    return destination
