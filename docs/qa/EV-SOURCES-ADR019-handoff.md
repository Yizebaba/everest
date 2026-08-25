# EV-SOURCES-ADR019 — QA Handoff Evidence Package

**Prepared:** 2026-08-24 (Everest Manager session)  
**For:** Independent QA  
**Lines:** EV-TERRAIN-001 (GLO-30), EV-AWS-STATION-001, EV-SAT-001 (Himawari) — authorized by ADR-019  
**Status of source work:** `connected` (real-data retrieval/parse/QC/canonical/API + integration tests PASS; independent code review resolved). NOT `verified` — awaiting independent QA verdict.

Sanitized: no secrets, credentials, or private material. Raw data files are
retained under `D:\Everest-data\raw\` (outside Git, per AGENTS.md).

## 1. Scope and constraints

Three external sources integrated through the canonical Everest chain
(`external source -> connector -> raw data -> parser -> normalizer -> QC ->
canonical model -> PostgreSQL -> service -> REST/WS`). Frontend never calls
external providers. Data acquisition stays within the Everest AOI.

## 2. Source facts (verified against official documentation, 2026-08-24)

| Source | Official access | Auth | License | Status |
| --- | --- | --- | --- | --- |
| Copernicus DEM GLO-30 | AWS Open Data `copernicus-dem-30m` (eu-central-1, anonymous) | none | free + attribution (DOI 10.5270/ESA-c5d3d65) | `connected` |
| Everest AWS | AppState Everest Weather Portal `scidata.appstate.edu/everest/` (CSV feed; GitHub mirror approved by ADR-019 amendment as the portal's public feed) | none | no license stated; display/research only, commercial NOT authorized | `connected` |
| Himawari-8/9 | NOAA AWS S3 `noaa-himawari9` (anonymous) | none | free distribution with attribution (NOAA); HimawariCloud NMHS-only (not usable) | `connected` |

PENDING (not claimed verified): commercial-use clause text for GLO-30 beyond
free license; exact quota numbers; Everest-AWS provider-backed endpoint;
Himawari full field-level band/geometry decode (JMA format guide is a PDF not
machine-readable this session).

## 3. Code / artifacts

| Area | Path |
| --- | --- |
| Terrain | `services/terrain/` (connector, parser, qc, real_retrieval, tests) |
| Observations | `services/weather/everest_aws/` (connector, parser, qc, real_retrieval, tests) |
| Satellite | `services/satellite/himawari/` (connector, parser, qc, real_retrieval, tests) |
| Canonical models/normalizers | `apps/api/everest_api/sources/` |
| Migration | `apps/api/alembic/versions/20260824_0007_source_tables.py` |
| API routes | `apps/api/everest_api/app.py` — `/api/terrain/tile`, `/api/observations/current`, `/api/satellite/segments` |
| Tests | `apps/api/tests/test_sources_normalizers.py`, `apps/api/tests/test_sources_integration.py` |

## 4. Test evidence

### Unit tests (17 total, all pass)

- terrain (4): tile naming, parse+QC pass, wrong-CRS/extreme flags.
- everest_aws (5): feed URL, invalid station, NPT->UTC parse, Camp-2 layout,
  precipitation-anomaly QC flag.
- himawari (5): R-code discovery (mocked listing), header identity,
  QC pass, bad satellite/area flags, invalid band.
- sources normalizers (3): terrain/observation/satellite normalization.

### Integration tests (3/3 PASS, disposable PostgreSQL 15.19 in WSL)

- Alembic `upgrade head` -> 0007; downgrade `0007->0006` drops the 3 tables;
  re-upgrade restores them.
- Real data ingested (GLO-30 Everest tile, Everest AWS Base Camp row, Himawari
  band-3 segment) then queried via FastAPI TestClient:
  - `/api/terrain/tile?lat=27.9881&lon=86.9250` -> tile (max elevation > 8000 m)
  - `/api/observations/current` -> Base Camp present
  - `/api/satellite/segments?band=3` -> FLDK segment present
- No-leak assertions: `object_reference` and `sha256` are NOT exposed by the
  terrain/satellite routes.
- Test uses the real parsers to compute values (not hardcoded) and skips when
  raw files are absent. Requires `EVEREST_TEST_DATABASE_URL`.

## 5. Independent code review outcome

Verdict `FAIL-with-issues` -> all High/Medium/Low resolved:

- HIGH: Everest AWS unofficial-mirror channel -> ADR-019 amendment approving it
  as the portal's public feed (same terms); `/api/satellite/segments` raw-path
  leak -> removed + no-leak assertions; Himawari placeholder sha256 -> real
  SHA-256 computed.
- MEDIUM: ingestion path wiring; registry registration (seed pending);
  observations SQL dedup (`DISTINCT ON`); integration test uses real parsers;
  relative imports -> absolute; redaction consistency.
- LOW: black 80-col (24 files clean); unused imports removed; network test
  mocked; atomic `.part` downloads; AWS parser bounds guard; QC time min/max;
  terrain `elevation:null` removed; CLI exception handling; docs encoding
  typos fixed.

Remaining documented follow-ups (non-blocking for QA of what is built):
Himawari field-level band/geometry decode and calibration requires the JMA
format guide; `data_source_registry` seed rows for the three sources.

## 6. QA verification guidance (suggested)

1. `python -m black --line-length 80 --check` on the listed paths.
2. Unit tests: run the 4 test modules above (no DB needed).
3. With a disposable PostgreSQL and `EVEREST_TEST_DATABASE_URL` +
   `EVEREST_RAW_ROOT`, run `apps/api/tests/test_sources_integration.py`
   (3 tests) and `alembic upgrade/downgrade` for revision `20260824_0007`.
4. Call the three new routes and assert no `object_reference`/`sha256` in
   responses, correct 422 on invalid inputs (band out of 1..16; coordinates
   out of range).
5. Confirm status claims remain `connected`, never `verified`, per ADR-019.

Primary references: `docs/management/decisions.md` (ADR-019),
`docs/gis/terrain-spec.md`, `docs/meteorology/weather-spec.md`.
