"""Deterministic unit tests for the Summit Window risk engine (EV-RISK-001)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import math

import pytest

from services.risk import (
    DEFAULT_THRESHOLDS,
    RiskLevel,
    RiskResult,
    assess,
    RiskThresholds,
)
from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
)

_UTC = UTC
_NOW = datetime(2026, 8, 25, 6, 0, tzinfo=_UTC)
_SUMMIT_ALT = 6008.05  # grid-point approximation (documented limitation)


def _record(**overrides) -> WeatherRecord:
    base = WeatherRecord(
        record_type=RecordType.FORECAST,
        timestamp=_NOW,
        latitude=27.98806,
        longitude=86.92528,
        altitude=_SUMMIT_ALT,
        wind_speed=12.0,
        wind_direction=90.0,
        temperature=-20.0,
        precipitation=0.0,
        visibility=5000.0,
        source="ecmwf-ifs",
        model="IFS",
        forecast=ForecastIdentity(_NOW, timedelta(hours=6)),
        quality_flags=frozenset(),
    )
    return replace(base, **overrides)


def test_go_when_all_factors_favorable() -> None:
    """A mild record with all factors known yields level=go."""
    result = assess(_record(), DEFAULT_THRESHOLDS)
    assert result.level == RiskLevel.GO
    assert result.confidence == pytest.approx(1.0)


def test_wind_boundary_15_is_go_just_above_is_caution() -> None:
    """15 m/s is favorable; just above 15 is caution (boundary exact)."""
    at_limit = assess(_record(wind_speed=15.0), DEFAULT_THRESHOLDS)
    assert at_limit.level == RiskLevel.GO
    above = assess(_record(wind_speed=15.0001), DEFAULT_THRESHOLDS)
    assert above.level == RiskLevel.CAUTION


def test_wind_boundary_25_is_caution_just_above_is_block() -> None:
    """25 m/s is caution; just above 25 is blocking."""
    at_limit = assess(_record(wind_speed=25.0), DEFAULT_THRESHOLDS)
    assert at_limit.level == RiskLevel.CAUTION
    above = assess(_record(wind_speed=25.0001), DEFAULT_THRESHOLDS)
    assert above.level == RiskLevel.BLOCK


def test_most_restrictive_factor_wins() -> None:
    """A blocking wind overrides a caution precipitation factor."""
    result = assess(
        _record(wind_speed=30.0, precipitation=5.0), DEFAULT_THRESHOLDS
    )
    assert result.level == RiskLevel.BLOCK


def test_precipitation_caution_additive() -> None:
    """Precipitation above 0.1 mm adds a caution factor, not a silent pass."""
    result = assess(
        _record(wind_speed=5.0, precipitation=5.0), DEFAULT_THRESHOLDS
    )
    assert result.level == RiskLevel.CAUTION


def test_visibility_caution() -> None:
    """Known visibility below 200 m contributes caution."""
    result = assess(
        _record(wind_speed=5.0, visibility=100.0), DEFAULT_THRESHOLDS
    )
    assert result.level == RiskLevel.CAUTION


def test_temperature_caution() -> None:
    """Temperature below -25 C contributes caution (exposure)."""
    result = assess(
        _record(wind_speed=5.0, temperature=-30.0), DEFAULT_THRESHOLDS
    )
    assert result.level == RiskLevel.CAUTION


def test_missing_wind_yields_unknown_not_go() -> None:
    """A missing wind factor yields unknown; never go."""
    result = assess(_record(wind_speed=None), DEFAULT_THRESHOLDS)
    assert result.level == RiskLevel.UNKNOWN
    assert result.confidence < 1.0


def test_all_unknown_yields_unknown_zero_confidence() -> None:
    """All factors unknown yields level=unknown and confidence=0.0."""
    result = assess(
        _record(
            wind_speed=None,
            temperature=None,
            precipitation=None,
            visibility=None,
        ),
        DEFAULT_THRESHOLDS,
    )
    assert result.level == RiskLevel.UNKNOWN
    assert result.confidence == 0.0


def test_blocking_quality_flag_blocks() -> None:
    """A record with a blocking flag is never silently used (block)."""
    result = assess(
        _record(quality_flags=frozenset({QualityFlag.INVALID_UNIT})),
        DEFAULT_THRESHOLDS,
    )
    assert result.level == RiskLevel.BLOCK


def test_profile_is_filter_label_not_geometry() -> None:
    """profile output is a label; no coordinate/geometry is emitted."""
    result = assess(_record(), DEFAULT_THRESHOLDS, profile="SUMMIT")
    assert result.profile == "SUMMIT"
    assert not hasattr(result, "coordinates")
    assert result.altitude_metres == pytest.approx(_SUMMIT_ALT)


def test_outputs_source_and_identity() -> None:
    """Inputs provenance is preserved in the result."""
    result = assess(_record(), DEFAULT_THRESHOLDS)
    assert result.inputs["source"] == "ecmwf-ifs"
    assert result.inputs["model"] == "IFS"
    assert result.valid_time == _NOW


def test_unknown_flag_factors_listed() -> None:
    """factors lists each applied factor and its risk; unknown not skipped silently."""
    result = assess(_record(wind_speed=None), DEFAULT_THRESHOLDS)
    names = {f["name"] for f in result.factors}
    assert "wind" in names
    assert result.factors[0]["risk"] in {
        "favorable",
        "caution",
        "block",
        "unknown",
    }
