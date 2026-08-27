# Regional Wind Grid and 3D Field Rendering

**Status:** Authorized; review corrections complete (2026-08-28).
**Owners:** meteorology (backend grid extraction) + gis-3d/frontend (3D
particle rendering).
**Dependencies:** `services/weather/wind_field.py`,
`services/weather/aoi.py`, `apps/api/everest_api/weather/wind_field.py`,
`apps/web/src/cesium/wind/`, `apps/web/src/cesium/EverestScene.tsx`.

## Problem

The map weather layer currently renders only discrete point markers at single
provider cells (camp/point forecasts). The Everest regional meteorological
field is not shown. Single provider cells must not be the only visual form of
the map weather layer.

## Requirement (regional grid, not points)

1. **Backend extraction** (`services/weather`): IFS and GFS regional frame
   materialization MUST open retained GRIB through `cfgrib`/`xarray`, select the
   pressure-level U/V variables, and materialize a complete 2-D grid array over
   the regional AOI. Direct ecCodes parsing remains part of canonical point
   ingestion; it is not the regional grid-materialization path. The frame
   includes the full `u` (eastward wind) and `v` (northward wind) matrices.

2. **Regional grid AOI** (authoritative, inside the approved 100 km AOI of
   `docs/everest-aoi.md`):

   | Bound | Value |
   | --- | --- |
   | `min_lat` / `south` | 27.5 |
   | `max_lat` / `north` | 28.5 |
   | `min_lon` / `west` | 86.4 |
   | `max_lon` / `east` | 87.4 |

   This exact inclusive WGS 84 rectangle is defined once as
   `REGIONAL_GRID_AOI` in `services/weather/aoi.py` and reused by both the GFS
   and ECMWF IFS materialization paths. It is a tighter visualization subset
   within the project's approved 100 km geodesic-radius AOI; it is not a
   replacement definition for that project AOI.

3. **Single-point use rule**: EBC / C1 / C2 / C3 / C4 / Summit coordinates are
   sampling points for the floating UI panels only. They must never be the
   unique display of the map weather layer.

4. **Frontend 3D rendering** (`apps/web`): the backend regional grid response
   drives a 3-D particle wind field (reference: RaymanNg `3D-Wind-Field`,
   pinned at `ddbbca160c14b5fe081fdd5c2e3dcd05718dba66`) rendered over the
   Cesium Everest terrain. The single-point circle layer is removed as the
   map weather layer.

## Data flow (unchanged constraints)

`external source -> connector -> raw -> parser -> normalizer -> QC ->
canonical model -> DB/derived storage -> service -> REST -> frontend`.

- The frontend NEVER calls a provider.
- No invented geometry, vectors, or camp coordinates.
- The canonical weather schema field meanings are unchanged
  (`docs/weather-spec.md`).
- The A-F / ADR-015 acceptance surface is unchanged.

## Backend changes

### GFS (services/weather/gfs + apps/api provider job)

- The configured GFS provider job requests the official `pgrb2.0p25` 400 hPa
  U/V fields. The intended regional path opens the retained GRIB through
  `cfgrib`/`xarray`, subsets to `REGIONAL_GRID_AOI`, and writes a
  `WindFieldFrame` through `build_wind_field_frame` and
  `materialize_wind_field_frame`.
- The existing nearest-cell single-point extraction is retained ONLY for the
  canonical point/panel records; the grid frame is the map layer's data source.
- Status: **connector/configured only**. The public frame reader accepts the
  exact `noaa-gfs`/`GFS` identity, but no real GFS regional grid frame has been
  materialized and served through this path. GFS regional output therefore
  remains unverified and must not be described as real-data complete.

### ECMWF (services/weather/ecmwf + apps/api schedule)

- The existing native-grid 400 hPa IFS U/V materialization
  (`_materialize_ifs_wind_field`) is kept; its envelope is switched to
  `REGIONAL_GRID_AOI` so future materializations use the regional box. The
  served frame at `/api/weather/wind-field` continues to be read without
  provider or GRIB access.

### API

`GET /api/weather/wind-field` serves an integrity-checked `WindFieldFrame`
(`u`/`v` full matrices over `latitude`/`longitude`) and returns an explicit
`unavailable` response when no acceptable frame exists. Without a query, it
selects the frame referenced by the root `latest.json` pointer.

The reviewed `valid_time` contract is an **exact selector**, not a nearest-time
search: accept only an explicit UTC RFC 3339 `Z` value; resolve only the frame
whose `frame.valid_time` equals it; and return `unavailable` if that exact frame
is absent. It must never fall back to the latest frame. The GET handler and
reader implement this selector and allow-list exactly `ecmwf-ifs`/`IFS` and
`noaa-gfs`/`GFS`; arbitrary or mismatched identities remain rejected.

Materialization maintains a bounded `valid-time-index.json` that maps each
exact UTC `valid_time` to its content-addressed frame and source/model/cycle
identity. The complete index payload is validated and atomically replaced;
readers never consume a partially written index. Exact-time reads use this
index (including forecast-lead storage), validate its selected digest and frame
identity, and perform no directory scan or latest-frame fallback.

### Storage and API hard limits

The materializer and reader reject frames that exceed any of these limits:

| Resource | Hard limit |
| --- | ---: |
| Latitude axis | 1,000 values |
| Longitude axis | 1,000 values |
| Grid points (`latitude × longitude`) | 250,000 |
| Serialized frame | 16 MiB |
| In-process validated-frame cache | 8 entries |

The materializer writes content-addressed JSON outside both the repository and
raw root. The API reads bounded regular non-symlink files and verifies the
SHA-256 pointer target before returning a frame.

## Frontend changes

### RegionalWindField layer (`apps/web/src/cesium/wind/`)

- The module uses Cesium's public `ParticleSystem` and `Transforms` APIs from a
  validated `WindFieldFrame`; Cesium's public `ParticleSystem` is the complete
  rendering boundary for this feature. The current implementation creates one
  public `ParticleSystem` per retained seed and uses its public update callback
  to apply displacement. It does not use a custom shader or GPU-compute path.
- Seeds MUST be exact retained grid nodes selected by a deterministic stride.
  Each seed uses the U/V pair at that exact flattened node. Seed placement and
  vector selection perform no bilinear interpolation and synthesize no
  midpoint values. Nodes with a missing U or V value are skipped.
- The consumer hard cap is 256 seed emitters. Defaults are emission rate 2
  particles/second per emitter, particle life 1.5 seconds, one initial burst of
  2-4 particles, and a 4 px sprite. A larger caller-provided seed cap is not
  permitted by this design contract.
- Rendering uses a single velocity source: Cesium's initial particle speed is
  zero. CircleEmitter radius is `Number.EPSILON` because Cesium 1.144 requires
  radius > 0; EPSILON is a public-API point approximation, not a geometric
  disk. Speed 0 cancels the emitter's UNIT_Z velocity, and the update callback
  applies only the exact backend eastward/northward U/V displacement. Setup is
  transactional: a partial primitive-add failure removes all systems already
  added and restores the prior `requestRenderMode` value.
- The 400 hPa field is displayed on a clearly non-geometric, fixed 7,500 m
  visualization plane. Pressure level is not geometric altitude, so the plane
  must not be labeled or interpreted as the physical height of the 400 hPa
  surface, terrain clearance, or a route/camp forecast altitude.
- Rendering is enabled only while a live frame is present. When a frame is
  unavailable, the existing lightweight point-particle fallback is retained
  (Everest OS constraint: only Cesium's public `ParticleSystem` path is used; a
  torn-down Scene is never dereferenced).

### EverestScene

- The map weather layer is the regional grid particle field from
  `windFieldFrame`.
- The per-record point markers and per-record wind barbs (the "single-point
  circle layer") are removed from the map weather layer.
- Camp / route / summit markers (EV-OSM-002 overlay) stay: they are the UI
  panel sampling anchors.

## Acceptance

- A retained IFS `WindFieldFrame` with complete U/V matrices is served by the
  backend and rendered with Cesium public `ParticleSystem` objects over the
  Everest terrain. The 7,500 m plane is explicitly non-geometric.
- Exact-node seed tests prove that the current public `ParticleSystem`
  implementation uses retained backend nodes without cell-center or bilinear
  interpolation.
- The 256-emitter ceiling is enforced as a hard cap even when a caller supplies
  a larger option.
- GFS remains connector/configured despite reader support for the exact
  `noaa-gfs`/`GFS` identity; a real regional frame has not been materialized and
  served, so real GFS regional output remains unverified.
- `valid_time` tests prove exact UTC selection through the atomically replaced
  bounded index and prove that a missing exact frame does not fall back to the
  latest frame.
- No map weather layer is built from a single camp point.
- EBC / C1 / C2 / C3 / C4 / Summit remain available as UI panel sampling
  points.
- `typecheck`, `lint`, and unit tests pass on both `apps/web` and the Python
  services.
- The pre-existing npm audit findings remain residual risk: three high-severity
  advisories affecting `next`, `postcss`, and `sharp`. They are not closed by
  this work and require a separately scoped Next.js migration and revalidation.
