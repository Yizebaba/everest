"""Everest AWS observation parser: CSV to UTC canonical rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

NPT_OFFSET = timezone(timedelta(hours=5, minutes=45))


@dataclass(frozen=True)
class AwsObservationRow:
    """One parsed, UTC-normalized observation row.

    Only named columns are used; unnamed provider columns (col3..col7) are
    treated as UNKNOWN and never assigned semantics.
    """

    timestamp: datetime  # UTC, timezone-aware
    temperature_c: float | None
    relative_humidity: float | None
    weather_code: str | None
    precipitation: float | None
    missing: bool

    def to_record(self, station: str) -> dict[str, object]:
        """Project to a canonical observation-shaped record."""
        return {
            "record_type": "observation",
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "source": "everest-aws",
            "model": None,
            "station": station,
            "temperature": self.temperature_c,
            "relative_humidity": self.relative_humidity,
            "precipitation": self.precipitation,
            "weather": self.weather_code,
            "missing": self.missing,
        }


def _parse_float(value: str) -> float | None:
    text = value.strip().upper()
    if text in ("", "NAN", "NULL", "NONE"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_rows(path: Path, station: str) -> list[AwsObservationRow]:
    """Parse a station CSV into UTC-normalized rows.

    Columns are located by header name so station layout differences are
    tolerated. The time column is in Nepal Time (NPT, UTC+5:45). Rows with
    unparsable time are skipped. Unnamed provider columns (col3..col7) are
    never assigned semantics.
    """
    rows: list[AwsObservationRow] = []
    with path.open(encoding="utf-8", errors="replace") as stream:
        header = stream.readline()
        if not header:
            return rows
        columns = [c.strip() for c in header.rstrip("\n").split(",")]
        index = {name: i for i, name in enumerate(columns)}

        def find(*names: str) -> int | None:
            for name in names:
                if name in index:
                    return index[name]
            return None

        time_idx = find("Time (NPT)")
        temp_idx = find("Temperature (Celsius)")
        hum_idx = find("Relative Humidity")
        weather_idx = find("Weather")
        precip_idx = find("Precipitation")
        missing_idx = find("Missing")
        if time_idx is None or temp_idx is None:
            return rows
        for line in stream:
            if not line.strip():
                continue
            fields = [f.strip() for f in line.rstrip("\n").split(",")]
            if len(fields) <= max(
                i for i in (time_idx, temp_idx, hum_idx) if i is not None
            ):
                continue
            try:
                npt_time = datetime.strptime(
                    fields[time_idx], "%Y-%m-%d %H:%M:%S"
                )
            except (ValueError, IndexError):
                continue

            def field(idx: int | None) -> str | None:
                if idx is None or idx >= len(fields):
                    return None
                return fields[idx]

            utc_time = npt_time.replace(tzinfo=NPT_OFFSET).astimezone(
                timezone.utc
            )
            temperature = _parse_float(fields[temp_idx])
            humidity = (
                _parse_float(field(hum_idx)) if hum_idx is not None else None
            )
            weather = field(weather_idx) or None
            precipitation = (
                _parse_float(field(precip_idx))
                if precip_idx is not None
                else None
            )
            missing = (
                (field(missing_idx) or "").strip().lower() == "true"
                if missing_idx is not None
                else False
            )
            rows.append(
                AwsObservationRow(
                    timestamp=utc_time,
                    temperature_c=temperature,
                    relative_humidity=humidity,
                    weather_code=weather,
                    precipitation=precipitation,
                    missing=missing,
                )
            )
    return rows
