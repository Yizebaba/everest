# pylint: disable=duplicate-code
"""Materialized wind-field API tests with no provider access."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import xarray as xr

from services.weather.wind_field import (  # pylint: disable=import-error
    build_wind_field_frame,
    materialize_wind_field_frame,
)
from everest_api.app import create_app
from everest_api.weather.wind_field import read_latest_wind_field


def _session_must_not_be_opened():
    raise AssertionError("wind-field GET must not open a database session")


def test_unconfigured_wind_field_is_explicitly_unavailable(monkeypatch) -> None:
    """An absent root yields a bounded response without touching dependencies."""
    monkeypatch.delenv("EVEREST_WIND_FIELD_DERIVED_ROOT", raising=False)

    response = TestClient(create_app(_session_must_not_be_opened)).get(
        "/api/weather/wind-field"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "unavailable",
        "reason": "not_configured",
        "frame": None,
    }


def test_configured_empty_root_is_explicitly_unavailable(tmp_path) -> None:
    """A configured root with no latest frame remains an honest empty result."""
    response = TestClient(
        create_app(_session_must_not_be_opened, wind_field_root=tmp_path)
    ).get("/api/weather/wind-field")

    assert response.status_code == 200
    assert response.json() == {
        "status": "unavailable",
        "reason": "no_valid_materialized_frame",
        "frame": None,
    }


def test_get_reads_latest_local_frame_without_provider_or_raw_path(
    tmp_path,
) -> None:
    """GET serves only the latest integrity-checked derived JSON frame."""
    cycle = datetime(2026, 8, 27, tzinfo=UTC)
    dataset = xr.Dataset(
        {
            "u": (("latitude", "longitude"), [[1.0]]),
            "v": (("latitude", "longitude"), [[2.0]]),
        },
        coords={"latitude": [28.0], "longitude": [87.0]},
    )
    frame = build_wind_field_frame(
        dataset,
        source="ecmwf-ifs",
        model="IFS",
        cycle=cycle,
        valid_time=cycle + timedelta(hours=3),
        lead=timedelta(hours=3),
        level=400.0,
        level_units="hPa",
        bounds=(86.5, 27.5, 87.5, 28.5),
    )
    materialize_wind_field_frame(frame, tmp_path)

    response = TestClient(
        create_app(_session_must_not_be_opened, wind_field_root=tmp_path)
    ).get("/api/weather/wind-field")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["frame"] == frame.to_dict()
    assert "path" not in response.text.lower()
    assert "url" not in response.text.lower()


def _write_frame(root: Path, frame: dict) -> None:
    """Write a canonical digest object and pointer for adversarial reader tests."""
    payload = json.dumps(
        frame, allow_nan=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    directory = root / "wind-field"
    directory.mkdir(parents=True)
    (directory / f"{digest}.json").write_bytes(payload)
    (directory / "latest.json").write_text(
        json.dumps({"sha256": digest}), encoding="utf-8"
    )


def _valid_frame() -> dict:
    cycle = datetime(2026, 8, 27, tzinfo=UTC)
    dataset = xr.Dataset(
        {
            "u": (("latitude", "longitude"), [[1.0]]),
            "v": (("latitude", "longitude"), [[2.0]]),
        },
        coords={"latitude": [28.0], "longitude": [87.0]},
    )
    return build_wind_field_frame(
        dataset,
        source="ecmwf-ifs",
        model="IFS",
        cycle=cycle,
        valid_time=cycle + timedelta(hours=3),
        lead=timedelta(hours=3),
        level=400.0,
        level_units="hPa",
        bounds=(86.5, 27.5, 87.5, 28.5),
    ).to_dict()


@pytest.mark.parametrize(
    ("mutation",),
    [
        (lambda frame: frame.update(source="attacker"),),
        (lambda frame: frame.update(model="AIFS"),),
        (lambda frame: frame.update(valid_time="2026-08-27T04:00:00Z"),),
        (lambda frame: frame.update(cycle="20260827T000000Z"),),
        (lambda frame: frame.update(level=float("inf")),),
        (lambda frame: frame.update(units="knots"),),
        (lambda frame: frame.update(latitude=[]),),
        (lambda frame: frame.update(latitude=[29.0]),),
        (lambda frame: frame.update(u=[float("nan")]),),
        (lambda frame: frame.update(minimum={"u": 0.0, "v": 2.0}),),
        (lambda frame: frame.update(quality_flags=["unknown_flag"]),),
    ],
)
def test_reader_rejects_invalid_frame_schema(tmp_path: Path, mutation) -> None:
    """Every public scalar, axis, vector, summary, and flag is fail-closed."""
    frame = _valid_frame()
    mutation(frame)
    _write_frame(tmp_path, frame)

    assert read_latest_wind_field(tmp_path) is None


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unsupported")
def test_reader_rejects_symlink_digest_file(tmp_path: Path) -> None:
    """Digest content is never consumed through a symlink."""
    frame = _valid_frame()
    _write_frame(tmp_path, frame)
    directory = tmp_path / "wind-field"
    pointer = json.loads(
        (directory / "latest.json").read_text(encoding="utf-8")
    )
    target = directory / f"{pointer['sha256']}.json"
    outside = tmp_path / "outside.json"
    target.replace(outside)
    try:
        target.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    assert read_latest_wind_field(tmp_path) is None


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unsupported")
def test_reader_rejects_symlink_latest_file(tmp_path: Path) -> None:
    """The digest pointer is never consumed through a symlink."""
    frame = _valid_frame()
    _write_frame(tmp_path, frame)
    directory = tmp_path / "wind-field"
    pointer = directory / "latest.json"
    outside = tmp_path / "outside-pointer.json"
    pointer.replace(outside)
    try:
        pointer.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    assert read_latest_wind_field(tmp_path) is None


def test_reader_cache_returns_detached_frame(tmp_path: Path) -> None:
    """A caller cannot mutate the digest-keyed process-local cache."""
    frame = _valid_frame()
    _write_frame(tmp_path, frame)

    first = read_latest_wind_field(tmp_path)
    assert first is not None
    first["u"][0] = 999.0

    second = read_latest_wind_field(tmp_path)
    assert second is not None
    assert second["u"] == [1.0]
