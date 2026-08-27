# PRD: EV-UI-001 — Everest Frontend UI (Milestone 1: Weather / Forecast Display)

**Delivery line:** EV-UI-001 — Frontend UI (deferred EV-DATA-001 A-F display)
**Status:** In `/plan-ceo-review` — 5 scope expansions adopted 2026-08-24
**Author:** Product (Everest Manager board) — `docs/management/board.md`
**Last Updated:** 2026-08-27
**Version:** 0.3
**Stakeholders:** Everest Manager, Architect, GIS/3D, Meteorology, Backend, Frontend, QA, Release
**Authorization:** ADR-017 (`docs/management/decisions.md`) — approved 2026-08-24
**Lifecycle stage:** `/plan-ceo-review` (in progress; expansions adopted). Stages follow `AGENTS.md`:
PRD → `/plan-ceo-review` → architecture → `/plan-eng-review` → UI →
`/plan-design-review` → implementation → `/review` → QA → release.

---

## 1. Executive Summary (press release)

Everest puts the Summit Window decision on a single 3D map. An expedition
planner, a meteorologist, or a climbing operator opens the Everest scene, sees
the approved Everest Area of Interest (AOI) rendered in three dimensions, and
reads — from Everest-owned data only — the current weather, the multi-model
forecast timeline, the vertical profile across the south-route camps, and the
health of the data sources behind every number. No browser ever dials ECMWF,
NOAA, DWD, or any other external provider: every value on screen comes from the
five Everest REST APIs built and tested in EV-DATA-001. Milestone 1 delivered
the read-only weather/forecast display surface. HEAD now also includes the
Cesium 3D scene, OSM South Col route/camp overlay (EV-OSM-002), terrain /
observation / satellite REST routes, and a rule-based Summit Window engine at
`services/risk/`. Remaining separately scoped work is production/shared
deployment (Gate C-Operational), EV-OSM-001 vector basemap, EV-TERRAIN-002 3D
Tiles, EV-SAT-002 additional satellite, and persisted ADR-019 ingestion. The
screen tells the truth about the data — including when there is no data.

## 2. Problem Statement

Expedition teams on the Everest south side make Summit Window decisions —
"do we leave C4 tonight?" — under high stakes and hard time pressure. They need
weather context across altitude (EBC through the Summit), across models
(ECMWF IFS, ECMWF AIFS, NOAA GFS, DWD ICON), and across the forecast timeline,
all tied to the terrain and route they are actually on.

The data foundation already exists: EV-DATA-001 A-F produced a canonical
weather model in PostgreSQL and five backend REST APIs that return real
canonical records (forecast is retained-evidenced; the other four routes are
implemented with an accepted historical evidence gap — ADR-015/ADR-016). What
did not exist at the 2026-08-24 PRD cut is any way for a human to see that
data. HEAD now has the Next.js + Cesium UI in `apps/web`.

The cost of not solving this: the Everest data pipeline produces canonical
weather records that no one can read; Summit Window decisions continue to be
made from scattered provider pages; and the project has no demonstration
surface for stakeholders, QA, or users.

**Evidence:**
- ADR-017 authorizes the Frontend UI line and explicitly defers the A-F
  "display" requirement to this delivery.
- ADR-015 defines "display" for the A-F surface as five queryable APIs that
  return real canonical data; ADR-016 records that only
  `GET /api/weather/forecast` has retained real-data HTTP evidence.
- `docs/api/API.md` defines the exact contracts for the five APIs.
- `docs/meteorology/weather-spec.md` defines the canonical weather fields,
  units, record types, and quality flags the UI must render.
- `docs/everest-aoi.md` defines the approved AOI center
  `27.98806, 86.92528` and scope the map must respect.

## 3. Product Vision

A 3D digital twin of the Everest south-side route that turns approved,
canonical weather data into a Summit Window decision surface: the expedition
planner, meteorologist, and climbing operator see *where* conditions matter,
*what* the models say, *when* the window opens, and *how much to trust* the
data — without ever touching an external provider, inventing geometry, or
overstating data health.

The north-star outcome is a **well-informed Summit Window decision supported by
verifiable, canonical data**.

### Goals for Milestone 1 (EV-UI-001 MVP)

| Goal | Target |
| --- | --- |
| Make the five Everest APIs visible to humans | All five APIs consumed and rendered from real canonical data in a controlled validation run |
| Provide a Summit Window assessment surface | Summit-region conditions summarized transparently from canonical forecast/current records |
| Keep the frontend fully inside the Everest data boundary | Zero direct external-provider calls from the browser |
| Show data truthfully | Lifecycle status, health, timestamps, sources, and quality flags rendered without overstating verification |

## 4. Success Metrics

Success is defined at three levels, aligned with the A-F display acceptance
definition in ADR-015 (the five APIs are queryable and return real canonical
data).

| Metric | Baseline | Target | Measurement window |
| --- | --- | --- | --- |
| API integration completeness | 0/5 APIs consumed by a UI | 5/5 APIs queried and rendered with real canonical records in a controlled validation run | MVP acceptance |
| Direct external-provider calls from the browser | n/a (no UI) | 0 (verified by network inspection in review/QA) | MVP acceptance |
| Summit Window assessment task success | n/a | 100% of tested assessment tasks completed without invented data | Usability pass during QA |
| Truthful health display | n/a | 100% of source/health states rendered per ADR-004 semantics; no presence-as-verified | QA |
| Initial scene load (bundle + baseline scene, no external data) | n/a | < 5 s on reference broadband laptop | QA (NFR-PERF-001) |
| Data-panel render after fetch | n/a | < 2 s for documented record counts on validation environment | QA (NFR-PERF-002) |
| Regression on backend/API contract | none | 0 changes to the five API contracts or canonical semantics | Review/QA |

Historical disposable acceptance facts from EV-DATA-001 are not current
operational health. Where the backend reports `unknown` health (the truthful
state after teardown), the UI must render that state; success is measured
against the validation run authorized for this delivery, not against a claimed
live service.

## 5. Non-Goals / Out of Scope

### Explicitly out of scope for the original EV-UI-001 MVP (2026-08-24)

The bullets below are the original MVP non-goals. They are **not** a claim
that HEAD still lacks these surfaces. Current-state notes follow each item.

- **Satellite layers** (Himawari-8/9, Sentinel-1/2, Landsat 8/9) — original
  MVP deferred `EV-SAT-001`. HEAD serves `/api/satellite/segments` and a local
  RGB overlay; EV-SAT-002 additional satellite remains separately scoped.
- **Terrain overlays beyond a baseline scene** (Copernicus DEM GLO-30 tiles,
  3D Tiles terrain service, PostGIS terrain pipeline) — original MVP deferred
  `EV-TERRAIN-001`. HEAD serves `/api/terrain/tile`; Cesium World Terrain is
  optional via ion token; EV-TERRAIN-002 3D Tiles remains separately scoped.
- **Route/camp geometry on the map** — original MVP forbade invented
  coordinates. HEAD overlays OSM South Col route/camps from
  `/api/everest/route` (EV-OSM-002).
- **Observations** (Everest AWS, Pyramid network) — original MVP deferred
  `EV-AWS-STATION-001` / `EV-PYRAMID-001`. HEAD serves
  `/api/observations/current`.
- **OpenStreetMap / environmental layers** — original MVP deferred OSM.
  HEAD has EV-OSM-002 South Col overlay; EV-OSM-001 vector basemap remains
  separately scoped. Local NaturalEarthII TMS is the offline globe fallback.
- **AI and Risk** — original MVP kept Summit Window as presentation-only.
  HEAD has a rule-based engine at `services/risk/` (not AI). The UI STOP
  label maps to engine BLOCK.
- **Multi-language UI** — original MVP was English-only. Phase 1 was explicitly
  expanded by the Everest Manager on 2026-08-27 to `en | zh` with one typed
  message catalog shape and a top navigation switch.
- **Write/control features** — the frontend is read-only. Unchanged.
- **WebSocket live streams** — REST only. Unchanged.
- **New backend endpoints** — original MVP consumed exactly the five weather
  APIs. HEAD also serves terrain, observations, satellite, Everest route,
  `/healthz`, and `/readyz`.
- **Production deployment / GA** — still blocked by Gate C-Operational
  (ADR-013/ADR-017). Local UI against a controlled environment is in HEAD.

## 6. Target Users and Personas

| Persona | Context | Needs in MVP | Success signal |
| --- | --- | --- | --- |
| **Expedition Planner** | Plans south-side Everest expeditions; owns go/no-go timing | See the forecast timeline and Summit-region conditions in one place; understand which sources/models agree | Completes a Summit Window assessment from the UI alone |
| **Meteorologist** | Reads the canonical weather data professionally | Compare models (IFS/AIFS/GFS/ICON), inspect vertical profiles by camp label, check quality flags | Can validate the display against the canonical record values |
| **Climber / Operator** | In-the-field decision maker, time-poor, high stakes | Fast read of current conditions at the Summit region; clear error/empty states; trust signals | Finds the current Summit condition in < 30 s and can assess data freshness |
| **Admin / Data steward** | Oversees data-source health and lifecycle | See truthful lifecycle status and health per source; distinguish `verified` (historical) from current health | Can confirm the UI does not overstate verification |

## 7. Data & API Surface (grounding for requirements)

### 7.1 The five consumed APIs (exact, from `docs/api/API.md`)

| Endpoint | Contract summary | Consumed by |
| --- | --- | --- |
| `GET /api/weather/current` | Up to 100 persisted canonical records, descending valid-time; optional `source` filter; body `{ "records": [CanonicalWeatherRecord] }` | Current weather display, map markers |
| `GET /api/weather/forecast` | Persisted `forecast` records ordered by valid time; optional UTC `start`, `end`, `source`; naive/non-UTC/reversed ranges rejected HTTP 422; body `{ "records": [...] }` | Forecast timeline, time navigation |
| `GET /api/weather/profile` | Requires `profile` ∈ {`EBC`, `C1`, `C2`, `C3`, `C4`, `SUMMIT`} (case-insensitive); unsupported → HTTP 422; filters connector-supplied labels only; body `{ "profile": "...", "records": [...] }` | Vertical profile view |
| `GET /api/weather/sources` | `{ "sources": [...] }` with source ID, lifecycle status, operational health, last persisted success time; excludes endpoints, credentials, raw metadata | Sources panel |
| `GET /api/data-health` | `{ "sources": [...] }` with source ID, persisted health status, last success/failure times; no presence-as-health inference | Health panel |

`CanonicalWeatherRecord` preserves the canonical units and includes
`record_type`, `timestamp`, coordinates/altitude, core meteorology values,
`spatial_key`, `source`, `model`, forecast identity, and additive
`quality_flags`. Timestamps are UTC ISO-8601 `Z`. Responses never expose raw
paths, provider URLs, hashes, raw metadata, retention, hold, disposition, or
audit fields; the UI must not request or display them.

### 7.2 Canonical weather contract (`docs/meteorology/weather-spec.md`)

Core fields and units the UI renders: `timestamp` (UTC ISO-8601), `latitude` /
`longitude` (decimal degrees), `altitude` (m), `wind_speed` (m/s),
`wind_direction` (0–360 deg, null for calm), `temperature` (°C),
`precipitation` (mm), `visibility` (m). Recommended fields shown when present:
`pressure` (Pa), `relative_humidity` (%), `dew_point` (°C), `cloud_cover` (%),
`cloud_base` / `cloud_top` (m), `snowfall` (mm), `gust_speed` (m/s), `source`,
`model`, `forecast_cycle`, `forecast_lead_time`, `quality_flags`.

> **Wire-key decision:** the frontend contract uses **`quality_flags`** (array),
> per the API response contract in `docs/api/API.md`. `docs/meteorology/
> weather-spec.md` spells it `quality_flag` (single); the PRD pins the API wire
> key and this naming conflict is escalated to the meteorology and backend
> owners for reconciliation in the architecture handoff.

`record_type` is one of `forecast` | `observation` | `satellite` | `derived`;
the UI distinguishes forecast from observation and labels the others exactly.

`quality_flags` is an additive list: `clean`, `missing_value`, `out_of_range`,
`invalid_timestamp`, `invalid_coordinate`, `invalid_unit`, `duplicate`,
`stale`, `provenance_error`, `cycle_time_mismatch`. The UI renders flags as
labels, never hides records, and never imputes values.

### 7.3 Data boundary rules (mandatory)

1. The frontend MUST NOT call ECMWF, NOAA, DWD, or any other external source.
   The only permitted flow is: `external source → connector → raw data →
   parser → normalizer → QC → canonical model → PostgreSQL/PostGIS or object
   storage → service → REST/WS → frontend` (AGENTS.md).
2. The UI must not invent camp/route geometry. Camp labels
   (EBC/C1/C2/C3/C4/SUMMIT) are filter labels only.
3. Data scope is the approved AOI: Everest south-side route and the area
   within the approved radii from center `27.98806, 86.92528`
   (`docs/everest-aoi.md`). The map must not request global data.
4. No AI and no Risk-engine output in the MVP.

## 8. User Stories

### P0 — MVP core (must be demonstrable at acceptance)

| ID | Story | API | UI component |
| --- | --- | --- | --- |
| US-01 | As an expedition planner, I want to open a 3D scene centered on the Everest AOI so I can orient myself before reading weather. | none (canonical AOI artifact) | Everest map view |
| US-02 | As a climber/operator, I want to see the current weather at the Everest region so I can assess immediate conditions. | `GET /api/weather/current` | Current weather display, map markers |
| US-03 | As a meteorologist, I want a forecast timeline for the Everest region so I can assess the coming Summit Window. | `GET /api/weather/forecast` | Forecast display, time navigation |
| US-04 | As a meteorologist, I want the vertical profile filtered by EBC/C1/C2/C3/C4/SUMMIT labels so I can compare conditions across altitude. | `GET /api/weather/profile` | Vertical profile view |
| US-05 | As an expedition planner, I want a Summit Window indicator summarizing canonical conditions at the Summit region so I can make a go/no-go assessment. | `GET /api/weather/current` + `GET /api/weather/forecast` (+ `profile=SUMMIT` when present) | Summit Window panel |
| US-06 | As an admin, I want to see per-source lifecycle and health so I can trust — or question — the data. | `GET /api/weather/sources`, `GET /api/data-health` | Sources/health panel |

### P1 — Important for trust and usability

| ID | Story | API | UI component |
| --- | --- | --- | --- |
| US-07 | As any user, I want distinct error and empty states so I can tell "no data" from "API failure". | all five | Error/empty states |
| US-08 | As a meteorologist, I want to filter forecasts by `source` and see `model` so I can compare IFS/AIFS/GFS/ICON. | `GET /api/weather/forecast` | Forecast display, source filter |
| US-09 | As an expedition planner, I want to step through forecast valid times so I can see how conditions evolve. | `GET /api/weather/forecast` | Time navigation |
| US-10 | As any user, I want every value labeled with its canonical unit and UTC timestamp so I can interpret it correctly. | all five | Display conventions |
| US-11 | As a meteorologist, I want to see quality flags so I can judge data confidence. | current/forecast/profile | Record detail |

### P2 — Polish and accessibility

| ID | Story | API | UI component |
| --- | --- | --- | --- |
| US-12 | As an admin, I want the UI to reflect truthful health semantics (`unknown`, `stale`, `healthy`) without ever implying presence = verified. | `GET /api/data-health`, `GET /api/weather/sources` | Sources/health panel |
| US-13 | As a user with assistive technology, I want keyboard access and screen-reader labels for all UI chrome and a non-visual alternative for the map, so I can use the tool. | all five | Entire UI |
| US-14 | As a user on a machine without WebGL, I want a clear fallback (not a blank screen) so I know why the map is unavailable and can still read the data panels. | all five | Map fallback |

### P0/P1 — Accepted scope expansions (adopted at `/plan-ceo-review`, 2026-08-24)

| ID | Story | API | UI component |
| --- | --- | --- | --- |
| US-15 | As an expedition planner, I want a Summit Window scoreboard that synthesizes cross-source conditions into a green/amber/red state with per-source agreement and staleness, so I can make a go/no-go call at a glance. | current + forecast (+ profile=SUMMIT when present) | Summit Window panel |
| US-16 | As a meteorologist, I want to step through the available forecast valid times so I can watch how conditions evolve; step granularity is data-dependent (provider leads differ, e.g. 3/6/12-hourly) and the UI never fabricates intermediate timestamps. | `GET /api/weather/forecast` | Time navigation (animation) |
| US-17 | As any user, I want to click any displayed value and see its provenance (model, cycle, lead time, quality flags, retrieval time) so I can trust or question it. | current/forecast/profile | Provenance / record detail |
| US-18 | As a planner, I want a camp altitude ladder (EBC→C1→C2→C3→C4→SUMMIT) so I can compare conditions at every stage at a glance. | `GET /api/weather/profile` | Camp altitude ladder |
| US-19 | As a meteorologist, I want model disagreement (min/max/median across IFS/AIFS/GFS/ICON) for wind/temperature/visibility so I can gauge forecast uncertainty. | `GET /api/weather/forecast` (+ sources) | Model disagreement view |

## 9. Functional Requirements

### 9.1 Everest map view (`apps/web/src/cesium*` / `apps/web/src/map*` — gis-3d owned)

- **FR-MAP-001** — The scene initializes with CesiumJS centered on the approved
  AOI center `27.98806, 86.92528` at a default camera position that frames the
  AOI. Default camera parameters are recorded in the architecture handoff.
- **FR-MAP-002** — The MVP renders the approved AOI boundary from the canonical
  project-owned GeoJSON artifact (`docs/everest-south-route-v1.0-expanded-
  2000km.geojson`, the only serialized expanded polygon). Record markers are
  restricted to records whose coordinates pass the 100 km geodesic-membership
  test from center `27.98806, 86.92528` (per `docs/everest-aoi.md`), and the
  default camera frames the 100 km operational scope. No other geometry is
  rendered.
- **FR-MAP-003** — Canonical weather records are rendered as markers only at
  their record `latitude`/`longitude` and record `altitude`, plotted on the
  ellipsoid and deliberately NOT terrain-clamped (the MVP baseline has no
  terrain; clamping would invent ground height). Markers are styled by `source`
  and `record_type`; selecting a marker shows the canonical record values with
  units and UTC time.
- **FR-MAP-004** — No camp or route geometry is invented. EBC/C1/C2/C3/C4/SUMMIT
  appear only as filter labels in panels (profile filter, Summit Window basis).
  The map never places a camp marker at a fabricated coordinate, and no route
  polyline is drawn from invented points.
- **FR-MAP-005** — The baseline scene uses only locally owned assets and the
  CesiumJS ellipsoid. The frontend must not fetch terrain, imagery, or any data
  from external providers. Everest-owned terrain/tileset consumption is
  **deferred entirely to line `EV-TERRAIN-001`** and MUST NOT be consumed in the
  MVP.
- **FR-MAP-006** — The map does not request or render data outside the AOI; no
  global dataset requests, no world-wide imagery dependency.
- **FR-MAP-007** — Without WebGL/GPU support, the map area shows a clear,
  accessible fallback message while all data panels remain functional
  (US-14).

### 9.2 Summit Window panel

- **FR-SW-001** — The panel summarizes Summit-region conditions derived ONLY
  from canonical records: the `profile=SUMMIT` forecast/current records when
  present, otherwise the forecast record minimizing geodesic distance to the
  summit center `27.98806, 86.92528` within 25 km, tie-broken by highest
  `altitude`. If no record passes the 25 km test, the panel renders the empty
  state (FR-ERR-003). Records carrying any **non-clean** `quality_flags` entry
  render as "unavailable" per FR-SW-004 (`clean` is always present and never
  suppresses display). It displays `temperature`, `wind_speed`,
  `wind_direction`, `visibility`, and `precipitation` with canonical units.
- **FR-SW-002** — Every displayed value carries its data basis: UTC
  `timestamp`, `source`, `model`, `forecast_cycle`/`forecast_lead_time` when
  applicable, `spatial_key`, and `quality_flags`.
- **FR-SW-003** — The panel applies documented, configurable threshold framing
  (e.g., wind-speed bands) to label conditions. The framing rules, their
  source, and their non-authoritative nature are displayed. This is a
  presentation-layer summary of canonical values — not a Risk-engine, AI, or
  derived record.
- **FR-SW-004** — Missing, null, or quality-flagged values render as
  "unavailable" with the flag shown; zero and imputed values are never
  displayed as real data.
- **FR-SW-005** — The panel has no integration with `services/risk/` and no AI
  dependency in the MVP.
- **FR-SW-006** — The panel adds a Summit Window **scoreboard**: a
  green/amber/red state derived transparently from canonical record values and
  documented, configurable thresholds (same basis as FR-SW-003). The scoreboard
  never invents data; it is a presentation-layer summary only.
- **FR-SW-007** — The scoreboard shows **per-source agreement** (how many of the
  present sources/models fall into each band) and **staleness** (from record
  `timestamp` and source `last_success_at`). Disagreement and stale data are
  shown, never hidden.
- **FR-SW-008** — The scoreboard is explicitly labeled as non-authoritative,
  presentation-layer framing. It is not a Risk-engine result, an AI prediction,
  or a derived record (per ADR boundaries).
- **FR-SW-009** — Multi-API composition degradation: the Summit Window panel
  (current + forecast + profile=SUMMIT) and the ladder (six profile calls)
  define explicit partial-failure behavior. The scoreboard renders from
  successfully loaded sources only; failed sources are listed as unavailable
  with an error hint (FR-ERR-002), and the panel never synthesizes a score from
  missing inputs. A panel with no successfully loaded inputs renders the empty
  state (FR-ERR-003), not a fabricated assessment.

### 9.3 Weather current / forecast display

- **FR-WX-001** — The UI queries `GET /api/weather/current` and
  `GET /api/weather/forecast` with documented query parameters and renders the
  returned `records`.
- **FR-WX-002** — All values are rendered with canonical units and labels:
  temperature °C, wind_speed m/s, wind_direction ° (0–360), precipitation mm,
  visibility m, altitude m, timestamps UTC ISO-8601 with trailing `Z`.
- **FR-WX-003** — Each record shows `record_type`, `source`, `model`,
  `forecast_cycle`, `forecast_lead_time`, and `spatial_key` when present.
  `forecast` vs `observation` vs `satellite` vs `derived` are visually
  distinct.
- **FR-WX-004** — The forecast view supports a `source` filter and a UTC
  time-range filter. The UI applies the same UTC rules as the backend
  (RFC 3339 with explicit zero offset; naive/non-UTC/reversed ranges rejected
  before request) so users get immediate validation.
- **FR-WX-005** — Empty responses render an explicit empty state
  ("no data for this selection and time range") that is visually and
  semantically distinct from an error state.
- **FR-WX-006** — `quality_flags` are displayed as additive labels on the
  record; flagged records are shown, never hidden or corrected.
- **FR-WX-007** — Data freshness is displayed from record `timestamp` and, for
  sources, `last_success_at`; the UI does not invent freshness.

### 9.4 Vertical profile view

- **FR-PRO-001** — The UI queries `GET /api/weather/profile` with exactly one
  of the labels `EBC`, `C1`, `C2`, `C3`, `C4`, `SUMMIT` (presented as filter
  chips; case-insensitive per the API contract). Unsupported values are
  blocked client-side.
- **FR-PRO-002** — Forecast and observation records are rendered distinctly and
  can be toggled separately.
- **FR-PRO-003** — The profile chart uses each record's actual `altitude` for
  the vertical axis and canonical values (e.g., `temperature`, `wind_speed`)
  for the horizontal axis. Altitudes are never replaced by labels, and no
  altitude is invented.
- **FR-PRO-004** — A legitimate empty profile result (records with null
  `route_profile` do not match a named label) renders the empty state with an
  explanation; it is not an error.
- **FR-PRO-005** — Profile labels never produce map geometry (FR-MAP-004).

### 9.5 Sources / health panel

- **FR-SRC-001** — The panel queries `GET /api/weather/sources` and
  `GET /api/data-health` and renders the returned `sources`.
- **FR-SRC-002** — Lifecycle status (`planned`, `configured`, `connected`,
  `verified`, `degraded`, `disabled`) and operational health (`unknown`,
  `healthy`, `stale`, `failed`, `degraded`, `disabled`) are displayed as two
  distinct, labeled fields per ADR-004 semantics.
- **FR-SRC-003** — `last_success_at` / `last_failure_at` are shown as UTC
  timestamps.
- **FR-SRC-004** — The panel never implies that a source's presence or
  lifecycle status means current health. `unknown` health is rendered as a
  truthful state, and historical `verified` is never presented as current
  verification (ADR-004 / AGENTS.md health semantics).
- **FR-SRC-005** — The UI displays only the public allow-list fields; it never
  requests or renders endpoints, credentials, raw paths, hashes, retention,
  hold, disposition, or audit data.

### 9.6 Time navigation

- **FR-TIME-001** — The forecast view supports stepping/playing across the
  distinct `timestamp` (valid-time) values present in the loaded records.
- **FR-TIME-002** — The timeline is bounded by the available records; the UI
  clamps navigation to the fetched extent and, when a server-side range filter
  is active, respects it.
- **FR-TIME-003** — All timestamps render as UTC ISO-8601 with `Z`. Any
  local-time display, if added, must be explicitly labeled as local and must
  never replace the UTC label.
- **FR-TIME-004** — A play/scrub control animates the loaded forecast across its
  distinct valid-time extent; the active time drives the forecast panel and the
  map markers, and every rendered value at a scrubbed time stays provenance-
  traceable (FR-PRV-001).
- **FR-TIME-005** — Animation is bounded to the fetched records, clamps at the
  extent (FR-TIME-002), and never issues new requests beyond the active server
  range; pause/step controls are keyboard-accessible (NFR-ACC).

### 9.7 Provenance / record detail (accepted expansion)

- **FR-PRV-001** — Every displayed value is clickable to a provenance panel
  showing the canonical record identity: `timestamp`, `source`, `model`,
  `forecast_cycle`, `forecast_lead_time`, `spatial_key`, `record_type`, and
  `quality_flags`. This applies to the map markers, forecast/current panels,
  Summit Window panel, profile view, ladder, and disagreement view.
- **FR-PRV-002** — The provenance panel renders the source lifecycle status and
  operational health (from `GET /api/weather/sources` / `GET /api/data-health`)
  for the record's source, without implying current `verified` health. No
  credentials, endpoints, raw paths, or hashes are requested or rendered
  (FR-SRC-005).

### 9.8 Camp altitude ladder (accepted expansion)

- **FR-LAD-001** — The ladder renders EBC/C1/C2/C3/C4/SUMMIT as a vertical
  strip driven by `GET /api/weather/profile`, which accepts **exactly one label
  per call** (API.md), so the ladder issues six profile queries (one per label,
  issued in parallel where possible). Each label shows `temperature`,
  `wind_speed`, `wind_direction`, `visibility` using the record's actual
  `altitude`. Labels remain filter labels; no map geometry is produced
  (FR-MAP-004).
- **FR-LAD-002** — Ladder cells whose profile label has no matching records
  render the empty state with explanation (FR-PRO-004); forecast and
  observation records remain visually distinct (FR-PRO-002). **Partial
  degradation:** if one or more of the six profile queries fails, the ladder
  renders the labels that returned successfully and shows the failed ones as
  unavailable with an error hint (per FR-ERR-002); it never substitutes or
  invents values.

### 9.9 Model disagreement (accepted expansion)

- **FR-DIS-001** — For a selected valid time and variable (`temperature`,
  `wind_speed`, `visibility`), the UI shows the min/max/median across the
  present sources/models from the loaded forecast records. Alignment rule:
  exact valid-time match across sources when present; otherwise each source's
  nearest valid time is used and **labeled as such** (provider lead grids
  differ, e.g. 3/6/12-hourly). Cross-grid and cross-`spatial_key` comparison is
  a presentation-layer choice, not a canonical fact, and is disclosed in the
  view. Only present canonical values are used; absent sources are noted, never
  imputed.
- **FR-DIS-002** — The disagreement view is labeled as a presentation-layer
  summary of canonical values (not a Risk/AI/derived record) and each point
  remains provenance-traceable (FR-PRV-001).

### 9.10 Error / empty / loading states

- **FR-ERR-001** — API unreachable: actionable error message with a retry
  action. The API client sends an `X-Correlation-ID` header on each request and
  surfaces the backend's echoed value on error (API.md: the header is echoed
  when the client sends it).
- **FR-ERR-002** — HTTP 4xx/5xx responses are distinguished; HTTP 422 input
  validation errors call out the offending parameter.
- **FR-ERR-003** — Empty datasets show "no data for this selection" with the
  most likely cause (e.g., null `route_profile`, empty time range) when known.
- **FR-ERR-004** — Loading states are shown for every async panel; stale-data
  indications are derived from record timestamps and health fields only.
- **FR-ERR-005** — The UI never renders fabricated, interpolated, or cached
  fallback data as if it were canonical API data.

## 10. Non-Functional Requirements

### Performance

- **NFR-PERF-001** — Initial scene load (bundle + baseline scene, no external
  data) completes in < 5 s on a reference broadband laptop
  (Chrome latest, 8 GB RAM, discrete or integrated WebGL2 GPU).
- **NFR-PERF-002** — Data panels render within 2 s of fetch completion on the
  validation environment. Assumed fetch bound for the MVP: `current` ≤ 100
  records (API cap); `forecast` fetches the latest available cycle's lead-time
  extent for the selected source (or all sources) without a time filter unless
  the user narrows it. Concrete page sizes are recorded in the architecture
  handoff and NFR-PERF-002/003 targets are measured against that documented
  bound (contingent, not self-referential).
- **NFR-PERF-003** — The UI remains responsive (no main-thread stall > 200 ms)
  while rendering map markers and profile charts for the documented record
  counts defined for NFR-PERF-002.

### Availability & resilience

- **NFR-AVAIL-001** — When the backend is unreachable, the UI remains usable:
  scene renders from local assets and every data panel shows a truthful error
  state with retry.
- **NFR-AVAIL-002** — The UI treats `unknown`/`stale` health truthfully and
  never fabricates a healthy status (US-12).

### Accessibility

- **NFR-ACC-001** — UI chrome (panels, tables, filters, buttons, forms)
  meets WCAG 2.1 AA: keyboard operable, focus visible, sufficient contrast,
  semantic markup, ARIA labels.
- **NFR-ACC-002** — The 3D canvas is provided a non-visual alternative: a
  textual data table of loaded canonical records is accessible without the map
  (US-13).
- **NFR-ACC-003** — Error and empty states are announced to assistive
  technology (live regions).

### Browser support

- **NFR-BRW-001** — Supported: latest two stable versions of Chrome, Edge,
  Firefox, Safari. CesiumJS WebGL2 requirement is declared; without WebGL the
  map fallback is shown (FR-MAP-007).

### Security

- **NFR-SEC-001** — No secrets, API keys, tokens, or credentials exist in the
  frontend bundle or repository. Only non-secret runtime configuration (e.g.,
  API base URL) is injected at build/deploy time.
- **NFR-SEC-002** — The frontend calls only Everest-owned REST/WS APIs. A
  network-level verification (review/QA inspection of the built app) confirms
  zero requests to ECMWF, NOAA, DWD, or any external provider.
- **NFR-SEC-003** — Backend CORS is configured for the documented frontend
  origin(s) with a minimal allow-list; the architecture handoff records the
  exact origins and methods.
- **NFR-SEC-004** — The app ships with a Content-Security-Policy, no inline
  scripts, and subresource integrity where feasible. The UI never requests or
  displays raw storage references, hashes, retention, or audit fields
  (FR-SRC-005).

### Internationalization readiness

- **NFR-I18N-001** — User-facing Phase 1 strings live in a typed message catalog
  with matching English and Chinese keys. Switching locale updates visible
  labels, accessible names, and `document.documentElement.lang`; canonical
  units, provider/model IDs, coordinates, and data values never change.

### Engineering standards

- **NFR-ENG-001** — TypeScript per AGENTS.md: ES modules, named exports,
  `const` by default, single quotes, `interface` for props, `import type` for
  type-only imports, `??` for nullish fallback. Before delivery:
  `prettier --write`, `eslint`, `tsc --noEmit`.
- **NFR-ENG-002** — All API responses are validated against typed contracts
  derived from `docs/api/API.md`; unknown fields are ignored, required fields
  are checked, and unit/record-type invariants follow the canonical contract.

## 11. Acceptance Criteria

Acceptance aligns with the A-F display definition (ADR-015): the five APIs are
queryable and return real canonical data, consumed by the UI.

1. **AC-01 — API completeness.** In a controlled validation run authorized by
   the Everest Manager (per ADR-016: substantive validation objective, QA plan,
   random non-standard port, disposable environment, teardown procedure), the
   UI successfully queries and renders real canonical records from all five
   APIs: `current`, `forecast`, `profile`, `sources`, `data-health`.
2. **AC-02 — External-source isolation.** Network inspection of the built
   application shows zero requests to ECMWF, NOAA, DWD, or any other external
   provider; all data requests target Everest-owned API origins.
3. **AC-03 — No invented geometry.** No camp/route geometry is rendered from
   fabricated coordinates; camp labels are filter labels only; the only
   geometric overlay is the approved AOI artifact.
4. **AC-04 — Canonical fidelity.** Every rendered value matches the canonical
   units and semantics of `docs/meteorology/weather-spec.md`; `record_type`
   and `quality_flags` are displayed distinctly; null values are rendered as
   unavailable, never as zero/imputed.
5. **AC-05 — Truthful health.** Lifecycle vs health semantics follow
   ADR-004; `unknown` health renders as unknown; presence is never rendered as
   verified or healthy.
6. **AC-06 — Error/empty correctness.** Empty and error states are distinct,
   actionable, and never fabricate data (FR-ERR-001–005).
7. **AC-07 — Accessibility.** WCAG 2.1 AA checks pass for UI chrome; map has a
   non-visual alternative; WebGL fallback verified.
8. **AC-08 — Performance.** NFR-PERF-001/002/003 targets met in the validation
   environment.
9. **AC-09 — No backend regression.** The five API contracts and canonical
   semantics are unchanged by this delivery; backend suites remain green on the
   validation run.
10. **AC-10 — Quality gates.** `prettier`, `eslint`, `tsc --noEmit` pass;
     QA records tests, failures, and teardown evidence per `AGENTS.md` before
     release consideration.
11. **AC-11 — Summit Window scoreboard.** The green/amber/red scoreboard renders
     from canonical values only, shows per-source agreement and staleness, and
     is labeled non-authoritative; no Risk/AI/derived claim
     (FR-SW-006–009).
12. **AC-12 — Provenance.** Every displayed value opens a provenance panel with
     the canonical record identity and source health, without requesting
     restricted fields (FR-PRV-001/002).
13. **AC-13 — Camp ladder & disagreement.** The camp altitude ladder renders all
     six profile labels (EBC/C1/C2/C3/C4/SUMMIT) from the profile API with actual
     altitudes and empty-state handling; the model-disagreement view shows
     min/max/median from present sources only, never imputed (FR-LAD-001/002,
     FR-DIS-001/002).
14. **AC-14 — Time animation.** Play/scrub animation runs within the fetched
     extent, stays provenance-traceable at every scrubbed time, and is
     keyboard-accessible (FR-TIME-004/005).

## 12. Dependencies and Delivery Order

### 12.1 Lifecycle stages (mandatory order, `AGENTS.md`)

| # | Stage | Input | Output / gate |
| --- | --- | --- | --- |
| 1 | PRD | This document | Approved PRD (this delivery) |
| 2 | `/plan-ceo-review` | PRD | Vision/scope decision |
| 3 | Architecture | Approved scope | `docs/architecture/architecture.md` update (frontend architecture, API client, scene composition, CORS/env plan) |
| 4 | `/plan-eng-review` | Architecture | Execution plan locked |
| 5 | UI | Architecture | Design system / screen mockups |
| 6 | `/plan-design-review` | UI artifacts | Design acceptance |
| 7 | Implementation | Approved design | Frontend code under `apps/web/` |
| 8 | `/review` | Implementation | Code review PASS |
| 9 | QA | Reviewed build | `docs/qa/test-plan.md` update; acceptance evidence |
| 10 | Release | QA PASS | Release gate — **blocked until Gate C-Operational** (ADR-013/ADR-017) |

### 12.2 Cross-domain ownership (AGENTS.md)

- `apps/web/src/cesium*`, `apps/web/src/map*` → **gis-3d** owns the Cesium
  scene, map markers, and AOI rendering.
- `apps/web/src/` excluding Cesium/map paths → **frontend** owns panels, API
  client, state, i18n catalog, accessibility.
- Backend API behavior → **backend** (no changes expected; the UI consumes the
  contract).
- Weather semantics → **meteorology** (consulted for canonical rendering rules).
- QA and release → **qa** and **release** per delivery stages.

EV-UI-001 is therefore a cross-domain delivery: frontend leads, gis-3d owns the
scene paths, and all changes respect the ownership table.

### 12.3 Blocking dependencies

| Dependency | Owner | Status / note |
| --- | --- | --- |
| ADR-017 authorization | Everest Manager | Done (2026-08-24) |
| Validation API run with real canonical data | backend + QA + Everest Manager | **Required for AC-01.** ADR-016 requires a new explicit Manager assignment with a substantive validation objective; the UI validation run is that assignment. |
| Gate C-Operational blocks DB-005, RUNTIME-006, SECRETS-007, AUDIT-008, QA-009, RELEASE-010 | security/release/backend | **Blocks release only**, not development or validation. EV-GATEC-OP-ACL-001 is in progress (board 2026-08-24). |
| `docs/gis/terrain-spec.md` baseline | gis-3d | Needed to document the baseline scene and camera/model constraints for `cesium*` paths. |
| Canonical AOI artifact | gis-3d | Exists: `docs/everest-south-route-v1.0-expanded-2000km.geojson` (project-owned, ~14 KB). |
| EV-TERRAIN-001 (terrain tiles / 3D Tiles) | gis-3d | **Not a dependency of the MVP.** Route/terrain enhancements beyond the baseline scene belong to that separate line. |

### 12.4 Internal milestone order (EV-UI-001)

| Milestone | Scope | Exit gate |
| --- | --- | --- |
| M0 — Foundation | Next.js app skeleton, typed API client for the five endpoints, env/config, i18n catalog, lint/type gates | Builds clean; API client contract tests |
| M1 — Map view | Cesium scene, AOI rendering, record markers, WebGL fallback (gis-3d owned) | FR-MAP-001–007 pass |
| M2 — Current & forecast | Current weather display, forecast timeline, source filter, time navigation | FR-WX-*, FR-TIME-* pass |
| M3 — Profile & Summit Window | Vertical profile view, Summit Window panel | FR-PRO-*, FR-SW-* pass |
| M4 — Sources & health | Sources/health panel, truthful semantics | FR-SRC-* pass |
| M5 — Error/empty/a11y polish | Error/empty states, accessibility, performance pass | FR-ERR-*, NFR-ACC/PERF pass |
| M6 — Validation, review, QA | Controlled validation run (AC-01), `/review`, QA, teardown | AC-01–AC-14 |

## 13. Launch Plan

The MVP cannot go to production until Gate C-Operational release controls pass.
This delivery therefore defines a staged rollout ending at QA-accepted
validation, not at production GA.

| Phase | Date | Audience | Success gate |
| --- | --- | --- | --- |
| Internal preview (dev build) | after M4 | Everest team + design partners | All P0 user stories demonstrable |
| Validation run | after M6 | QA + Everest Manager | AC-01–AC-14 (five APIs return real canonical data; scoreboard, provenance, ladder, disagreement, animation verified) |
| Review | after validation | Reviewer + Everest Manager | `/review` PASS |
| QA acceptance | after review | qa | `docs/qa/test-plan.md` records tests, failures, teardown |
| Release decision | after QA | Everest Manager | **Blocked** until Gate C-Operational (RELEASE-010); not authorized by this PRD |

**Rollback criteria** — since the MVP is read-only and consumes no external
services, the primary rollback is feature-flagging the UI off or reverting the
frontend build. Rollback is automatic if: any direct external-provider request
is observed, any fabricated geometry/data is rendered, or API contract
mismatches cause incorrect units or fabricated values.

## 14. Risks and Open Questions

### Risks

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R-01 | Four of five APIs lack retained real-data HTTP evidence (ADR-015/016); the UI cannot be validated against real data without a new authorized validation run | High | High | AC-01 explicitly requires a Manager-authorized validation run with a substantive objective; empty/error states are first-class requirements |
| R-02 | Baseline 3D scene without external terrain/imagery may look sparse or fail to meet stakeholder expectations of "3D Everest" | Medium | Medium | Explicit non-goals; MVP shows AOI + canonical markers; terrain belongs to EV-TERRAIN-001 |
| R-03 | Stakeholders expect the route line and camps on the map; approved data has no route/camp geometry | High | Medium | FR-MAP-004 + non-goals make this explicit; route visualization is deferred pending authorized geometry |
| R-04 | Summit Window indicator drifts into Risk-engine/AI scope | Medium | High | FR-SW-003/005: presentation-only, configurable thresholds, no `services/risk/` integration |
| R-05 | WebGL/GPU availability on low-end or older devices | Medium | Medium | FR-MAP-007 fallback; data panels remain usable |
| R-06 | Accessibility on a 3D canvas | Medium | Medium | NFR-ACC-002 non-visual alternative; QA check |
| R-07 | Backend CORS/env misconfiguration in a disposable validation environment | Low | Medium | NFR-SEC-003 records exact origins in architecture handoff |
| R-08 | Release blocked by Gate C-Operational indefinitely | Medium | Medium | Delivery ends at QA-accepted validation; release is a separate decision |
| R-09 | Health semantics misread by users ("verified" as current health) | Medium | Medium | FR-SRC-002/004; ADR-004 semantics rendered explicitly |

### Open questions (must resolve before/at architecture)

| ID | Question | Owner | Needed by |
| --- | --- | --- | --- |
| OQ-01 | What is the baseline scene composition without external providers (bare ellipsoid vs project-owned static assets vs Everest-owned tileset from EV-TERRAIN-001)? | architect + gis-3d | Architecture |
| OQ-02 | What are the default camera position, AOI presentation scope (100 km default vs expanded artifact), and navigation constraints? | gis-3d | Architecture |
| OQ-03 | What are the Summit Window threshold values and their documented basis (config-driven, presentation-only)? | product + meteorology | UI/design |
| OQ-04 | What is the refresh/polling policy for `current` and `forecast` in a read-only MVP (manual refresh vs timed refresh)? | architect + product | Architecture |
| OQ-05 | Is any project-owned imagery/terrain asset approved for local bundling, and what is its license/size impact? | Everest Manager + gis-3d | Architecture |
| OQ-06 | Where does the validation environment run, and what is its approved origin for CORS? | backend + release | Before M6 validation |
| OQ-07 | Is WebSocket live display in scope for a later milestone (not MVP)? | architect | Architecture |

## 15. References

- `AGENTS.md` — governance, delivery stages, ownership, data boundary,
  canonical contract, A-F display acceptance (方案 A / ADR-015).
- `docs/management/decisions.md` — ADR-017 (this line), ADR-014/015/016
  (A-F display and evidence boundary), ADR-004 (lifecycle/health semantics),
  ADR-013 (Gate C split).
- `docs/management/board.md` — EV-UI-001 planned; EV-GATEC-OP-ACL-001 in
  progress; delivery stop and roadmap.
- `docs/everest-aoi.md` — approved AOI center `27.98806, 86.92528`, default
  100 km radius, approved 2,000 km expansion artifact.
- `docs/meteorology/weather-spec.md` — normative canonical weather contract.
- `docs/api/API.md` — the five API contracts and ADR-015 evidence inventory.
- `docs/management/phase-f-report.md` — Phase-F outcomes and evidence status.

---

*End of PRD. CEO review (this stage) has adopted 5 scope expansions; next lifecycle stage: architecture.*
