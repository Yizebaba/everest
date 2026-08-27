"""Read-only access to bounded, locally materialized wind-field frames."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_FRAME_BYTES = 16 * 1024 * 1024


# Reading is deliberately fail-closed at each integrity validation guard.
# pylint: disable=too-many-return-statements
def read_latest_wind_field(derived_root: Path | str) -> dict[str, Any] | None:
    """Read and integrity-check the latest local frame without external I/O."""
    root = Path(derived_root)
    if not root.is_absolute():
        return None
    directory = root / "wind-field"
    pointer = directory / "latest.json"
    if not pointer.is_file():
        return None
    try:
        pointer_payload = json.loads(pointer.read_text(encoding="utf-8"))
        digest = pointer_payload["sha256"]
        if set(pointer_payload) != {"sha256"} or not isinstance(digest, str):
            return None
        if not _DIGEST.fullmatch(digest):
            return None
        target = directory / f"{digest}.json"
        if not target.is_file() or target.stat().st_size > _MAX_FRAME_BYTES:
            return None
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            return None
        frame = json.loads(payload)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ):
        return None
    if not _is_public_frame(frame):
        return None
    return frame


def _is_public_frame(frame: Any) -> bool:
    """Reject malformed or expanded payloads before crossing the API boundary."""
    if not isinstance(frame, dict):
        return False
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
    if set(frame) != required or frame.get("schema_version") != 1:
        return False
    if not all(
        isinstance(frame.get(name), str) and bool(_IDENTIFIER.fullmatch(frame[name]))
        for name in ("source", "model")
    ):
        return False
    latitude = frame.get("latitude")
    longitude = frame.get("longitude")
    shape = frame.get("shape")
    vectors = (frame.get("u"), frame.get("v"))
    if not isinstance(latitude, list) or not isinstance(longitude, list):
        return False
    if len(latitude) > 1_000 or len(longitude) > 1_000:
        return False
    expected_shape = [len(latitude), len(longitude)]
    if shape != expected_shape or expected_shape[0] * expected_shape[1] > 250_000:
        return False
    if frame.get("order") != "latitude_longitude_c":
        return False
    point_count = expected_shape[0] * expected_shape[1]
    return all(
        isinstance(vector, list) and len(vector) == point_count for vector in vectors
    )


__all__ = ["read_latest_wind_field"]
