# Canonical Weather Schema

## EV-DATA-001-F-AIFS-DOCS-CLOSE-RETRY — authoritative hardened DBRE evidence

This documentation-only retry is the authoritative closure record for the
AIFS handoff. It supersedes the historical `61/63` and failing results,
`61/61`, port `44859`, and all older `pre-DBRE`/`no-DBRE` assertions. No code,
test, external data, or raw artifact was changed.

The hardened run used WSL ecCodes/Python bindings **2.47.1**, pinned
PostgreSQL port **`46901`**, and migrations **`0001`–`0006`**. The complete
`apps/api` suite was **66 passed, 0 failed, 0 skipped**; focused AIFS coverage
was **4 passed, 0 failed, 0 skipped**; and the meteorology AIFS suite was
**37 passed, 0 failed, 0 skipped**. The successful path used the accepted
direct-argv/reviewed wrapper procedure. The three-occurrence wrapper incident
is accepted as an infrastructure incident and had **no recurrence**. Docker
lifecycle evidence was **2**, and the fixture root counter was **1**.

The AIFS registry is **connected-only** and the current state is **no-DBRE**
for lifecycle purposes after teardown; no current `verified`/`healthy` or live
API claim is made. Historical `verified`/`healthy` applies only after the
canonical commit in the disposable run. The committed success had exactly
**`raw=1`, `record=1`, `audit=1`**, after which PostgreSQL, Docker resources,
the listener, and port `46901` were removed. Current health and API
availability are **unknown**.

### AIFS retained-real evidence

The retained payload, canonical metadata, and sidecar are unchanged from the
existing handoff: payload `3,061,386` bytes with SHA-256
`46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5`;
`metadata.json` `1,116` bytes with SHA-256
`86e77f9d36058c40495d3641ff1afce38343c61deb89901cd3435ec702cb9b01`; and
`metadata.json.sha256` file SHA-256
`62f264fe043978e39936e0a51e71385e8c95f8916e7bd342bc90d456fa0ee78e`.
The sidecar declaration matches the metadata digest.

Hardened conversion and backend validation required regular non-symlink files
in one content-addressed directory beneath the approved absolute
`EVEREST_RAW_ROOT`, with the directory name equal to the payload digest. It
bound approved-root containment, AOI, canonical JSON, exact non-overlapping
range inventory and payload size, source/model/dataset, cycle/lead/valid time,
and payload/metadata/sidecar hashes. Raw is retained first and immutable;
canonical persistence and lifecycle promotion cannot manufacture provenance.

WSL ecCodes decoded exactly five messages: `z`, `10u`, `10v`, `2t`, `tp`.
Their native levels were `surface/0`, `heightAboveGround/10`,
`heightAboveGround/10`, `heightAboveGround/2`, and `surface/0`; every message
had AIFS Single v2 process ID **5**. The regular grid was **1440 x 721** and
the Everest request selected `(28.0, 87.0)`, index **358188**, spatial key
**`aifs-single:0p25:1440x721:358188`**. Canonical values were altitude
`5346.3264215561 m`, temperature `0.45586547851564774 C`, wind speed
`0.16091116689523915 m/s`, direction `86.4729776688032` degrees,
precipitation `0.0 mm`, null visibility, and `[missing_value]`.

The historical bounded forecast API returned **HTTP 200**, UTC `Z` timestamps,
the AIFS record and native spatial key, with no raw/private leak. It proved
HTTP 200 AIFS identity is never IFS and that provider URLs, approved-root
paths, hashes, raw metadata, retention, hold, disposition, and audit fields
are excluded. Negative tests rejected IFS/AIFS conflation and raw-first
canonical failure; raw-first retained/classified raw only, persisted no
canonical record, and did not promote lifecycle or health. `Retry-After`
accepts RFC 9110 delta-seconds or IMF-fixdate, rejects malformed or over-60s
values, and remains bounded; UTC API behavior is historical because the
service was removed.

## EV-DATA-001-F-REVIEW-FIX-PARSER — decoded trust boundary

The AIFS review found that the original parser retained `typeOfLevel` but did
not retain numeric `level`, did not reject duplicate/missing/unexpected decoded
messages, and did not bind the decoded inventory/run facts to the immutable raw
metadata before adapter composition. This assignment closes those
meteorology-owned findings without external retrieval, raw mutation, database,
API, or lifecycle/status work.

Current official references consulted are ECMWF Set IX AIFS Single
<https://www.ecmwf.int/en/forecasts/datasets/set-ix>, ECMWF Open Data index and
GRIB documentation
<https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS>,
and ECMWF ecCodes GRIB keys
<https://confluence.ecmwf.int/display/ECC/GRIB+keys>. Set IX defines `z`,
`10u`, `10v`, `2t`, and `tp` as single-level forecast products. The retained
real AIFS GRIB was inspected read-only with ecCodes `grib_get`; its exact native
facts are:

| Parameter | `typeOfLevel` | `level` | AIFS v2 process ID |
| --- | --- | ---: | ---: |
| `z` | `surface` | `0` | `5` |
| `10u` | `heightAboveGround` | `10` | `5` |
| `10v` | `heightAboveGround` | `10` | `5` |
| `2t` | `heightAboveGround` | `2` | `5` |
| `tp` | `surface` | `0` | `5` |

`ParsedMessage` now retains both level type and numeric level plus the existing
generating-process fact. Parsing and normalization require exactly one message
for every field in ordered inventory `z,10u,10v,2t,tp`. Duplicate, missing, or
unexpected parameters; incorrect native level; and process IDs other than `5`
fail closed. All five messages must still share one regular grid, cycle, lead,
and valid time.

Before constructing `AifsRawRetentionMetadata`, conversion rehashes the payload
and sidecars, parses the exact retained payload, and binds decoded inventory,
cycle, lead, valid time, and process ID to the retained connector DTO and
canonical metadata. The scalar adapter projection includes the ordered decoded
inventory, generating process ID, and ordered native level bindings. AIFS v2
metadata identity binds process ID `5`; immutable parameter/range order binds
the decoded inventory. Caller-supplied decoded messages are not accepted as
authority.

Source-specific QC uses explicit `AifsQualityEvidence`. Failed source identity,
checksum, or inventory evidence adds `provenance_error`; stale evidence adds
`stale`; duplicate evidence adds `duplicate`. Flags are additive and the raw
artifact and canonical record are not deleted. Hard parser/metadata trust
failures remain fail-closed before adapter invocation rather than being
silently converted into trusted canonical data.

The immutable historical sidecar names dataset
`AIFS Single Open Data 0.25 degree`; current connector metadata uses the shorter
`AIFS Single`. Conversion accepts only these two known AIFS names and does not
rewrite the historical sidecar. Any other dataset identity fails closed.

Final review-fix checks: focused Windows AIFS tests `36 passed, 1 skipped`;
focused WSL retained-real AIFS tests `37 passed, 0 failed, 0 skipped`; complete
weather tests `147 passed, 1 skipped`; Black left all 30 weather files unchanged;
complete weather Pylint `10.00/10`; and compileall exited `0`. The Windows skip
is the opt-in native retained-real-data case; WSL executed that case against the
actual retained artifact, including decoded-to-retained metadata binding.
The repository regression suite additionally passed `197 passed, 20 skipped`;
those environment-dependent skips are not new DB/API or status evidence.

## EV-DATA-001-F-INCIDENT-001: Accepted Wrapper Procedure

**Reconciliation assignment:** `EV-DATA-001-F-INCIDENT-RECONCILE`

During the AIFS DBRE task, the same PowerShell -> `wsl.exe` -> inline nested
Bash quoting failure occurred three times. Exact per-occurrence timestamps and
complete logs are unavailable and cannot be recovered. Their absence remains a
compliance evidence limitation, so this record does not claim full repeated
failure escalation compliance. The root cause was multi-layer shell parsing,
not AIFS data, ecCodes, PostgreSQL, or API behavior.

Official documentation consulted:

- <https://learn.microsoft.com/en-us/windows/wsl/basic-commands>
- <https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.6>

The accepted next-run rule is to invoke the Linux executable with separate
arguments through `wsl.exe`, or use a reviewed script file when shell syntax is
required. Inline `bash -c`/`bash -lc` strings originating in PowerShell are
prohibited for this root-cause signature. Future runs must capture version,
argument-boundary, UTC, stdout/stderr, exit-code, expected-evidence, and cleanup
records before claiming success.

The complete incident decision and cleanup/rollback procedure are recorded in
`docs/management/decisions.md` under `EV-DATA-001-F-INCIDENT-001`.

The Everest Manager accepts the residual evidence gap as a historical
limitation and prohibits any future use of the failed nested-wrapper pattern.
The successful AIFS DBRE used the accepted corrected direct-argv/reviewed
procedure and was a distinct corrected execution, not a fourth attempt of that
prohibited pattern. Its available report records **61/61** for the complete
test execution, **AIFS 3/3** for focused PostgreSQL/API coverage, disposable
localhost port **`44859`**, and cleanup of the disposable database resources,
listener, and port. Those are successful product-test and cleanup facts. They
do not reconstruct the missing per-occurrence incident logs or timestamps,
erase the three invocation failures, or make the invocation defect a product
failure.

## EV-DATA-001-F-AIFS — Phase F meteorology handoff

The independent implementation is under `services/weather/aifs/`; it does not
alias, subclass, or import the IFS connector/parser/normalizer. It targets the
official ECMWF Open Data `aifs-single/0p25/oper` hierarchy and always emits
stable source/model identity `ecmwf-aifs` / `AIFS`. Provider identity also
retains `aifs-single`, AIFS version `2`, and GRIB
`generatingProcessIdentifier=5`, preventing canonical or persistence
conflation with `ecmwf-ifs` / `IFS`.

`EcmwfAifsConnector` requires existing absolute external `EVEREST_RAW_ROOT`
outside the repository (with test-only explicit injection). It validates AIFS
cycles 00/06/12/18 UTC and 6-hour steps through 360, consumes the official
JSON-Lines index, selects exactly one class-`ai`, model-`aifs-single`,
stream-`oper`, type-`fc`, surface range for every requested field, and accepts
only exact HTTP 206 range responses. It atomically retains content-addressed
GRIB2, canonical metadata, and the mandatory metadata digest sidecar with fsync,
rehash-on-write/reuse, provenance comparison, containment checks, and a
best-effort read-only bit. Full global source objects are never requested.

The parser uses actual ecCodes and requires AIFS Single v2 process ID `5`, one
regular latitude/longitude grid, aligned coordinate/value arrays, and coherent
cycle/valid time. The normalizer validates requested WGS 84 coordinates,
selects the nearest provider cell, and preserves identity as
`aifs-single:0p25:<Ni>x<Nj>:<flat-index>`. Explicit units are required:
`z: m**2 s**-2` to metres using standard gravity, `10u/10v: m s**-1`, `2t: K`
to Celsius, and AIFS v2 `tp: kg m**-2` to the numerically equivalent millimetres
of water depth. Unknown units produce null affected canonical values plus
`invalid_unit`; missing fields remain null/NaN with additive QC. No magnitude
guessing, interpolation, clamping, or imputation occurs.

The thin `AifsIngestionAdapter` imports only the owner-neutral
`weather_ingestion_contract` and meteorology types. Connector-output conversion
re-reads and verifies payload, canonical metadata, and checksum sidecar before
creating scalar descriptor facts. The adapter rejects non-forecast records,
missing native spatial keys, IFS/AIFS source-model conflation, and cycle/lead/
valid mismatch before calling the injected port. This makes direct IFS/AIFS
comparison possible through unchanged canonical fields while preserving
separate provenance and deduplication identity.

The retained real-data evidence is authoritative in
[`docs/data-sources.md`](../data-sources.md#ev-data-001-f-aifs--phase-f-connector-and-retained-real-data-handoff):
cycle/lead/valid `2026-08-21T00:00:00Z` / `0` /
`2026-08-21T00:00:00Z`, five real messages, provider grid `(28.0, 87.0)`,
index `358188`, spatial key `aifs-single:0p25:1440x721:358188`, exact values,
hashes, and immutable external-root paths. WSL ecCodes `2.47.1` performed the
real parse. Connector/parser/normalizer/adapter tests and the retained-real-data
semantic test are meteorology-owned.

### Historical pre-DBRE status

At completion of the meteorology implementation assignment, status was
`connected`, not `verified`: that assignment did not modify or execute
backend-owned PostgreSQL/API integration, obtain independent QA acceptance, or
update frontend display. The later corrected AIFS DBRE result recorded in the
incident reconciliation above supersedes only the earlier absence of DB/API
test evidence. Current runtime and API health remain `unknown`; no live,
production, continuous-service, release, or full-escalation-compliance claim is
made here.

### Phase F implementation verification

The final meteorology-owned checks ran on 2026-08-21 with CPython `3.14.5`,
Black `24.10.0`, Pylint `3.3.9`, pytest `8.4.2`, and WSL ecCodes/Python bindings
`2.47.1`. Final results were:

- Black check: all `30` weather Python files unchanged;
- complete weather Pylint: `10.00/10`;
- `compileall -q -f services/weather`: exit `0`;
- complete weather suite: `129 passed, 1 skipped` (the opt-in Windows native
  parser case only);
- complete repository suite: `175 passed, 17 skipped`, no failures; expected
  skips include unavailable local PostgreSQL/native parser integrations and do
  not constitute AIFS DB/API evidence;
- focused WSL AIFS suite against the retained real artifact: `19 passed, 0
  failed, 0 skipped`.

Tests deterministically cover independent URL/model identity, AIFS index
semantics, valid and invalid HTTP ranges, bounded retry success/exhaustion with
no wall-clock sleep, required external raw root, canonical metadata reuse and
tamper rejection, explicit units, provider spatial key, IFS-conflation
rejection, connector-output payload/sidecar integrity, owner-neutral dependency
direction, parser rejection, and retained-real-data semantics.

## EV-DATA-001-E-POSTREVIEW-MET-DOC — authoritative post-review evidence

**Assignment:** `EV-DATA-001-E-POSTREVIEW-MET-DOC`

The authoritative post-review Phase E execution passed the complete `apps/api`
suite **58/58 (`58 passed, 0 failed, 0 skipped`)** and the focused ICON
PostgreSQL/API integration **2/2 (`2 passed, 0 failed, 0 skipped`)**. It used
pinned disposable PostgreSQL on non-standard localhost port **`46583`**, with
migrations `20260821_0001` through `20260821_0006` applied.

The final retained-data test exercised one continuous six-message pipeline:
approved external-root artifact -> WSL ecCodes `2.47.1` -> six parsed messages
(`2t`, `10u`, `10v`, `HSURF`, `tlat`, `tlon`) -> canonical normalization/QC ->
connector-output conversion -> owner-neutral adapter -> backend descriptor
validation -> PostgreSQL -> bounded forecast API. The successful canonical
transaction persisted exactly `raw=1`, `record=1`, and `audit=1`, and lifecycle
advanced only after canonical commit.

Requested-coordinate validation rejects non-finite or out-of-range WGS 84
latitude/longitude. Native-coordinate validation requires finite canonical
ranges, matching unstructured-grid identity/UUID, and aligned coordinate/value
arrays. The accepted Everest request preserved native coordinate
`(27.926742553710938, 86.921875)`, DWD grid UUID
`a27b8de618c411e4820ab5b098c6a5c0`, point index `818403`, and spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`; it did not substitute a rounded
requested coordinate.

The connector-output conversion bound the retrieval to the re-read payload,
canonical `metadata.json`, and `metadata.json.sha256`. It verified payload size
and SHA-256, metadata and sidecar hashes, source/model, URL and field set,
cycle/lead/valid time, requested coordinate, and AOI provenance before adapter
composition. The allow-listed scalar projection retained independent provider
payload/metadata/sidecar integrity values. Backend descriptor checks then
independently required a regular file under the approved raw root and verified
its bytes/hash plus projected descriptor size/hash consistency before any raw
or canonical persistence.

The API returned HTTP `200` with exactly one canonical ICON forecast and its
native `spatial_key`. Public response allow-list checks proved **no raw/private
leak**: no approved-root path, DWD URL, payload hash, raw metadata, retention,
hold, disposition, or audit field was exposed. The synthetic ICON raw-first
failure preserved the classified raw fact, inserted no canonical record, and
left lifecycle/health at `configured`/`unknown`. GFS/IFS persistence regressions
and shared current/forecast/profile API regressions passed.

The disposable database, container/volume, listener, port `46583`, and temporary
Python environment were cleaned up after acceptance; approved-root retained
payload/metadata/sidecar counts were unchanged. Consequently, in-run
`verified`/`healthy` is historical and **current ICON runtime health and API
availability are `unknown`**. Gate C-Core is accepted, but **Gate C-Operational
remains open** for production/shared-deployment controls. This record makes no
live or production claim and includes no AIFS work.

The manager’s
[Review Finding Disposition](../management/decisions.md#review-finding-disposition)
is the closure authority for **E-001 through E-010**. E-001–E-006 and
E-008–E-010 are closed; E-007 remains within open Gate C-Operational. This
cross-reference does not convert the E-007 operational control into a closed or
production-verified claim.

All earlier counts (including `42`, `49/49`, `53 passed`, and environment-skip
counts), ports (`53112`, `47189`), and blocked/pre-DBRE/no-DBRE assertions in
this handoff are **historical and superseded for current Phase E status**. They
remain chronology only and must not override this 58/58 post-review record.

## Historical predecessor — EV-DATA-001-E-DOCS-FULL-FINAL

> **Historical notice:** The following 53-pass record predates and is superseded
> by the authoritative 58/58 execution above. Its port, counts, and any blocked
> assertions are non-authoritative for current Phase E status.

For Phase E review and handoff, the authoritative test evidence is the final
full-pipeline result **53 passed, 0 failed, 0 skipped**, including **ICON 2/2**
focused PostgreSQL/API tests. Every earlier `49/49`, skipped-test, blocked,
pre-DBRE, or no-DBRE statement is retained only as historical chronology and is
superseded as a statement of final Gate C-Core/DBRE capability. It must not be
used to describe the current accepted core pipeline. Current runtime health and
API availability remain **unknown**, and **Gate C-Operational remains open**.

The final full-pipeline evidence supersedes earlier statements that connector
metadata could not reach the adapter, or that the ICON parser-to-database path
was unproven. Using WSL ecCodes and a pinned PostgreSQL environment on
`localhost:47189`, migrations `0001`–`0006` applied and the full suite completed
with **53 passed, 0 failed, 0 skipped**. The focused ICON PostgreSQL/API
coverage was **2 passed**. GFS and IFS regression coverage also passed.

The real connector output was converted through the authoritative connector-
output metadata conversion into the owner-neutral adapter projection. The
backend rehashed the retained payload before accepting it. The successful
transaction persisted exactly `raw=1`, `record=1`, and `audit=1` (unchanged
root counts). WSL ecCodes parsed six actual ICON messages: `2t`, `10u`, `10v`,
`HSURF`, `tlat`, and `tlon`. The bounded API response preserved the native
`spatial_key` and exposed no raw path, provider URL, payload hash, raw
metadata, retention, hold, disposition, or audit fields.

The synthetic raw-first regression accepted and classified one raw artifact,
then forced canonical persistence to fail. It persisted no canonical record
and left lifecycle/health at `configured`/`unknown`; it did not falsely
escalate to `verified`/`healthy`. The disposable database, container/volume,
listener, and port `47189` resources were cleaned up, while the approved raw
artifact remained retained. Current runtime health and API availability are
therefore **unknown**.

Gate C-Core/DBRE is complete; **Gate C-Operational remains open**. These are
historical disposable acceptance results, not a live or production claim. No
ECMWF AIFS work has started.

**Assignment:** EV-DATA-001-B-METEOROLOGY  
**Status:** ECMWF IFS and DWD ICON have historical disposable end-to-end
acceptance evidence through PostgreSQL persistence and the backend forecast API.
Their test environments were removed after acceptance; current operational
health and live API availability are unknown. ICON Gate C-Operational remains
incomplete, and no production claim is made.

This document is the meteorology handoff for every later weather connector and
normalizer. It is deliberately independent of PostgreSQL, HTTP, and any
provider-specific file format. The executable shape is
`services/weather/contract.py`.

## Record identity and types

Every record has exactly one `record_type`:

* `forecast` is a model prediction. It must identify the model run (`cycle`),
  the lead from that run, and the resulting valid time.
* `observation` is a measurement made by an instrument or observing network.
  It has an observation timestamp and no forecast cycle or lead.
* `satellite` is a remotely sensed observation or product. It is not silently
  converted into an observation or forecast.
* `derived` is computed from one or more canonical records or approved source
  data. Its derivation metadata must be retained by the owning pipeline.

`timestamp` means the record's valid/measurement time. Forecast records also
carry `forecast_cycle` (the model initialization time) and
`forecast_lead_time` (duration from cycle to valid time). For forecasts,
`timestamp == forecast_cycle + forecast_lead_time`; a mismatch is flagged.
All times are timezone-aware UTC ISO-8601 values (a trailing `Z` is the wire
representation). Naive timestamps and non-UTC offsets are rejected by the
contract validator rather than guessed.

`source` is the stable approved-source identifier, not a free-form URL.
`model` is the provider model name (for example, a later AIFS connector must
write `AIFS`). Both are provenance and are required for every record. Raw
source metadata must preserve the provider's original names and values.

## Canonical fields

The following core keys are mandatory in the serialized contract. Their values
may be `null` only where marked nullable; null means “not supplied or not
applicable,” never zero or an imputed value.

| Field | Type | Nullability | Unit and convention |
| --- | --- | --- | --- |
| `timestamp` | UTC datetime | Required | UTC ISO-8601 |
| `latitude` | number | Required | decimal degrees, north positive, `[-90, 90]` |
| `longitude` | number | Required | decimal degrees, east positive, normalized to `[-180, 180]` |
| `altitude` | number | Required | metres above mean sea level; finite |
| `wind_speed` | number | Nullable | metres per second, `>= 0` |
| `wind_direction` | number | Nullable | degrees from true north, clockwise, `[0, 360)`; null for calm/absent direction |
| `temperature` | number | Nullable | degrees Celsius |
| `precipitation` | number | Nullable | millimetres for the source interval; `>= 0` |
| `visibility` | number | Nullable | metres, `>= 0` |

Recommended nullable keys are `pressure` (Pa), `relative_humidity` (percent,
`0..100`), `dew_point` (C), `cloud_cover` (percent, `0..100`), `cloud_base`
(m), `cloud_top` (m), `snowfall` (mm for the source interval), `gust_speed`
(m/s), `source`, `model`, `forecast_cycle`, `forecast_lead_time`, and
`quality_flag`. In the executable contract, provenance `source` and `model`
are required despite their historical placement in the recommended list;
provider connectors must never emit an unidentified record.

The route profile uses the same contract at EBC, C1, C2, C3, C4, and Summit;
altitude remains the record's actual value and is not replaced with a route
label.

## Quality flags and validation

`quality_flag` is a set of machine-readable flags. `clean` means all applicable
checks passed. Other flags include `missing_value`, `out_of_range`,
`invalid_timestamp`, `invalid_coordinate`, `invalid_unit`, `duplicate`,
`stale`, `provenance_error`, and `cycle_time_mismatch`. Flags are additive;
they describe the record and must not be used to erase it. A record with any
non-clean flag is retained for audit and may be excluded by a later consumer.

Normalization converts timestamps to UTC, coordinates to decimal degrees with
the conventions above, temperatures to C, wind speeds/gusts to m/s,
precipitation/snowfall to mm, and visibility/altitude/cloud heights to m. It
must use explicit provider unit metadata or a connector-specific documented
mapping; it must not infer units from magnitude. Wind directions are normalized
modulo 360, except that 360 is converted to 0. Missing-value sentinels become
null and add `missing_value`. No interpolation, clamping, or silent imputation
is part of normalization.

The validator flags, rather than deletes, failures. Required checks include:
UTC/timezone awareness; latitude and longitude ranges; finite altitude;
non-negative speed, precipitation, visibility, and heights; humidity and cloud
cover in `0..100`; direction in `[0, 360)`; source/model identity; forecast
cycle/lead/valid-time consistency; duplicate identity; and stale-data policy
defined by the consuming source schedule. QC must also retain the original
value and raw metadata when a conversion or check fails.

## Raw retention and deduplication

Raw provider payloads and raw metadata are immutable, content-addressed
artifacts. They are retained even when parsing, normalization, or QC fails;
canonical records are a derived view and may be superseded, never rewritten in
place. Raw metadata includes source, dataset, model/run/cycle/lead/valid time,
retrieval time, original filename/format, declared units, checksum, and parser
version when available.

The minimum deduplication identity is `(source, dataset, timestamp, spatial
key, forecast_cycle, forecast_lead_time)`. `spatial_key` is the provider grid
cell or stable station/pixel identifier, not a rounded coordinate invented by
the normalizer. Include a content hash when the source can publish different
payloads for the same logical identity. A duplicate is flagged and does not
replace the immutable raw artifact; conflict resolution is a later persistence
policy.

### Provider adapter metadata projection

The canonical raw sidecar remains immutable and complete beside the payload
under the approved raw root. An owner-neutral adapter must not forward that
sidecar mapping unchanged. For the ICON boundary, `RawArtifactDescriptor`
metadata is a scalar-only projection containing source, provider, dataset,
model, format, cycle, lead, valid time, retrieval time, size, payload SHA-256,
metadata SHA-256, sidecar SHA-256, AOI id/version/scope, retention owner,
retention class/period, disposition state, hold state, and a safe
content-addressed provenance reference. Provider URLs, arrays, mappings, and
provider objects remain in the retained sidecar and never cross the port.

Required projected values are validated before the persistence port is called;
unsupported values fail closed. The projection is transport metadata only and
does not alter canonical weather fields or the raw sidecar.

#### Authoritative cross-layer vocabulary translation

**Assignment:** `EV-DATA-001-E-REVIEW-FIX-VOCAB`

This is the single authoritative translation table for raw-sidecar, adapter,
and backend ingestion vocabulary. Names are layer-specific; equal values do not
authorize using one layer's key at another layer. Lead conversion is explicit
because the raw sidecar stores hours while the adapter and backend store
seconds.

| Semantic fact | Raw sidecar key | Adapter scalar projection key | Backend descriptor/model key | Required translation |
| --- | --- | --- | --- | --- |
| Payload digest | `sha256` | `provider_payload_sha256` | `sha256` | Preserve the lowercase SHA-256 digest exactly; the backend independently rehashes the payload before acceptance. |
| Payload length | `size_bytes` | `provider_payload_size_bytes` | `size_bytes` | Preserve the integer byte count exactly. |
| Forecast lead | `lead_hours` | `provider_lead_seconds` | `forecast_lead_seconds` | Convert with `seconds = lead_hours * 3600`; do not relabel hours as seconds. |
| Forecast valid time | `valid_time` | `provider_valid_time` | `valid_time` | Preserve the same timezone-aware UTC instant; serialize as UTC ISO-8601. |
| Backend hold state | Not provider-owned | Not provider-owned | Hold enum: `none`, `held`, `released`, `unknown` | Persist only one backend enum value. `none` is the persisted value meaning no hold; “not held” may appear only as prose and `not_held` is not a persisted value. |

The hold state is backend policy vocabulary, not raw provider provenance and not
a `provider_*` adapter fact. In particular, factual persistence evidence must
say `none`, not `not_held`.

## Phase C ECMWF IFS handoff

The IFS implementation is under `services/weather/ecmwf/`. It uses only the
official ECMWF Open Data portal (`https://data.ecmwf.int/forecasts/`), reads
the portal's `.index` sidecar, and downloads byte ranges for a minimal set of
surface GRIB2 messages (`z`, `10u`, `10v`, `2t`, `tp`). Raw bytes are retained
under a SHA-256 content-addressed directory with immutable JSON metadata.
The parser uses ecCodes, preserves the provider grid, and the normalizer
selects the nearest provider grid cell. Declared IFS units are required for
each converted field: geopotential `z` (`m**2 s**-2`) becomes metres, `2t`
(`K`) becomes Celsius, vector wind (`m s**-1`) becomes speed/direction, and
total precipitation `tp` (`m`) becomes interval millimetres. Unknown or invalid
declared units are not guessed: the input is retained in raw artifacts, the
canonical affected value is null, and additive QC includes `invalid_unit`.

### Real-data evidence

The earlier pre-correction 23-pass/one-artifact acceptance record is
superseded by the final corrected DBRE evidence in the section below. The final
record, including migration `0003`, two raw artifacts, one canonical record,
and one `static_altitude` association, is authoritative.

The official directory observed for this handoff was
`https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/`, and the
official index was
`https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.index`.
The selected GRIB2 URL was
`https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.grib2`.
The directory and index returned HTTP 200 and exposed the 2026-08-20 00:00
UTC IFS run, valid at 00:00 UTC for lead 0. The complete source file advertised
137,248,825 bytes, but was not downloaded; the connector used index-selected
HTTP ranges only. Range responses now require HTTP `206`, a matching
`Content-Range`, and the exact selected byte length; unexpected full HTTP `200`
responses are rejected. The local retrieval succeeded on 2026-08-21 UTC: the
selected artifact was 3,276,049 bytes with SHA-256
`a9298ae22a556f3d4ec053f0a07c33bd3d2156cd130f5e09068090e079be2d48`, retained
under a temporary content-addressed raw store. The Windows Python binding
remained unusable because its native library was absent. WSL Kali Linux
already provided the compatible open packages `libeccodes0=2.47.1-1` and
`python3-eccodes=2:2.47.0-1`; no package installation was needed. Running the
parser in WSL against the validated artifact produced 4 GRIB2 messages and 4
variables: `z`, `10u`, `10v`, and `2t`. At the nearest provider grid point
`(28.0, 87.0)` to Everest `(27.9881, 86.9250)`, values were respectively
`58918.8818359375 m**2 s**-2`, `0.666534423828125 m s**-1`,
`0.1239166259765625 m s**-1`, and `269.5345001220703 K`.

Normalization produced a forecast record at `2026-08-20T00:00:00Z`, altitude
`6008.053905863623 m`, temperature `-3.6154998779296648 C`, wind speed
`0.6779553586640538 m/s`, and wind direction `259.4682756841703 degrees`.
QC produced the additive flag `missing_value` because this minimal artifact
does not contain precipitation or visibility. No values were deleted or
imputed.

Raw artifacts are written through a temporary file, fsynced, rehashed before
atomic replacement, and rehashed again when an existing content-addressed path
is reused; a checksum mismatch fails retention. The connector requests a
best-effort read-only file bit after write. On Windows this is not an immutable
ACL boundary, so enforcement beyond that bit remains an object-store or
filesystem-policy responsibility.

### Corrected `tp` real-data recheck

The corrected strict-range connector was run against this additional official
historical IFS file and index:

- GRIB2: `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-3h-oper-fc.grib2`
- Index: `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-3h-oper-fc.index`
- Cycle: `2026-08-20T00:00:00Z`; lead `3` hours; valid time
  `2026-08-20T03:00:00Z`.

The connector made index-selected requests only and retained a `3,074,657`
byte artifact with SHA-256
`7d4b2feae148ade17a90b8168091d64d0f27b40ed55aa19530c48f49d53fdf9d`.
The actual `tp` request was HTTP `206` with
`Content-Range: bytes 0-695124/145014222` and returned exactly `695,125` bytes;
the strict connector validates this same status/header/length condition for
every selected range and rejects full HTTP `200` responses.

ecCodes parsed four GRIB2 messages/variables: `tp`, `10u`, `10v`, and `2t`.
For requested Everest coordinate `(27.9881, 86.9250)`, all selected messages
used provider grid point `(28.0, 87.0)`. The actual parsed `tp` value was
`3.814697265625e-06 m`; normalization produced canonical precipitation
`0.003814697265625 mm`. The other parsed grid values were `10u =
-0.120147705078125 m s**-1`, `10v = 0.8499603271484375 m s**-1`, and `2t =
271.78648376464844 K`. The normalized record has timestamp
`2026-08-20T03:00:00Z`, temperature `-1.3635162353515398 C`, wind speed
`0.8584101751271469 m/s`, and wind direction `171.95415714345518 degrees`.

This minimal 3-hour selected artifact does not include surface `z`. The
normalizer therefore retained no fabricated altitude (`NaN`) and additive QC
returned `missing_value` and `out_of_range`; `invalid_unit` was not present
because all four parsed declared units matched their expected IFS mappings.

### Same-cycle surface-geopotential altitude resolution

Inspection of the official 3-hour index found `z` only at pressure levels, not
at `levtype=sfc`; this is expected because ECMWF's official IFS Open Data table
defines surface `z` as **Geopotential (step 0)** and lists forecast geopotential
at pressure levels. This was not a connector-selection bug: the connector
correctly selects requested surface messages, so `z` is absent from the 3-hour
surface selection. The official same-cycle step-zero index does contain one
surface `z` range. It was retrieved with the same strict HTTP-206,
`Content-Range`, length-validation, atomic-write, and rehash retention path:

- Step-zero GRIB2: `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.grib2`
- Step-zero index: `https://data.ecmwf.int/forecasts/20260820/00z/ifs/0p25/oper/20260820000000-0h-oper-fc.index`
- Selected `z` artifact: `896,851` bytes; SHA-256
  `529c14e03a8b22d86ff85e2bbd9d81c481ca626e410d1f6e8d875a112f4cb501`.
- Parsed static surface `z`: `58918.8818359375 m**2 s**-2` at `(28.0, 87.0)`;
  converted using standard gravity `9.80665 m/s²` to altitude
  `6008.053905863623 m`.

The static step-zero surface geopotential is semantically compatible with the
same-cycle 3-hour forecast record because it is ECMWF IFS's own surface
geopotential/orography field on the same provider grid; it supplies only the
required grid-cell altitude and does not change forecast meteorology, valid
time, cycle, or lead. The normalizer now anchors forecast identity to the
latest valid-time dynamic message while accepting the same-cycle step-zero `z`
for altitude.

Combining the real step-zero `z` message with the real 3-hour `tp`, `10u`,
`10v`, and `2t` messages produced one coherent persistence-ready canonical
record for requested `(27.9881, 86.9250)` and selected grid `(28.0, 87.0)`:

```text
source/model: ecmwf-ifs / IFS
record_type: forecast
timestamp: 2026-08-20T03:00:00Z
forecast_cycle: 2026-08-20T00:00:00Z
forecast_lead_seconds: 10800
spatial_key: ifs:0p25:28.0:87.0
altitude: 6008.053905863623 m (same-cycle step-zero surface z)
wind_speed: 0.8584101751271469 m/s
wind_direction: 171.95415714345518 degrees
temperature: -1.3635162353515398 C
precipitation: 0.003814697265625 mm
visibility: null
quality_flags: [missing_value]
```

The combined parse contains five real GRIB messages: step-zero surface `z` and
3-hour surface `tp`, `10u`, `10v`, and `2t`. All declared units matched the
IFS mappings; no `invalid_unit` or `out_of_range` flag was returned. This
descriptor is persistence-ready; it retains two raw artifacts rather than
claiming that they are one source-file object.

### Historical disposable E2E acceptance evidence

DBRE executed the complete backend suite against an official pinned PostgreSQL
disposable session on `localhost:46133`; the result was `27 passed, 16
warnings`, with all PostgreSQL tests run. Migration `0003` was applied. The E2E execution
migrated to head, registered `ecmwf-ifs` at `planned`, and did not manually set
evidence states. `WeatherIngestionService` persisted two raw artifacts, one
canonical weather record, and one auxiliary association:

- `raw_artifact_count=2`; `weather_record_count=1`;
  `auxiliary_association_count=1`, with role `static_altitude`.
- Dynamic 3-hour artifact: `3,074,657` bytes, SHA-256
  `7d4b2feae148ade17a90b8168091d64d0f27b40ed55aa19530c48f49d53fdf9d`.
- Static 0-hour surface-`z` artifact: `896,851` bytes, SHA-256
  `529c14e03a8b22d86ff85e2bbd9d81c481ca626e410d1f6e8d875a112f4cb501`.
- Both artifacts use IFS cycle `2026-08-20T00:00:00Z`; dynamic valid time is
  `2026-08-20T03:00:00Z` with lead `10800` seconds. Dynamic is primary; static
  `z` is auxiliary provenance only.
- Backend-persisted registry facts: `registry_status=verified`,
  `health=healthy`, `last_success_at=2026-08-20T18:40:28.274415+00:00`.
- `GET /api/weather/forecast?source=ecmwf-ifs&start=2026-08-20T03:00:00Z&end=2026-08-20T03:00:00Z`
  returned HTTP `200` and exactly one persisted record. It returned requested
  Everest coordinate `(27.9881, 86.9250)` as provider grid `(28.0, 87.0)`,
  timestamp `2026-08-20T03:00:00Z`, cycle `2026-08-20T00:00:00Z`, lead
  `10800`, altitude `6008.053905863623 m`, temperature
  `-1.3635162353515398 C`, wind speed `0.8584101751271469 m/s`, wind direction
  `171.95415714345518 degrees`, precipitation `0.003814697265625 mm`, null
  visibility, and `[missing_value]` quality flags.
- The combined parse contained five GRIB messages: `z`, `tp`, `10u`, `10v`,
  and `2t`. Dynamic is primary; static `z` is auxiliary provenance only.

The disposable container, database volume, and listener were removed after the
test. Accordingly, `verified` documents historical end-to-end acceptance only;
it does not claim a current continuously healthy runtime, an available API, or
a production deployment. Current runtime health is unknown.

WSL installation option, if absent on another compatible instance:
`wsl.exe -d kali-linux -- sudo apt-get update && wsl.exe -d kali-linux -- sudo apt-get install -y libeccodes0 python3-eccodes`.
This was not executed here because both packages were already installed.

### Superseded ingestion guidance

Earlier one-artifact ingestion examples and the pre-persistence backend blocker
are superseded and intentionally removed. The authoritative Phase C E2E
handoff is the final two-artifact, migration-`0003` acceptance section above:
the dynamic 3-hour artifact is primary, the step-zero surface-`z` artifact is
associated with role `static_altitude`, and PostgreSQL persistence plus the
bounded forecast API query completed successfully. Its `verified` state is
historical disposable acceptance evidence only; current runtime health remains
unknown after teardown.

## Phase B boundary

This handoff adds only the canonical typed contract and its unit tests. It does
not implement connectors, real retrieval, parsers, database tables, APIs,
frontend display, scheduling, or any Phase C–F source work.

## Phase D NOAA GFS handoff

The independent NOAA/NCEP implementation is under `services/weather/gfs/` and
does not change ECMWF behavior. `connector.py` targets the official NOMADS
filter endpoint and official product directory, requests only a bounded box
around Everest `(27.9881, 86.9250)`, retains raw GRIB2 and deterministic
metadata with SHA-256, and retries transport failures with injectable backoff.
`parser.py` requires ecCodes and parses actual GRIB2 messages. `normalizer.py`
maps declared GFS units to the canonical contract: Kelvin to Celsius,
geopotential metres, vector wind to speed/direction, and precipitation to
millimetres.

### Superseded GFS retrieval and provisional E2E evidence

The following retrieval and port-`52370` disposable evidence is retained only
as historical context. It is superseded by the checked-in-adapter E2E record
below and is not an alternative authoritative GFS E2E path.

The official directory observed for this attempt was
`https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/`.
It advertised `gfs.t00z.pgrb2.0p25.f000` (473 MB) and its 31 KB `.idx` sidecar;
the full file was not downloaded. The official filter request for cycle
`2026-08-20T00:00:00Z`, lead `0`, returned HTTP 500; this is a historical
failed alternative, not the final source result. A direct official
`.idx`/HTTP-range alternative succeeded. The `.idx` URL was
`https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000.idx`
and the GRIB2 URL was the same path without `.idx`. Four selected messages
(`orog`, `2t`, `10u`, `10v`) produced 2,937,483 bytes with SHA-256
`9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`.
WSL ecCodes parsed all four messages. At requested `(27.9881, 86.9250)`,
provider grid `(28.0, 87.0)` yielded cycle/valid time
`2026-08-20T00:00:00Z`, altitude `5917.819375 m`, temperature
`-3.243212890625 C`, wind speed `2.0815467554532674 m/s`, wind direction
`235.34425831717988 degrees`, precipitation `null`, and `[missing_value]`.
The historical disposable PostgreSQL E2E acceptance persisted one raw artifact
and one canonical weather record. Raw artifact ID was
`ca066011-7a81-46ab-af45-3f1a7b1fcf73`; canonical record ID was
`c33d84d9-b221-43e1-a68a-e1b8f580904a`. The backend recorded
`status=verified`, `health=healthy`, and `last_success_at`
`2026-08-21T02:03:40.349485+00:00` during that run. The exact bounded query
`GET /api/weather/forecast?source=noaa-gfs` returned HTTP 200 and exposed API
latitude `27.9881`, longitude `86.925`, altitude `5917.819375 m`, temperature
`-3.2432128906249886 C`, wind speed `2.081546755453268 m/s`, wind direction
`235.34425831717988 degrees`, null precipitation/visibility, and
`[missing_value]`.

The test suite completed with `27 passed, 16 warnings`; all PostgreSQL tests
executed. The disposable database used temporary port `52370` and was cleaned
up afterward. The lifecycle `verified` and historical `healthy` values are
acceptance facts from that removed environment. Current runtime health and API
availability remain `unknown`.

The GFS quality remediation makes the selected metadata authoritative:
`orog`, `2t`, `10u`, and `10v` are the four recorded provider messages; stale
`HGT`/`APCP` selections are not part of this artifact. Each retained artifact
now has canonical `metadata.json` and a `metadata.json.sha256` sidecar.
Metadata is atomically written with fsync and a best-effort read-only bit, then
rehashed and canonicalized on every reuse. Tampered, missing, malformed, or
noncanonical metadata is rejected. Deterministic tests cover valid and invalid
HTTP 206 ranges, incomplete indexes, HTTP 500 retries/exhaustion, metadata
integrity, and no-wall-clock-sleep failure paths. GFS is not marked verified by
this quality assignment; historical acceptance and current unknown runtime
health remain distinct as documented above.

### Authoritative GFS checked-in-adapter E2E evidence

On `2026-08-21T02:27:10.360839Z`, the corrected connector re-ran the
authoritative direct NOAA/NCEP `.idx` and strict HTTP-206 range path against
the still-serving historical `2026-08-20T00:00:00Z` GFS `f000` product. This is
a fresh retained raw artifact. This artifact was preverified and then passed
through the checked-in `compose_gfs_ingestion_adapter`; no direct backend
descriptor construction was used.

- GRIB2 URL:
  `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000`
- Index URL:
  `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260820/00/atmos/gfs.t00z.pgrb2.0p25.f000.idx`
- Cycle/valid time: `2026-08-20T00:00:00Z`; lead: `0` seconds; format:
  `GRIB2`.
- Retained payload:
  `tmp-gfs-refresh-20260821/noaa-gfs/9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4/gfs.t00z.pgrb2.0p25.f000.grib2`.
- Retained canonical metadata:
  `tmp-gfs-refresh-20260821/noaa-gfs/9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4/metadata.json`,
  with the sibling `metadata.json.sha256` integrity sidecar.
- Metadata sidecar SHA-256:
  `f99e6967479a193def39c1bf80e364fcaea9ac39a4fb3ebaf2f97778e54eb9de`.
- Size: `2,937,483` bytes; SHA-256:
  `9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`.
- Canonical metadata records source `noaa-gfs`, provider `NOAA/NCEP`, dataset
  `GFS pgrb2.0p25`, model `GFS`, requested coordinate `(27.9881, 86.9250)`,
  exact selected messages `orog/surface`, `2t/2 m above ground`,
  `10u/10 m above ground`, and `10v/10 m above ground`.

WSL ecCodes parsed four messages. At requested Everest coordinate
`(27.9881, 86.9250)`, all selected messages used provider grid `(28.0, 87.0)`:
`orog = 5917.819375 m`, `2t = 269.906787109375 K`,
`10u = 1.7122460937500001 m s**-1`, and
`10v = 1.18365966796875 m s**-1`. Normalization produced the factual adapter
input record: `record_type=forecast`, timestamp/cycle
`2026-08-20T00:00:00Z`, lead `0`, provider spatial key
`gfs:0p25:28.0:87.0`, altitude `5917.819375 m`, temperature
`-3.2432128906249886 C`, wind speed `2.081546755453268 m/s`, wind direction
`235.34425831717988 degrees`, null precipitation/visibility, source
`noaa-gfs`, model `GFS`, and additive quality flag `[missing_value]`.

The disposable PostgreSQL harness used temporary port `34034`, applied
migrations `0001` through `0003`, persisted `raw=1` and `record=1`, and created
primary record ID `5b036b60-fe79-4e02-8681-a142b81b17e3`. The service generated
`status=verified`, `health=healthy`, and `last_success_at`
`2026-08-21T02:27:10.360839+00:00`. The exact bounded 00Z query with
`source=noaa-gfs` returned HTTP 200 and one record with API latitude `27.9881`,
longitude `86.925`, altitude `5917.819375 m`, temperature
`-3.2432128906249886 C`, wind speed `2.081546755453268 m/s`, wind direction
`235.34425831717988 degrees`, null precipitation/visibility, and
`[missing_value]`.

Historical backend-harness evidence is `29 passed, 20 warnings`; the explicit
checked-in adapter integration tests are `2 passed`. The database and all
temporary resources were cleaned up. Therefore `verified` and `healthy` are
historical disposable-acceptance facts only; current runtime health and API
availability are `unknown`. The earlier practical/full counts (`35 passed` and
`54 passed, 8 skipped`) are superseded by the authoritative final result:
`53 passed, 0 failed, 0 skipped`.

### GFS owner-neutral ingestion adapter boundary

`services/weather/gfs/ingestion.py` is the meteorology-owned thin adapter from
verified NOAA GFS retention facts and normalized `WeatherRecord` values to the
owner-neutral `RawArtifactDescriptor` and `CanonicalRecordInput` commands from
`weather_ingestion_contract`.
It does not import FastAPI, SQLAlchemy/ORM models, ecCodes, HTTP clients, or
database/session code. It preserves the raw source metadata dictionary,
source/cycle/lead, provider spatial key, nullable weather values, and QC flags
without conversion or filtering. The shared descriptor accepts only string-keyed
scalar JSON metadata (`str`, `int`, `float`, `bool`, or `null`); construction
rejects nested containers and provider objects before the persistence port is
called.

Backend composition uses this exact API (where `service` is an existing
`WeatherIngestionService` instance):

```python
from services.weather.gfs import compose_gfs_ingestion_adapter

adapter = compose_gfs_ingestion_adapter(service)
artifact_id = adapter.ingest(raw_retention_metadata, canonical_gfs_records)
```

The injected object must implement the shared `IngestionPort` protocol. Before
calling that port, the adapter rejects inconsistent GFS source,
model, raw cycle/lead/valid-time, forecast record cycle/lead/valid-time, record
type, and missing spatial-key provenance. This prevents a raw artifact from
being retained before the adapter detects a provenance mismatch.

## Phase E DWD ICON handoff

The ICON provider path follows the canonical contract directly: cycle and valid
time are timezone-aware UTC values and require `valid_time == cycle + lead`.
The normalizer preserves the native DWD UUID and selected point index as
`icon:<uuid>:<index>`, and the adapter forwards that exact key into
`CanonicalRecordInput`. Missing values remain null with additive
`missing_value`; invalid declarations for `T_2M`, `U_10M`, `V_10M`, or `HSURF`
produce null affected values plus `invalid_unit` without magnitude-based
guessing. Calm vectors retain zero speed and a null direction.

### Lifecycle status

ICON now has historical disposable `verified`/`healthy` evidence from the final
approved-root canonical-commit execution documented below. Those values were
written only after one canonical record committed. The disposable environment
was then removed, so current `health_status` and API availability are `unknown`.
Gate C-Operational remains incomplete and this is not a production claim. The
historical 00Z HTTP 404 remains a failed retrieval attempt; it does not negate
the later retrieval, parsing, or final disposable acceptance evidence.

The independent DWD ICON implementation is under `services/weather/icon/`.
It uses only `https://opendata.dwd.de/weather/nwp/icon/grib/`, the official DWD
Open Data global ICON GRIB2 product hierarchy. The product hierarchy exposes
individual bzip2-compressed variable objects rather than a provider GRIB-message
inventory/index or a documented safe range-selection API. Consequently the
connector requests the smallest factual official objects available for the
required fields (`T_2M`, `U_10M`, `V_10M`, and `HSURF`), decompresses and checks
that every response is GRIB2, and does not attempt a prohibited global/full
multivariable download.

`DwdIconConnector` requires an existing absolute external raw root through
`EVEREST_RAW_ROOT` at runtime. It fails closed when that value is absent,
relative, nonexistent, or resolves inside the repository; all payload,
metadata, and sidecar object references must resolve beneath that root. An
explicit `test_raw_root` injection is available only for deterministic unit
tests. The connector uses bounded injectable retry/backoff, SHA-256
content-addressed raw retention, temporary-file fsync, rehash-before-atomic
replace, rehash-on-reuse, canonical JSON metadata, and a mandatory
`metadata.json.sha256` sidecar. Its best-effort read-only bit is not an ACL or
object-store immutability guarantee. `parse_grib_bytes` requires ecCodes (the
available WSL Kali environment has `python3-eccodes` and `libeccodes0`) and
preserves DWD short name, unit, cycle, lead, valid time, `gridType`, and each
native grid coordinate. `normalize_messages` selects the nearest provider grid
cell for the request—not a fabricated rounded cell. Before nearest-cell
selection, requested latitude and longitude must both be finite; latitude must
be in `[-90, 90]` and longitude in `[-180, 180]`. Invalid requests are rejected
rather than wrapped or matched. Valid requests, including Everest
`(27.9881, 86.9250)`, retain native nearest-cell selection. Values are accepted
only when declared units match: `T_2M: K -> C`, `U_10M/V_10M: m s**-1`, and
`HSURF: m`.
`HSURF` is the DWD-provided time-invariant terrain height. It is retained as the
canonical altitude only when a real parsed message supplies it; missing or
invalid fields are null/NaN plus additive QC, never inferred.

### ICON parser coordinate and temporary-file contract

The parser follows the official Python `tempfile` lifecycle guidance and the
official ecCodes Python file-object API:

* Python `tempfile`: https://docs.python.org/3/library/tempfile.html
* ecCodes Python interface:
  https://sites.ecmwf.int/docs/eccodes/namespaceec_codes.html
* ECMWF-maintained Python bindings:
  https://github.com/ecmwf/eccodes-python

`codes_grib_new_from_file` receives a separately opened binary reader. The
payload writer is closed before that reader is opened, which avoids Windows
named-file sharing conflicts. The securely created `mkstemp` descriptor is
owned and closed by the parser, and its path is unlinked in `finally` on both
success and failure; no parser temporary file is retained as raw data.

DWD `CLAT`/`CLON` decode as `tlat`/`tlon` with exact declared units `Degree N`
and `Degree E`. Both arrays must be non-empty, equal length, finite, and use the
same non-empty DWD grid UUID and `unstructured_grid` identity as every attached
message. Latitude is accepted only in `[-90, 90]`. Longitude is accepted only
in the canonical `[-180, 180]` range and is **rejected**, not normalized, when
outside that range. This preserves provider grid identity and prevents silent
coordinate wrapping before nearest-cell selection.

The ICON deterministic integrity suite fail-closes when `metadata.json` is
missing, when `metadata.json.sha256` is missing or tampered, when JSON is valid
but not in its canonical byte representation, and when metadata's payload
digest differs from the expected retained payload digest. It also rejects `..`
path escapes and, where the Windows host permits creating a directory symlink,
rejects a symlink/reparse-point reference that resolves outside the configured
raw root. The symlink check is skipped only when the host security policy does
not permit creating the test link; it never relaxes connector behavior.

The DWD static terrain listing and object were reached on 2026-08-21:

```text
https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/
https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2
compressed bytes: 1,313,525
```

The original 2026-08-20 00 UTC lead-12 request returned HTTP 404 and remains a
recorded failure, not a data success. A retry inspected current official cycle
directories and used exact hrefs from the DWD 12 UTC listing only. The complete
smallest factual field set for cycle/valid time `2026-08-20T12:00:00Z`, lead 0,
was retained: `T_2M` (2,970,882 compressed bytes), `U_10M` (3,878,199), `V_10M`
(3,518,048), time-invariant `HSURF` (1,314,087), and the required native-grid
CLAT/CLON products (1,264,311 and 1,398,271). The latter decode with ecCodes as
`tlat`/`tlon` in `Degree N`/`Degree E`; they are required because these ICON
unstructured-grid forecast messages do not carry `latitudes`/`longitudes` keys.

The connector retained a 16,894,069-byte decompressed six-message GRIB2 artifact
at `tmp-icon-real-20260821/dwd-icon/04cfe27cc6681ac1f8a685e882824fcdcc21e05ba5da1995d9963c67a9f56f21/icon_2026082012_000.grib2`,
SHA-256 `04cfe27cc6681ac1f8a685e882824fcdcc21e05ba5da1995d9963c67a9f56f21`.
Canonical metadata is beside it with SHA-256
`e365ebcf9ae95723c3951bec813c04088c2bb0dd6719094a59b749ad6780ca79` and a
`metadata.json.sha256` integrity sidecar. The six exact official URLs appear in
that canonical metadata and are under the corresponding `12/t_2m`, `u_10m`,
`v_10m`, `hsurf`, `clat`, and `clon` directories using the observed
`2026082012` filenames.

WSL ecCodes parsed six real messages (`2t`, `10u`, `10v`, `HSURF`, `tlat`,
`tlon`). For requested Everest `(27.9881, 86.9250)`, the native provider cell is
`(27.926742553710938, 86.921875)`, DWD grid UUID
`a27b8de618c411e4820ab5b098c6a5c0`, index `818403`, spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. Explicit conversion produced
timestamp/cycle `2026-08-20T12:00:00Z`, lead 0, altitude `5830.964752197266 m`,
temperature `0.32810363769533524 C`, wind speed `3.5184451983214364 m/s`, wind
direction `254.03374128644649 degrees`, null precipitation/visibility, and
`[missing_value]` QC. No values were invented or silently substituted.

The then-DBRE-ready raw descriptor was the artifact path, SHA-256, size, six-url
canonical metadata, retrieval timestamp `2026-08-21T02:56:40.309778+00:00`,
cycle/valid time `2026-08-20T12:00:00Z`, and lead `0` above. It must be passed
through `compose_icon_ingestion_adapter`. The statement that DBRE had not yet
persisted it was true for this older project-root artifact and is superseded by
the approved-root final DBRE record below. This remains historical endpoint/raw-
processing evidence only, not a current-health or operational-service claim.

This connector-level configuration and reference-validation change does not
close ADR-010 Gate C. It does not move, copy, hash, reopen, or reuse the
historical project-root `tmp-icon*` artifacts; operational retention/access/
disposition policy and independent QA evidence remain required.

### EV-DATA-001-E-ROOT-SMOKE

Fresh raw-retention smoke using the current connector and
`EVEREST_RAW_ROOT=D:\\Everest-data\\raw`; this smoke assignment itself invoked
no backend, PostgreSQL, API, or lifecycle change. Its artifact was later used by
the final disposable DBRE execution. Retrieval UTC was
`2026-08-21T03:59:32.333262Z`; independent checks ran at
`2026-08-21T04:12:21.662491Z`. Old project-root `tmp-icon*` artifacts were not
inspected or used. AOI scalars: `aoi_id=everest-south-route`,
`aoi_version=everest-south-route-v1.0`,
`aoi_scope_id=everest-south-route-v1.0-expanded-2000km`; requested WGS 84 point
`27.98806,86.92528`. Cycle/lead/valid were
`2026-08-21T00:00:00Z` / `0` hours / `2026-08-21T00:00:00Z`.

Retention scalars were owner `Everest Manager`, class `operational_raw`, period
`24 months from acquisition`, and disposition `controlled disposition after
expiry and hold checks; not automatic deletion; retained/not disposed`.
Payload path was
`D:\\Everest-data\\raw\\dwd-icon\\e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57\\icon_2026082100_000.grib2`;
decompressed size/hash were `17,624,861` bytes /
`e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57`.
Sibling metadata was `1,392` bytes, SHA-256
`cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf`;
the `65`-byte sidecar file SHA-256 was
`0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46`, and its
declared digest matched metadata. All three paths were independently confirmed
contained beneath the raw root and in one artifact directory.

Exact official URLs and compressed/decompressed bytes were, in field order:
`T_2M` `https://opendata.dwd.de/weather/nwp/icon/grib/00/t_2m/icon_global_icosahedral_single-level_2026082100_000_T_2M.grib2.bz2` (`3,338,757`/`3,323,939`); `U_10M` `https://opendata.dwd.de/weather/nwp/icon/grib/00/u_10m/icon_global_icosahedral_single-level_2026082100_000_U_10M.grib2.bz2` (`3,876,736`/`3,860,511`); `V_10M` `https://opendata.dwd.de/weather/nwp/icon/grib/00/v_10m/icon_global_icosahedral_single-level_2026082100_000_V_10M.grib2.bz2` (`3,885,537`/`3,870,728`); `HSURF` `https://opendata.dwd.de/weather/nwp/icon/grib/00/hsurf/icon_global_icosahedral_time-invariant_2026082100_HSURF.grib2.bz2` (`1,313,525`/`1,369,453`); `CLAT` `https://opendata.dwd.de/weather/nwp/icon/grib/00/clat/icon_global_icosahedral_time-invariant_2026082100_CLAT.grib2.bz2` (`1,264,300`/`2,574,603`); `CLON` `https://opendata.dwd.de/weather/nwp/icon/grib/00/clon/icon_global_icosahedral_time-invariant_2026082100_CLON.grib2.bz2` (`1,398,235`/`2,625,627`).

WSL ecCodes `2.47.1` parsed six messages, each `2,949,120` values: `2t`,
`10u`, `10v`, `HSURF`, `tlat`, `tlon`. Native point was
`(27.926742553710938,86.921875)`, UUID
`a27b8de618c411e4820ab5b098c6a5c0`, index `818403`, spatial key
`icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. Values/QC normalized to
altitude `5830.964752197266 m`, temperature `-3.3708862304687273 C`, wind
speed `2.0440636678148207 m/s`, direction `286.0613838292081 degrees`, null
precipitation/visibility, `[missing_value]`. Windows ecCodes lacked its native
library; WSL performed the real parse. ICON tests were `42 passed`; Black and
compileall passed. The original Pylint run was `9.11/10` and exited non-zero on
the unavailable external `weather_ingestion_contract` import. That environment
blocker was superseded by `EV-DATA-001-QUALITY-MET`: the editable workspace
package is installed through `services/weather/requirements-local.txt`, the
project root is supplied through `PYTHONPATH` for absolute `services.*`
imports, and no `import-error` suppression is used. The documented invocation
in `services/weather/QUALITY.md` passed Black, Pylint `10.00/10`, compileall,
and all `80` weather tests on 2026-08-21. These quality results do not change
the fact that the earlier smoke assignment itself was raw-only; the final
disposable DBRE lifecycle evidence is recorded below.

The ICON adapter is deliberately thin and meteorology-owned. It uses the same
owner-neutral `IngestionPort` boundary as GFS while retaining its independent
provider parser, normalizer, provenance checks, and future AIFS boundary:

```python
from services.weather.icon import compose_icon_ingestion_adapter

adapter = compose_icon_ingestion_adapter(service)
artifact_id = adapter.ingest(raw_icon_metadata, canonical_icon_records)
```

It imports only `RawArtifactDescriptor`, `CanonicalRecordInput`, and
`IngestionPort` from the shared package, never FastAPI, ORM/session, HTTP, or
ecCodes types. It
rejects mismatched source/model, record type, cycle, lead, valid time, or missing
native `spatial_key` **before** calling the injected backend port. The adapter
contract was exercised by the final disposable DBRE execution below. That
execution does not complete Gate C-Operational or establish a production
service.

### Historical predecessor ICON Gate C-Core/DBRE evidence

> **Historical notice:** This 53-pass/port-47189 execution remains factual prior
> evidence, but it is superseded by the authoritative 58/58, ICON-2/2 execution
> on disposable port `46583` at the top of this handoff. It is not the current
> post-review test record.

The controlled execution used the checked-in `compose_icon_ingestion_adapter`,
the approved external raw root, and pinned disposable PostgreSQL at
`localhost:47189`. Migrations `0001`–`0006` applied. The full suite passed
`53 passed, 0 failed, 0 skipped`, and the focused ICON PostgreSQL/API tests
passed `2/2`. The successful path persisted exactly one raw artifact, one
canonical record, and one append-only acceptance audit event (`raw=1`,
`record=1`, `audit=1`). This supersedes the earlier `49/49`/port-`53112`
execution.

The raw descriptor referenced only the approved-root retained artifact:

```text
path: D:\Everest-data\raw\dwd-icon\e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57\icon_2026082100_000.grib2
payload bytes: 17624861
payload SHA-256: e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57
metadata.json bytes: 1392
metadata SHA-256: cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf
metadata.json.sha256 bytes: 65
sidecar file SHA-256: 0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46
```

Persisted retention facts were owner `Everest Manager`, class
`operational_raw`, policy version `2026-08-21.v1`, period `24 months from
acquisition`, disposition state `retained`, hold state `none` (not held), and a
non-null retention due date. Controlled disposition still requires expiry and
hold checks plus explicit approval; DBRE cleanup did not remove the retained
approved-root artifact.

The service began with lifecycle/health `configured`/`unknown` and changed them
to `verified`/`healthy` only after the canonical transaction committed. Its
historical `last_success_at` was `2026-08-21T03:59:32.333262+00:00`. The bounded
`GET /api/weather/forecast?source=dwd-icon` query returned HTTP `200` with one
canonical record:

```text
source/model: dwd-icon / ICON
record_type: forecast
timestamp: 2026-08-21T00:00:00Z
forecast_cycle: 2026-08-21T00:00:00Z
forecast_lead_seconds: 0
spatial_key: icon:a27b8de618c411e4820ab5b098c6a5c0:818403
latitude/longitude: 27.926742553710938 / 86.921875
altitude: 5830.964752197266 m
temperature: -3.3708862304687273 C
wind_speed: 2.0440636678148207 m/s
wind_direction: 286.0613838292081 degrees
precipitation/visibility: null / null
quality_flags: [missing_value]
```

The public JSON contained no approved-root path, DWD provider URL, payload hash,
raw metadata, retention, hold, disposition, or audit fields. The negative
raw-first case deliberately caused canonical persistence to fail: one classified
raw artifact remained, no canonical record was inserted, and source lifecycle/
health remained `configured`/`unknown` with no escalation.

The previous API acceptance run failed because the shared response projection
omitted the persisted `spatial_key`. This identifiable defect occurred twice
(`occurrence_count=2`). The successful fix added the field to the shared
allow-listed projection used by current, forecast, and profile responses, while
preserving all raw/private exclusions. The final `53 passed, 0 failed, 0 skipped`
and `2/2` execution
supersedes the failed run but does not erase its occurrence history.

The disposable database, container/volume, listener, and port `47189` resources
were removed after success. Consequently, `verified`/`healthy` are historical
canonical-commit facts; current health and API availability are `unknown`.
Gate C-Core/DBRE evidence is complete, Gate C-Operational remains incomplete,
and no live, continuous, or production ICON service is claimed. Phase F AIFS
was not started.

### ICON connector-output metadata boundary

`icon_raw_retention_metadata_from_retrieval()` is the sole authoritative
conversion from connector-produced `RawRetrieval` output to
`IconRawRetentionMetadata`. Before adapter composition it re-reads and verifies
the retained payload, canonical `metadata.json`, and mandatory
`metadata.json.sha256`; checks payload size/hash and the sidecar's declared
metadata hash; checks source, model, URLs, fields, cycle, lead, valid time, and
AOI provenance against the connector return value; and returns both the exact
`metadata_sha256` and the SHA-256 of the sidecar file as `sidecar_sha256`.
Missing files, malformed/noncanonical metadata, and any size/hash/provenance
mismatch fail before the backend ingestion port is called.

Connector metadata stores `cycle`, `valid_time`, and `retrieved_at` as
timezone-aware UTC ISO-8601 strings. `valid_time_epoch` is an optional separate
integer compatibility fact and must equal the ISO value when present; it never
replaces `valid_time`. The approved scope key remains `aoi_scope_id` from
connector metadata through scalar projection as `provider_aoi_scope_id`.
Nested provider provenance, URL arrays, requested coordinates, and other
canonical metadata remain only in the immutable sidecar; the owner-neutral DTO
receives an allow-listed scalar projection.

The conversion has a read-only compatibility branch for previously retained,
immutable ICON sidecars whose historical `valid_time` is an epoch number. It
normalizes that value to UTC for adapter use without rewriting the artifact.
All newly produced connector metadata uses the ISO-8601 field plus the separate
`valid_time_epoch` fact; the historical branch is not an authorized write
format.

Provider facts use `provider_*` names (`provider_payload_sha256`,
`provider_metadata_sha256`, `provider_sidecar_sha256`, and corresponding
identity/time/AOI fields). They do not use backend lifecycle vocabulary such as
`hold_state`; “not held” is prose only, while the persisted backend value is
`none` from the enum (`none`, `held`, `released`, `unknown`). The connector
does not fabricate retention owner, class, period, disposition, or hold facts. Backend
policy remains backend-owned; composition may inject explicitly approved
scalar facts only under the distinct `backend_*` allow-list. The adapter does
not require such injected facts, and backend persistence remains responsible
for its own retention decision.

This metadata review fix used synthetic connector-shaped filesystem output
only. It performed no external retrieval, raw-artifact modification, database
or API operation, or source lifecycle/status change.

Python standard-library documentation consulted for this boundary:
[`hashlib`](https://docs.python.org/3/library/hashlib.html),
[`json`](https://docs.python.org/3/library/json.html), and
[`datetime`](https://docs.python.org/3/library/datetime.html).

### EV-DATA-001-E-REVIEW-FIX-INTEGRATE

The concurrent integration root cause had occurred once during full-suite
collection before this assignment. The authoritative conversion remains defined
exactly once in `services/weather/icon/ingestion.py` and is exported by
`services/weather/icon/__init__.py`. ICON tests and the retained-artifact
integration test import this public API consistently from the package; only
connector-specific test types remain direct connector imports. A deterministic
regression check protects both the single definition and public export.

The retained-artifact integration assertions now use the conversion result's
independent `metadata_sha256` and `sidecar_sha256` fields and the adapter's
`provider_metadata_sha256` / `provider_sidecar_sha256` scalar projection. They
do not expect those computed integrity facts to be fabricated inside provider
sidecar metadata, and they do not introduce provider-owned retention policy.
This integration repair performs no external retrieval, raw operation,
database/API operation, or lifecycle/status change. Python's official import
system reference was consulted:
<https://docs.python.org/3/reference/import.html>.


## EV-AWS-STATION-001 / EV-SAT-001: New-source connector evidence (ADR-019)

**Date:** 2026-08-24  
**Status:** connected (real-data retrieval/parse/QC passed); NOT verified
(no DB/API/review yet). Facts verified against official docs; PENDING items not
claimed.

### Everest AWS observations (services/weather/everest_aws/)

- Source: AppState Everest Weather Portal (scidata.appstate.edu/everest/)
  hourly CSV feed (Base Camp / Camp 2 / South Col), public, no auth. No
  license stated -- display/research use only; commercial use NOT authorized;
  data not QC-adjusted by provider.
- Real retrieval (2026-08-24): Base Camp 421,365 B (7,322 rows, 2025-10-23..
  2026-08-24, temp -16.5..10.9 C, 31 missing flags, **4 precipitation
  anomalies flagged**); Camp 2 405,452 B (7,309 rows, temp -24.6..4.0 C, QC
  PASS); South Col 182,607 B (2,871 rows, 2026-04-26.., temp -22.9..5.5 C, QC
  PASS). Raw files: D:\Everest-data\raw\everest-aws\.
- Parser normalizes NPT (UTC+5:45) to UTC; columns located by header name;
  unnamed provider columns never assigned semantics.
- 5 unit tests pass.

### Himawari-8/9 (services/satellite/himawari/)

- Source: NOAA AWS S3 
oaa-himawari9 (anonymous); Himawari Standard Data
  FLDK, 16 bands x 10 segments, bz2. Free distribution with attribution
  (HimawariCloud is NMHS-only, not usable).
- Real retrieval (2026-08-24T13:50Z slot): band 3 segment 1
  (HS_H09_20260824_1350_B03_FLDK_R05_S0110.DAT.bz2, 9,816,761 B) downloaded,
  decompressed 96,801,523 B; satellite name and FLDK observation area
  verified in header; QC PASS. Raw: D:\Everest-data\raw\himawari\.
- Connector discovers the band-dependent R code via S3 ListObjectsV2 (not
  guessed).
- **Pending:** full field-level band/geometry decode and calibration requires
  the official JMA Himawari Standard Data format guide (PDF not machine-readable
  this session); documented as the next step.
- 5 unit tests pass.

Remaining for all: normalizer -> canonical model -> PostgreSQL/object storage ->
service API -> integration tests -> review -> QA.
