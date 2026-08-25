"""Himawari-8/9 satellite connector: NOAA AWS S3, anonymous."""

from __future__ import annotations

import hashlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as etree
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

BUCKET = "noaa-himawari9"
BUCKET_BASE = f"https://{BUCKET}.s3.amazonaws.com"
BAND_COUNT = 16
SEGMENTS_PER_BAND = 10
_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
_SEGMENT_RE = re.compile(
    r"(HS_H\d{2}_\d{8}_\d{4}_B(\d{2})_FLDK_R\d+_S(\d{2})10\.DAT\.bz2)"
)


@dataclass(frozen=True)
class FlDkTimeSlot:
    """One full-disk AHI observation time."""

    timestamp: datetime  # UTC, must be on a 10-minute boundary

    def path_prefix(self) -> str:
        """Return the S3 key prefix for this time slot."""
        return f"AHI-L1b-FLDK/{self.timestamp:%Y/%m/%d/%H%M}"


def _list_keys(slot: FlDkTimeSlot) -> list[str]:
    """List object keys in a time slot via S3 ListObjectsV2 (public GET)."""
    query = urllib.parse.urlencode(
        {
            "list-type": "2",
            "prefix": f"{slot.path_prefix()}/",
            "max-keys": "1000",
        }
    )
    with urllib.request.urlopen(f"{BUCKET_BASE}/?{query}", timeout=120) as resp:
        root = etree.fromstring(resp.read())
    return [
        key.text or "" for key in root.findall(".//s3:Contents/s3:Key", _NS)
    ]


def segment_filename(slot: FlDkTimeSlot, band: int, segment: int) -> str:
    """Discover the exact object name for one band segment.

    The AHI 'R' code in the name is band-dependent (e.g. R10 for visible,
    R05 for others), so the name is discovered from the slot listing rather
    than guessed.
    """
    if not 1 <= band <= BAND_COUNT:
        raise ValueError(f"invalid band: {band}")
    if not 1 <= segment <= SEGMENTS_PER_BAND:
        raise ValueError(f"invalid segment: {segment}")
    for key in _list_keys(slot):
        filename = key.rsplit("/", 1)[-1]
        match = _SEGMENT_RE.fullmatch(filename)
        if (
            match
            and match.group(2) == f"{band:02d}"
            and match.group(3) == f"{segment:02d}"
        ):
            return filename
    raise FileNotFoundError(
        f"no segment band={band} segment={segment} in {slot.path_prefix()}"
    )


def segment_key(slot: FlDkTimeSlot, band: int, segment: int) -> str:
    """Return the S3 object key for one band segment."""
    return f"{slot.path_prefix()}/{segment_filename(slot, band, segment)}"


def segment_url(slot: FlDkTimeSlot, band: int, segment: int) -> str:
    """Return the official public URL for one band segment."""
    return f"{BUCKET_BASE}/{segment_key(slot, band, segment)}"


def latest_ten_minute_slot() -> FlDkTimeSlot:
    """Return a recent 10-minute boundary UTC time slot.

    Data has ~10-20 minute latency, so step back 20 minutes to a slot that is
    virtually guaranteed to exist.
    """
    now = datetime.now(timezone.utc)
    minute = now.minute - (now.minute % 10)
    slot = now.replace(minute=minute, second=0, microsecond=0)
    return FlDkTimeSlot(slot - timedelta(minutes=20))


def download_segment(
    slot: FlDkTimeSlot, band: int, segment: int, destination: Path
) -> tuple[Path, str]:
    """Download one bz2-compressed band segment; return (path, sha256).

    Downloads to a temporary ``.part`` file and atomically renames it so a
    truncated download is never reused as if complete.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        part = destination.with_suffix(destination.suffix + ".part")
        with urllib.request.urlopen(
            segment_url(slot, band, segment), timeout=120
        ) as response:
            with part.open("wb") as out:
                out.write(response.read())
        part.replace(destination)
    return destination, sha256_of(destination)


def sha256_of(path: Path) -> str:
    """Return the SHA-256 of a file, chunked for large files."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
