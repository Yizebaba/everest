# EV-DATA-001 Phase-F Final Evidence Report

**Assignment:** `EV-DATA-001-ADR015-REPORT-CORRECTION`  
**Evidence cutoff:** 2026-08-22 authoritative handoffs and current `AGENTS.md`  
**Report date:** 2026-08-22  
**Scope:** Documentation-only synthesis of the authoritative current handoffs.
No external source was called, no raw artifact was read or changed, no code or
test was run, no database or API was started, and no lifecycle, health, board,
or frontend state was changed by this assignment.

## Executive Result

The four approved forecast sources have the following actual outcomes:

| Source | Evidence-backed outcome | Current lifecycle interpretation | Current health/API |
| --- | --- | --- | --- |
| ECMWF IFS | Official retrieval, five-message combined parse, normalization/QC, two-artifact PostgreSQL persistence, and one-record forecast API query succeeded in a disposable environment. Phase C QA accepted the source. | Historical disposable `verified`; not a production-service claim. | `unknown` after teardown. |
| NOAA GFS | Official indexed range retrieval, four-message parse, normalization/QC, checked-in adapter, PostgreSQL persistence, and one-record forecast API query succeeded in a disposable environment. Phase D QA accepted the source. | Historical disposable `verified`; not a production-service claim. | `unknown` after teardown. |
| DWD ICON | Official six-object retrieval, six-message parse, normalization/QC, approved-root retention, full PostgreSQL/API path, and post-review QA succeeded. Gate C-Core is accepted. | Historical disposable `verified`; not a production-service claim. | `unknown` after teardown. |
| ECMWF AIFS | Official selected-range retrieval, five-message parse, normalization/QC, immutable retention, PostgreSQL persistence, audit, and forecast API query succeeded in a disposable environment. Authoritative hardened evidence is `full66`, `AIFS4`, and `met37`, with `raw=1`, `record=1`, `audit=1`, HTTP `200`, and `model=AIFS`. AIFS source/core is PASS. | Historical disposable `verified`/`healthy` after canonical commit; the documented current registry remains `connected`, not a current `verified` claim. | `unknown` after teardown. |

All four forecast sources pass the authorized A-F source/core chain as
historical disposable evidence. The exact ADR-015 display criterion is a
different gate: each of the five specified backend routes must have returned
real canonical data. The retained inventory fully evidences that HTTP path only
for `GET /api/weather/forecast`; therefore the exact ADR-015 display criterion
is **not fully evidenced**. QA completed and the Everest Manager accepted this
as the ADR-016 historical evidence limitation. This is an evidence-gap finding,
not a finding that the other route implementations fail, and it does not reopen
the confirmed A-F stop gate.

This report does **not** claim current source health, a live API, UI display,
production readiness, or Gate C-Operational closure. ADR-015 requires no
Next.js, Cesium, browser, or other UI, and no UI was implemented. Current health
and availability remain `unknown` after teardown.

**Report status:** complete for the confirmed A-F stop. **AIFS source/core QA
status:** PASS. **ADR-015 five-route display evidence:** EVIDENCED HISTORICALLY
(disposable) — all five routes returned HTTP `200` with real canonical records
in the 2026-08-28 validation run; see the ADR-015 Evidence Update below. ADR-016
recorded the prior four-route limitation; ADR-021 closed it with disposable
evidence.

## Source Evidence

### ECMWF IFS

**Provider and product.** ECMWF Open Data, IFS 0.25-degree operational forecast,
GRIB2. The documented run cadence is 00, 06, 12, and 18 UTC.

**Exact official URLs:**

- 0-hour GRIB2:
  `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.grib2`
- 0-hour index:
  `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.index`
- 3-hour GRIB2:
  `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-3h-oper-fc.grib2`
- 3-hour index:
  `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-3h-oper-fc.index`

**Size and integrity evidence:**

| Artifact | Full official object | Retained selected bytes | SHA-256 |
| --- | ---: | ---: | --- |
| Initial 0-hour four-message sample | `137,248,825` bytes | `3,276,049` bytes | `a9298ae22a556f3d4ec053f0a07c33bd3d2156cd130f5e09068090e079be2d48` |
| Final primary 3-hour dynamic artifact (`tp`, `10u`, `10v`, `2t`) | `145,014,222` bytes, derived from the recorded `Content-Range` total | `3,074,657` bytes | `7d4b2feae148ade17a90b8168091d64d0f27b40ed55aa19530c48f49d53fdf9d` |
| Final auxiliary 0-hour surface-`z` artifact | Same 0-hour object above | `896,851` bytes | `529c14e03a8b22d86ff85e2bbd9d81c481ca626e410d1f6e8d875a112f4cb501` |

The full objects were not downloaded. The final accepted canonical record uses
the 3-hour dynamic artifact as primary and same-cycle step-zero surface `z` only
as `static_altitude` auxiliary provenance.

**UTC and coordinate evidence:**

- Forecast cycle: `2026-08-20T00:00:00Z`.
- Primary lead: `3` hours / `10800` seconds.
- Primary valid time: `2026-08-20T03:00:00Z`.
- Auxiliary `z` lead/valid time: `0` / `2026-08-20T00:00:00Z`.
- Exact connector retrieval timestamp is not stated in the current handoffs;
  they state only that local retrieval succeeded on 2026-08-21 UTC.
- Historical backend `last_success_at`:
  `2026-08-20T18:40:28.274415+00:00`; this is not identified as retrieval time.
- Requested Everest coordinate: `(27.9881, 86.9250)`.
- Selected provider coordinate: `(28.0, 87.0)`.
- Combined real parse: five GRIB messages, `z`, `tp`, `10u`, `10v`, and `2t`.

**Persistence and API outcome.** Disposable PostgreSQL at `localhost:46133`
applied migration `20260821_0003` as part of the chain. The accepted run
persisted two raw artifacts, one canonical weather record, and one
`static_altitude` association. The bounded request
`GET /api/weather/forecast?source=ecmwf-ifs&start=2026-08-20T03:00:00Z&end=2026-08-20T03:00:00Z`
returned HTTP `200` with exactly one record. The disposable database, volume,
and listener were removed afterward.

### NOAA GFS

**Provider and product.** NOAA/NCEP NOMADS, `GFS pgrb2.0p25`, GRIB2. The
documented run cadence is 00, 06, 12, and 18 UTC.

**Exact official URLs:**

- GRIB2:
  `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000`
- Index:
  `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000.idx`
- Official product root:
  `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod`

**Size and integrity evidence:**

- The directory advertised the full GRIB2 object as approximately `473 MB` and
  the index as approximately `31 KB`; exact full-object bytes and a full-object
  hash are not recorded.
- The full object was not downloaded.
- Selected retained payload: `2,937,483` bytes.
- Payload SHA-256:
  `9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`.
- Canonical metadata sidecar digest:
  `f99e6967479a193def39c1bf80e364fcaea9ac39a4fb3ebaf2f97778e54eb9de`.

**UTC and coordinate evidence:**

- Cycle/lead/valid time: `2026-08-20T00:00:00Z` / `0` seconds /
  `2026-08-20T00:00:00Z`.
- The corrected connector rerun and historical backend `last_success_at` are
  recorded as `2026-08-21T02:27:10.360839+00:00`; the handoff does not preserve
  a separately named connector retrieval timestamp.
- Requested Everest coordinate: `(27.9881, 86.9250)`.
- Selected provider coordinate: `(28.0, 87.0)`.
- Parsed messages/variables: four, `orog`, `2t`, `10u`, and `10v`.

**Persistence and API outcome.** The checked-in
`compose_gfs_ingestion_adapter` path used disposable PostgreSQL at temporary
port `34034`, applied migrations `20260821_0001` through `20260821_0003`, and
persisted `raw=1` and `record=1`. A bounded `source=noaa-gfs` 00Z forecast query
returned HTTP `200` with one record. The disposable database and temporary
resources were removed afterward. The earlier official filter request's HTTP
`500` is an alternative-path failure; the authoritative direct `.idx`/HTTP-206
path succeeded and is the accepted source outcome.

### DWD ICON

**Provider and product.** DWD Open Data global ICON on its native approximately
13 km unstructured grid. Source objects are bzip2-compressed GRIB2 products.
The documented run cadence is 00, 06, 12, and 18 UTC.

**Exact official URLs and selected object sizes:**

| Field | Exact URL | Compressed bytes | Decompressed bytes |
| --- | --- | ---: | ---: |
| `T_2M` | `https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/icon_global_icosahedral_single-level_2026082100_000_T_2M.grib2.bz2` | `3,338,757` | `3,323,939` |
| `U_10M` | `https://opendata.dwd.de/weather/nwp/icon/grib/00/u_10m/icon_global_icosahedral_single-level_2026082100_000_U_10M.grib2.bz2` | `3,876,736` | `3,860,511` |
| `V_10M` | `https://opendata.dwd.de/weather/nwp/icon/grib/00/v_10m/icon_global_icosahedral_single-level_2026082100_000_V_10M.grib2.bz2` | `3,885,537` | `3,870,728` |
| `HSURF` | `https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2` | `1,313,525` | `1,369,453` |
| `CLAT` | `https://opendata.dwd.de/weather/nwp/icon/grib/00/clat/icon_global_icosahedral_time-invariant_2026082100_CLAT.grib2.bz2` | `1,264,300` | `2,574,603` |
| `CLON` | `https://opendata.dwd.de/weather/nwp/icon/grib/00/clon/icon_global_icosahedral_time-invariant_2026082100_CLON.grib2.bz2` | `1,398,235` | `2,625,627` |

The aggregate compressed source size was `15,077,090` bytes. These six
independent objects were the smallest official products available on the
documented route; no provider message index or safe byte-range product API was
found. No larger combined full-object size or hash exists in the handoff.

**Retained artifact integrity:**

- Combined decompressed GRIB2: `17,624,861` bytes; SHA-256
  `e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57`.
- Canonical `metadata.json`: `1,392` bytes; SHA-256
  `cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf`.
- `metadata.json.sha256`: `65` bytes; file SHA-256
  `0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46`.

**UTC and coordinate evidence:**

- Retrieval UTC: `2026-08-21T03:59:32.333262+00:00`.
- Cycle/lead/valid time: `2026-08-21T00:00:00Z` / `0` hours /
  `2026-08-21T00:00:00Z`.
- Requested WGS 84 coordinate: `(27.98806, 86.92528)`; acceptance tests also
  describe the canonical request as `(27.9881, 86.9250)`.
- Selected provider coordinate:
  `(27.926742553710938, 86.921875)`.
- DWD grid UUID/index:
  `a27b8de618c411e4820ab5b098c6a5c0` / `818403`.
- Parsed messages: six, `2t`, `10u`, `10v`, `HSURF`, `tlat`, and `tlon`, each
  with `2,949,120` values.

**Persistence and API outcome.** The authoritative post-review run used pinned
`postgres:17-alpine` at disposable localhost port `46583` and migrations
`20260821_0001` through `20260821_0006`. It persisted exactly `raw=1`,
`record=1`, and `audit=1` after canonical commit. The request
`GET /api/weather/forecast?source=dwd-icon` returned HTTP `200` with exactly one
record and native spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. Public output exposed no raw
path, provider URL, payload hash, raw metadata, retention, hold, disposition, or
audit fields. The database, container/volume, listener, port, and temporary
Python environment were removed; retained approved-root raw artifacts were not
deleted or rewritten.

One prior exact dynamic-product request returned HTTP `404`; a later exact-href
retrieval succeeded. The API `spatial_key` omission occurred twice before the
shared serializer was corrected. That occurrence counter remains `2` and was
not reset by the successful run.

### ECMWF AIFS

**Provider and product.** ECMWF Open Data `aifs-single/0p25/oper`, AIFS Single
v2, GRIB2. Runs are 00, 06, 12, and 18 UTC with 6-hour forecast steps through
360 hours.

**Exact official URLs:**

- GRIB2:
  `https://data.ecmwf.int/forecasts/20260821/00z/aifs-single/0p25/oper/20260821000000-0h-oper-fc.grib2`
- Index: the exact GRIB2 object stem above with `.index`, namely
  `https://data.ecmwf.int/forecasts/20260821/00z/aifs-single/0p25/oper/20260821000000-0h-oper-fc.index`
- Official data root: `https://data.ecmwf.int/forecasts/`

**Size and integrity evidence:**

- The global source object is described only as `89+ MB`; its exact full size
  and full-object hash are not recorded, and it was not downloaded.
- Five selected ranges totaled `3,061,386` retained bytes.
- Payload SHA-256:
  `46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5`.
- Canonical `metadata.json`: `1,116` bytes; SHA-256
  `86e77f9d36058c40495d3641ff1afce38343c61deb89901cd3435ec702cb9b01`.
- `metadata.json.sha256`: `65` bytes; file SHA-256
  `62f264fe043978e39936e0a51e71385e8c95f8916e7bd342bc90d456fa0ee78e`.
- Selected ranges in retained order: `z` offset `16865591`, length `802648`;
  `10u` offset `89067274`, length `821931`; `10v` offset `3123280`, length
  `824820`; `2t` offset `5780158`, length `611763`; and `tp` offset `32006373`,
  length `224`.

**UTC and coordinate evidence:**

- Retrieval UTC: `2026-08-21T10:09:58.234370Z`.
- Cycle/lead/valid time: `2026-08-21T00:00:00Z` / `0` hours /
  `2026-08-21T00:00:00Z`.
- Requested coordinate: `(27.98806, 86.92528)`.
- Selected provider coordinate: `(28.0, 87.0)`; flat index `358188`.
- Native spatial key: `aifs-single:0p25:1440x721:358188`.
- Parsed messages/variables: five, `z`, `10u`, `10v`, `2t`, and `tp`.
- Every retained message has AIFS Single v2
  `generatingProcessIdentifier=5` and the reviewed level binding.

**Source/core and historical DB/API outcome.** The hardened accepted run used
WSL ecCodes/Python bindings `2.47.1`, pinned disposable PostgreSQL on
non-standard localhost port `46901`, and migrations `0001` through `0006`. The
complete `apps/api` result was `66 passed, 0 failed, 0 skipped`; focused AIFS
coverage was `4 passed, 0 failed, 0 skipped`; and focused meteorology AIFS
coverage was `37 passed, 0 failed, 0 skipped`. The committed path persisted
exactly `raw=1`, `record=1`, and `audit=1`. The historical bounded
`GET /api/weather/forecast?source=ecmwf-aifs` request returned HTTP `200`, UTC
`Z` timestamps, the native spatial key, `source=ecmwf-aifs`, and `model=AIFS`,
never IFS, without exposing private raw or audit fields. This establishes AIFS
source/core PASS and historical disposable DB/API acceptance.

The source registry still documents AIFS as `connected`. Historical
`verified`/`healthy` was valid only after canonical commit in the disposable
run and is not promoted into a current lifecycle or health claim. PostgreSQL,
the container, volume, listener, and port `46901` were removed; current database
health, API availability, and runtime status are `unknown`.

The strict 6-hour complete-field request failed at
`2026-08-21T10:16:03.8283828Z` because the official index lacked exactly one
surface `z` message. No corrupt artifact was retained. The complete 0-hour
sample succeeded. A future non-zero-step altitude association requires a
separately reviewed same-AIFS, same-cycle auxiliary-artifact design.

## Database and Migrations

The backend persistence chain is Alembic `20260821_0001` through
`20260821_0006`:

| Revision | Database effect |
| --- | --- |
| `20260821_0001_data_source_registry` | Creates `data_source_registry`, `data_source_schedule`, and `data_source_run`. |
| `20260821_0002_weather_persistence` | Creates `weather_raw_artifact` and `weather_record`, including source/raw relationships, canonical fields, constraints, deduplication keys, and append-only protections. |
| `20260821_0003_weather_record_provenance` | Creates `weather_record_raw_artifact` for immutable `static_altitude` auxiliary provenance. |
| `20260821_0004_raw_retention_audit` | Adds retention, acquisition, due-date, disposition, hold, and policy fields to `weather_raw_artifact`; creates append-only `raw_artifact_audit_event`. |
| `20260821_0005_retention_trigger_correction` | Corrects table-specific immutable and retention-transition triggers and scalar audit validation. |
| `20260821_0006_raw_retention_json_trigger_fix` | Corrects PostgreSQL JSON comparison in retention triggers while preserving the reviewed downgrade path. |

IFS and GFS authoritative source runs used migrations through `0003`. ICON's
authoritative post-review run and the authoritative hardened AIFS DBRE run used
the full chain from `0001` through `0006` without a revision gap.

## API Evidence

Under ADR-015, the A-F display acceptance surface is exactly the following five
backend routes. Route implementation, fake-session HTTP, direct database
assertions, and retained provider-backed HTTP evidence are not interchangeable.

| Required route | Implemented | Exact retained evidence | ADR-015 finding |
| --- | --- | --- | --- |
| `GET /api/weather/current` | Yes | Retained IFS bytes (surface + pressure) were parsed, normalized, committed to disposable PostgreSQL, and queried over HTTP with `200` and 13 real records in the 2026-08-28 disposable validation run. | **EVIDENCED HISTORICALLY** (disposable 2026-08-28). This is disposable historical evidence, not current availability. |
| `GET /api/weather/forecast` | Yes | Retained provider bytes were parsed, normalized, committed to disposable PostgreSQL, and queried over HTTP for the accepted source paths. ICON and AIFS retain executable integration coverage and historical HTTP `200` evidence; IFS and GFS retain historical handoff evidence; the 2026-08-28 disposable validation run also returned HTTP `200` with 13 real IFS records. | **EVIDENCED HISTORICALLY.** This is disposable historical evidence, not current availability. |
| `GET /api/weather/profile` | Yes | Retained IFS pressure levels were parsed, normalized, vertically interpolated to route elevations, persisted, and queried over HTTP: `?profile=SUMMIT` returned HTTP `200` with a real interpolated record (8848.86 m, interp 400-300 hPa) in the 2026-08-28 disposable validation run. | **EVIDENCED HISTORICALLY** (disposable 2026-08-28). This is disposable historical evidence, not current availability. |
| `GET /api/weather/sources` | Yes | The 2026-08-28 disposable validation run persisted four real registry source rows (IFS/GFS/ICON/AIFS) and returned HTTP `200` with all four over HTTP. | **EVIDENCED HISTORICALLY** (disposable 2026-08-28). This is disposable historical evidence, not current availability. |
| `GET /api/data-health` | Yes | The 2026-08-28 disposable validation run returned HTTP `200` with the four persisted registry health rows over HTTP. | **EVIDENCED HISTORICALLY** (disposable 2026-08-28). This is disposable historical evidence, not current availability. |

Consequently, this report makes no generalized claim that all five routes
returned real data. It retains the final source/core evidence and the exact
forecast-route evidence without upgrading fake-session tests, database rows, or
route existence into missing HTTP evidence. The missing evidence was not
regenerated because `AGENTS.md` prohibits rerunning a database solely to close
documentation. No database, API, provider, raw-data operation, or test was run
for this correction.

## ADR-015 Evidence Update — 2026-08-28 Disposable Validation Run

The Everest Manager assigned a substantive validation run (ADR-021,
`EV-DATA-001-ADR015-VALIDATE-2026-08-28`) to close the four-route evidence gap
recorded by ADR-016. Under the ADR-016 future-run conditions (explicit
assignment, substantive objective, QA harness, random nonstandard port `59613`,
disposable `postgres:17-alpine`, teardown, no external retrieval), the run:

- ingested only retained real IFS payloads (surface `638a075b…`, pressure
  `00741f…`, SHA-256 verified; no provider contact and no raw mutation);
- migrated the disposable database to head (`0001`→`0010`);
- returned HTTP `200` with real canonical records for all five ADR-015 routes:
  `forecast` 13 records, `current` 13 records, `profile?profile=SUMMIT` 1
  interpolated record (8848.86 m, interp 400–300 hPa), `sources` 4 registry
  rows, `data-health` 4 health rows;
- recorded evidence at `docs/qa/adr015-disposable-evidence-2026-08-28.json`;
- was torn down after the run (container removed, port `59613` released).

This closes the ADR-015 four-route evidence gap. It is historical disposable
evidence only. Current health and API availability remain `unknown` after
teardown; no live-service or current-health claim follows.

The public canonical allow-list excludes raw object identifiers and paths,
provider URLs, hashes, metadata, retention, hold, disposition, and audit facts.
No route is currently claimed available because all disposable environments
were torn down. Current API availability remains `unknown`.

No UI was implemented or evidenced. ADR-015 defines "frontend display" for A-F
as the five-route backend REST criterion above; it does not require Next.js,
Cesium, a browser, or any other UI. Frontend pages remain deferred to a
separately authorized delivery, and the prohibition on new UI remains in force.

## Authoritative Test Evidence

| Scope | Final authoritative result | Failures | Skips | Qualification |
| --- | --- | ---: | ---: | --- |
| IFS final disposable backend E2E | `27 passed, 16 warnings` | Not separately stated | All PostgreSQL tests ran; an exact total skip count is not separately stated | Phase C QA ultimately passed after metadata and handoff remediation. |
| GFS historical backend harness | `29 passed, 20 warnings` | Not separately stated | Not separately stated | Explicit checked-in adapter integration: `2 passed`. |
| ICON post-review complete `apps/api` suite | `58 passed` | `0` | `0` | Focused real ICON PostgreSQL/API: `2 passed, 0 failed, 0 skipped`. This supersedes earlier 49- and 53-pass records. |
| AIFS parser review focused WSL retained-real suite | `37 passed` | `0` | `0` | Executes against the retained artifact. |
| AIFS parser review complete weather suite | `147 passed` | `0` | `1` | The skip is the opt-in Windows native retained-real case; WSL executed it separately. |
| AIFS parser review repository regression suite | `197 passed` | `0` | `20` | Environment-dependent skips do not establish DB/API acceptance. |
| AIFS hardened complete `apps/api` execution | `66 passed` | `0` | `0` | Focused AIFS PostgreSQL/API: `4 passed, 0 failed, 0 skipped`; focused meteorology AIFS: `37 passed, 0 failed, 0 skipped`. Source/core PASS. |

No tests were rerun for this report. The counts above are evidence quoted from
the authoritative handoffs, not new execution results. Where a handoff does not
state failures or skips separately, this report records them as unavailable
rather than deriving them from shorthand.

## Licensing and Commercial Use

| Source | Recorded licensing finding | Commercial-use finding and explicit limits |
| --- | --- | --- |
| ECMWF IFS | CC BY 4.0 plus ECMWF Open Data Terms of Use. | ECMWF source terms permit redistribution and commercial use subject to attribution, licence link, modification notice, disclaimer, and the applicable ECMWF terms. This is a source-terms finding only; no deployment-specific legal approval for Everest is recorded. |
| NOAA GFS | Public distribution; product-specific licensing terms were not assessed in the source registry. | Commercial permission remains unknown pending product-specific confirmation and policy review. Credentials and numerical rate limits were also not authoritatively assessed in the final registry entry. |
| DWD ICON | DWD legal notice applies CC BY 4.0 with attribution to the documented Open Data products. | Phase E QA records that CC BY 4.0 permits commercial reuse subject to its terms. The registry field still says unknown pending policy review, so Everest deployment-specific legal approval remains unknown. No credential or numerical rate-limit claim is made. |
| ECMWF AIFS | CC BY 4.0 plus ECMWF Open Data Terms of Use. | ECMWF permits redistribution and commercial use subject to attribution, licence link, modification notice, and disclaimer. This is a source-terms finding, not legal approval for an Everest deployment. Direct Open Data retrieval was anonymous; archive MARS is separate and restricted. The documented concurrent-connection limit is `500`; per-IP request/minute, byte/day, and bandwidth quotas are unknown. |

The official licensing references retained by the handoffs are:

- ECMWF Open Data catalogue:
  `https://www.ecmwf.int/en/forecasts/datasets/open-data`
- ECMWF Open Data Terms of Use:
  `https://apps.ecmwf.int/datasets/licences/general/`
- DWD legal notice:
  `https://www.dwd.de/EN/service/legal_notice/legal_notice_node.html`

## Operational Status and Latency

Current source health and API availability are **unknown** after teardown. The
historical IFS, GFS, and ICON `verified`/`healthy` values were facts inside
disposable acceptance databases and are not current health. AIFS has no current
runtime health record. Source presence in configuration does not imply a live,
healthy, or verified service.

No authoritative end-to-end, retrieval, parser, persistence, or API latency
measurement is recorded for any of the four sources. Current latency is
**unavailable**, not zero and not inferred from test duration. Continuous
scheduling, freshness, availability, and operational health reporting were not
demonstrated.

## Gate C-Operational Gaps

Gate C-Core is accepted for the controlled historical ICON path. Gate
C-Operational remains open and blocks shared/production deployment, automatic
disposition, and production-grade retention claims. The open controls are:

1. Named connector-write and operator-read identities, least-privilege OS ACL or
   object-store IAM, unauthorized read/write denial, and grant/change/revocation
   evidence.
2. Deployment-enforced legal-hold authority and release lifecycle, controlled
   disposition authority, fail-closed hold handling, and WORM or equivalent
   resistance to privileged modification.
3. Complete production audit coverage, audit access controls, and operational
   retention enforcement.
4. Authoritative Git-bearing evidence that raw payloads, metadata, and checksum
   sidecars are excluded and untracked. This workspace has no `.git` metadata.
5. Controlled disposition of legacy project-root `tmp-icon*` and `tmp-gfs*`
   artifacts, which remain noncompliant durable-storage evidence and were not
   operated on by this report.
6. Current deployed database, service, scheduler, health monitor, and API
   evidence. None is established by the historical disposable runs. Browser/UI
   implementation is separately deferred and is not a Gate C-Operational
   closure claim.

## Repeated-Failure Record

### `EV-DATA-001-F-INCIDENT-001`

- Affected component: PowerShell -> `wsl.exe` -> nested inline Bash invocation.
- Identical root-cause occurrence count: `3`.
- Root cause: a structured argument vector was encoded as an inline nested shell
  string and reparsed across PowerShell, WSL, and Bash, altering argument
  boundaries. It was not an AIFS, GRIB, PostgreSQL, FastAPI, raw-data, or product
  defect.
- Exact occurrence timestamps, full stdout/stderr, exit codes, PowerShell
  version, serialized command lines, and Linux argv are unavailable and cannot
  be recovered. Full repeated-failure escalation compliance is therefore not
  claimed.
- No fourth use of the prohibited nested-wrapper pattern occurred.
- Accepted procedure: invoke the Linux executable through `wsl.exe` with each
  argument separate, or use a reviewed script file; capture versions, UTC start
  and end, argument manifest, stdout/stderr, child/native exit codes, expected
  evidence, and cleanup. Inline PowerShell-originated `bash -c`/`bash -lc`
  strings are prohibited for this signature.
- The corrected successful AIFS DBRE was a distinct direct-argument/reviewed-
  procedure execution. It does not erase the three-event counter or reconstruct
  the missing incident logs.

The other retained counter is the ICON/shared-serializer `spatial_key` omission:
`2` occurrences, corrected and covered by regression tests. It did not reach
the three-occurrence escalation threshold. The GFS filter HTTP `500`, ICON
product HTTP `404`, and AIFS 6-hour missing-surface-`z` event are distinct source
or product-path failures; the authoritative handoffs do not establish three
identical occurrences for any of them.

## Required Next Recommendation

The next action is **not** a new data-source phase and is not evidence
regeneration. AIFS and all four forecast-source/core paths retain their final
historical evidence. QA and the Everest Manager must decide disposition of the
incomplete retained evidence for the exact ADR-015 five-route display criterion.
That decision must not infer endpoint evidence from implementation, fake-session
HTTP, or underlying rows, and must not infer current health from historical
disposable runs.

Gate C-Operational remains open until its IAM/ACL, legal/WORM, production audit,
Git, and deployment controls have independent evidence; under `AGENTS.md` these
are non-blocking follow-ups for A-F source/core close. Project-root `tmp-gfs*`
and `tmp-icon*` disposition, EBC-C4 camp-labelled records, measured current
latency or a continuously running service, `docs/product/PRD.md`,
`docs/gis/terrain-spec.md`, `GET /api/data-sources`, and GFS/ICON commercial-use
confirmation also remain explicitly non-blocking. No such artifact was operated
on by this correction. UI implementation requires separate authorization.

## Mandatory Stop

This delivery is stopped at Phase F by the controlling QA record
`EV-DATA-001-F-QA-STOP` and Everest Manager confirmation. The exact ADR-015
five-route display criterion is not fully evidenced; ADR-016 accepts that
historical limitation. Do not regenerate the
missing evidence solely for documentation, and do not begin Everest AWS,
Pyramid, satellite, terrain, environmental, OpenStreetMap, AI, Risk, UI, or any
other post-Phase-F work without a new explicit instruction and the required
governance sequence. Open non-blocking follow-ups do not authorize bypassing or
extending the current delivery boundary.

## Handoff Authorities

This report synthesizes, without replacing, these current authorities:

- `docs/data-sources.md`
- `docs/meteorology/weather-spec.md`
- `docs/api/API.md`
- `docs/qa/test-plan.md`
- `docs/management/decisions.md`
- `docs/management/board.md`
- `docs/architecture/architecture.md`

Where chronology conflicts, this report follows each handoff's explicit
authoritative/superseding marker and the current `AGENTS.md`. In particular,
the authoritative AIFS evidence labels are `full66`, `AIFS4`, `met37`, and
port `46901`. Historical AIFS DB/API acceptance does not alter its documented
current `connected` registry status or current unknown health.
