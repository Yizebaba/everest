"""Minimal ECMWF AIFS Single Open Data retrieval and immutable retention."""

# Provider independence deliberately keeps AIFS identity and trust checks local.
# pylint: disable=duplicate-code

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Protocol
from email.utils import parsedate_to_datetime

import requests


OFFICIAL_ROOT = "https://data.ecmwf.int/forecasts"
RAW_ROOT_ENVIRONMENT_VARIABLE = "EVEREST_RAW_ROOT"
SOURCE_ID = "ecmwf-aifs"
MODEL = "AIFS"
PROVIDER_MODEL = "aifs-single"
DEFAULT_PARAMETERS = ("z", "10u", "10v", "2t", "tp")
AOI_ID = "everest-south-route"
AOI_VERSION = "everest-south-route-v1.0"
AOI_SCOPE_ID = "everest-south-route-v1.0-default-100km"
EVEREST_LATITUDE = 27.98806
EVEREST_LONGITUDE = 86.92528


class HttpSession(Protocol):  # pylint: disable=too-few-public-methods
    """Minimal injectable HTTP session used by the connector."""

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Issue one HTTP GET request."""


class RawStorageConfigurationError(ValueError):
    """Raised when external AIFS raw storage is not safely configured."""


@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class RawRetrieval:  # pylint: disable=too-many-instance-attributes
    """Retained AIFS payload and immutable provenance references."""

    payload_path: Path
    metadata_path: Path
    url: str
    index_url: str
    sha256: str
    size_bytes: int
    cycle: datetime
    lead_hours: int
    parameters: tuple[str, ...]


class EcmwfAifsConnector:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Retrieve selected AIFS Single GRIB2 messages from official open data."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        session: HttpSession | None = None,
        timeout_seconds: float = 30.0,
        retry_limit: int = 2,
        backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        retry_after_max_seconds: float = 60.0,
        test_raw_root: Path | None = None,
        environment: dict[str, str] | None = None,
        repository_root: Path | None = None,
    ) -> None:
        """Initialize bounded transport and required external raw storage."""
        self.raw_root = self._configured_raw_root(
            test_raw_root, environment, repository_root
        )
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.retry_limit = retry_limit
        self.backoff_seconds = backoff_seconds
        self._sleep = sleep
        self._now = now
        self.retry_after_max_seconds = retry_after_max_seconds

    def retrieve(
        self,
        cycle: datetime,
        lead_hours: int = 0,
        parameters: tuple[str, ...] = DEFAULT_PARAMETERS,
    ) -> RawRetrieval:
        """Retrieve selected ranges and retain exact GRIB2 bytes."""
        cycle = _utc_cycle(cycle)
        _validate_request(cycle, lead_hours, parameters)
        url, index_url, filename = self._urls(cycle, lead_hours)
        rows = self._index_rows(index_url)
        selected = self._selected_ranges(rows, parameters)
        payload = b"".join(
            self._range(url, row["_offset"], row["_length"]) for row in selected
        )
        if not payload.startswith(b"GRIB"):
            raise ValueError("AIFS selected response is not GRIB2")
        digest = _sha256(payload)
        artifact_dir = self.raw_root / SOURCE_ID / digest
        artifact_dir.mkdir(parents=True, exist_ok=True)
        payload_path = artifact_dir / filename
        self._write_verified(payload_path, payload, digest)
        metadata_path = artifact_dir / "metadata.json"
        metadata = self._metadata(
            cycle,
            lead_hours,
            url,
            index_url,
            selected,
            payload,
            digest,
        )
        self._write_metadata(metadata_path, metadata)
        return RawRetrieval(
            payload_path=payload_path,
            metadata_path=metadata_path,
            url=url,
            index_url=index_url,
            sha256=digest,
            size_bytes=len(payload),
            cycle=cycle,
            lead_hours=lead_hours,
            parameters=tuple(row["param"] for row in selected),
        )

    @staticmethod
    def _urls(cycle: datetime, lead_hours: int) -> tuple[str, str, str]:
        """Build current official AIFS Single open-data object URLs."""
        directory = (
            f"{OFFICIAL_ROOT}/{cycle:%Y%m%d}/{cycle:%Hz}/"
            "aifs-single/0p25/oper"
        )
        filename = f"{cycle:%Y%m%d%H%M%S}-{lead_hours}h-oper-fc.grib2"
        return (
            f"{directory}/{filename}",
            f"{directory}/{filename[:-6]}.index",
            filename,
        )

    def _index_rows(self, url: str) -> list[dict[str, Any]]:
        """Read the official newline-delimited JSON field index."""
        response = self._request(url)
        try:
            rows = [
                json.loads(line)
                for line in response.text.splitlines()
                if line.strip()
            ]
        except json.JSONDecodeError as error:
            raise ValueError("AIFS index is not JSON Lines") from error
        if not rows or not all(isinstance(row, dict) for row in rows):
            raise ValueError("AIFS index is empty or malformed")
        return rows

    @staticmethod
    def _selected_ranges(
        rows: list[dict[str, Any]], parameters: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        """Select exactly one surface AIFS Single range per requested field."""
        selected: list[dict[str, Any]] = []
        for parameter in parameters:
            matches = [
                row
                for row in rows
                if row.get("param") == parameter
                and row.get("levtype") == "sfc"
                and row.get("model") == PROVIDER_MODEL
                and row.get("class") == "ai"
                and row.get("stream") == "oper"
                and row.get("type") == "fc"
                and row.get("_offset").__class__ is int
                and row.get("_length").__class__ is int
                and row["_offset"] >= 0
                and row["_length"] >= 224
            ]
            if len(matches) != 1:
                raise ValueError(
                    "AIFS index must contain exactly one requested surface "
                    f"message for {parameter}"
                )
            selected.append(matches[0])
        return selected

    def _range(self, url: str, offset: int, length: int) -> bytes:
        """Retrieve one exact HTTP 206 byte range, never a full object."""
        end = offset + length - 1
        response = self._request(
            url, headers={"Range": f"bytes={offset}-{end}"}
        )
        if response.status_code != 206:
            raise ValueError("AIFS range request did not return HTTP 206")
        if not response.headers.get("Content-Range", "").startswith(
            f"bytes {offset}-{end}/"
        ):
            raise ValueError("AIFS range response has invalid Content-Range")
        if len(response.content) != length:
            raise ValueError("AIFS range response has unexpected byte length")
        return response.content

    def _request(self, url: str, **kwargs: Any) -> requests.Response:
        """Apply bounded exponential retry to transport/server failures."""
        for attempt in range(self.retry_limit + 1):
            try:
                response = self.session.get(
                    url, timeout=self.timeout_seconds, **kwargs
                )
                if response.status_code == 429:
                    delay = _retry_after_delay(
                        response.headers.get("Retry-After"),
                        self._now(),
                        self.retry_after_max_seconds,
                    )
                    if attempt == self.retry_limit:
                        response.raise_for_status()
                    self._sleep(delay)
                    continue
                response.raise_for_status()
                return response
            except (requests.RequestException, OSError):
                if attempt == self.retry_limit:
                    raise
                self._sleep(self.backoff_seconds * (2**attempt))
        raise RuntimeError("unreachable AIFS retry state")

    def _write_verified(self, path: Path, payload: bytes, digest: str) -> None:
        """Atomically fsync and rehash one content-addressed object."""
        path = self._contained(path)
        if path.exists():
            if _sha256(path.read_bytes()) != digest:
                raise ValueError("existing AIFS artifact checksum mismatch")
            return
        descriptor, name = tempfile.mkstemp(dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if _sha256(temporary.read_bytes()) != digest:
                raise ValueError("persisted AIFS artifact checksum mismatch")
            os.replace(temporary, path)
            _make_read_only(path)
        finally:
            temporary.unlink(missing_ok=True)

    def _write_metadata(self, path: Path, metadata: dict[str, Any]) -> None:
        """Retain canonical metadata and its mandatory digest sidecar."""
        encoded = _canonical_json(metadata)
        digest = _sha256(encoded)
        sidecar = path.with_name(f"{path.name}.sha256")
        if path.exists() or sidecar.exists():
            self._verify_metadata(path, sidecar, metadata)
            return
        self._write_verified(path, encoded, digest)
        declaration = f"{digest}\n".encode("ascii")
        self._write_verified(sidecar, declaration, _sha256(declaration))

    def _verify_metadata(
        self, path: Path, sidecar: Path, expected: dict[str, Any]
    ) -> None:
        """Reject missing, changed, noncanonical, or inconsistent sidecars."""
        path = self._contained(path)
        sidecar = self._contained(sidecar)
        if not path.is_file() or not sidecar.is_file():
            raise ValueError("AIFS metadata or checksum sidecar is missing")
        encoded = path.read_bytes()
        declaration = sidecar.read_bytes()
        actual_digest = _sha256(encoded)
        if declaration != f"{actual_digest}\n".encode("ascii"):
            raise ValueError("AIFS metadata sidecar is inconsistent")
        try:
            parsed = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("AIFS metadata is not UTF-8 JSON") from error
        if not isinstance(parsed, dict) or _canonical_json(parsed) != encoded:
            raise ValueError("AIFS metadata is not canonical JSON")
        actual_without_time = dict(parsed)
        expected_without_time = dict(expected)
        actual_without_time.pop("retrieved_at", None)
        expected_without_time.pop("retrieved_at", None)
        if actual_without_time != expected_without_time:
            raise ValueError("AIFS metadata provenance mismatch")

    def _contained(self, path: Path) -> Path:
        """Resolve one object strictly beneath the approved external root."""
        resolved = path.resolve()
        if not resolved.is_relative_to(self.raw_root):
            raise ValueError("AIFS object reference escapes raw root")
        return resolved

    @staticmethod
    def _configured_raw_root(
        test_raw_root: Path | None,
        environment: dict[str, str] | None,
        repository_root: Path | None,
    ) -> Path:
        """Require an existing absolute external EVEREST_RAW_ROOT."""
        values = os.environ if environment is None else environment
        configured = (
            str(test_raw_root)
            if test_raw_root is not None
            else values.get(RAW_ROOT_ENVIRONMENT_VARIABLE)
        )
        if not configured:
            raise RawStorageConfigurationError(
                f"{RAW_ROOT_ENVIRONMENT_VARIABLE} must be configured"
            )
        raw_root = Path(configured)
        project_root = repository_root or Path(__file__).resolve().parents[3]
        if not raw_root.is_absolute() or not project_root.is_absolute():
            raise RawStorageConfigurationError(
                "AIFS raw and repository roots must be absolute"
            )
        raw_root = raw_root.resolve()
        project_root = project_root.resolve()
        if not raw_root.is_dir():
            raise RawStorageConfigurationError(
                "AIFS raw root must be an existing directory"
            )
        if raw_root.is_relative_to(project_root):
            raise RawStorageConfigurationError(
                "AIFS raw root must be outside the repository"
            )
        return raw_root

    @staticmethod
    # Each range and retention fact is explicit at this integrity boundary.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def _metadata(
        cycle: datetime,
        lead_hours: int,
        url: str,
        index_url: str,
        selected: list[dict[str, Any]],
        payload: bytes,
        digest: str,
    ) -> dict[str, Any]:
        """Build complete factual AIFS acquisition metadata."""
        valid_time = cycle + timedelta(hours=lead_hours)
        return {
            "source": SOURCE_ID,
            "provider": "ECMWF",
            "dataset": "AIFS Single",
            "model": MODEL,
            "provider_model": PROVIDER_MODEL,
            "aifs_version": "2",
            "cycle": cycle.isoformat(),
            "lead_hours": lead_hours,
            "valid_time": valid_time.isoformat(),
            "url": url,
            "index_url": index_url,
            "format": "GRIB2",
            "parameters": [row["param"] for row in selected],
            "ranges": [
                {
                    "offset": row["_offset"],
                    "length": row["_length"],
                    "parameter": row["param"],
                }
                for row in selected
            ],
            "aoi_id": AOI_ID,
            "aoi_version": AOI_VERSION,
            "aoi_scope_id": AOI_SCOPE_ID,
            "requested_coordinate": [EVEREST_LATITUDE, EVEREST_LONGITUDE],
            "size_bytes": len(payload),
            "sha256": digest,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }


def _utc_cycle(cycle: datetime) -> datetime:
    """Require an aware forecast cycle and normalize it to UTC."""
    if cycle.tzinfo is None:
        raise ValueError("AIFS cycle must be timezone-aware")
    return cycle.astimezone(timezone.utc)


def _retry_after_delay(
    value: str | None, now: datetime, maximum: float
) -> float:
    """Parse RFC 9110 Retry-After and enforce the connector's hard bound.

    Delta-seconds are preferred. IMF-fixdate is accepted for interoperability;
    its reference time is injected so tests never depend on wall-clock time.
    Invalid or over-limit provider values fail closed instead of being guessed.
    """
    if value is None or not value.strip():
        raise ValueError("AIFS HTTP 429 requires a valid Retry-After header")
    candidate = value.strip()
    if candidate.isascii() and candidate.isdigit():
        delay = float(candidate)
    else:
        try:
            retry_at = parsedate_to_datetime(candidate)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("AIFS Retry-After is malformed") from error
        if retry_at is None or retry_at.tzinfo is None:
            raise ValueError("AIFS Retry-After date is malformed")
        if now.tzinfo is None:
            raise ValueError("AIFS retry clock must be timezone-aware")
        delay = max(
            0.0, (retry_at - now.astimezone(timezone.utc)).total_seconds()
        )
    if delay > maximum:
        raise ValueError("AIFS Retry-After exceeds connector maximum")
    return delay


def _validate_request(
    cycle: datetime, lead_hours: int, parameters: tuple[str, ...]
) -> None:
    """Validate current AIFS Single cycle, step, and approved fields."""
    if cycle.hour not in (0, 6, 12, 18) or cycle.minute or cycle.second:
        raise ValueError("AIFS cycle must be 00, 06, 12, or 18 UTC")
    if lead_hours < 0 or lead_hours > 360 or lead_hours % 6:
        raise ValueError("AIFS lead must be 0..360 hours in 6-hour steps")
    if not parameters or len(set(parameters)) != len(parameters):
        raise ValueError("AIFS parameters must be nonempty and unique")
    if any(parameter not in DEFAULT_PARAMETERS for parameter in parameters):
        raise ValueError("AIFS parameter is outside the approved minimal set")


def _canonical_json(value: dict[str, Any]) -> bytes:
    """Serialize deterministic UTF-8 JSON for integrity checks."""
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    """Return SHA-256 for exact bytes."""
    return hashlib.sha256(value).hexdigest()


def _make_read_only(path: Path) -> None:
    """Set a best-effort read-only bit; storage ACLs remain external."""
    try:
        path.chmod(0o444)
    except OSError:
        pass
