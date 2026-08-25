"""Summit Window risk engine (EV-RISK-001): transparent rule-based assessment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from services.weather.contract import QualityFlag, WeatherRecord


class RiskLevel(str, Enum):
    """Ordered risk level; most restrictive known factor wins."""

    GO = "go"
    CAUTION = "caution"
    BLOCK = "block"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RiskThresholds:
    """Configurable, transparent thresholds (pending meteorology calibration)."""

    go_max_wind: float = 15.0  # m/s
    caution_max_wind: float = 25.0  # m/s
    precipitation_caution: float = 0.1  # mm
    visibility_caution: float = 200.0  # m
    temperature_caution: float = -25.0  # C


DEFAULT_THRESHOLDS = RiskThresholds()

# Quality flags that make a record unsuitable for scoring (never silently used).
_BLOCKING_FLAGS = frozenset(
    {
        QualityFlag.INVALID_UNIT,
        QualityFlag.INVALID_COORDINATE,
        QualityFlag.INVALID_TIMESTAMP,
        QualityFlag.PROVENANCE_ERROR,
        QualityFlag.CYCLE_TIME_MISMATCH,
    }
)

_LEVEL_ORDER = {
    RiskLevel.GO: 0,
    RiskLevel.CAUTION: 1,
    RiskLevel.BLOCK: 2,
    RiskLevel.UNKNOWN: 3,
}


@dataclass(frozen=True)
class RiskResult:
    """Structured, non-destructive risk assessment for one record."""

    valid_time: datetime
    profile: str
    altitude_metres: float
    level: RiskLevel
    confidence: float
    factors: tuple[dict[str, Any], ...]
    inputs: dict[str, str | int | float | None]

    @property
    def as_dict(self) -> dict[str, Any]:
        """Return a serializable projection (no geometry, no raw metadata)."""
        return {
            "valid_time": self.valid_time.isoformat().replace("+00:00", "Z"),
            "profile": self.profile,
            "altitude_metres": self.altitude_metres,
            "level": self.level.value,
            "confidence": self.confidence,
            "factors": list(self.factors),
            "inputs": dict(self.inputs),
        }


def _risk_for(
    value: float | None, *, low: float, high: float
) -> tuple[RiskLevel, str]:
    """Classify a numeric factor by the configured threshold band."""
    if value is None:
        return RiskLevel.UNKNOWN, "unknown"
    if value <= low:
        return RiskLevel.GO, "favorable"
    if value <= high:
        return RiskLevel.CAUTION, "caution"
    return RiskLevel.BLOCK, "block"


def _classify(
    record: WeatherRecord, thresholds: RiskThresholds
) -> list[tuple[str, RiskLevel, float | None]]:
    """Apply each factor; returns (name, level, value)."""
    factors: list[tuple[str, RiskLevel, float | None]] = []
    level, _risk = _risk_for(
        record.wind_speed,
        low=thresholds.go_max_wind,
        high=thresholds.caution_max_wind,
    )
    factors.append(("wind", level, record.wind_speed))
    if record.precipitation is not None:
        factors.append(
            (
                "precipitation",
                (
                    RiskLevel.CAUTION
                    if record.precipitation > thresholds.precipitation_caution
                    else RiskLevel.GO
                ),
                record.precipitation,
            )
        )
    if record.visibility is not None:
        factors.append(
            (
                "visibility",
                (
                    RiskLevel.CAUTION
                    if record.visibility < thresholds.visibility_caution
                    else RiskLevel.GO
                ),
                record.visibility,
            )
        )
    if record.temperature is not None:
        factors.append(
            (
                "temperature",
                (
                    RiskLevel.CAUTION
                    if record.temperature < thresholds.temperature_caution
                    else RiskLevel.GO
                ),
                record.temperature,
            )
        )
    return factors


def assess(
    record: WeatherRecord,
    thresholds: RiskThresholds = DEFAULT_THRESHOLDS,
    profile: str = "SUMMIT",
) -> RiskResult:
    """Evaluate one canonical record into a transparent risk result.

    Non-destructive: never fabricates, interpolates, or substitutes a missing
    value. A blocking quality flag makes the result ``block`` (never silently
    used). ``profile`` is a filter label only; no geometry is emitted.
    """
    if record.quality_flags.intersection(_BLOCKING_FLAGS):
        return RiskResult(
            valid_time=record.timestamp,
            profile=profile,
            altitude_metres=record.altitude,
            level=RiskLevel.BLOCK,
            confidence=0.0,
            factors=(("quality", RiskLevel.BLOCK, "blocking_flag"),),
            inputs=_inputs(record),
        )

    factors = _classify(record, thresholds)
    known = [f for f in factors if f[1] is not RiskLevel.UNKNOWN]
    confidence = (len(known) / len(factors)) if factors else 0.0
    if not known:
        level = RiskLevel.UNKNOWN
    else:
        level = max((f[1] for f in factors), key=_LEVEL_ORDER.__getitem__)

    factor_view = tuple(
        (
            {"name": name, "value": value, "risk": level.value}
            if value is not None
            else {"name": name, "value": None, "risk": "unknown"}
        )
        for name, level, value in factors
    )
    return RiskResult(
        valid_time=record.timestamp,
        profile=profile,
        altitude_metres=record.altitude,
        level=level,
        confidence=confidence,
        factors=factor_view,
        inputs=_inputs(record),
    )


def _inputs(record: WeatherRecord) -> dict[str, str | int | float | None]:
    """Return bounded, non-secret provenance for the input record."""
    lead_s = (
        int(record.forecast.lead_time.total_seconds())
        if record.forecast is not None
        else None
    )
    return {
        "source": record.source,
        "model": record.model,
        "cycle": (
            record.forecast.cycle.isoformat().replace("+00:00", "Z")
            if record.forecast is not None
            else None
        ),
        "lead_s": lead_s,
    }
