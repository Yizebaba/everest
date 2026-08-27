# Authorized Scope — OSM / Risk / additional satellite / additional terrain

**Authorizing decision:** Everest Manager, 2026-08-25  
**Status:** Scope definitions for four separately authorized work items. Each
item proceeds only after the Manager confirms its specific scope; no item is
authorized merely by the existence of this document.

These items are each a **new data domain** and follow the same chain as the
weather/ADR-019 sources:
`external source -> connector -> raw data -> parser -> normalizer -> QC ->
canonical model -> PostgreSQL -> service -> REST/WS -> frontend`.
The frontend never calls an external provider.

---

## EV-OSM-001 — OpenStreetMap base layer

- **Data source**: OpenStreetMap (public extract). Options: Geofabrik /
  BBBike / OSM API. Must stay within the approved AOI (`docs/everest-aoi.md`).
- **What it adds**: base-map vector layer for the Cesium scene (roads, terrain
  labels, contours where available) behind the weather data.
- **License**: ODbL — must preserve attribution and share-alike; must be
  reviewed before any commercial reuse.
- **Precondition**: define the exact AOI extract scope and tile/pbf format
  (vector tiles vs raw PBF).
- **Acceptance**: connector + real AOI extract + parser + normalize into a
  vector-layer store (or PostGIS) + service + frontend layer toggle; tests,
  docs, QA. `connected` until real extract QA passes.

## EV-RISK-001 — Risk engine (new module)

- **Status (2026-08-25 authorization)**: `services/risk/` did **not** exist
  at authorization time. HEAD now has `services/risk/engine.py`,
  `services/risk/tests/test_risk.py`, `apps/api/risk_assess.py`, and the
  read-only API adapter under `apps/api/everest_api/risk/`. This is a rule-based
  module, not AI. The 2026-08-25 text is the authorization, not a claim that the
  directory is still absent.
- **What it would do**: a transparent, configurable rule-based assessment that
  combines canonical weather values (wind/temp/precip) at Summit/camp altitudes
  into a Summit Window indicator. **Explicitly not AI**, not a black-box
  prediction, and the Summit Window UI remains presentation-only until this
  module is separately approved and integrated.
- **Precondition**: architecture decomposition (which inputs, which thresholds,
  which output contract) must be reviewed before any code. Requires the AOI
  camp altitudes and a reviewed threshold/weight design.
- **Acceptance**: deterministic rule engine + unit tests (threshold boundaries,
  missing data, no-fabrication) + reviewed integration with the weather API.
  Keep the UI independent of it until integration is separately approved.

## EV-SAT-002 — Additional satellite (Sentinel-1/2, Landsat 8/9)

- **Data sources** (official, free):
  - Sentinel-1/2: Copernicus Data Space Ecosystem / AWS `sentinel-s2-l1c`.
  - Landsat 8/9: USGS EarthExplorer / AWS `usgs-landsat`.
- **License**: Sentinel — free, open (full, free and open license); Landsat —
  free, public domain.
- **Precondition**: register a Copernicus / USGS Earthdata account (user action)
  and confirm the AOI-specific scene/slice retrieval (not full scenes).
- **What it adds**: cloud/glacier/snow imagery context over the Everest scene.
- **Acceptance**: connector + AOI-scoped real retrieval + parser + normalize +
  store + service + frontend overlay; tests, docs, QA.

## EV-TERRAIN-002 — Additional terrain (Cesium 3D Tiles / PostGIS)

- **What it adds**: render the already-retained GLO-30 tile (and future tiles)
  as Cesium 3D Tiles so the Everest scene shows real terrain, plus optional
  PostGIS spatial queries (e.g., profile, distance, route later).
- **Precondition**: decide 3D Tiles generation path (Cesium ion / open-source
  `py3dtiles` / CesiumJS offline) and PostGIS vs pgvector layout. Ports and
  service ownership are backend-owned.
- **Acceptance**: a 3D Tiles tileset from the retained GLO-30 tile served to
  the Cesium scene over the approved API path; PostGIS spatial index and a
  queryable profile endpoint; tests, docs, QA.

---

## Current-state note (2026-08-27)

This document is the 2026-08-25 authorization, not a live inventory. HEAD
already contains:

- EV-OSM-002 South Col route/camp overlay (`GET /api/everest/route`)
- `GET /api/terrain/tile`, `GET /api/observations/current`,
  `GET /api/satellite/segments`
- `services/risk/` rule engine (EV-RISK-001 code present; UI STOP maps to
  engine BLOCK)
- Phase 1 official-client adapters for GFS, IFS, and AIFS; optional GFS/AIFS/
  ICON scheduler jobs remain disabled by default until the ingestion extras are
  installed and each source is operationally enabled
- additive `/api/risk/summit-window` and `/api/weather/wind-field` routes;
  neither changes the historical ADR-015 five-route acceptance surface

Still separately scoped: EV-OSM-001 vector basemap, EV-TERRAIN-002 3D Tiles,
EV-SAT-002 additional satellite, persisted ADR-019 ingestion, and
Gate C-Operational production/shared deployment.

---

## Sequencing recommendation

1. **EV-TERRAIN-002** (3D Tiles from already-retained data) — smallest, uses
   existing data, immediately improves the scene.
2. **EV-OSM-001** (base layer) — AOI extract, then layer under weather.
3. **EV-SAT-002** (satellite overlay) — after a Copernicus/USGS account exists.
4. **EV-RISK-001** (rule engine) — last, after the others stabilize and the
   threshold design is reviewed.

Each item is confirmed individually by the Manager. Work on one does not
authorize another. This document is scope/planning only; it changes no code,
data, or runtime state.
