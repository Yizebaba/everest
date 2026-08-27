# Everest Decisions

## ADR-017: New delivery lines authorized

**Date:** 2026-08-24  
**Status:** Approved by Everest Manager  
**Decision:** The Everest Manager authorizes new product delivery lines beyond
the completed EV-DATA-001 A-F boundary. Each authorized line opens a new
delivery lifecycle per `AGENTS.md` (PRD → `/plan-ceo-review` → architecture →
`/plan-eng-review` → UI → `/plan-design-review` → implementation → `/review` →
QA → release) and must not bypass the external-source isolation rule (frontend
never calls external providers).

Authorized lines (all):

1. **Frontend UI** — deferred EV-DATA-001 frontend display; consumes only
   Everest-owned REST/WS APIs.
2. **Everest AWS observation stations** — approved source per AGENTS.md.
3. **Pyramid meteorological network** — approved source per AGENTS.md.
4. **Satellite data** — Himawari-8/9, Sentinel-1/2, Landsat 8/9 (approved).
5. **Terrain/GIS** — Copernicus DEM GLO-30, Cesium/3D Tiles, PostGIS (approved).
6. **Environmental / OSM / AI / Risk** — individually scoped before any work.

Each line retains the mandatory verification chain
(`official documentation → connector → real data → parser → normalizer → QC →
canonical model → DB/object storage → service → REST/WS → frontend`) and the
`configured` vs `verified` distinction. Data acquisition stays within
`docs/everest-aoi.md` unless an expanded AOI is separately approved.

### ADR-019: Authorize connecting external sources (GLO-30 / Himawari / Everest AWS)

**Date:** 2026-08-24  
**Status:** Approved by Everest Manager  
**Scope:** The Everest Manager authorizes the **Everest backend pipeline** to
connect to three immediately available external sources for direct integration
into the EV-UI-001 surface:

1. **Copernicus DEM GLO-30** (terrain) — AWS Open Data
   `arn:aws:s3:::copernicus-dem-30m` (eu-central-1, anonymous). Verified: HTTP
   200 on the Everest tile (`..._N27_00_E086_00_DEM/..._DEM.tif`, ~43 MB,
   30 m COG). Free license + attribution (DOI 10.5270/ESA-c5d3d65).
2. **Himawari-8/9** (satellite) — NOAA AWS S3 `noaa-himawari8`/`noaa-himawari9`
   (us-east-1, anonymous). Full-disk every 10 min, archive to Jul 2015, free
   distribution with attribution.
3. **Everest AWS observation network** — AppState Everest Weather Portal
   (`scidata.appstate.edu/everest/`) hourly CSV feed (Base Camp / Camp 2 /
   South Col; public, no auth). No license stated — display/research use only;
   commercial use NOT authorized; data is not QC-adjusted (own QC required).

> **ADR-019 amendment (2026-08-24):** the Everest AWS connector retrieves the
> station CSVs from `raw.githubusercontent.com/G-w-e-n-d-o-l-y-n/MetData_/main/`,
> which is the **same public data feed the official AppState Everest Weather
> Portal loads in its own client code** (verified during official-docs
> research). The Everest Manager approves this mirror as the portal's public
> data feed for connector retrieval, on the same terms as the portal (public,
> as-is, display/research use only, commercial use NOT authorized). The portal
> `scidata.appstate.edu/everest/` remains the documented official access point;
> the feed is treated as `configured`, not `verified`, until a provider-backed
> endpoint is confirmed.

**Hard constraint retained:** the **frontend MUST NOT call any external source**
(AGENTS.md isolation rule). These sources are integrated through the canonical
chain only: `external source → connector → raw data → parser → normalizer →
QC → canonical model → PostgreSQL/PostGIS or object storage → service →
REST/WS → frontend`. The UI consumes Everest-owned endpoints
(terrain/satellite/observations), never the providers directly. Network
inspection (AC-02) remains a gate.

**Status semantics:** these sources are being integrated but are NOT yet
`verified`; they remain `connected`/`configured` until real-data retrieval,
parsing, normalization, QC, persistence, API, tests, docs, and review pass.

## ADR-EV-VIS-004: Cesium base-map replacement (World Imagery + World Terrain)

**Date:** 2026-08-26
**Status:** Approved by Everest Manager (project owner granted permission to
proceed)
**Scope:** Replace the Cesium scene base imagery from OSM raster tiles with
**Cesium World Imagery** (ion-hosted Bing global imagery) and use **Cesium
World Terrain** for 3D terrain, when `NEXT_PUBLIC_CESIUM_ION_TOKEN` is set in
`apps/web/.env.local`. OSM remains the automatic fallback when no ion token is
configured.

**Verified official facts (consulted 2026-08-26):**

- CesiumJS itself is open source (Apache 2.0). Cesium ion is a commercial
  hosting platform with a free **Community** plan for personal/non-commercial
  use (5 GB storage, 15 GB/month streaming), paid **Commercial** ($149/month
  individual / $524/month team) and **Premium** ($499/$874/month) plans.
  Official: <https://cesium.com/platform/cesium-ion/pricing/>. The ion ToS
  require a paid plan when the organization exceeds $50K annual revenue, runs a
  government project, funded research, or exceeds free quotas.
- Cesium World Terrain is ion-hosted global quantized-mesh 1.0 terrain (curated
  DEM; Everest region 30–90 m resolution). Free to stream with a free ion
  account within quotas; offline purchase and on-premises are available.
  Official: <https://cesium.com/platform/cesium-ion/content/cesium-world-terrain/>.
- Open-source vs paid-map standards differ in three ways: **format** (OSM uses
  XYZ Web Mercator raster `{z}/{x}/{y}.png`; Cesium uses quantized-mesh terrain
  and ion-hosted raster/3D Tiles), **usage/licence** (OSM is ODbL + OSMF Tile
  Usage Policy: attribution, User-Agent, no bulk scraping, no SLA; Cesium ion is
  ToS-governed, quota-based, paid for commercial use), and **service quality**
  (OSM is best-effort donation-funded; ion has quotas and paid SLAs). Official
  OSM policy: <https://operations.osmfoundation.org/policies/tiles/>.

**Implementation:** `apps/web/src/cesium/EverestScene.tsx` adds
`ImageryLayer.fromWorldImagery()` when the ion token is present; terrain uses
`Terrain.fromWorldTerrain()`. `apps/web/next.config.mjs` CSP adds
`http/https *.virtualearth.net` (Bing tiles are served over http) and `img-src
http:`.

**Verification (2026-08-26):** live headless-Chromium load showed 42
virtualearth imagery tile requests and 44 Cesium World Terrain terrain tile
requests with zero CSP violations. Web typecheck, ESLint, prettier clean;
42 vitest tests pass. This replaces the prior OSM-only base-map rendering and
does not change weather/observation data flow; the frontend still never calls
weather providers directly.

**Licensing note:** World Imagery/World Terrain are ion content. Free Community
use is non-commercial and quota-limited; commercial Everest deployment requires
a paid Cesium ion plan. This decision records source terms, not legal approval
for a specific commercial deployment.

## EV-VIS-006: Restore live data chain and overlay weather on the 3D scene

**Date:** 2026-08-26
**Status:** Completed by Everest Manager authorization (user requested the 3D
scene be made serviceable and show real weather data).
**Scope:** The persistent runtime had been torn down, so the backend API and
database were not serving data. Restored the chain and extended the Cesium scene
with real weather overlays.

**Data chain restore (no re-download):**

- WSL PostgreSQL 15 cluster started on port 5432; role `everest` and database
  `everest_test` created.
- Alembic migrations applied to head (`20260821_0001` … `20260826_0009`),
  creating all 14 application tables.
- The retained immutable IFS artifact (cycle `2026-08-24T00:00:00Z`, lead 0,
  variables `z/10u/10v/2t`, SHA-256 `638a075b…`) recorded in
  `docs/data-sources.md` was parsed with ecCodes and persisted through
  `WeatherIngestionService` by `apps/api/ingest_retained_ifs.py`. No external
  provider call was made. Database holds 2 raw artifacts and 2 canonical
  records (prior ICON + this IFS).
- Backend FastAPI runs on `127.0.0.1:52147` (reachable from Windows;
  `localhost` from Windows times out under the mirrored-network setup).
  `apps/web/.env.local` points at `127.0.0.1:52147`; CSP allows it.
- Verified over HTTP: `/api/weather/current` returns the IFS record
  (28.0, 87.0, 6008 m, -6.0 °C), `/api/weather/forecast` returns ICON, and
  `/api/weather/sources` + `/api/data-health` return lifecycle facts.

**3D weather overlay (real data only, no fabrication):**

- Weather grid points now render a label with temperature, wind speed, and an
  oxygen-fraction estimate, plus a wind-direction vector line built from the
  record's real `wind_direction`. `windVector` in `lib/geo.ts` converts the
  meteorological "wind FROM" direction into the travel vector.
- Oxygen fraction uses the standard barometric scale-height formula
  (`oxygenFractionAtAltitude`), labeled `est.` and never presented as a
  provider-reported value (AGENTS.md: no invented data).
- The OSM South Col route now samples Cesium World Terrain elevation via
  `sampleTerrainMostDetailed` and labels real heights at a bounded stride.
- Verified in headless Chromium: forecast/current/sources/data-health all
  return real records; the scene renders 25k+ marker/label pixels with zero
  console errors; web typecheck/lint/prettier clean, 49 tests pass.

**Scope limits:** only two canonical weather records exist (IFS + ICON). Camp
labels do not claim per-camp forecasts; the weather markers are the actual grid
points. Additional sources (GFS, AIFS, and more leads) require the scheduler or
a separately authorized ingestion run.

**Verified-at-research facts** (from official docs, 2026-08-24) are recorded in
the relevant handoffs; items marked `UNKNOWN/PENDING` in the research
(licenses beyond free distribution, exact quota numbers, Everest-AWS commercial
terms) are not claimed as verified.

## EV-VIS-007: Forecast data-pipeline refresh — stale data and missing fields

**Date:** 2026-08-26
**Status:** Completed by Everest Manager authorization (user explicitly granted
permission to bypass project-documentation limits and fix the data pipeline).
**Root cause:** The database held only two old forecast records (ICON
2026-08-21, IFS 2026-08-24), so the UI reported `stale basis (115 h)`, and the
weather QC incorrectly flagged every provider that does not publish visibility
(e.g. IFS open data) as both `missing_value` and `out_of_range`, which blocked
the Summit Window decision even with fresh wind/temperature.

**Official-source verification (2026-08-25/26):**

- ECMWF IFS Open Data surface products do NOT include a visibility variable
  (verified against the official JSON-Lines index: `z, 10u, 10v, 2t, tp, tprate,
  10fg, tcc, …`). Precipitation (`tp`) and gust (`10fg`) are present.
- NOAA GFS `pgrb2.0p25` DOES include `VIS` (surface, m) and `APCP` (surface,
  kg/m²) on forecast files f003+. Verified against the official NOMADS file
  inventory (`gfs.t00z.pgrb2.0p25.f000.shtml`: "Visibility [m]") and the `.idx`
  contents (`VIS:surface`, `APCP:surface` present on f003+; absent on f000
  analysis, which carries only `PRATE`).
- DWD ICON Open Data has `tot_prec`/`rain_gsp`/`snow_gsp` for precipitation but
  no visibility product (verified against the official directory listing).

**Changes:**

1. `services/weather/gfs/connector.py` + `normalizer.py`: added `VIS` and
   `APCP` to the default messages and `EXPECTED_UNITS` (`vis: m`,
   `apcp: kg m**-2`); `visibility` is now populated for GFS.
2. `apps/api/ingest_refresh.py`: fetches the latest published cycles over
   official HTTP byte ranges (IFS 2026-08-25 06Z leads 0/3/6/12/24/48/72 h;
   GFS 2026-08-25 12Z f003/f006/f024), parses with ecCodes, normalizes, and
   persists through `WeatherIngestionService`. It does not reuse a metadata
   sidecar cache, avoiding the connector's idempotency "checksum sidecar
   inconsistent" trip on a refresh pass. IFS altitude is carried from the
   lead-0 `z` for later leads (same as the accepted scheduler logic).
3. `services/weather/contract.py` QC: a `None` field is `missing_value`, not
   additionally `out_of_range` (the two flags have distinct meanings; flagging
   both falsely degraded any record with an optional field the provider does
   not publish).
4. `apps/web/src/lib/geo.ts` `summitBasisRecord`: prefers the freshest record
   (valid time), then distance, then altitude — a current IFS/GFS forecast
   wins over an older nearer sample.
5. `apps/web/src/components/panels/SummitWindowPanel.tsx` `isClean`: accepts
   `missing_value` so a provider without visibility does not block the
   wind-based decision; other flags remain disqualifying.

**Verification (live):** database rebuilt clean (10 records: IFS 7 + GFS 3, all
real provider data, no NaN altitude). Summit Window shows **GO** with IFS
2026-08-28 06Z (0.0 °C, 0.6 m/s, 7.5 mm precip), `stale basis` gone, agreement
GO 2 / sources 2 / stale 0, GFS visibility 996/13045/50 m over its leads.
`/api/weather/current` returns all 10 records; `/api/weather/forecast` returns
them. Web 51 tests pass; weather suite 109 pass (2 pre-existing environment
failures unrelated to this change). ECMWF IFS has no visibility field in its
public open data — that remains honestly `unavailable` rather than fabricated.

**Rollback:** every change is additive and reversible; no raw artifact was
deleted. The database was recreated (drop/create + migrate + ingest) to clear
pre-fix QC rows; this is reproducible from `ingest_refresh.py`.

## EV-VIS-008: Mount weather data on the 3D scene (camp boards, wind particles, terrain picking)

**Date:** 2026-08-26
**Status:** Completed by Everest Manager authorization (user requested these
three concrete Cesium bindings).
**Scope:** Make the weather data actually visible in the 3D map.

**1. Camp 3D floating boards (Billboard & Label).** The OSM South Col camps
(EBC, Camp 1S, 2S, 3S, 4S South Col) render as floating label entities carrying
the nearest weather record's temperature / wind / visibility. Camp and route
geometry come from the approved OSM Overpass source and were re-seeded after
the EV-VIS-007 database rebuild (`apps/api/ingest_osm_route.py`; 5 camps + 359
route vertices). No camp coordinates are invented; elevations are taken from the
OSM snapshot or Cesium terrain.

**2. Wind particle field (ParticleSystem).** One Cesium `ParticleSystem` is
created per weather grid point that has a real `wind_direction`/`wind_speed`.
Particles stream along the meteorological travel vector (derived from the
"wind FROM" direction) above the terrain, coloured by source (IFS cyan, GFS
purple, etc.). Emission rate and particle life are bounded for visual clarity;
wind speed sets the visual baseline (min 2 m/s).

**3. Terrain picking (MOUSE_MOVE).** A `ScreenSpaceEventHandler` on
`MOUSE_MOVE` uses `viewer.scene.sampleHeight` at the cursor plus four neighboring
probes (~50 m) to compute and display live altitude and slope in a bottom-left
scene readout (e.g. `alt 4975 m · slope 18.1°`).

**StrictMode/unmount hardening.** React 18 StrictMode double-invokes effects;
the original cleanup callbacks called `viewer.isDestroyed()`, which itself
throws on a torn-down Viewer (`Cannot read properties of undefined (reading
'scene'/'entities')`). All cleanups and async callbacks now guard with
`viewerRef.current === viewer` (a plain ref comparison) instead of touching
Viewer internals after teardown.

**Verification (live headless Chromium):** zero console/page errors; terrain
pick returns real elevation and slope; pixel analysis confirms IFS markers +
particles (2.5k+ cyan px) and camp/route amber labels render; web
typecheck/lint clean, 51 tests pass.

## EV-VIS-009: Cesium scene performance — requestRenderMode (4 → 60 FPS)

**Date:** 2026-08-26
**Status:** Completed by Everest Manager authorization (user reported the map
was "非常卡").
**Root cause:** the scene rendered at ~4 FPS with the CPU idle. Diagnostics in
headless Chromium: `TaskDuration` ~3 ms (CPU fine), but canvas
`visibility:hidden` jumped FPS to 60 (rAF idle) while restoring the canvas
collapsed it back to 0–4 FPS. This proves Cesium's default `Viewer` re-draws
the full viewport every animation frame regardless of scene change, and the
1024×900 terrain+imagery repaint saturated the rasterizer. In a software
renderer this floor is ~4 FPS; on a real GPU it is smoother but still wasteful
and the user experienced visible stutter.

**Fix (`apps/web/src/cesium/EverestScene.tsx`):**

- `requestRenderMode: true` + `maximumRenderTimeChange: 0.5` on the `Viewer`
  options, so Cesium renders only when something changes (camera move, tiles
  streaming, entity edits, or a render request), instead of repainting every
  frame.
- Reduced wind-particle load: particle life 1.2 s (was 3.0), emissionRate 3
  (was 12), burst 4–6 (was 20–30), imageSize 4 px (was 6), emitter radius 40
  (was 60), alpha 0.7 start.
- Throttled terrain picking to 100 ms between `sampleHeight` batches and cut
  the slope probes from 4 to 2 orthogonal neighbors (~50 m), keeping the
  per-hover raycast count low.

**Verification:** FPS 4 → **60** idle in the same headless environment, zero
console/page errors, terrain picking still returns real elevation/slope, wind
particles still render during camera motion. Web typecheck/lint clean, 51 tests
pass.

## EV-VIS-006-INCIDENT-002: User cannot see 3D terrain in their browser

**Repeated-failure event count:** 3 (three identical user reports: "不是3d",
"还是没有3d", "我在地图上都看不到，立体的").

**Affected component:** Cesium 3D scene rendering in the user's browser.

**Server-side evidence collected (2026-08-26):**

- WSL PostgreSQL 15 online (port 5432); alembic head (`0009`); 14 tables;
  `everest_test` reachable from Windows via `127.0.0.1:5432`.
- Backend FastAPI on `127.0.0.1:52147` returns HTTP 200 for
  `/api/weather/current` (2 records), `/api/weather/forecast` (2 records),
  `/api/weather/sources`, `/api/data-health`.
- Frontend `http://localhost:52148/` returns HTTP 200; `.env.local` points at
  `127.0.0.1:52147`; CSP allows it; dev server serves the current bundle
  (contains `enableLighting`, `requestVertexNormals`, `fromWorldImagery`).
- Headless Chromium (Playwright) loaded the page: canvas present
  (1024x900), WebGL available, 7 panels rendered, **zero console errors**,
  terrain `getHeight` returns summit 8773 m / EBC 5234 m, World Terrain tiles
  load at zoom 10–13 with `octvertexnormals`, lighting on/off brightness delta
  124, 25k+ weather-marker pixels rendered.
- Web typecheck/lint/prettier clean; 49 vitest tests pass.

**Root-cause analysis:**

The application, API, database, and headless-rendering paths are all verified
working. The user still reports a flat, non-3D map with none of the overlays
visible. Because the same server-side build renders 3D correctly in an isolated
browser, the failure signature points to the **user's browser session**, not the
application code. Two leading hypotheses (both browser-side):

1. **Stale bundle / cache:** the browser is still executing a pre-change chunk
   (the original 45 km nadir view without lighting or overlays) and hard refresh
   was not performed or was blocked by a proxy/service worker.
2. **Different origin:** the user is viewing a different port or a proxied copy
   of the page (the dev log shows `layui` CSS requests, which this app never
   emits, implying another local page/proxy is involved).

**Status:** PAUSED pending Everest Manager / user input. The next attempt will
NOT modify server code until the user reports:
- the exact URL they open (port and host),
- the browser and version,
- whether a hard refresh (Ctrl+Shift+R / Cmd+Shift+R) or an incognito window was
  tried,
- a screenshot or description of what the map area actually shows (blank / dark
  / flat imagery / error text).

**Correct next-run procedure (after user input):**

1. Confirm the exact URL matches `http://localhost:52148/` (or the network IP
   the dev server prints).
2. Perform a hard refresh or open an incognito window; verify via the page
   "Summit Window" panel that live data (e.g. "-6.0 °C" IFS) is present.
3. If the scene area is blank/dark, check the browser console (F12) for
   WebGL/Cesium errors and capture them.
4. Only after this evidence is captured should server-side code be changed.

**Rollback:** no destructive change was made; all changes are additive
(lighting clock pin, overlays, ingest script). Reverting to OSM-only requires
removing the ion token from `.env.local`.

**Date:** 2026-08-26

**Date:** 2026-08-24  
**Status:** Approved by Everest Manager via `/plan-ceo-review` (SCOPE EXPANSION)
**Document:** `docs/product/PRD.md` (v0.2)

The EV-UI-001 MVP adopts five scope expansions (all presentation-layer over the
existing five APIs; no Risk/AI, no invented geometry, no external calls):

1. Summit Window scoreboard (green/amber/red + per-source agreement + staleness) — FR-SW-006..009, AC-11.
2. Forecast time animation across valid-time extent — FR-TIME-004/005, AC-14.
3. Click-to-provenance panel (canonical record identity + source health) — FR-PRV-001/002, AC-12.
4. Camp altitude ladder (EBC→C1→C2→C3→C4→SUMMIT, six profile calls) — FR-LAD-001/002, AC-13.
5. Model disagreement (min/max/median across IFS/AIFS/GFS/ICON) — FR-DIS-001/002, AC-13.

Two adversarial review rounds: 16 issues found and fixed (round 1), all verified
resolved with 5 minor polish items then fixed (round 2); quality 7/10 → 8/10.
Acceptance is gated by AC-01–AC-14 at M6/validation. Next lifecycle stage:
architecture.

## ADR-001: Phase A Registry Authority

**Status:** Accepted

The PostgreSQL-backed `data_source_registry` is the operational source of
truth for source metadata, scheduling configuration, lifecycle status, and
health timestamps. Version-controlled configuration may seed or reconcile the
registry, but cannot be a competing runtime authority.

This decision prevents configuration drift while allowing an auditable,
queryable operational registry.

## ADR-002: Phase A Scheduler Boundary

**Status:** Accepted

Phase A defines a scheduler configuration and adapter boundary only. It does
not start a scheduler, execute jobs, or call external sources. Connector job
execution will be designed after Phase A and must have exactly one scheduler
owner, rather than running independently in every API worker.

## ADR-003: Phase A API Boundary

**Status:** Accepted

Phase A documents contracts for `GET /api/data-sources` and
`GET /api/data-health`, but does not implement them. These endpoints require
real operational evidence before they can report health accurately. No frontend
work is authorized in Phase A.

## ADR-004: Lifecycle and Health Semantics

**Status:** Accepted

Source lifecycle status is limited to `planned`, `configured`, `connected`,
`verified`, `degraded`, and `disabled`. Operational health is separate and may
use `unknown`, `healthy`, `stale`, `failed`, `degraded`, or `disabled`.
Creating a registry row never establishes `connected` or `verified` status.

## ADR-005: Database Migration Standard

**Status:** Accepted

Backend schema migrations use Alembic and require reviewed upgrade and
downgrade paths in a disposable PostgreSQL test database. Autogenerated
migrations are candidates only and require manual review.

## ADR-006: Phase A Acceptance Condition

**Status:** Accepted

Phase A is conditionally accepted after static migration rendering, unit tests,
formatting, compilation, and lint checks passed. It is not fully accepted and
does not authorize Phase B until the PostgreSQL-only migration/persistence test
suite executes, rather than skips, against an isolated disposable database.

SQLite is not an allowed substitute because PostgreSQL constraints, migration
behavior, and transaction semantics are acceptance requirements.

## ADR-007: Updated AGENTS.md Compliance Gates

**Status:** Accepted

The latest `AGENTS.md` is the sole governing specification. Existing historical
connector and disposable-database evidence does not override its current AOI,
raw-storage, ownership, verification, or phase-order requirements.

ICON database/API execution and Phase E acceptance were previously blocked by
the single-Gate-C interpretation. ADR-013 now places the accepted disposable
ICON DB/API result and Phase E acceptance under Gate C-Core; Gate C-Operational
remains the production/shared-deployment blocker. AOI Gate A is complete under
ADR-012.

## ADR-008: Canonical Weather Contract Path

**Status:** Accepted

`docs/meteorology/weather-spec.md` remains the single normative meteorology
weather contract. `docs/weather-spec.md` is a non-duplicating compatibility
entry point and must not contain a second editable schema.

Meteorology owns weather-field semantic changes. Downstream agents must use the
normative document rather than infer a contract from the compatibility pointer.

**Gate-B clarification:** Gate B is closed only when QA records provider-path
evidence that parsing, normalization, and QC exercise the semantics in
`docs/meteorology/weather-spec.md`: UTC valid time; native provider spatial
key; altitude in metres; temperature in Celsius; wind speed in m/s and
true-north direction in degrees; precipitation in millimetres; visibility in
metres; nullable missing values; required source/model and forecast identity;
and additive, non-destructive quality flags. QA must also prove that unknown
units are not guessed and that no provider-local or compatibility schema
substitutes for the normative document.

ADR-009 dependency isolation is a separate structural gate. Passing import,
shared-DTO, or injected-port tests does not close Gate B; conversely, semantic
contract evidence does not close ADR-009. Downstream work must read
`docs/meteorology/weather-spec.md` as the sole semantic authority;
`docs/weather-spec.md` may be used only as its non-editable compatibility entry
point.

## ADR-009: Owner-Neutral Ingestion Contract

**Status:** Accepted

Provider adapters under `services/weather/` must not import `apps/api` or
`everest_api`. Ingestion DTOs and the protocol move to an owner-neutral shared
package. Backend implements the port; meteorology implements provider adapters.
The shared contract must not import FastAPI, SQLAlchemy, HTTP, ecCodes, or
provider-specific types.

ICON persistence/API execution was previously blocked until QA verified this
direction. The final Phase E QA and DBRE records now document that acceptance;
Gate C-Operational remains a production/shared-deployment blocker.

## ADR-010: External Raw Storage Policy

**Status:** Accepted policy; partial runtime implementation; QA acceptance pending

The Everest Manager approved `D:\Everest-data\raw` as the external operational
raw-storage root. The directory was created on 2026-08-21. It is outside
repository content. Runtime configuration must still provide and validate this
root; future enforcement must fail closed when it is absent, invalid, or inside
the repository.

All raw provider payloads, including GRIB/GRIB2 and compressed provider
objects, must remain outside Git. Raw metadata and checksum sidecars are raw
retention facts and must remain outside Git with their payloads. Repository
exclusion rules and the configuration/schema needed to enforce this boundary
are implementation work to be completed later.

Existing project-root `tmp-icon*` and `tmp-gfs*` artifacts remain unmoved.
They are noncompliant and are not durable operational storage or evidence of
use of the approved root. Their retention, access, and disposition remain open
and no raw files are moved, copied, deleted, hashed, or otherwise operated on
by this decision.

The future external-root implementation must define and record, for every
retained raw artifact:

- retention owner, retention period/class, and disposition or legal-hold
  rules;
- access owner, permitted identities/roles, least-privilege mode, and audit
  expectations;
- immutable payload identity, provider/source identity, dataset/model,
  cycle/lead/valid time, retrieval time, format, size, and approved AOI
  identifier/version;
- canonical metadata retained beside the payload; and
- payload and metadata-sidecar SHA-256 values, with deterministic verification
  on write and reuse, and rejection/flagging of missing or changed facts.

Gate C-Operational remains open. Gate C-Core's required real connector run using
`D:\Everest-data\raw`, an executed PostgreSQL persistence/retention result,
and independent QA evidence are recorded in the final Phase E DBRE/QA handoff.
Operational IAM, legal/WORM, Git, and production-grade retention controls are
not closed by that evidence. Any acquisition must use only the approved AOI;
an expansion requires a separate documented manager approval.

This policy does not itself verify a provider. The final Phase E QA and DBRE
records provide historical disposable ICON `verified`/`healthy` and DB/API
acceptance under Gate C-Core. Current health and API availability are unknown
after teardown. Gate C-Operational remains open for production/shared
deployment, automatic disposition, and production-grade retention claims.
ADR-011 is superseded by the final ICON lifecycle reconciliation below.

## EV-DATA-001-REM-03-RETENTION: Raw Retention Controls

**Assignment:** EV-DATA-001-REM-03-RETENTION  
**Status:** Policy approved; partial runtime implementation; QA acceptance pending  
**Scope:** `D:\Everest-data\raw` and raw artifacts produced by approved
forecast connectors

This record defines the controls that must govern the approved external raw root.
It does not prove that any control is deployed, configured, or operating. No
raw file was moved, copied, hashed, deleted, or otherwise operated on by this
assignment.

The Everest Manager approved the recommended defaults on 2026-08-21:

- `operational_raw`: 24 months from acquisition.
- `failed_or_rejected_raw`: 180 days from acquisition.
- `raw_audit`: 36 months from event time.
- `legal_hold`: until authorized release, then the remaining applicable period
  or 12 months after release, whichever is longer.
- Disposition requires explicit approval after retention expiry and hold checks;
  unattended automatic deletion is prohibited.
- Retention owner, raw custodian, hold authority, audit approver, and historical
  `tmp-*` disposition owner: Everest Manager.
- Frontend users, public API consumers, and unauthenticated identities have no
  raw-root or raw-metadata access.

### Required controls

- **Retention:** Every retained payload and metadata sidecar must have a
  recorded retention owner, retention class, retention period, acquisition
  timestamp, and disposition due date. No unclassified artifact may be
  accepted as durable operational raw data. A retention period is not inferred
  from provider update frequency or from the existence of the root.
- **Access:** Access to the root must be limited to named service identities
  and approved operator roles. Connector writes must use the least-privilege
  service identity; routine consumers must be read-only; frontend access and
  direct external-source access are prohibited. Access grants, changes, and
  revocations must identify the approver and effective time.
- **Disposition:** Expiry must trigger a controlled disposition workflow, not
  automatic deletion by an unreviewed job. The workflow must check legal hold,
  record the authorizing owner, disposition method, UTC completion time, and
  resulting audit evidence. Until that workflow is runtime-enforced, expired
  artifacts remain an open control and must not be represented as disposed.
- **Legal hold:** A hold record must identify the artifact or selection rule,
  hold owner, reason/reference, start time, affected retention class, and
  release authority. Held artifacts must be excluded from disposition until an
  auditable release is recorded. Missing or ambiguous hold state must fail
  closed for disposition.
- **Audit:** The system must retain append-only audit events for artifact
  acceptance, read, reuse, integrity failure, access change, hold placement or
  release, disposition approval, and disposition completion. Events must record
  artifact identity, actor/service identity, action, result, UTC time, and
  correlation or run ID. Audit retention and access must be governed separately
  from payload retention.
- **Artifact identity and evidence:** The artifact record must retain source,
  dataset/model, cycle, lead and valid time, retrieval time, format, byte size,
  `aoi_id`, `aoi_version`, payload SHA-256, metadata-sidecar SHA-256, and the
  canonical metadata beside the payload. Write and reuse must verify these
  facts; missing, changed, or inconsistent facts must be rejected or flagged
  without deleting the raw payload.
- **Root boundary:** Runtime configuration must validate that the root is an
  existing absolute directory outside the repository and that every resolved
  object reference remains beneath it. This is distinct from retention,
  access, legal-hold, disposition, and audit enforcement.

### QA acceptance checklist

QA may close this assignment only with executable evidence against
`D:\Everest-data\raw` or an explicitly approved equivalent test root that
preserves the same boundary semantics. Documentation, configuration presence,
unit-only mocks, or historical disposable runs are insufficient.

- [ ] Runtime fails closed when `EVEREST_RAW_ROOT` is absent, relative,
  nonexistent, inside the repository, or otherwise invalid.
- [ ] Runtime rejects empty, traversal, absolute-escape, and symlink/junction
  escape object references before raw persistence.
- [ ] A real connector run writes payload, canonical metadata, and checksum
  sidecar beneath the approved root and retains the required provenance,
  AOI, cycle/lead/valid-time, size, and retrieval facts.
- [ ] Payload and metadata are reverified on write and reuse; changed or
  missing sidecars are rejected or flagged without raw deletion.
- [ ] Retention owner, class, period, due date, and disposition state are
  persisted and queryable for every accepted artifact.
- [ ] Access tests prove least privilege for connector write, operator read,
  unauthorized read/write, grant, change, and revocation paths.
- [ ] Legal-hold placement, hold protection during disposition, authorized
  release, and ambiguous/missing hold fail-closed behavior are evidenced.
- [ ] Disposition requires approval, performs a hold check, records completion
  evidence, and cannot run as an unreviewed automatic deletion.
- [ ] Append-only audit events are produced and queryable for all listed
  retention, access, integrity, hold, and disposition actions.
- [ ] Evidence includes real UTC timestamps, artifact identifiers, test output,
  failed-path results, and teardown/cleanup results without deleting retained
  operational raw data.
 - [x] QA records the final ICON DB/API acceptance under Gate C-Core; this
   checklist remains the Gate C-Operational hardening record.

### Exact open controls

The following controls remain open and are not claimed as implemented by this
record:

1. Backend migration `0004` and the internal ingestion service implement
   retention classification, due-date persistence, controlled internal
   transitions, and append-only acceptance/reuse audit primitives. No executed
   PostgreSQL evidence proves these controls for an approved-root ICON artifact.
2. Runtime retention scheduling and operational enforcement have not been
   proven.
3. Root access identities, roles, filesystem/object-store permissions, and
   least-privilege enforcement have not been implemented or tested.
4. Legal-hold schema, authority, release process, and fail-closed enforcement
   have not been implemented or QA-verified.
5. Disposition authorization, hold checking, execution, and evidence capture
   have not been implemented or QA-verified.
6. Append-only audit storage is implemented in migration `0004` for
   acceptance, reuse, and internal transitions; executed PostgreSQL evidence,
   full event coverage, audit access controls, and QA verification remain open.
7. End-to-end runtime evidence that a real connector retains all required
   payload/metadata artifacts under `D:\Everest-data\raw` is not accepted for
   this assignment.
8. Repository exclusion/tracking enforcement remains open; existing
   project-root `tmp-icon*` and `tmp-gfs*` artifacts remain noncompliant and
   their disposition is open.
9. AOI-controlled acquisition/reuse remains subject to the approved AOI
   version and geometry constraints; this record authorizes no acquisition.
10. Gate C-Operational controls remain open for production/shared deployment,
    automatic disposition, and production-grade retention claims. The ICON
    DB/API result is accepted historically under Gate C-Core.

## EV-DATA-001-REM-03-GOVERNANCE: Gate C Operational Blockers

**Assignment:** `EV-DATA-001-REM-03-GOVERNANCE`  
**Review date:** 2026-08-21  
**Status:** Gate C-Core passed; Gate C-Operational remains blocked

The latest Gate C QA decision in `docs/qa/test-plan.md` accepts the supplied
disposable PostgreSQL run as backend/database evidence only. The run covered
migrations `20260821_0001` through `20260821_0006`, completed with `44 passed,
no skips` on documented port `64035`, and was followed by test database and
listener cleanup. This acceptance preserves PostgreSQL as the required
database acceptance path; it does not establish operational access control,
legal authority, storage immutability, or Git tracking evidence.

The following exact blockers remain open:

1. **ACL/IAM:** Named connector-write and operator-read identities, least
   privilege, unauthorized read/write denial, grant/change/revocation controls,
   and corresponding approval/audit identity evidence have not been proven by
   OS ACL or object-store IAM evidence. Path validation and a caller-provided
   actor/role do not substitute for deployment-enforced authorization.
2. **Legal/WORM:** Legal-hold authority and fail-closed hold lifecycle are not
   operationally evidenced. Controlled disposition authority is not proven, and
   filesystem/object-store WORM or an approved equivalent against privileged
   modification is not proven. A best-effort read-only bit is insufficient.
3. **Git evidence:** This workspace has no `.git` metadata, so raw
   payload/metadata/sidecar exclusion and non-tracking cannot be verified here.
   Verification must occur in the authoritative Git-bearing checkout without
   operating on the legacy `tmp-icon*`/`tmp-gfs*` artifacts; their disposition
   remains open.

These blockers keep Gate C-Operational open under ADR-010 and the approved
`EV-DATA-001-REM-03-RETENTION` policy. No policy relaxation, raw-artifact
operation, code change, or production status claim is made by this record.
ICON's historical disposable `verified`/`healthy` DB/API acceptance is recorded
by the final Phase E QA and DBRE evidence; current health and API availability
are unknown after teardown.

## ADR-011: ICON Interim Status

**Status:** Accepted; reconciled by final Phase E QA

ICON has historical disposable `verified`/`healthy` and accepted PostgreSQL/API
evidence after the final canonical commit. The disposable database, listener,
and test resources were removed, so current ICON health and API availability
are `unknown`. Gate C-Operational remains open and is a production/shared
deployment blocker only.

## ADR-012: AOI Manager Approval Gate

**Assignment:** EV-DATA-001-REM-01-APPROVAL  
**Status:** Accepted; Gate A complete

Manager checklist:

- [x] Confirm the authoritative AOI identifier and version.
- [x] Approve WGS-84 / EPSG:4326 and GeoJSON axis order.
- [x] Approve the generated 2,000 km geodesic geometry and bounding box.
- [x] Approve the explicit expansion from the default 100 km scope.
- [x] Approve inclusion, exclusion, validation, and change-control records.
- [x] Record the manager decision, approver reference, effective date, and
  resulting AOI version in `docs/everest-aoi.md`.

`docs/everest-aoi.md` is the approved AOI authority. The approved operational
center is WGS-84 `27.98806, 86.92528`; the approved expanded acquisition scope
is `docs/everest-south-route-v1.0-expanded-2000km.geojson`, the generated,
validated 2,000,000 m geodesic boundary recorded there. Its identity is
`everest-south-route-v1.0`, `Polygon`, SHA-256
`b21ce4c8fe8d0fae15e0723e54fa3224f06e253b2662cdaee58e8efe1bb290ac`.

## EV-DATA-001-FULL-AUDIT: From-Scratch Audit

**Review date:** 2026-08-21
**Status:** Audit recorded; Phase E accepted at Gate C-Core

The latest `AGENTS.md` was reread before this audit. The following facts were
verified from the workspace and handoff documents:

- Phases A and B, ECMWF IFS, and NOAA GFS have historical acceptance records;
  their disposable runtime health is not current health after teardown.
- ICON has final approved-root retrieval, parsing, normalization, QC, raw
  retention, PostgreSQL persistence, bounded API, and Phase E QA evidence.
  Historical disposable lifecycle state is `verified`/`healthy`; current
  health/API availability are `unknown` after teardown.
- The approved AOI is WGS-84 `27.98806, 86.92528` with an explicitly approved
  2,000 km geodesic expansion and recorded GeoJSON artifact.
- The approved raw root is `D:\Everest-data\raw`; the root boundary and
  retention/audit database controls are implemented/tested in part, but ACL/IAM,
  legal/WORM, and Git-bearing exclusion evidence remain unresolved.
- The workspace is not a Git checkout. Raw-looking `tmp-icon*` and `tmp-gfs*`
  artifacts remain in the project tree, are noncompliant durable storage, and
  were not operated on during this audit.
- The normative weather contract is `docs/meteorology/weather-spec.md`;
  `docs/weather-spec.md` is only a compatibility entry point.
- The owner-neutral ingestion package and provider dependency-direction tests
  exist. Provider-path semantic QA for ICON is recorded as closed, but it does
  not close raw retention or ICON DB/API acceptance.

### Repeated Failure Escalation Audit

The three-occurrence escalation rule was added to `AGENTS.md` during this
audit. The available handoffs show several different failure signatures,
including provider HTTP 404/500 responses, PostgreSQL trigger defects, JSON
comparison failure, and test-harness assertion placement. The current record
does **not** establish that one identical root-cause signature has occurred
three times. Therefore no fourth-attempt escalation is claimed retroactively.

For every future failure, the owner must count occurrences across retries,
agents, and sessions; at the third identical root-cause occurrence, pause and
record official documentation URLs, complete logs, root cause, next-run
procedure, prerequisites, expected evidence, and cleanup/rollback before any
fourth attempt.

### Current Audit Blockers

1. Gate C-Operational hardening remains open for production/shared deployment,
   automatic disposition, and production-grade retention claims. It does not
   invalidate the accepted historical ICON DB/API result or Phase E QA.
2. Windows ACL/IAM least-privilege and identity evidence is not established.
3. Legal-hold authority, WORM/object-lock or equivalent privileged-modification
   protection, and controlled disposition evidence are not established.
4. Git tracking/exclusion evidence cannot be produced in this non-Git workspace.
5. Existing project-root raw artifact disposition is unresolved.
6. AIFS remains blocked until the Phase E code review and handoff
   reconciliation are documented by the manager and owning domains.

No external acquisition, raw-file operation, or business-code change was made
by this audit. The final Phase E DBRE/API execution and QA acceptance are
recorded in the QA and data-source handoffs; this audit does not authorize
production deployment or Gate C-Operational claims.

## ADR-013: Split Raw Acceptance and Operational Hardening

**Status:** Accepted

Gate C is split into two independently tracked gates:

- **Gate C-Core** is the mandatory Phase E source-acceptance gate. It requires
  the approved external root, approved AOI, immutable payload and metadata
  retention, checksum verification, deterministic reuse/deduplication, real
  parsing/normalization/QC, PostgreSQL persistence, queryable API evidence,
  tests, documentation, review, and truthful lifecycle/health reporting.
- **Gate C-Operational** covers deployment hardening: named OS/object-store
  identities, least-privilege ACL/IAM, legal-hold and disposition authority,
  complete operational audit, privileged-modification resistance/WORM where
  selected, and authoritative Git repository exclusion/history evidence.

Gate C-Operational remains required before shared or production deployment,
automatic disposition, or any claim of production-grade retention governance.
It does not block a controlled disposable Phase E verification run when Gate
C-Core and all other Phase E gates pass.

The approved retention periods, owner assignments, hold rules, no-automatic-
deletion rule, and public/frontend raw-access prohibition remain in force. This
decision changes gate placement, not the approved policy. No IAM, WORM, legal,
or Git claim may be made without separate evidence.

## EV-DATA-001-E-REVIEW-CLOSURE-EVIDENCE

**Status:** Recorded for final review

The authoritative post-review DBRE run is a test count, not a directory name:

- Full `apps/api` suite: `58 passed, 0 failed, 0 skipped`.
- Focused ICON integration: `2 passed, 0 failed, 0 skipped`.
- PostgreSQL: pinned `postgres:17-alpine` digest, disposable localhost port
  `46583`, migrations `20260821_0001` through `20260821_0006`.
- Real retained ICON path: six GRIB2 messages parsed with WSL ecCodes `2.47.1`;
  native point index `818403`; exact provider spatial key retained.
- Backend descriptor file size/hash and projected payload size/hash consistency
  checks passed.
- PostgreSQL persisted one raw artifact, one canonical record, and one audit
  event; lifecycle changed only after canonical commit.
- Forecast API returned HTTP 200 with one ICON record and no raw path, URL,
  hash, retention, or audit leakage.
- Synthetic ICON raw-first failure and GFS/IFS persistence regressions passed.
- Container, volume, listener, and temporary Python environment were removed;
  current runtime health and API availability remain `unknown`.

### Review Finding Disposition

| Finding | Disposition | Evidence |
| --- | --- | --- |
| E-001 connector/adapter metadata mismatch | Closed | Authoritative retrieval conversion verifies payload, metadata, sidecar, AOI, and scalar projection; full retained pipeline passed. |
| E-002 Windows-unsafe parser temporary file | Closed | Writer closes before ecCodes reopen; cleanup is guaranteed; parser tests pass. |
| E-003 incomplete connector-to-database proof | Closed | Offline retained artifact executes parser, normalizer, adapter, PostgreSQL, and API in one test. |
| E-004 noncanonical valid-time metadata | Closed | Current metadata uses UTC ISO-8601; historical numeric value is compatibility-only. |
| E-005 metadata digest not bound to retrieval | Closed | Conversion verifies metadata and sidecar hashes and returns them with the verified retrieval handoff. |
| E-006 backend path-only raw verification | Closed | Backend verifies regular-file existence, path containment, byte size, SHA-256, and projected descriptor consistency before persistence. |
| E-007 GUC/database authorization | Gate C-Operational | Does not block controlled Phase F under ADR-013; no production authorization claim. |
| E-008 retention vocabulary mismatch | Closed | Cross-layer vocabulary table defines raw, adapter, and backend fields; persisted hold state uses `none`. |
| E-009 longitude/requested-coordinate validation | Closed | Native and requested coordinates require finite values and canonical ranges; tests pass. |
| E-010 contradictory handoffs | Closed by authoritative current-status records | Historical sections remain evidence only; current status is Phase E Gate C-Core accepted, current health unknown, Gate C-Operational open. |

No identical root-cause reached the three-occurrence escalation threshold. The
spatial-key omission remains at two historical occurrences and did not recur.

## EV-DATA-001-F-INCIDENT-001: Repeated WSL Wrapper Failure

**Parent task:** `EV-DATA-001-F-AIFS-DBRE`  
**Reconciliation assignment:** `EV-DATA-001-F-INCIDENT-RECONCILE`  
**Affected component:** PowerShell -> `wsl.exe` -> nested Bash invocation  
**Occurrence count:** 3  
**Status:** Corrective procedure accepted by Everest Manager with a residual
historical evidence limitation  
**Per-occurrence timestamps:** unavailable and cannot be recovered from the
retained evidence  
**Fourth attempt:** no fourth attempt of the prohibited nested-wrapper pattern
was made

The three events share one root-cause signature: a structured argument vector
was encoded as an inline nested shell string. PowerShell parsed and serialized
native-command arguments, `wsl.exe` forwarded them, and Bash parsed the command
string again. The intended argument boundaries were altered or reinterpreted.

This was an invocation-wrapper defect, not an ECMWF AIFS, GRIB, PostgreSQL,
FastAPI, raw-data, or product-test defect. Complete per-occurrence stdout,
stderr, exit codes, PowerShell version, serialized command line, Linux argv,
and exact timestamps are unavailable and cannot be recovered. The missing
per-occurrence logs and timestamps remain a compliance evidence limitation.
The DBRE report and this decision are the available incident evidence; they do
not establish full compliance with every repeated-failure escalation evidence
requirement in `AGENTS.md`.

Official documentation consulted:

- Microsoft WSL basic commands:
  <https://learn.microsoft.com/en-us/windows/wsl/basic-commands>
- Microsoft PowerShell `about_Parsing`:
  <https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.6>

### Accepted next-run procedure

1. Do not use PowerShell -> `wsl.exe` -> inline `bash -c`/`bash -lc` strings.
2. Invoke the Linux executable directly with each argument passed separately,
   for example `wsl.exe -d kali-linux -- python3 -m <module> <arg...>`.
3. If shell syntax is required, use a reviewed script file and pass its path
   and parameters as separate arguments.
4. Record PowerShell version, `$PSNativeCommandArgumentPassing`, WSL version and
   distribution, UTC start time, correlation ID, and a redacted argument
   manifest before execution.
5. Capture stdout, stderr, native/child exit codes, UTC end time, expected
   evidence, and cleanup result.
6. Treat missing or ambiguous evidence as failure, not partial success.

The prohibited fourth-attempt pattern is any variation of one quoted nested
Bash command string, including changes that only add quotes, backslashes,
backticks, or `--%`.

Cleanup is limited to run-owned wrapper files and disposable test resources.
Do not modify/delete retained raw artifacts, reset WSL, or alter product
code/schema/provider configuration as wrapper cleanup.

The Everest Manager accepts the corrective procedure and accepts the
unrecoverable evidence gap as a historical limitation, without claiming full
escalation compliance. Future runs may use only the accepted direct-argument or
reviewed-script form; the failed nested-wrapper pattern is prohibited.

The successful AIFS DBRE was a distinct corrected execution using the accepted
direct-argv/reviewed procedure, not a fourth attempt of the prohibited nested
wrapper. The earlier **61/61**, focused **AIFS 3/3**, and disposable port
**`44859`** evidence is superseded. The authoritative hardened evidence is
`apps/api` **66 passed, 0 failed, 0 skipped**, focused AIFS **4 passed, 0
failed, 0 skipped**, meteorology AIFS **37 passed, 0 failed, 0 skipped**, and
disposable port **`46901`**. Docker lifecycle evidence is accepted as **RC2**
and fixture evidence as **RC1**. The committed path recorded exactly `raw=1`,
`record=1`, and `audit=1`, with historical disposable `verified`/`healthy`
only after commit. These corrected-run facts do not recover the missing
evidence for the three invocation failures, erase the incident history, or
convert the wrapper incident itself into a successful result. The historical
evidence limitation and accepted direct-argv procedure remain in force.
The default 100 km scope remains documented but is not the active expanded
scope.

This completes AOI Gate A and authorizes only AOI-constrained acquisition where
the remaining controls permit it. Final Phase E QA and DBRE evidence close
Gate C-Core and ICON lifecycle reconciliation for historical disposable
acceptance. Gate C-Operational remains open; it does not authorize production
deployment or production-grade retention claims.

## EV-DATA-001-E-RETENTION-AUDIT: Accepted Raw-Artifact Metadata Audit

**Assignment:** `EV-DATA-001-E-RETENTION-AUDIT`  
**Status:** Documentation/code audit complete; no raw-artifact operation

This audit read the latest `AGENTS.md`, the approved raw-retention policy in
ADR-010 and `EV-DATA-001-REM-03-RETENTION`, the AOI authority, the ICON
connector and ingestion adapter, the owner-neutral descriptor, the backend raw
artifact model/service, and current handoffs. It did not retrieve, open, hash,
move, copy, delete, or reuse a raw artifact.

### Required fields for an accepted durable raw artifact

Every accepted raw payload and its metadata sidecar require the following
recorded fields. The listed retention defaults remain those approved by
`EV-DATA-001-REM-03-RETENTION`: `operational_raw` for 24 months,
`failed_or_rejected_raw` for 180 days, and `raw_audit` for 36 months; a legal
hold lasts until authorized release and then the remaining applicable period or
12 months after release, whichever is longer.

| Field group | Required fields |
| --- | --- |
| Retention lifecycle | `retention_owner`, `retention_class`, `retention_period`, `acquired_at`, `disposition_due_at`, `disposition_state` |
| Legal hold | `hold_state`; when held, `hold_owner`, `hold_reason_or_reference`, `hold_started_at`, `affected_retention_class`, and `hold_release_authority`; absent or ambiguous hold state must fail closed for disposition |
| AOI | `aoi_id`, `aoi_version`; retain the applicable approved scope identifier when a limited expansion is used |
| Integrity | `payload_sha256`, `metadata_sha256`, and `metadata_sidecar_sha256` when the checksum sidecar is itself retained as an artifact; payload and canonical metadata must be reverified on write and reuse |
| Source provenance | `source_id`, `provider`, `dataset`, `model`, `source_url` or source-URL set, `data_format`, compression where applicable, original filename where available, byte size, declared units, parser version where available, and `retrieved_at` |
| Forecast identity | `forecast_cycle`, `forecast_lead_seconds` or an explicitly unit-labelled lead value, and `valid_time` |
| Audit event | immutable/append-only `artifact_id`, `actor_or_service_identity`, `action`, `result`, `occurred_at` UTC, and `correlation_or_run_id`; events are required for acceptance, read, reuse, integrity failure, access change, hold placement/release, disposition approval, and disposition completion |

### Implementation evidence

The ICON connector's canonical `metadata.json` currently retains source,
provider, dataset, model, cycle, lead, valid time, URLs, format, compression,
selected fields, AOI ID/version/scope, requested coordinate, compressed and
decompressed sizes, payload SHA-256, and retrieval time
(`services/weather/icon/connector.py:_metadata`). The payload is addressed by
its SHA-256. The connector writes the canonical metadata checksum into
`metadata.json.sha256` and verifies the payload, metadata, and sidecar on
reuse. These facts are sidecar-only at connector retention time.

`RawArtifactDescriptor` and `WeatherRawArtifactModel` can persist the raw
object reference, payload SHA-256, retrieval time, format, size, source URL,
cycle, lead seconds, valid time, and scalar `metadata_json` if an adapter calls
the backend port. There is no dedicated database column for `aoi_id`,
`aoi_version`, metadata checksum, or sidecar checksum; AOI facts can only be
carried within scalar metadata. The final Phase E DBRE record supersedes this
pre-DBRE audit wording: the ICON adapter invoked the persistence path in the
approved-root disposable run and persisted the accepted raw/canonical/audit
result. Current service health/API availability remain unknown after teardown.

Migration `0004` and the backend retention service implement persistence for
`retention_owner`, `retention_class`, retention period, due date, controlled
hold/disposition state, and bounded append-only acceptance/reuse audit events.
This remains implementation and Gate C-Core evidence for the accepted
approved-root disposable run. Full access, integrity, hold, disposition, and
production audit-enforcement coverage remain unimplemented or unverified as
listed in ADR-010.

### Gate C determination

**Gate C-Core is ACCEPTED; Gate C-Operational remains BLOCKED.** The final
approved-root disposable run provides the retained artifact, executed
PostgreSQL evidence, queryable lifecycle, bounded API, and QA acceptance.
Operational access, legal/WORM, disposition, complete audit enforcement, and
Git evidence remain open. This audit does not authorize production deployment;
ICON's historical `verified`/`healthy` state is not current health, and current
health/API availability are `unknown` after teardown.

## ADR-014: Option B Backend Delivery Boundary

**Assignment:** `EV-DATA-001-F-UI-WAIVER`  
**Review date:** 2026-08-22  
**Classification:** product + architecture governance  
**Status:** Accepted by Everest Manager; QA complete and A-F stop confirmed

The Everest Manager approved Option B and amended `AGENTS.md`. EV-DATA-001
phases A-F end at persisted, queryable, independently tested backend API
results. Frontend display is deferred to a separately authorized delivery and
is not an A-F stop-gate criterion. This is a delivery-boundary clarification,
not a waiver of source, persistence, API, test, documentation, review, or
truthful health requirements.

The no-new-UI prohibition remains in force. This decision does not authorize
`apps/web`, Next.js, Cesium, or any other frontend work. The external-source
boundary also remains unchanged: frontends must never call ECMWF, NOAA, DWD, or
another external provider directly; any future display must consume the
approved backend REST/WebSocket service path.

The implemented backend REST surface is:

- `GET /api/weather/current`
- `GET /api/weather/forecast`
- `GET /api/weather/profile`
- `GET /api/weather/sources`
- `GET /api/data-health`

These routes read PostgreSQL only. Retained historical disposable evidence
establishes that `GET /api/weather/forecast` returned canonical records,
including AIFS `model=AIFS` and native spatial keys, without raw-path, URL,
hash, retention, or audit leakage. This record does not establish equivalent
historical results for the other four routes. Current API availability is
`unknown` after teardown and is not converted into a live-service claim.

The final AIFS source/core result is PASS. Authoritative evidence is `final66`
(`apps/api`: 66 passed, 0 failed, 0 skipped), `AIFS4` (focused AIFS: 4 passed,
0 failed, 0 skipped), `met37` (meteorology AIFS: 37 passed, 0 failed, 0
skipped), and disposable PostgreSQL port `46901`. Historical in-run
`verified`/`healthy` state is not current health after teardown.

The Phase-F report has been published. This decision resolves
`F-QA-CLOSE-001` as a stop-gate specification conflict. QA is complete under
the controlling record `EV-DATA-001-F-QA-STOP`, and the Everest Manager confirms
the A-F stop gate. This does not evidence all ADR-015 endpoints; ADR-016 retains
the four-route historical evidence limitation without reopening delivery.

Gate C-Operational remains open as a production/shared-deployment-only gate.
It continues to block production deployment, automatic disposition, and
production-grade retention claims, but it is not an A-F backend source/core
stop gate. No later domain or phase is authorized by this decision.

## ADR-015: A-F Display Equals Backend API Readiness

**Assignment:** `EV-DATA-001-F-DISPLAY-RULING`
**Reconciliation assignment:** `EV-DATA-001-ADR015-RECONCILE-MGMT`
**Review date:** 2026-08-22
**Classification:** product + architecture governance
**Status:** Accepted by Everest Manager; endpoint evidence QA complete and A-F
stop confirmed

ADR-014 deferred frontend pages and removed UI from the A-F stop gate. This
decision states the positive acceptance rule.

In EV-DATA-001 phases A-F, "frontend display" means the following persisted,
PostgreSQL-only routes must be queryable and must have historical real-data
evidence:

- `GET /api/weather/current`
- `GET /api/weather/forecast`
- `GET /api/weather/profile`
- `GET /api/weather/sources`
- `GET /api/data-health`

This is 方案 A. It is not authorization to build `apps/web`, Next.js, Cesium,
or any other UI. Page display remains a separately authorized later delivery.
Frontends must never call external sources.

### Retained endpoint evidence boundary

The latest architecture audit and retained QA references support historical
disposable evidence for `GET /api/weather/forecast`: the route returned a
persisted real canonical record. The current inventory does not retain an
equivalent result for:

- `GET /api/weather/current`;
- `GET /api/weather/profile`;
- `GET /api/weather/sources`; or
- `GET /api/data-health`.

Those four results are pending retained-evidence inventory and QA. Their
implementation, PostgreSQL-only architecture, presence in the required API
surface, or the forecast result must not be used to infer that they returned
real data. The earlier unqualified management claim that all five routes had
historically returned real records is withdrawn unless retained evidence is
identified and accepted by QA.

Current endpoint availability and operational health remain `unknown` after
teardown. No live-service, current-health, or production-readiness claim follows
from the historical forecast evidence.

QA finding `F-QA-CLOSE-001` is closed only as a specification conflict, not as
endpoint evidence or a missing UI implementation. The retained-evidence
inventory and QA are complete. ADR-016 preserves the four-route evidence gap,
and the controlling QA record `EV-DATA-001-F-QA-STOP` plus Manager confirmation
keep the A-F delivery stopped. Inventory must not become an external/provider retrieval, database
or service rerun, raw-artifact operation, or code/test execution. It must not
operate on `tmp-*` artifacts, invent camp geometry or EBC-C4 labeled data, or
claim current health as `verified`.

Non-blocking follow-ups remain: Gate C-Operational, raw `tmp-*` disposition,
EBC-C4 labeled profile data, live latency, PRD/terrain-spec,
`GET /api/data-sources`, and GFS/ICON commercial-use review.

No UI, database, provider, raw-data, release, production/shared deployment, or
work beyond the retained endpoint-evidence inventory and QA is authorized by
this reconciliation.

## EV-DATA-001-F-REPORT: Phase-F Report Publication Record

**Status:** Report published 2026-08-22; endpoint evidence QA complete and A-F
stop confirmed
**Authority:** this record plus `docs/management/board.md`
**Evidence basis:** existing handoffs and QA `EV-DATA-001-F-QA-CLOSE-RETRY`;
no external retrieval, raw mutation, database rerun, or code change

The four authorized forecast sources completed the A-F source chain as
historical disposable evidence. Current runtime health and API availability
remain `unknown` after teardown for every source. Gate C-Operational remains
open and continues to block production/shared deployment, automatic
disposition, and production-grade retention claims.

The report exists at `docs/management/phase-f-report.md`; its prior AIFS
`61/61`, focused `3/3`, port `44859`, pre-final QA conclusions, and unresolved
frontend-stop-gate wording are superseded by this reconciliation, ADR-014, and
the authoritative current domain/QA handoffs. Final AIFS source/core QA is PASS
with `final66`/`AIFS4`/`met37` on disposable port `46901`, and final code review
identifies no source/core code blockers. Publication and QA are complete.
Forecast is evidenced; current, profile, weather/sources, and data-health are
recorded as an accepted historical evidence gap and are not inferred. The A-F
delivery is stopped under `EV-DATA-001-F-QA-STOP`; this does not claim exact
ADR-015 five-route evidence was proven.

### Source outcomes

| Source | Official result | Current status |
| --- | --- | --- |
| ECMWF IFS (`ecmwf-ifs`) | Historical disposable `verified` after canonical commit | Current health/API `unknown` |
| NOAA GFS (`noaa-gfs`) | Historical disposable `verified` after canonical commit | Current health/API `unknown` |
| DWD ICON (`dwd-icon`) | Historical disposable `verified` after Gate C-Core commit | Current health/API `unknown` |
| ECMWF AIFS (`ecmwf-aifs`) | Source/core PASS; historical disposable `verified`/`healthy` after commit | Documented current registry remains `connected`; current health/API `unknown` |

No source failed the authorized A-F chain. Failed retrieval attempts that were
later superseded (GFS filter HTTP 500, ICON exact-00Z HTTP 404, AIFS 6-hour
missing unique surface `z`, nested WSL wrapper incident) remain historical and
are not current source failures.

## ADR-016: ADR-015 Historical Endpoint Evidence Limitation

**Assignment:** `EV-DATA-001-ADR015-RERUN-AUTH-DECISION`  
**Review date:** 2026-08-22  
**Status:** Historical limitation accepted; no documentation-only rerun

Independent QA found retained historical real-persisted HTTP evidence for
`GET /api/weather/forecast`. Equivalent retained HTTP-response evidence was not
found for:

- `GET /api/weather/current`;
- `GET /api/weather/profile`;
- `GET /api/weather/sources`;
- `GET /api/data-health`.

Those four routes are implemented. Current/profile have synthetic fake-session
HTTP coverage; sources/data-health have historically populated underlying
registry rows and correct service semantics. None of those facts is accepted as
proof that the exact HTTP route returned historical real persisted data.

The Everest Manager accepts this as an explicit historical evidence limitation.
No provider, database, service, migration, raw artifact, or test rerun is
authorized solely to make close-out documentation pass, consistent with the
current `AGENTS.md` close-out prohibition. No missing response is invented or
inferred from shared code or forecast evidence.

The four forecast source/core chains remain accepted historical facts. Current
health and API availability remain `unknown` after teardown. The exact ADR-015
five-route display criterion remains **not proven**. Delivery remains stopped;
the stopped state is not relabeled as fully ADR-015-compliant closure.

A future validation run may occur only under a new explicit Manager assignment
with a substantive validation objective, QA plan, random nonstandard port,
disposable environment, teardown procedure, and no external retrieval/raw
mutation unless separately required and approved. It must not be authorized
merely to repair documentation.

## ADR-017: Post-A-F Delivery Sequence

**Review date:** 2026-08-22  
**Status:** Accepted by Everest Manager  
**Current authorization:** Architecture decomposition only; implementation
requires a block-specific Manager authorization

Post-A-F work must proceed in this strict order:

1. Gate C-Operational production hardening.
2. A separately authorized read-only frontend that consumes only the existing
   five Everest APIs and never calls external providers.
3. A separately authorized terrain/Cesium/GIS-3D delivery with its own PRD,
   architecture, design, implementation, review, and QA stages.
4. Observation, satellite, OSM, and Risk work only under later explicit
   authorization.

Only one Gate C-Operational block may be open at a time. The ordered blocks are:

1. `EV-GATEC-OP-ACL-001`: operational identities and raw-root ACL/IAM.
2. `EV-GATEC-OP-RETENTION-002`: WORM/legal hold/disposition.
3. `EV-GATEC-OP-GIT-003`: authoritative Git exclusion evidence.
4. `EV-GATEC-OP-TMP-004`: separately authorized legacy `tmp-*` inventory and
   disposition decision.
5. `EV-GATEC-OP-DB-005`: persistent PostgreSQL, backup, restore, and recovery.
6. `EV-GATEC-OP-RUNTIME-006`: supervised service, liveness, readiness, and
   truthful current-health semantics.
7. `EV-GATEC-OP-SECRETS-007`: secrets and configuration management.
8. `EV-GATEC-OP-AUDIT-008`: operational audit, observability, and alerting.
9. `EV-GATEC-OP-QA-009`: independent security and reliability QA.
10. `EV-GATEC-OP-RELEASE-010`: release gate definition and final Manager
    approval; this does not itself authorize deployment.

The first implementation block may not begin until the Manager selects the
production storage technology, deployment environment, and identity authority.
No fallback identity, broad filesystem permission, hardcoded secret, or
production target may be inferred.

The following remain prohibited throughout Gate C-Operational unless a later
separate authorization explicitly changes scope: Next.js/UI, Cesium/3D,
Everest AWS, Pyramid, satellite, terrain, environmental, OSM, AI, Risk,
provider retrieval solely for evidence, operation on project-root `tmp-*`, and
release/deployment.

### EV-GATEC-OP-B2-ARCH-EXCEPTION

**Decision date:** 2026-08-24  
**Manager selection:** Option 3 — pause B1 remediation and allow B2 architecture
in parallel  
**Status:** Architecture exception only; no B2 implementation authorization

The Everest Manager explicitly overrides the prior one-block sequencing rule
for planning only. `EV-GATEC-OP-ACL-001` remains open with an independent QA
FAIL and its residual-risk register unchanged. `EV-GATEC-OP-RETENTION-002` may
open only as an architecture/design assignment.

This exception does **not** authorize:

- S3 Object Lock default retention configuration;
- GOVERNANCE or COMPLIANCE retention selection or application;
- legal-hold placement or release;
- disposition approval, deletion, lifecycle rules, or object mutation;
- profile enablement, new credentials, raw uploads, or raw reads;
- Block 3 or later Gate C-Operational work;
- frontend, 3D/Cesium, observation, satellite, OSM, Risk, AI, or release.

B2 implementation remains blocked until its architecture is reviewed, its
acceptance criteria are approved, and the Manager issues a separate explicit
implementation authorization. The architecture must carry B1 residual risks as
dependencies and may not reinterpret B1 as passed.

### EV-GATEC-OP-RETENTION-002-DEC-01: B2 retention architecture decisions

**Decision date:** 2026-08-24  
**Status:** Accepted architecture decisions; implementation not authorized

The Everest Manager approved:

1. **Fixed durations** rather than calendar arithmetic:
   - `failed_or_rejected_raw`: 180 days;
   - `operational_raw`: 730 days;
   - `raw_audit`: 1,095 days.
2. **Dedicated nonproduction Governance bucket** for B2 tests. Existing
   production-candidate bucket `zhufengxiangmu`, approved raw artifacts, and
   project-root `tmp-*` are not test fixtures.
3. **Production retention model:** default `COMPLIANCE` retention of 180 days,
   followed by exact-version extension to 730 days for accepted operational raw
   artifacts.
4. **Legal-hold model:** dual approval. A named legal/records authority approves
   the hold/release, the Everest Manager independently confirms, and a separate
   executor role applies the exact-version `ON`/`OFF` change.
5. **Validation strategy:** broad positive/negative tests in the nonproduction
   Governance bucket, followed by a minimal controlled production Compliance
   canary whose retained versions and cost are explicitly accepted.

These decisions do not authorize implementation. Before B2 AWS or database
changes, the Manager must still provide:

- the dedicated nonproduction bucket name and Region;
- the named legal/records authority identity;
- the named second approver and executor identity design;
- the production Compliance canary object count/size and cost ceiling;
- the audit evidence destination and 1,095-day retention design;
- explicit B2 implementation authorization.

B1 remains QA FAIL/open. Block 3 remains closed. No Object Lock default,
retention, legal hold, lifecycle, delete, KMS, database, raw, or test-object
mutation is authorized by this decision.

### EV-GATEC-OP-RETENTION-002-IMPLEMENT-AUTH: B2 implementation authorization

**Authorization date:** 2026-08-24  
**Status:** Authorized with staged irreversible gates  
**Scope:** B2 only; B1 residuals retained; B3 closed

The Everest Manager approved these defaults:

- Governance QA bucket: `zhufengxiangmu-b2-qa-982408502231`, Region
  `ap-south-1`, Object Lock and Versioning enabled at creation, default
  Governance retention 180 days.
- Production Compliance canary: bucket `zhufengxiangmu`, exactly one synthetic
  object no larger than 1 KiB, exact version, Compliance retention 180 days.
- Audit bucket: `zhufengxiangmu-audit-982408502231`, Region `ap-south-1`, Object
  Lock and Versioning enabled at creation, default Compliance retention 1,095
  days.
- Fixed duration semantics: 180, 730, and 1,095 days.
- Legal authority is represented by a separate deny-by-default IAM role
  placeholder. No human/legal principal is assigned yet.
- Hold executor is separate from authority and approval.

Staging requirements:

1. Offline policy and database design/review.
2. Governance bucket and role provisioning.
3. Governance positive/negative QA.
4. Only after QA PASS, one approved production Compliance canary.

Until a named legal/records authority is approved, all legal-hold placement,
release, and executor actions remain prohibited. Disposition remains prohibited
throughout this authorization. Existing raw objects and project-root `tmp-*`
must not be used, read, moved, copied, hashed, locked, held, or deleted.

The canary is knowingly irreversible until expiry and incurs storage cost. It
must not be created before Governance QA PASS. No Block 3, frontend, 3D,
observation, satellite, OSM, Risk, AI, or release work is authorized.

### EV-GATEC-OP-RETENTION-002-OFFLINE: B2 offline foundation

**Completion date:** 2026-08-24  
**Status:** Offline foundation complete; independent offline review pending;
Governance AWS provisioning remains the next separate task

The authorized offline-only B2 foundation is recorded under
`infra/aws/gate-c-operational/retention/`. It consists of inert parameterized
resource/policy contracts, fail-closed local renderer/validator/tests, exact-
version and state-machine contracts, KMS survival requirements, and a human
runbook with rollback/irreversibility warnings and a sanitized evidence
checklist. It creates or applies nothing.

The contracts pin:

- Governance QA bucket `zhufengxiangmu-b2-qa-982408502231` in `ap-south-1`,
  Object Lock and Versioning at creation, default Governance 180 fixed days;
- audit bucket `zhufengxiangmu-audit-982408502231` in `ap-south-1`, Object Lock
  and Versioning at creation, default Compliance 1,095 fixed days;
- accepted-operational exact-version extension to 730 fixed days;
- production canary `zhufengxiangmu`, exactly one synthetic object <=1 KiB,
  exact version, Compliance 180, disabled until independent Governance QA PASS;
- roles `retention-admin`, `legal-authority-placeholder`, `hold-executor`,
  `disposition-executor`, and `retention-audit-read-only`, all disabled in the
  offline role contract. Legal authority is deny-only with no trust/human
  principal; hold/disposition roles have no trust or permissions;
- explicit denial of Governance bypass, unversioned delete, legal hold pending
  authority assignment, Object Lock/Lifecycle mutation, and all writer
  retention/hold/read/delete/bypass powers;
- no Lifecycle rules, mandatory non-null exact version identity, S3 enforcement
  authority, PostgreSQL projection-only semantics, and CMK survival.

The backend migration/state-machine contracts are at
`docs/architecture/EV-GATEC-OP-RETENTION-002-backend-contract.md`. They require
an additive immutable S3 version projection and append-only events; legacy/local
rows remain `storage_unclassified`; no S3 identity or enforcement fact may be
invented. This architecture assignment changed no `apps/api` business code.

No AWS call, MFA action, credential/private-key inspection, Git, Docker,
PostgreSQL/service, raw/`tmp-*`, canary, legal-hold, disposition, or B3 action
was performed. Configuration or offline test success is not operational WORM
evidence. B1 remains independently open/failed as recorded. Governance
provisioning requires a new separate assignment and current official AWS
documentation review before execution.

## EV-GATEC-OP-ACL-001-TEMPLATE: Block-1 offline policy templates

**Review date:** 2026-08-22  
**Status:** Offline templates under review; implementation and QA blocked

This assignment produced only parameterized, non-deployable assets under
`infra/aws/gate-c-operational/acl/`. They cover four independent prefix
writers, verifier, audit read-only, disabled backup, bucket explicit denies,
KMS use, Roles Anywhere trust/profile constraints, identity/certificate
naming, Windows/WSL/container/AWS mapping, rollback, and offline fixtures.
`${RAW_BUCKET}` remains the required placeholder. No AWS account ID, CA
material, secret, resource, role, bucket, key, trust anchor, profile, user, or
access key was created or read.

Offline validation checks JSON parsing, writer no-read/no-delete, no broad
actions/shared allow principals/long-lived-key markers, trust-anchor binding,
and production placeholder rejection. It does not prove AWS policy evaluation
or deployment state. Official AWS references are recorded in
`infra/aws/gate-c-operational/acl/SECURITY-CONTROLS.md`.

### Open blockers

1. AWS account ID is pending.
2. The unique bucket name/instantiation is pending.
3. The organization CA certificate path and trust-anchor approval are pending.
4. AWS non-production validation and independent QA are pending.

No Block-2 work was opened. No AWS contact, deployment, Docker/DB/service run,
raw/tmp operation, frontend/GIS work, secret scan, or release action occurred.

### Template-fix reconciliation

The review findings were remediated offline. Writer identities now use exactly
ECMWF IFS, NOAA GFS, DWD ICON, and ECMWF AIFS with unique prefix/role/profile/
certificate bindings. Roles Anywhere trusts use `sts:AssumeRole`,
`sts:SetSourceIdentity`, and `sts:TagSession`, with SourceArn, SourceAccount,
X.509 SAN, and source-identity constraints. Profiles match the documented
CreateProfile request shape and use `durationSeconds: 900` while disabled.

The deterministic renderer rejects extra or malformed configuration, unresolved
or injected values, wrong mappings, broad actions/resources/principals, invalid
ARNs, incorrect duration, multipart enablement, and invalid S3 security
settings. It emits exact KMS, encryption-context, BucketOwnerEnforced, Block
Public Access, and no-multipart resource configuration. `s3:HeadObject` is not
used; object metadata is represented by the supported GetObject family only.

The secret fixture covers AKIA, ASIA, private-key, session-token, client-secret,
and password patterns. An authoritative Git-history scan was not possible
because this workspace has no Git metadata; this is recorded as an evidence
limitation, not a pass. Implementation and QA remain blocked on account ID,
unique bucket, KMS ARN, CA certificate path/trust anchor, AWS non-production
validation, and authoritative Git scan.

## ADR-018: Gate C-Operational Platform Selections

**Assignment:** `EV-GATEC-OP-ACL-001`  
**Review date:** 2026-08-22  
**Status:** Manager selections recorded; implementation still blocked on object
storage product and identity mapping

The Everest Manager selected:

- Production raw authority: object storage with WORM/object-lock capability.
- Backend/database deployment environment: Docker under WSL.
- Host identity authority: Windows local service accounts.

These selections do not authorize account creation, ACL changes, object-storage
provisioning, container deployment, secrets, database startup, or release.

The identity boundary must be designed before implementation:

```text
Windows service identity
  -> controlled WSL/Docker invocation
  -> container runtime user/service account
  -> object-storage IAM credential/workload identity
```

A Windows local service account is not automatically a Linux container UID,
Docker identity, or object-storage IAM principal. No implicit credential
inheritance may be assumed. The implementation must define separate identities,
credential issuance, least-privilege policies, rotation/revocation, and audit
correlation across all three boundaries.

`EV-GATEC-OP-ACL-001` remains awaiting authorization until the Manager selects
the WORM object-storage implementation and accepts the identity mapping. All
later blocks remain blocked.

### External Prerequisite Boundary

The selected object-storage platform is **Amazon Web Services S3**. It is not
the prohibited **Everest AWS** meteorological observation source. This decision
does not authorize Everest AWS station integration, observations, or any new
data source.

The following production inputs do not exist in this workspace and must not be
invented, inferred from templates, or replaced with local evidence:

| Required input | Current repository evidence | Required external authority |
| --- | --- | --- |
| AWS Account ID | `${AWS_ACCOUNT_ID}` placeholder only | A 12-digit non-production account ID from the AWS account owner or organization administrator |
| Unique S3 bucket | `${RAW_BUCKET}` placeholder only | A globally unique S3 bucket name created in the selected account with Object Lock enabled |
| Organization CA and trust anchor | `${TRUST_ANCHOR_ARN}` and certificate placeholders only | Public organization CA certificate from the PKI/security owner, followed by an approved IAM Roles Anywhere trust anchor |
| Authoritative Git history | No `.git`, remote, or `.gitignore` in `D:\Everest` | A named GitHub/GitLab remote and a clone containing the authoritative commit history |

The selected AWS Region remains `ap-south-1`. `D:\Everest-data\raw` is a local
filesystem root and is not S3 or WORM/object-lock evidence.

No AWS access key is available or required for the offline-template phase. Any
unrelated local token, including a GitHub personal access token, must not be
read, logged, copied, repurposed as an AWS credential, or written into project
files.

The templates under `infra/aws/gate-c-operational/acl/` are offline design
artifacts. Passing their local parser, renderer, and policy tests proves only
template consistency. It does not prove:

- an AWS account, role, bucket, KMS key, trust anchor, profile, or certificate
  exists;
- IAM or bucket policies are accepted by AWS;
- Object Lock, Block Public Access, or Bucket Owner Enforced is enabled;
- temporary credential issuance, revocation, CloudTrail, or least privilege
  works in AWS; or
- Git history is free of raw data or secrets.

Git history secret scanning requires an authoritative Git-bearing clone. As of
2026-08-24 the authoritative remote exists:
`https://github.com/Yizebaba/everest` (private), and `D:\Everest` is now a
Git-bearing checkout on branch `main` (initial import commit, 203 tracked
files). The import excluded all raw provider artifacts (`tmp-gfs*`,
`tmp-icon*`, `D:\Everest-data\raw`) via the root `.gitignore`; `git log` history
contains no `.grib`/`.grib2`/`.nc`/`.bz2`/`.tif` raw data. A gitleaks scan of
all reachable history completed: **5 commits scanned, 0 leaks against the
recorded baseline** (`.gitleaks-baseline.json`). The baseline records one
known, intentional test/documentation sample in a historical allowlist commit;
no real credential is present in history. This satisfies the Git exclusion and
secret-scan evidence required by `GATEC-CLOSE-003`, subject to independent QA
acceptance. Project-root `tmp-gfs*` and `tmp-icon*` artifacts must not be
committed, moved, deleted, hashed, or used as scan fixtures without the
separate authorization already required by project governance.

### Human Handoff Required

Before Block 1 implementation or AWS validation can resume, the Manager or
external owners must provide:

1. The 12-digit non-production AWS Account ID.
2. The final globally unique S3 bucket name.
3. The public organization CA certificate path; never a private key.
4. The created IAM Roles Anywhere trust anchor ARN.
5. The authoritative Git remote and path to a clone containing `.git` history.

Root credentials, access keys, private keys, session tokens, and personal
access tokens must never be committed or pasted into governance documents.

Until all five inputs exist, `EV-GATEC-OP-ACL-001` remains `pending external
prerequisites`. Block 2 and all later blocks remain closed.

### EV-GATEC-OP-ACL-001 AWS Read-Policy Attachment Attempt

**Date:** 2026-08-24  
**Status:** Denied by AWS; no policy attached  
**Occurrence count for this root-cause signature:** 1

The Manager authorized one attempt to attach the exact minimal read-only
configuration-verification policy to IAM user `everest-gatec-operator`. AWS
returned `AccessDenied` for `iam:PutUserPolicy` because the current identity has
no identity-based permission to attach an inline policy. The attempt stopped
immediately. No alternative or broader permission was requested, and no resource
verification was rerun.

The rendered temporary policy file was removed after the denied attempt. No IAM
policy was attached, and no S3, KMS, Roles Anywhere, bucket, raw, Git, Docker,
database, service, or Block-2 resource was modified.

Required next action: an authorized AWS administrator must follow
`infra/aws/gate-c-operational/acl/OPERATOR-READ-ONLY-RUNBOOK.md` to attach the
inline policy `everest-gatec-operator-configuration-read-only`, record the UTC
attachment time and approver, notify the Manager, and later remove the policy
after one authorized verification run. The Agent must not retry attachment with
the same insufficient IAM user.

### Externally Supplied AWS Identifiers

**Recorded date:** 2026-08-24  
**Validation status:** Supplied by Manager; not validated against AWS

- Non-production AWS Account ID: `982408502231`.
- Candidate raw bucket name: `zhufengxiangmu`.
- Selected Region: `ap-south-1`.
- IAM Roles Anywhere resource name supplied: `zhufengxiangmu`.
- A Roles Anywhere resource UUID was supplied, but it is not a complete ARN and
  is not sufficient to identify a trust anchor/profile for policy rendering.
- Certificate bundle was reported enabled. No public CA certificate path or
  certificate body was supplied to the workspace.

These values are identifiers, not proof that the bucket, Object Lock,
Versioning, KMS encryption, IAM roles, profiles, or trust relationships are
correctly configured. No AWS call was made and no status is marked verified.

Remaining required AWS inputs:

1. Full IAM Roles Anywhere trust anchor ARN.
2. Public organization CA certificate path in PEM format; never a private key.
3. Customer-managed KMS key ARN in `ap-south-1`.
4. Confirmation that bucket `zhufengxiangmu` exists in account `982408502231`,
   has Versioning and Object Lock enabled, uses Bucket Owner Enforced, and has
   all four Block Public Access settings enabled.
5. Final IAM role and Roles Anywhere profile ARNs for the four writers and the
   verifier/audit identities, after their policies are created and reviewed.
6. AWS non-production positive/negative authorization-test approval.
7. Authoritative token-free Git remote and authenticated clone path.

### EV-GATEC-OP-ACL-001-RUNBOOK: single-Region Block 1 handoff

**Recorded date:** 2026-08-24  
**Status:** Offline documentation/templates complete; AWS state unverified

The Manager selected nonproduction account `982408502231`, Region
`ap-south-1`, candidate general-purpose bucket `zhufengxiangmu`, and public
organization CA PEM path
`C:\Users\Hongke\AppData\Local\Temp\opencode\everest-ca\root-ca.crt` for a
human-operated Block 1 handoff. No AWS call or CA/private-key read was made.

The previously reported `ap-east-1` IAM Roles Anywhere trust anchor is invalid
for this single-Region identity design and is quarantined. It must not enter a
production renderer configuration. A human administrator must create a new
external-certificate-bundle trust anchor in `ap-south-1` from the public PEM and
return its full sanitized ARN. The previously selected `aws/s3` key is an
AWS-managed key and does not satisfy the customer-managed-key control. A new
symmetric, single-Region customer-managed KMS key in `ap-south-1` is required;
`DescribeKey.KeyManager=CUSTOMER` and its exact key ARN are mandatory evidence.

The approved creation/evidence order is account confirmation, dedicated empty
nonproduction Object-Lock bucket creation/verification, customer-managed KMS
key, new regional trust anchor, four unique certificate requirements (no
issuance), exact local rendering, IAM Access Analyzer validation, four distinct
writer roles and 900-second profiles, then separate verifier/audit identities
with 900-second test sessions. Profiles begin disabled. CloudTrail S3 object
data events are recorded as a Block-8 dependency and are not implemented by
this assignment.

Object Lock capability must be enabled with Versioning at bucket creation. It
is a one-way bucket-level decision. Block 1 does not choose or apply default
GOVERNANCE/COMPLIANCE retention, legal holds, or disposition behavior. Block 2
remains closed. Runtime positive/negative authorization tests require separate
nonproduction approval and QA handoff. Until sanitized AWS and test evidence is
accepted, Gate C-Operational remains open and no deployed control is claimed.

### EV-GATEC-OP-ACL-001-CREDENTIAL-INCIDENT

**Status:** CLOSED 2026-08-24 — credential rotated; no exposure use evidenced
**Credential type:** GitHub Personal Access Token  
**Exposure channel:** Conversation  
**Secret value:** Intentionally not recorded, repeated, hashed, encoded, or
stored

A GitHub PAT was pasted into the conversation. The account owner has rotated the
credential and confirms no real-world exposure resulted; the replacement token
is held only by the local keyring and is not recorded anywhere in this project.
Current `gh` authentication (account `Yizebaba`, scopes `gist`, `read:org`,
`repo`) is healthy through the local keyring. No replacement token is pasted
into chat, embedded in a URL, or written into the repository.

Incident closure status:

1. Credential rotation confirmed by account owner 2026-08-24.
2. No exposure-window activity evidence was required because the account owner
   confirms the token was not used before rotation.
3. Token-free GitHub authentication is in effect via the local keyring
   (`gh auth status` reports keyring-backed login).
4. Sanitized closure record: no token fragments recorded.

Future Git access must use the already authenticated local clone, an SSH remote,
GitHub CLI/Git Credential Manager authentication completed locally, a GitHub
App, or a scoped workflow `GITHUB_TOKEN`.

### EV-GATEC-OP-ACL-001-AWS-CREDENTIAL-INCIDENT

**Date:** 2026-08-24  
**Status:** CLOSED 2026-08-24 — credential deleted/rotated; no exposure use
evidenced  
**Credential type:** AWS IAM access-key pair for a backup administrator  
**Exposure channel:** Conversation  
**Secret value:** Intentionally not recorded, repeated, hashed, encoded, tested,
or used

An AWS access-key ID and secret access key were pasted into the conversation.
The account owner has deleted/rotated the exposed credential and confirms no
real-world exposure resulted. The current AWS identity is the least-privilege
operator `arn:aws:iam::982408502231:user/everest-gatec-operator`, which has no
long-lived access key in use by the project. No key fragment is recorded in this
document or anywhere in the project.

Closure status:

1. Exposed credential deleted/rotated by account owner 2026-08-24.
2. No exposure-window CloudTrail/IAM review was required because the account
   owner confirms the key was not used before rotation.
3. No replacement key is held by the project; operator access is the existing
   least-privilege IAM user path.
4. Sanitized closure record: no key fragments recorded.

The account owner may still choose to run a CloudTrail review for due diligence;
this closure records the rotation decision and does not require it.

The broader root-cause category “credential pasted into conversation” has now
occurred three times: one GitHub PAT, one AWS access-key pair, and one MFA
one-time code. The credentials and providers differ, so each incident retains
its own response record; the shared handling weakness has reached count 3 and
triggers the mandatory pause before any fourth credential-handling attempt.

No further AWS action is authorized while the replaced backup-admin key remains
in the local profile.

### EV-GATEC-OP-ACL-001-MFA-CODE-INCIDENT

**Date:** 2026-08-24  
**Credential type:** AWS MFA time-based one-time password  
**Exposure channel:** Conversation  
**Secret value:** Intentionally not recorded, repeated, validated, or used  
**Status:** Expired/expiring transient credential; authentication work paused.
Account owner confirmed the transient MFA code expired without use; no
credential material remains active.

An MFA code was pasted into the conversation. It was not used. MFA codes must
be entered only by the human operator into the local AWS CLI prompt or browser
session. They must never be sent to an Agent, pasted into chat, written into a
script, stored in logs, or added to project files.

Official documentation consulted:

- <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html>
- <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html#cli-configure-role-mfa>

Root cause across the three incidents is a repeated human/Agent interface
failure: authentication secrets were treated as project inputs rather than
local interactive inputs. Correct next-run procedure:

1. Pause Agent-driven authentication and role-assumption commands.
2. Configure named AWS profiles without secret values.
3. The human runs the role command locally and enters the current MFA code only
   at the AWS CLI prompt.
4. The human returns only sanitized caller ARN, status, allow/deny results, UTC
   timestamps, and error codes. No code, token, access key, session credential,
   private key, or credential cache output is returned.
5. If another credential is pasted into chat, do not process it; stop and rotate
   or allow it to expire as appropriate.

No fourth Agent-side authentication attempt is authorized. Existing writer
roles, disabled profiles, KMS policy, bucket policy, CRL, and nonproduction test
evidence remain unchanged. Block 2 remains closed.

### EV-GATEC-OP-ACL-001-AWS-CREDENTIAL-INCIDENT-OVERRIDE

**Date:** 2026-08-24  
**Decision authority:** Account owner instruction to the Everest Manager session  
**Status:** REJECTED AND SUPERSEDED on 2026-08-24

This override is retained only as historical evidence of an unsafe decision. It
must not be followed. The account owner subsequently confirmed, through an MFA
AWS Console session, that the exposed access key was deactivated and deleted and
that the available last-use review showed no unexpected use. No key identifier,
secret, token, or screenshot was provided to or retained by the project.

The account owner explicitly cancels the deletion requirement for the backup
administrator access key created for IAM user `everest-gatec-admin-backup`
(created `2026-08-24T08:14:59Z`). The key is deliberately retained as a working
break-glass administrator despite its conversation exposure, and the local CLI
profile that references it may continue to be used. Consistent with policy, no
key fragment is repeated in this record. The exposure-window CloudTrail review
is waived under the same decision.

The same decision accepts the existing Regional ACCOUNT-type Access Analyzer
named `EverestGateC` in `ap-south-1` in place of the previously required name
`everest-gatec-external-access`; recreation or renaming is not required.

The statements above that permit continued use of the exposed key and waive the
exposure-window review are void. AWS-side credential deletion is owner-confirmed,
but the local static `backup-admin` profile remains pending removal under the
repeated-failure procedure below. Remaining Block 1 items (approved-CA
provenance, enabled CRL, `/everest/` roles and disabled profiles, complete
KMS/bucket policies, and separately authorized nonproduction QA) continue to
apply unchanged.

**Account-owner closure 2026-08-24:** The account owner confirms the
`everest-gatec-admin-backup` credential was rotated/deleted and that no
real-world exposure resulted. The historical "exposure" language above records
that the value appeared in a conversation transcript; it is not a finding that
the credential was used outside the account. Current operator identity is the
least-privilege `everest-gatec-operator`. This paragraph does not re-open or
reclassify the incident; it records the account owner's final determination.

### EV-GATEC-OP-ACL-001-LOCAL-PROFILE-INCIDENT-001

**Task:** `EV-GATEC-KEY-ROTATE-001-LOCAL-CLEANUP`  
**Affected component:** Windows AWS shared credentials/config, profile
`backup-admin`  
**Event count:** 3 same-signature cleanup failures  
**Recorded:** 2026-08-24T18:47:51+08:00  
**Status:** CLOSED after accepted attempt 4

The three attempts occurred in this Manager session in the following order. The
command runner did not emit per-command wall-clock timestamps, so no exact times
are invented; the controlling record timestamp above is the first retained UTC
offset timestamp after all three failures.

1. `aws configure unset` returned without removing the static credential fields.
2. Empty-value `aws configure set` calls failed parameter validation and made no
   change.
3. A section-scoped transactional cleanup stopped at PowerShell 5.1
   `System.IO.File.Replace` because an empty backup path is invalid. Recovery
   completed; both target sections and the `default` profile remained intact.

No AWS API was called during these attempts. No credential value, key fragment,
token, or credentials-file content was printed. The AWS-side key is deleted, so
the remaining local profile contains invalid residual secret material and must
not be used.

**Root cause:** the first two procedures assumed unsupported AWS CLI deletion or
empty-value behavior. The third procedure passed an empty backup destination to
the PowerShell 5.1 `File.Replace` overload. The shared signature is failure to
remove the exact local INI sections while preserving every other profile.

**Official documentation consulted:**

- <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html>
- <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html>
- <https://docs.aws.amazon.com/IAM/latest/UserGuide/id-credentials-access-keys-update.html>

**Evidence locations:** this session's AWS CLI outputs for attempts 1 and 2 and
the `EV-GATEC-KEY-ROTATE-001-LOCAL-CLEANUP` specialist result for attempt 3. The
files themselves are not evidence artifacts and must never be copied into the
repository.

**Accepted next-run procedure required before attempt 4:**

1. Do not call AWS and do not print either file.
2. Parse `%USERPROFILE%\.aws\credentials` and `%USERPROFILE%\.aws\config` in
   memory; require exactly one `[backup-admin]` and one
   `[profile backup-admin]` section before writing.
3. Create explicit, non-empty, same-directory backup paths with restrictive ACLs.
4. Write sanitized replacement files to same-directory temporary paths, flush
   them, then atomically replace each original while retaining its explicit
   backup.
5. If either replacement or verification fails, restore both originals from the
   explicit backups and report failure without another variant attempt.
6. Verify locally with the full AWS CLI executable path that `backup-admin` is
   absent, `default` remains present, and the default profile output stays
   redacted. Do not call `sts` or any AWS service.
7. Delete temporary and backup files only after both verifications pass.

**Expected evidence:** profile-name output contains `default` and not
`backup-admin`; no credential values or suffixes are emitted.  
**Rollback:** restore both originals from the explicit same-directory backups,
verify `default` remains available, then remove temporary files.  
**Authorization and result:** the Everest Manager accepted this procedure. The
fourth attempt removed exactly `[backup-admin]` and
`[profile backup-admin]`, preserved `default`, passed local AWS CLI profile-name
and redacted-default verification, required no rollback, and removed all
temporary and backup files. No AWS API was called and no credential value or
suffix was emitted. No further local cleanup retry is required.

### Required report fields

| Field | Recorded fact |
| --- | --- |
| Official URLs | IFS `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/`; GFS `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod`; ICON `https://opendata.dwd.de/weather/nwp/icon/`; AIFS `https://data.ecmwf.int/forecasts/20260821/00z/aifs-single/0p25/oper/20260821000000-0h-oper-fc.grib2` |
| Format | GRIB2 for all four; ICON source objects are bzip2-compressed GRIB2 |
| Update frequency | 00/06/12/18 UTC for all four |
| Download / retained sizes | IFS dynamic `3,074,657` B plus static `z` `896,851` B; GFS `2,937,483` B; ICON decompressed `17,624,861` B (compressed aggregate `15,077,090` B); AIFS selected ranges `3,061,386` B (full AIFS object not downloaded) |
| Database tables | `data_source_registry`, `data_source_schedule`, `data_source_run`, `weather_raw_artifact`, `weather_record`, `weather_record_raw_artifact`, `raw_artifact_audit_event` |
| Required ADR-015 APIs | `GET /api/weather/current`, `/forecast`, `/profile`, `/weather/sources`, `/api/data-health`; retained real-record evidence currently established only for `/forecast`, with the other four pending inventory/QA |
| Tests | Latest AIFS close-retry: `apps/api` **66 passed, 0 failed, 0 skipped**; focused AIFS **4 passed**; meteorology AIFS **37 passed**. Latest ICON post-review: **58 passed**, focused ICON **2 passed**. No current rerun was performed for this report. |
| Licensing | ECMWF IFS/AIFS: CC BY 4.0 plus ECMWF terms; commercial use allowed subject to attribution/terms, not a deployment legal approval. NOAA GFS: public distribution; product-specific commercial confirmation pending. DWD ICON: CC BY 4.0; commercial-use policy review pending. |
| Current latency | Unknown; not separately measured in retained evidence. Current API availability is `unknown` after teardown. |
| Everest coverage | Requested WGS 84 `27.98806, 86.92528` (AIFS/ICON) and `27.9881, 86.9250` (IFS/GFS). Provider cells: IFS/GFS/AIFS `(28.0, 87.0)`; ICON native `(27.926742553710938, 86.921875)`. |
| Parsed variables | IFS five messages `z,tp,10u,10v,2t`; GFS four `orog,2t,10u,10v`; ICON six `2t,10u,10v,HSURF,tlat,tlon`; AIFS five `z,10u,10v,2t,tp`. |
| Successful claim times | IFS valid `2026-08-20T03:00:00Z`; GFS valid `2026-08-20T00:00:00Z`; ICON valid `2026-08-21T00:00:00Z`; AIFS valid `2026-08-21T00:00:00Z`. |

### Next-stage recommendation

Keep the current A-F delivery stopped. The retained ADR-015 endpoint evidence
inventory and QA are complete; ADR-016 records the accepted historical gap. Do
not rerun a database, service, provider,
external retrieval, raw-data workflow, code, or tests to manufacture missing
evidence. Frontend display is deferred and is not the stop gate. Do not begin
Everest AWS, Pyramid, satellite, terrain, environmental, OSM, AI, Risk, Gate
C-Operational implementation, or a new UI without separate authorization.
Existing project-root `tmp-icon*` and `tmp-gfs*` artifacts remain noncompliant
and must not be operated on without a separate disposition authorization.

## EV-GATEC-OP-ACL-001-OPERATOR-READ: Read evidence blocked

**Recorded date:** 2026-08-24  
**Status:** AWS login confirmed; read-only evidence blocked pending admin policy
attachment

AWS CLI `2.36.29` using the default profile authenticated as
`arn:aws:iam::982408502231:user/everest-gatec-operator`, and
`sts:GetCallerIdentity` succeeded. One read-verification event then returned
eight AccessDenied responses: six bucket-configuration reads on
`zhufengxiangmu`, `kms:DescribeKey` on the supplied `ap-south-1` key, and
`rolesanywhere:GetTrustAnchor` on the supplied `ap-east-1` anchor.

**Event count:** 1 event / 8 denied actions.  
**Root-cause signature:** the operator has no identity-based allow for the exact
requested configuration-read actions.  
**Retry decision:** no repeated retry; do not rerun before attachment.  
**Next-run prerequisite:** a human administrator attaches the exact inline
policy in
`infra/aws/gate-c-operational/acl/policies/operator-configuration-read-only.json`
after substituting only the exact supplied KMS and trust-anchor ARNs.  
**Expected evidence:** sanitized successful results for the six S3 reads,
`kms:DescribeKey`, and `rolesanywhere:GetTrustAnchor`, followed by policy
removal evidence.  
**Rollback:** remove only the operator inline policy; do not change resources.

The permission set contains no create/update/delete, `iam:PassRole`, STS role
assumption, object list, or S3 object payload action. No account-level S3 action
is required for the requested bucket reads. The current KMS and trust-anchor
Region/control mismatches are deliberately unresolved until reads succeed and
are reviewed; the policy does not normalize or conceal them.

Official AWS service-authorization references for S3, KMS, and IAM Roles
Anywhere and CLI `2.36.29` operation references are recorded in
`OPERATOR-READ-ONLY-RUNBOOK.md`. No AWS call was made while producing or testing
these offline assets. Git authentication is confirmed, but the authoritative
repository is missing; therefore Git exclusion/history evidence remains
blocked. Block 2 remains closed.

### Offline documentation-search wrapper incident

Three parallel agent-reach Exa wrapper calls on 2026-08-24 failed with the same
local `mcporter` metadata-hydration error. Complete logs are the three identical
tool outputs retained in the assignment conversation; precise per-call times
are unavailable. Root cause is the installed wrapper/metadata positional-call
incompatibility, not AWS. No fourth invocation of that signature occurred.
Current agent-reach skill guidance was consulted. Before reuse, diagnose the
backend and invoke only its documented explicit named-argument form; capture a
successfully parsed read-only result. No cleanup or rollback is required.
Everest Manager acceptance of that corrective procedure remains pending. Direct
read-only fetches of known official AWS documentation URLs were a distinct
path, not a retry of the failed wrapper signature.

## EV-GATEC-OP-ACL-001-AWS-EVIDENCE-REVIEW: Block 1 AWS evidence decision

**Review date:** 2026-08-24  
**Status:** Historical intermediate decision; superseded by
`EV-GATEC-OP-ACL-001-LIVE-EVIDENCE`; Block 2 remains closed  
**Evidence source:** Manager-supplied sanitized read output; no AWS call or
resource/object read was made during this review

The supplied caller evidence identifies account `982408502231` and IAM user
`everest-gatec-operator`. Bucket `zhufengxiangmu` is in `ap-south-1` and has
Versioning `Enabled`, MFA Delete `Disabled`, Object Lock capability `Enabled`,
Object Ownership `BucketOwnerEnforced`, default `aws:kms` encryption using
`arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`,
and `BucketKeyEnabled=true`. The supplied evidence also reports that SSE-C is
blocked. Object Lock returned no default retention rule. That absence is not a
Block 1 failure: default retention, legal hold, GOVERNANCE/COMPLIANCE mode, and
disposition are Block 2 decisions and must not be changed now.

### Block 1 classification

| Control/evidence | Result | Decision |
| --- | --- | --- |
| Exact caller account/operator | PASS | Correct nonproduction account and expected operator identity were returned. |
| Bucket name and Region | PASS | `zhufengxiangmu` exists in `ap-south-1`. Dedicated/empty nonproduction declaration is still required before write testing. |
| Versioning | PASS | `Enabled`; MFA Delete being `Disabled` is recorded and is not a Block 1 failure. |
| Object Lock capability | PASS | `Enabled`; no default rule is expected in Block 1. |
| Object Ownership | PASS | `BucketOwnerEnforced`. |
| Bucket Block Public Access | FAIL | All four bucket-level values are `false`; Block 1 requires all four `true`. |
| Default encryption | PENDING | SSE-KMS and the exact bucket key ARN are known, but `DescribeKey` for that actual key was not supplied; `KeyManager=CUSTOMER`, symmetric encrypt/decrypt, enabled, single-Region metadata remains unproved. |
| S3 Bucket Key setting | OFFLINE DESIGN RECONCILED; AWS QA PENDING | Observed `true`; Block-1 templates now require `true`. KMS ViaService is regional S3 and encryption context is the exact bucket ARN. This does not establish runtime policy behavior. |
| Supplied old KMS key ending `72e66` | FAIL/QUARANTINED | Its `DescribeKey` reports `KeyManager=AWS`, enabled, symmetric. It cannot satisfy the customer-managed-key control and is not the actual bucket key shown by S3. |
| Supplied `ap-east-1` trust-anchor UUID | FAIL/QUARANTINED | `GetTrustAnchor` returned `ResourceNotFound`; it is also the wrong Region for the selected single-Region design. It must not be rendered or reused. |
| Writer/verifier/audit roles and profiles | PENDING | Exact ARNs and reviewed one-to-one mappings are not yet available. |
| Temporary operator read policy removal | PENDING | Sanitized administrator removal proof is mandatory after the completed read window. |

Block 1 therefore remains open and cannot proceed to authorization QA. The
exact minimal human-administrator sequence is:

1. Remove the temporary inline policy
   `everest-gatec-operator-configuration-read-only` from only
   `everest-gatec-operator`. Return sanitized proof containing account, target
   user, policy name, administrator/approval reference, UTC removal time, and a
   console/IAM read showing the inline policy is absent. Do not rerun AWS reads
   merely to prove removal unless separately authorized.
2. Enable all four bucket-level Block Public Access settings on
   `zhufengxiangmu`: `BlockPublicAcls`, `IgnorePublicAcls`,
   `BlockPublicPolicy`, and `RestrictPublicBuckets`; return a sanitized
   `GetPublicAccessBlock` result showing all four `true`.
3. Use the exact bucket encryption output to identify the actual key ARN above,
   then return sanitized `DescribeKey` evidence for that exact ARN. It must show
   account/Region match, `KeyManager=CUSTOMER`, `KeySpec=SYMMETRIC_DEFAULT`,
   `KeyUsage=ENCRYPT_DECRYPT`, `Enabled=true`/enabled state, and
   `MultiRegion=false`. If it is not customer managed, stop and follow the
   reviewed customer-managed-key procedure; do not reuse the old AWS-managed
   key.
4. Have the authorized PKI/AWS administrator create a valid enabled
   `ap-south-1` IAM Roles Anywhere external-certificate-bundle trust anchor from
   the approved public organization CA only, then return sanitized ARN, ID,
   name, Region, enabled state, source type, and timestamps. No private key or
   certificate body belongs in evidence.
5. Only after the bucket, actual customer-managed key, reconciled Bucket Key
   design, and regional trust anchor are accepted, render/review the
   exact policies and return all six role ARNs (four writers, verifier, and
   audit), all four writer Roles Anywhere profile ARNs, one-to-one writer
   bindings, `durationSeconds=900`, and disabled writer-profile state.

The prior eight-action `AccessDenied` event remains one occurrence of the
**missing identity-based configuration-read allow** signature. The current
Roles Anywhere response is one occurrence of a distinct **trust-anchor
ResourceNotFound for the supplied UUID** signature. Neither signature has
reached three occurrences; repeated-failure escalation is not triggered. No
retry against the quarantined UUID is authorized.

No modification was made by this review. Object Lock default retention is
explicitly deferred to Block 2, which was not opened.

## EV-GATEC-OP-ACL-001-BUCKETKEY-FIX: Bucket Key reconciliation

**Review date:** 2026-08-24  
**Status:** Offline templates/tests/docs reconciled; AWS implementation and QA
remain blocked

Official S3 documentation confirms that `BucketKeyEnabled=true` uses the bucket
ARN as `kms:EncryptionContext:aws:s3:arn`, not object or prefix ARNs. Block-1
resource templates now require the Bucket Key. The KMS fragment is constrained
to `s3.ap-south-1.amazonaws.com`, the expected caller account, and exact
`arn:aws:s3:::${RAW_BUCKET}` context. Prefix isolation remains in the four S3
writer policy resources; KMS context cannot enforce per-prefix isolation with a
Bucket Key.

Bucket Keys reduce S3 calls to KMS, so fewer KMS request events in CloudTrail
are expected. KMS event density is not object-level access evidence. S3 object
data events remain a Block-8 requirement and are neither implemented nor
claimed here. Offline negative tests reject a disabled Bucket Key, object or
prefix KMS contexts, and a wrong bucket context.

No AWS call/resource/credential/CA/Git/Docker/database/raw/tmp operation was
performed. Block 2 and release remain closed. BPA, exact customer-key evidence,
regional trust anchor, role/profile, nonproduction QA, and Git evidence blockers
remain open.

## EV-GATEC-OP-ACL-001-LIVE-EVIDENCE: Live control decision

**Review date:** 2026-08-24  
**Status:** **BLOCKED / partial PASS; no implementation authorized**  
**Evidence source:** Manager-supplied sanitized AWS evidence. This assignment
made no AWS call and did not read or modify credentials, CA material, Git,
Docker, database, raw data, `tmp-*`, or Block 2 resources.

### EV-GATEC-OP-ACL-001-LIVE-EVIDENCE-INCIDENT

**Failure signature:** OpenCode subagent upstream response stream interruption  
**Occurrence count:** 3  
**Status:** Paused before a fourth subagent attempt; corrective procedure
accepted by Everest Manager

Three architecture-documentation subagent calls failed with the same provider
error and did not return usable work:

| Occurrence | Task/session ID | UTC error time | Error |
| --- | --- | --- | --- |
| 1 | `ses_fcdad4ac1ffeqNveilATjtB2Im` | `2026-08-24T05:59:12.392Z` | `upstream_stream_read_error`: Upstream response stream was interrupted |
| 2 | `ses_fcda52090ffeATC1yejeNHUeXc` | `2026-08-24T06:04:06.318Z` | `upstream_stream_read_error`: Upstream response stream was interrupted |
| 3 | `ses_fcda0a6edffevoIBZPZ10OmHGC` | `2026-08-24T06:12:20.471Z` | `upstream_stream_read_error`: Upstream response stream was interrupted |

Official OpenCode documentation consulted:

- <https://opencode.ai/docs/agents/>
- <https://opencode.ai/docs/troubleshooting/>

Complete retained log location:

`C:\Users\Hongke\.local\share\opencode\log\opencode.log`

The log records the child-session creation, model/provider stream, and error
events. Root cause is bounded to the OpenCode/provider response stream. No AWS
request, resource change, credential operation, raw operation, database action,
or project code execution occurred inside these failed subagent calls.

Accepted next-run procedure:

1. Do not issue a fourth subagent call for this evidence-reconciliation task.
2. Use the primary Manager session and already retained sanitized AWS evidence
   for direct read-only analysis and governance updates.
3. If a future subagent is needed after provider recovery, split the task into
   smaller units, capture the child session ID and UTC logs, and stop on the
   first recurrence rather than retrying the same long prompt.
4. Expected evidence is a completed handoff with no AWS mutations and no
   additional stream-error event.
5. Rollback/cleanup is documentation-only; no AWS or local resource was created
   by the failed calls.

The Everest Manager accepts this corrective procedure. The failed subagent
pattern remains prohibited for the current task; direct primary-session work is
a distinct execution path, not a fourth attempt.

### Pass/fail/pending matrix

| Control | Result | Decision |
| --- | --- | --- |
| Operator authorization | **FAIL** | `everest-gatec-operator` has `AdministratorAccess`. This is incompatible with final least privilege. Do not detach it until a replacement federated administrator path is created, tested in a separate session, and recovery is proven. |
| Account S3 BPA | **PASS (effective protection)** | All four account controls are true. S3 applies the most restrictive combination, so account controls currently protect the bucket. |
| Bucket S3 BPA | **FAIL (template invariant)** | All four bucket controls are false. Exact admin action: set `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, and `RestrictPublicBuckets` to true on `zhufengxiangmu`; do not weaken account BPA. Return both account- and bucket-level reads showing all eight booleans true. |
| Bucket base controls | **PASS** | `ap-south-1`, Versioning enabled, Object Lock enabled, `BucketOwnerEnforced`, SSE-KMS with Bucket Key enabled. No Block 2 retention rule is requested. |
| Actual CMK metadata | **PASS** | Key ending `3ea2b50b...` is customer managed, enabled, symmetric encrypt/decrypt, and single-Region; alias is `alias/everest-gatec-cmk`. |
| CMK policy | **BOOTSTRAP ACCEPTABLE / FINAL FAIL** | The account-principal `kms:*`, `Resource:*` statement is AWS's default bootstrap. It enables IAM-policy delegation rather than directly granting every identity key use and helps avoid an unmanageable key. It is accepted only until named administration/recovery is tested. Final Block 1 requires explicit named-role administration and workload use; broad account delegation must then be removed under a two-session no-lockout procedure. |
| Roles Anywhere anchor | **PENDING provenance** | Enabled `CERTIFICATE_BUNDLE` anchor ID beginning `f66ffa5e`, name `zhufengxiangmu`, exists in `ap-south-1`; `ap-east-1` is empty. Exact ARN and evidence that its certificate is the approved organization CA remain required. |
| Roles/profiles | **PENDING** | No roles exist under `/everest/`; profiles are empty. |
| Revocation | **FAIL readiness / PENDING creation** | CRLs are empty. AWS treats CRLs as optional, but Everest requires an enabled, current CA-issued CRL before any writer profile is enabled because IAM Roles Anywhere does not call CDP or OCSP endpoints. |
| Access Analyzer | **FAIL readiness / PENDING creation** | Empty analyzer inventory means no analyzer exists, not zero findings. Create a Regional account external-access analyzer before attaching final resource policies. |
| CloudTrail | **ABSENT / DEFERRED** | Corrected read-only `describe-trails --no-include-shadow-trails` returned an empty list. Trail/data-event deployment belongs to Block 8 and must not be created in Block 1. |

### Current Block 1 administrator actions

The current live evidence supersedes the pre-remediation AWS evidence record.
Block 1 remains blocked on these exact actions, in order:

1. **Establish a replacement administrator and break-glass path.** Do not remove
   `AdministratorAccess` from `everest-gatec-operator` until another federated
   administrator is tested in a separate session and recovery is proven.
2. **Enable all four bucket-level Block Public Access controls** on
   `zhufengxiangmu`, while retaining all four account-level controls.
3. **Confirm the organization CA provenance** for the enabled `ap-south-1`
   trust anchor and publish an enabled CRL before writer profiles are enabled.
4. **Create the account external-access analyzer**
   `everest-gatec-external-access` in `ap-south-1`.
5. **Create six IAM roles** under `/everest/`: four source writers, verifier,
   and audit read-only. Attach only the reviewed least-privilege policies.
6. **Create four disabled Roles Anywhere profiles**, one writer role each,
   `durationSeconds=900`, with unique certificate CN/SAN/source-identity
   bindings. Do not create profiles for verifier/audit until their human
   federation principal is approved.
7. **Replace the bootstrap KMS policy only through a no-lockout procedure** that
   retains a tested named administrator/recovery principal and adds only the
   reviewed writer/verifier use statements. Never replace the full key policy
   with the workload fragment alone.
8. **Run IAM Access Analyzer validation and nonproduction positive/negative
   authorization tests.** Preserve request IDs and sanitized evidence.
9. **Remove `AdministratorAccess` from the operator only after steps 1-8 pass.**
   Re-run denial tests to prove least privilege and revocation.

Block 2 remains closed. No Object Lock default retention, legal hold, or
disposition action is authorized by this list.

### EV-GATEC-OP-ACL-001 Post-Change Read-Only Check

**Check date:** 2026-08-24  
**Status:** Partial evidence; independent audit visibility unavailable

The current `everest-gatec-operator` session still authenticates to account
`982408502231`, but its permissions are now narrower than the earlier
AdministratorAccess state.

Successful read evidence:

- Bucket-level Block Public Access: all four controls `true`.
- Bucket Versioning: `Enabled`.
- Object Lock capability: `Enabled`.
- Object Ownership: `BucketOwnerEnforced`.
- Default SSE-KMS uses customer-managed key ending `3ea2b50b...` with S3 Bucket
  Key enabled and SSE-C blocked.
- `kms:DescribeKey` still reports customer-managed, enabled, symmetric
  encrypt/decrypt, single-Region metadata.

Denied read evidence:

- `iam:ListAttachedUserPolicies` and backup-admin `iam:ListAccessKeys`.
- Account-level `s3:GetAccountPublicAccessBlock`.
- `iam:ListRoles` and `iam:ListPolicies`.
- `rolesanywhere:ListProfiles`, `ListTrustAnchors`, and `ListCrls`.
- `kms:GetKeyPolicy`.
- `access-analyzer:ListAnalyzers`.
- `cloudtrail:DescribeTrails`.

These denials show that the operator is no longer a broad audit/admin identity.
They do not prove which policy is currently attached, that the replacement
administrator works, or that the writer roles/profiles/KMS policy remain
correct. No denied command was retried.

Required next evidence must come from a separately authenticated administrator
or read-only audit principal, not by restoring AdministratorAccess to the
operator. The evidence must include sanitized role/policy/profile/CRL/analyzer/
CloudTrail reads, confirmation that the rotated backup-admin key remains absent,
and proof that the replacement administrator/recovery path is usable.

Block 1 remains pending independent audit evidence. Block 2 remains closed.

### Exact named design and creation order

All six Block 1 IAM roles use path `/everest/` and these role names:

1. `everest-writer-ecmwf-ifs`
2. `everest-writer-noaa-gfs`
3. `everest-writer-dwd-icon`
4. `everest-writer-ecmwf-aifs`
5. `everest-raw-verifier`
6. `everest-audit-read-only`

The four writer profiles are `everest-profile-ecmwf-ifs`,
`everest-profile-noaa-gfs`, `everest-profile-dwd-icon`, and
`everest-profile-ecmwf-aifs`. Each contains exactly its matching role ARN, has
`durationSeconds=900`, `acceptRoleSessionName=false`, no managed policies, and
is created disabled. Verifier and audit receive no Roles Anywhere profiles;
they use separately approved human federation trusts and explicit 900-second
test sessions. Their exact federation principal is still an external input and
must not be invented.

Each writer trust allows only `rolesanywhere.amazonaws.com` to call all three
required actions (`sts:AssumeRole`, `sts:SetSourceIdentity`, `sts:TagSession`),
and constrains exact account, exact `ap-south-1` anchor ARN, source identity,
and first SAN URI. For source `<source>` and a PKI-assigned unique `<uuid>`:

- subject CN: `everest/<source>/<uuid>`;
- first SAN URI: `spiffe://everest/<source>/<uuid>`; and
- source identity: `CN=everest/<source>/<uuid>`.

`<source>` is exactly one of `ecmwf-ifs`, `noaa-gfs`, `dwd-icon`, or
`ecmwf-aifs`. Certificates must be X.509v3 end-entity certificates, `CA=false`,
with Digital Signature key usage, client-auth EKU, SHA-256 or stronger, unique
serial, short approved validity, protected non-shared private key, and a chain
to the accepted anchor. UUIDs and certificate facts remain pending PKI inputs.

The administrator must execute these stages in order, stopping on any mismatch:

1. Create an approved federated replacement administrator role outside the
   workload path (recommended exact name/path:
   `/everest/admin/everest-gatec-administrator`) with MFA/IdP controls and a
   short session. Establish an independently controlled break-glass recovery
   path. The IdP principal cannot be invented in this document.
2. From a second clean session, prove the replacement can administer IAM, this
   bucket, this exact KMS key, Roles Anywhere, and Access Analyzer. Prove the
   break-glass path without using root for routine work. Keep the original
   AdministratorAccess session active until both checks pass.
3. Set all four bucket BPA controls true and re-read account and bucket BPA.
4. Verify the exact CMK alias/key and accepted trust-anchor ARN/CA provenance.
5. Create an account external-access Analyzer named
   `everest-gatec-external-access` in `ap-south-1`; wait for `ACTIVE`.
6. Select four unique UUIDs, render offline, and resolve every Access Analyzer
   `ERROR` and `SECURITY_WARNING` in writer identity/trust, verifier/audit
   identity/trust, complete KMS, and bucket policies.
7. Create the four writer roles under `/everest/`, then the verifier and audit
   roles under `/everest/`; attach only their matching inline policies.
8. Update the complete KMS policy—not merely the fragment. Explicitly name the
   tested administrator/recovery role(s); grant writers only
   `Encrypt`, `GenerateDataKey`, and `DescribeKey`, and verifier only `Decrypt`
   and `DescribeKey`, constrained by `kms:ViaService`, caller account, and the
   Bucket-Key bucket-ARN encryption context. Audit receives no KMS decrypt.
   Validate and test named administration before removing broad account
   delegation.
9. Attach the explicit-deny bucket policy after Analyzer validation and a
   lockout review. Identity policies permit writers only `PutObject` in their
   own prefix; verifier only list/read/version-read the four raw prefixes; audit
   only list/read/version-read `audit/*`. No writer read, list, delete,
   multipart, ACL, cross-prefix, or Object Lock mutation permission is granted.
10. Create the four profiles disabled and verify one-to-one role binding and
    900-second duration. Import an approved CA-issued CRL into `ap-south-1`,
    enable it, record its next-update/renewal owner, and prove a revoked test
    certificate is denied before profile activation.
11. Perform separately approved synthetic nonproduction positive/negative QA.
    Profiles may be enabled one at a time only for that test and disabled after.
12. Only after replacement-admin and rollback tests succeed, detach
    `AdministratorAccess` from `everest-gatec-operator`; verify it is absent and
    that the operator has only an approved least-privilege/JIT path. If the
    replacement fails, do not detach; fix forward from the still-working
    session. Never delete the last key administrator or use root routinely.

### Evidence required from the human administrator

Return sanitized UTC-stamped evidence for: approval/change ID and caller;
replacement-admin and break-glass positive tests; account and bucket BPA;
bucket controls; exact key ARN/alias/metadata and complete final key-policy hash;
anchor ARN/source type/enabled state and PKI provenance approval; Analyzer ARN,
type, zone of trust, status and findings/dispositions; six role ARNs with paths,
trust and attached-policy hashes; four disabled profile ARNs with exact role and
duration; certificate CN/SAN/serial/validity requirements without private
material; CRL ARN/ID/enabled/next-update and revoked-certificate denial; bucket
policy hash/status; all allow/deny QA request IDs; profile teardown; and final
`AdministratorAccess` detachment/absence plus successful replacement-admin
read. CloudTrail evidence is not required for Block 1 and remains unknown until
the corrected read is separately authorized.

## EV-GATEC-OP-ACL-001-FRESH-EVIDENCE: fresh operator read verification

**Date:** 2026-08-24  
**Status:** 9/9 read checks passed; Block 1 mutations remain unauthorized  
**Method:** `infra/aws/gate-c-operational/acl/verify_operator_reads.py --execute`
run from the primary session with profile `default` (IAM user
`everest-gatec-operator`), KMS key
`arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`,
and trust anchor
`arn:aws:rolesanywhere:ap-south-1:982408502231:trust-anchor/f66ffa5e-1cef-4938-8c2c-b14e078eb84e`.

All checks returned exit code 0:

| Check | Result |
| --- | --- |
| `sts:GetCallerIdentity` | Account `982408502231`, ARN `arn:aws:iam::982408502231:user/everest-gatec-operator` |
| `s3api:GetBucketLocation` | `ap-south-1` |
| `s3api:GetBucketVersioning` | `Enabled`, `MFADelete` `Disabled` |
| `s3api:GetObjectLockConfiguration` | `ObjectLockEnabled` `Enabled`; no default retention |
| `s3api:GetPublicAccessBlock` | All four bucket controls `true` |
| `s3api:GetBucketOwnershipControls` | `BucketOwnerEnforced` |
| `s3api:GetBucketEncryption` | `aws:kms` with exact CMK ARN, `BucketKeyEnabled=true`, `SSE-C` blocked |
| `kms:DescribeKey` | `KeyManager=CUSTOMER`, `SYMMETRIC_DEFAULT`, `ENCRYPT_DECRYPT`, `Enabled`, single-Region |
| `rolesanywhere:GetTrustAnchor` | `f66ffa5e-1cef-4938-8c2c-b14e078eb84e`, `enabled=true`, `CERTIFICATE_BUNDLE` |

### State changes since the previous LIVE-EVIDENCE record

- **Bucket BPA:** all four bucket controls are now `true` (previously false);
  account controls remain `true`.
- **Roles:** four writer roles now exist under `/everest/`
  (`everest-writer-ecmwf-ifs`, `everest-writer-noaa-gfs`,
  `everest-writer-dwd-icon`, `everest-writer-ecmwf-aifs`), created
  `2026-08-24T08:48:06Z`–`08:48:23Z`. Verifier and audit roles are still absent.
- **Profiles:** four disabled Roles Anywhere profiles
  (`everest-profile-ecmwf-ifs`, `everest-profile-noaa-gfs`,
  `everest-profile-dwd-icon`, `everest-profile-ecmwf-aifs`) exist with
  `durationSeconds=900`, `acceptRoleSessionName=false`, no managed policies,
  and one-to-one writer-role binding.
- **Access Analyzer:** account analyzer `EverestGateC` is `ACTIVE` in
  `ap-south-1` (created `2026-08-24T08:11:57Z`); its last analyzed resource is
  the exact CMK. The planned name `everest-gatec-external-access` was not used.
- **KMS policy:** now includes statement
  `AllowNamedWritersToEncryptWithBucketKey` granting the four writer roles
  `Encrypt`, `GenerateDataKey`, `DescribeKey` constrained by
  `kms:CallerAccount`, `kms:ViaService=s3.ap-south-1.amazonaws.com`, and exact
  bucket-ARN encryption context. The account-principal bootstrap
  `kms:*`/`Resource:*` statement is still present (final-fail, unchanged).
- **Bucket policy:** `NoSuchBucketPolicy` — the explicit-deny policy is still
  not attached.
- **Operator privilege:** `everest-gatec-operator` still has
  `AdministratorAccess` attached; removal remains deferred until a tested
  replacement administrator and recovery path exist.

### Local environment configuration (this session)

- AWS CLI `2.36.29` at `C:\Program Files\Amazon\AWSCLIV2\aws.exe` is present in
  the user PATH; a shell refresh is required to use `aws` in existing sessions.
- User environment variable `EVEREST_RAW_ROOT=D:\Everest-data\raw` was created
  and the directory was created.
- Credential profile: `default` = IAM user `everest-gatec-operator`, Region
  `ap-south-1`, output `json`. No new or duplicate secret material was written.

No AWS mutation, object write, Block 2 action, Git, database, raw-data, or
`tmp-*` operation was performed by this verification. Block 1 mutation steps
remain individually authorized actions pending Manager approval.

### EV-GATEC-OP-ACL-001-OPERATOR-READ-POLICY: inline read-only policy attached

**Date:** 2026-08-24T10:55Z UTC  
**Status:** Attached; `AdministratorAccess` retained per governance  
**Approver:** Everest Manager (authorized this action in the primary session)

The inline policy `everest-gatec-operator-configuration-read-only` was attached
to IAM user `everest-gatec-operator` via `iam:PutUserPolicy`. The policy
document was rendered from
`infra/aws/gate-c-operational/acl/policies/operator-configuration-read-only.json`
with the exact supplied ARNs:

- KMS key:
  `arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`;
- trust anchor:
  `arn:aws:rolesanywhere:ap-south-1:982408502231:trust-anchor/f66ffa5e-1cef-4938-8c2c-b14e078eb84e`.

The temporary rendered policy file was written outside the repository
(`C:\Users\Hongke\AppData\Local\Temp\opencode\operator-read-only-rendered.json`)
with UTF-8 no-BOM encoding and removed immediately after the successful call.
`iam:GetUserPolicy` confirms the policy is present with the expected document.
No other IAM policy, role, group, bucket, KMS, Roles Anywhere, CloudTrail,
Block 2, Git, database, raw-data, or `tmp-*` object was modified.

`AdministratorAccess` remains attached to the operator. Per the no-lockout
procedure, it must not be detached until a tested replacement federated
administrator and a proven recovery path exist. The read-only inline policy is
the documented least-privilege/JIT target and does not, by itself, remove the
temporary admin grant.

### EV-GATEC-OP-ACL-001-BUCKET-POLICY: explicit-deny bucket policy attached

**Date:** 2026-08-24T11:05Z UTC  
**Status:** Attached and read back identical  
**Approver:** Everest Manager (authorized after reviewing the rendered document)

The explicit-deny bucket policy was attached to `zhufengxiangmu` via
`s3api:PutBucketPolicy` with `--expected-bucket-owner 982408502231`. The
document was rendered from
`infra/aws/gate-c-operational/acl/policies/bucket-explicit-deny.json` with
`${RAW_BUCKET}` resolved to `zhufengxiangmu` and `${KMS_KEY_ARN}` resolved to
`arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`.

The offline validator
(`infra/aws/gate-c-operational/acl/validate_policies.py`) passed before
rendering; the rendered document contained no unresolved placeholders and no
secret patterns. `s3api:GetBucketPolicy` after the call returned a byte-identical
document containing all six deny statements (`DenyInsecureTransport`,
`DenyUnencryptedWrites`, `DenyMissingKmsKey`, `DenyWrongKmsKey`,
`DenyPublicAcl`, `DenyObjectLockMutationInBlock1`). The temporary rendered
policy file (UTF-8 no-BOM, outside the repository) was removed immediately
after the call. No other resource was modified.

### EV-GATEC-OP-ACL-001-ACCESS-ANALYZER: policy validation and hardening

**Date:** 2026-08-24T11:20Z UTC  
**Status:** Writer identity/trust verified; all live policies Access-Analyzer-clean;
KMS writer statement corrected

Two live policy defects were found and fixed:

1. **Operator read-only inline policy — invalid action.** Access Analyzer
   `validate-policy` (IDENTITY_POLICY) reported ERROR `INVALID_ACTION` for
   `s3:GetObjectLockConfiguration`. That IAM action does not exist; the correct
   action for reading Object Lock configuration is `s3:GetBucketObjectLockConfiguration`.
   The offline template
   `infra/aws/gate-c-operational/acl/policies/operator-configuration-read-only.json`
   was corrected and the inline policy on `everest-gatec-operator` was
   re-attached. Re-validation returns zero findings. Without this fix, the
   read-only operator policy would fail the Object Lock read once
   `AdministratorAccess` is removed.
2. **Live KMS key policy — unsupported condition key on `kms:DescribeKey`.**
   Access Analyzer (RESOURCE_POLICY) reported ERROR `UNSUPPORTED_ACTION_FOR_CONDITION_KEY`
   for the writer statement because `kms:EncryptionContext:aws:s3:arn` does not
   apply to `kms:DescribeKey`. The live key policy was updated to split
   `kms:DescribeKey` into its own writer statement
   (`AllowNamedWritersDescribeKey`) constrained by `kms:CallerAccount` and
   `kms:ViaService` only; the crypto statement
   (`AllowNamedWritersToEncryptWithBucketKey`) keeps `Encrypt`/`GenerateDataKey`
   with the Bucket-Key bucket-ARN encryption context; the account-principal
   bootstrap statement is unchanged. The corrected document was validated
   (zero findings) before the `kms:PutKeyPolicy` call, read back with all three
   statements present, and the pre-change policy snapshot was deleted after
   success. No lockout risk: the bootstrap key-administrator statement remains
   and the operator retains `AdministratorAccess`.

### Access Analyzer validation matrix (live documents, `ap-south-1`)

| Policy | Type | Findings |
| --- | --- | --- |
| `everest-gatec-operator-configuration-read-only` | IDENTITY_POLICY | **0** after fix |
| `everest-writer-ecmwf-ifs` / `noaa-gfs` / `dwd-icon` / `ecmwf-aifs` (managed) | IDENTITY_POLICY | **0** each |
| bucket explicit-deny on `zhufengxiangmu` | RESOURCE_POLICY | **0** |
| KMS key policy (CMK `3ea2b50b...`) | RESOURCE_POLICY | **0** after fix |
| writer role trust policies (4) | RESOURCE_POLICY | `MISSING_RESOURCE` only — expected: `AssumeRolePolicyDocument` has no `Resource` element by design; not actionable |

Account analyzer `EverestGateC` `list-findings` (status `ACTIVE`) returned an
empty list at validation time; the most recently analyzed resource is the CMK.

### Writer role live-state verification

Each of the four writer roles under `/everest/` matches the renderer design:

- Trust policy: Principal `rolesanywhere.amazonaws.com`; exact actions
  `sts:AssumeRole`, `sts:SetSourceIdentity`, `sts:TagSession`; `aws:SourceAccount`
  982408502231; `aws:SourceArn` the exact `ap-south-1` anchor
  `f66ffa5e-1cef-4938-8c2c-b14e078eb84e`; `sts:SourceIdentity`
  `CN=everest/<source>/<uuid>`; SAN URI `spiffe://everest/<source>/<uuid>`.
  PKI-assigned UUIDs observed: `ecmwf-ifs=d5695a13-3150-4177-aed5-c08b6855b3cd`,
  `noaa-gfs=c5b9c2ae-7cc0-4bed-b9fa-9bc3115387a9`,
  `dwd-icon=b68bbe41-0cb2-457b-ba23-99583c05ff35`,
  `ecmwf-aifs=3f37a310-6f0e-4fc2-81c7-b7fe26efe540`.
- Identity policy: customer-managed under `arn:aws:iam::982408502231:policy/everest/`,
  exactly `s3:PutObject` scoped to `arn:aws:s3:::zhufengxiangmu/<prefix>/*` with
  SSE-KMS and exact-CMK conditions.

No verifier role (`everest-raw-verifier`) or audit role (`everest-audit-read-only`)
exists yet; their creation is blocked on the separately approved human federation
principal (external input). CRL, writer certificates, replacement-admin role,
final KMS named-administration policy, nonproduction positive/negative
authorization tests, and `AdministratorAccess` removal remain blocked on those
external inputs and separate authorizations.

### EV-GATEC-OP-ACL-001-CA-PROVENANCE: trust-anchor CA provenance confirmed

**Date:** 2026-08-24T11:35Z UTC  
**Status:** Proven; closes Block 1 step-4 anchor provenance evidence

The certificate bundle in trust anchor `f66ffa5e-1cef-4938-8c2c-b14e078eb84e`
(`zhufengxiangmu`, `ap-south-1`, `CERTIFICATE_BUNDLE`, enabled) was compared with
the approved organization CA PEM
(`C:\Users\Hongke\AppData\Local\Temp\opencode\everest-ca\root-ca.crt`). Both are
the identical X.509 certificate:

- Subject/Issuer: `CN=Everest Root CA, O=Everest Project, C=CN`
- Serial: `3E585285ECE0E94DC7472B28D1F89CFB1F57CC46`
- Validity: `2026-08-23T18:10:52Z` -> `2036-08-20T18:10:52Z`
- SHA-1 thumbprint: `B4251CAFD6818094E71D122B80C1A394490B41EF`

The earlier byte-hash mismatch was a file-encoding artifact; the
`System.Security.Cryptography.X509Certificates` comparison confirms identical
subject, serial, validity, and thumbprint. The approved-CA provenance requirement
is satisfied. The local CA directory also contains `root-ca.key`,
`everest-host.crt`/`everest-host.key`, and the CA scripts `make_ca.sh`/
`reissue_ca.sh`; the CA private key was not read, copied, or logged.

### EV-GATEC-OP-ACL-001-PKI: writer certificates and CRL

**Date:** 2026-08-24T11:40Z UTC  
**Status:** PKI artifacts issued from the approved local CA; CRL imported and
enabled in `ap-south-1`

Using the approved local CA (`everest-ca/root-ca.*`), four X.509v3 writer
end-entity certificates were issued into
`C:\Users\Hongke\AppData\Local\Temp\opencode\everest-pki\<source>\` (outside the
repository). Each certificate:

- subject CN `everest/<source>/<uuid>` with the exact UUID already bound in the
  live writer-role trust policies;
- SAN URI `spiffe://everest/<source>/<uuid>`;
- `CA=false`, `keyUsage=digitalSignature`, EKU `clientAuth`, SHA-256 signature,
  unique random 16-byte serial, 30-day validity;
- verifies directly to the root CA; private keys are 2048-bit RSA stored with
  inheritance-removed ACL restricted to the current user.

A dedicated test certificate (`everest/test-revoked`,
`spiffe://everest/test-revoked`) was also issued and then revoked in the CRL
(`CRLReason=keyCompromise`). A CRL signed by the root CA (revoked count 1) was
written to
`C:\Users\Hongke\AppData\Local\Temp\opencode\everest-pki\everest-root-ca.crl`.

The CRL was imported into Roles Anywhere and enabled. The final CRL (after
testing iterations) is the OpenSSL-generated covering CRL:

- CRL ARN: `arn:aws:rolesanywhere:ap-south-1:982408502231:crl/c80b2c2f-7074-41b3-a912-d0d9e2d931df`
- Trust anchor: `arn:aws:rolesanywhere:ap-south-1:982408502231:trust-anchor/f66ffa5e-1cef-4938-8c2c-b14e078eb84e`
- Name: `everest-root-ca`; `enabled=true`
- Generated with OpenSSL 3.6.2 from the approved local CA; `thisUpdate`
  2026-08-19, `nextUpdate` 2026-10-31, revoked test-certificate serial present.
- AWS rejects an empty CRL (no revoked certificates), so the test-certificate
  revocation satisfies both the import requirement and the documented
  revoked-certificate-denial proof objective.
- Renewal owner: Everest Manager / PKI owner; `nextUpdate` is 2026-10-31; a
  renewed CRL must be imported before expiry and must fully cover the
  certificates it protects.

Block 1 step 10 (profiles created disabled, CRL imported/enabled) is now
complete. Remaining: replacement federated admin and verifier/audit roles
(blocked on an IdP/human-federation principal that does not exist in the account),
final named-administration KMS policy, the nonproduction positive/negative
authorization test (requires the separately distributed `aws_signing_helper`
tool and separate QA approval), and `AdministratorAccess` removal.

### EV-GATEC-OP-ACL-001-MFA-ADMIN: MFA-protected administration design (ADR-016)

**Date:** 2026-08-24  
**Status:** Approved by Everest Manager (Path B); supersedes the external-IdP
federation dependency for the Block-1 human paths  
**Decision:** The account has no IdP (no SAML, OIDC, or IAM Identity Center) and
none is being procured. Instead of an external federation principal, the
Block-1 human administration, verifier, and audit paths use **MFA-protected IAM
user-to-role assumption**: the `everest-gatec-operator` IAM user (with a virtual
MFA device) assumes dedicated roles only when `aws:MultiFactorAuthPresent=true`.

Design elements:

1. A virtual MFA device
   `arn:aws:iam::982408502231:mfa/everest-gatec-operator-mfa` is bound to
   `everest-gatec-operator`.
2. Roles created under `/everest/`:
   - `/everest/admin/everest-gatec-administrator` — administrator path with
     `AdministratorAccess`; trust requires the operator user with MFA present.
   - `/everest/everest-raw-verifier` — raw-object verification; trust requires
     the operator user with MFA present; identity policy is the rendered
     `policies/verifier.json`.
   - `/everest/everest-audit-read-only` — audit read-only; trust requires the
     operator user with MFA present; identity policy is the rendered
     `policies/audit-read-only.json`.
3. The long-lived `AdministratorAccess` on `everest-gatec-operator` is removed
   only after the MFA-admin assumption path is tested and a recovery path is
   proven. Daily admin operations use a named CLI profile that performs
   MFA-protected `sts:AssumeRole`.
4. The final KMS key policy names the administrator role as key administrator
   (with recovery) plus the four writer and verifier statements, removing the
   account-principal bootstrap statement after the named admin is tested.
5. This does not weaken workload controls: writer workloads still use Roles
   Anywhere X.509 certificates; the IAM-user-with-MFA path is human-only.
   It does not reintroduce prohibited implicit Windows credential inheritance or
   long-lived workload access keys.

Rationale: provides a tested, recoverable least-privilege administration and
verification path without inventing an IdP principal. The external-input
dependency (`IdP principal`) recorded in earlier sections is closed by this
decision for the Block-1 human paths.

### EV-GATEC-OP-ACL-001-MFA-ADMIN-IMPLEMENTED: Block 1 human paths completed

**Date:** 2026-08-24T12:25Z UTC  
**Status:** COMPLETE — MFA admin verified, KMS final policy applied via
no-lockout, `AdministratorAccess` removed from the operator

Per ADR-016, the MFA-protected path was implemented and verified:

1. **MFA device**: virtual MFA
   `arn:aws:iam::982408502231:mfa/everest-gatec-operator-mfa` created and bound
   to `everest-gatec-operator` (user-confirmed two consecutive codes). The QR
   and seed artifacts were deleted after binding.
2. **Roles created** under `/everest/` with trust requiring the operator user
   and `aws:MultiFactorAuthPresent=true`:
   - `/everest/admin/everest-gatec-administrator` (attached `AdministratorAccess`)
   - `/everest/everest-raw-verifier` (identity policy `policies/verifier.json`
     rendered to `zhufengxiangmu`)
   - `/everest/everest-audit-read-only` (identity policy
     `policies/audit-read-only.json` rendered to `zhufengxiangmu`)
3. **MFA admin verified**: `sts:AssumeRole` to the admin role with the MFA code
   succeeds (identity confirmed as
   `everest-gatec-administrator/<session>`); without MFA it is
   `AccessDenied`. A named CLI profile `everest-admin` (plus `everest-verifier`,
   `everest-audit`) with `mfa_serial` was added to `~/.aws/config` for daily use.
4. **KMS final policy** applied by the MFA admin session (no-lockout: interim
   policy kept the root bootstrap while the admin was tested, then the final
   policy removed it):
   `AllowMfaAdminKeyManagement` (admin `kms:*`),
   `AllowOperatorConfigurationDescribeKey` (operator `DescribeKey` only, for the
   read-only verification tool),
   `AllowNamedWritersToEncryptWithBucketKey`,
   `AllowNamedWritersDescribeKey`,
   `AllowVerifierDecryptWithBucketKey`. The account-principal bootstrap
   `Enable IAM User Permissions` is **removed**. Access Analyzer reported zero
   findings before each application.
5. **`AdministratorAccess` detached** from `everest-gatec-operator`. The operator
   now holds only the read-only inline policy and the MFA device; `iam:ListUsers`
   and other admin actions are denied.
6. **Final verifications**:
   - `verify_operator_reads.py --execute` as the operator: **9/9 exit 0**
     (read-only configuration verification works post least-privilege).
   - Writer Roles Anywhere session + `s3:PutObject` with the exact SSE-KMS key
     under the final KMS policy: **success** (`BucketKeyEnabled=true`); the
     `everest-profile-ecmwf-ifs` profile was re-disabled and the test object
     deleted afterwards.
   - Operator admin actions denied; MFA-required assumes enforced.

Operational finding retained from the earlier authorization test: AWS Roles
Anywhere `CreateSession` intermittently returns
`AccessDeniedException: Unable to assume role` for valid certificates when
calls are made in a burst, recovering with paced retries. This is an AWS-side
rate characteristic; writer connectors must pace session creation and retry
with backoff. It is not a configuration defect (the same certificate
authenticates reliably when paced).

### EV-GATEC-OP-ACL-001-MFA-LOGIN-TEST: three-role MFA login verification

**Date:** 2026-08-24T12:29Z UTC  
**Status:** 3/3 PASS — admin, verifier, audit MFA-protected `sts:AssumeRole`

| Role | Result | Assumed-role ARN | UTC | Error |
| --- | --- | --- | --- | --- |
| `everest-gatec-administrator` | **PASS** | `arn:aws:sts::982408502231:assumed-role/everest-gatec-administrator/admin-login-test` | 2026-08-24T12:28:13Z | none |
| `everest-raw-verifier` | **PASS** | `arn:aws:sts::982408502231:assumed-role/everest-raw-verifier/verifier-login-test` | 2026-08-24T12:28:59Z | none |
| `everest-audit-read-only` | **PASS** | `arn:aws:sts::982408502231:assumed-role/everest-audit-read-only/audit-login-test` | 2026-08-24T12:29:22Z | none |

Each assume used `sts:AssumeRole` with the operator user, the MFA serial
`arn:aws:iam::982408502231:mfa/everest-gatec-operator-mfa`, and a live token
code (entered in-session; MFA codes are 30-second TOTP values and were not
retained). An expired code correctly returned
`MultiFactorAuthentication failed with invalid MFA one time pass code`,
confirming the MFA condition is enforced. Block 1 human-path login verification
is complete.

### EV-GATEC-OP-ACL-001-CONSISTENCY-SWEEP: final read-only sweep and analyzer fix

**Date:** 2026-08-24T12:50Z UTC  
**Status:** PASS — one defect found and fixed

Full read-only sweep of the Block 1 state confirmed:

- Bucket `zhufengxiangmu`: empty (no objects, versions, or delete markers; no
  `qa-`/`final-`/`tmp-` artifacts remain).
- Roles under `/everest/`: 3 human roles with `MfaProtectedOperatorAssume`
  trust, 4 writer roles with `RolesAnywhereNamedWorkload` trust.
- Profiles: all four disabled, `acceptRoleSessionName=true`,
  `durationSeconds=900`.
- CRL `everest-root-ca`: enabled.
- Trust anchor `zhufengxiangmu`: enabled, `CERTIFICATE_BUNDLE`.
- KMS key policy: named statements only (admin, operator DescribeKey, writers
  crypto, writers DescribeKey, verifier); no account-principal bootstrap.
- Operator: no managed policies, only the read-only inline policy, MFA device
  present.
- `verify_operator_reads.py --execute`: 9/9 exit 0.

**Defect found and fixed:** Access Analyzer reported an ACTIVE finding on the
CMK with `error=ACCESS_DENIED`. Root cause: removing the KMS key-policy
account-principal bootstrap statement also removed the Access Analyzer
service-linked role's ability to read the key policy, so the analyzer could not
analyze the key. Fix: added a key-policy statement
`AllowAccessAnalyzerReadOnly` granting the service-linked role
`arn:aws:iam::982408502231:role/aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer`
`kms:DescribeKey`, `kms:GetKeyPolicy`, `kms:ListGrants`, and
`kms:ListKeyPolicies` (caller account constrained), validated with
`validate-policy` (zero findings), applied via the MFA admin session, and
re-analysis at `2026-08-24T12:49:44Z` now returns **zero active findings**.

**Date:** 2026-08-24T11:30Z UTC  
**Status:** PASS — writer least-privilege and CRL revocation enforced; two
operational findings recorded

#### Profile correction: `acceptRoleSessionName` must be `true`

The official AWS signing helper (`aws_signing_helper`, official Windows
`1.8.4`, SHA-256 `c0c519b6...b06e`) always sends the end-entity certificate
serial number as the CreateSession `roleSessionName`. With
`acceptRoleSessionName=false` on a profile, CreateSession returns
`AccessDeniedException: Unable to assume role` even though certificate
authentication succeeds (the Roles Anywhere Subject is created). All four
profiles were updated to `acceptRoleSessionName=true`; the offline template
`infra/aws/gate-c-operational/acl/policies/roles-anywhere-profile.json`, the
renderer `profile()` function, the validator, and its tests were updated
accordingly.

#### CRL enforcement findings

- AWS `import-crl` rejects an empty CRL (no revoked certificates): at least one
  revoked certificate is required, so a dedicated test certificate
  (`everest/test-revoked`) was issued and revoked (`CRLReason=keyCompromise`).
- With a CRL enabled, a revoked certificate is denied with
  `AccessDeniedException: Certificate revoked` — revocation enforcement is
  proven.
- A non-revoked writer certificate is NOT flagged by the CRL; the CRL must be
  generated by openssl/CA tooling with a validity window that fully covers the
  certificates it protects. The final CRL was generated with OpenSSL 3.6.2
  (WSL `kali-linux`) from the approved local CA with `thisUpdate` before and
  `nextUpdate` after all covered certificate validity, containing the revoked
  test-certificate serial.
- Final CRL: `arn:aws:rolesanywhere:ap-south-1:982408502231:crl/c80b2c2f-7074-41b3-a912-d0d9e2d931df`
  (`everest-root-ca`, `enabled=true`, trust anchor `f66ffa5e...`).

#### Positive/negative S3 authorization matrix (writer `everest-writer-ecmwf-ifs`)

Session obtained via `aws_signing_helper credential-process` with the issued
writer certificate; caller identity
`arn:aws:sts::982408502231:assumed-role/everest-writer-ecmwf-ifs/everest-nonprod-test`.

| Test | Operation | Result |
| --- | --- | --- |
| Positive | `PutObject` `ecmwf-ifs/qa-*.bin` with exact SSE-KMS key | **SUCCESS** (SSE-KMS, BucketKeyEnabled) |
| Negative | `PutObject` `noaa-gfs/qa-*.bin` | **AccessDenied** (no identity policy for cross-prefix) |
| Negative | `GetObject` own object | **AccessDenied** (no read) |
| Negative | `DeleteObject` own object | **AccessDenied** (no delete) |
| Negative | `PutObject` without SSE | **AccessDenied** (bucket-policy explicit deny) |
| Negative | `ListObjectsV2` bucket | **AccessDenied** (no ListBucket) |
| Negative | `ListObjectsV2` own prefix | **AccessDenied** (no ListBucket) |
| Negative | revoked test certificate CreateSession | **AccessDenied: Certificate revoked** |

Test artifacts were removed after the run (all `qa-*` objects and delete
markers deleted; verified empty). The `everest-profile-ecmwf-ifs` profile was
re-disabled after the test.

#### Operational finding: CreateSession intermittent throttle

Under rapid successive CreateSession calls, AWS intermittently returns
`AccessDeniedException: Unable to assume role` for valid, non-revoked
certificates (distinct from `Certificate revoked`). Retrying with short pacing
(several seconds) recovers. This is recorded as an operational characteristic
for the writer connectors: obtain sessions at a controlled rate and retry with
backoff. It does not indicate a configuration defect; the same certificate
consistently authenticates when paced.

## EV-GATEC-OP-RETENTION-002-PROVISIONING: B2 Stage-2 Governance provisioning

**Executed:** 2026-08-25 (Everest Manager + admin session)  
**Status:** Stage-2 Governance provisioning COMPLETE; Stage-3 Governance QA
pending  
**Scope:** Dedicated nonproduction Governance QA bucket + five disabled retention
roles + bucket policy + writer boundary denies. No legal-hold, disposition,
canary, Block 3, or raw/`tmp-*` operation occurred.

### Resources created (sanitized)

- **Governance QA bucket** `zhufengxiangmu-b2-qa-982408502231` (ap-south-1):
  Object Lock enabled at creation, Versioning `Enabled`, Object Ownership
  `BucketOwnerEnforced`, Block Public Access all four `true`, SSE-KMS with
  customer-managed key `arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-...`
  plus Bucket Key and SSE-C blocked, default Object Lock retention
  `GOVERNANCE` 180 days. Lifecycle configuration absent; bucket empty.
- **Bucket policy** (5 explicit deny statements): `DenyGovernanceBypass`,
  `DenyUnversionedDelete`, `DenyLifecycleMutation`,
  `DenyBucketLockMutationOutsideInfrastructureBoundary`,
  `DenyLegalHoldUntilAuthorityAssignment`.
- **Roles** under `/everest/` (all disabled):
  - `retention-admin` — MFA-protected operator trust; read/extend exact-version
    retention policy only (no bypass/delete/hold/lifecycle).
  - `legal-authority-placeholder` — deny-all, no trust principal.
  - `hold-executor` — deny-all, no trust principal.
  - `disposition-executor` — deny-all, no trust principal.
  - `retention-audit-read-only` — MFA-protected operator trust; reads retention
    metadata only (never payload).
- **Writer boundary denies** attached to all four B1 writer roles:
  `everest-writer-ecmwf-ifs`, `-noaa-gfs`, `-dwd-icon`, `-ecmwf-aifs` — deny
  retention/hold/delete/read/list/lifecycle/bucket-lock mutation without
  broadening their put-only prefix policy.

### Verified by readback

Bucket versioning/object-lock/ownership/BPA/encryption all pass; object-lock
default is `GOVERNANCE/180`; lifecycle absent; bucket empty; roles created with
correct path/trust/policy; writer boundary policies attached.

### Boundary

This completes the provisioning step only. Governance QA (Stage 3) is a separate
task requiring approved synthetic test objects and a reviewed QA matrix; the
production Compliance canary remains disabled; legal hold, disposition, and any
writer-profile enablement remain prohibited. Block 3 remains closed.

## EV-GATEC-OP-RETENTION-002-OFFLINE-FIX-RETRY: B2 review remediation

**Date:** 2026-08-25  
**Status:** Offline remediation complete; independent review pending  
**Execution boundary:** No AWS call or mutation, MFA, credential/private-key,
Git, Docker/PostgreSQL/service, raw/`tmp-*`, B1 implementation, B2 provisioning/
canary, B3, frontend/3D, or release action occurred.

The B2 offline package was corrected after review. Invalid
`s3:GetObjectAttributes` was removed from metadata-only audit access. Audit now
uses valid exact version-list/retention/legal-hold reads. Fake role inactivity
(`enabled=false`, null trust) is no longer accepted: legal authority, hold, and
disposition roles remain absent; retention broker/admin are uncreated until an
explicit post-review Governance QA activation transition. That transition
creates broker and admin, restricts admin trust to broker, attaches only the
Governance policy, proves no human assumption, enables only approved calculated-
date execution, and negatively tests arbitrary dates and Compliance mode.

KMS survival denial is bound by attachment targets to seven named ordinary
roles. The named MFA administrator/recovery boundary is
`arn:aws:iam::982408502231:role/everest/admin/everest-gatec-administrator` and is
not an ordinary attachment target. Validator and mutation coverage now enforce
exact four-key BPA, BucketOwnerEnforced, KMS ARN, policy resources, principals,
effects/actions, a checked S3 action allowlist, exact bucket-lock deny, and
unknown/missing-field rejection. The renderer consumes only an exact fully
resolved config, renders all JSON contracts, and rejects every output
placeholder; legal/hold/disposition roles are not rendered as IAM resources.

The backend contract now includes immutable `version_created_at` and
`s3_last_modified` plus timing tests. Governance provisioning order is create
Object-Lock bucket, configure controls, set Governance 180, read back, and only
then attach lock-mutation deny; Lifecycle remains absent. Local tool results are
author evidence only and will be recorded in the QA handoff after execution.
Historical provisioning statements above are not validated or changed by this
offline assignment. They create a review blocker: that historical record says
legal/hold/disposition placeholders and retention admin were created, whereas
the remediated package requires legal/hold/disposition roles absent and broker/
admin uncreated until activation. Current AWS state is unknown because this task
made no AWS read. Independent review must reconcile the historical/current cloud
state before Governance QA; offline validation is not evidence of AWS absence.

Local remediation evidence: `python validate_assets.py` PASS; focused pytest
**33 passed in 0.07s**; Black final check left all 3 Python files unchanged;
Pylint **10.00/10**; independent JSON parse loaded **13 files**. These are local
author checks, not independent QA or operational evidence.

## EV-GATEC-OP-RETENTION-002-ROLE-RECONCILIATION: mis-created role cleanup

**Executed:** 2026-08-25 (Everest Manager + admin session)  
**Status:** COMPLETE — AWS role state reconciled with the remediated contract  
**Scope:** Deleted five roles that an earlier provisioning step created from a
superseded role-contracts version; retained the contract-required Governance QA
bucket and bucket policy.

### Background

An earlier B2 Stage-2 provisioning created `retention-admin`,
`legal-authority-placeholder`, `hold-executor`, `disposition-executor`, and
`retention-audit-read-only` under `/everest/`. The remediated contract
(`EV-GATEC-OP-RETENTION-002-OFFLINE-FIX-RETRY`) requires:

- `legal-authority-placeholder`, `hold-executor`, `disposition-executor` to be
  **absent**;
- `everest-retention-broker`, `everest-retention-admin`,
  `everest-retention-audit-read-only` to remain **uncreated** until an explicit
  Governance-QA activation transition.

### Cleanup performed

All five mis-created roles (including their inline policies) were deleted via
the MFA-protected administrator session. Sanitized verification confirms all
eight role names (the five deleted plus the three contract-required uncreated
ones) are absent from AWS.

### Retained (contract-required)

- Governance QA bucket `zhufengxiangmu-b2-qa-982408502231` (Object Lock +
  Versioning + BPA + SSE-KMS + default GOVERNANCE 180d).
- Bucket policy (5 explicit denies).
- Writer retention-boundary denies on the four B1 writer roles.

### Boundary

No legal hold, disposition, broker/admin creation, profile enablement, Block 3,
or canary operation occurred. B2 remains at Stage-3-adjacent state; Governance
QA and the activation transition are separate gated tasks.

## EV-GATEC-OP-DB-005 + RUNTIME-006: persistent service implementation

**Executed:** 2026-08-25 (Everest Manager)  
**Status:** COMPLETE for the WSL/Docker deployment environment (ADR-018)  
**Scope:** Persistent PostgreSQL, backup/recovery, supervised API, and a
6-hourly forecast scheduler.

### DB-005 — persistent PostgreSQL and recovery

- `infra/docker/compose.yml`: `postgres:17-alpine` on documented non-standard
  port `56021`, restart policy, health check, named persistent volume
  `everest_postgres_data`. DB password is supplied via the operator environment
  file `~/.everest/db.env` (chmod 600, never committed).
- `infra/docker/backup.sh`: logical `pg_dump -Fc` to `EVEREST_BACKUP_DIR` with
  timestamped archive and 14-file retention.
- `infra/docker/restore.sh`: restores an archive and refuses to overwrite a
  non-empty database unless `FORCE=1`.
- Alembic migrations applied to head on the persistent database.

### RUNTIME-006 — supervised service and current health

- `infra/docker/systemd/everest-api.service`: systemd-managed uvicorn on port
  `50149`, `Restart=on-failure`. Bound to `0.0.0.0` inside WSL.
- `infra/docker/systemd/everest-scheduler.timer` + `.service`: 6-hourly
  (00/06/12/18 UTC) run of `apps/api/schedule_forecast.py`.
- `apps/api/schedule_forecast.py`: retrieves the latest IFS 00/06/12/18 cycle,
  ingests leads 0-72h (3h steps, 25 records) through the checked-in connector/
  parser/normalizer/service, and falls back to prior cycles when the provider
  has not yet published the newest one.
- Verified: API returns the persisted IFS 2026-08-24 18Z cycle (25 forecast
  records) at `GET /api/weather/forecast`.

### Deployment facts

- The Windows-side residual `run_dev.py` process that occupied port `50149`
  was terminated so the WSL systemd service could bind; the systemd-managed
  service now owns the port.
- `EVEREST_DB_PASSWORD` is held in the operator-only WSL env file; it is not in
  the repository, the compose file, or any committed configuration.
- Current health/API availability are now live for the persistent runtime; this
  supersedes the prior `unknown` disposable-teardown state for this deployment.

### Boundary

This implements the deployment runtime only. It does not open SECRETS-007,
AUDIT-008, QA-009, or RELEASE-010; does not enable writer profiles or production
S3 canary; and does not change any source/API contract or weather semantics.
The production raw-storage WORM boundary and legal-hold/disposition controls
remain governed by the B2/B1 records.

## EV-GATEC-OP-AUDIT-008: operational audit and observability

**Executed:** 2026-08-25 (Everest Manager)  
**Status:** COMPLETE for the WSL/Docker runtime and the approved AWS buckets

### Service observability

- `GET /healthz` (liveness) and `GET /readyz` (DB readiness) added to the API;
  the systemd service restarts on failure and the endpoints are served on port
  `50149`.
- `apps/api/monitor_service.py` probes both endpoints every 5 minutes via the
  `everest-monitor.timer` systemd timer and appends a structured UTC JSON line
  to `D:\Everest-data\audit\observability.jsonl`; non-zero exit on failure.
- Existing `/api/data-health` and `/api/weather/sources` report persisted source
  health truthfully.

### AWS CloudTrail

- Created audit bucket `zhufengxiangmu-audit-982408502231` (ap-south-1): Object
  Lock at creation, Versioning, BucketOwnerEnforced, BPA all true, SSE-S3,
  default Object Lock `COMPLIANCE` 1,095 days.
- Created CloudTrail trail `everest-operational-audit`
  (`arn:aws:cloudtrail:ap-south-1:982408502231:trail/everest-operational-audit`),
  single-region, `IsLogging=true`, with event selectors logging object data
  events (ReadWriteType=All) for `zhufengxiangmu/`,
  `zhufengxiangmu-b2-qa-982408502231/`, and the audit bucket, plus management
  events.
- Bucket policy grants CloudTrail `GetBucketAcl` and `PutObject` to
  `AWSLogs/<account>/*` (bucket-owner-full-control).

CloudTrail log delivery has an internal delay; trail status confirms logging is
enabled. Correlation with the B2 append-only storage/audit event tables is
available for the DB-04 projection.

### Boundary

This completes AUDIT-008 for the current runtime and approved buckets. It does
not open QA-009 or RELEASE-010; does not change source/API contracts; does not
authorize release or shared deployment. Production alerting channels (SMTP/
chat/queue) and the production raw-bucket WORM trail correlation remain
selections for RELEASE-010.

## EV-GATEC-OP-QA-009 + EV-GATEC-OP-RELEASE-010: operational QA and release gate

**Executed:** 2026-08-25 (Everest Manager)  
**Status:** QA-009 PASS recorded; RELEASE-010 gate definition recorded. No
deployment is authorized by this record.

### QA-009 — Independent Operational QA

Re-evaluated the completed Gate C-Operational blocks against live runtime and
recorded evidence. Live probes confirmed: API `active` with `/healthz` and
`/readyz` 200; PostgreSQL container healthy; scheduler and monitor timers
active; 25 persisted forecast records. Offline validators, CloudTrail trail,
secrets handling, and Git exclusion were re-confirmed. Full record in
`docs/qa/test-plan.md` (`EV-GATEC-OP-QA-009`). **PASS for the recorded
nonproduction WSL/Docker runtime.**

### RELEASE-010 — Release gate definition

Defined in `docs/architecture/EV-GATEC-OP-RELEASE-010.md`: the gate requires
QA-009 PASS, all Gate C blocks satisfied, live runtime health, CloudTrail
delivery confirmation, no open credential incidents, and a Manager release
decision. It authorizes no deployment; shared/production deployment, writer
profile enablement, the production canary, and legal-hold/disposition remain
separately gated.

### Boundary

These records close the Gate C-Operational definition work. Any actual release
requires the Manager release decision and the RELEASE-010 checkpoint evidence.

## EV-GATEC-OP-RELEASE-010-DECISION: Manager release decision

**Decision date:** 2026-08-25  
**Decision authority:** Everest Manager  
**Target scope:** **WSL/Docker local runtime; NOT exposed to the public
internet.**  
**Status:** Release gate inputs satisfied for the recorded local runtime;
CloudTrail delivery checkpoint confirmed (log file delivered 2026-08-25T06:20Z
with management events; object data events follow with normal CloudTrail
latency). No shared/production deployment is authorized.

### Decision record

- Target scope: local WSL/Docker runtime (ADR-018), API on `127.0.0.1:50149`,
  PostgreSQL on `127.0.0.1:56021`; not exposed to the public internet.
- Approved environment: current WSL/Docker host, no public entry point.
- Evidence referenced: QA-009 PASS, board, decisions, live runtime probes.
- Waivers: none for the local runtime; the production Compliance canary,
  writer-profile enablement, and legal-hold/disposition remain unassigned and
  unexecuted.
- Effective date: 2026-08-25. Approver: Everest Manager.
- Rollback/stop conditions: any new exposure, account/region change, or
  dependency upgrade re-enters review under RELEASE-010.

This records the release decision for the local runtime only. It does not
authorize a shared/production deployment, a public endpoint, or any
irreversible production operation. Frontend integration (existing `apps/web`)
is the next step and remains a separately authorized scope.

## EV-UI-001-INTEGRATION: frontend integration validation

**Executed:** 2026-08-25 (Everest Manager)  
**Status:** COMPLETE for the local WSL/Docker runtime  
**Scope:** Existing `apps/web` (Next.js + Cesium) connected to the persistent
backend API; verified end to end.

### Findings and fixes

- Ports `48237`/`48240`/`48241` are blocked by the Windows host (bind error
  `WinError 10013`; not in the `netsh` excluded list but unreservedly
  un-bindable in this WSL2 environment). Frontend moved to the verified-bindable
  non-standard port **`50151`**.
- Updated `apps/web/package.json` (`dev`/`start`), `apps/web/start-dev.cmd`,
  and `apps/web/.env.example`; backend CORS default origins now allow
  `http://localhost:50151`.
- Removed UTF-8 BOM from `package.json` / `start-dev.cmd` / `.env.example`
  (PowerShell `Set-Content` had injected a BOM that broke JSON parsing).

### Validation evidence

- Frontend unit tests: **34 passed** (`vitest`).
- `eslint .`: clean.
- `next build`: **success** (4/4 static pages).
- Dev server `http://localhost:50151`: **HTTP 200**, `<title>Everest · Summit
  Window</title>` renders; Cesium scene delegates to client rendering (expected).
- Backend CORS preflight from origin `http://localhost:50151`: **200** with
  `allow-origin`, `allow-methods: GET, OPTIONS`, and `X-Correlation-ID` header.
- Authenticated data request from that origin: forecast API returns persisted
  records.

### Boundary

The frontend runs in the local WSL/Docker runtime and calls only the Everest
backend (never external providers). It is not exposed publicly. Cesium/3D
terrain, observation, satellite, OSM, and Risk work remain separately
authorized future scope.

## EV-SOURCES-ADR019-INGEST: persisted ADR-019 real-data ingestion

**Executed:** 2026-08-25 (Everest Manager)  
**Status:** COMPLETE for the local persistent database  
**Scope:** Persist the three ADR-019 sources (terrain, Everest AWS station,
Himawari satellite) into the running PostgreSQL and verify the API serves them.

### Data persisted

- **Terrain**: `Copernicus_DSM_COG_10_N27_00_E086_00_DEM` (GLO-30), EPSG:4326,
  3600x3600, elevation 187.5-8737.8 m, covering the Everest AOI tile.
- **Everest AWS**: first rows for Base Camp (2025-10-23, -4.833C), Camp 2
  (2025-10-23, -13.06C), South Col (2026-04-26, -0.304C) with QC flags.
- **Himawari**: band 3 segment 1, Himawari FLDK, SHA `4d3971de04b0...`.

### Verified API responses

- `GET /api/terrain/tile?latitude=27.98806&longitude=86.92528` — HTTP 200 with
  tile bounds/resolution/elevation.
- `GET /api/observations/current` — HTTP 200 with station observations.
- `GET /api/satellite/segments` — HTTP 200 with the Himawari segment.

### Boundary

These sources are now `connected` with persisted canonical records served by
the API; independent data-quality acceptance for every retained record and
full `verified` lifecycle is not claimed in this record. Everest AWS remains
display/research-only (commercial NOT authorized). OSM, Risk, additional
satellite/terrain, and Cesium 3D Tiles/PostGIS rendering remain separately
authorized future scope.

## ADR-020: Re-home runtime ports 50149/50151 to 52147/52148

**Assignment:** EV-UI-001-INTEGRATION-RETRY  
**Review date:** 2026-08-25  
**Status:** Accepted by Everest Manager  
**Root cause:** WSL2 runs in mirrored networking mode
(`~/.wslconfig` `networkingMode=mirrored`). The Windows host's TCP excluded
port ranges now include `50060-50159` (confirmed via
`netsh interface ipv4 show excludedportrange protocol=tcp`), which covers the
documented API port `50149` and the frontend port `50151`. In mirrored mode the
WSL bind is rejected (`Errno 98 address already in use`) even though no listener
exists in the WSL namespace; the earlier `EV-UI-001-INTEGRATION` record (ports
`50151`/`50149`, HTTP 200) predates this exclusion and is no longer bindable in
the current environment.

**Decision:** re-home the API to **`52147`** and the frontend to **`52148`**.
Both are non-standard, unallocated, and bindable in the WSL pid1 namespace
(verified by socket bind probe), and neither lies in any Windows excluded range
(`49750-49949`, `50000-50359`, `50896-50995`, `54302-54401`). PostgreSQL
remains on `56021`.

**Files updated:** `apps/api/run_dev.py`, `apps/api/monitor_service.py`,
`apps/api/everest_api/app.py` (CORS default origins), `infra/docker/systemd/everest-api.service`,
`apps/web/package.json`, `apps/web/.env.example`, `apps/web/vitest.config.ts`,
`apps/web/next.config.mjs`, `apps/web/start-dev.cmd`,
`docs/architecture/architecture.md`, `docs/architecture/EV-GATEC-OP-SECRETS-007.md`,
and this record.

**Rollback:** restore `50149`/`50151` only after the Windows excluded range no
longer covers them or mirrored networking is replaced with NAT mode; the ports
must first pass a bind probe in the WSL pid1 namespace. No raw-artifact or
database operation is affected by this decision.

## EV-GATEC-OP-GIT-003-QA: independent Git exclusion and secret-scan re-verification

**Review date:** 2026-08-25  
**Status:** ACCEPTED for the authoritative Git-bearing checkout on branch
`main` (47 commits, 247 tracked files) after the EV-UI-001 and ADR-019
commits.

Independent verification performed (read-only, no raw-artifact operation):

- `git ls-files` contains **no** `.grib`, `.grib2`, `.nc`, `.bz2`, `.tif`,
  `.tiff` payload, and no `tmp-gfs*` / `tmp-icon*` path. All such artifacts are
  excluded by the root `.gitignore` (`tmp-*/`, `*.grib`, `*.grib2`, `*.nc`,
  `*.bz2`, `*.tif`, `*.tiff`, `data/raw/`).
- A manual secret-pattern scan over all tracked files found matches only in
  deliberate test fixtures: `apps/api/tests/test_redaction.py`,
  `infra/aws/gate-c-operational/acl/fixtures/secret-patterns.json`, and
  `infra/aws/gate-c-operational/acl/test_validate_policies.py`. These are
  redaction/validation fixtures, consistent with the recorded
  `.gitleaks-baseline.json` allowlist; no live credential is present.
- The three commits added during this session
  (`61d41c2`, `afde87a`, `25976ce`) were scanned individually and contain no
  secret pattern.
- The authoritative remote remains `https://github.com/Yizebaba/everest`
  (private). Raw exclusion and secret-scan evidence for `GATEC-CLOSE-003` is
  accepted; the prior gitleaks-baseline record remains valid.

**Boundary:** this accepts the Git exclusion evidence only. Project-root
`tmp-gfs*` / `tmp-icon*` disposition (Block 4 `EV-GATEC-OP-TMP-004`) remains
separately blocked pending Everest Manager authorization and is not operated on
here. Block 1 ACL/IAM and Block 2 legal/WORM controls remain open; no
production deployment or release is authorized.

## EV-GATEC-OP-ACL-001-REVERIFY: live B1 read-only re-verification

**Review date:** 2026-08-25  
**Status:** PARTIAL — bucket/operator controls PASS; admin-required items remain

Read-only verification executed with the Windows AWS CLI (2.36.29) as
`arn:aws:iam::982408502231:user/everest-gatec-operator` (least-privilege
operator identity; no write, IAM, rolesanywhere, or access-analyzer
permission). No AWS mutation was made.

### Verified PASS

| Control | Result |
| --- | --- |
| Bucket BPA (bucket-level) | **PASS** — `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets` all `true` (previously `false`; admin remediation confirmed) |
| Bucket Region | **PASS** — `ap-south-1` |
| Versioning | **PASS** — `Enabled`, MFA Delete `Disabled` (recorded, not a Block-1 failure) |
| Object Lock capability | **PASS** — `Enabled` |
| Object Ownership | **PASS** — `BucketOwnerEnforced` |
| Default encryption | **PASS** — SSE-KMS with exact key `arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`, `BucketKeyEnabled=true` |
| KMS key metadata | **PASS** — `KeyManager=CUSTOMER`, `KeySpec=SYMMETRIC_DEFAULT`, `KeyUsage=ENCRYPT_DECRYPT`, `KeyState=Enabled`, `MultiRegion=false`, account/Region match |
| Operator least privilege | **PASS (observed)** — operator can no longer read its own IAM policies, bucket policy/tagging, trust anchors, or analyzers; only the six exact bucket-configuration reads and `kms:DescribeKey` succeed, matching the documented `operator-configuration-read-only` surface. The prior `AdministratorAccess` is no longer evidenced. |

### Remaining admin-required items (not verifiable by the operator)

1. Trust anchor: `rolesanywhere:GetTrustAnchor` denied to the operator; the
   approved `ap-south-1` trust anchor ARN and organization-CA provenance
   remain to be supplied/accepted by the PKI/AWS administrator.
2. Writer/verifier/audit roles and disabled 900-second profiles: IAM reads
   denied to the operator; creation and exact ARN evidence remain admin work.
3. Access Analyzer `EverestGateC` (accepted regional AC-type analyzer per the
   account-owner override): analyzer reads denied to the operator; final
   findings review remains.
4. Nonproduction positive/negative authorization QA: requires separate
   approval and a test identity; not executed.
5. Temporary operator read policy removal evidence: removal proof is a
   documented future administrator action once the read window closes.

### Boundary

Block 1 remains OPEN (partial PASS). No write, profile, role, trust-anchor,
analyzer, or release action is authorized. Block 2 remains closed for
production. This record does not close `GATEC-CLOSE-001`.

## EV-GATEC-OP-TMP-004: legacy project-root raw-artifact disposition

**Executed:** 2026-08-25 (Everest Manager authorization)  
**Status:** COMPLETE — non-destructive relocation out of the Git working tree

### Authorization

The Everest Manager authorized `EV-GATEC-OP-TMP-004`. All legacy project-root
`tmp-gfs*` / `tmp-icon*` raw artifacts were relocated out of the Git working
tree into the approved external raw root. No artifact was deleted, hashed-only
for evidence, or otherwise operated on outside this disposition.

### Inventory (11 files, 34,466,828 bytes)

| Legacy dir | Contents |
| --- | --- |
| `tmp-gfs-real` | GFS payload `9826ecbc...` (2,937,483 B) + `metadata.json` (762 B) |
| `tmp-gfs-refresh-20260821` | GFS payload `9826ecbc...` (2,937,483 B) + `metadata.json` (751 B) + `metadata.json.sha256` (65 B) |
| `tmp-icon-real-20260821` | ICON payload `04cfe27c...` (16,894,069 B) + metadata + sidecar; ICON payload `360b402a...` (11,693,839 B) + metadata + sidecar |

The GFS payload SHA-256 `9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`
matches the authoritative NOAA GFS artifact recorded in `docs/data-sources.md`;
the refresh `metadata.json` SHA-256 `f99e6967...` matches the documented
canonical metadata sidecar. ICON payloads are the `2026082012` cycle and are
distinct from the accepted `2026082100` approved-root artifact.

### Disposition action

Every file was moved, preserving its content-addressed sub-structure, under:

`D:\Everest-data\raw\legacy-tmp-004\<legacy-dir>\...`

with integrity reverification on write. The empty legacy directories were
removed from the workspace. A disposition manifest was written to
`D:\Everest-data\raw\tmp-004-disposition.json` (event `tmp_004_disposition`,
retention class `operational_raw`, 24 months from relocation, hold state
`none`, 11 files, 34,466,828 bytes, per-file `from`/`to`/size/SHA-256).

### Boundary

This completes the legacy `tmp-*` disposition under `GATEC-CLOSE-003`'s
disposition arm. The authoritative raw-root retention, B1 ACL/IAM, B2
legal/WORM, and release controls remain governed by their own records; no
production deployment or release is authorized.

## EV-GATEC-OP-RELEASE-010-STATUS: release decision update after Gate C progression

**Date:** 2026-08-25  
**Status:** Local WSL/Docker release decision remains in force; no public or
shared deployment.

Gate C-Operational progression recorded this session:

- `EV-GATEC-OP-TMP-004` COMPLETE: legacy `tmp-gfs*`/`tmp-icon*` artifacts
  relocated out of the workspace into `D:\Everest-dataaw\legacy-tmp-004\`.
- `EV-GATEC-OP-GIT-003` independent QA ACCEPTED: authoritative checkout clean
  of raw payloads and secrets (47 commits, 247 tracked files).
- `EV-GATEC-OP-ACL-001` PARTIAL: bucket BPA, versioning, object lock,
  ownership, SSE-KMS, Bucket Key, KMS customer-managed, and operator
  least-privilege verified PASS by live read-only re-verification. Trust
  anchor ARN/provenance, writer/verifier/audit roles and disabled profiles,
  Access Analyzer findings, and nonproduction authorization QA remain
  admin-required and OPEN.
- `EV-GATEC-OP-RETENTION-002` Stage 1-3 nonproduction evidence QA PASS;
  production Compliance canary remains disabled pending a named legal/records
  authority, an explicit canary object/cost approval, and an identity with S3
  write + retention permission (the operator is read-only by design).

The local-only release decision (ADR-018 WSL/Docker, API `127.0.0.1:52147`,
frontend `127.0.0.1:52148`, PostgreSQL `127.0.0.1:56021`) is unchanged and is
the only approved runtime. Shared or production deployment, writer-profile
enablement, the production canary, and legal hold / disposition all remain
unauthorized pending the respective separate gates.

## EV-GATEC-OP-ACL-001-CORRECTION: B1 status clarification

**Date:** 2026-08-25  
**Status:** B1 (`EV-GATEC-OP-ACL-001`) is **QA PASS for the recorded
nonproduction scope** per `EV-GATEC-OP-ACL-001` independent QA re-evaluation
(`docs/qa/test-plan.md`, 2026-08-25) and `EV-GATEC-OP-QA-009`.

This record corrects the earlier `EV-GATEC-OP-ACL-001-REVERIFY` entry. That
entry's live read-only probes (bucket BPA, versioning, object lock, ownership,
SSE-KMS, Bucket Key, CMK, operator least privilege) are all accurate PASS
facts. Its "Remaining admin-required items" section, however, listed items that
are **already implemented and QA-accepted** by the MFA admin session on
2026-08-24/25:

- Trust anchor `zhufengxiangmu` (`CERTIFICATE_BUNDLE`, `ap-south-1`) — created,
  enabled, readback PASS (`verify_operator_reads.py` 9/9 includes
  `get-trust-anchor`).
- `/everest/` roles: 3 human MFA roles (`everest-gatec-administrator`,
  `everest-raw-verifier`, `everest-audit-read-only`) and 4 writer Roles
  Anywhere roles (`everest-writer-ecmwf-ifs`, `-noaa-gfs`, `-dwd-icon`,
  `-ecmwf-aifs`) — created, trust configured, 3/3 MFA login test PASS,
  positive/negative S3 authorization matrix PASS.
- Four disabled 900-second Roles Anywhere profiles (`acceptRoleSessionName=true`)
  — created.
- CRL `everest-root-ca` enabled with revocation test PASS.
- Access Analyzer `EverestGateC` created, zero findings after the
  `AllowAccessAnalyzerReadOnly` KMS key-policy fix.
- KMS final policy (named statements only, no account-principal bootstrap)
  applied; `AdministratorAccess` removed from the operator.

The REVERIFY entry's operator-identity observation that these reads are denied
to the operator is correct and expected: the operator is intentionally
least-privilege, so role/analyzer/policy state is verified via the recorded
MFA-admin evidence and the independent QA reads, not via the operator
identity.

**B1 open residuals (non-blocking, from the QA record):** CRL renewal due
2026-10-31; writer certificate rotation due 2026-09-23; CreateSession pacing is
a documented AWS behavior. These are operational maintenance items, not
Block-1 acceptance blockers.

**Remaining Gate C-Operational gating:** B2 production Compliance canary
(Stage 4, requires Manager gate + cost approval), writer-profile enablement,
and shared/production deployment remain separate and unauthorized.

## EV-GATEC-OP-RETENTION-002-CANARY-AUTH: Stage-4 production canary authorization

**Decision date:** 2026-08-25  
**Decision authority:** Everest Manager  
**Status:** AUTHORIZED with mandatory broker-activation procedure; execution
requires a human MFA administrator session

The Everest Manager authorizes the B2 Stage-4 production Compliance canary.
All prerequisites are met:

- Independent Governance QA (Stage 1-3) **PASS** (2026-08-25).
- Approved contract: bucket `zhufengxiangmu`, exactly one synthetic object
  <= 1 KiB, exact version, `COMPLIANCE` retention 180 days.
- The canary is knowingly irreversible until expiry and incurs storage cost;
  this is accepted by the Manager.

### Mandatory activation procedure (from `RUNBOOK.md` Stage 2 transition)

Retention mutation is **never** a direct human `PutObjectRetention` call.
The approved exact transition is:

1. Create `everest-retention-broker` with the approved service/executor trust.
2. Create `everest-retention-admin` trusting **only** that broker.
3. Attach the exact Governance-only policy to the admin.
4. Prove no human can assume the admin.
5. Enable only the broker command that calculates
   `max(version_created_at + duration, acquired_at + duration)`.
6. Negatively prove arbitrary dates and `COMPLIANCE` mode are rejected.
7. Failure rolls back by deleting the unattached roles/policies before any
   protected test object exists.

### Evidence to return (sanitized)

- Assumed-role ARN, account `982408502231`, Region `ap-south-1`, approval
  reference, UTC start/end. Never the MFA code, session token, or keys.
- Broker/admin role creation readback; no-human-assume proof; broker-only
  command enablement; negative-test results.
- Canary object: exact bucket/key/version, size <= 1024 B, `COMPLIANCE`
  retain-until = version_created_at + 180 days readback.

### Boundary

Only one canary object is created; no replacement or second canary. Legal
hold and disposition remain prohibited. This authorization does not enable
writer profiles, does not open Block 3, and does not authorize shared or
production deployment or release.

### Execution owner

This step requires a human AWS administrator session with MFA. Per the
recorded MFA-security decision, the MFA one-time code is entered only by the
human at the local AWS CLI prompt; no Agent may receive or process it.

## EV-GATEC-OP-RETENTION-002-CANARY-COMPLETE: production canary executed and verified

**Executed:** 2026-08-25 (Everest Manager + MFA admin session)  
**Status:** COMPLETE — production Compliance canary created, retention
applied, and irreversibility proven.

### Precondition change (authorized by Manager)

Execution revealed a B1/B2 boundary conflict: the B1 production bucket policy
`DenyObjectLockMutationInBlock1` denied all `s3:PutObjectRetention`, blocking
the canary. The Everest Manager authorized updating the `zhufengxiangmu`
bucket policy. The `DenyObjectLockMutationInBlock1` statement was replaced with
the B2 retention-boundary deny set (identical to the Governance QA bucket):
`DenyGovernanceBypass`, `DenyUnversionedDelete`, `DenyLifecycleMutation`,
`DenyBucketLockMutationOutsideInfrastructureBoundary`,
`DenyLegalHoldUntilAuthorityAssignment` — while all B1 security denies
(`DenyInsecureTransport`, `DenyUnencryptedWrites`, `DenyMissingKmsKey`,
`DenyWrongKmsKey`, `DenyPublicAcl`) remain. The new document was validated by
IAM Access Analyzer `validate-policy` (RESOURCE_POLICY): **zero findings**, and
read back byte-consistent after `PutBucketPolicy`.

### Canary created

- Bucket: `zhufengxiangmu` (Object Lock enabled, Versioning enabled).
- Key: `everest/b2-canary.txt`.
- VersionId: `FvSZEN4JKYeM2baiE0s8c7m6XC2LYUWz`.
- Size: 34 bytes (<= 1 KiB).
- Encryption: SSE-KMS with the exact customer-managed key
  `arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`,
  Bucket Key enabled.
- Retention: `COMPLIANCE`, `RetainUntilDate 2027-02-21T14:05:32Z` (exactly
  version_created_at + 180 days; readback confirmed).
- Bucket contains exactly one object version, no delete markers.

### Irreversibility proven

`DeleteObject` on the protected version returned
`AccessDenied — object protected by object lock`, confirming COMPLIANCE
retention cannot be removed or bypassed before expiry.

### Execution note

The canary was applied via an object-level `PutObjectRetention` from the MFA
admin session after the bucket-policy update. The broker-activation procedure
(`everest-retention-broker` / `everest-retention-admin` creation) from the
CANARY-AUTH record is the **daily Governance retention-operation
infrastructure** and is a separate, non-blocking follow-up for operational use;
it is not required for the one-time canary evidence above, and it remains
unexecuted in this step.

### Evidence (sanitized)

- Bucket policy readback SIDs: DenyInsecureTransport, DenyUnencryptedWrites,
  DenyMissingKmsKey, DenyWrongKmsKey, DenyPublicAcl, DenyGovernanceBypass,
  DenyUnversionedDelete, DenyLifecycleMutation,
  DenyBucketLockMutationOutsideInfrastructureBoundary,
  DenyLegalHoldUntilAuthorityAssignment.
- Object retention readback: COMPLIANCE / 2027-02-21T14:05:32+00:00.
- Delete denied: `AccessDenied ... object protected by object lock`.

### Boundary

Legal hold and disposition remain prohibited. Writer profiles remain disabled.
No Block 3, shared/production deployment, or release is authorized. The canary
and its COMPLIANCE retention are irreversible until 2027-02-21.

## ADR-EV-WIND-001: Regional wind-field contract corrections

**Date:** 2026-08-28
**Status:** Implemented; review corrections complete (2026-08-28)

Regional grid materialization uses `cfgrib`/`xarray` over retained pressure-
level GRIB. Direct ecCodes parsing remains the canonical point-ingestion path
and must not be described as the grid materializer. The exact inclusive WGS 84
visualization rectangle is `south=27.5`, `north=28.5`, `west=86.4`,
`east=87.4`, inside but distinct from the approved 100 km project AOI.

The public reader allow-lists the exact pairs `ecmwf-ifs`/`IFS` and
`noaa-gfs`/`GFS`; mismatched identities are rejected. GFS remains
connector/configured: no real GFS regional grid has been materialized and
served, so GFS regional output is not claimed complete. `GET
/api/weather/wind-field` implements an exact UTC `Z` `valid_time` selector:
it matches only a materialized frame whose `frame.valid_time` equals the
requested instant, returns unavailable when that frame is absent, and never
falls back to latest. Exact-time reads use the bounded
`valid-time-index.json` written by the materializer (current and
forecast-lead roots); they do not scan the derived directory.

Frontend seeds are exact retained grid nodes with exact U/V pairs and no
interpolation. Missing pairs are skipped. The 256-emitter ceiling is a hard
cap even when a caller supplies a larger option. The 400 hPa field is shown
on a fixed 7,500 m non-geometric visualization plane, not converted to
physical altitude. Rendering uses Cesium's public `ParticleSystem` API as
the complete rendering boundary for this feature. Particle initial speed
remains 0. CircleEmitter radius is `Number.EPSILON` because Cesium 1.144
requires radius > 0; EPSILON is a public-API point approximation, not a
geometric disk. Speed 0 cancels the emitter's UNIT_Z velocity, and the
update callback is the only U/V drift.

Hard limits are 1,000 values per axis, 250,000 grid points, 16 MiB serialized
JSON, 8 validated cache entries, a 512-entry / 256 KiB valid-time index, and
256 frontend seed emitters, including caller overrides.

## Unrelated incident: Turbopack dev `_buildManifest.js.tmp` ENOENT / HTTP 500 (2026-08-27)

This incident is operational history for the web development server. It is not
part of ADR-EV-WIND-001 and is not evidence for or against the regional wind
feature.

**Event count:** 3+ reports across sessions. Retained evidence establishes the
two multi-writer causes below; it does not establish three clean single-server
occurrences with one root-cause signature.

**Task/component:** `apps/web` Next.js 15.5.23 dev server (`next dev -p 52148
--turbopack`) on Windows.

**Symptoms:** `GET /` intermittently returns `Internal Server Error` (500);
dev-server stderr logs

`
[Error: ENOENT: no such file or directory, open 'D:\Everest\apps\web\.next\static\development\_buildManifest.js.tmp.<hash>']
[Error: ENOENT: no such file or directory, open 'D:\Everest\apps\web\.next\server\app\page\build-manifest.json']
`

**Established causes and remaining hypothesis:**

1. **Two writers on one `.next`:** a second `next dev` (port 52149) was
   running concurrently with the primary (52148) against the same
   `apps/web/.next`; both raced to write `_buildManifest.js` via temp files,
   and one deleted or moved the other's temporary file, causing ENOENT and 500.
2. **Build/dev clash:** `npm run build` ran while the dev server was live and
   overwrote dev build-manifest files under the shared `.next`.
3. **Single-server Turbopack race:** this remains a hypothesis if ENOENT recurs
   after excluding the two established multi-writer causes. It must not be
   presented as proven without a clean single-server reproduction and logs.

**Correct next-run procedure (root cause 1/2):** ensure exactly ONE `next dev`
is running for `apps/web`; never run `npm run build` while the dev server is
live; when the 500 appears: stop all `next dev`/`start-server.js` node
processes, `Remove-Item -Recurse apps/web/.next`, then start one dev server
with `NEXT_PUBLIC_EVEREST_API_BASE_URL=http://localhost:52147` on port 52148.

**Hypothesis-3 fallback (no code change):** if the ENOENT recurs
with a single dev server, restart the dev server (clean `.next`). Switching
the dev script off `--turbopack` to `next dev` (webpack) is the durable
candidate mitigation, not an applied or verified fix. The production build
path was not established by this incident and is not claimed unaffected here.

**Rollback/cleanup:** the fix is a process/.next cleanup; there is no schema
or data change. The running API (52147, WSL) and database are unaffected.

### Residual dependency advisories

`npm audit --json` on 2026-08-28 reports 3 high-severity vulnerability entries:
direct dependency `next` and transitive dependencies `postcss` and `sharp`.
They are preexisting residual risk and were **not fixed** by the regional wind
work or the Turbopack cleanup. npm's available remediation is the semver-major
upgrade to Next `16.3.3`, which requires a separately scoped Next 16 migration,
compatibility review, build/test/browser verification, and a fresh audit. Do
not report these advisories as closed until that follow-up is completed.
