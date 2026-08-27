"""Read-only access to bounded, locally materialized wind-field frames."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_MAX_FRAME_BYTES = 16 * 1024 * 1024
_MAX_POINTS = 250_000
_MAX_AXIS = 1_000
_MAX_CACHE_ENTRIES = 8
_MAX_INDEX_ENTRIES = 512
_MAX_INDEX_BYTES = 256 * 1024
_MAX_WIND_COMPONENT = 150.0
_APPROVED_SOURCE_MODELS = {("ecmwf-ifs", "IFS"), ("noaa-gfs", "GFS")}
_ALLOWED_FLAGS = {"missing_values"}
_CACHE: OrderedDict[str, dict[str, Any]] = OrderedDict()
_INDEX_NAME = "valid-time-index.json"


def read_latest_wind_field(  # pylint: disable=too-many-return-statements,too-many-branches
    derived_root: Path | str,
) -> dict[str, Any] | None:
    """Read and integrity-check the latest local frame without external I/O."""
    root = Path(derived_root)
    if not root.is_absolute():
        return None
    resolved_root = root.resolve(strict=False)
    excluded_roots = [Path(__file__).resolve().parents[4]]
    configured_raw_root = os.environ.get("EVEREST_RAW_ROOT")
    if configured_raw_root:
        raw_root = Path(configured_raw_root)
        if raw_root.is_absolute():
            excluded_roots.append(raw_root.resolve(strict=False))
    for excluded in excluded_roots:
        try:
            resolved_root.relative_to(excluded)
            return None
        except ValueError:
            try:
                excluded.relative_to(resolved_root)
                return None
            except ValueError:
                pass
    directory = root / "wind-field"
    pointer = directory / "latest.json"
    try:
        _reject_symlink_components(directory)
        pointer_payload = json.loads(
            _read_regular(pointer, 1_024),
            parse_constant=_bad,
            object_pairs_hook=_unique_object,
        )
        if not isinstance(pointer_payload, dict) or set(pointer_payload) != {
            "sha256"
        }:
            return None
        digest = pointer_payload["sha256"]
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            return None
        target = directory / f"{digest}.json"
        payload = _read_regular(target, _MAX_FRAME_BYTES)
        if hashlib.sha256(payload).hexdigest() != digest:
            return None
        cached = _CACHE.get(digest)
        if cached is not None:
            _CACHE.move_to_end(digest)
            return deepcopy(cached)
        frame = json.loads(
            payload, parse_constant=_bad, object_pairs_hook=_unique_object
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ):
        return None
    if not _is_public_frame(frame):
        return None
    _CACHE[digest] = deepcopy(frame)
    _CACHE.move_to_end(digest)
    while len(_CACHE) > _MAX_CACHE_ENTRIES:
        _CACHE.popitem(last=False)
    return deepcopy(frame)


def read_wind_field_at(  # pylint: disable=too-many-return-statements
    derived_root: Path | str, valid_time: datetime
) -> dict[str, Any] | None:
    """Read an exact local frame from current and forecast-lead storage.

    Selection uses bounded per-root indexes. It performs no directory scan,
    provider, GRIB, database, or network access and validates the selected frame.
    """
    if valid_time.tzinfo is None or valid_time.utcoffset() != timedelta(0):
        return None
    expected = valid_time.isoformat().replace("+00:00", "Z")
    root = _validated_root(derived_root)
    if root is None:
        return None
    candidates: list[tuple[dict[str, str], Path]] = []
    for storage_root in (root, root / "forecast-leads"):
        directory = storage_root / "wind-field"
        try:
            _reject_symlink_components(directory)
            entry = _read_index_entry(directory / _INDEX_NAME, expected)
        except FileNotFoundError:
            continue
        except ValueError:
            return None
        except OSError:
            continue
        if entry is not None:
            candidates.append((entry, directory))
    if not candidates:
        return None
    entry, directory = max(
        candidates,
        key=lambda candidate: _index_rank(candidate[0]),
    )
    target = directory / f"{entry['sha256']}.json"
    frame, _ = _read_digest_frame(target)
    if frame is None or not _frame_matches_index(frame, expected, entry):
        return None
    return deepcopy(frame)


def _validated_root(derived_root: Path | str) -> Path | None:
    root = Path(derived_root)
    if not root.is_absolute():
        return None
    resolved_root = root.resolve(strict=False)
    excluded_roots = [Path(__file__).resolve().parents[4]]
    configured_raw_root = os.environ.get("EVEREST_RAW_ROOT")
    if configured_raw_root:
        raw_root = Path(configured_raw_root)
        if raw_root.is_absolute():
            excluded_roots.append(raw_root.resolve(strict=False))
    for excluded in excluded_roots:
        try:
            resolved_root.relative_to(excluded)
            return None
        except ValueError:
            try:
                excluded.relative_to(resolved_root)
                return None
            except ValueError:
                pass
    return root


def _read_index_entry(path: Path, expected: str) -> dict[str, str] | None:
    value = json.loads(
        _read_regular(path, _MAX_INDEX_BYTES),
        parse_constant=_bad,
        object_pairs_hook=_unique_object,
    )
    if not isinstance(value, dict) or set(value) != {
        "entries",
        "schema_version",
    }:
        raise ValueError("invalid wind-field index")
    if (
        not isinstance(value["schema_version"], int)
        or isinstance(value["schema_version"], bool)
        or value["schema_version"] != 1
    ):
        raise ValueError("invalid wind-field index")
    if not isinstance(value["entries"], dict):
        raise ValueError("invalid wind-field index")
    entries = value["entries"]
    if len(entries) > _MAX_INDEX_ENTRIES:
        raise ValueError("invalid wind-field index")
    if any(
        not _valid_index_entry(valid_time, entry)
        for valid_time, entry in entries.items()
    ):
        raise ValueError("invalid wind-field index")
    return entries.get(expected)


def _valid_index_entry(valid_time: Any, entry: Any) -> bool:
    return (
        _timestamp(valid_time) is not None
        and isinstance(entry, dict)
        and set(entry) == {"cycle", "model", "sha256", "source"}
        and _timestamp(entry["cycle"]) is not None
        and (entry["source"], entry["model"]) in _APPROVED_SOURCE_MODELS
        and isinstance(entry["sha256"], str)
        and bool(_DIGEST.fullmatch(entry["sha256"]))
    )


def _index_rank(entry: dict[str, str]) -> tuple[datetime, str, str, str]:
    cycle = _timestamp(entry["cycle"])
    if cycle is None:  # The complete index is validated before selection.
        raise ValueError("invalid wind-field index")
    return cycle, entry["source"], entry["model"], entry["sha256"]


def _frame_matches_index(
    frame: dict[str, Any],
    expected: str,
    entry: dict[str, str],
) -> bool:
    return (
        frame["valid_time"] == expected
        and frame["cycle"] == entry["cycle"]
        and frame["source"] == entry["source"]
        and frame["model"] == entry["model"]
    )


def _read_digest_frame(target: Path) -> tuple[dict[str, Any] | None, int]:
    digest = target.stem
    try:
        payload = _read_regular(target, _MAX_FRAME_BYTES)
        if hashlib.sha256(payload).hexdigest() != digest:
            return None, len(payload)
        cached = _CACHE.get(digest)
        if cached is not None:
            _CACHE.move_to_end(digest)
            return deepcopy(cached), len(payload)
        frame = json.loads(
            payload, parse_constant=_bad, object_pairs_hook=_unique_object
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ):
        return None, 0
    if not _is_public_frame(frame):
        return None, len(payload)
    _cache_frame(digest, frame)
    return deepcopy(frame), len(payload)


def _cache_frame(digest: str, frame: dict[str, Any]) -> None:
    _CACHE[digest] = deepcopy(frame)
    _CACHE.move_to_end(digest)
    while len(_CACHE) > _MAX_CACHE_ENTRIES:
        _CACHE.popitem(last=False)


# Exact ``type`` checks intentionally reject bool, an int subclass.
def _is_public_frame(  # pylint: disable=too-many-return-statements,too-many-branches,too-many-locals,unidiomatic-typecheck
    frame: Any,
) -> bool:
    """Fully validate the versioned public frame before returning it."""
    required = {
        "source",
        "model",
        "cycle",
        "valid_time",
        "lead_seconds",
        "level",
        "level_units",
        "bounds",
        "latitude",
        "longitude",
        "u",
        "v",
        "shape",
        "order",
        "units",
        "minimum",
        "maximum",
        "quality_flags",
        "schema_version",
    }
    if not isinstance(frame, dict) or set(frame) != required:
        return False
    if type(frame["schema_version"]) is not int or frame["schema_version"] != 1:
        return False
    if (frame["source"], frame["model"]) not in _APPROVED_SOURCE_MODELS:
        return False
    if frame["level_units"] != "hPa" or frame["units"] != "m s-1":
        return False
    if frame["order"] != "latitude_longitude_c":
        return False
    lead = frame["lead_seconds"]
    if type(lead) is not int or lead < 0:
        return False
    cycle = _timestamp(frame["cycle"])
    valid_time = _timestamp(frame["valid_time"])
    try:
        expected_valid_time = cycle + timedelta(seconds=lead) if cycle else None
    except OverflowError:
        return False
    if cycle is None or valid_time != expected_valid_time:
        return False
    if not _finite_number(frame["level"]):
        return False
    bounds = _bounds(frame["bounds"])
    if bounds is None:
        return False
    latitude = _axis(frame["latitude"], _MAX_AXIS)
    longitude = _axis(frame["longitude"], _MAX_AXIS)
    if latitude is None or longitude is None:
        return False
    west, south, east, north = bounds
    if min(latitude) < south or max(latitude) > north:
        return False
    if min(longitude) < west or max(longitude) > east:
        return False
    shape = frame["shape"]
    if (
        not isinstance(shape, list)
        or len(shape) != 2
        or any(type(item) is not int or item <= 0 for item in shape)
    ):
        return False
    point_count = len(latitude) * len(longitude)
    if point_count > _MAX_POINTS or shape != [len(latitude), len(longitude)]:
        return False
    u_values = _vector(frame["u"], point_count)
    v_values = _vector(frame["v"], point_count)
    if u_values is None or v_values is None:
        return False
    flags = frame["quality_flags"]
    if (
        not isinstance(flags, list)
        or len(flags) != len(set(flags))
        or any(
            type(flag) is not str or flag not in _ALLOWED_FLAGS
            for flag in flags
        )
    ):
        return False
    has_missing = any(value is None for value in (*u_values, *v_values))
    if ("missing_values" in flags) != has_missing:
        return False
    return _summaries_match(frame, u_values, v_values)


def _summaries_match(
    frame: dict[str, Any], u_values: list, v_values: list
) -> bool:
    for name in ("minimum", "maximum"):
        summary = frame[name]
        if not isinstance(summary, dict) or set(summary) != {"u", "v"}:
            return False
        if any(
            value is not None and not _finite_number(value)
            for value in summary.values()
        ):
            return False
    expected_minimum = {
        "u": _summary(u_values, min),
        "v": _summary(v_values, min),
    }
    expected_maximum = {
        "u": _summary(u_values, max),
        "v": _summary(v_values, max),
    }
    return (
        frame["minimum"] == expected_minimum
        and frame["maximum"] == expected_maximum
    )


def _summary(values: list[float | None], operation) -> float | None:
    present = [value for value in values if value is not None]
    return operation(present) if present else None


def _vector(value: Any, size: int) -> list[float | None] | None:
    if not isinstance(value, list) or len(value) != size:
        return None
    if any(
        item is not None
        and (not _finite_number(item) or abs(item) > _MAX_WIND_COMPONENT)
        for item in value
    ):
        return None
    return value


def _axis(value: Any, limit: int) -> list[float] | None:
    if not isinstance(value, list) or not value or len(value) > limit:
        return None
    if any(not _finite_number(item) for item in value):
        return None
    differences = [right - left for left, right in zip(value, value[1:])]
    if differences and not (
        all(difference > 0 for difference in differences)
        or all(difference < 0 for difference in differences)
    ):
        return None
    return value


def _bounds(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, dict) or set(value) != {
        "west",
        "south",
        "east",
        "north",
    }:
        return None
    west, south, east, north = (
        value[name] for name in ("west", "south", "east", "north")
    )
    if not all(_finite_number(item) for item in (west, south, east, north)):
        return None
    if not -180 <= west < east <= 180 or not -90 <= south <= north <= 90:
        return None
    return west, south, east, north


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not _UTC_TIMESTAMP.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError:
        return None
    return (
        parsed
        if parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)
        else None
    )


def _finite_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(
        value
    )  # exact type rejects bool


def _read_regular(path: Path, maximum_bytes: int) -> bytes:
    if path.is_symlink():
        raise ValueError("derived file must not be a symlink")
    flags = (
        os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(path, flags)
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode) or status.st_size > maximum_bytes:
            raise ValueError("derived file must be a bounded regular file")
        blocks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            block = os.read(descriptor, min(remaining, 1024 * 1024))
            if not block:
                break
            blocks.append(block)
            remaining -= len(block)
        payload = b"".join(blocks)
        if len(payload) > maximum_bytes:
            raise ValueError("derived file exceeds byte limit")
        return payload
    finally:
        os.close(descriptor)


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("derived path must not contain symlinks")


def _bad(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key rejected")
        result[key] = value
    return result


__all__ = ["read_latest_wind_field", "read_wind_field_at"]
