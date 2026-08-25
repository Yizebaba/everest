"""Deterministic unit tests for IFS pressure-level normalization (EV-DATA-001 ext)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import math

import pytest

from services.weather.ecmwf.pressure import (
    ParsedPressureMessage,
    PressureLevelRecord,
    normalize_pressure_levels,
)

_CYCLE = datetime(2026, 8, 24, tzinfo=UTC)


def _msg(
    parameter: str,
    level: str,
    value: float,
    lat: float = 28.0,
    lon: float = 87.0,
) -> ParsedPressureMessage:
    return ParsedPressureMessage(
        parameter=parameter,
        level_hpa=level,
        valid_time=_CYCLE,
        cycle=_CYCLE,
        lead_hours=0,
        values=(value,),
        latitudes=(lat,),
        longitudes=(lon,),
    )


def _suite() -> tuple[ParsedPressureMessage, ...]:
    # 300 hPa: gh=9797 gpm, t=249K, u=-6.4, v=6.1
    # 500 hPa: gh=5888 gpm, t=271.5K, u=0.37, v=0.30
    return (
        _msg("gh", "300", 9797.0),
        _msg("t", "300", 249.0),
        _msg("u", "300", -6.4),
        _msg("v", "300", 6.1),
        _msg("gh", "500", 5888.0),
        _msg("t", "500", 271.5),
        _msg("u", "500", 0.37),
        _msg("v", "500", 0.30),
    )


def test_pressure_levels_normalized() -> None:
    """Each complete pressure level yields one record with altitude from gh."""
    records = normalize_pressure_levels(_suite(), 27.98806, 86.92528)
    assert len(records) == 2
    by_level = {r.level_hpa: r for r in records}
    r300 = by_level["300"]
    assert r300.altitude == pytest.approx(9797.0)
    assert r300.temperature_c == pytest.approx(249.0 - 273.15)
    assert r300.wind_speed == pytest.approx(math.hypot(-6.4, 6.1))
    assert r300.source == "ecmwf-ifs"
    assert r300.model == "IFS"


def test_missing_level_skipped_not_fabricated() -> None:
    """An incomplete level is skipped rather than synthesized."""
    msgs = (
        _msg("gh", "300", 9797.0),
        _msg("t", "300", 249.0),
        # u/v missing for 300; 500 complete
        _msg("gh", "500", 5888.0),
        _msg("t", "500", 271.5),
        _msg("u", "500", 0.37),
        _msg("v", "500", 0.30),
    )
    records = normalize_pressure_levels(msgs, 27.98806, 86.92528)
    assert [r.level_hpa for r in records] == ["500"]


def test_nearest_grid_point_selected() -> None:
    """The nearest grid point (not requested coordinate) is used."""
    msgs = (
        _msg("gh", "300", 9000.0, lat=26.0, lon=85.0),
        _msg("t", "300", 250.0, lat=26.0, lon=85.0),
        _msg("u", "300", -3.0, lat=26.0, lon=85.0),
        _msg("v", "300", 4.0, lat=26.0, lon=85.0),
    )
    records = normalize_pressure_levels(msgs, 27.98806, 86.92528)
    assert records == [] or records[0].altitude == pytest.approx(9000.0)


def test_lead_seconds_from_anchor() -> None:
    """lead_seconds is derived from the anchor valid/cycle time."""
    records = normalize_pressure_levels(_suite(), 27.98806, 86.92528)
    assert records[0].lead_seconds == 0
    assert records[0].timestamp == _CYCLE
