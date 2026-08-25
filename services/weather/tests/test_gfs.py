"""Deterministic tests for the NOAA GFS connector and normalizer."""

# Private methods are exercised to lock transport and retention trust boundaries.
# The fake transport and provider fixture intentionally mirror ECMWF tests.
# pylint: disable=protected-access,too-few-public-methods,duplicate-code

from datetime import datetime, timezone
from pathlib import Path
import stat
from typing import Any

import pytest
import requests

from services.weather.gfs.connector import GfsNcepConnector
from services.weather.gfs.normalizer import normalize_messages
from services.weather.gfs.parser import ParsedMessage, parse_grib_bytes


def _make_writable(path: Path) -> None:
    """Restore write permission before an intentional Windows tamper."""
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _replace_for_test(path: Path, payload: bytes) -> None:
    """Temporarily make a retained file writable, then restore protection."""
    _make_writable(path)
    try:
        path.write_bytes(payload)
    finally:
        if path.exists():
            path.chmod(stat.S_IRUSR)


def _remove_for_test(path: Path) -> None:
    """Temporarily make a retained file writable before deleting it."""
    _make_writable(path)
    try:
        path.unlink()
    finally:
        if path.exists():
            path.chmod(stat.S_IRUSR)


class FakeResponse:
    """Minimal response fixture."""

    def __init__(
        self,
        content: bytes = b"GRIB2",
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.content = content
        self.status_code = status
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        """Raise for an unsuccessful status."""
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class FakeSession:
    """Queued response session."""

    def __init__(self, outcomes: list[FakeResponse | Exception]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        """Return the next queued result."""
        self.calls.append((url, kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _message(parameter: str, value: float, units: str) -> ParsedMessage:
    """Create a one-cell provider message."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    return ParsedMessage(
        parameter,
        cycle,
        cycle,
        0,
        (value,),
        (27.9881,),
        (86.9250,),
        units,
        "sfc",
    )


def test_normalizer_applies_explicit_gfs_units() -> None:
    """Kelvin, geopotential, vector wind, and precipitation normalize exactly."""
    record = normalize_messages(
        (
            _message("tmp", 273.15, "K"),
            _message("ugrd", 3.0, "m s**-1"),
            _message("vgrd", 4.0, "m s**-1"),
            _message("hgt", 6008.0, "gpm"),
            _message("apcp", 2.5, "kg m**-2"),
        ),
        27.9881,
        86.9250,
    )
    assert record.temperature == 0.0
    assert record.wind_speed == 5.0
    assert record.altitude == 6008.0
    assert record.precipitation == 2.5


def test_normalizer_flags_unknown_units_without_guessing() -> None:
    """An unexpected provider unit becomes null and is additively flagged."""
    record = normalize_messages(
        (_message("tmp", 273.15, "unknown"),), 27.9881, 86.9250
    )
    assert record.temperature is None
    assert "invalid_unit" in record.quality_flags
    assert "missing_value" in record.quality_flags


def test_retry_is_bounded_and_injected(tmp_path: Path) -> None:
    """Transient transport failure uses deterministic injected backoff."""
    delays: list[float] = []
    session = FakeSession([requests.Timeout(), FakeResponse()])
    connector = GfsNcepConnector(
        tmp_path, session=session, backoff_seconds=0.25, sleep=delays.append
    )
    response = connector._request("https://example.test")
    assert response.content == b"GRIB2"
    assert len(session.calls) == 2
    assert delays == [0.25]


def test_retry_exhaustion_is_deterministic(tmp_path: Path) -> None:
    """Exhausted transport failures are not swallowed."""
    connector = GfsNcepConnector(
        tmp_path,
        FakeSession([requests.Timeout()] * 3),
        retry_limit=2,
        sleep=lambda _: None,
    )
    with pytest.raises(requests.Timeout):
        connector._request("https://example.test")


def test_http_500_retries_and_exhausts_without_sleep(tmp_path: Path) -> None:
    """Historical filter failures follow the bounded retry policy."""
    delays: list[float] = []
    responses = [FakeResponse(status=500)] * 3
    connector = GfsNcepConnector(
        tmp_path,
        FakeSession(responses),
        retry_limit=2,
        sleep=delays.append,
    )
    with pytest.raises(requests.HTTPError):
        connector._request("https://example.test/filter")
    assert delays == [1.0, 2.0]


def test_raw_artifact_reuse_detects_tampering(tmp_path: Path) -> None:
    """Content-addressed raw retention rejects changed bytes."""
    connector = GfsNcepConnector(tmp_path)
    payload = b"GRIB2 sample"
    digest = connector._sha256(payload)
    path = tmp_path / "sample.grib2"
    connector._write_verified(path, payload, digest)
    _replace_for_test(path, b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_verified(path, payload, digest)


def test_metadata_reuse_is_canonical_and_sidecar_protected(
    tmp_path: Path,
) -> None:
    """Metadata writes canonical JSON and a reusable SHA-256 sidecar."""
    connector = GfsNcepConnector(tmp_path)
    path = tmp_path / "metadata.json"
    metadata = {"source": "noaa-gfs", "messages": [["orog", "surface"]]}
    connector._write_metadata(path, metadata)
    sidecar = tmp_path / "metadata.json.sha256"
    assert (
        path.read_bytes()
        == b'{"messages":[["orog","surface"]],"source":"noaa-gfs"}\n'
    )
    assert len(sidecar.read_text(encoding="ascii").strip()) == 64
    connector._write_metadata(path, metadata)


def test_metadata_tampering_and_missing_sidecar_are_rejected(
    tmp_path: Path,
) -> None:
    """Metadata JSON and its sidecar are both mandatory immutable artifacts."""
    connector = GfsNcepConnector(tmp_path)
    path = tmp_path / "metadata.json"
    metadata = {"source": "noaa-gfs"}
    connector._write_metadata(path, metadata)
    _replace_for_test(path, b'{"source":"tampered"}\n')
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_metadata(path, metadata)
    _replace_for_test(path, connector._canonical_json(metadata))
    sidecar = tmp_path / "metadata.json.sha256"
    _remove_for_test(sidecar)
    with pytest.raises(ValueError, match="missing"):
        connector._write_metadata(path, metadata)


def test_metadata_noncanonical_json_is_rejected(tmp_path: Path) -> None:
    """Valid JSON with noncanonical formatting cannot be reused."""
    connector = GfsNcepConnector(tmp_path)
    path = tmp_path / "metadata.json"
    metadata = {"source": "noaa-gfs"}
    connector._write_metadata(path, metadata)
    _replace_for_test(path, b'{ "source": "noaa-gfs" }\n')
    sidecar = tmp_path / "metadata.json.sha256"
    _replace_for_test(
        sidecar, connector._sha256(path.read_bytes()).encode("ascii")
    )
    with pytest.raises(ValueError, match="canonical"):
        connector._write_metadata(path, metadata)


def test_index_selection_is_exact_and_deterministic() -> None:
    """Only requested parameter/level messages become byte ranges."""
    index = (
        "1:0:d=2026082000:HGT:surface:anl:\n"
        "2:100:d=2026082000:TMP:2 m above ground:anl:\n"
        "3:250:d=2026082000:UGRD:10 m above ground:anl:\n"
        "4:400:d=2026082000:VGRD:10 m above ground:anl:\n"
    )
    assert GfsNcepConnector._select_index_ranges(
        index,
        (
            ("HGT", "surface"),
            ("TMP", "2 m above ground"),
        ),
    ) == [(0, 99), (100, 249)]


def test_range_rejects_full_response(tmp_path: Path) -> None:
    """A server ignoring Range cannot cause an unbounded download."""
    connector = GfsNcepConnector(
        tmp_path,
        FakeSession([FakeResponse(b"full", status=200)]),
    )
    with pytest.raises(ValueError, match="HTTP 206"):
        connector._get_range("https://example.test/file", 0, 3)


def test_range_accepts_valid_206_and_rejects_malformed_or_truncated(
    tmp_path: Path,
) -> None:
    """Range trust requires exact status, header, and byte count."""
    valid = FakeResponse(b"abcd", 206, {"Content-Range": "bytes 4-7/20"})
    connector = GfsNcepConnector(tmp_path, FakeSession([valid]))
    assert connector._get_range("https://example.test/file", 4, 7) == b"abcd"
    cases = [
        FakeResponse(b"abcd", 206, {"Content-Range": "bytes 3-6/20"}),
        FakeResponse(b"abc", 206, {"Content-Range": "bytes 4-7/20"}),
    ]
    for response in cases:
        connector = GfsNcepConnector(tmp_path, FakeSession([response]))
        with pytest.raises(ValueError):
            connector._get_range("https://example.test/file", 4, 7)


def test_index_failure_is_not_silently_converted_to_empty_selection() -> None:
    """Malformed or incomplete indexes fail closed."""
    with pytest.raises(ValueError, match="lacks"):
        GfsNcepConnector._select_index_ranges(
            "1:0:d=2026082000:TMP:2 m above ground:anl:\n",
            (("OROG", "surface"),),
        )


def test_parser_rejects_non_grib_payload() -> None:
    """Parser never treats arbitrary bytes as a weather message."""
    with pytest.raises((RuntimeError, ValueError)):
        parse_grib_bytes(b"not GRIB2")
