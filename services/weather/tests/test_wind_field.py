"""Bounded wind-field projection and materialization tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import math
from pathlib import Path

import pytest
import xarray as xr

from services.weather.wind_field import (  # pylint: disable=import-error
    WindFieldLimits,
    build_wind_field_frame,
    materialize_wind_field_frame,
)


_CYCLE = datetime(2026, 8, 27, tzinfo=UTC)


def _dataset(
    u: list[list[float]] | None = None,
    v: list[list[float]] | None = None,
) -> xr.Dataset:
    return xr.Dataset(
        data_vars={
            "u": (("latitude", "longitude"), u or [[1.0, 2.0], [3.0, 4.0]]),
            "v": (("latitude", "longitude"), v or [[-1.0, -2.0], [-3.0, -4.0]]),
        },
        coords={
            "latitude": [28.0, 27.5],
            "longitude": [86.5, 87.0],
        },
    )


def _frame(dataset: xr.Dataset | None = None):
    return build_wind_field_frame(
        dataset or _dataset(),
        source="ecmwf-ifs",
        model="IFS",
        cycle=_CYCLE,
        valid_time=_CYCLE + timedelta(hours=6),
        lead=timedelta(hours=6),
        level=400.0,
        level_units="hPa",
        bounds=(86.0, 27.0, 87.5, 28.5),
    )


def test_builds_valid_native_grid_frame_without_interpolation() -> None:
    """Projection preserves native coordinate and C-order vector values."""
    frame = _frame()

    assert frame.source == "ecmwf-ifs"
    assert frame.cycle == "2026-08-27T00:00:00Z"
    assert frame.valid_time == "2026-08-27T06:00:00Z"
    assert frame.lead_seconds == 21600
    assert frame.level == 400.0
    assert frame.bounds == {
        "west": 86.0,
        "south": 27.0,
        "east": 87.5,
        "north": 28.5,
    }
    assert frame.latitude == [28.0, 27.5]
    assert frame.longitude == [86.5, 87.0]
    assert frame.shape == [2, 2]
    assert frame.order == "latitude_longitude_c"
    assert frame.u == [1.0, 2.0, 3.0, 4.0]
    assert frame.v == [-1.0, -2.0, -3.0, -4.0]
    assert frame.units == "m s-1"
    assert frame.minimum == {"u": 1.0, "v": -4.0}
    assert frame.maximum == {"u": 4.0, "v": -1.0}
    assert not frame.quality_flags
    assert frame.schema_version == 1


def test_rejects_wind_dimension_mismatch() -> None:
    """U and V must both align to the two declared coordinate dimensions."""
    dataset = _dataset()
    dataset["v"] = (("latitude",), [-1.0, -2.0])

    with pytest.raises(ValueError, match="same two dimensions"):
        _frame(dataset)


def test_rejects_coordinates_outside_declared_bounds() -> None:
    """Declared AOI bounds must contain every retained source coordinate."""
    with pytest.raises(ValueError, match="outside declared bounds"):
        build_wind_field_frame(
            _dataset(),
            source="ecmwf-ifs",
            model="IFS",
            cycle=_CYCLE,
            valid_time=_CYCLE,
            lead=timedelta(0),
            level=400.0,
            level_units="hPa",
            bounds=(86.6, 27.0, 87.5, 28.5),
        )


def test_converts_nan_to_json_null_and_flags_missing_values() -> None:
    """Missing source cells remain missing and are never interpolated."""
    frame = _frame(_dataset(u=[[1.0, math.nan], [3.0, 4.0]]))

    assert frame.u == [1.0, None, 3.0, 4.0]
    assert frame.minimum["u"] == 1.0
    assert frame.maximum["u"] == 4.0
    assert frame.quality_flags == ["missing_values"]
    assert "NaN" not in json.dumps(frame.to_dict(), allow_nan=False)


def test_rejects_missing_wind_variable() -> None:
    """Both vector components are mandatory for a wind frame."""
    with pytest.raises(KeyError, match="missing wind variable"):
        _frame(_dataset().drop_vars("v"))


def test_rejects_grid_over_point_limit() -> None:
    """Point limits stop unexpectedly large arrays before serialization."""
    with pytest.raises(ValueError, match="point limit"):
        build_wind_field_frame(
            _dataset(),
            source="ecmwf-ifs",
            model="IFS",
            cycle=_CYCLE,
            valid_time=_CYCLE,
            lead=timedelta(0),
            level=400.0,
            level_units="hPa",
            bounds=(86.0, 27.0, 87.5, 28.5),
            limits=WindFieldLimits(max_latitudes=2, max_longitudes=2, max_points=3),
        )


def test_rejects_serialized_frame_over_byte_limit(tmp_path: Path) -> None:
    """Serialized-size limits apply before a derived artifact is written."""
    frame = _frame()

    with pytest.raises(ValueError, match="byte limit"):
        materialize_wind_field_frame(
            frame,
            tmp_path,
            limits=WindFieldLimits(max_serialized_bytes=32),
        )


def test_materialization_is_content_addressed_atomic_and_idempotent(
    tmp_path: Path,
) -> None:
    """Equal content resolves to one stable digest object and latest pointer."""
    frame = _frame()

    first = materialize_wind_field_frame(frame, tmp_path)
    first_stat = first.stat()
    second = materialize_wind_field_frame(frame, tmp_path)

    assert second == first
    assert second.stat().st_mtime_ns == first_stat.st_mtime_ns
    assert first.parent == tmp_path / "wind-field"
    assert first.name.endswith(".json")
    assert json.loads(first.read_text(encoding="utf-8")) == frame.to_dict()
    latest = json.loads(
        (tmp_path / "wind-field" / "latest.json").read_text(encoding="utf-8")
    )
    assert latest == {"sha256": first.stem}
    assert not list((tmp_path / "wind-field").glob("*.tmp"))
