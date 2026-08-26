"""South-route profile elevations and vertical interpolation to camp height.

IFS open data publishes pressure levels, not camp altitudes. A 400 hPa record is
~7600 m: labelling it "C4" (7920 m) or "Summit" (8848.86 m) would misstate the
height its values belong to by hundreds of metres. This module instead
interpolates between the two levels that bracket a camp, in geometric height,
and records which levels were used so the derivation stays inspectable.

No value is ever extrapolated: a camp outside the retrieved level range is
skipped rather than guessed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


# South-col route elevations in metres above mean sea level, taken from the OSM
# ``ele`` tags of the nodes the 3D scene draws its markers from (camp nodes
# 5225912921, 4880806686, 4880806685, 5058632244, 576713400) and of the summit
# peak node 164979149, whose ``ele`` is the 2020 China/Nepal joint survey figure.
# Guidebook heights differ from these by up to ~120 m; using the OSM values keeps
# a camp's weather record at the same altitude as its marker, so the vertical
# profile and the scene cannot disagree about where a camp is.
ROUTE_PROFILE_ELEVATIONS: tuple[tuple[str, float], ...] = (
    ("EBC", 5364.0),
    ("C1", 6060.0),
    ("C2", 6400.0),
    ("C3", 7100.0),
    ("C4", 7920.0),
    ("SUMMIT", 8848.86),
)


@dataclass(frozen=True)
class ProfileSample:
    """One canonical-unit sample interpolated to a named route elevation."""

    profile: str
    elevation: float
    temperature_c: float
    wind_speed: float
    wind_direction: float
    pressure_hpa: float
    lower_level_hpa: str
    upper_level_hpa: str
    lower_altitude: float
    upper_altitude: float

    @property
    def bracket_span(self) -> float:
        """Vertical distance spanned by the two source levels, in metres."""
        return self.upper_altitude - self.lower_altitude


@dataclass(frozen=True)
class _Level:
    """A bracketing source level reduced to what interpolation needs."""

    level_hpa: str
    altitude: float
    temperature_c: float
    u_wind: float
    v_wind: float


def _components(speed: float, direction: float) -> tuple[float, float]:
    """Recover the east/north wind components from speed and true direction.

    Exact inverse of ``direction = (degrees(atan2(-u, -v)) + 360) % 360``, so a
    record that stored only speed and direction can still be interpolated as
    vectors. Averaging directions in degrees instead would turn 350 deg and
    10 deg into a southerly wind.
    """
    radians = math.radians(direction)
    return -speed * math.sin(radians), -speed * math.cos(radians)


def _as_levels(records: Sequence[object]) -> list[_Level]:
    """Reduce pressure-level records to finite, height-sorted levels."""
    levels: list[_Level] = []
    for record in records:
        altitude = float(getattr(record, "altitude"))
        temperature = float(getattr(record, "temperature_c"))
        speed = float(getattr(record, "wind_speed"))
        direction = float(getattr(record, "wind_direction"))
        if not all(
            math.isfinite(value)
            for value in (altitude, temperature, speed, direction)
        ):
            continue
        u_wind = getattr(record, "u_wind", math.nan)
        v_wind = getattr(record, "v_wind", math.nan)
        if not (math.isfinite(u_wind) and math.isfinite(v_wind)):
            u_wind, v_wind = _components(speed, direction)
        levels.append(
            _Level(
                str(getattr(record, "level_hpa")),
                altitude,
                temperature,
                float(u_wind),
                float(v_wind),
            )
        )
    levels.sort(key=lambda level: level.altitude)
    return levels


def interpolate_route_profiles(
    records: Sequence[object],
    elevations: tuple[tuple[str, float], ...] = ROUTE_PROFILE_ELEVATIONS,
) -> list[ProfileSample]:
    """Interpolate pressure-level records to each named route elevation.

    ``records`` are ``PressureLevelRecord``-shaped values that all share one
    valid time and one grid point; mixing valid times here would blend two
    forecast hours into a single sample, so callers must group first.
    """
    levels = _as_levels(records)
    if len(levels) < 2:
        return []
    samples: list[ProfileSample] = []
    for name, elevation in elevations:
        bracket = _bracket(levels, elevation)
        if bracket is None:
            continue  # outside the retrieved levels: skipped, not extrapolated
        lower, upper = bracket
        span = upper.altitude - lower.altitude
        weight = 0.0 if span == 0 else (elevation - lower.altitude) / span
        u_wind = lower.u_wind + weight * (upper.u_wind - lower.u_wind)
        v_wind = lower.v_wind + weight * (upper.v_wind - lower.v_wind)
        samples.append(
            ProfileSample(
                profile=name,
                elevation=elevation,
                temperature_c=(
                    lower.temperature_c
                    + weight * (upper.temperature_c - lower.temperature_c)
                ),
                wind_speed=math.hypot(u_wind, v_wind),
                wind_direction=(
                    math.degrees(math.atan2(-u_wind, -v_wind)) + 360
                )
                % 360,
                # Pressure falls exponentially with height, so it is the one
                # field interpolated in log space rather than linearly.
                pressure_hpa=math.exp(
                    math.log(float(lower.level_hpa))
                    + weight
                    * (
                        math.log(float(upper.level_hpa))
                        - math.log(float(lower.level_hpa))
                    )
                ),
                lower_level_hpa=lower.level_hpa,
                upper_level_hpa=upper.level_hpa,
                lower_altitude=lower.altitude,
                upper_altitude=upper.altitude,
            )
        )
    return samples


def _bracket(
    levels: list[_Level], elevation: float
) -> tuple[_Level, _Level] | None:
    """Return the tightest level pair enclosing an elevation, or None."""
    for lower, upper in zip(levels, levels[1:]):
        if lower.altitude <= elevation <= upper.altitude:
            return lower, upper
    return None
