# Everest Data Sources

## EV-DATA-001-F-AIFS-DOCS-CLOSE-RETRY — authoritative hardened closure

This section is the authoritative final documentation for the AIFS closure
retry. It supersedes the earlier `61/63` and failing-result reports, the
`61/61` report, the earlier `44859` port, and every older `pre-DBRE`,
`no-DBRE`, or blocked assertion. Those records remain historical chronology
only. No code, test, external-source, or raw-artifact change was made by this
documentation-only retry.

### Final evidence and lifecycle boundary

The hardened evidence used WSL ecCodes/Python bindings **2.47.1**, pinned
disposable PostgreSQL on non-standard localhost port **`46901`**, and applied
migrations **`0001`–`0006`**. The complete `apps/api` result was **66 passed,
0 failed, 0 skipped**. Explicit focused results were **AIFS 4 passed, 0
failed, 0 skipped** and **meteorology AIFS 37 passed, 0 failed, 0 skipped**.
The accepted direct-argv/reviewed wrapper procedure was used; the prior
PowerShell-to-WSL nested-wrapper incident remains accepted as an infrastructure
incident, with **no recurrence** in this run. Docker lifecycle evidence records
**2** disposable lifecycle checks. The fixture root counters were
**fixture=1**, and the successful committed path was exactly
**`raw=1`, `record=1`, `audit=1`**.

The source registry remains **`connected` only** for AIFS. This evidence does
not promote the current registry row to `verified`, and the current lifecycle
claim is **no-DBRE/current runtime unknown** after teardown. Historical
`verified`/`healthy` values are valid only for the disposable run and only
after the canonical transaction committed; the database, container, volume,
listener, and port `46901` were then removed. Current health and API
availability are therefore **unknown**.

### Retained artifact, provenance, and decoded message inventory

The existing immutable retained payload/metadata/sidecar evidence is unchanged:

* Payload: `3,061,386` bytes, SHA-256
  `46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5`.
* Canonical `metadata.json`: `1,116` bytes, SHA-256
  `86e77f9d36058c40495d3641ff1afce38343c61deb89901cd3435ec702cb9b01`.
* `metadata.json.sha256`: file SHA-256
  `62f264fe043978e39936e0a51e71385e8c95f8916e7bd342bc90d456fa0ee78e`;
  its declaration matches the metadata digest.

The payload, metadata, and sidecar were bound to the same regular,
non-symlink artifact directory beneath the approved absolute
`EVEREST_RAW_ROOT`; the directory name equals the payload digest. Hardened
validation independently checked approved-root containment, canonical JSON,
range inventory and complete non-overlapping byte coverage, file sizes,
checksums, source/model/dataset identity, AOI, cycle, lead, valid time, and
inventory binding. Caller-provided paths, hashes, URLs, ranges, and decoded
messages were not trusted. Raw retention is first and immutable; QC flags
anomalies and does not delete raw data.

WSL ecCodes decoded **exactly five** messages and no others: `z`, `10u`,
`10v`, `2t`, and `tp`. Native levels were `surface/0`,
`heightAboveGround/10`, `heightAboveGround/10`, `heightAboveGround/2`, and
`surface/0`, respectively. Every message carried AIFS Single v2
`generatingProcessIdentifier=5`. The regular grid was **1440 x 721**; the
Everest request selected provider point `(28.0, 87.0)`, flat index **358188**,
and spatial key **`aifs-single:0p25:1440x721:358188`**. Canonical values were
altitude `5346.3264215561 m`, temperature `0.45586547851564774 C`, wind speed
`0.16091116689523915 m/s`, wind direction `86.4729776688032` degrees,
precipitation `0.0 mm`, null visibility, and `[missing_value]`.

### API, identity, and negative-path evidence

The historical bounded AIFS forecast query returned **HTTP 200**, UTC
timestamps with a trailing `Z`, the canonical record, and the native spatial
key. It proved AIFS remained `ecmwf-aifs` / `AIFS` and **never IFS**; no raw
path, provider URL, payload/metadata/sidecar hash, raw metadata, retention,
hold, disposition, or audit field leaked through the public projection.
The API contract requires UTC-aware input and emits UTC ISO-8601 values; this
behavior is historical test evidence only because the API was torn down.

Negative tests covered AIFS/IFS conflation and source/model/provider-process
identity mismatches, wrong inventory or levels, forged provenance, range or
checksum tampering, and raw-first canonical failure. Raw-first failure left
the classified raw fact retained, inserted no canonical record, and did not
escalate lifecycle or health to `verified`/`healthy`. `Retry-After` handling
remains fail-closed and RFC 9110 compliant: delta-seconds and IMF-fixdate are
accepted, malformed or over-60-second values are rejected, and the retry is
bounded. Official facts, licensing, anonymous-authentication behavior, the
500-connection limit, and undocumented per-IP/byte/bandwidth limits remain as
recorded below; unknowns are not inferred.

## EV-DATA-001-F-REVIEW-FIX-PARSER

The AIFS decoded trust boundary now requires exact five-message inventory
`z,10u,10v,2t,tp` and binds parser output to retained metadata before adapter
composition. The retained sample's read-only ecCodes level inventory is
`z=surface/0`, `10u=heightAboveGround/10`,
`10v=heightAboveGround/10`, `2t=heightAboveGround/2`, and `tp=surface/0`;
every message has AIFS Single v2 `generatingProcessIdentifier=5`. Duplicate,
missing, unexpected, wrong-level, wrong-process, or cycle/lead/valid metadata
mismatches are rejected. Explicit source/checksum/inventory/stale/duplicate QC
evidence is additive and never deletes raw data. This review fix performed no
external retrieval, raw mutation, DB/API operation, or status change.

The immutable historical dataset label
`AIFS Single Open Data 0.25 degree` and current connector label `AIFS Single`
are the only accepted dataset identities; the historical sidecar was not
rewritten. Final evidence: focused WSL retained-real tests `37/37`, complete
weather tests `147 passed, 1 skipped`, Black 30 files unchanged, Pylint
`10.00/10`, compileall exit `0`, and repository regression tests `197 passed,
20 skipped` with no failure.

## EV-DATA-001-F-AIFS — Phase F connector and retained-real-data handoff

### EV-DATA-001-F-REVIEW-FIX-RETRY

The AIFS connector handles HTTP 429 independently from transport and other HTTP
failures. It requires `Retry-After`, accepts RFC 9110 delta-seconds and
IMF-fixdate values, and injects both sleep and the reference clock for
deterministic tests. Delays above the documented connector maximum of 60 seconds
and malformed values fail closed; valid delays are slept once per retry and the
existing `retry_limit + 1` attempt bound is preserved. The implementation was
checked against RFC 9110 section 10.2.3 and the Requests response/exception
documentation:

- <https://www.rfc-editor.org/rfc/rfc9110.html#field.retry-after>
- <https://requests.readthedocs.io/en/latest/api/#requests.Response>

This review fix is connector/tests/docs only. No external data, raw artifact,
database, API, or frontend behavior was changed.

### EV-DATA-001-F-REVIEW-FIX-PROVENANCE

The AIFS conversion boundary now treats `RawRetrieval` as an untrusted caller
DTO. Conversion reconstructs all provenance from the retained payload and its
sibling `metadata.json` and `metadata.json.sha256`; it does not trust caller
paths, hashes, sizes, URLs, cycles, leads, or parameter lists. Runtime
conversion requires an existing absolute `EVEREST_RAW_ROOT`. Payload,
metadata, and sidecar must be regular non-symlink files in the same
content-addressed directory beneath that root, whose name is the payload
SHA-256. Canonical metadata is fail-closed unless it identifies provider
`ECMWF`, `aifs_version=2`, format `GRIB2`, dataset `AIFS Single`, the approved
Everest coordinate/AOI, and a complete non-overlapping range inventory whose
lengths equal the retained payload size. The metadata hash declaration and
canonical JSON bytes are independently checked.

This change is conversion/tests/docs only. It does not alter external
retrieval, database/API behavior, raw files, scalar projection, or the strict
AIFS-versus-IFS identity boundary. Negative tests cover mixed artifact
directories, root escape, symlinks, forged retrieval fields, provider/model
identity, version, format, dataset, AOI, range, inventory, canonical JSON,
and payload/metadata/sidecar integrity failures.

**Assignment:** `EV-DATA-001-F-AIFS`  
**Evidence date:** 2026-08-21  
**Lifecycle:** `connected`, **not `verified`**. Official retrieval, immutable
retention, WSL ecCodes parsing, canonical normalization/QC, and the thin shared
ingestion adapter succeeded. No AIFS PostgreSQL persistence, API query, QA
acceptance, frontend display, or lifecycle promotion was performed. Current
runtime/API health is `unknown`.

### Official documentation and current source facts

The following current ECMWF-owned documentation was consulted before
implementation:

- Open Data catalogue and terms:
  <https://www.ecmwf.int/en/forecasts/datasets/open-data>
- Technical access, naming, index, and byte-range documentation (last updated
  2026-07-06):
  <https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS>
- AIFS model/data description:
  <https://www.ecmwf.int/en/forecasts/dataset/aifs-machine-learning-data>
- Deterministic AIFS Set IX product table:
  <https://www.ecmwf.int/en/forecasts/datasets/set-ix>
- AIFS Single v2 implementation and GRIB identity:
  <https://confluence.ecmwf.int/display/FCST/Implementation+of+AIFS+Single+v2>
- Open Data Terms of Use:
  <https://apps.ecmwf.int/datasets/licences/general/>
- Official data root: <https://data.ecmwf.int/forecasts/>

Verified facts are: current deterministic model `aifs-single`, canonical model
label `AIFS`, operational version **AIFS Single v2** since 2026-05-12 06 UTC,
MARS class `ai`, stream `oper`, type `fc`; four runs daily at 00/06/12/18 UTC;
6-hour forecast steps from 0 through 360 hours; global regular 0.25 by 0.25
degree Open Data grid (native model grid N320, approximately 31 km); GRIB edition
2 with WMO units; and ECMWF's recommendation of ecCodes 2.42.0 or newer for Open
Data, with 2.46.0 specifically recommended for AIFS Single v2. The portal has a
rolling archive of the latest 12 runs (approximately 2–3 days) and a documented
limit of **500 simultaneous connections**. No documented per-IP request/minute,
byte/day, or bandwidth quota was found; those limits are **unknown**, and HTTP
429/`Retry-After` must be treated as provider control rather than guessed.

The official direct Open Data portal is anonymous for this retrieval; no API
key, account, or credential was required. Archive MARS access is a separate,
registered/restricted path and was not used. Data are CC BY 4.0 plus ECMWF Terms
of Use. ECMWF explicitly states redistribution and commercial use are allowed
subject to the required ECMWF attribution, licence link, modification notice,
and disclaimer. This records source terms, not legal approval for a particular
Everest deployment.

### Exact real retrieval and immutable artifact

The connector used only the approved default 100 km AOI's summit center
`27.98806, 86.92528` as the requested location. ECMWF's official Open Data files
are global grids, but the full 89+ MB source object was **not** downloaded. The
connector read the official JSON-Lines `.index` and issued strict HTTP `206`
requests for only five surface ranges. Each response required matching
`Content-Range` and exact byte length; an unexpected HTTP `200` fails closed.

- Cycle / lead / valid UTC: `2026-08-21T00:00:00Z` / `0` hours /
  `2026-08-21T00:00:00Z`.
- GRIB2 URL:
  `https://data.ecmwf.int/forecasts/20260821/00z/aifs-single/0p25/oper/20260821000000-0h-oper-fc.grib2`
- Index URL: same object stem with `.index`.
- Selected index ranges, in retained order: `z` offset `16865591`, length
  `802648`; `10u` offset `89067274`, length `821931`; `10v` offset `3123280`,
  length `824820`; `2t` offset `5780158`, length `611763`; `tp` offset
  `32006373`, length `224`.
- Retained payload:
  `D:\Everest-data\raw\ecmwf-aifs\46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5\20260821000000-0h-oper-fc.grib2`.
- Payload size / SHA-256: `3,061,386` bytes /
  `46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5`.
- Retrieval UTC: `2026-08-21T10:09:58.234370Z`.
- Canonical `metadata.json`: `1,116` bytes, SHA-256
  `86e77f9d36058c40495d3641ff1afce38343c61deb89901cd3435ec702cb9b01`.
- Mandatory 65-byte `metadata.json.sha256` file: SHA-256
  `62f264fe043978e39936e0a51e71385e8c95f8916e7bd342bc90d456fa0ee78e`;
  its declaration matches the metadata digest.

Payload, canonical metadata, and sidecar are content-addressed beneath the
external `EVEREST_RAW_ROOT`, atomically written, fsynced, rehashed, checked on
reuse, and marked read-only on a best-effort basis. This does not claim Windows
ACL/WORM enforcement. AOI scalars are `aoi_id=everest-south-route`,
`aoi_version=everest-south-route-v1.0`, and
`aoi_scope_id=everest-south-route-v1.0-default-100km`.

### Parse, grid, values, QC, and backend descriptor

WSL ecCodes/Python bindings `2.47.1` parsed five real GRIB2 messages: `z`,
`10u`, `10v`, `2t`, and `tp`. Every message had
`generatingProcessIdentifier=5`, the documented AIFS Single v2 atmospheric
identifier, and regular grid `1440 x 721`. Requested
`(27.98806, 86.92528)` selected provider point `(28.0, 87.0)`, flat index
`358188`, and native spatial key
`aifs-single:0p25:1440x721:358188`. Parsed values were:

- `z=52429.552001953125 m**2 s**-2`;
- `10u=-0.16060638427734375 m s**-1`;
- `10v=-0.009899139404296875 m s**-1`;
- `2t=273.6058654785156 K`;
- `tp=0.0 kg m**-2` (numerically equivalent to `0.0 mm` water depth).

Canonical output is source/model `ecmwf-aifs`/`AIFS`, altitude
`5346.3264215561 m`, temperature `0.45586547851564774 C`, wind speed
`0.16091116689523915 m/s`, direction `86.4729776688032` degrees,
precipitation `0.0 mm`, null visibility, and additive QC `[missing_value]`.
The record remains distinct from IFS through source, model, provider model,
spatial key, cycle, lead, valid time, and content hash.

The exact backend-E2E handoff is produced by
`aifs_raw_retention_metadata_from_retrieval` then
`compose_aifs_ingestion_adapter`. Its primary descriptor has dataset
`AIFS Single Open Data 0.25 degree`, the retained absolute object reference,
format `GRIB2`, size/hash and retrieval/cycle/lead/valid facts above, source URL
above, and scalar projected payload/metadata/sidecar integrity plus AOI facts.
The canonical DTO carries the native spatial key and values above. No nested
sidecar mappings cross the owner-neutral port. This descriptor has **not** yet
been persisted by the backend; status therefore remains `connected`, not
`verified`, pending backend DB/API integration and independent QA.

One factual limitation was observed: the official 6-hour index did not contain
exactly one surface `z` message, so the strict complete-field request was
rejected rather than fabricating altitude or conflating an IFS/static artifact.
The retained 0-hour sample is complete. Any future non-zero-step altitude
association requires a formally reviewed same-AIFS, same-cycle auxiliary
artifact design.

Final implementation evidence: full weather tests `129 passed, 1 skipped`;
full repository tests `175 passed, 17 skipped`; retained-artifact WSL AIFS tests
`19 passed, 0 failed, 0 skipped`; Black passed with 30 files unchanged; complete
weather Pylint `10.00/10`; compileall exit `0`. The skips were expected local
PostgreSQL/native-parser conditions and are not represented as AIFS DB/API/QA
acceptance.

## EV-DATA-001-E-POSTREVIEW-MET-DOC — authoritative post-review evidence

**Assignment:** `EV-DATA-001-E-POSTREVIEW-MET-DOC`

The authoritative post-review Phase E result is **58/58 full-suite tests passed
(`58 passed, 0 failed, 0 skipped`)**, including **ICON 2/2 focused
PostgreSQL/API tests passed**. The disposable pinned PostgreSQL execution used
the non-standard localhost port **`46583`** and migrations
`20260821_0001` through `20260821_0006`.

The accepted test followed the complete retained six-message path: the approved
external-root ICON GRIB2 artifact was read with WSL ecCodes `2.47.1`; all six
real messages (`2t`, `10u`, `10v`, `HSURF`, `tlat`, and `tlon`) were parsed and
normalized; connector output was converted and bound to verified payload,
canonical-metadata, and sidecar hashes; the owner-neutral adapter projected the
verified scalar metadata; backend descriptor checks independently verified the
regular file, approved-root containment, byte size, SHA-256, and projected
payload size/hash consistency before persistence; and PostgreSQL persisted
exactly `raw=1`, `record=1`, and `audit=1` after canonical commit.

Coordinate acceptance covered both sides of the boundary. Requested WGS 84
latitude/longitude must be finite and within canonical ranges; the retained
Everest request selected and preserved the provider-native coordinate
`(27.926742553710938, 86.921875)`, grid UUID
`a27b8de618c411e4820ab5b098c6a5c0`, index `818403`, and native
`spatial_key=icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. Conversion
metadata binding, requested/native coordinate validation, and mismatch
fail-closed behavior all passed.

The bounded forecast API returned HTTP `200` with exactly one ICON record and
the native spatial key. Public API projection checks confirmed **no leak** of
the approved raw-root path, provider URL, payload hash, raw metadata, retention,
hold, disposition, or audit fields. The synthetic ICON raw-first failure passed
without false lifecycle escalation, and GFS/IFS persistence and shared API
regressions passed.

After acceptance, the disposable database, container/volume, listener, port
`46583`, and temporary Python environment were removed. The retained approved-
root ICON artifact and sidecars were not deleted, moved, or rewritten. Therefore
the in-run `verified`/`healthy` state is historical; **current ICON runtime
health and API availability are `unknown`**. Gate C-Core is accepted, while
**Gate C-Operational remains open**. No live, continuous, shared-deployment, or
production claim is made, and no AIFS work was performed.

Review findings **E-001 through E-010** are reconciled by the manager’s
[authoritative closure table in `docs/management/decisions.md`](management/decisions.md#review-finding-disposition).
E-001–E-006 and E-008–E-010 are closed there; E-007 remains assigned to the
open Gate C-Operational and does not support a production-authorization claim.

Every older test count (including `42`, `49/49`, and `53 passed`), older port
(`53112` or `47189`), skipped-test result, and blocked/pre-DBRE/no-DBRE assertion
elsewhere in this document is **historical and superseded for current Phase E
status**. Such text is retained only as chronology and must not be interpreted
as the authoritative post-review result or as a current blocker to Gate C-Core.

## Historical predecessor — EV-DATA-001-E-DOCS-FULL-FINAL

> **Historical notice:** This section records the predecessor 53-pass execution.
> It is superseded by the 58/58 post-review record above. Its counts, port, and
> any blocked assertions are non-authoritative for current Phase E status.

**Vocabulary reconciliation assignment:**
`EV-DATA-001-E-REVIEW-FIX-VOCAB`

For Phase E review and handoff, the final full-pipeline result **53 passed, 0
failed, 0 skipped**, including **ICON 2/2** focused PostgreSQL/API tests, is
authoritative. Every earlier `49/49`, skipped-test, blocked, pre-DBRE, or
no-DBRE statement is historical and superseded as a description of final Gate
C-Core/DBRE capability. Current runtime health and API availability remain
**unknown**, and **Gate C-Operational remains open**.

Cross-layer metadata names and conversions are governed by the single
authoritative translation table in
[`docs/meteorology/weather-spec.md`](meteorology/weather-spec.md#authoritative-cross-layer-vocabulary-translation).
In summary, raw `lead_hours` is converted to adapter
`provider_lead_seconds` and backend `forecast_lead_seconds`; it is never merely
renamed. Backend hold state uses only `none`, `held`, `released`, or `unknown`.
The persisted no-hold value is `none`; “not held” is prose only.

This section supersedes earlier ICON/DBRE statements that used port `53112`,
reported `49/49`, included skipped tests, or said that connector metadata could
not reach the adapter or that the parser/database path was unproven. The final
controlled run used WSL ecCodes and pinned PostgreSQL on the non-standard
listener `localhost:47189`. Migrations `0001`–`0006` applied successfully. The
full suite was **53 passed, 0 failed, 0 skipped**; focused ICON PostgreSQL/API
coverage was **2 passed**.

The complete path was exercised: actual connector output went through the
connector-output conversion and owner-neutral adapter projection; the backend
rehashed the retained payload before persistence; and the successful
transaction left exactly `raw=1`, `record=1`, and `audit=1`. WSL ecCodes parsed
six actual ICON messages: `2t`, `10u`, `10v`, `HSURF`, `tlat`, and `tlon`. The
bounded API response included the native `spatial_key` and leaked no raw path,
provider URL, payload hash, raw metadata, retention, hold, disposition, or
audit fields.

The synthetic raw-first regression forced canonical persistence to fail after
raw acceptance. It retained one classified raw artifact, persisted no
canonical record, and did not promote lifecycle or health to `verified` or
`healthy`. GFS and IFS regressions passed. The disposable database,
container/volume, listener, and port `47189` resources were cleaned up; the
approved raw artifact was not deleted. Current runtime health and API
availability are **unknown**. Root counts are unchanged at `raw=1`, `record=1`,
`audit=1` for the successful ICON path.

Gate C-Core/DBRE is complete, but **Gate C-Operational remains open**. This is
historical disposable acceptance evidence only, not a live, continuous, or
production claim. ECMWF AIFS work has not started.

## Phase A Registry Metadata

**Assignment:** EV-DATA-001-A-MET-DOCS  
**Scope:** Phase A data-registry documentation only.

This document registers only the four approved forecast sources in the current
delivery boundary: ECMWF IFS, ECMWF AIFS, NOAA GFS, and DWD ICON. The ECMWF IFS,
NOAA GFS, and DWD ICON entries below include explicitly recorded historical
disposable end-to-end acceptance evidence. None of those historical results
claims current operational health or a currently available API after environment
teardown.

ECMWF IFS and NOAA GFS have historical end-to-end acceptance evidence from
isolated disposable PostgreSQL executions. Each is documented as `verified`
because the backend persisted raw and canonical records and returned the record
through the forecast API. Each disposable environment was removed after its
test; this is not evidence of a currently healthy, continuously operating, or
production source. The Phase A `planned` statement for AIFS is superseded by
the current Phase F `connected` evidence at the top of this document. ICON has
historical disposable `verified`/`healthy` evidence only after its approved-root raw artifact and one
canonical record committed successfully. Its disposable database, listener,
and API were then removed, so current ICON health and API availability are
`unknown`; Gate C-Operational remains incomplete and no production claim is
made.

The entries identify official provider endpoints. Exact retrieval paths are
recorded only where their completed source phase has factual evidence; unstarted
sources retain only the official browse/portal information available to Phase A.

## Registry Entries

| Field | ECMWF IFS |
| --- | --- |
| `source_id` | `ecmwf-ifs` |
| `name` | ECMWF Integrated Forecasting System (IFS) |
| `provider` | European Centre for Medium-Range Weather Forecasts (ECMWF) |
| `category` | Forecast |
| `status` | `verified` (historical disposable end-to-end acceptance only; not a current production-service claim) |
| `access_method` | Official ECMWF Open Data portal with `.index`-selected HTTP byte ranges |
| `endpoint` | https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/ |
| `format` | GRIB2 |
| `update_frequency` | Runs at 00, 06, 12, and 18 UTC |
| `spatial_resolution` | Nominal 0.25 degrees |
| `temporal_resolution` | 0-hour lead sample; cycle/valid time 2026-08-20 00:00 UTC |
| `coverage` | Everest-area nearest-grid lookup demonstrated: requested 27.9881,86.9250 mapped to provider grid 28.0,87.0 |
| `license` | CC BY 4.0 plus ECMWF terms; official documentation: https://www.ecmwf.int/en/forecasts/datasets/open-data |
| `commercial_allowed` | Unknown pending applicable ECMWF terms and policy review |
| `credentials_required` | Unknown; not assessed in Phase A |
| `last_success_at` | `2026-08-20T18:40:28.274415+00:00` (persisted by the final disposable acceptance test; not current live health) |
| `last_failure_at` | `null` |
| `health_status` | `unknown` currently: the backend persisted `healthy` during the disposable test, but its container, volume, and listener were removed afterward |

### ECMWF IFS historical evidence

The earlier 23-pass, one-artifact, 00Z-only acceptance record previously
described in this document is superseded. The final corrected DBRE record below
is authoritative: it uses migration `0003`, two raw artifacts, one canonical
record, and one `static_altitude` association.

- Official GRIB2 URL: `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.grib2`
- Cycle and valid time: `2026-08-20T00:00:00Z`; lead `0` hours.
- Selected artifact: `3,276,049` bytes.
- SHA-256: `a9298ae22a556f3d4ec053f0a07c33bd3d2156cd130f5e09068090e079be2d48`.
- Actual parsed variables: `z`, `10u`, `10v`, `2t` (four GRIB2 messages).
- Requested coordinate `(27.9881, 86.9250)` selected provider grid point
  `(28.0, 87.0)`.
- DBRE ran the complete backend suite against an official pinned PostgreSQL
  disposable session at `localhost:46133`: `27 passed, 16 warnings`; all
  PostgreSQL tests ran. Migration `0003` was applied.
- The E2E run migrated to head, registered `ecmwf-ifs` as `planned`, and
  did not manually set evidence-bearing lifecycle states. The backend
  `WeatherIngestionService` then persisted `raw_artifact_count=2` and
  `weather_record_count=1`, plus `auxiliary_association_count=1` with role
  `static_altitude`. The dynamic artifact is primary; static `z` is auxiliary
  provenance only.
- Dynamic 3-hour artifact: `3,074,657` bytes, SHA-256
  `7d4b2feae148ade17a90b8168091d64d0f27b40ed55aa19530c48f49d53fdf9d`.
- Static 0-hour surface-`z` artifact: `896,851` bytes, SHA-256
  `529c14e03a8b22d86ff85e2bbd9d81c481ca626e410d1f6e8d875a112f4cb501`.
- Both artifacts use IFS cycle `2026-08-20T00:00:00Z`; the dynamic artifact is
  valid at `2026-08-20T03:00:00Z` with lead `10800` seconds.
- The backend persisted `registry_status=verified`, `health=healthy`, and
  `last_success_at=2026-08-20T18:40:28.274415+00:00` during that test.
- `GET /api/weather/forecast?source=ecmwf-ifs&start=2026-08-20T03:00:00Z&end=2026-08-20T03:00:00Z`
  returned HTTP `200` with exactly one persisted record at grid `(28.0, 87.0)`
  for requested coordinate `(27.9881, 86.9250)`: timestamp
  `2026-08-20T03:00:00Z`, cycle `2026-08-20T00:00:00Z`, lead `10800`, altitude
  `6008.053905863623 m`, temperature `-1.3635162353515398 C`, wind speed
  `0.8584101751271469 m/s`, wind direction `171.95415714345518 degrees`,
  precipitation `0.003814697265625 mm`, null visibility, and quality flag
  `[missing_value]`.
- The combined parse contained five GRIB messages: `z`, `tp`, `10u`, `10v`,
  and `2t`. Dynamic is primary; static `z` is auxiliary provenance only.
- The PostgreSQL container, volume, and listener were removed after the test.
  `verified` therefore records historical acceptance only; current runtime
  health and API availability are unknown and no live production claim is made.

| Field | ECMWF AIFS |
| --- | --- |
| `source_id` | `ecmwf-aifs` |
| `name` | ECMWF Artificial Intelligence Forecasting System (AIFS) |
| `provider` | European Centre for Medium-Range Weather Forecasts (ECMWF) |
| `category` | Forecast |
| `status` | `connected` (real official retrieval/parser/normalizer/adapter evidence; DB/API/QA still pending, so not `verified`) |
| `access_method` | Official ECMWF Open Data JSON-Lines `.index` with strict HTTP 206 byte ranges |
| `endpoint` | https://data.ecmwf.int/forecasts/20260821/00z/aifs-single/0p25/oper/ |
| `format` | GRIB2 |
| `update_frequency` | Runs at 00, 06, 12, and 18 UTC |
| `spatial_resolution` | Nominal 0.25 degrees |
| `temporal_resolution` | 6-hour forecast steps through 360 hours; retained sample lead 0 |
| `coverage` | Global Open Data grid; Everest request `(27.98806, 86.92528)` selected provider grid `(28.0, 87.0)` |
| `license` | CC BY 4.0 plus ECMWF terms; official documentation: https://www.ecmwf.int/en/forecasts/datasets/open-data |
| `commercial_allowed` | Yes under CC BY 4.0 plus ECMWF attribution/terms; deployment-specific legal approval not asserted |
| `credentials_required` | No for direct ECMWF Open Data retrieval used here; archive MARS is separate/restricted |
| `last_success_at` | `2026-08-21T10:09:58.234370+00:00` (connector-level retained retrieval only; not backend lifecycle success) |
| `last_failure_at` | `2026-08-21T10:16:03.8283828Z` (strict 6-hour complete-field request rejected because the official index had no unique surface `z`; no corrupt artifact was retained) |
| `health_status` | `unknown` (no continuously running service or backend health record) |

| Field | NOAA GFS |
| --- | --- |
| `source_id` | `noaa-gfs` |
| `name` | Global Forecast System (GFS) |
| `provider` | National Oceanic and Atmospheric Administration (NOAA), National Centers for Environmental Prediction (NCEP) |
| `category` | Forecast |
| `status` | `verified` (historical checked-in-adapter disposable E2E; not current runtime health) |
| `access_method` | Official NOAA/NCEP `.idx` metadata with HTTP 206 byte ranges |
| `endpoint` | https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod |
| `format` | GRIB2 |
| `update_frequency` | Runs at 00, 06, 12, and 18 UTC |
| `spatial_resolution` | Available 0.25, 0.5, and 1 degree grids |
| `temporal_resolution` | GFS `f###` lead; accepted sample lead 0 hours |
| `coverage` | Everest request `(27.9881, 86.9250)` mapped to provider grid `(28.0, 87.0)` |
| `license` | Public distribution; product-specific licensing terms not assessed in Phase A |
| `commercial_allowed` | Pending product-specific confirmation and policy review |
| `credentials_required` | Unknown; not assessed in Phase A |
| `last_success_at` | `2026-08-21T02:27:10.360839+00:00` (historical final disposable acceptance) |
| `last_failure_at` | `null` |
| `health_status` | `unknown` currently; historical disposable run reported `healthy` before teardown |

### NOAA GFS authoritative historical E2E evidence

This is the sole authoritative GFS E2E record. Earlier filter-HTTP-500-only,
pre-sidecar, pre-adapter, and port-`52370` executions are superseded historical
attempts; the filter failure remains only an alternative-path fact, not a
source failure.

- Official GRIB2 URL:
  `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000`
- Official index URL: the GRIB2 URL plus `.idx`.
- Dataset/model: `GFS pgrb2.0p25` / `GFS`; format `GRIB2`; cycle and valid
  time `2026-08-20T00:00:00Z`; lead `0` seconds.
- The corrected retained artifact is `2,937,483` bytes with SHA-256
  `9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`.
  Its canonical metadata sidecar SHA-256 is
  `f99e6967479a193def39c1bf80e364fcaea9ac39a4fb3ebaf2f97778e54eb9de`.
- After retention preverification, the checked-in
  `compose_gfs_ingestion_adapter` was used, rather than constructing a backend
  descriptor directly. The disposable database at temporary port `34034` ran
  migrations `0001`–`0003`, persisted `raw=1` and `record=1`, and created
  primary record ID `5b036b60-fe79-4e02-8681-a142b81b17e3`.
- The service generated `status=verified`, `health=healthy`, and
  `last_success_at=2026-08-21T02:27:10.360839+00:00`. The exact bounded
  `source=noaa-gfs` 00Z forecast query returned HTTP 200 with one record:
  latitude `27.9881`, longitude `86.925`, altitude `5917.819375 m`, temperature
  `-3.2432128906249886 C`, wind speed `2.081546755453268 m/s`, wind direction
  `235.34425831717988 degrees`, null precipitation/visibility, and
  `[missing_value]`.
- Historical backend-harness evidence is `29 passed, 20 warnings`, and the
  explicit checked-in adapter integration tests are `2 passed`. The disposable
  database and its resources were cleaned up. Thus `verified`/`healthy` are
  historical acceptance facts; current runtime health and API availability are
  `unknown`.

An earlier practical/full count (`35 passed`; `54 passed, 8 skipped`) is
superseded by the authoritative final result: `53 passed, 0 failed, 0 skipped`.

| Field | DWD ICON |
| --- | --- |
| `source_id` | `dwd-icon` |
| `name` | ICOsahedral Nonhydrostatic (ICON) |
| `provider` | Deutscher Wetterdienst (DWD) |
| `category` | Forecast |
| `status` | `verified` (historical disposable canonical-commit acceptance only; not a current production-service claim) |
| `access_method` | Official DWD Open Data individual bzip2-compressed global GRIB2 variable products, including DWD's CLAT/CLON native-grid products; no GRIB message inventory/index or safe byte-range product API was found on this route |
| `endpoint` | https://opendata.dwd.de/weather/nwp/icon/; GRIB directory: https://opendata.dwd.de/weather/nwp/icon/grib/ |
| `format` | GRIB2 |
| `update_frequency` | Runs at 00, 06, 12, and 18 UTC |
| `spatial_resolution` | Native global grid, approximately 13 km |
| `temporal_resolution` | Forecast lead encoded as the `NNN` product-filename field; accepted sample is lead 0 |
| `coverage` | Everest `(27.9881, 86.9250)` mapped to native grid `(27.926742553710938, 86.921875)` with DWD grid UUID `a27b8de618c411e4820ab5b098c6a5c0`, index `818403` |
| `license` | CC BY 4.0 with attribution |
| `commercial_allowed` | Unknown pending policy review |
| `credentials_required` | Unknown; not assessed in Phase A |
| `last_success_at` | `2026-08-21T03:59:32.333262+00:00` (persisted by the final disposable canonical-commit acceptance; not current live health) |
| `last_failure_at` | `2026-08-21T10:48:00Z` (prior exact 00 UTC dynamic-product HTTP 404) |
| `health_status` | `unknown` currently; the disposable database recorded `healthy` only after canonical commit and was then torn down |

### DWD ICON historical implementation and real-access evidence

This connector/parser evidence predates and is superseded for lifecycle purposes
by the final Gate C-Core/DBRE record below. It remains factual raw provenance,
but is not the authoritative status record. Historical `verified`/`healthy`
applies only to the later disposable canonical commit; current health remains
`unknown`, Gate C-Operational is incomplete, and no production claim is made.

`services/weather/icon/` is independent from ECMWF, GFS, and AIFS. It uses only
the official DWD Open Data host and retains decompressed GRIB2 payloads and
canonical JSON metadata in SHA-256 content-addressed directories. Metadata has
an immutable `metadata.json.sha256` sidecar; payload and sidecar are atomically
written, fsynced, rehashed on write and reuse, and made read-only on a
best-effort filesystem basis. The parser requires ecCodes, preserves
`gridType`, and normalizes explicit ICON `T_2M` Kelvin, `U_10M`/`V_10M` m/s, and
`HSURF` metre units. `HSURF` is DWD's provider-supplied time-invariant terrain
height and is never invented by the normalizer.

On 2026-08-21, the official directory listing was reachable through a direct
TLS connection and showed
`https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/` plus factual
`2026082000` lead-12 product listing entries. DWD publishes independent
compressed variable objects, not an official message index: the listed lead-12
temperature product was 2,973,836 bytes; listed U/V products were 3,929,812 and
3,941,274 bytes. The official static terrain object was retrieved successfully:
`https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2`, size
`1,313,525` compressed bytes. It was not treated as an accepted forecast raw
artifact because matching dynamic fields for a coherent run were not retained.

The original exact `2026082000` lead-12 request returned HTTP 404 despite its
listing. The retry used only exact hrefs from the observed official 12 UTC
listing. It successfully retrieved and retained these six separate objects for
cycle/valid time `2026-08-20T12:00:00Z`, lead `0`:

- `t_2m/...2026082012_000_T_2M.grib2.bz2` — 2,970,882 compressed bytes.
- `u_10m/...2026082012_000_U_10M.grib2.bz2` — 3,878,199 compressed bytes.
- `v_10m/...2026082012_000_V_10M.grib2.bz2` — 3,518,048 compressed bytes.
- `hsurf/...2026082012_HSURF.grib2.bz2` — 1,314,087 compressed bytes.
- `clat/...2026082012_CLAT.grib2.bz2` — 1,264,311 compressed bytes.
- `clon/...2026082012_CLON.grib2.bz2` — 1,398,271 compressed bytes.

The immutable decompressed six-message artifact is
`tmp-icon-real-20260821/dwd-icon/04cfe27cc6681ac1f8a685e882824fcdcc21e05ba5da1995d9963c67a9f56f21/icon_2026082012_000.grib2`.
It is 16,894,069 bytes with SHA-256
`04cfe27cc6681ac1f8a685e882824fcdcc21e05ba5da1995d9963c67a9f56f21`.
Its canonical `metadata.json` SHA-256 is
`e365ebcf9ae95723c3951bec813c04088c2bb0dd6719094a59b749ad6780ca79`, with the
required `metadata.json.sha256` sidecar in the same directory.

WSL ecCodes parsed six actual GRIB2 messages: `2t`, `10u`, `10v`, `HSURF`,
`tlat`, and `tlon`. The CLAT/CLON products decode as `tlat`/`tlon` and provide
the required native unstructured-grid coordinate arrays. At requested Everest
coordinate `(27.9881, 86.9250)`, the selected provider grid is
`(27.926742553710938, 86.921875)`, grid UUID
`a27b8de618c411e4820ab5b098c6a5c0`, point index `818403`, spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. Canonical normalization produced
altitude `5830.964752197266 m`, temperature `0.32810363769533524 C`, wind speed
`3.5184451983214364 m/s`, wind direction `254.03374128644649 degrees`, null
precipitation/visibility, and additive `[missing_value]` QC.

The then-DBRE-ready descriptor was `dataset=ICON global`, object reference equal
to the artifact path above, source ID `dwd-icon`, model `ICON`, format `GRIB2`,
size `16894069`, SHA-256 as above, retrieval time
`2026-08-21T02:56:40.309778+00:00`, forecast cycle/valid time
`2026-08-20T12:00:00Z`, lead `0`, and the six-URL raw metadata in the retained
canonical sidecar. The statement that DBRE had not run was true at that stage
but is superseded by the final approved-root Gate C-Core/DBRE record below. This
older project-root artifact is not the artifact used by that final execution.

### EV-DATA-001-E-RAW-APPROVED fresh raw sample (2026-08-21)

**Assignment:** `EV-DATA-001-E-RAW-APPROVED`  
**Outcome:** Real DWD retrieval, immutable retention, ecCodes parsing, and
canonical normalization succeeded. This assignment itself did **not** execute
database persistence or an API. A later disposable DBRE execution used this
approved-root artifact and is recorded below; current operational
`health_status` remains `unknown` after teardown.

The connector ran only with `EVEREST_RAW_ROOT=D:\Everest-data\raw`; it has no
repository-root fallback. It resolved each requested product by first reading
the current official DWD directory listing and accepting only the exact
advertised href. The source objects are individually compressed global ICON
fields, which are the smallest official objects available on this route; the
selected native point is inside the approved expanded 2,000 km AOI.

| Retention/provenance field | Actual value |
| --- | --- |
| Retrieval UTC | `2026-08-21T03:59:32.333262+00:00` |
| AOI scalar metadata | `aoi_id=everest-south-route`; `aoi_version=everest-south-route-v1.0`; `aoi_scope_id=everest-south-route-v1.0-expanded-2000km` |
| Requested WGS 84 coordinate | `27.98806, 86.92528` |
| Forecast cycle / lead / valid UTC | `2026-08-21T00:00:00Z` / `0` hours / `2026-08-21T00:00:00Z` |
| Retained GRIB2 path | `D:\Everest-data\raw\dwd-icon\e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57\icon_2026082100_000.grib2` |
| Decompressed payload size / SHA-256 | `17,624,861` bytes / `e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57` |
| Aggregate compressed source size | `15,077,090` bytes |
| Metadata path / SHA-256 | same directory `metadata.json` / `cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf` |
| Mandatory metadata integrity sidecar | same directory `metadata.json.sha256`; its exact text is the metadata SHA-256 above; sidecar payload SHA-256 is `0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46` |

Exact current official hrefs and compressed sizes, in the fixed retained field
order `T_2M`, `U_10M`, `V_10M`, `HSURF`, `CLAT`, `CLON`, are:

1. `https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/icon_global_icosahedral_single-level_2026082100_000_T_2M.grib2.bz2` — `3,338,757` compressed / `3,323,939` decompressed bytes.
2. `https://opendata.dwd.de/weather/nwp/icon/grib/00/u_10m/icon_global_icosahedral_single-level_2026082100_000_U_10M.grib2.bz2` — `3,876,736` compressed / `3,860,511` decompressed bytes.
3. `https://opendata.dwd.de/weather/nwp/icon/grib/00/v_10m/icon_global_icosahedral_single-level_2026082100_000_V_10M.grib2.bz2` — `3,885,537` compressed / `3,870,728` decompressed bytes.
4. `https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2` — `1,313,525` compressed / `1,369,453` decompressed bytes.
5. `https://opendata.dwd.de/weather/nwp/icon/grib/00/clat/icon_global_icosahedral_time-invariant_2026082100_CLAT.grib2.bz2` — `1,264,300` compressed / `2,574,603` decompressed bytes.
6. `https://opendata.dwd.de/weather/nwp/icon/grib/00/clon/icon_global_icosahedral_time-invariant_2026082100_CLON.grib2.bz2` — `1,398,235` compressed / `2,625,627` decompressed bytes.

WSL ecCodes `2.47.1` read six actual messages (`2t`, `10u`, `10v`, `HSURF`,
`tlat`, `tlon`) of `2,949,120` values each. DWD's `CLAT`/`CLON` files decode as
`tlat`/`tlon`; all six messages declare `unstructured_grid` and grid UUID
`a27b8de618c411e4820ab5b098c6a5c0`. Nearest-point selection returned native
coordinate `27.926742553710938, 86.921875`, index `818403`, and spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`.

Canonical values at that point are altitude `5830.964752197266 m`, temperature
`-3.3708862304687273 C`, wind speed `2.0440636678148207 m/s`, and wind
direction `286.0613838292081 degrees`; precipitation and visibility are null.
Additive QC is `[missing_value]`, solely because this approved six-field sample
does not include those two canonical fields. No data was fabricated, deleted,
or persisted beyond the immutable approved-root raw artifact.

## Phase A Validation Constraints

- Only the four approved forecast sources above are registered.
- ECMWF IFS is `verified` only as historical evidence of the documented
  disposable end-to-end acceptance test. Its current runtime `health_status` is
  `unknown` after teardown and it does not represent a continuously healthy or
  live production source.
- NOAA GFS is `verified` only as historical evidence of the authoritative
  checked-in-adapter disposable E2E record above. Its historical database health
  was `healthy`, but the database, listener, and container were removed;
  therefore current `health_status` and API availability are `unknown`.
- AIFS is `connected` by the Phase F retained retrieval/parser/normalizer/adapter
  evidence above, but remains unverified pending DB/API/QA. ICON has historical
  disposable `verified`/`healthy` acceptance only after the final canonical
  commit documented below. The listener and database were removed, so current
  ICON `health_status` and API availability are `unknown`. Gate C-Operational
  and production acceptance remain incomplete.
- Fields for AIFS and ICON marked unknown require official-source confirmation
  during their assigned future phase; they are not assumptions or placeholders
  for success.

### EV-DATA-001-E-ROOT-SMOKE

The current connector ran with `EVEREST_RAW_ROOT=D:\\Everest-data\\raw`.
This assignment was raw-retention only: it did not invoke backend, PostgreSQL,
API, or lifecycle changes. Its retained artifact was used later by the final
disposable DBRE execution below. Retrieval UTC was
`2026-08-21T03:59:32.333262Z`; independent integrity
and containment checks ran at `2026-08-21T04:12:21.662491Z`. Old project-root
`tmp-icon*` artifacts were not inspected or used. AOI scalars were
`aoi_id=everest-south-route`, `aoi_version=everest-south-route-v1.0`, and
`aoi_scope_id=everest-south-route-v1.0-expanded-2000km`. Cycle/lead/valid were
`2026-08-21T00:00:00Z` / `0` hours / `2026-08-21T00:00:00Z`.

Retention owner/class/period/disposition were `Everest Manager` /
`operational_raw` / `24 months from acquisition` / controlled disposition after
expiry and hold checks, not automatic deletion, currently retained/not disposed.
The payload was retained at
`D:\\Everest-data\\raw\\dwd-icon\\e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57\\icon_2026082100_000.grib2`,
`17,624,861` bytes, SHA-256
`e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57`.
Sibling metadata was `1,392` bytes, SHA-256
`cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf`; sibling
sidecar was `65` bytes, file SHA-256
`0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46`, with a
matching declared metadata digest. All three paths resolved beneath the root
and shared one artifact directory.

The exact official hrefs and compressed/decompressed bytes were: `T_2M`
`https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/icon_global_icosahedral_single-level_2026082100_000_T_2M.grib2.bz2` (`3,338,757`/`3,323,939`); `U_10M` `https://opendata.dwd.de/weather/nwp/icon/grib/00/u_10m/icon_global_icosahedral_single-level_2026082100_000_U_10M.grib2.bz2` (`3,876,736`/`3,860,511`); `V_10M` `https://opendata.dwd.de/weather/nwp/icon/grib/00/v_10m/icon_global_icosahedral_single-level_2026082100_000_V_10M.grib2.bz2` (`3,885,537`/`3,870,728`); `HSURF` `https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2` (`1,313,525`/`1,369,453`); `CLAT` `https://opendata.dwd.de/weather/nwp/icon/grib/00/clat/icon_global_icosahedral_time-invariant_2026082100_CLAT.grib2.bz2` (`1,264,300`/`2,574,603`); `CLON` `https://opendata.dwd.de/weather/nwp/icon/grib/00/clon/icon_global_icosahedral_time-invariant_2026082100_CLON.grib2.bz2` (`1,398,235`/`2,625,627`).

WSL ecCodes `2.47.1` parsed six messages with `2,949,120` values each. Native
point was `(27.926742553710938,86.921875)`, UUID
`a27b8de618c411e4820ab5b098c6a5c0`, index `818403`; normalized values were
altitude `5830.964752197266 m`, temperature `-3.3708862304687273 C`, wind
speed `2.0440636678148207 m/s`, direction `286.0613838292081 degrees`, null
precipitation/visibility, QC `[missing_value]`. The earlier ICON semantic suite
reported `42 passed`; that count is superseded by the final `53 passed, 0 failed, 0 skipped` full suite
and `2/2` ICON DBRE/API tests below. Black and compileall passed. Pylint exited
non-zero at `9.11/10` because the external `weather_ingestion_contract` import
was unavailable in that earlier environment. Those older raw-smoke results are
historical evidence by themselves.

### EV-DATA-001-E-ICON-DOCS-FINAL historical predecessor evidence

> **Historical notice:** The 53-pass/port-47189 execution below was an accepted
> predecessor, but the authoritative post-review evidence is now the 58/58,
> ICON-2/2 execution on disposable port `46583` recorded at the top of this
> document. Older counts and blocker statements are chronology only.

The final controlled DBRE execution used the approved external raw root and the
checked-in ICON adapter. It applied migrations `0001`–`0006` on a disposable,
pinned PostgreSQL listener at `localhost:47189`. The full suite passed
`53 passed, 0 failed, 0 skipped`; focused ICON PostgreSQL/API integration tests
passed `2/2`. The successful path persisted exactly `raw=1`, `record=1`, and
`audit=1`. This final record supersedes the earlier `49/49`/port-`53112`
record.

The accepted approved-root artifact remained at
`D:\Everest-data\raw\dwd-icon\e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57\icon_2026082100_000.grib2`:

- payload: `17,624,861` bytes; SHA-256
  `e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57`;
- canonical `metadata.json`: `1,392` bytes; SHA-256
  `cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf`;
- `metadata.json.sha256`: `65` bytes; file SHA-256
  `0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46`,
  declaring the matching metadata digest.

The persisted retention facts were owner `Everest Manager`, class
`operational_raw`, policy version `2026-08-21.v1`, period `24 months from
acquisition`, state `retained`, and hold state `none` (not held); a due date was
persisted. Disposition remains controlled: expiry and hold checks plus explicit
approval are required, and teardown did not delete or shorten retention of the
approved-root artifact.

Only after the canonical transaction committed did the disposable registry row
become `verified`/`healthy`, with `last_success_at` equal to
`2026-08-21T03:59:32.333262+00:00`. The bounded
`GET /api/weather/forecast?source=dwd-icon` request then returned HTTP `200` and
exactly one record with source/model `dwd-icon`/`ICON`, timestamp and forecast
cycle `2026-08-21T00:00:00Z`, lead `0`, native spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`, latitude
`27.926742553710938`, longitude `86.921875`, altitude `5830.964752197266 m`,
temperature `-3.3708862304687273 C`, wind speed `2.0440636678148207 m/s`, wind
direction `286.0613838292081 degrees`, null precipitation/visibility, and
`[missing_value]`. The public response leaked no approved-root path, provider
URL, payload hash, raw metadata, retention, hold, disposition, or audit fields.

The negative raw-first test forced canonical persistence failure after raw
acceptance. It retained one classified raw artifact, persisted no canonical
record, and left lifecycle/health at `configured`/`unknown`; there was no false
escalation to `verified`/`healthy`.

The preceding failed API acceptance run omitted `spatial_key` from the shared
public response projection. The same identifiable defect had occurrence count
`2`. The corrected projection preserves the persisted native UUID/index key and
the final successful run above supersedes that failed run; the occurrence count
is retained rather than reset.

After the successful execution, the disposable database, container/volume,
temporary listener, and port `47189` resources were cleaned up. Therefore
`verified` and `healthy` are historical disposable acceptance facts only.
Current ICON runtime health and API availability are `unknown`. Gate C-Core/DBRE
evidence is complete, but Gate C-Operational remains incomplete; no live,
continuous, or production ICON service is claimed. AIFS was not started.
