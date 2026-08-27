"""Bounded wind-field projection and materialization tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import math
import os
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


def _frame(
    dataset: xr.Dataset | None = None,
    *,
    source: str = "ecmwf-ifs",
    model: str = "IFS",
    cycle: datetime = _CYCLE,
    lead: timedelta = timedelta(hours=6),
):
    return build_wind_field_frame(
        dataset or _dataset(),
        source=source,
        model=model,
        cycle=cycle,
        valid_time=cycle + lead,
        lead=lead,
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
            limits=WindFieldLimits(
                max_latitudes=2, max_longitudes=2, max_points=3
            ),
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
    index = json.loads(
        (tmp_path / "wind-field" / "valid-time-index.json").read_text(
            encoding="utf-8"
        )
    )
    assert index == {
        "entries": {
            frame.valid_time: {
                "cycle": frame.cycle,
                "model": frame.model,
                "sha256": first.stem,
                "source": frame.source,
            }
        },
        "schema_version": 1,
    }
    assert not list((tmp_path / "wind-field").glob("*.tmp"))


def test_materialization_updates_index_with_deterministic_winner(
    tmp_path: Path,
) -> None:
    """One exact time deterministically keeps the highest cycle/identity."""
    older_cycle = _CYCLE - timedelta(hours=6)
    gfs = _frame(
        source="noaa-gfs",
        model="GFS",
        cycle=older_cycle,
        lead=timedelta(hours=12),
    )
    ifs = _frame()

    gfs_path = materialize_wind_field_frame(gfs, tmp_path)
    ifs_path = materialize_wind_field_frame(ifs, tmp_path)
    # Re-materializing the lower-ranked candidate must not change selection.
    materialize_wind_field_frame(gfs, tmp_path)

    index = json.loads(
        (tmp_path / "wind-field" / "valid-time-index.json").read_text(
            encoding="utf-8"
        )
    )
    assert index["entries"][ifs.valid_time] == {
        "cycle": ifs.cycle,
        "model": "IFS",
        "sha256": ifs_path.stem,
        "source": "ecmwf-ifs",
    }
    assert gfs_path.exists()
    latest = json.loads(
        (tmp_path / "wind-field" / "latest.json").read_text(encoding="utf-8")
    )
    assert latest == {"sha256": gfs_path.stem}


def test_materialization_tie_breaks_source_and_model_stably(
    tmp_path: Path,
) -> None:
    """Same-cycle model collisions are independent of write ordering."""
    ifs = _frame()
    gfs = _frame(source="noaa-gfs", model="GFS")

    ifs_path = materialize_wind_field_frame(ifs, tmp_path)
    gfs_path = materialize_wind_field_frame(gfs, tmp_path)
    materialize_wind_field_frame(ifs, tmp_path)

    index = json.loads(
        (tmp_path / "wind-field" / "valid-time-index.json").read_text(
            encoding="utf-8"
        )
    )
    assert index["entries"][ifs.valid_time] == {
        "cycle": gfs.cycle,
        "model": "GFS",
        "sha256": gfs_path.stem,
        "source": "noaa-gfs",
    }
    assert ifs_path.exists()


def test_materialization_caps_index_to_newest_valid_times(
    tmp_path: Path,
) -> None:
    """The public lookup index has a hard, deterministic entry bound."""
    limits = WindFieldLimits(max_index_entries=2)
    frames = [
        _frame(cycle=_CYCLE + timedelta(hours=offset), lead=timedelta(0))
        for offset in range(3)
    ]

    for frame in frames:
        materialize_wind_field_frame(frame, tmp_path, limits=limits)

    index = json.loads(
        (tmp_path / "wind-field" / "valid-time-index.json").read_text(
            encoding="utf-8"
        )
    )
    assert list(index["entries"]) == [
        frames[1].valid_time,
        frames[2].valid_time,
    ]


def test_materialization_rejects_corrupt_existing_index(tmp_path: Path) -> None:
    """A corrupt index is not silently trusted or replaced during an update."""
    directory = tmp_path / "wind-field"
    directory.mkdir()
    index = directory / "valid-time-index.json"
    index.write_text('{"schema_version":1,"entries":[]}', encoding="utf-8")

    with pytest.raises(ValueError, match="index"):
        materialize_wind_field_frame(_frame(), tmp_path)
    assert index.read_text(encoding="utf-8") == (
        '{"schema_version":1,"entries":[]}'
    )


def test_materialization_rejects_derived_root_beneath_repository(
    tmp_path: Path,
) -> None:
    """Derived output must not be written into the source repository."""
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    with pytest.raises(ValueError, match="outside repository and raw roots"):
        materialize_wind_field_frame(
            _frame(),
            repository_root / "derived",
            excluded_roots=(repository_root,),
        )


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unsupported")
def test_materialization_rejects_symlink_path_component(tmp_path: Path) -> None:
    """A symlink cannot redirect derived writes to another storage tree."""
    real_root = tmp_path / "real"
    real_root.mkdir()
    linked_root = tmp_path / "linked"
    try:
        linked_root.symlink_to(real_root, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="symlink"):
        materialize_wind_field_frame(_frame(), linked_root)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unsupported")
def test_materialization_rejects_symlink_latest_file(tmp_path: Path) -> None:
    """The latest pointer must never be read through or replace a symlink."""
    directory = tmp_path / "wind-field"
    directory.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("untouched", encoding="utf-8")
    try:
        (directory / "latest.json").symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="symlink"):
        materialize_wind_field_frame(_frame(), tmp_path)
    assert outside.read_text(encoding="utf-8") == "untouched"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unsupported")
def test_materialization_rejects_symlink_index_file(tmp_path: Path) -> None:
    """The exact-time index cannot redirect atomic updates outside storage."""
    directory = tmp_path / "wind-field"
    directory.mkdir()
    outside = tmp_path / "outside-index.json"
    outside.write_text("untouched", encoding="utf-8")
    try:
        (directory / "valid-time-index.json").symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="symlink"):
        materialize_wind_field_frame(_frame(), tmp_path)
    assert outside.read_text(encoding="utf-8") == "untouched"
