"""Network-free retained AIFS GRIB2 parser and normalizer smoke command."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any

from services.weather.aifs.normalizer import (
    nearest_grid_index,
    normalize_messages,
    provider_spatial_key,
)
from services.weather.aifs.parser import parse_grib_bytes


def retained_evidence(
    payload_path: Path, latitude: float, longitude: float
) -> dict[str, Any]:
    """Parse retained bytes and return deterministic factual smoke evidence."""
    messages = parse_grib_bytes(payload_path.read_bytes())
    anchor = messages[0]
    index = nearest_grid_index(anchor, latitude, longitude)
    record = normalize_messages(messages, latitude, longitude)
    weather = asdict(record)
    weather["record_type"] = record.record_type.value
    weather["timestamp"] = record.timestamp.isoformat()
    weather["forecast"] = _forecast_json(record.forecast)
    weather["quality_flags"] = sorted(record.quality_flags)
    return {
        "message_count": len(messages),
        "parameters": [message.parameter for message in messages],
        "units": [message.units for message in messages],
        "levels": [
            {
                "parameter": message.parameter,
                "type": message.level_type,
                "level": message.level,
            }
            for message in messages
        ],
        "generating_process_identifiers": sorted(
            {message.generating_process_identifier for message in messages}
        ),
        "grid_type": anchor.grid_type,
        "ni": anchor.ni,
        "nj": anchor.nj,
        "requested_coordinate": [latitude, longitude],
        "selected_index": index,
        "selected_coordinate": [
            anchor.latitudes[index],
            anchor.longitudes[index],
        ],
        "selected_values": {
            message.parameter: message.values[index] for message in messages
        },
        "spatial_key": provider_spatial_key(anchor, index),
        "canonical_record": weather,
    }


def _forecast_json(value: object) -> dict[str, object] | None:
    """Serialize the known canonical forecast identity for evidence JSON."""
    if value is None:
        return None
    cycle = getattr(value, "cycle")
    lead_time = getattr(value, "lead_time")
    if not isinstance(cycle, datetime) or not isinstance(lead_time, timedelta):
        raise TypeError("canonical forecast identity has unexpected types")
    return {
        "cycle": cycle.isoformat(),
        "lead_seconds": int(lead_time.total_seconds()),
    }


def main() -> None:
    """Print retained artifact evidence as sorted JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--latitude", type=float, default=27.98806)
    parser.add_argument("--longitude", type=float, default=86.92528)
    arguments = parser.parse_args()
    evidence = retained_evidence(
        arguments.payload, arguments.latitude, arguments.longitude
    )
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
