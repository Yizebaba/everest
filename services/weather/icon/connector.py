"""Retrieve minimal, official DWD ICON GRIB2 variable products."""

# The native global ICON grid has no published HTTP message index.  DWD serves
# individually compressed variable products, so each requested product is the
# smallest factual official object available through this route.
# pylint: disable=duplicate-code

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import bz2
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Protocol
from urllib.parse import urljoin

import requests


OFFICIAL_ROOT = "https://opendata.dwd.de/weather/nwp/icon/grib"
REQUESTED_FIELDS = ("T_2M", "U_10M", "V_10M", "HSURF", "CLAT", "CLON")
TIME_INVARIANT_FIELDS = ("HSURF", "CLAT", "CLON")
RAW_ROOT_ENVIRONMENT_VARIABLE = "EVEREST_RAW_ROOT"
AOI_ID = "everest-south-route"
AOI_VERSION = "everest-south-route-v1.0"
AOI_SCOPE_ID = "everest-south-route-v1.0-expanded-2000km"
EVEREST_LATITUDE = 27.98806
EVEREST_LONGITUDE = 86.92528


class _HrefParser(HTMLParser):
    """Extract literal directory href values from a DWD directory listing."""

    def __init__(self) -> None:
        """Initialize the empty href collection."""
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        """Retain hrefs from anchor tags only."""
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value is not None:
                self.hrefs.append(value)


class RawStorageConfigurationError(ValueError):
    """Raised when the configured ICON raw root is unsafe or unavailable."""


class RawStorageReferenceError(ValueError):
    """Raised when an ICON raw object path escapes the configured root."""


class HttpSession(Protocol):  # pylint: disable=too-few-public-methods
    """Minimal injectable HTTP session."""

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Issue an HTTP GET request."""


@dataclass(frozen=True)
class RawRetrieval:  # pylint: disable=too-many-instance-attributes
    """One retained DWD compressed product and canonical metadata."""

    payload_path: Path
    metadata_path: Path
    url: str
    sha256: str
    size_bytes: int
    cycle: datetime
    lead_hours: int
    fields: tuple[str, ...]


class DwdIconConnector:  # pylint: disable=too-few-public-methods
    """Download and retain a bounded set of official ICON field products."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        session: HttpSession | None = None,
        timeout_seconds: float = 60.0,
        retry_limit: int = 2,
        backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        *,
        test_raw_root: Path | None = None,
        environment: dict[str, str] | None = None,
        repository_root: Path | None = None,
    ) -> None:
        """Initialize an injectable, bounded-retry DWD transport.

        Runtime retention requires the external ``EVEREST_RAW_ROOT`` value.
        ``test_raw_root`` exists only to make filesystem tests deterministic.
        Runtime callers must not use it as fallback configuration.
        """
        self.raw_root = self._raw_root_from_configuration(
            test_raw_root, environment, repository_root
        )
        if session is None:
            session = requests.Session()
            # DWD direct TLS works in this environment; inherited proxy settings
            # terminate the official connection before a response is received.
            session.trust_env = False
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.retry_limit = retry_limit
        self.backoff_seconds = backoff_seconds
        self._sleep = sleep

    def retrieve(
        self,
        cycle: datetime,
        lead_hours: int = 0,
        fields: tuple[str, ...] = REQUESTED_FIELDS,
    ) -> RawRetrieval:
        """Retrieve, verify, concatenate, and retain DWD ICON GRIB messages.

        DWD's official compressed product route offers no message index or safe
        GRIB byte-range addressing.  The connector therefore downloads only the
        requested field products and validates each decompressed GRIB.
        """
        cycle = cycle.astimezone(timezone.utc)
        if cycle.hour not in (0, 6, 12, 18):
            raise ValueError("ICON cycle must be 00, 06, 12, or 18 UTC")
        if lead_hours < 0:
            raise ValueError("ICON lead must not be negative")
        if not fields or any(field not in REQUESTED_FIELDS for field in fields):
            raise ValueError("ICON fields must be approved requested fields")
        urls = tuple(
            self._official_product_href(cycle, lead_hours, field)
            for field in fields
        )
        compressed = tuple(self._request(url).content for url in urls)
        payload = b"".join(
            self._decompress(url, item) for url, item in zip(urls, compressed)
        )
        if not payload.startswith(b"GRIB"):
            raise ValueError("DWD response is not a decompressed GRIB2 payload")
        digest = self._sha256(payload)
        artifact_dir = self._resolve_object_reference(f"dwd-icon/{digest}")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        payload_path = (
            artifact_dir / f"icon_{cycle:%Y%m%d%H}_{lead_hours:03d}.grib2"
        )
        self._write_verified(payload_path, payload, digest)
        metadata = self._metadata(
            cycle, lead_hours, fields, urls, compressed, payload, digest
        )
        metadata_path = artifact_dir / "metadata.json"
        self._write_metadata(metadata_path, metadata)
        return RawRetrieval(
            payload_path,
            metadata_path,
            ",".join(urls),
            digest,
            len(payload),
            cycle,
            lead_hours,
            fields,
        )

    @staticmethod
    def _url(cycle: datetime, lead_hours: int, field: str) -> str:
        """Build DWD's documented ICON global single-level product URL."""
        directory = field.lower()
        if field in TIME_INVARIANT_FIELDS:
            filename = (
                "icon_global_icosahedral_time-invariant_"
                f"{cycle:%Y%m%d%H}_{field}.grib2.bz2"
            )
            return f"{OFFICIAL_ROOT}/{cycle:%H}/{directory}/{filename}"
        filename = (
            "icon_global_icosahedral_single-level_"
            f"{cycle:%Y%m%d%H}_{lead_hours:03d}_{field}.grib2.bz2"
        )
        return f"{OFFICIAL_ROOT}/{cycle:%H}/{directory}/{filename}"

    def _official_product_href(
        self, cycle: datetime, lead_hours: int, field: str
    ) -> str:
        """Resolve a product only from its current DWD listing href."""
        expected_url = self._url(cycle, lead_hours, field)
        directory_url = expected_url.rsplit("/", 1)[0] + "/"
        response = self._request(directory_url)
        parser = _HrefParser()
        parser.feed(response.content.decode("utf-8", errors="strict"))
        hrefs = {urljoin(directory_url, href) for href in parser.hrefs}
        if expected_url not in hrefs:
            raise ValueError(
                "DWD directory does not currently advertise expected ICON "
                f"product href: {expected_url}"
            )
        return expected_url

    @staticmethod
    def _decompress(url: str, compressed: bytes) -> bytes:
        """Decompress one bzip2 product without accepting HTML or errors."""
        try:
            payload = bz2.decompress(compressed)
        except OSError as error:
            raise ValueError(
                f"DWD ICON product is not valid bzip2: {url}"
            ) from error
        if not payload.startswith(b"GRIB"):
            raise ValueError(f"DWD ICON product is not GRIB2: {url}")
        return payload

    def _request(self, url: str) -> requests.Response:
        """Run deterministic exponential retry for DWD transport failures."""
        for attempt in range(self.retry_limit + 1):
            try:
                response = self.session.get(url, timeout=self.timeout_seconds)
                response.raise_for_status()
                return response
            except (requests.RequestException, OSError):
                if attempt == self.retry_limit:
                    raise
                self._sleep(self.backoff_seconds * (2**attempt))
        raise RuntimeError("unreachable retry state")

    @staticmethod
    def _sha256(payload: bytes) -> str:
        """Return SHA-256 for immutable payload or metadata bytes."""
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _project_root() -> Path:
        """Return the repository root inferred from the ICON module location."""
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _raw_root_from_configuration(
        cls,
        test_raw_root: Path | None,
        environment: dict[str, str] | None,
        repository_root: Path | None,
    ) -> Path:
        """Validate test storage or required runtime configuration."""
        values = os.environ if environment is None else environment
        configured_root = (
            str(test_raw_root)
            if test_raw_root is not None
            else values.get(RAW_ROOT_ENVIRONMENT_VARIABLE)
        )
        if not configured_root:
            raise RawStorageConfigurationError(
                f"{RAW_ROOT_ENVIRONMENT_VARIABLE} must be configured"
            )
        raw_root = Path(configured_root)
        project_root = repository_root or cls._project_root()
        if not raw_root.is_absolute():
            raise RawStorageConfigurationError(
                "ICON raw storage root must be an absolute path"
            )
        if not project_root.is_absolute():
            raise RawStorageConfigurationError(
                "ICON repository root must be an absolute path"
            )
        raw_root = raw_root.resolve()
        project_root = project_root.resolve()
        if not raw_root.exists() or not raw_root.is_dir():
            raise RawStorageConfigurationError(
                "ICON raw storage root must be an existing directory"
            )
        if raw_root.is_relative_to(project_root):
            raise RawStorageConfigurationError(
                "ICON raw storage root must be outside the repository"
            )
        return raw_root

    def _resolve_object_reference(self, object_reference: str) -> Path:
        """Resolve an object reference only when it remains under raw root."""
        if not object_reference:
            raise RawStorageReferenceError(
                "ICON raw object reference must not be empty"
            )
        reference = Path(object_reference)
        candidate = (
            reference if reference.is_absolute() else self.raw_root / reference
        ).resolve()
        if not candidate.is_relative_to(self.raw_root):
            raise RawStorageReferenceError(
                "ICON raw object reference must resolve under raw storage root"
            )
        return candidate

    def _write_verified(self, path: Path, payload: bytes, digest: str) -> None:
        """Atomically fsync and rehash an immutable content-addressed object."""
        path = self._resolve_object_reference(str(path))
        if path.exists():
            if self._sha256(path.read_bytes()) != digest:
                raise ValueError("existing ICON artifact checksum mismatch")
            return
        descriptor, temporary_name = tempfile.mkstemp(dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if self._sha256(temporary_path.read_bytes()) != digest:
                raise ValueError("persisted ICON artifact checksum mismatch")
            os.replace(temporary_path, path)
            try:
                path.chmod(0o444)
            except OSError:
                pass
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _canonical_json(metadata: dict[str, Any]) -> bytes:
        """Serialize metadata in its canonical integrity-protected form."""
        return (
            json.dumps(
                metadata,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

    def _write_metadata(self, path: Path, metadata: dict[str, Any]) -> None:
        """Retain canonical metadata and mandatory SHA-256 sidecar."""
        path = self._resolve_object_reference(str(path))
        sidecar = path.with_name(f"{path.name}.sha256")
        self._resolve_object_reference(str(sidecar))
        encoded = self._canonical_json(metadata)
        if path.exists() or sidecar.exists():
            self._verify_metadata(path, sidecar, metadata)
            return
        digest = self._sha256(encoded)
        self._write_verified(path, encoded, digest)
        sidecar_bytes = f"{digest}\n".encode("ascii")
        self._write_verified(
            sidecar, sidecar_bytes, self._sha256(sidecar_bytes)
        )

    def _verify_metadata(
        self, path: Path, sidecar: Path, expected: dict[str, Any]
    ) -> None:
        """Reject absent, changed, malformed, or noncanonical metadata reuse."""
        if not path.exists() or not sidecar.exists():
            raise ValueError("ICON metadata or checksum sidecar is missing")
        encoded = path.read_bytes()
        if self._sha256(encoded) != sidecar.read_text(encoding="ascii").strip():
            raise ValueError("ICON metadata checksum mismatch")
        try:
            actual = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("ICON metadata is not valid UTF-8 JSON") from error
        if (
            not isinstance(actual, dict)
            or self._canonical_json(actual) != encoded
        ):
            raise ValueError(
                "ICON metadata is not canonical deterministic JSON"
            )
        expected_without_time = dict(expected)
        actual_without_time = dict(actual)
        expected_without_time.pop("retrieved_at", None)
        actual_without_time.pop("retrieved_at", None)
        if actual_without_time != expected_without_time:
            raise ValueError("ICON metadata provenance mismatch")

    @staticmethod
    # Each retention fact is explicit so a downstream audit has no implicit I/O.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def _metadata(
        cycle: datetime,
        lead_hours: int,
        fields: tuple[str, ...],
        urls: tuple[str, ...],
        compressed: tuple[bytes, ...],
        payload: bytes,
        digest: str,
    ) -> dict[str, Any]:
        """Return complete factual raw-retention metadata."""
        valid_time = cycle + timedelta(hours=lead_hours)
        return {
            "source": "dwd-icon",
            "provider": "DWD",
            "dataset": "ICON global",
            "model": "ICON",
            "cycle": cycle.isoformat(),
            "lead_hours": lead_hours,
            "valid_time": valid_time.isoformat(),
            "valid_time_epoch": int(valid_time.timestamp()),
            "urls": list(urls),
            "format": "GRIB2",
            "compression": "bzip2",
            "fields": list(fields),
            "aoi_id": AOI_ID,
            "aoi_version": AOI_VERSION,
            "aoi_scope_id": AOI_SCOPE_ID,
            "requested_coordinate": [EVEREST_LATITUDE, EVEREST_LONGITUDE],
            "compressed_size_bytes": [len(item) for item in compressed],
            "size_bytes": len(payload),
            "sha256": digest,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
