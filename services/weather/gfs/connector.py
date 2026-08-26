"""Retrieve a minimal NOAA NOMADS GFS GRIB2 subset."""

# Provider-specific retrieval repeats the accepted ECMWF trust boundary.
# pylint: disable=duplicate-code

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Protocol

import requests


OFFICIAL_ROOT = "https://nomads.ncep.noaa.gov"
DEFAULT_VARIABLES = ("TMP", "UGRD", "VGRD", "OROG", "VIS", "APCP")
DEFAULT_MESSAGES = (
    ("HGT", "surface"),
    ("TMP", "2 m above ground"),
    ("UGRD", "10 m above ground"),
    ("VGRD", "10 m above ground"),
    ("VIS", "surface"),
    ("APCP", "surface"),
)


class HttpSession(Protocol):  # pylint: disable=too-few-public-methods
    """Minimal injectable HTTP session."""

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Issue an HTTP GET request."""


@dataclass(frozen=True)
class RawRetrieval:  # pylint: disable=too-many-instance-attributes
    """Content-addressed GFS artifact and immutable retrieval metadata."""

    payload_path: Path
    metadata_path: Path
    url: str
    sha256: str
    size_bytes: int
    cycle: datetime
    lead_hours: int


class GfsNcepConnector:  # pylint: disable=too-few-public-methods
    """Download a small, official NOAA/NCEP GFS filter result."""

    def __init__(
        # Injectable retry dependencies are intentional for deterministic tests.
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        raw_root: Path,
        session: HttpSession | None = None,
        timeout_seconds: float = 60.0,
        retry_limit: int = 2,
        backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize transport and deterministic retry dependencies."""
        self.raw_root = raw_root
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.retry_limit = retry_limit
        self.backoff_seconds = backoff_seconds
        self._sleep = sleep

    def retrieve(
        self,
        cycle: datetime,
        lead_hours: int = 0,
        file_name: str | None = None,
    ) -> RawRetrieval:
        """Retrieve, checksum, and retain indexed GFS messages."""
        # URL query construction and artifact metadata are one transaction.
        # pylint: disable=too-many-locals
        cycle = cycle.astimezone(timezone.utc)
        if cycle.hour not in (0, 6, 12, 18):
            raise ValueError("GFS cycle must be 00, 06, 12, or 18 UTC")
        if lead_hours < 0:
            raise ValueError("GFS lead must not be negative")
        directory = f"/pub/data/nccf/com/gfs/prod/gfs.{cycle:%Y%m%d/%H}/atmos/"
        file_name = (
            file_name or f"gfs.t{cycle:%H}z.pgrb2.0p25.f{lead_hours:03d}"
        )
        url = f"{OFFICIAL_ROOT}{directory}{file_name}"
        index_url = f"{url}.idx"
        index_response = self._request(index_url)
        selections = self._select_index_ranges(
            index_response.text, DEFAULT_MESSAGES
        )
        payload = b"".join(
            self._get_range(url, start, end) for start, end in selections
        )
        if not payload.startswith(b"GRIB"):
            raise ValueError("NOAA response is not a GRIB2 payload")
        digest = hashlib.sha256(payload).hexdigest()
        artifact_dir = self.raw_root / "noaa-gfs" / digest
        artifact_dir.mkdir(parents=True, exist_ok=True)
        payload_path = artifact_dir / f"{file_name}.grib2"
        self._write_verified(payload_path, payload, digest)
        metadata = {
            "source": "noaa-gfs",
            "provider": "NOAA/NCEP",
            "dataset": "GFS pgrb2.0p25",
            "model": "GFS",
            "cycle": cycle.isoformat(),
            "lead_hours": lead_hours,
            "valid_time": (cycle.timestamp() + lead_hours * 3600),
            "url": url,
            "index_url": index_url,
            "format": "GRIB2",
            "variables": ["HGT", "TMP", "UGRD", "VGRD", "VIS", "APCP"],
            "messages": [list(item) for item in DEFAULT_MESSAGES],
            "requested_coordinate": [27.9881, 86.9250],
            "size_bytes": len(payload),
            "sha256": digest,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
        metadata_path = artifact_dir / "metadata.json"
        self._write_metadata(metadata_path, metadata)
        return RawRetrieval(
            payload_path,
            metadata_path,
            url,
            digest,
            len(payload),
            cycle,
            lead_hours,
        )

    @staticmethod
    def _select_index_ranges(
        index_text: str, messages: tuple[tuple[str, str], ...]
    ) -> list[tuple[int, int]]:
        """Select GRIB messages and infer ends from subsequent offsets."""
        rows: list[tuple[int, str, str]] = []
        for line in index_text.splitlines():
            parts = line.split(":")
            if len(parts) < 5:
                continue
            try:
                rows.append((int(parts[1]), parts[3], parts[4]))
            except ValueError:
                continue
        selected: list[tuple[int, int]] = []
        for parameter, level in messages:
            matches = [
                index
                for index, item in enumerate(rows)
                if item[1] == parameter and item[2] == level
            ]
            if not matches:
                raise ValueError(f"GFS index lacks {parameter}/{level}")
            position = matches[0]
            start = rows[position][0]
            end = (
                rows[position + 1][0] - 1 if position + 1 < len(rows) else None
            )
            if end is None:
                raise ValueError("GFS index lacks terminal message length")
            selected.append((start, end))
        return selected

    def _get_range(self, url: str, start: int, end: int) -> bytes:
        """Download one exact HTTP byte range and reject full-file responses."""
        response = self._request(url, headers={"Range": f"bytes={start}-{end}"})
        expected = f"bytes {start}-{end}/"
        if response.status_code != 206:
            raise ValueError("GFS range request did not return HTTP 206")
        if not response.headers.get("Content-Range", "").startswith(expected):
            raise ValueError("GFS range response has invalid Content-Range")
        if len(response.content) != end - start + 1:
            raise ValueError("GFS range response has unexpected byte length")
        return response.content

    def _request(self, url: str, **kwargs: Any) -> requests.Response:
        """Perform bounded retries for transport and HTTP failures."""
        for attempt in range(self.retry_limit + 1):
            try:
                response = self.session.get(
                    url, timeout=self.timeout_seconds, **kwargs
                )
                response.raise_for_status()
                return response
            except (requests.RequestException, OSError):
                if attempt == self.retry_limit:
                    raise
                self._sleep(self.backoff_seconds * (2**attempt))
        raise RuntimeError("unreachable retry state")

    @staticmethod
    def _sha256(payload: bytes) -> str:
        """Return the SHA-256 digest of payload bytes."""
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _write_verified(path: Path, payload: bytes, digest: str) -> None:
        """Atomically write bytes and verify the persisted checksum."""
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("existing GFS artifact checksum mismatch")
            return
        descriptor, temporary_name = tempfile.mkstemp(dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            with open(descriptor, "wb", closefd=True) as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if (
                hashlib.sha256(temporary_path.read_bytes()).hexdigest()
                != digest
            ):
                raise ValueError("persisted GFS artifact checksum mismatch")
            temporary_path.replace(path)
            try:
                path.chmod(0o444)
            except OSError:
                pass
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def _write_metadata(self, path: Path, metadata: dict[str, Any]) -> None:
        """Write canonical metadata and verify every content-addressed reuse."""
        sidecar = path.with_name(f"{path.name}.sha256")
        if path.exists() or sidecar.exists():
            self._verify_metadata(path, sidecar, metadata)
            return
        encoded = self._canonical_json(metadata)
        digest = self._sha256(encoded)
        self._write_verified(path, encoded, digest)
        self._write_verified(
            sidecar,
            f"{digest}\n".encode("ascii"),
            self._sha256(f"{digest}\n".encode("ascii")),
        )

    @staticmethod
    def _canonical_json(metadata: dict[str, Any]) -> bytes:
        """Serialize metadata deterministically as UTF-8 JSON."""
        return (
            json.dumps(
                metadata,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

    def _verify_metadata(
        self, path: Path, sidecar: Path, expected: dict[str, Any]
    ) -> None:
        """Reject missing, tampered, or noncanonical metadata on reuse."""
        if not path.exists() or not sidecar.exists():
            raise ValueError("GFS metadata or checksum sidecar is missing")
        encoded = path.read_bytes()
        recorded_digest = sidecar.read_text(encoding="ascii").strip()
        if self._sha256(encoded) != recorded_digest:
            raise ValueError("GFS metadata checksum mismatch")
        try:
            actual = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("GFS metadata is not valid UTF-8 JSON") from error
        if (
            not isinstance(actual, dict)
            or self._canonical_json(actual) != encoded
        ):
            raise ValueError("GFS metadata is not canonical deterministic JSON")
        stable_expected = dict(expected)
        stable_actual = dict(actual)
        stable_expected.pop("retrieved_at", None)
        stable_actual.pop("retrieved_at", None)
        if stable_actual != stable_expected:
            raise ValueError("GFS metadata provenance mismatch")
