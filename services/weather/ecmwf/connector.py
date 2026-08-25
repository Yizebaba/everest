"""Retrieval of minimal ECMWF IFS Open Data GRIB2 samples."""

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


OFFICIAL_ROOT = "https://data.ecmwf.int/forecasts"
DEFAULT_PARAMETERS = ("z", "10u", "10v", "2t", "tp")


class HttpSession(Protocol):  # pylint: disable=too-few-public-methods
    """Minimal HTTP dependency required by the connector."""

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Issue one HTTP GET request."""


@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class RawRetrieval:  # pylint: disable=too-many-instance-attributes
    """Immutable raw artifact and its source metadata."""

    payload_path: Path
    metadata_path: Path
    url: str
    index_url: str
    checksum_sha256: str
    size_bytes: int
    cycle: datetime
    lead_hours: int


class EcmwfOpenDataConnector:  # pylint: disable=too-few-public-methods
    """Download a small, index-selected IFS GRIB2 artifact."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        raw_root: Path,
        session: HttpSession | None = None,
        timeout_seconds: float = 30.0,
        retry_limit: int = 2,
        backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize injectable transport and backoff dependencies."""
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
        parameters: tuple[str, ...] = DEFAULT_PARAMETERS,
    ) -> RawRetrieval:
        """Retrieve, verify, and retain index-selected IFS messages."""
        cycle = cycle.astimezone(timezone.utc)
        url, index_url, filename = self._urls(cycle, lead_hours)
        rows = self._get_json_lines(index_url)
        ranges = self._select_ranges(rows, parameters)
        payload = b"".join(
            self._get_range(url, row["_offset"], row["_length"])
            for row in ranges
        )
        digest = self._sha256(payload)
        artifact_dir = self.raw_root / "ecmwf-ifs" / digest
        artifact_dir.mkdir(parents=True, exist_ok=True)
        payload_path = artifact_dir / filename
        self._write_verified(payload_path, payload, digest)
        metadata_path = artifact_dir / "metadata.json"
        self._write_metadata(
            metadata_path,
            self._metadata(
                cycle, lead_hours, url, index_url, ranges, payload, digest
            ),
        )
        return RawRetrieval(
            payload_path,
            metadata_path,
            url,
            index_url,
            digest,
            len(payload),
            cycle,
            lead_hours,
        )

    @staticmethod
    def _urls(cycle: datetime, lead_hours: int) -> tuple[str, str, str]:
        """Build the official IFS operational GRIB2 and index URLs."""
        directory = f"{OFFICIAL_ROOT}/{cycle:%Y%m%d}/{cycle:%Hz}/ifs/0p25/oper"
        filename = f"{cycle:%Y%m%d%H%M%S}-{lead_hours}h-oper-fc.grib2"
        return (
            f"{directory}/{filename}",
            f"{directory}/{filename[:-6]}.index",
            filename,
        )

    @staticmethod
    def _select_ranges(
        rows: list[dict[str, Any]], parameters: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        """Select requested surface messages from the official index."""
        ranges = [
            row
            for row in rows
            if row.get("param") in parameters
            and row.get("levtype") == "sfc"
            and isinstance(row.get("_offset"), int)
            and isinstance(row.get("_length"), int)
            and row["_length"] > 224
        ]
        if not ranges:
            raise ValueError("IFS index contains no requested surface messages")
        return ranges

    def _get_json_lines(self, url: str) -> list[dict[str, Any]]:
        """Request and parse the official newline-delimited JSON index."""
        response = self._request(url)
        try:
            return [
                json.loads(line) for line in response.text.splitlines() if line
            ]
        except json.JSONDecodeError as error:
            raise ValueError(
                "IFS index is not valid newline-delimited JSON"
            ) from error

    def _get_range(self, url: str, offset: int, length: int) -> bytes:
        """Request one validated HTTP byte range, never a full response."""
        end = offset + length - 1
        response = self._request(
            url, headers={"Range": f"bytes={offset}-{end}"}
        )
        if response.status_code != 206:
            raise ValueError("IFS range request did not return HTTP 206")
        expected = f"bytes {offset}-{end}/"
        content_range = response.headers.get("Content-Range", "")
        if not content_range.startswith(expected):
            raise ValueError("IFS range response has invalid Content-Range")
        if len(response.content) != length:
            raise ValueError("IFS range response has unexpected byte length")
        return response.content

    def _request(self, url: str, **kwargs: Any) -> requests.Response:
        """Run a bounded retry loop for retryable transport failures."""
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

    def _write_verified(self, path: Path, payload: bytes, digest: str) -> None:
        """Atomically retain payload and rehash persisted bytes."""
        if path.exists():
            if self._sha256(path.read_bytes()) != digest:
                raise ValueError("existing raw artifact checksum mismatch")
            return
        descriptor, temporary_name = tempfile.mkstemp(dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if self._sha256(temporary_path.read_bytes()) != digest:
                raise ValueError("persisted raw artifact checksum mismatch")
            os.replace(temporary_path, path)
            self._make_read_only(path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def _write_metadata(self, path: Path, metadata: dict[str, Any]) -> None:
        """Atomically retain and verify canonical metadata with a sidecar."""
        encoded = self._canonical_json(metadata)
        digest = self._sha256(encoded)
        checksum_path = path.with_name(f"{path.name}.sha256")
        if path.exists() or checksum_path.exists():
            self._verify_metadata(path, checksum_path, digest)
            return
        self._write_verified(path, encoded, digest)
        self._write_verified(
            checksum_path,
            f"{digest}\n".encode("ascii"),
            self._sha256(f"{digest}\n".encode("ascii")),
        )

    @staticmethod
    def _canonical_json(metadata: dict[str, Any]) -> bytes:
        """Serialize metadata deterministically for integrity verification."""
        return (
            json.dumps(
                metadata,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

    def _verify_metadata(
        self, path: Path, checksum_path: Path, expected_digest: str
    ) -> None:
        """Reject missing, tampered, or inconsistent metadata artifacts."""
        if not path.exists() or not checksum_path.exists():
            raise ValueError("metadata or metadata checksum sidecar is missing")
        encoded = path.read_bytes()
        sidecar = checksum_path.read_text(encoding="ascii").strip()
        if sidecar != expected_digest:
            raise ValueError("metadata checksum sidecar is inconsistent")
        if self._sha256(encoded) != expected_digest:
            raise ValueError("metadata checksum mismatch")
        try:
            parsed = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("metadata is not valid UTF-8 JSON") from error
        if (
            not isinstance(parsed, dict)
            or self._canonical_json(parsed) != encoded
        ):
            raise ValueError("metadata is not canonical deterministic JSON")

    @staticmethod
    def _make_read_only(path: Path) -> None:
        """Set a best-effort read-only bit.

        Windows ACLs remain storage-policy owned.
        """
        try:
            path.chmod(0o444)
        except OSError:
            pass

    @staticmethod
    def _metadata(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        cycle: datetime,
        lead_hours: int,
        url: str,
        index_url: str,
        ranges: list[dict[str, Any]],
        payload: bytes,
        digest: str,
    ) -> dict[str, Any]:
        """Build immutable non-secret raw-artifact metadata."""
        return {
            "source": "ecmwf-ifs",
            "provider": "ECMWF",
            "dataset": "IFS open data",
            "model": "IFS",
            "cycle": cycle.isoformat(),
            "lead_hours": lead_hours,
            "valid_time": cycle.timestamp() + lead_hours * 3600,
            "url": url,
            "index_url": index_url,
            "format": "GRIB2",
            "parameters": [row["param"] for row in ranges],
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "size_bytes": len(payload),
            "sha256": digest,
        }
