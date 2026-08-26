"""Deterministic tests for the ECMWF IFS connector and normalizer."""

# Tests deliberately exercise connector-private trust boundaries directly.
# pylint: disable=protected-access

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import requests

from services.weather.ecmwf.connector import EcmwfOpenDataConnector
from services.weather.ecmwf.normalizer import normalize_messages
from services.weather.ecmwf.parser import ParsedMessage, parse_grib_bytes


class FakeResponse:  # pylint: disable=too-few-public-methods
    """Minimal controllable HTTP response for connector tests."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        status: int = 200,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
        text: str = "",
        error: Exception | None = None,
    ) -> None:
        self.status_code = status
        self.content = content
        self.headers = headers or {}
        self.text = text
        self._error = error

    def raise_for_status(self) -> None:
        """Raise configured transport error or HTTP status failure."""
        if self._error:
            raise self._error
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class FakeSession:  # pylint: disable=too-few-public-methods
    """Record HTTP calls and return queued fake outcomes."""

    def __init__(self, outcomes: list[FakeResponse | Exception]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        """Return the next fake outcome."""
        self.calls.append((url, kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _message(parameter: str, value: float, units: str) -> ParsedMessage:
    """Build one parsed-message fixture with a provider grid."""
    cycle = datetime(2026, 8, 20, tzinfo=timezone.utc)
    return ParsedMessage(
        parameter,
        cycle,
        cycle,
        0,
        (value,),
        (27.9881,),
        (86.925,),
        units,
        "sfc",
    )


def _messages(tp_units: str = "m") -> tuple[ParsedMessage, ...]:
    """Build a complete unit-declared IFS surface sample."""
    return (
        _message("z", 5_364 * 9.80665, "m**2 s**-2"),
        _message("10u", 3.0, "m s**-1"),
        _message("10v", 4.0, "m s**-1"),
        _message("2t", 265.15, "K"),
        _message("tp", 1.2, tp_units),
    )


def test_normalizer_converts_declared_ifs_units() -> None:
    """IFS geopotential, Kelvin, vector wind, and metre tp become canonical."""
    record = normalize_messages(_messages(), 27.99, 86.93)
    assert record.altitude == 5364.0
    assert record.wind_speed == 5.0
    assert record.temperature == -8.0
    assert record.precipitation == 1200.0
    assert "missing_value" in record.quality_flags
    assert "invalid_unit" not in record.quality_flags


def test_normalizer_flags_unknown_precipitation_unit_without_guessing() -> None:
    """An unknown tp unit is retained upstream but absent from canonical data."""
    record = normalize_messages(_messages("unknown"), 27.99, 86.93)
    assert record.precipitation is None
    assert "invalid_unit" in record.quality_flags
    assert "missing_value" in record.quality_flags


def test_static_surface_geopotential_anchors_dynamic_forecast_altitude() -> (
    None
):
    """Same-cycle step-zero z supplies altitude without changing valid time."""
    cycle = datetime(2026, 8, 20, tzinfo=timezone.utc)
    static_z = ParsedMessage(
        "z",
        cycle,
        cycle,
        0,
        (5_364 * 9.80665,),
        (28.0,),
        (87.0,),
        "m**2 s**-2",
        "sfc",
    )
    dynamic = tuple(
        ParsedMessage(
            message.parameter,
            cycle.replace(hour=3),
            cycle,
            3,
            message.values,
            (28.0,),
            (87.0,),
            message.units,
            message.level_type,
        )
        for message in _messages()[1:]
    )
    record = normalize_messages((static_z, *dynamic), 27.9881, 86.9250)
    assert record.timestamp == cycle.replace(hour=3)
    assert record.forecast is not None
    assert record.forecast.lead_time.total_seconds() == 10_800
    assert record.altitude == 5364.0


def test_request_retries_transient_error_with_deterministic_backoff(
    tmp_path: Path,
) -> None:
    """One transport error retries once with injected, observable backoff."""
    session = FakeSession(
        [requests.Timeout("temporary"), FakeResponse(text="")]
    )
    delays: list[float] = []
    connector = EcmwfOpenDataConnector(
        tmp_path,
        session=session,
        retry_limit=2,
        backoff_seconds=0.25,
        sleep=delays.append,
    )
    assert (
        connector._request("https://example.test").text == ""
    )  # pylint: disable=protected-access
    assert len(session.calls) == 2
    assert delays == [0.25]


def test_request_raises_after_exhausted_timeout_retries(tmp_path: Path) -> None:
    """Timeouts are retried exactly through the configured bounded limit."""
    session = FakeSession([requests.Timeout("one"), requests.Timeout("two")])
    delays: list[float] = []
    connector = EcmwfOpenDataConnector(
        tmp_path, session, retry_limit=1, sleep=delays.append
    )
    with pytest.raises(requests.Timeout):
        connector._request(
            "https://example.test"
        )  # pylint: disable=protected-access
    assert len(session.calls) == 2
    assert delays == [1.0]


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (FakeResponse(status=200, content=b"x"), "HTTP 206"),
        (FakeResponse(status=206, content=b"x", headers={}), "Content-Range"),
        (
            FakeResponse(
                status=206,
                content=b"x",
                headers={"Content-Range": "bytes 0-1/2"},
            ),
            "byte length",
        ),
    ],
)
def test_range_rejects_untrusted_or_wrong_sized_responses(
    tmp_path: Path,
    response: FakeResponse,
    message: str,
) -> None:
    """Range downloads reject full, malformed, and truncated responses."""
    connector = EcmwfOpenDataConnector(tmp_path, FakeSession([response]))
    with pytest.raises(ValueError, match=message):
        connector._get_range(
            "https://example.test", 0, 2
        )  # pylint: disable=protected-access


def test_range_accepts_exact_validated_partial_response(tmp_path: Path) -> None:
    """Only an exact 206 range with expected Content-Range is accepted."""
    response = FakeResponse(206, b"ab", {"Content-Range": "bytes 3-4/10"})
    connector = EcmwfOpenDataConnector(tmp_path, FakeSession([response]))
    assert (
        connector._get_range("https://example.test", 3, 2) == b"ab"
    )  # pylint: disable=protected-access


def test_verified_raw_write_rehashes_and_detects_existing_tamper(
    tmp_path: Path,
) -> None:
    """Raw retention rehashes disk bytes and rejects a tampered artifact."""
    connector = EcmwfOpenDataConnector(tmp_path)
    payload = b"raw-data"
    digest = connector._sha256(payload)  # pylint: disable=protected-access
    path = tmp_path / "raw.grib2"
    connector._write_verified(
        path, payload, digest
    )  # pylint: disable=protected-access
    assert path.read_bytes() == payload
    path.chmod(0o644)
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_verified(
            path, payload, digest
        )  # pylint: disable=protected-access


def test_metadata_initial_write_and_valid_reuse(tmp_path: Path) -> None:
    """Metadata is canonical, sidecar-protected, and safely reusable."""
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    metadata = {"z": 1, "source": "ecmwf-ifs"}
    connector._write_metadata(path, metadata)
    sidecar = tmp_path / "metadata.json.sha256"
    assert path.read_bytes() == b'{"source":"ecmwf-ifs","z":1}\n'
    assert sidecar.read_text(encoding="ascii").strip()
    connector._write_metadata(path, metadata)


def test_metadata_reuse_rejects_tampered_json(tmp_path: Path) -> None:
    """Changing canonical metadata bytes is rejected on reuse."""
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    connector._write_metadata(path, {"source": "ecmwf-ifs"})
    path.chmod(0o644)
    path.write_bytes(b'{"source":"tampered"}\n')
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_metadata(path, {"source": "ecmwf-ifs"})


def test_metadata_reuse_rejects_missing_checksum_sidecar(
    tmp_path: Path,
) -> None:
    """A metadata file without its integrity sidecar is never trusted."""
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    connector._write_metadata(path, {"source": "ecmwf-ifs"})
    checksum_path = tmp_path / "metadata.json.sha256"
    checksum_path.chmod(0o644)
    checksum_path.unlink()
    with pytest.raises(ValueError, match="missing"):
        connector._write_metadata(path, {"source": "ecmwf-ifs"})


def test_metadata_reuse_rejects_tampered_checksum_sidecar(
    tmp_path: Path,
) -> None:
    """A changed checksum sidecar is rejected even when JSON is unchanged."""
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    connector._write_metadata(path, {"source": "ecmwf-ifs"})
    checksum_path = tmp_path / "metadata.json.sha256"
    checksum_path.chmod(0o644)
    checksum_path.write_text("0" * 64, encoding="ascii")
    with pytest.raises(ValueError, match="sidecar is inconsistent"):
        connector._write_metadata(path, {"source": "ecmwf-ifs"})


def test_retained_metadata_is_reused_when_the_payload_is_unchanged(
    tmp_path: Path,
) -> None:
    """A cached artifact is accepted although its ``retrieved_at`` is older.

    Rebuilding the metadata on a second retrieval produces a newer timestamp and
    therefore a different digest, so requiring byte equality made every already
    retained cycle fail once the raw tree stopped being wiped between runs.
    """
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    connector._write_metadata(
        path, {"sha256": "a" * 64, "retrieved_at": "2026-08-01T00:00:00+00:00"}
    )
    connector._verify_retained_metadata(path, "a" * 64)


def test_retained_metadata_about_another_payload_is_rejected(
    tmp_path: Path,
) -> None:
    """Reuse requires the retained metadata to describe this exact payload."""
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    connector._write_metadata(path, {"sha256": "a" * 64})
    with pytest.raises(ValueError, match="different payload"):
        connector._verify_retained_metadata(path, "b" * 64)


def test_retained_metadata_with_a_tampered_sidecar_is_rejected(
    tmp_path: Path,
) -> None:
    """Relaxing the timestamp check does not relax the integrity check."""
    connector = EcmwfOpenDataConnector(tmp_path)
    path = tmp_path / "metadata.json"
    connector._write_metadata(path, {"sha256": "a" * 64})
    checksum_path = tmp_path / "metadata.json.sha256"
    checksum_path.chmod(0o644)
    checksum_path.write_text("0" * 64, encoding="ascii")
    with pytest.raises(ValueError, match="sidecar is inconsistent"):
        connector._verify_retained_metadata(path, "a" * 64)


def test_parser_rejects_non_grib_payload() -> None:
    """Parser does not turn arbitrary bytes into weather records."""
    with pytest.raises(Exception):  # ecCodes exposes platform-specific errors.
        parse_grib_bytes(b"not a GRIB2 payload")
