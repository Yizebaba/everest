"""Deterministic tests for DWD ICON retrieval, normalization, and parsing."""

# Tests intentionally exercise ICON's private transport/integrity boundary.
# pylint: disable=protected-access,too-few-public-methods,duplicate-code

import bz2
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Any

import pytest
import requests

from services.weather.icon.connector import DwdIconConnector
from services.weather.icon.connector import RawStorageConfigurationError
from services.weather.icon.connector import RawStorageReferenceError
from services.weather.icon.normalizer import (
    nearest_grid_index,
    normalize_canonical_record,
    normalize_messages,
    provider_spatial_key,
)
from services.weather.icon import parser as icon_parser
from services.weather.icon.parser import (
    ParsedMessage,
    _with_native_coordinates,
    parse_grib_bytes,
)


class FakeResponse:
    """A minimal requests-compatible response."""

    def __init__(self, content: bytes = b"", status: int = 200) -> None:
        """Set fixed content and HTTP status."""
        self.content = content
        self.status_code = status

    def raise_for_status(self) -> None:
        """Raise the same failure family as requests."""
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class FakeSession:
    """A queued transport fake with captured calls."""

    def __init__(self, results: list[FakeResponse | Exception]) -> None:
        """Initialize queued outcomes."""
        self.results = results
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        """Return the next deterministic outcome."""
        self.calls.append((url, kwargs))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


# Fixture construction intentionally exposes provider message fields directly.
# pylint: disable=too-many-arguments
def _message(
    parameter: str,
    value: float,
    units: str,
    *,
    cycle: datetime | None = None,
    valid_time: datetime | None = None,
    latitudes: tuple[float, ...] = (27.98,),
    longitudes: tuple[float, ...] = (86.93,),
) -> ParsedMessage:
    """Build one native-grid ICON fixture message."""
    cycle = cycle or datetime(2026, 8, 21, tzinfo=timezone.utc)
    valid_time = valid_time or cycle
    return ParsedMessage(
        parameter,
        valid_time,
        cycle,
        int((valid_time - cycle).total_seconds() // 3600),
        (value,) * len(latitudes),
        latitudes,
        longitudes,
        units,
        "surface",
        "unstructured_grid",
        "a27b8de618c411e4820ab5b098c6a5c0",
    )


def test_normalizer_applies_explicit_icon_units() -> None:
    """DWD-declared Kelvin, wind, and native terrain metres are exact."""
    record = normalize_messages(
        (
            _message("t_2m", 273.15, "K"),
            _message("u_10m", 3.0, "m s**-1"),
            _message("v_10m", 4.0, "m s**-1"),
            _message("hsurf", 6012.0, "m"),
        ),
        27.9881,
        86.9250,
    )
    assert record.temperature == 0.0
    assert record.wind_speed == 5.0
    assert record.altitude == 6012.0
    assert record.latitude == 27.98
    assert {"missing_value"} <= record.quality_flags
    assert record.record_type.value == "forecast"
    assert record.source == "dwd-icon"
    assert record.model == "ICON"


def test_normalizer_retains_nonzero_utc_forecast_identity() -> None:
    """Valid time is exactly cycle plus a positive integral lead."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    valid = cycle + timedelta(hours=3)
    record = normalize_messages(
        (_message("t_2m", 273.15, "K", cycle=cycle, valid_time=valid),),
        27.9881,
        86.9250,
    )
    assert record.timestamp == valid
    assert record.timestamp.tzinfo == timezone.utc
    assert record.forecast is not None
    assert record.forecast.cycle == cycle
    assert record.forecast.lead_time == timedelta(hours=3)
    assert record.timestamp == record.forecast.cycle + record.forecast.lead_time


def test_normalizer_converts_aware_non_utc_time_and_rejects_naive() -> None:
    """Aware offsets become UTC; naive provider times fail closed."""
    cycle = datetime(2026, 8, 21, 2, tzinfo=timezone(timedelta(hours=2)))
    valid = cycle + timedelta(hours=3)
    record = normalize_messages(
        (_message("t_2m", 273.15, "K", cycle=cycle, valid_time=valid),),
        27.9881,
        86.9250,
    )
    assert record.timestamp == datetime(2026, 8, 21, 3, tzinfo=timezone.utc)
    naive = cycle.replace(tzinfo=None)
    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_messages(
            (_message("t_2m", 273.15, "K", cycle=naive, valid_time=naive),),
            27.9881,
            86.9250,
        )


def test_provider_spatial_key_preserves_native_grid_identity() -> None:
    """The spatial identity comprises DWD grid UUID and true point index."""
    message = _message("t_2m", 273.15, "K")
    index = nearest_grid_index(message, 27.9881, 86.9250)
    assert provider_spatial_key(message, index) == (
        "icon:a27b8de618c411e4820ab5b098c6a5c0:0"
    )


def test_native_uuid_index_propagates_from_normalizer() -> None:
    """The selected native UUID/index becomes the adapter-facing key."""
    messages = (
        _message(
            "t_2m",
            273.15,
            "K",
            latitudes=(27.0, 27.9881),
            longitudes=(86.0, 86.9250),
        ),
    )
    record = normalize_canonical_record(messages, 27.9881, 86.9250)
    assert record.spatial_key == ("icon:a27b8de618c411e4820ab5b098c6a5c0:1")


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (float("nan"), 86.9250),
        (float("inf"), 86.9250),
        (float("-inf"), 86.9250),
        (27.9881, float("nan")),
        (27.9881, float("inf")),
        (27.9881, float("-inf")),
    ],
)
def test_normalizer_rejects_nonfinite_requested_coordinates(
    latitude: float,
    longitude: float,
) -> None:
    """NaN and infinite requests fail before native-grid selection."""
    with pytest.raises(
        ValueError, match="requested coordinates must be finite"
    ):
        normalize_messages(
            (_message("t_2m", 273.15, "K"),), latitude, longitude
        )


@pytest.mark.parametrize("latitude", (-90.01, 90.01))
def test_normalizer_rejects_requested_latitude_outside_both_bounds(
    latitude: float,
) -> None:
    """Requested latitude must remain within both canonical bounds."""
    with pytest.raises(ValueError, match=r"latitude is outside \[-90, 90\]"):
        normalize_messages((_message("t_2m", 273.15, "K"),), latitude, 86.9250)


@pytest.mark.parametrize("longitude", (-180.01, 180.01))
def test_normalizer_rejects_requested_longitude_outside_both_bounds(
    longitude: float,
) -> None:
    """Requested longitude must remain within both canonical bounds."""
    with pytest.raises(ValueError, match=r"longitude is outside \[-180, 180\]"):
        normalize_messages((_message("t_2m", 273.15, "K"),), 27.9881, longitude)


def test_normalizer_flags_unknown_units_without_guessing() -> None:
    """Unexpected provider units produce null values and additive QC."""
    record = normalize_messages(
        (_message("t_2m", 273.15, "unknown"),), 27.9881, 86.9250
    )
    assert record.temperature is None
    assert "invalid_unit" in record.quality_flags
    assert "missing_value" in record.quality_flags


@pytest.mark.parametrize(
    ("parameter", "units", "field"),
    [
        ("t_2m", "C", "temperature"),
        ("u_10m", "km h-1", "wind_speed"),
        ("v_10m", "knots", "wind_speed"),
        ("hsurf", "km", "altitude"),
    ],
)
def test_all_wrong_icon_units_are_not_guessed(
    parameter: str, units: str, field: str
) -> None:
    """Plausible magnitudes with wrong declarations remain unavailable."""
    record = normalize_messages(
        (_message(parameter, 273.15, units),), 27.9881, 86.9250
    )
    assert getattr(record, field) is None
    assert "invalid_unit" in record.quality_flags


def test_calm_and_missing_values_are_null_and_additive() -> None:
    """Calm, absent, and non-finite inputs are never converted to zero."""
    record = normalize_messages(
        (
            _message("t_2m", float("nan"), "K"),
            _message("u_10m", 0.0, "m s**-1"),
            _message("v_10m", 0.0, "m s**-1"),
        ),
        27.9881,
        86.9250,
    )
    assert record.temperature is None
    assert record.wind_speed == 0.0
    assert record.wind_direction is None
    assert "missing_value" in record.quality_flags
    assert record.precipitation is None
    assert record.visibility is None


@pytest.mark.parametrize(
    ("u_value", "v_value", "expected"),
    [
        (0.0, -1.0, 0.0),
        (-1.0, 0.0, 90.0),
        (0.0, 1.0, 180.0),
        (1.0, 0.0, 270.0),
        (-1.0, -1.0, 45.0),
    ],
)
def test_wind_direction_is_true_north_clockwise_in_range(
    u_value: float, v_value: float, expected: float
) -> None:
    """ICON vector conversion follows the canonical compass convention."""
    record = normalize_messages(
        (
            _message("u_10m", u_value, "m s**-1"),
            _message("v_10m", v_value, "m s**-1"),
        ),
        27.9881,
        86.9250,
    )
    assert record.wind_direction == expected
    assert 0 <= record.wind_direction < 360


def test_retry_is_bounded_and_injected(tmp_path: Path) -> None:
    """A transient error gets deterministic exponential backoff."""
    delays: list[float] = []
    connector = DwdIconConnector(
        FakeSession([requests.Timeout(), FakeResponse(b"ok")]),
        backoff_seconds=0.25,
        sleep=delays.append,
        test_raw_root=tmp_path,
    )
    assert (
        connector._request("https://opendata.dwd.de/example").content == b"ok"
    )
    assert delays == [0.25]


def test_default_session_does_not_inherit_broken_proxy_settings(
    tmp_path: Path,
) -> None:
    """DWD direct transport ignores ambient proxy configuration."""
    assert DwdIconConnector(test_raw_root=tmp_path).session.trust_env is False


def test_retry_exhaustion_and_invalid_bzip2_fail_closed(tmp_path: Path) -> None:
    """Retries do not hide exhaustion and non-bzip2 data cannot be parsed."""
    connector = DwdIconConnector(
        FakeSession([requests.Timeout()] * 3),
        retry_limit=2,
        sleep=lambda _: None,
        test_raw_root=tmp_path,
    )
    with pytest.raises(requests.Timeout):
        connector._request("https://opendata.dwd.de/example")
    with pytest.raises(ValueError, match="bzip2"):
        connector._decompress("https://opendata.dwd.de/example", b"not-bzip2")


def test_dwd_product_urls_are_deterministic() -> None:
    """Only the official global ICON product route can be constructed."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    assert DwdIconConnector._url(cycle, 3, "T_2M") == (
        "https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/"
        "icon_global_icosahedral_single-level_2026082100_003_T_2M.grib2.bz2"
    )
    assert DwdIconConnector._url(cycle, 0, "HSURF").endswith(
        "hsurf/icon_global_icosahedral_time-invariant_2026082100_"
        "HSURF.grib2.bz2"
    )
    assert DwdIconConnector._url(cycle, 0, "CLAT").endswith(
        "clat/icon_global_icosahedral_time-invariant_2026082100_CLAT.grib2.bz2"
    )


def test_retention_metadata_reuse_detects_tampering(tmp_path: Path) -> None:
    """Raw content and JSON metadata always rehash before reuse."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    payload = b"GRIB sample"
    path = tmp_path / "artifact.grib2"
    connector._write_verified(path, payload, connector._sha256(payload))
    path.chmod(0o644)
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_verified(path, payload, connector._sha256(payload))
    metadata_path = tmp_path / "metadata.json"
    metadata = {"source": "dwd-icon", "model": "ICON"}
    connector._write_metadata(metadata_path, metadata)
    metadata_path.chmod(0o644)
    metadata_path.write_bytes(b'{"source":"altered"}\n')
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_metadata(metadata_path, metadata)
    metadata_path.write_bytes(connector._canonical_json(metadata))
    sidecar = metadata_path.with_name("metadata.json.sha256")
    sidecar.chmod(0o644)
    sidecar.write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_metadata(metadata_path, metadata)


def test_metadata_reuse_rejects_missing_metadata_json(tmp_path: Path) -> None:
    """Sidecars cannot recreate a missing metadata document."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    metadata_path = tmp_path / "metadata.json"
    metadata = {"model": "ICON", "source": "dwd-icon"}
    connector._write_metadata(metadata_path, metadata)
    metadata_path.chmod(0o644)
    metadata_path.unlink()
    with pytest.raises(ValueError, match="sidecar is missing"):
        connector._write_metadata(metadata_path, metadata)


def test_metadata_reuse_rejects_missing_checksum_sidecar(
    tmp_path: Path,
) -> None:
    """Existing metadata cannot recreate a missing integrity sidecar."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    metadata_path = tmp_path / "metadata.json"
    metadata = {"model": "ICON", "source": "dwd-icon"}
    connector._write_metadata(metadata_path, metadata)
    sidecar = metadata_path.with_name("metadata.json.sha256")
    sidecar.chmod(0o644)
    sidecar.unlink()
    with pytest.raises(ValueError, match="sidecar is missing"):
        connector._write_metadata(metadata_path, metadata)


def test_metadata_reuse_rejects_tampered_checksum_sidecar(
    tmp_path: Path,
) -> None:
    """A modified sidecar fails with unchanged canonical metadata."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    metadata_path = tmp_path / "metadata.json"
    metadata = {"model": "ICON", "source": "dwd-icon"}
    connector._write_metadata(metadata_path, metadata)
    sidecar = metadata_path.with_name("metadata.json.sha256")
    sidecar.chmod(0o644)
    sidecar.write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(ValueError, match="checksum mismatch"):
        connector._write_metadata(metadata_path, metadata)


def test_metadata_reuse_rejects_noncanonical_json(tmp_path: Path) -> None:
    """A valid JSON document with a matching sidecar must still be canonical."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    metadata_path = tmp_path / "metadata.json"
    metadata = {"model": "ICON", "source": "dwd-icon"}
    connector._write_metadata(metadata_path, metadata)
    metadata_path.chmod(0o644)
    noncanonical = b'{"source": "dwd-icon", "model": "ICON"}\n'
    metadata_path.write_bytes(noncanonical)
    sidecar = metadata_path.with_name("metadata.json.sha256")
    sidecar.chmod(0o644)
    sidecar.write_text(connector._sha256(noncanonical) + "\n", encoding="ascii")
    with pytest.raises(ValueError, match="canonical deterministic JSON"):
        connector._write_metadata(metadata_path, metadata)


def test_metadata_reuse_rejects_payload_metadata_digest_mismatch(
    tmp_path: Path,
) -> None:
    """Metadata cannot claim a digest other than the retained payload digest."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    payload = b"GRIB payload"
    payload_path = tmp_path / "artifact.grib2"
    payload_digest = connector._sha256(payload)
    connector._write_verified(payload_path, payload, payload_digest)
    metadata_path = tmp_path / "metadata.json"
    metadata = {
        "model": "ICON",
        "sha256": payload_digest,
        "size_bytes": len(payload),
        "source": "dwd-icon",
    }
    connector._write_metadata(metadata_path, metadata)
    altered = {**metadata, "sha256": "0" * 64}
    altered_bytes = connector._canonical_json(altered)
    metadata_path.chmod(0o644)
    metadata_path.write_bytes(altered_bytes)
    sidecar = metadata_path.with_name("metadata.json.sha256")
    sidecar.chmod(0o644)
    sidecar.write_text(
        connector._sha256(altered_bytes) + "\n", encoding="ascii"
    )
    with pytest.raises(ValueError, match="provenance mismatch"):
        connector._write_metadata(metadata_path, metadata)


def test_retrieve_concatenates_only_requested_dwd_products(
    tmp_path: Path,
) -> None:
    """No directory/global-file request is made when products are selected."""
    compressed = bz2.compress(b"GRIB first")
    connector = DwdIconConnector(
        FakeSession(
            [
                FakeResponse(
                    b'<a href="icon_global_icosahedral_single-level_'
                    b'2026082100_000_T_2M.grib2.bz2">T_2M</a>'
                ),
                FakeResponse(compressed),
            ]
        ),
        sleep=lambda _: None,
        test_raw_root=tmp_path,
    )
    result = connector.retrieve(
        datetime(2026, 8, 21, tzinfo=timezone.utc), fields=("T_2M",)
    )
    assert result.payload_path.read_bytes() == b"GRIB first"
    assert result.size_bytes == len(b"GRIB first")
    assert result.metadata_path.with_name("metadata.json.sha256").exists()
    metadata = result.metadata_path.read_text(encoding="utf-8")
    assert '"aoi_id":"everest-south-route"' in metadata
    assert '"aoi_version":"everest-south-route-v1.0"' in metadata
    decoded = json.loads(metadata)
    assert decoded["valid_time"] == "2026-08-21T00:00:00+00:00"
    assert decoded["valid_time_epoch"] == 1787270400


def test_parser_rejects_non_grib_payload() -> None:
    """Parser cannot turn arbitrary source bytes into an ICON observation."""
    with pytest.raises((RuntimeError, ValueError)):
        parse_grib_bytes(b"not GRIB2")


def _coordinate_messages(
    latitudes: tuple[float, ...],
    longitudes: tuple[float, ...],
) -> tuple[ParsedMessage, ...]:
    """Build matching native coordinate messages for parser validation."""
    timestamp = datetime(2026, 8, 21, tzinfo=timezone.utc)
    grid_uuid = "a27b8de618c411e4820ab5b098c6a5c0"
    return (
        ParsedMessage(
            "tlat",
            timestamp,
            timestamp,
            0,
            latitudes,
            (),
            (),
            "Degree N",
            "surface",
            "unstructured_grid",
            grid_uuid,
        ),
        ParsedMessage(
            "tlon",
            timestamp,
            timestamp,
            0,
            longitudes,
            (),
            (),
            "Degree E",
            "surface",
            "unstructured_grid",
            grid_uuid,
        ),
    )


def test_parser_rejects_mismatched_coordinate_arrays() -> None:
    """Native CLAT and CLON arrays must identify the same point count."""
    with pytest.raises(ValueError, match="lengths differ"):
        _with_native_coordinates(_coordinate_messages((27.0,), (86.0, 87.0)))


@pytest.mark.parametrize("longitude", (-180.01, 180.01))
def test_parser_rejects_invalid_longitude(longitude: float) -> None:
    """DWD longitudes outside canonical [-180, 180] are rejected."""
    with pytest.raises(ValueError, match="longitude range"):
        _with_native_coordinates(_coordinate_messages((27.0,), (longitude,)))


@pytest.mark.parametrize(
    ("latitudes", "longitudes", "error"),
    [
        ((float("nan"),), (86.0,), "latitude range"),
        ((float("inf"),), (86.0,), "latitude range"),
        ((27.0,), (float("nan"),), "longitude range"),
        ((27.0,), (float("inf"),), "longitude range"),
    ],
)
def test_parser_rejects_nonfinite_coordinates(
    latitudes: tuple[float, ...],
    longitudes: tuple[float, ...],
    error: str,
) -> None:
    """NaN and infinite native coordinates fail before normalization."""
    with pytest.raises(ValueError, match=error):
        _with_native_coordinates(_coordinate_messages(latitudes, longitudes))


def test_parser_rejects_coordinate_grid_identity_mismatch() -> None:
    """CLAT and CLON must describe one DWD unstructured provider grid."""
    latitude, longitude = _coordinate_messages((27.0,), (86.0,))
    longitude = replace(longitude, grid_uuid="different-grid")
    with pytest.raises(ValueError, match="grid identities differ"):
        _with_native_coordinates((latitude, longitude))


def _fake_eccodes(on_open: Any) -> ModuleType:
    """Create a native-library-free ecCodes module for file lifecycle tests."""
    module = ModuleType("eccodes")

    def new_from_file(stream: Any) -> None:
        on_open(stream)

    module.codes_grib_new_from_file = new_from_file
    module.codes_get = lambda *_: None
    module.codes_get_array = lambda *_: ()
    module.codes_release = lambda *_: None
    return module


def test_parser_closes_writer_before_eccodes_and_cleans_temp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ecCodes sees a closed writer and no temporary file survives failure."""
    created: list[Path] = []
    writers: list[Any] = []
    real_mkstemp = tempfile.mkstemp
    real_fdopen = os.fdopen

    def tracked_mkstemp(*, suffix: str) -> tuple[int, str]:
        descriptor, path = real_mkstemp(suffix=suffix, dir=tmp_path)
        created.append(Path(path))
        return descriptor, path

    def tracked_fdopen(descriptor: int, mode: str) -> Any:
        writer = real_fdopen(descriptor, mode)
        writers.append(writer)
        return writer

    def fail_after_open(stream: Any) -> None:
        assert stream.read() == b"GRIB fixture"
        assert writers and writers[0].closed
        raise ValueError("synthetic ecCodes failure")

    monkeypatch.setattr(icon_parser.tempfile, "mkstemp", tracked_mkstemp)
    monkeypatch.setattr(icon_parser.os, "fdopen", tracked_fdopen)
    monkeypatch.setitem(sys.modules, "eccodes", _fake_eccodes(fail_after_open))
    with pytest.raises(ValueError, match="synthetic ecCodes failure"):
        parse_grib_bytes(b"GRIB fixture")
    assert created and all(not path.exists() for path in created)


def test_runtime_requires_an_external_configured_raw_root(
    tmp_path: Path,
) -> None:
    """Runtime does not fall back to a project-relative temporary directory."""
    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    external_root = tmp_path / "external"
    external_root.mkdir()
    with pytest.raises(
        RawStorageConfigurationError, match="must be configured"
    ):
        DwdIconConnector(environment={}, repository_root=repository_root)
    with pytest.raises(RawStorageConfigurationError, match="absolute"):
        DwdIconConnector(
            environment={"EVEREST_RAW_ROOT": "relative/raw"},
            repository_root=repository_root,
        )
    with pytest.raises(RawStorageConfigurationError, match="outside"):
        DwdIconConnector(
            environment={"EVEREST_RAW_ROOT": str(repository_root)},
            repository_root=repository_root,
        )
    connector = DwdIconConnector(
        environment={"EVEREST_RAW_ROOT": str(external_root)},
        repository_root=repository_root,
    )
    assert connector.raw_root == external_root.resolve()


def test_retention_rejects_raw_references_outside_external_root(
    tmp_path: Path,
) -> None:
    """Raw files cannot be written through path traversal."""
    connector = DwdIconConnector(test_raw_root=tmp_path)
    with pytest.raises(
        RawStorageReferenceError, match="under raw storage root"
    ):
        connector._resolve_object_reference("../outside.grib2")
    with pytest.raises(
        RawStorageReferenceError, match="under raw storage root"
    ):
        connector._write_verified(
            tmp_path.parent / "outside.grib2",
            b"GRIB",
            connector._sha256(b"GRIB"),
        )


def test_retention_rejects_symlinked_raw_reference_escape(
    tmp_path: Path,
) -> None:
    """A symlink or reparse point cannot redirect raw retention."""
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    escape = raw_root / "escape"
    try:
        escape.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(
            f"directory symlinks unavailable on this Windows host: {error}"
        )
    connector = DwdIconConnector(test_raw_root=raw_root)
    with pytest.raises(
        RawStorageReferenceError, match="under raw storage root"
    ):
        connector._resolve_object_reference("escape/payload.grib2")
