# Everest Terrain Specification (EV-TERRAIN-001)

**Status:** GLO-30 connector `connected` (real-data retrieval, parsing, and QC
passed); NOT `verified` — persistence (PostGIS/object storage), API, tests
beyond unit, docs, and review remain.

## Scope

Terrain/elevation foundation for the Everest digital twin: Copernicus DEM
GLO-30 (30 m) as the baseline DSM, serving the 3D Cesium scene (EV-UI-001) and
future terrain analyses. AOI-limited to the Everest area defined in
`docs/everest-aoi.md`; no global downloads.

## Source (verified against official documentation, 2026-08-24)

| Fact | Value | Evidence |
| --- | --- | --- |
| Provider | ESA Copernicus / DLR TanDEM-X + Airbus WorldDEM | official docs |
| Access | AWS Open Data `arn:aws:s3:::copernicus-dem-30m` (eu-central-1), anonymous | registry.opendata.aws/copernicus-dem |
| Format | Cloud-Optimized GeoTIFF (COG), float32, 1°×1° tiles | readme + product handbook |
| Resolution | GLO-30 = 1.0 arcsec (~30 m) | product handbook |
| Datum | Vertical EGM2008; horizontal WGS84-G1150 (EPSG:4326) | product handbook |
| Coverage | Global land; Everest AOI unrestricted | registry |
| Epoch | Static (TanDEM-X 2011–2015); 2021 AWS release | registry |
| License | Free worldwide; attribution "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"; DOI 10.5270/ESA-c5d3d65 | CDSE |
| Commercial | Free license for general public; exact commercial clause text PENDING | CDSE |
| Auth | None for AWS Open Data copy | registry |

## Real-data evidence (2026-08-24)

- Tile: `Copernicus_DSM_COG_10_N27_00_E086_00_DEM` (covers 86°–87°E, 27°–28°N;
  contains summit `27.9881, 86.9250`).
- Downloaded `D:\Everest-data\raw\terrain\Copernicus_DSM_COG_10_N27_00_E086_00_DEM.tif`
  (43,039,634 bytes; SHA-256
  `4dfc87a0dec44a8a037164ddade45dd24bb53187176b5a14175c265bd6d20e76`).
- Parser: EPSG:4326, 3600×3600, ~30 m; elevation min 187.5 m, max 8737.8 m,
  mean 2570.5 m; 12,960,000 valid pixels, 0 nodata.
- QC: **PASS** (no flags).
- Summit 5×5 window: 8648–8735 m (Everest massif ridge).

## Implementation

`services/terrain/` (gis-3d owned):

- `connector.py` — tile identity, official URL, download (urllib, chunked),
  SHA-256.
- `parser.py` — rasterio COG parse → metadata + elevation array.
- `qc.py` — CRS/size/nodata/finite/elevation-range checks; flags, never deletes.
- `real_retrieval.py` — CLI: `python -m terrain.real_retrieval --raw-root <root>`.
- `tests/test_terrain.py` — 4 tests (tile naming, parse+QC pass, flag cases).

## Remaining (next)

1. ~~Normalizer → canonical terrain model + PostGIS raster / object storage~~ —
   **DONE (code)**: `terrain_tile` canonical table (migration `20260824_0007`)
   + `GET /api/terrain/tile?lat&lon`; integration test PASS on a disposable
   PostgreSQL (real tile ingested, point query returns max-elevation > 8000 m).
   PostGIS raster point-sampling remains optional for exact elevation reads.
2. Dependency/registration approval for rasterio (installed 1.5.1) per
   AGENTS.md.
3. Independent review and QA.
4. Related: Himawari (EV-SAT-001) and Everest AWS (EV-AWS-STATION-001)
   connectors — both also reached the same canonical+API+integration state
   (see `docs/meteorology/weather-spec.md`).

## Real-data integration evidence (disposable PostgreSQL, 2026-08-24)

Ran in WSL (PostgreSQL 15.19) against `everest_test`:

- Alembic upgrade head → all 7 revisions incl. `20260824_0007`; downgrade
  `0007→0006` drops the three source tables; re-upgrade restores them (verified
  `3` tables).
- Ingested the real GLO-30 Everest tile, Everest AWS Base Camp row, and
  Himawari band-3 segment; then queried via FastAPI TestClient:
  `/api/terrain/tile` → tile returned (max elevation > 8000 m),
  `/api/observations/current` → Base Camp present,
  `/api/satellite/segments?band=3` → FLDK segment present. **3/3 PASS**.
- Test: `apps/api/tests/test_sources_integration.py` (requires
  `EVEREST_TEST_DATABASE_URL`; skips otherwise).

