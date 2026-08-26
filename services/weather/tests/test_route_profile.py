"""Tests for vertical interpolation from IFS pressure levels to camp heights."""

from __future__ import annotations

import math

import pytest

from services.weather.ecmwf.pressure import PressureLevelRecord
from services.weather.route_profile import (
    ROUTE_PROFILE_ELEVATIONS,
    interpolate_route_profiles,
)

from datetime import datetime, timezone


CYCLE = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)


def _level(
    level_hpa: str,
    altitude: float,
    temperature_c: float,
    u_wind: float,
    v_wind: float,
) -> PressureLevelRecord:
    """Build one pressure-level record at a known height and wind vector."""
    speed = math.hypot(u_wind, v_wind)
    direction = (math.degrees(math.atan2(-u_wind, -v_wind)) + 360) % 360
    return PressureLevelRecord(
        level_hpa=level_hpa,
        timestamp=CYCLE,
        cycle=CYCLE,
        lead_seconds=0,
        altitude=altitude,
        temperature_c=temperature_c,
        wind_speed=speed,
        wind_direction=direction,
        u_wind=u_wind,
        v_wind=v_wind,
        latitude=28.0,
        longitude=87.0,
    )


def _full_column() -> list[PressureLevelRecord]:
    """A six-level column spanning the whole south-side route."""
    return [
        _level("850", 1550.0, 10.0, 2.0, 0.0),
        _level("700", 3150.0, -2.0, 4.0, 0.0),
        _level("600", 4400.0, -10.0, 6.0, 0.0),
        _level("500", 5900.0, -20.0, 10.0, 0.0),
        _level("400", 7600.0, -34.0, 20.0, 0.0),
        _level("300", 9800.0, -50.0, 40.0, 0.0),
    ]


def test_every_named_camp_is_produced_from_a_full_column() -> None:
    """A full column brackets all six route elevations."""
    samples = interpolate_route_profiles(_full_column())
    assert [sample.profile for sample in samples] == [
        name for name, _ in ROUTE_PROFILE_ELEVATIONS
    ]


def test_summit_is_interpolated_between_400_and_300_hpa() -> None:
    """The 8848.86 m summit comes from the two levels that enclose it."""
    samples = {s.profile: s for s in interpolate_route_profiles(_full_column())}
    summit = samples["SUMMIT"]
    assert summit.elevation == pytest.approx(8848.86)
    assert (summit.lower_level_hpa, summit.upper_level_hpa) == ("400", "300")
    weight = (8848.86 - 7600.0) / (9800.0 - 7600.0)
    assert summit.temperature_c == pytest.approx(-34.0 + weight * -16.0)
    assert summit.wind_speed == pytest.approx(20.0 + weight * 20.0)
    assert summit.bracket_span == pytest.approx(2200.0)
    # Pressure is interpolated in log space: the summit sits at ~340 hPa, not
    # the ~357 hPa a linear blend of 400 and 300 would claim.
    assert summit.pressure_hpa == pytest.approx(
        math.exp(math.log(400.0) + weight * (math.log(300.0) - math.log(400.0)))
    )
    assert 330.0 < summit.pressure_hpa < 345.0


def test_an_exact_level_height_reproduces_that_level() -> None:
    """Interpolation at a level's own height returns that level's values."""
    column = _full_column()
    samples = interpolate_route_profiles(column, (("C2", 5900.0),))
    assert samples[0].temperature_c == pytest.approx(-20.0)
    assert samples[0].wind_speed == pytest.approx(10.0)
    assert samples[0].pressure_hpa == pytest.approx(500.0)


def test_elevations_outside_the_column_are_skipped_not_extrapolated() -> None:
    """A camp above the highest retrieved level yields no sample."""
    column = [
        _level("850", 1550.0, 10.0, 2.0, 0.0),
        _level("700", 3150.0, -2.0, 4.0, 0.0),
    ]
    assert interpolate_route_profiles(column) == []


def test_a_single_level_cannot_be_interpolated() -> None:
    """One level is not a column: nothing is produced."""
    assert interpolate_route_profiles(_full_column()[:1]) == []


def test_wind_direction_is_interpolated_as_a_vector() -> None:
    """Opposing bearings across a bracket average through the components."""
    column = [
        _level("400", 7600.0, -34.0, 0.0, 10.0),  # from the south, 180 deg
        _level("300", 9800.0, -50.0, 10.0, 0.0),  # from the west, 270 deg
    ]
    samples = interpolate_route_profiles(column, (("MID", 8700.0),))
    assert samples[0].wind_direction == pytest.approx(225.0)
    assert samples[0].wind_speed == pytest.approx(math.hypot(5.0, 5.0))


def test_speed_and_direction_alone_are_enough_to_interpolate() -> None:
    """Records without stored components fall back to inverting the bearing."""
    from dataclasses import replace

    column = [
        replace(level, u_wind=math.nan, v_wind=math.nan)
        for level in _full_column()
    ]
    samples = {
        s.profile: s for s in interpolate_route_profiles(column)
    }
    assert samples["SUMMIT"].wind_speed == pytest.approx(
        20.0 + (8848.86 - 7600.0) / 2200.0 * 20.0
    )


def test_non_finite_levels_are_dropped_before_bracketing() -> None:
    """A level with a NaN height cannot bracket anything."""
    from dataclasses import replace

    column = _full_column()
    column[-1] = replace(column[-1], altitude=math.nan)
    samples = {s.profile: s for s in interpolate_route_profiles(column)}
    assert "SUMMIT" not in samples
    assert samples["C3"].upper_level_hpa == "400"
