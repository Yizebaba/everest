# Everest API Contract

## Phase C status

Phase A reserved contracts and implemented no HTTP routes. That sentence is
historical. HEAD implements the five weather/health routes plus terrain,
observations, satellite, Everest route, `/healthz`, and `/readyz` (see
Implemented routes below). Controllers still call the registry application
service, never repositories or external providers directly. No endpoint may
claim source verification or health without operational evidence.

All future responses use UTF-8 JSON, UTC ISO-8601 timestamps, and an optional
`X-Correlation-ID` request header echoed in responses and structured logs.
Errors must be `{ "error": { "code": "...", "message": "...",
"correlation_id": "..." } }`; responses must never expose credentials,
credential-reference values, tokens, or unbounded failure details.

The API retains a caller-supplied `X-Correlation-ID` only when it is 1--128
characters from the bounded ASCII set `A-Z`, `a-z`, `0-9`, `.`, `_`, `:`, and
`-`; otherwise it generates an opaque ID. The selected ID is returned in both
the response header and every error envelope. Request validation uses code
`VALIDATION_ERROR` with HTTP 422; unexpected failures use
`INTERNAL_SERVER_ERROR` with HTTP 500 and never return exception details.

Local browser CORS is configuration-driven by the comma-separated
`EVEREST_CORS_ALLOWED_ORIGINS` environment value. Its safe development default
allows exactly `http://localhost:42420` and `http://localhost:52148` (the
current frontend runtime after ADR-020). Only `GET` and
preflight `OPTIONS` are allowed, credentials are disabled, request
`X-Correlation-ID` is allowed, and response `X-Correlation-ID` is exposed. No
origin wildcard is accepted.

Implementation references consulted for `EV-UI-001-INTEGRATION-FIX-BE`:

- FastAPI, **CORS (Cross-Origin Resource Sharing)**:
  <https://fastapi.tiangolo.com/tutorial/cors/>
- FastAPI, **Handling Errors**:
  <https://fastapi.tiangolo.com/tutorial/handling-errors/>
- FastAPI, **JSON Compatible Encoder**:
  <https://fastapi.tiangolo.com/tutorial/encoder/>

## Runtime raw-storage configuration

Raw retention is configured only in the backend process environment. A runtime
that composes `WeatherIngestionService` must require `EVEREST_RAW_ROOT` and
construct `RawStoragePolicy` from it before exposing ingestion. The value must
resolve to an existing absolute directory outside the resolved repository root;
missing, relative, unavailable, repository-contained, or escaping paths fail
closed. The API does not expose this setting, raw object references, raw URLs,
or raw metadata.

The persistence edge verifies the payload before inserting a database row: it
must be a regular, non-symlink file beneath the approved root and its SHA-256
must match the descriptor. This is a read/hash check only; it does not acquire,
write, move, copy, or delete raw artifacts. Metadata and checksum-sidecar
verification remains provider-owned. Provider attestations crossing this
boundary must be scalar descriptor metadata, never provider objects. Filesystem
access control and physical disposition remain storage-owner controls. The
2026-08-22 snapshot had no Git metadata. This checkout has `.git` and remote
`Yizebaba/everest`; repository-exclusion evidence is recorded under GIT-003
and Gate C-Operational, not claimed by this contract.

## Raw retention and audit (internal only)

Migrations `20260821_0004` through corrective `20260821_0006` add backend
retention facts to every raw artifact, correct trigger dispatch, and use a
PostgreSQL-valid text comparison for immutable JSON metadata.
Existing rows are explicitly `legacy_unclassified`; their owner, period,
acquisition, and due-date facts are intentionally not invented. New accepted
rows receive a backend `RetentionDecision` using the approved defaults:
`operational_raw` for 24 months, `failed_or_rejected_raw` for 180 days, and
policy version `2026-08-21.v1`. Provider adapters pass only factual scalar
metadata.

`raw_artifact_audit_event` is append-only and records bounded, controlled event
types, result, actor identity/role, correlation ID, event time, details, and an
audit due date. Database triggers prevent updates/deletes. Internal service
methods support acceptance/reuse, internal read, integrity-failure, access-change,
hold, and disposition audit events and retention state transitions;
disposition fails closed for missing, unknown, or held state.
Completion additionally requires an expired persisted artifact, a prior audited
approval, and persisted `none` or audited `released` hold state. Hold release
and completion are separate calls.

The actor/role is an authorization boundary input. Deployment IAM must
authenticate and authorize it; this local package validates the allowed role
shape but does **not** claim ACL or filesystem permission enforcement. No
operator retention API is public, and public responses do not expose raw
references, retention details, hold details, or audit events.

Runtime retention model implementation is present. The authoritative post-review
evidence below closes **Gate C-Core** for the controlled disposable Phase E run.
**Gate C-Operational remains open** for IAM/ACL, legal authority, WORM or
equivalent privileged-write resistance, production audit, and authoritative Git
exclusion/history evidence. Existing `tmp-*` raw artifacts were not read or
operated on.

## Reserved endpoints

### `GET /api/data-sources`

Reserved for paginated, read-only registry metadata. The eventual contract will
return source identity, non-secret descriptive metadata, lifecycle `status`,
and `health_status`. Lifecycle status is one of `planned`, `configured`,
`connected`, `verified`, `degraded`, or `disabled`; it is not derived from
health. In Phase A, routine registry commands may set only `planned`,
`configured`, `degraded`, or `disabled`; `connected` and `verified` remain
reserved for a future connector-evidence workflow and cannot be claimed by the
Phase A service.

### `GET /api/data-health`

Reserved for read-only operational health. It will report only persisted
evidence such as health status and last success/failure timestamps. Presence in
the registry does not imply `connected`, `verified`, or `healthy`.

Phase C registers read-only PostgreSQL-backed routes. They never invoke a
connector, parser, or external provider. Source health and lifecycle values are
persisted facts: a registry entry alone is not verification evidence.

### `GET /api/weather/current`

Returns up to 100 persisted canonical records in descending valid-time order.
Optional `source` filters on the stable source identifier. Response body is
`{ "records": [CanonicalWeatherRecord] }`.

### `GET /api/weather/forecast`

Returns persisted `forecast` records ordered by valid time. Optional UTC
`start`, `end`, and `source` filters are supported. When supplied, `start` and
`end` must be RFC 3339 timezone-aware datetimes with an explicit zero offset
(`Z` or `+00:00`). Naive values and non-UTC offsets are rejected with HTTP 422;
the server never converts them using its local environment. `start > end` is
also rejected with HTTP 422. Response body is
`{ "records": [CanonicalWeatherRecord] }`.

### `GET /api/weather/profile`

Requires `profile` from exactly `EBC`, `C1`, `C2`, `C3`, `C4`, or `SUMMIT`
(case-insensitive). Unsupported values return HTTP 422. The service filters
only connector-supplied profile labels and never synthesizes route coordinates
or altitudes. Response body is `{ "profile": "...", "records": [...] }`.

### `GET /api/weather/sources`

Returns `{ "sources": [...] }` containing source ID, lifecycle status,
operational health status, and last persisted success time. It intentionally
excludes endpoints, credential references, and raw metadata.

### `GET /api/data-health`

Returns `{ "sources": [...] }` with source ID, persisted health status, and
last success/failure times. It does not infer healthy or verified from source
presence.

`CanonicalWeatherRecord` preserves the Phase B core units and includes
`record_type`, `timestamp`, coordinate/altitude, core meteorology values,
`spatial_key`, `source`, `model`, forecast identity, and additive
`quality_flags`. Public current/forecast/profile records also serialize
persisted `relative_humidity` (nullable; never invented). `spatial_key` is
the canonical provider grid-cell or stable station/pixel identity required
for provenance and deduplication; it is not a raw-storage reference.
Datetimes are emitted as UTC ISO-8601 `Z` values.

## Implemented routes (HEAD, 2026-08-27)

Live FastAPI GET routes in `apps/api/everest_api/app.py`, in addition to the
five weather/health contracts above:

| Route | Purpose |
| --- | --- |
| `GET /api/terrain/tile` | AOI terrain tile metadata (`min_elevation`, `max_elevation`, bounds, CRS) |
| `GET /api/observations/current` | Current observation records (includes `relative_humidity`) |
| `GET /api/satellite/segments` | Satellite segment listing; optional `band` filter |
| `GET /api/everest/route` | OSM South Col route polyline and camp points (EV-OSM-002) |
| `GET /api/risk/summit-window` | Read-only assessment from the existing Python Risk Engine using the newest persisted SUMMIT basis |
| `GET /api/weather/wind-field` | Latest integrity-checked, AOI-bounded derived U/V frame; explicit unavailable response when not materialized |
| `GET /healthz` | Process liveness |
| `GET /readyz` | Readiness (database reachable) |

CORS default origins remain `http://localhost:42420` and
`http://localhost:52148`. The frontend Cesium scene may use a local
NaturalEarthII TMS under `/cesium/` as an offline basemap fallback; that is
not an Everest REST route.

The same canonical response projection is used by current, forecast, and
profile records. Its explicit public allow-list excludes record/raw object
identifiers, dataset/raw paths, provider URLs, hashes, raw metadata, retention,
hold, disposition, and audit fields.

`/api/weather/wind-field` is an additive visualization projection and is not a
new canonical weather contract or ADR-015 evidence route. The GET handler never
contacts a provider or decodes GRIB. The scheduler derives a native-grid 400 hPa
frame from an already retained IFS pressure artifact with `cfgrib`/`xarray`,
clips it to the approved 100 km AOI envelope without interpolation, and
publishes it atomically under the configured external derived root.

`/api/risk/summit-window` reads PostgreSQL only and calls
`services/risk/engine.py`. Its `go`, `caution`, `block`, and `unknown` values are
the backend engine contract; the frontend may localize `block` as `STOP` but
must not rescore weather independently.

## ADR-015 retained endpoint evidence inventory

**Assignment:** `EV-DATA-001-ADR015-EVIDENCE-INVENTORY-BE`  
**Inventory date:** 2026-08-22  
**Method:** read-only repository inventory; no database, API, provider, test, or
raw-artifact operation was performed

ADR-015 requires historical real-data evidence for each of the five A-F
display routes. The inventory searched the retained source and build copies,
tests, documentation, management/QA handoffs, pytest caches, and available
workspace output/cache paths. No standalone request log, captured response
body, JUnit report, coverage report, or other execution-output artifact was
found. Pytest `nodeids` caches prove test discovery only; they do not prove a
test passed or identify the data behind an invocation.

The classifications below are deliberately separate:

- **Fake-session HTTP** means FastAPI `TestClient` was invoked, but
  `_FakeSession` returned a transient, hard-coded ORM-shaped object and no
  PostgreSQL query occurred.
- **Synthetic PostgreSQL fixture** means a disposable PostgreSQL test persisted
  deterministic test bytes and/or caller-constructed canonical values; those
  values may reproduce documented provider values but do not make the payload
  a retained provider artifact.
- **Retained-real integration** means retained provider bytes were decoded,
  normalized, committed to disposable PostgreSQL, and then queried over HTTP.
- **Direct DB assertion** proves persisted rows or lifecycle facts but is not an
  HTTP invocation.
- **Historical handoff statement** is retained documentation of an earlier
  execution when its original request log/body is no longer present.

### Endpoint evidence matrix

| Required route | Fake-session HTTP | Synthetic PostgreSQL fixture / direct DB | Retained-real integration and historical HTTP evidence | ADR-015 exact retained-evidence finding |
| --- | --- | --- | --- | --- |
| `GET /api/weather/current` | **Yes, HTTP 200 only against fake data.** `apps/api/tests/test_weather_api.py::test_weather_responses_include_spatial_key_without_private_fields` invokes `/api/weather/current?source=dwd-icon`; `_FakeSession` returns `_weather_record()`, a transient hard-coded ICON-shaped object, without a database. Root and `apps/api` pytest `nodeids` retain the case name but not a pass result or response artifact. | **No HTTP invocation found.** PostgreSQL persistence tests contain synthetic canonical rows and direct DB assertions, but none calls this route. | **Not found.** No retained-real test, request log, response body, or endpoint-specific handoff states that this route returned real persisted provider records. | **NOT EVIDENCED for the required real persisted HTTP path.** Route implementation exists at `apps/api/everest_api/app.py::current`; implementation is not execution evidence. |
| `GET /api/weather/forecast` | **Yes, HTTP 200 against fake data.** The shared fake-session test invokes the route, and UTC validation tests also use `_FakeSession`; neither is real-data or PostgreSQL evidence. | **Yes, but synthetic.** `apps/api/tests/test_gfs_adapter_integration.py::test_gfs_adapter_persists_factual_record_and_public_forecast` writes `synthetic-gfs-composition-fixture`, constructs canonical values, asserts PostgreSQL `raw=1`/`record=1`, then invokes `/api/weather/forecast?source=noaa-gfs` and asserts HTTP 200. IFS persistence tests in `test_weather_persistence.py` directly assert synthetic PostgreSQL rows but do not invoke HTTP. | **Yes.** Checked-in retained-real tests decode provider bytes, assert committed PostgreSQL rows, and invoke HTTP 200 for ICON (`test_icon_adapter_integration.py::test_retained_icon_grib_to_postgres_and_public_forecast`) and AIFS (`test_aifs_adapter_integration.py::test_retained_aifs_grib_to_postgres_and_bounded_public_forecast`). Historical handoffs record HTTP 200 over persisted real records for IFS (`docs/data-sources.md`, “ECMWF IFS historical evidence”; `docs/meteorology/weather-spec.md`, “Historical disposable E2E acceptance evidence”), GFS (the “authoritative historical E2E evidence” sections in those handoffs), ICON (this document's authoritative post-review section), and AIFS (this document's authoritative hardened section). Original IFS/GFS request logs and response bodies were not found. | **EVIDENCED historically.** Strongest retained executable evidence is ICON/AIFS; IFS/GFS are retained handoff statements rather than surviving original execution output. All are historical disposable facts, not current availability. |
| `GET /api/weather/profile` | **Yes, HTTP 200 only against fake data.** The shared test invokes `/api/weather/profile?profile=summit` against `_FakeSession`, whose transient object hard-codes `route_profile="SUMMIT"`. The unsupported-label HTTP 422 test is also fake-session contract evidence. | **Direct DB only; no endpoint invocation found.** Synthetic IFS persistence inputs use `route_profile="SUMMIT"`, but their tests do not call the profile route. | **Not found.** ICON, GFS, and AIFS provider adapters default `route_profile` to null, and the retained-real ICON/AIFS integrations call only forecast. No retained artifact, handoff, request log, or body proves profile HTTP returned a real persisted provider record. | **NOT EVIDENCED for the required real persisted HTTP path.** Label validation and serializer behavior are evidenced, but real-data HTTP invocation is not. |
| `GET /api/weather/sources` | **No invocation found.** | **No invocation found.** Provider integration tests directly assert registry rows and historical `verified`/`healthy` promotion after canonical commit; those are DB assertions, not HTTP. | **Not found.** Handoffs list the route and describe lifecycle facts but do not state that this exact endpoint was invoked or retain an HTTP status/body. | **NOT EVIDENCED.** Route implementation exists at `apps/api/everest_api/app.py::sources`; source presence and direct DB assertions cannot be upgraded to endpoint evidence. |
| `GET /api/data-health` | **No invocation found.** | **No invocation found.** Direct DB lifecycle/health assertions exist in GFS, ICON, and AIFS integration tests, but no test calls this route. | **Not found.** No endpoint-specific historical HTTP status, request log, or response artifact was retained. | **NOT EVIDENCED.** Route implementation exists at `apps/api/everest_api/app.py::data_health`; persisted health facts alone are not HTTP evidence. |

This matrix narrows the broader statement in
`docs/management/phase-f-report.md` under “API Evidence”: that section lists all
five implemented routes but supplies exact historical HTTP results only for
forecast. Route existence, a common serializer, direct database assertions, or
a test-discovery cache must not be interpreted as proof that all five routes
were historically invoked against real persisted records.

### Profile-label and geometry semantics

The accepted filter vocabulary is case-insensitive `EBC`, `C1`, `C2`, `C3`,
`C4`, and `SUMMIT`; the API normalizes a supplied label and filters only the
persisted `route_profile` column. These are filter labels, not coordinates,
altitudes, route geometry, or permission for a connector to assign a camp by
proximity. Connectors and the API must not invent EBC-to-C4 or Summit geometry.

For A-F, ADR-015 accepts provider records whose `route_profile` is null, or a
dataset containing only a factual connector-supplied `SUMMIT` label; complete
EBC/C1/C2/C3/C4-labelled records are non-blocking. A null label does not match a
named profile query, so it can legitimately produce an empty profile result.
The fake-session Summit test proves label filtering/serialization only. It does
not establish that any real provider record carried a factual Summit label or
that the profile endpoint historically returned real data.

### Availability and conclusion

All cited provider databases/listeners were disposable and were torn down.
Current database health, runtime health, and availability of every route are
**unknown**. The inventory found qualifying historical real-persisted HTTP
evidence only for `/api/weather/forecast`; it did **not** find qualifying exact
retained evidence for `/api/weather/current`, `/api/weather/profile`,
`/api/weather/sources`, or `/api/data-health`. This is an evidence-gap finding,
not a claim that those implementations fail and not authorization to rerun a
database or API solely to fill the gap.

## UTC query validation references

For `EV-DATA-001-F-REVIEW-FIX-UTC-API`, the backend consulted the current
official validation documentation before changing the forecast query contract:

- FastAPI, **Query Parameters and String Validations**:
  <https://fastapi.tiangolo.com/tutorial/query-params-str-validations/>
- Pydantic, **Standard Library Types — Datetimes**:
  <https://docs.pydantic.dev/latest/api/standard_library_types/#datetimes>

FastAPI documents custom `AfterValidator` validation in `Annotated` query
parameters, and Pydantic documents RFC 3339 parsing plus timezone-aware
datetime validation. The API adds the stricter project rule that the parsed
offset must be exactly zero; it rejects rather than normalizes naive or
non-UTC input.

## Response serialization references and spatial-key correction

For `EV-DATA-001-E-API-SPATIAL-KEY-FIX`, the backend consulted the current
official response-serialization documentation before editing:

- FastAPI, **Response Model - Return Type**:
  <https://fastapi.tiangolo.com/tutorial/response-model/>
- Pydantic, **Serialization**:
  <https://docs.pydantic.dev/latest/concepts/serialization/>

FastAPI documents that declared output contracts validate, document, serialize,
and—critically for security—filter response data. Pydantic documents explicit
field inclusion/exclusion and schema-directed serialization. The backend keeps
an explicit canonical allow-list rather than serializing SQLAlchemy objects or
runtime attributes wholesale.

The exact defect occurred twice: the persisted, required
`WeatherRecordModel.spatial_key` was available to the query layer but omitted
from the shared `records_payload()` dictionary projection, so forecast output
lost canonical spatial provenance. Because current, forecast, and profile all
use that projection, the correction adds `spatial_key` there once and focused
non-database API contract tests enforce its presence on all three views while
enforcing the private-field exclusion boundary.

## Connector-to-backend executable handoff

The meteorology connector must invoke the backend application port using the
owner-neutral `weather_ingestion_contract` package:
`WeatherIngestionService.ingest(RawArtifactDescriptor,
Sequence[CanonicalRecordInput], auxiliary_artifacts=())`.
The shared DTOs are primitive descriptors and deliberately
import neither ecCodes nor connector/parser/HTTP types. The connector supplies
the raw object reference, SHA-256, retrieval metadata, provider spatial key,
and already normalized canonical values. The API commits the raw artifact before
canonical persistence; a downstream failure leaves it retained and cannot mark
the source verified. Only a transaction that persists at least one canonical
record updates its source to `verified`/`healthy` with `last_success_at`.

Auxiliary raw provenance (including a same-cycle static-altitude artifact) is
internal-only. It is retained in append-only persistence associations but is
never emitted in public weather, source, or health responses; raw object
references, raw URLs, and raw metadata remain private.

The backend no longer defines duplicate primary-artifact or canonical-record
DTOs. `everest_api.weather.contracts` re-exports the shared types for safe
transition, and retains only the deprecated `StaticAltitudeArtifactReference`
wrapper. New callers must use `AuxiliaryArtifactReference(role='static_altitude',
artifact=...)`; the wrapper is translated at the backend edge and does not
change persistence, deduplication, lifecycle, health, or response semantics.
The API distribution declares `weather-ingestion-contract==0.1.0`. Because the
contract is a workspace package rather than a published dependency, local
backend setup must use `apps/api/requirements-local.txt`; it installs the
contract first and the API second. Meteorology-only setup uses
`services/weather/requirements-local.txt`, which installs only the shared
contract and leaves backend ownership out of the environment. These local
requirements files are installation configuration only; they do not change
the distribution metadata or contract semantics.

## Offline AIFS PostgreSQL/API integration test prerequisites (historical)

Assignment `EV-DATA-001-F-AIFS-INTEGRATION` adds a checked-in, network-forbidden
backend integration test analogous to the final ICON path. It does not change a
provider connector, retrieve external data, execute a database during
implementation, or change persisted/runtime source status. The test requires:

- `EVEREST_RAW_ROOT` set to the existing absolute external raw root containing
  the approved retained AIFS payload, canonical `metadata.json`, and mandatory
  `metadata.json.sha256` sidecar under the exact `ecmwf-aifs` content-addressed
  object reference;
- a compatible native ecCodes runtime and Python binding capable of decoding
  AIFS Single v2 GRIB2 (ECMWF recommends ecCodes 2.46.0 for AIFS Single v2); and
- `EVEREST_TEST_DATABASE_URL` naming a disposable PostgreSQL database on which
  Alembic may apply and downgrade revisions `20260821_0001` through
  `20260821_0006`. SQLite is intentionally rejected.

Absent environment prerequisites produce explicit skips. Once files are
present, a changed retained payload, metadata, sidecar, size, hash, model, or
provenance is a failure rather than a skip. The positive test parses five real
messages, normalizes and adapts them, and—when executed with PostgreSQL—requires
exactly `raw=1`, `record=1`, and `audit=1` before querying a bounded forecast
window. Public output must retain separate `source=ecmwf-aifs` and `model=AIFS`
comparison fields while excluding raw paths, URLs, hashes, retention, and audit
facts. Negative tests reject IFS/AIFS conflation before raw persistence and
prove raw-first retention with no lifecycle/health promotion after canonical
database rejection. These are executable acceptance conditions, not current
DB/API execution evidence or a live `verified`/`healthy` claim. This older
test-prerequisite/no-execution record is retained for chronology only.

## Authoritative hardened AIFS DBRE/API acceptance evidence

**Assignment:** `EV-DATA-001-F-API-DOC-CLOSE`  
**Evidence type:** controlled disposable PostgreSQL DBRE execution; historical
execution evidence, not current service health

This is the authoritative AIFS API handoff. The complete `apps/api` result was
**66 passed, 0 failed, 0 skipped** (`full66/0/0`). Focused AIFS coverage was
**4 passed, 0 failed, 0 skipped** (`AIFS4/0/0`), and focused meteorology AIFS
coverage was **37 passed, 0 failed, 0 skipped** (`meteorology37/0/0`). The run
used pinned disposable PostgreSQL on non-standard localhost port **`46901`**
and applied migrations **`0001` through `0006`** without a revision gap.
Older `61/3`, `61/61`, `63/2`, and port `44859` records, including failed
records, are historical chronology and are superseded by this result.

The successful run used the accepted direct-argv/reviewed wrapper procedure;
the prior PowerShell-to-WSL nested-wrapper incident did not recur. Its
residual evidence limitation is recorded in
[`EV-DATA-001-F-INCIDENT-001`](../management/decisions.md#ev-data-001-f-incident-001):
the three historical failed invocations lack recoverable complete
per-occurrence logs and timestamps, so this document makes no claim that the
incident record is complete.

### Retained-real five-message level/process/provenance path

The retained AIFS payload crossed the real path: raw artifact and
metadata/sidecar integrity checks -> ecCodes decode -> parser -> normalization
-> owner-neutral adapter -> `WeatherIngestionService` -> PostgreSQL -> FastAPI
forecast query. Exactly five messages were decoded: `z`, `10u`, `10v`, `2t`, and
`tp`. Native level/process provenance was `surface/0`, `heightAboveGround/10`,
`heightAboveGround/10`, `heightAboveGround/2`, and `surface/0`, respectively;
every message carried AIFS Single v2 process identifier `5`.

Decoded inventory, levels, process identifier, cycle/lead/valid time, grid,
source/model identity, and checksums were bound to retained provenance;
caller-supplied paths, hashes, URLs, and decoded messages were not trusted.
The Everest-area selection was provider point `(28.0, 87.0)`, flat index
`358188`, spatial key `aifs-single:0p25:1440x721:358188`. The committed
transaction persisted exactly **`raw=1`, `record=1`, `audit=1`**. Raw retention
was first and immutable; canonical commit, not raw acceptance alone, was the
only lifecycle/health promotion point.

### API identity, UTC filters, leak boundary, and regressions

The bounded historical request to
`GET /api/weather/forecast?source=ecmwf-aifs` returned **HTTP 200**. It
retained `source=ecmwf-aifs`, **`model=AIFS`**, UTC `Z` timestamps, and the
canonical spatial key; it was never reported as IFS. No raw-root path, raw
object/reference ID, provider URL, payload/metadata/sidecar hash, raw metadata,
retention, hold, disposition, or audit field leaked through the public
projection. This HTTP result is historical evidence only.

Negative and regression coverage rejected AIFS/IFS conflation; source,
dataset, model, provider-process, level, inventory, cycle/lead/valid-time,
provenance, range, checksum, stale, duplicate, and tampered-artifact
mismatches. Raw-first canonical failure retained the classified raw fact,
persisted no canonical record, and did not promote lifecycle or health.

Forecast `start`/`end` filters require explicit UTC, timezone-aware RFC 3339
values (`Z` or `+00:00`); naive, non-UTC, and reversed ranges return HTTP 422,
and responses serialize UTC `Z` values. These are API contract rules, not
provider behavior. `Retry-After` parsing, rate limits, and retry timing are
**provider-owned behavior** and are not API response guarantees.

After evidence capture, PostgreSQL, the container, volume, listener, and port
`46901` were removed. Therefore current AIFS database health, API availability,
and runtime status are **unknown**; historical in-run `verified`/`healthy`
values must not be presented as current or production claims. No code or tests
were changed or run by this documentation close.

## Authoritative post-review ICON DB/API acceptance evidence

**Assignment:** `EV-DATA-001-E-POSTREVIEW-API-DOC`  
**Evidence date:** 2026-08-21  
**Evidence type:** controlled disposable PostgreSQL DBRE acceptance; historical
execution evidence, not a current service-health claim

This section is the controlling API handoff for the final Phase E post-review
run. The authoritative complete `apps/api` result is **58 passed, 0 failed, 0
skipped**. **`58` is the number of tests that passed; it is not a path and must
not be rendered or interpreted as `apps/api58`.** The focused real ICON
PostgreSQL/API composition result within the accepted evidence was **2 passed,
0 failed, 0 skipped**. Earlier `53`, `49`, and `44`-pass DBRE records are retained
only as historical chronology and are superseded for final post-review Gate
C-Core acceptance.

The run used the pinned `postgres:17-alpine` image on disposable, non-standard
localhost port **`46583`**. Alembic applied the complete migration chain with no
revision gap:

1. `20260821_0001_data_source_registry`;
2. `20260821_0002_weather_persistence`;
3. `20260821_0003_weather_record_provenance`;
4. `20260821_0004_raw_retention_audit`;
5. `20260821_0005_retention_trigger_correction`; and
6. `20260821_0006_raw_retention_json_trigger_fix`.

### Real six-message pipeline and backend integrity boundary

The accepted network-free regression consumed the approved retained ICON
artifact beneath `EVEREST_RAW_ROOT` and its immutable `metadata.json` and
`metadata.json.sha256` sidecars. WSL ecCodes `2.47.1` parsed all six actual
GRIB2 messages—`2t`, `10u`, `10v`, `HSURF`, `tlat`, and `tlon`—then selected
and normalized native point index `818403`. The real connector output crossed
the owner-neutral adapter contract into `WeatherIngestionService`, PostgreSQL,
and the FastAPI forecast route; no fake ingestion port replaced that path.

At the backend persistence boundary, the approved retained payload was
independently checked as a regular contained file. Its actual byte size and
SHA-256 matched the descriptor, and the descriptor's projected payload size and
hash remained consistent with the connector's verified retrieval projection.
Metadata/sidecar integrity, source/model identity, AOI, cycle, lead, valid time,
URL set, and field projection were also bound before adapter/backend acceptance.
Mismatch and missing-artifact paths failed before canonical persistence.

The successful transaction persisted exactly **raw=1, record=1, audit=1**. The
source changed from `configured`/`unknown` to the historical in-run
`verified`/`healthy` state only after canonical commit; raw acceptance by itself
did not promote lifecycle or health.

### HTTP contract, spatial provenance, and leak boundary

`GET /api/weather/forecast?source=dwd-icon` returned **HTTP 200** with exactly
one ICON forecast record. The response included the exact native canonical
`spatial_key`:

```text
icon:a27b8de618c411e4820ab5b098c6a5c0:818403
```

The public allow-list exposed no raw-root path, raw object/reference ID,
provider URL, payload or sidecar hash, raw metadata, retention owner/class/
period/due date, hold or disposition state, or audit event. `spatial_key` is
intentional canonical provider-grid provenance, not a raw-storage reference.
Current, forecast, and profile serializer regressions preserve the same private
field boundary.

### Negative and cross-source regression evidence

- The synthetic ICON raw-first failure forced canonical persistence to fail
  after raw acceptance. It left exactly **raw=1, record=0**, retained the
  classified raw evidence, and kept lifecycle/health at
  `configured`/`unknown`; no false verification or health promotion occurred.
- Provider/model and projected-integrity mismatches were rejected before the
  backend could persist or promote the source.
- GFS and IFS persistence regressions passed in the authoritative full backend
  run, demonstrating that the ICON post-review changes did not regress those
  existing source paths.

### Management disposition and gate interpretation

The controlling review disposition is
[`EV-DATA-001-E-REVIEW-CLOSURE-EVIDENCE`](../management/decisions.md#ev-data-001-e-review-closure-evidence).
Its findings **E-001 through E-010** apply to this handoff: E-001–E-006,
E-008–E-009 are closed by the recorded connector, parser, complete pipeline,
metadata/hash binding, backend integrity, vocabulary, and coordinate evidence;
E-010 is closed by the authoritative current-status handoffs. E-007 remains in
**Gate C-Operational** and is not a production database-authorization claim.

- **Gate C-Core: accepted** for the controlled Phase E DB/API path.
- **Gate C-Operational: open** for named IAM/ACL identities, legal-hold and
  disposition authority, WORM or equivalent privileged-write resistance,
  production audit, and authoritative Git exclusion/history evidence.

After acceptance, the disposable database, container, volume, listener, port
`46583`, and temporary Python environment were removed. Cleanup did not delete,
move, rewrite, or shorten retention of the approved external ICON payload or
sidecars. Therefore **current ICON operational health and API availability are
`unknown`**. Historical in-run `verified`/`healthy` facts must not be presented
as a live-service or production-health claim.

This documentation-only assignment did not change code or tests and did not
rerun the accepted DBRE evidence.

## Backend Python quality gates

`EV-DATA-001-QUALITY-BACKEND` standardizes quality discovery without changing
API, database, provider, retention, or source-status behavior. Generated
`build`, `dist`, `*.egg-info`, `.pytest_cache`, and `__pycache__` paths are not
source and are excluded by each owned `pyproject.toml`. Generated directories
may remain in a developer workspace; their contents are never lint inputs.

Run the backend gate from `apps/api` with repository and API paths available:

```powershell
$env:PYTHONPATH='D:\Everest;D:\Everest\apps\api'
python -m black --line-length 80 everest_api tests alembic
python -m pylint .
python -m compileall -q everest_api tests alembic
```

Run the owner-neutral shared-contract gate from
`packages/weather_ingestion_contract`:

```powershell
$env:PYTHONPATH='D:\Everest'
python -m black --line-length 80 weather_ingestion_contract tests
python -m pylint .
python -m compileall -q weather_ingestion_contract tests
```

Repository-root pytest discovery is configured in `pytest.ini`, including the
`real_data` marker and Python paths needed for backend/shared-package imports:

```powershell
python -m pytest -q
```

Pylint exceptions remain structural and narrow: SQLAlchemy declarative classes
are exempt from behavior-method counting through their metadata-base ancestor;
schema DTO attribute-count exceptions and test stand-ins are attached to their
exact declarations. No broad DTO/ORM design-message disable is applied.
