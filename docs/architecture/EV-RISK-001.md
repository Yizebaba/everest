# EV-RISK-001 — Summit Window Risk Engine (architecture)

**Assignment:** `EV-RISK-001`  
**Status:** Architecture; implementation follows only after this design is
reviewed and approved. `services/risk/` does not exist yet; this is a **new**
module, not a modification of any tested engine.
**Owner:** architect + meteorology (thresholds) + backend (service)

## Purpose

A transparent, **rule-based** (non-AI) assessment that combines canonical
weather values at the Summit/C4 altitudes into a Summit Window indicator. It is
a pure presentation/decision-support layer: it never changes canonical weather
fields, source health, or the weather API contract. The Summit Window UI
remains independent of this module until integration is separately approved
(PRD FR-SW-005: no `services/risk/` integration and no AI).

## Inputs

Consumed from the canonical weather records only (the five Everest APIs and
their underlying tables). For a target camp/altitude (default Summit):

- `wind_speed` (m/s)
- `wind_direction` (degrees, used only contextually, e.g. cross-slope)
- `temperature` (C)
- `precipitation` (mm)
- `visibility` (m, nullable)
- forecast identity (`source`, `model`, `cycle`, `lead`, `valid_time`)
- `quality_flags` (additive; a record with a blocking flag is not silently used)

All inputs are read-only; the engine never fabricates, interpolates, or
substitutes a missing value.

> **Altitude limitation (review note):** canonical records carry the provider
> grid-point altitude (e.g. 6008 m / 5830 m), not the summit's 8848 m. The
> engine evaluates the nearest grid-point weather as a documented approximation
> of summit conditions; it does not claim an exact summit measurement. This
> limitation is part of the output metadata, not hidden.

## Rule contract (configurable thresholds, default values)

Thresholds are a reviewed configuration (extended from the frontend
`SUMMIT_THRESHOLDS`: `goMaxWind=15`, `cautionMaxWind=25` m/s). Defaults below
are **demonstration defaults pending meteorology calibration** — they are not
claimed as validated summit-safety thresholds until the meteorology owner
confirms them. Thresholds are the only place where calibration happens; the
rule logic itself is fixed and transparent.

| Factor | Condition (at target altitude) | Risk contribution |
| --- | --- | --- |
| Wind | `wind_speed <= 15` | favorable |
| Wind | `15 < wind_speed <= 25` | caution |
| Wind | `wind_speed > 25` | blocking |
| Precipitation | `> 0.1 mm` in window | caution (slab/ice) |
| Visibility | known and `< 200 m` | caution |
| Temperature | `< -25 C` (exposure) | caution |
| Data quality | missing wind/visibility with no fallback | unknown / not-scored |

Output `level` is the **most restrictive** factor: `block`, `caution`, `go`, or
`unknown`. `factors` lists each applied factor and its value; `confidence` is
the fraction of scored factors that are known (never overstates unknown data).
If **all** factors are unknown, `level` is `unknown` and `confidence` is `0.0`.

## Output contract

```text
{
  "valid_time": "…",            // matching the input record
  "profile": "SUMMIT",           // filter label only; never a coordinate/geometry
  "altitude_metres": 6008.05,    // grid-point altitude used (approximation note)
  "level": "go" | "caution" | "block" | "unknown",
  "confidence": 0.0..1.0,       // fraction of scored factors with known values
  "factors": [
    {"name": "wind", "value": 18.2, "risk": "caution"},
    {"name": "temperature", "value": -22.0, "risk": "favorable"}
  ],
  "inputs": {"source": "ecmwf-ifs", "model": "IFS", "cycle": "…", "lead_s": 0}
}
```

Rules are additive and non-destructive: a missing factor yields `unknown`, not
`go`. No value is fabricated. `profile` is a route/camp **filter label** only
and never implies or carries a camp coordinate or geometry (per AOI/PRD: no
invented named-feature geometry).

## Module boundaries

- `services/risk/` — pure functions: `assess(records, thresholds) -> RiskResult`.
  Imports only stdlib and the canonical `WeatherRecord` shape; no FastAPI,
  SQLAlchemy, HTTP, or AWS.
- `apps/api` may expose `GET /api/risk/summit` later (separate authorization);
  this architecture defines the engine only, not the endpoint.
- The frontend Summit Window panel stays independent (FR-SW-005) until a
  separate integration decision.

## Acceptance criteria

1. Deterministic unit tests cover threshold boundaries (15/25), missing data,
   blocking flags, and additive factor rules.
2. Output level is always the most restrictive known factor; unknown data
   never becomes `go`; all-unknown yields `unknown` with confidence `0.0`.
3. No AI, no ML, no learned weights; thresholds are configuration and marked
   as pending meteorology calibration.
4. `profile` is a filter label only and never emits a camp coordinate or
   geometry; grid-point altitude is reported with an explicit approximation
   note.
5. Weather semantics and API contracts unchanged; no frontend integration in
   this module.
6. `black`, `pylint`, `compileall` pass; tests green.

## Sequence

1. Approve this architecture.
2. Implement `services/risk/` (pure engine) + tests (TDD).
3. Optional later: backend endpoint + frontend integration (separate
   authorization).
