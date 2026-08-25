# AUTHORITATIVE CURRENT STATUS — EV-DATA-001-F-QA-STOP

> **Effective date:** 2026-08-22  
> **Authority:** This banner and the final record
> [`EV-DATA-001-F-QA-STOP`](#ev-data-001-f-qa-stop--amended-phase-f-stop-gate)
> are the controlling QA status for the complete A-F delivery. If any
> historical record below conflicts with them, this banner and that record
> control.
>
> - **Phase E / Gate C-Core: ACCEPTED.** The authoritative final full-pipeline
>   evidence is recorded in
>   [`EV-DATA-001-E-QA-FINAL-2`](#ev-data-001-e-qa-final-2--final-full-pipeline-dbre-re-evaluation):
>   **58 passed, 0 failed, 0 skipped**, and the focused ICON composition result
>   was **2 passed**.
> - **Current ICON health and API availability: `unknown`.** The disposable
>   PostgreSQL/API environment was removed after acceptance; historical in-run
>   `verified`/`healthy` evidence is not a current operational-health claim.
> - **Gate C-Operational: OPEN.** IAM/ACL, legal/WORM, production audit, and
>   authoritative Git-exclusion controls remain production/shared-deployment
>   blockers. They do not invalidate the accepted Gate C-Core evidence.
> - **Phase F AIFS source/core acceptance: PASS.** The authoritative hardened
>   evidence is `apps/api` **66 passed, 0 failed, 0 skipped** (`DBRE66`),
>   focused AIFS **4 passed, 0 failed, 0 skipped** (`AIFS4`), and meteorology
>   AIFS **37 passed, 0 failed, 0 skipped** (`met37`). It covers retained real
>   data, five-message decode, normalization/QC, persistence
>   (`raw=1`, `record=1`, `audit=1`), and HTTP `200` API evidence with
>   `model=AIFS`. Historical disposable `verified`/`healthy` applies only after
>   canonical commit; current runtime health remains `unknown` after teardown.
> - **Frontend display: DEFERRED / NOT A STOP GATE.** Amended `AGENTS.md`
>   explicitly defers frontend display to a separately authorized delivery.
>   The no-new-UI prohibition remains in force. Absence of a frontend is not a
>   Phase-F failure and does not authorize UI work.
> - **Complete A-F stop gate and corrected final-report evidence: PASS.** All
>   four forecast sources have accepted historical disposable evidence through
>   the required backend delivery boundary. The Phase-F report is accepted only
>   together with its authoritative hardened AIFS correction (`DBRE66` /
>   `AIFS4` / `met37`); its older `61/61`, `3/3`, port `44859`, and
>   frontend-blocker wording are superseded.
> - **MANDATORY STOP REACHED.** EV-DATA-001 phases A-F pass the authorized
>   source/core delivery stop gate. Delivery must stop. Everest AWS, Pyramid,
>   satellite, terrain, environmental, OpenStreetMap/OSM, AI, and Risk work
>   must not begin without a new explicit authorization and governance cycle.
>
> **Historical-record interpretation:** Earlier conclusions stating that Phase
> E was blocked, that ICON had no accepted DB/API or DBRE evidence, or that ICON
> DB/API execution was unauthorized were accurate at the time they were written
> but are now **historical/superseded for current Phase E status** by
> [`EV-DATA-001-E-QA-FINAL-2`](#ev-data-001-e-qa-final-2--final-full-pipeline-dbre-re-evaluation).
> Earlier statements that Phase F was pending final code review, frontend
> display, or another closure QA are likewise **superseded**.
> Evidence and failure history below are intentionally retained and must not be
> read as the current handoff verdict.

> **Post-review evidence clarification:** `58` is the full `apps/api` test
> count, not a path named `apps/api58`. The exact post-review DBRE evidence and
> the E-001 through E-010 disposition mapping are recorded in
> `docs/management/decisions.md` under
> `EV-DATA-001-E-REVIEW-CLOSURE-EVIDENCE`.

> **Phase-F stop clarification:** This acceptance does not convert historical
> health into current health, authorize production/shared deployment, close
> Gate C-Operational, or authorize frontend implementation. Gate
> C-Operational is production-only and remains open.

# Phase A Registry QA Record

## EV-DATA-001-FULL-AUDIT — Current Audit Record

> **Historical status notice:** This audit's Phase E blocked/no ICON DB/API
> conclusion is superseded for current sequencing by the
> [authoritative current-status banner](#authoritative-current-status--ev-data-001-e-qa-handoff-clean)
> and the later
> [`EV-DATA-001-E-QA-FINAL-2`](#ev-data-001-e-qa-final-2--final-full-pipeline-dbre-re-evaluation)
> acceptance. Its evidence remains part of the audit history.

**Review date:** 2026-08-21
**Scope:** From-scratch review against the latest `AGENTS.md`.
**Verdict:** Delivery blocked at Phase E; no ICON DB/API or AIFS execution.

### Verification snapshot

- Root test command with workspace/API import paths: `114 passed, 14 skipped,
  1 warning`.
- `compileall` for weather, the shared contract, and API: passed.
- Pylint currently reports `9.92/10`; the required quality gate is not green.
- `D:\Everest-data\raw`, `docs/everest-aoi.md`, and `docs/weather-spec.md`
  exist.
- The workspace is not a Git checkout. Raw tracking/exclusion and history
  evidence cannot be verified here.
- Existing project-root `tmp-icon*` and `tmp-gfs*` artifacts remain untouched
  and are not compliant durable raw storage.

### Current status

- Phase A/B, ECMWF IFS, and NOAA GFS have historical acceptance records.
- ICON has historical official retrieval, parsing, normalization, approved-root
  smoke, shared adapter, retention-model, and semantic-test evidence, but no
  accepted ICON PostgreSQL/API result or Phase E final QA. ICON is not
  `verified`; current health is `unknown`.
- AIFS has not started and remains blocked by the strict A-F sequence.
- AOI Gate A is approved for the WGS-84 summit center and documented 2,000 km
  geodesic expansion.
- Gate C remains blocked by unresolved ACL/IAM, legal/WORM, Git-bearing
  exclusion, and historical raw disposition evidence.

### Repeated-failure escalation audit

The three-occurrence escalation rule is now recorded in `AGENTS.md` and
`docs/management/decisions.md`. This audit found no evidence that one identical
root-cause signature reached three occurrences. No fourth-attempt escalation is
claimed. Future identical failures must pause at the third occurrence and
record official documentation, complete logs, root cause, next-run
command/configuration, prerequisites, expected evidence, and cleanup/rollback.

This audit does not authorize external acquisition, raw reuse, ICON DB/API,
AIFS implementation, or release.

## EV-DATA-001-A-QA — 2026-08-21

**Scope:** Independent, report-only acceptance verification of the Phase A data
registry implementation. No business code or test code was changed.

**Acceptance verdict: FAIL — Phase A must not be accepted and Phase B remains
blocked.** The implementation is appropriately limited to the registry boundary,

## Evidence Reviewed

- `AGENTS.md`, especially EV-DATA-001 registry requirements (lines 133–144),
  lifecycle evidence rules (lines 128–131), phase ordering (lines 111–121), and
  mandatory Python quality gates (lines 71–86).
- `docs/architecture/architecture.md`, including the Phase A boundary (lines
  3–8), no-external-dependency registry contract (lines 21–25), required
  database test strategy (lines 95–104), and exit criteria (lines 106–113).
- Backend contracts, validation, service, SQLAlchemy models/repository, Alembic
  environment and migration under `apps/api/everest_api/` and
  `apps/api/alembic/`.
- Existing tests: `apps/api/tests/test_registry_validation.py`,
  `test_registry_service.py`, and `test_migration_contract.py` (8 tests total).
- Phase-A documentation: `docs/data-sources.md`, `docs/api/API.md`, and
  `docs/management/decisions.md`.

## Findings

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| QA-A-001 | High | The public `RegistryService.change_status()` allows an unverified source to progress through `planned -> configured -> connected -> verified` solely through application commands. `apps/api/everest_api/registry/service.py:45–53` calls `validate_status_transition()` only; `apps/api/everest_api/registry/validation.py:15–22, 51–56` permits both transitions; no connector/evidence interface exists. This conflicts with `AGENTS.md:128–131` and `docs/architecture/architecture.md:67–69`, which require real connector acceptance before `connected` or `verified`. A caller can therefore create a false lifecycle claim during Phase A. | Backend must restrict evidence-bearing transitions until their connector phases provide recorded acceptance evidence, or require a future evidence port that Phase A cannot satisfy. Add regression coverage for the rejected paths. |
| QA-A-002 | High | Required executable migration and persistence tests are absent. The architecture requires disposable-PostgreSQL upgrade/downgrade, persistence constraints, and transaction rollback tests (`docs/architecture/architecture.md:95–103`; ADR-005 at `docs/management/decisions.md:42–48`). `apps/api/tests/test_migration_contract.py:13–32` only searches migration source text. There are no tests exercising `SqlAlchemyRegistryRepository`, `SqlAlchemyRegistryUnitOfWork`, database check/FK/index constraints, migration upgrade/downgrade, or rollback. | Add isolated PostgreSQL-backed tests which apply `upgrade` and `downgrade`, verify the created schema/constraints, and exercise commit/rollback and repository behaviour. Do not substitute SQLite for PostgreSQL migration acceptance. |
| QA-A-003 | Medium | The required `pylint` quality gate does not pass. `python -m pylint everest_api tests alembic` ended at **8.13/10** with errors and warnings. In addition to missing installed dependencies (below), it reports framework/dataclass exceptions without narrowly documented configuration: `R0902` in `registry/contracts.py:43,75,91`; `R0903` in `persistence/database.py:10` and `registry/models.py:16,80,133`; and Alembic-specific naming/import/order issues in `alembic/env.py:7–11` and `alembic/versions/20260821_0001_data_source_registry.py:1,8–14,153`. | Establish project lint configuration with concise, scoped exceptions for generated/framework-required Alembic and SQLAlchemy constructs; resolve all remaining real lint violations; run the required lint gate in the project environment. |
| QA-A-004 | Medium | The declared runtime/migration dependencies cannot be exercised in the supplied environment. `apps/api/pyproject.toml:10–13` declares SQLAlchemy and Alembic, but import discovery found `sqlalchemy: False`; `python -m alembic current` cannot run because the available `alembic` package lacks the normal CLI/config modules. `alembic.ini:4` also targets local PostgreSQL but no disposable database execution evidence exists. The 8 passing tests do not import SQLAlchemy models or execute a migration. | Provide a reproducible locked environment/installation path and disposable PostgreSQL test configuration in CI. QA must rerun the migration and database tests there before acceptance. |
| QA-A-005 | Medium | Required QA handoff documentation was missing at assignment start. This file now records the evidence and blockers, but no Phase-A test matrix existed previously. The only test coverage is eight unit/static checks, leaving secret-redaction, health timestamp persistence, schedule replacement, status/health independence, run-history constraints, transaction rollback, and scheduler-adapter translation unverified. | Keep this record as the QA handoff and add the missing backend-owned tests before resubmission. |
| QA-A-006 | High | The service accepts and persists supposedly “safe” failure detail without redaction or secret-pattern rejection. `apps/api/everest_api/registry/contracts.py:65–71` makes `failure_detail` arbitrary text; `validation.py:90–102` only requires a value for failed health and caps it at 1,024 characters; `sqlalchemy_repository.py:91–100` writes it after that validation. This contradicts the non-secret registry boundary in `docs/architecture/architecture.md:84–93` and its explicit required secret-redaction coverage at lines 100–103. A token, password, or signed URL passed by a future connector could be retained. | Define and enforce a redaction/safe-detail policy before persistence, and add deterministic unit and PostgreSQL persistence tests proving secrets are neither stored nor returned. |

## Boundary Verification

### Passed: no unauthorized Phase B–F implementation found

Static inspection of all Python and frontend-source patterns found:

- **No connector or external HTTP implementation:** no imports/usages of
  `requests`, `httpx`, `urllib`, `aiohttp`, sockets, or HTTP client code. The
  only URLs are registry documentation in `docs/data-sources.md`; no code calls
  them.
- **No API route/framework implementation:** no FastAPI, Flask, Starlette,
  router, or route-decorator code. `docs/api/API.md:3–8,32–33` explicitly
  reserves, rather than registers, routes.
- **No frontend implementation or external frontend calls:** no TypeScript,
  JavaScript, React, or web source files were present.
- **No weather schema / Phase B implementation:** no canonical weather model,
  weather-spec handoff, parser, normalizer, QC, GRIB/NetCDF/xarray code, or
  `services/weather/` implementation exists.
- **No forecast connectors / Phase C–F implementation:** no ECMWF IFS, NOAA
  GFS, DWD ICON, or ECMWF AIFS connector source is present; no retrieval,
  external call, raw payload, or successful/verified source claim was found.
- **No hard sleeps:** scan found no `sleep(` or `waitForTimeout` usage.

The registry model itself contains the required registry fields and declarative

## Checks Run

| Check | Result | Evidence |
| --- | --- | --- |
| `python -m pytest -q` | PASS | `8 passed in 0.02s` from `apps/api`. This validates only the existing unit/static suite. |
| `python -m black --check --line-length 80 everest_api tests alembic` | PASS | `15 files would be left unchanged.` |
| `python -m compileall -q everest_api alembic tests` | PASS | Exit 0; no output. |
| `python -m pylint everest_api tests alembic` | FAIL | Exit failure; 8.13/10 with the findings in QA-A-003. |
| `python -m alembic current` / migration execution | BLOCKED | The installed `alembic` namespace has no executable `__main__` or `alembic.config`; SQLAlchemy is not installed in the active interpreter. No migration was applied and no database was modified. |
| Static repository boundary scan | PASS | No code-level HTTP client, connector, API-router, weather-schema, GRIB/NetCDF, or frontend-call pattern found. Documentation-only source URLs were reviewed separately. |

## Resubmission Exit Criteria

1. Resolve QA-A-001 so `connected` and `verified` cannot be asserted without
   actual phase-appropriate connector acceptance evidence.
2. Resolve QA-A-006 so raw secret-bearing failure details cannot be persisted.
3. Resolve QA-A-002 and QA-A-004 with repeatable PostgreSQL-backed migration,
   constraint, repository, and rollback tests that run in the declared project
   environment.
4. Resolve QA-A-003: the required Black and Pylint gates must pass with
   framework-specific lint exceptions explicitly scoped and explained.
5. Retain the confirmed Phase-A-only boundary: no connector, external call,
   API route, frontend code, or weather schema may be introduced to address
   these findings.

---

## EV-DATA-001-A-QA-RETEST — 2026-08-21

**Scope:** Independent, report-only retest of backend remediation. No business
code or test code was modified.

**Retest verdict: CONDITIONAL PASS — the two High implementation findings are
fixed and all executable non-database gates pass. Phase A acceptance remains
conditional on a real disposable-PostgreSQL execution; Phase B remains blocked
and was not advanced by QA.**

### Remediation Verification

| Prior finding | Retest result | Evidence |
| --- | --- | --- |
| QA-A-001 — unsubstantiated `connected` / `verified` lifecycle claims | **FIXED** | `apps/api/everest_api/registry/validation.py:16–24` removes routine transitions into evidence-bearing states; `:53–63` rejects either target before evaluating the state graph. `RegistryService.change_status()` at `service.py:45–53` uses this validator, so its public command now also rejects them. Regression coverage: `tests/test_registry_validation.py:49–63`. |
| QA-A-006 — secret-bearing failure detail could persist | **FIXED, within the explicitly limited documented common-pattern policy** | `registry/redaction.py:1–51` documents and implements common-token detection/redaction; `validation.py:97–111` rejects secret-bearing health commands before persistence; `models.py:176–180` independently redacts `DataSourceRunModel.failure_detail` on ORM assignment. Unit coverage in `tests/test_redaction.py:13–57` verifies passwords, bearer authorization, credential-bearing URLs, AWS access-key IDs, service-layer rejection, and ORM redaction. The policy correctly states it is not a general secret-scanning guarantee; future connectors must supply structured safe diagnostics. |
| QA-A-003 — Pylint quality gate | **FIXED** | Narrowly documented project exceptions are now in `pyproject.toml:36–47`; Alembic-specific inline explanations are in `alembic/env.py:3–4` and migration `:8–9`. The valid file-target lint invocation passes at 10.00/10. See checks below. |
| QA-A-004 / QA-A-005 — repeatable dependency and PostgreSQL test foundation | **PARTIALLY FIXED / still unverified in this environment** | `pyproject.toml:10–14` now declares `psycopg[binary]`; active interpreter discovers SQLAlchemy, Alembic config, and psycopg. `tests/conftest.py:20–52` supplies a PostgreSQL-only `EVEREST_TEST_DATABASE_URL` fixture which runs Alembic `upgrade head` and cleanup `downgrade base` per test. `tests/test_postgres_registry.py:41–115` adds migration table, repository commit/rollback, DB constraint, and ORM-redaction tests. No test URL was supplied, so all three PostgreSQL tests skipped; no live upgrade, downgrade, constraints, or cleanup was observed. |

### Checks Run

| Exact command | Result | Evidence / limitation |
| --- | --- | --- |
| `python -m pytest -q` | **PASS with skips** | `16 passed, 3 skipped in 0.04s`. The three skips are the PostgreSQL integration tests. |
| `python -m pytest -q tests/test_postgres_registry.py -rs` | **NOT EXECUTED — configuration blocker** | `3 skipped`; each reports `EVEREST_TEST_DATABASE_URL is required for PostgreSQL tests`. Environment check confirmed `EVEREST_TEST_DATABASE_URL=UNSET`. |
| `python -m black --check --line-length 80 everest_api tests alembic` | **PASS** | `19 files would be left unchanged.` |
| `python -m pylint everest_api tests alembic/env.py alembic/versions/20260821_0001_data_source_registry.py` | **PASS** | `Your code has been rated at 10.00/10.` This explicitly targets Python files. The earlier shorthand `python -m pylint everest_api tests alembic` is not a valid equivalent in this checkout because `alembic/` is a migration-script directory without `alembic/__init__.py`; Pylint reports a directory parse error and 0.00/10 before linting project files. |
| `python -m compileall -q everest_api alembic tests` | **PASS** | Exit 0; no output. |
| `python -m alembic --help` | **PASS** | Alembic CLI and configured dependency are now available. |
| `python -m alembic upgrade head --sql` | **PASS — static SQL only** | Alembic generated PostgreSQL transactional DDL for the three registry tables, indexes, FK constraints, checks, and revision insert. It did not open a database or demonstrate DDL acceptance. |

### PostgreSQL Fixture and SQL-Migration Assessment

The fixture is an honest PostgreSQL-only design: it rejects non-PostgreSQL URLs
(`tests/conftest.py:20–27`), sets the supplied URL only on a local Alembic
`Config` (`:30–36`), runs upgrade before each integration test (`:36`), and
runs downgrade-to-base in cleanup (`:41–42`). This is a valid acceptance-test
approach and does not substitute SQLite.

However, **the evidence is not yet execution evidence**: no
`EVEREST_TEST_DATABASE_URL` was available, so no database connection was made,
all three integration tests skipped, and neither `command.upgrade()` nor
`command.downgrade()` was observed against PostgreSQL. The successful
`--sql` command proves migration rendering only. It cannot prove PostgreSQL
execution, actual constraint behavior, transaction semantics, or teardown.

One remaining coverage limitation for backend resubmission: the PostgreSQL
constraint test exercises the invalid lifecycle check and ORM redaction, but
does not yet exercise the schedule foreign key/numeric checks, run time-order
check, or downgrade postcondition. This is non-blocking for the two remediated
High findings, but should be extended when a database run is available.

### Phase Boundary Retest

Static scans of Python and frontend source found **no** external HTTP client,
connector, API framework/route, weather schema, GRIB/NetCDF/xarray, ECMWF IFS,
NOAA GFS, DWD ICON, ECMWF AIFS, or frontend network implementation. No
TypeScript/JavaScript source exists. No hard-sleep implementation was found;
redaction module and PostgreSQL tests remain registry-bound Phase A work.

### Conditions Before Unconditional Phase A Acceptance

1. Supply an isolated, disposable PostgreSQL database URL through
   `EVEREST_TEST_DATABASE_URL` and run `python -m pytest -q`; preserve the
   result showing the three integration tests executed rather than skipped.
2. Confirm cleanup by inspecting the disposable database after each test or by
   adding an explicit downgrade postcondition test.
3. Do not start or advance Phase B until this conditional acceptance is changed
   to an unconditional pass by QA.

---

## EV-DATA-001-A-QA-FINAL — 2026-08-21

**Scope:** Close the conditional Phase A QA verdict using the supplied,
independent DBRE execution evidence. No business code was changed by QA or
DBRE, and QA did not begin Phase B.

**Final acceptance verdict: PASS — Phase A Data Registry is accepted. Phase B
is now unblocked for its assigned owner, subject to normal delivery governance.**

### Basis for Closing the PostgreSQL Condition

The two conditions at lines 152–156 are satisfied by DBRE's independent,
user-approved execution evidence:

- DBRE used the official `postgres:17-alpine` image pinned to digest
  `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
- It exposed the disposable database only on temporary localhost random port
  `44766`; `EVEREST_TEST_DATABASE_URL` was scoped to the test command only.
- From `apps/api`, the exact command `python -m pytest -q` completed with
  **`19 passed in 0.76s`**. This is execution evidence: all three tests in
  `tests/test_postgres_registry.py` ran, with no skips.
- Fixture teardown was independently verified after the test command:
  `registry tables=0` and `alembic_rows=0`. This confirms the observed
  `downgrade base` cleanup condition rather than merely its fixture code path.
- DBRE removed the container, named volume, localhost listener, and temporary
  Docker proxy after verification. No persistent database, listener, or test
  infrastructure remains.

This satisfies the architectural requirement for reviewed upgrade/downgrade
testing in a disposable PostgreSQL database and closes QA-A-002, QA-A-004, and
evidence boundary (QA-A-001) and failure-detail protection (QA-A-006) remain
verified as recorded in the retest section.

### Final Quality-Gate Evidence

| Command / check | Final result |
| --- | --- |
| `python -m pytest -q` from `apps/api`, with DBRE-scoped `EVEREST_TEST_DATABASE_URL` | **PASS** — `19 passed in 0.76s`; PostgreSQL tests executed, none skipped. |
| `python -m black --check --line-length 80 everest_api tests alembic` | **PASS** — 19 files unchanged. |
| `python -m pylint everest_api tests alembic/env.py alembic/versions/20260821_0001_data_source_registry.py` | **PASS** — 10.00/10. |
| `python -m compileall -q everest_api alembic tests` | **PASS**. |
| PostgreSQL fixture teardown check | **PASS** — `registry tables=0`; `alembic_rows=0`. |

### Final Phase-A Boundary Check

The final static scope recheck remains clean. No Python code matches external
HTTP clients, connector implementations, API frameworks/routes, weather schema
terms, GRIB/NetCDF/xarray, or the four forecast connector identifiers. There
are no frontend TypeScript/JavaScript source files or frontend network calls;
there is no `services/weather/` implementation. No hard sleep exists in
implementation code; the only scan match is historical prose in this QA record.

Accordingly, the remediation and its PostgreSQL tests remain Phase-A registry
work only. They did not introduce Phase B weather schema work or any Phase C–F
connector/retrieval work.

### Handoff

QA accepts **EV-DATA-001 Phase A**. The dependency recorded for
`EV-DATA-001-B` in `docs/management/board.md:11` is satisfied: **Phase B may
now be started by its assigned meteorology owner.** This QA assignment does not
perform Phase B work or change its owner/status.

---

# EV-DATA-001-B-QA — 2026-08-21

**Scope:** Independent acceptance QA of the Phase B canonical weather-schema
handoff. Reviewed `AGENTS.md`, the Phase A architecture/API/registry handoffs,
the Phase B meteorology handoff, and the complete `services/weather/` source and
test surface. No business or test code was changed; this QA record is the only
modified deliverable.

## Findings first

| ID | Severity | Finding and exact references | Disposition |
| --- | --- | --- | --- |
| QA-B-001 | Low | The three executable tests provide useful smoke coverage, but do not directly lock all acceptance semantics. In particular, `services/weather/tests/test_contract.py:35-61` has no explicit test for satellite/derived identity, non-forecast rejection of forecast identity, UTC rejection, every core-field boundary, or preservation of caller-supplied flags. The implementation nevertheless contains the relevant record-type and validation logic at `services/weather/contract.py:14-20, 87-160`. | **Non-blocking test-debt.** Before Phase C merges its first normalizer, meteorology should expand contract tests for the listed invariants. This is not a schema defect and does not authorize connector work as part of this QA assignment. |
| QA-B-002 | Low | Raw-artifact retention and duplicate detection are deliberately policy-only in Phase B: the policy is exact at `docs/meteorology/weather-spec.md:93-108`, while `services/weather/contract.py` has no raw store, deduplication service, or persistence dependency (and should not at this phase). `QualityFlag.DUPLICATE` exists at `contract.py:23-35` for a later pipeline to apply. | **Expected Phase B boundary, non-blocking.** The Phase C persistence/normalization design must implement this policy rather than treating presence of the enum as duplicate detection. |

**Acceptance verdict: PASS WITH NON-BLOCKING TEST DEBT.** The canonical
schema documentation and typed contract preserve the required Phase B semantics,
and the implementation stays within the authorized schema-only boundary.
**Phase C (ECMWF IFS) is unblocked for its assigned owner.** This verdict does
not begin, implement, or approve Phase C work.

## Contract acceptance evidence

### Mandatory core fields: meanings and units — PASS

- The mandatory serialized-contract keys are enumerated exactly as `timestamp`,
  `latitude`, `longitude`, `altitude`, `wind_speed`, `wind_direction`,
  `temperature`, `precipitation`, and `visibility` in
  `docs/meteorology/weather-spec.md:39-53`, matching the EV-DATA-001 mandatory
  list in `AGENTS.md:148-158`.
- Their meanings and units are preserved: UTC ISO-8601 timestamp; decimal-degree
  north/east coordinates; metres AMSL altitude; m/s speed; true-north clockwise
  degrees direction; Celsius temperature; interval mm precipitation; and metres
  visibility (`weather-spec.md:45-53`). The contract exposes precisely these
  fields as typed members at `services/weather/contract.py:52-61`.
- Contract QC enforces UTC-offset timestamps (`contract.py:87-91`), coordinate
  range/finite values (`:92-97`), finite numeric values (`:98-115`),
  non-negative speed/precipitation/visibility (`:116-126`), and direction in
  `[0, 360)` (`:127-131`). Unit conversion is correctly deferred to future
  normalizers but must use explicit metadata, never magnitude inference
  (`weather-spec.md:76-83`).

### Record separation and forecast identity/time semantics — PASS

- The handoff makes forecast, observation, satellite, and derived records
  distinct, defines each without silent conversion, and requires derived
  provenance to remain with its owner (`weather-spec.md:13-22`). The executable
  enum has exactly those values (`contract.py:14-20`).
- `timestamp` is consistently the valid/measurement time; forecasts additionally
  retain cycle and lead, with `timestamp == cycle + lead` (`weather-spec.md:24-30`).
  The typed `ForecastIdentity` holds `cycle` and `lead_time`
  (`contract.py:38-44`); forecast records require it and flag a mismatch
  (`:139-146`), while a non-forecast carrying it receives a provenance flag
  (`:147-148`). The regression test proves mismatch flagging at
  `test_contract.py:41-50`.
- Stable `source` and provider `model` provenance are required by the handoff
  (`weather-spec.md:32-35`) and represented as required record fields
  (`contract.py:62-64`); empty values are flagged (`:137-138`).

### Additive QC, raw retention, and deduplication — PASS AT PHASE-B BOUNDARY

- Flags are additive and records are retained rather than erased
  (`weather-spec.md:67-74, 85-91`). `validate_record()` copies supplied flags,
  returns an additive `frozenset`, and neither mutates nor deletes the frozen
  record (`contract.py:38, 82-87, 158-161`). The test at
  `test_contract.py:53-61` confirms invalid data is flagged while the record
  still contains its null value.
- Immutable, content-addressed raw payload and metadata retention is specified
  at `weather-spec.md:93-100`; the explicit no-rewrite rule is at `:95-98`.
  There is no raw-payload implementation in Phase B to contradict this policy.
- The minimum future deduplication key is exactly `(source, dataset, timestamp,
  spatial key, forecast_cycle, forecast_lead_time)`, with content hash when a
  source republishes a logical identity (`weather-spec.md:102-108`), satisfying
  `AGENTS.md:161-164`. The document correctly defines a spatial key as provider
  grid/station/pixel identity, not a normalizer-invented rounded coordinate
  (`weather-spec.md:103-105`).

## Boundary verification — PASS

The Phase B boundary expressly allows only a typed canonical contract and unit
tests and excludes connectors, retrieval, parsers, database tables, APIs,
frontend display, scheduling, and Phase C-F sources
(`weather-spec.md:110-114`). Inspection confirms:

- `services/weather/` contains only `__init__.py`, `contract.py`, and
  `tests/test_contract.py` (plus generated `__pycache__` files); `contract.py`
  explicitly states it has no I/O or connector dependency (`:1-5`).
- No `ecmwf`, `gfs`, `icon`, or `aifs` connector directory exists below
  `services/weather/`; no `services/forecast/`, `services/terrain/`, or
  `apps/web/src/` source surface exists in this checkout.
- Targeted source scans found no network-I/O primitive in `services/weather` and
  no TypeScript/JavaScript frontend source files. The broader Python scan's
  connector/API/database matches are confined to the already accepted Phase A
  registry under `apps/api`; its only Phase-B match is contract prose stating
  there are no connector dependencies (`services/weather/contract.py:4`).
- No parser, GRIB/NetCDF/xarray code, weather database persistence, API route,
  scheduler/cron execution, external call, or Phase C work was found. No hard
  sleep was found in the Phase B package.

## Checks run

| Exact command (working directory) | Result | Evidence |
| --- | --- | --- |
| `python -m pytest -q` (`D:\Everest`) | **PASS** | `19 passed, 3 skipped in 0.50s`. The three skips are the pre-existing Phase A PostgreSQL tests without `EVEREST_TEST_DATABASE_URL`; Phase B's three contract tests executed. |
| `python -m pytest -q services/weather/tests` (`D:\Everest`) | **PASS** | `3 passed in 0.01s`. |
| `python -m black --check --line-length 80 services/weather` (`D:\Everest`) | **PASS** | `3 files would be left unchanged.` |
| `PYTHONPATH=<repo root>; python -m pylint services/weather services/weather/tests` (`D:\Everest`) | **PASS** | `Your code has been rated at 10.00/10.` `PYTHONPATH` is required because package imports are rooted at `services`. |
| `python -m compileall -q services/weather` (`D:\Everest`) | **PASS** | Exit 0; no output. |

## Handoff

QA accepts **EV-DATA-001 Phase B: Weather Schema** with QA-B-001 and QA-B-002
recorded as non-blocking, implementation-boundary test debt. The canonical
contract is suitable for the next assigned phase. Phase C is **unblocked**, but
no connector, external retrieval, parser, database, API, frontend, or scheduler
work was initiated by this QA assignment.

---

# EV-DATA-001-C-QA — 2026-08-21

**Scope:** Independent Phase C ECMWF IFS acceptance review. Reviewed
`AGENTS.md`; all Phase A/B handoffs and QA records; meteorology, data-source,
API, architecture, and board documents; the complete `services/weather/` and
`apps/api/` implementation/test surfaces; and the supplied independent DBRE
evidence. No business code or test code was changed. This QA record is the only
modified deliverable.

## Findings first

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| QA-C-001 | **High** | **Precipitation normalization violates the canonical unit contract.** ECMWF `tp` is selected as an IFS field (`services/weather/ecmwf/connector.py:21-23, 73-84`), but the normalizer persists it unchanged (`normalizer.py:57`) despite the canonical contract requiring millimetres (`docs/meteorology/weather-spec.md:55, 79-85`; `AGENTS.md:157-158`). The normalizer ignores `ParsedMessage.units` entirely (`parser.py:10-24`; `normalizer.py:31-62`); its unit test locks the erroneous identity conversion by expecting `1.2` from input `1.2` (`tests/test_ecmwf.py:27-44`). IFS GRIB `tp` is accumulated depth in metres, so the canonical value must be explicitly converted to mm using declared/provider-mapped units. | Correct normalization and add deterministic unit-metadata tests for `tp` and every converted IFS variable. Invalid/unknown units must add `invalid_unit`, retain raw data, and never silently guess. Re-run real-data, PostgreSQL, and API evidence. |
| QA-C-002 | **High** | **The required Phase C quality gate fails.** `PYTHONPATH=<repo root>; python -m pylint services/weather services/weather/tests` exits non-zero at **9.66/10**, with `R0902`, `R0913`, `R0917`, `R0914`, `R0903`, `C0415`, and broad-exception `W0718` at `connector.py:26,42,57,39`, `parser.py:11,27,30`, and `tests/test_ecmwf.py:57`. Unlike the Phase A API lint configuration, these exceptions have no scoped documented disposition. This fails the mandatory Pylint gate in `AGENTS.md:83-86`. | Resolve the violations or add concise, narrow, justified framework/runtime exceptions; then rerun lint cleanly. |
| QA-C-003 | **High** | **Management handoff contradicts the claimed completion evidence.** `docs/management/board.md:12-13` still marks Phase C and C-QA `blocked`; `:30-32` says no messages were parsed, normalized, persisted, or served and source remains non-verified. That conflicts with the meteorology handoff's actual four-message parse and normalized record (`weather-spec.md:136-154`), its DBRE persistence/API result (`:156-180`), the API implementation, and `docs/data-sources.md:15-20, 50-77`, which records historical `verified` acceptance. This makes the delivery board an unreliable downstream handoff and leaves the historical evidence/current state reconciliation incomplete at governance level. | Everest Manager must reconcile the board with the factual historical acceptance and current post-teardown state: historical evidence may support `verified`; current runtime health/API availability must remain `unknown` after teardown. Do not represent the removed database's `healthy` value as current health. |
| QA-C-004 | Medium | **Retry/failure behavior is not tested.** Retry implementation catches transport failures and sleeps for exponential backoff (`connector.py:135-146`), but `tests/test_ecmwf.py:47-50` only checks that `retry_limit` is stored. It neither simulates transient failure followed by success nor exhausted retries, timeout, range failure, index parsing failure, or proves request counts/backoff behavior. The current `time.sleep()` backoff is also an unmocked wall-clock wait, contrary to deterministic test engineering. | Add injected/mocked clock/backoff and session tests proving bounded retry/failure paths without real sleeps. Keep real-data smoke separate and artifacted. |
| QA-C-005 | Medium | **Raw-store and byte-range trust checks are incomplete.** Content-addressed paths and SHA-256 metadata are created (`connector.py:85-111`) and PostgreSQL raw rows are append-only (`apps/api/alembic/versions/20260821_0002_weather_persistence.py:158-169`), but local payload/metadata files are ordinary writable files and their bytes are not rehashed after write. Further, `_get_range()` accepts HTTP 200 as equivalent to a range response without checking `Content-Range` or returned length (`connector.py:127-133`), so an origin ignoring `Range` could trigger a prohibited full-file download. No test covers either condition. | Verify written bytes against the digest; make raw-store immutability enforceable by storage policy; require valid partial-range semantics and expected byte count; add regression tests. |

**Acceptance verdict: FAIL — Phase C is not accepted and Phase D (NOAA GFS)
remains blocked.** The historical real-data/DBRE evidence is credible evidence
of an executed chain, but it cannot override an incorrect precipitation unit
implementation, a failed mandatory lint gate, and contradictory governance
handoff. This assignment does not begin Phase D.

## Required-chain evidence assessment

| Required link | Assessment | Evidence / limitation |
| --- | --- | --- |
| Official actual retrieval | **Historical PASS** | Official ECMWF Open Data directory, `.index`, and GRIB2 byte-range URL are exact at `weather-spec.md:125-138`; the selected 3,276,049-byte artifact and SHA-256 are recorded at `:136-139`. Connector is restricted to the official root at `connector.py:21, 68-84`. QA-C-005 remains open for range-response verification. |
| Raw immutability/checksum metadata | **Partial** | Connector records SHA-256, size, URLs, source/model/dataset/cycle/lead/retrieval time (`connector.py:85-111`); database stores hash/metadata and has raw-row triggers (`weather models.py:24-64`; migration `:158-169`). Local immutable retention/checksum revalidation is not proven; see QA-C-005. |
| Actual GRIB parsing | **Historical PASS** | Parser uses ecCodes and fails rather than fabricates data (`parser.py:27-83`). Historical WSL ecCodes execution parsed four actual messages/variables at Everest's nearest grid cell (`weather-spec.md:139-147`). Local native smoke is currently skipped when ecCodes is unavailable (`apps/api/tests/test_weather_persistence.py:26-38`). |
| Canonical normalization | **FAIL** | Geopotential-to-metres, Kelvin-to-Celsius, vector wind, nearest-provider-grid, forecast identity, and additive contract QC are implemented (`normalizer.py:26-65`) and historical values are recorded (`weather-spec.md:149-154`). `tp` is not converted from ECMWF depth units to canonical mm; QA-C-001 blocks this link. |
| Additive QC | **Partial** | Canonical validator is additive/non-destructive (`services/weather/contract.py:82-161`); normalizer attaches its flags (`normalizer.py:63-65`), and historical sample retained null precipitation/visibility with `missing_value` (`weather-spec.md:149-154`). The connector/normalizer does not validate declared units or emit `invalid_unit`; QA-C-001 remains. |
| PostgreSQL raw + canonical persistence | **Historical PASS; local rerun unavailable** | Raw-first separate commit and canonical dedupe/lifecycle update are implemented at `apps/api/everest_api/weather/service.py:33-68, 91-132`; models/migration have raw/canonical FK, uniqueness, and append-only triggers (`weather/models.py:24-159`; migration `:20-169`). DBRE reports `23 passed, 10 warnings`, no PostgreSQL skips, exactly one raw artifact and canonical record at `weather-spec.md:156-175` / `data-sources.md:59-75`. Current local environment has no `EVEREST_TEST_DATABASE_URL`, so 4 PostgreSQL tests skip. |
| Queryable API result | **Historical PASS** | Read-only API routes are PostgreSQL-only (`apps/api/everest_api/app.py:74-164`); DBRE recorded HTTP 200 and exactly one persisted forecast (`weather-spec.md:169-175`). No current API exists after disposable teardown, correctly documented as unknown. |
| Retry/failure tests | **FAIL** | Only configuration is tested (`services/weather/tests/test_ecmwf.py:47-50`); no behavioral retry/failure test exists. See QA-C-004. |
| Lifecycle/health truthfulness | **Partial / governance contradiction** | Service marks `verified`/`healthy` only after at least one canonical insert (`weather/service.py:39-67`); API contract states this correctly (`docs/api/API.md:75-85`). `docs/data-sources.md:35,46-48,75-77` correctly distinguishes historical verification from current `unknown` health after teardown. `docs/management/board.md:12-13,30-32` contradicts all of that; see QA-C-003. |
| Documentation | **Partial** | Excellent source-level historical URLs, timestamps, checksum, parsed variables, coordinate, DB/API result, and teardown disclosure appear in `weather-spec.md:113-269` and `data-sources.md:15-77`. Board status/claim conflict prevents acceptance. |

## Historical `verified` versus current `unknown` reconciliation

There is **no inherent semantic contradiction** in recording the persisted
disposable-test lifecycle state as historical `verified`, while recording current
operational health as `unknown`: lifecycle evidence and health are separate by
ADR-004 (`docs/management/decisions.md:33-40`). The ingestion service supports
that evidence model by setting `verified`/`healthy` only after canonical commit
(`weather/service.py:56-64`), and the test environment's destruction means that
specific `healthy` value is no longer a current operational fact. The correct
documentation treatment is used by `weather-spec.md:177-180` and
`data-sources.md:46-48, 75-77`.

The unresolved contradiction is exclusively the stale management board statement
that no parsing/persistence/API happened and that IFS is non-verified
(`board.md:12-13, 30-32`). QA-C-003 requires correction before a downstream
phase uses the board as its mandated handoff.

## Quality checks run

| Exact command | Result | Evidence / limitation |
| --- | --- | --- |
| `python -m pytest -q` from `D:\Everest` | **PASS with skips** | `24 passed, 5 skipped, 1 warning in 1.63s`. The warning is `PytestUnknownMarkWarning` for `real_data` because root-level discovery does not read `apps/api/pyproject.toml`. Skips include PostgreSQL tests without a test database and native ecCodes smoke. |
| `python -m pytest -q` from `D:\Everest\apps\api` | **PASS with skips** | `18 passed, 5 skipped in 0.40s`; the API-local marker configuration suppresses the root warning. No current DB URL was supplied, so this is not a replacement for DBRE. |
| Independent DBRE disposable PostgreSQL execution | **Historical PASS** | Latest supplied evidence: `23 passed, 10 warnings`, **no PostgreSQL skips**, on a local ephemeral random-port session at `localhost:32715`; all container, volume, listener, and resources were removed. Recorded at `weather-spec.md:156-180` and `data-sources.md:59-77`. |
| `python -m black --check --line-length 80 services/weather apps/api/everest_api apps/api/tests apps/api/alembic` from `D:\Everest` | **PASS** | `35 files would be left unchanged.` |
| `PYTHONPATH=<repo root>; python -m pylint services/weather services/weather/tests` from `D:\Everest` | **FAIL** | Exit non-zero; **9.66/10** with the violations enumerated in QA-C-002. |
| `python -m pylint everest_api tests alembic/env.py alembic/versions/20260821_0001_data_source_registry.py alembic/versions/20260821_0002_weather_persistence.py` from `D:\Everest\apps\api` | **PASS** | `10.00/10.` |
| `python -m compileall -q services/weather apps/api/everest_api apps/api/tests apps/api/alembic` from `D:\Everest` | **PASS** | Exit 0; no output. |

## Scope-isolation verification

Static inspection of all Python under `services/weather/` and `apps/api/` found
no GFS, NOAA, ICON, AIFS, Everest AWS, Pyramid, satellite, terrain,
environmental, OSM, AI, commercial weather, or prohibited-provider
implementation. There are no connector directories other than
`services/weather/ecmwf/`; `services/forecast/`, `services/terrain/`, and
`apps/web/src/` remain absent. The only external data connector is the allowed
official ECMWF IFS Open Data implementation. No Phase D work was begun.

## Resubmission exit criteria

1. Resolve QA-C-001 with declared-unit-driven IFS precipitation conversion to
   mm and invalid-unit retention/flagging tests.
2. Resolve QA-C-002 so the complete weather package/test lint command passes.
3. Resolve QA-C-003 by aligning the delivery board with the documented
   historical verification and current unknown post-teardown health state.
4. Resolve QA-C-004 and QA-C-005 with deterministic retry/failure, range, hash,
   and raw-immutability tests. No hard test sleep is permitted.
5. Re-execute the complete corrected chain against a disposable PostgreSQL
   database, retain the real-data and API artifacts, and confirm teardown.

**Handoff:** Phase C remains **blocked in QA**. Consequently **Phase D is not
unblocked** and must not be started.

---

# EV-DATA-001-C-QA-FINAL — 2026-08-21

**Scope:** Independent final QA of the Phase C meteorology/provenance
remediation. Reviewed the latest ECMWF connector, parser, normalizer, unit and
PostgreSQL tests, migrations `0001` through `0003`, backend service/API,
meteorology/data-source/API/management handoffs, and the supplied DBRE evidence.
No business or test code was changed; this QA record is the sole modified file.

## Findings first

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| QA-C-FINAL-001 | **High** | **Raw metadata integrity remains unverified after an existing metadata file is reused.** Payload retention is correctly atomic and rehashed in `services/weather/ecmwf/connector.py:179-198`, but `_write_metadata()` returns immediately for an existing `metadata.json` (`:200-205`), without reading/re-hashing it or comparing it to any persisted metadata checksum. The document claims immutable JSON metadata (`docs/meteorology/weather-spec.md:115-119`), but only payload writes/reuse are documented as rehashed (`:161-166`). `services/weather/tests/test_ecmwf.py:216-234` proves tamper detection for a raw GRIB file, not `metadata.json`. A caller can make the read-only file writable, alter its provenance fields, and future retrieval reuse will accept it silently. This violates the required immutable raw metadata and checksum-retention principle in `AGENTS.md:161-164` and `weather-spec.md:98-103`. | Store a metadata SHA-256 (in immutable/raw DB metadata or a manifest), rehash/compare existing metadata before reuse, reject mismatch, and add a deterministic metadata-tamper regression test. Then repeat the corrected disposable E2E evidence. |
| QA-C-FINAL-002 | Medium | **The final two-artifact DBRE result is supplied to QA but not yet reflected in the meteorology/data-source handoffs.** `docs/meteorology/weather-spec.md:168-252` correctly records both source artifacts and corrected canonical values, but its E2E section remains the superseded one-artifact, 0-hour `23 passed, 10 warnings` execution (`:254-278`). `docs/data-sources.md:50-77` likewise records only that superseded result. The latest supplied DBRE result is `27 passed, 16 warnings`, migration `0003`, `raw=2`, `record=1`, `assoc=1`, HTTP 200, followed by cleanup. The stale `### Persistence/API blocker for backend` at `weather-spec.md:369-380` also describes work that the existing backend code has already implemented. | Update meteorology and data-source handoffs with the final execution, exact two-artifact provenance association, corrected 3-hour response values, and teardown; remove or mark the obsolete blocker as historical. |

**Final verdict: FAIL — Phase C remains unaccepted and Phase D remains blocked.**
The remediation resolves the original precipitation, lint, retry, range-response,
raw-payload, and management-board findings, and the supplied DBRE run is strong
evidence of the corrected two-artifact chain. However, immutable **raw metadata**
is an explicit acceptance requirement, and the existing-file reuse path still
permits silent metadata tampering. QA cannot accept a completed source chain
until QA-C-FINAL-001 is fixed and retested. This assignment does not start Phase
D.

## Prior-finding retest

| Prior finding | Final assessment | Evidence |
| --- | --- | --- |
| QA-C-001 — `tp` unit conversion | **FIXED** | Declared IFS mapping explicitly requires `tp: m` (`services/weather/ecmwf/normalizer.py:19-25`), converts it with `* 1000` (`:99-101`), and rejects unknown units with additive `invalid_unit` without guessing (`:73-86`). Deterministic coverage asserts `1.2 m -> 1200 mm` and null/flagged unknown units (`tests/test_ecmwf.py:86-102`). Real recheck records `3.814697265625e-06 m -> 0.003814697265625 mm` (`weather-spec.md:186-199`). |
| QA-C-002 — weather lint | **FIXED** | `PYTHONPATH=<repo root>; python -m pylint services/weather services/weather/tests` now passes at **10.00/10**. Exceptions are scoped adjacent to the GRIB/dataclass/framework constructs (`connector.py:23,30-31,44,47,216`; `parser.py:10-11,27,32`; `tests/test_ecmwf.py:3-4,18,21,43`). |
| QA-C-003 — board conflict | **FIXED** | `docs/management/board.md:30-34` now accurately records historical end-to-end IFS evidence, current unknown health after teardown, prior QA failure/remediation, and the Phase D block. It no longer states that parsing/persistence/API did not happen. |
| QA-C-004 — deterministic retry/failure behavior | **FIXED** | Connector injects `sleep` (`connector.py:47-62`) and uses it only between bounded attempts (`:159-172`). Tests prove transient retry request count/backoff and exhausted retries with no wall-clock sleep (`tests/test_ecmwf.py:142-176`). |
| QA-C-005 — strict range/raw payload integrity | **FIXED for payload/range; metadata residual remains** | HTTP ranges now require 206, expected `Content-Range`, and exact length (`connector.py:143-157`); failure and valid partial-response tests are deterministic (`tests/test_ecmwf.py:179-213`). Payload temporary-file fsync, hash verification, atomic replacement, reuse rehash, and tamper test are implemented (`connector.py:179-198`; `tests/test_ecmwf.py:216-234`). Metadata reuse remains the separate QA-C-FINAL-001 blocker. |

## Corrected two-artifact provenance and E2E evidence

The code and migration correctly model **two distinct immutable raw facts** for
the corrected 3-hour record rather than falsely combining two source files:

- Dynamic primary artifact: SHA-256
  `7d4b2feae148ade17a90b8168091d64d0f27b40ed55aa19530c48f49d53fdf9d`,
  3,074,657 bytes, cycle `2026-08-20T00:00:00Z`, lead 10,800 seconds, valid
  `2026-08-20T03:00:00Z` (`weather-spec.md:168-194`; factual test descriptor
  at `apps/api/tests/test_weather_persistence.py:82-97`).
- Separate static-altitude artifact: SHA-256
  `529c14e03a8b22d86ff85e2bbd9d81c481ca626e410d1f6e8d875a112f4cb501`,
  896,851 bytes, same cycle, step zero, surface `z` at the same provider spatial
  key (`weather-spec.md:201-226`; test descriptor `test_weather_persistence.py:100-123`).
- Migration `0003` creates an immutable, role-constrained association with only
  `static_altitude` permitted (`apps/api/alembic/versions/20260821_0003_weather_record_provenance.py:20-60`). The service requires same source/cycle,
  distinct hash, step zero, surface `z`, same model, and same spatial key before
  associating it (`apps/api/everest_api/weather/service.py:139-185`). The
  PostgreSQL tests prove factual/idempotent association and retention of both raw
  facts when canonical persistence fails (`tests/test_weather_persistence.py:232-310`).
- The corrected record is internally consistent: grid `(28.0, 87.0)`, valid time
  `2026-08-20T03:00:00Z`, cycle `2026-08-20T00:00:00Z`, lead `10800`, altitude
  `6008.053905863623 m`, wind `0.8584101751271469 m/s` at
  `171.95415714345518°`, temperature `-1.3635162353515398 C`, precipitation
  `0.003814697265625 mm`, null visibility, and `[missing_value]`
  (`weather-spec.md:228-250`; backend descriptor
  `test_weather_persistence.py:126-146`).
- Supplied independent DBRE evidence reports the final disposable PostgreSQL run
  as **`27 passed, 16 warnings`**, with all PostgreSQL tests executing under
  migration `0003`, `raw=2`, `record=1`, `assoc=1`, and forecast API HTTP 200.
  The ephemeral local random-port database session and all associated resources
  were then removed. This is valid historical execution evidence, not a claim of
  a current healthy service.

## Practical checks run

| Exact command | Result | Evidence / limitation |
| --- | --- | --- |
| `python -m pytest -q` from `D:\Everest` | **PASS with environmental skips** | `33 passed, 8 skipped, 1 warning in 1.20s`. Root discovery does not read the API-local marker registration, causing the non-functional `PytestUnknownMarkWarning`; no current PostgreSQL URL/ecCodes binding is available locally. This does not replace the supplied DBRE execution. |
| `python -m black --check --line-length 80 services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | `36 files would be left unchanged.` |
| `PYTHONPATH=<repo root>; python -m pylint services/weather services/weather/tests` | **PASS** | `Your code has been rated at 10.00/10.` |
| `python -m pylint everest_api tests alembic/env.py alembic/versions/20260821_0001_data_source_registry.py alembic/versions/20260821_0002_weather_persistence.py alembic/versions/20260821_0003_weather_record_provenance.py` from `D:\Everest\apps\api` | **PASS** | `Your code has been rated at 10.00/10.` |
| `python -m compileall -q services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | Exit 0; no output. |

## Scope isolation

The final static source scan found no GFS, NOAA, ICON, AIFS, Everest AWS,
Pyramid, satellite, terrain, environmental, OSM, AI, commercial-provider, or
other prohibited implementation. Only the approved ECMWF IFS connector exists
under `services/weather/ecmwf/`. No Phase D work was started.

## Final resubmission condition

1. Close QA-C-FINAL-001 with metadata checksum/rehash-on-reuse and a tamper test.
2. Update the meteorology and data-source handoffs with the supplied final DBRE
   evidence and retire the obsolete backend blocker text.
3. Run the corrected chain again against an isolated disposable PostgreSQL
   database and preserve result/teardown evidence.

**Handoff:** Phase C is **not accepted**. **Phase D remains blocked** pending
the above final remediation; no Phase D activity was performed by QA.

---

# EV-DATA-001-REM-03-RAW-QA — Gate C verification — 2026-08-21

**Assignment:** `EV-DATA-001-REM-03-RAW-QA`  
**Scope:** Independent, report-only verification of the approved external raw
storage boundary and the DWD ICON raw-retention implementation. Only this QA
document was changed. No raw artifact was moved, copied, deleted, hashed,
reused, or otherwise operated on. ICON database and API execution was not
performed, as expressly prohibited by the assignment and ADR-010/ADR-011.

## Verdict

**Gate C: BLOCKED — not closed.**

The approved directory exists and the runtime root boundary is implemented and
covered by deterministic tests. The ICON connector has deterministic payload,
canonical metadata, and metadata-sidecar integrity logic and unit coverage.
Those facts are not sufficient for closure: no real connector artifact set has
been retained under `D:\Everest-data\raw` for this assignment, retention/access/
legal-hold/audit/disposition controls are documented but not runtime-proven,
and repository exclusion cannot be verified because this checkout has no Git
metadata. The existing project-root `tmp-icon*` and `tmp-gfs*` artifacts remain
explicitly noncompliant and were not touched.

## Evidence reviewed

- Latest `AGENTS.md`, including EV-DATA-001 phase ordering, approved-root,
  raw-retention, AOI, no-Git/raw-storage, and verification requirements.
- `docs/management/decisions.md`: ADR-010 and
  `EV-DATA-001-REM-03-RETENTION`; ADR-011 ICON interim status.
- `docs/architecture/architecture.md`: external raw-storage enforcement and
  its explicit path-only boundary.
- `docs/everest-aoi.md`: approved AOI identifier
  `everest-south-route`, version `everest-south-route-v1.0`, WGS 84 summit
  center, default 100 km radius, and separately approved 2,000 km expansion.
- `docs/management/board.md`: current Gate C checklist and open controls.
- `apps/api/everest_api/raw_storage.py` and
  `apps/api/tests/test_raw_storage.py`.
- `services/weather/icon/connector.py`,
  `services/weather/tests/test_icon.py`, and
  `services/weather/tests/test_icon_ingestion.py`.
- `docs/meteorology/weather-spec.md`, `docs/data-sources.md`, and
  `docs/api/API.md` for retention and status wording.

## Gate-C control assessment

| Control | Result | Independent evidence and limitation |
| --- | --- | --- |
| Approved root exists outside repository | **PASS — existence/boundary only** | Read-only filesystem check confirmed `D:\Everest-data\raw` exists as a directory. `D:\Everest\.git` is absent; the approved root is an external path. No contents were enumerated or operated on. |
| Runtime `EVEREST_RAW_ROOT` validation | **PASS — unit evidence** | `RawStoragePolicy.from_environment()` rejects missing, relative, nonexistent, and repository-contained roots (`apps/api/everest_api/raw_storage.py:63-80`; `apps/api/tests/test_raw_storage.py:33-79`). ICON repeats the runtime validation (`connector.py:197-234`; `test_icon.py:212-239`). |
| Reference boundary / fail closed | **PASS — partial coverage** | Empty and traversal references are rejected by the backend policy (`raw_storage.py:82-96`; `test_raw_storage.py:81-90`) and ICON (`connector.py:236-250`; `test_icon.py:241-257`). Absolute escapes are covered by the resolver. A dedicated symlink/junction escape test and real approved-root run are not evidenced. |
| Connector uses approved root at runtime | **NOT PROVEN** | ICON requires `EVEREST_RAW_ROOT` and has no runtime fallback (`connector.py:75-83, 204-234`). The tests use disposable `tmp_path` roots, not `D:\Everest-data\raw`; no real connector execution was run under the approved root. |
| Payload integrity | **PASS — deterministic unit evidence** | ICON performs atomic temporary write, fsync, post-write SHA-256 verification, immutable-mode attempt, and rehash-on-reuse (`connector.py:252-275`). Tests cover changed payload rejection (`test_icon.py:163-172`). No approved-root artifact evidence exists. |
| Canonical metadata integrity | **PASS — deterministic unit evidence** | Canonical JSON is verified on reuse, including UTF-8/JSON/canonical form and provenance comparison (`connector.py:290-331`). Metadata tampering is rejected (`test_icon.py:173-179`). No real retained metadata under the approved root was verified. |
| Metadata checksum sidecar integrity | **PASS — deterministic unit evidence** | `metadata.json.sha256` is written and verified; a changed sidecar is rejected (`connector.py:290-304`; `test_icon.py:180-185`). Missing sidecar is rejected by `_verify_metadata()` (`connector.py:306-314`), but a standalone missing-sidecar regression test is not present in the reviewed ICON test file. |
| Required provenance/AOI retention facts | **PARTIAL / NOT ACCEPTANCE EVIDENCE** | ICON metadata records source/provider/dataset/model/cycle/lead/valid time, URLs, format, sizes, fields, requested Everest coordinate `27.9881,86.9250`, retrieval time, and payload digest (`connector.py:336-363`). The reviewed test does not execute a real approved-root retention and does not prove `aoi_id`/`aoi_version` are persisted in the connector metadata. |
| Retention policy documentation | **PASS — documentation only** | ADR-010 and `EV-DATA-001-REM-03-RETENTION` document retention owner/class/period/due date, access, disposition, legal hold, append-only audit, artifact identity, and root controls (`docs/management/decisions.md:146-256`). The document explicitly says runtime enforcement and QA acceptance are pending. |
| Retention state persistence/enforcement | **OPEN** | No executable evidence shows retention owner/class/period/due date/disposition state persisted and queryable for each accepted raw artifact. |
| Access, legal hold, disposition, audit | **OPEN** | No runtime IAM/filesystem permission, hold lifecycle, controlled disposition, or append-only audit evidence was reviewed. These are expressly open in ADR-010 and the board. |
| Repository exclusion/tracking | **OPEN / NOT TESTABLE HERE** | The checkout has no `.git` directory, and architecture/API docs correctly make no `.gitignore` or tracking claim. Therefore exclusion enforcement cannot be asserted. Existing project-root temporary artifacts remain a documented open disposition issue. |
| AOI acquisition/reuse control | **OPEN FOR RUNTIME ACCEPTANCE** | AOI authority and version are documented, but no acquisition/reuse was authorized or executed for this assignment. Any future real run must record the applicable AOI identifier/version and remain within the approved radius. |
| ICON DB/API gate | **BLOCKED** | No ICON DB/API command was executed. ADR-010/ADR-011 and the board require Gate C plus the independent contract/ingestion gates before that work. |

## Checks run

| Exact check | Result | Evidence / limitation |
| --- | --- | --- |
| Read-only existence check for `D:\Everest-data\raw` | **PASS** | PowerShell `Test-Path -LiteralPath 'D:\Everest-data\raw' -PathType Container` returned true; no directory contents were changed or inspected for acceptance. |
| Read-only repository metadata check | **PASS — no Git metadata** | `Test-Path -LiteralPath 'D:\Everest\.git'` returned false. This prevents a repository tracking/exclusion assertion; it is not proof of Git exclusion. |
| `python -m pytest -q apps/api/tests/test_raw_storage.py services/weather/tests/test_icon.py services/weather/tests/test_icon_ingestion.py` | **PASS** | **21 passed in 0.31s**. These are deterministic unit/adapter tests using disposable test roots and fakes; they are not real approved-root retention evidence. |
| ICON DB/API execution | **NOT RUN** | Prohibited by assignment scope and current governance status. |
| Raw artifact operation | **NOT RUN** | No move, copy, delete, hash, reuse, or other operation was performed on existing raw artifacts. |

## Open controls required before Gate C closure

1. Execute an approved, artifact-producing ICON smoke run with
   `EVEREST_RAW_ROOT=D:\Everest-data\raw`, retaining payload, canonical metadata,
   and `metadata.json.sha256` beneath that root. Record real UTC times, artifact
   IDs, sizes, checksums, provenance, AOI identifier/version, and failed-path
   results without deleting the retained operational artifacts.
2. Persist and query retention owner, retention class, retention period, due
   date, and disposition state for every accepted artifact.
3. Implement and evidence least-privilege access, unauthorized access denial,
   grant/change/revocation audit, legal-hold protection and release, controlled
   disposition, and append-only audit retention/access.
4. Add and execute a deterministic symlink/junction escape test, plus an
   explicit missing-sidecar regression test, then repeat real-root evidence.
5. Establish repository exclusion/tracking evidence in a Git-bearing checkout
   without importing the existing `tmp-icon*`/`tmp-gfs*` artifacts; their
   disposition remains a separate open governance control.
6. Keep ICON DB/API execution blocked until these controls and the independent
   canonical-contract and ingestion-port gates are accepted.

**Handoff:** Gate C remains **blocked**. ICON remains not `verified`, not
currently `healthy`, and has no accepted database/API result.

---

# EV-DATA-001-C-QA-CLOSE — 2026-08-21

**Scope:** Independent closure check limited to the two final remediation items:
ECMWF raw `metadata.json` canonicalization/reuse/tamper detection and
meteorology-handoff reconciliation. Reviewed the latest connector/tests and
meteorology, data-source, API, and board documentation. No business or test code
was changed; this QA record is the only modified deliverable.

## Findings first

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| QA-C-CLOSE-001 | **Medium** | **Meteorology document reconciliation is incomplete.** The current final DBRE evidence is accurately recorded at `docs/meteorology/weather-spec.md:259-293`, and the document says the prior 23-pass record is superseded at `:128-133`. However, the same handoff still includes an obsolete one-artifact, 00-hour “Phase C ingestion integration attempt” at `:299-382` (including the superseded `a929…` raw artifact and old canonical values) and an active-looking `### Persistence/API blocker for backend` at `:384-395`, despite the implemented backend migration/API/provenance chain and final DBRE result. This directly misses the prior final disposition to retire or clearly mark the obsolete blocker as historical, and gives downstream readers two incompatible executable handoffs. | Remove the superseded one-artifact invocation or mark it explicitly historical/non-authoritative; remove or mark the backend blocker completed; leave the final corrected two-artifact 3-hour DBRE chain as the sole actionable Phase C handoff. |

**Closure verdict: FAIL — Phase C is not accepted and Phase D GFS remains
blocked.** Raw metadata integrity is now accepted, but the required meteorology
handoff reconciliation is not complete. The remaining defect is documentation
governance, not a reason to begin Phase D.

## Final-remediation verification

### Metadata JSON canonicalization, reuse, and tamper handling — PASS

- Metadata is deterministically serialized as UTF-8 canonical JSON with sorted
  keys, compact separators, and a trailing newline at
  `services/weather/ecmwf/connector.py:216-226`.
- A distinct `metadata.json.sha256` sidecar is written alongside the canonical
  JSON (`connector.py:200-213`). Both use the verified atomic payload-write
  path, which fsyncs, hashes before replacement, and applies the best-effort
  read-only bit (`:179-198, 251-256`).
- On any reuse, the connector requires both sidecar and JSON, verifies that the
  sidecar matches the expected digest, rehashes JSON bytes, parses UTF-8 JSON,
  and verifies re-canonicalization byte-for-byte (`connector.py:228-248`). It
  rejects missing artifacts, tampered JSON, tampered sidecar, malformed JSON,
  and non-canonical content rather than overwriting provenance.
- Deterministic regression coverage passes for initial canonical write and valid
  reuse (`services/weather/tests/test_ecmwf.py:236-246`), modified JSON
  (`:248-257`), missing sidecar (`:259-271`), and modified sidecar (`:273-284`).
  This closes **QA-C-FINAL-001**.

### Meteorology/document reconciliation — PARTIAL / FAIL

- The corrected meteorology evidence correctly names migration `0003`, the two
  distinct raw artifacts, one canonical record, one `static_altitude`
  association, corrected 3-hour query values, `27 passed, 16 warnings`, and
  disposable-session teardown (`weather-spec.md:259-293`).
- `docs/data-sources.md:50-93` is reconciled: it marks the prior record
  superseded and records the authoritative 27-pass/migration-0003/two-artifact
  execution, API 200, and current `unknown` health after cleanup.
- The active stale meteorology invocation/blocker detailed in QA-C-CLOSE-001
  prevents the meteorology handoff itself from being a single unambiguous final
  contract. This leaves **QA-C-FINAL-002** only partially resolved.

## Checks run

| Exact command | Result | Evidence / limitation |
| --- | --- | --- |
| `python -m pytest -q services/weather/tests` from `D:\Everest` | **PASS** | `18 passed in 0.28s`, matching the supplied latest meteorology-test evidence. |
| `python -m pytest -q` from `D:\Everest` | **PASS with environmental skips** | `37 passed, 8 skipped, 1 warning in 1.07s`. Skips remain unavailable local PostgreSQL/native-ecCodes paths; root-level discovery alone emits the known API-local `real_data` marker warning. |
| Prior DBRE disposable PostgreSQL result | **Historical PASS** | Supplied final evidence remains `27 passed, 16 warnings`, all PostgreSQL tests executed with migration `0003`, `raw=2`, `record=1`, `assoc=1`, forecast API HTTP 200, followed by database/container/listener cleanup. |
| `python -m black --check --line-length 80 services/weather` | **PASS** | `8 files would be left unchanged.` |
| `PYTHONPATH=<repo root>; python -m pylint services/weather services/weather/tests` | **PASS** | `10.00/10.` |
| `python -m compileall -q services/weather` | **PASS** | Exit 0; no output. |
| API-local regression/lint: `python -m pytest -q`; then Black and Pylint from `D:\Everest\apps\api` | **PASS with environmental skips** | `19 passed, 8 skipped in 0.37s`; Black reports 28 unchanged files; Pylint is 10.00/10. |

## Scope isolation

Static inspection of `services/weather/` confirms no GFS, NOAA, ICON, AIFS, or
prohibited-source implementation. This closure review did not start any Phase D
work.

**Handoff:** Metadata-sidecar remediation is accepted, but documentation
reconciliation remains open. **Phase C remains blocked in QA; Phase D GFS is not
unblocked.**

---

# EV-DATA-001-C-QA-ACCEPT — 2026-08-21

**Scope:** Independent verification of the sole final documentation remediation
in `docs/meteorology/weather-spec.md`. No code was inspected for a new feature,
no code was modified, and this QA record is the only changed file.

## Findings first

**No acceptance-blocking findings.** The obsolete one-artifact executable
ingestion example and the obsolete active backend blocker are absent. The former
material has been replaced by a non-executable, explicitly superseded note at
`docs/meteorology/weather-spec.md:299-308`, which directs downstream readers to
the single authoritative final two-artifact, migration-`0003` E2E handoff above.

## Documentation acceptance evidence — PASS

- The Phase C handoff explicitly identifies the final migration-`0003`,
  two-raw-artifact, one-canonical-record, one-`static_altitude` association as
  authoritative at `docs/meteorology/weather-spec.md:128-133`.
- The sole authoritative E2E section records `27 passed, 16 warnings`, all
  PostgreSQL tests run, migration `0003`, `raw_artifact_count=2`,
  `weather_record_count=1`, `auxiliary_association_count=1`, primary versus
  auxiliary provenance, API HTTP 200, corrected 3-hour canonical values, and
  disposable-resource teardown at `weather-spec.md:259-293`.
- `weather-spec.md:299-308` has no executable command, code block, object path,
  old one-artifact descriptor, or current backend-work instruction. It plainly
  states that the old guidance/blocker is superseded and intentionally removed.
- The historical 0-hour retrieval evidence at `weather-spec.md:135-171` remains
  contextual retrieval/parser evidence only; it is not an alternative E2E
  ingestion path. The document distinguishes it from the authoritative final
  record at `:128-133`.
- The independent registry handoff agrees: `docs/data-sources.md:50-93` marks
  the earlier 23-pass record superseded and repeats the final two-artifact,
  migration-`0003`, HTTP-200 evidence and current post-teardown `unknown`
  health.

## Closing verdict

**PASS — Phase C ECMWF IFS is accepted.** The final documentation ambiguity
identified in QA-C-CLOSE-001 is resolved. The historical `verified` result
remains correctly scoped to disposable end-to-end acceptance, while current
runtime health/API availability remain `unknown` after resource teardown.

**Phase D (NOAA GFS) is unblocked for its assigned owner.** This QA assignment
does not begin, implement, or approve any Phase D work.

---

# EV-DATA-001-D-QA — 2026-08-21

**Scope:** Independent, report-only acceptance QA of Phase D NOAA GFS. Reviewed
`AGENTS.md`; the accepted Phase A–C QA record; GFS connector, parser,
normalizer, and tests; canonical weather, API, migration, persistence, and API
test surfaces; `docs/data-sources.md`; `docs/meteorology/weather-spec.md`; and
the delivery board. No business or test code was changed. This QA handoff is
the only modified file. ICON and AIFS work was not begun.

## Findings first

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| QA-D-001 | **High** | **There is no executable GFS-to-backend ingestion chain or GFS PostgreSQL/API test.** The entire GFS package is used only by `services/weather/tests/test_gfs.py`; the only GFS references outside that package are documentation (`services/weather/gfs/connector.py:48-138`, `normalizer.py:28-88`, and repository-wide GFS reference scan). `WeatherIngestionService.ingest()` requires a `RawArtifactDescriptor` and `CanonicalRecordInput` at `apps/api/everest_api/weather/service.py:35-95`, but Phase D provides no adapter that converts the real `RawRetrieval`/`WeatherRecord` into those ports and invokes it. All executable PostgreSQL fixture data and seed registration are hard-coded to `ecmwf-ifs` (`apps/api/tests/test_weather_persistence.py:43-163`), and the only API test checks an invalid profile, not persisted GFS data (`apps/api/tests/test_weather_api.py:15-25`). Thus the supplied DBRE result is credible historical evidence of a disposable run, but the checked-in tests do not prove the GFS raw artifact, canonical record, lifecycle update, and HTTP result are produced by Phase-D code. | Add a GFS-owned adapter/orchestration boundary to construct the backend descriptors from the retained artifact and normalized GFS record, and PostgreSQL-backed GFS E2E coverage that starts with a `noaa-gfs` registry row, proves raw=1/record=1, checks `verified`/`healthy` only after canonical commit, and asserts the one-record HTTP 200 forecast response. Re-run it in a disposable PostgreSQL environment. |
| QA-D-002 | **High** | **The required weather Pylint quality gate fails.** `PYTHONPATH=D:\\Everest; python -m pylint services/weather services/weather/tests` exits non-zero at **9.86/10**, reporting duplicate-code `R0801` across the GFS and ECMWF connector, parser, normalizer, and fake-test fixtures. This fails the mandatory Pylint gate in `AGENTS.md:99-102`; unlike the accepted Phase C invocation, Phase D expanded the package sufficiently to trigger the failure. | Eliminate the duplication through a shared, owned weather utility/test fixture or add narrowly documented and justified lint configuration only where duplication is deliberately required. The complete weather-package Pylint command must exit zero before resubmission. |
| QA-D-003 | **High** | **The raw metadata integrity claim is not met by the GFS connector.** `GfsNcepConnector.retrieve()` writes `metadata.json` through `_write_verified()` but creates no metadata checksum sidecar, canonical-metadata verifier, fsync, or read-only protection (`services/weather/gfs/connector.py:105-129, 206-226`). The IFS remediation accepted in this QA record uses a deterministic JSON sidecar and verifies metadata reuse/tampering (`services/weather/ecmwf/connector.py:200-256`; `test_ecmwf.py:236-284`); no equivalent GFS behavior/test exists. Moreover, GFS metadata includes volatile `retrieved_at` (`gfs/connector.py:121`), so an otherwise identical re-retrieval cannot reuse existing metadata by expected digest. This violates immutable raw payload **and metadata** retention in `AGENTS.md:193-196` and `docs/meteorology/weather-spec.md:96-103`. | Implement GFS metadata canonicalization, checksum sidecar, atomic/fsynced write, rehash-and-verify reuse, and tamper/missing-sidecar deterministic tests, matching the accepted IFS integrity boundary. Keep raw data on failure; do not overwrite provenance. |
| QA-D-004 | **Medium** | **The GFS retrieval metadata is internally inconsistent with both the checked-in connector and the verified artifact.** The actual artifact's `metadata.json` records selected messages `HGT/surface`, `TMP`, `UGRD`, `VGRD`, and variables including `APCP`; WSL ecCodes independently parses `orog`, `2t`, `10u`, `10v` only. The current connector selects `OROG/surface`, not `HGT/surface`, and records `DEFAULT_VARIABLES = (TMP, UGRD, VGRD, OROG)` even though its metadata's `variables` field is caller-controlled and ignored for selection (`services/weather/gfs/connector.py:19-25, 70-76, 91-117`). The factual documentation states the four messages are `orog`, `2t`, `10u`, `10v` (`docs/data-sources.md:152-155`; `weather-spec.md:334-343`). The retained metadata therefore cannot be treated as a deterministic representation of the checked-in retrieval configuration. | Make requested/selected parameters a single validated source of truth; record the exact selected index rows/ranges and actual provider names/levels. Add a deterministic test that verifies metadata accurately describes a known selected set. Recreate and verify the retained GFS artifact/metadata before citing it as final provenance. |
| QA-D-005 | **Medium** | **Range/failure coverage is incomplete.** Strict implementation correctly rejects non-206, malformed `Content-Range`, and unexpected byte length (`services/weather/gfs/connector.py:173-183`), but the only range test asserts rejection of HTTP 200 (`services/weather/tests/test_gfs.py:152-160`). There is no valid-206 acceptance test, malformed-header test, truncated/oversized-range test, index-missing/terminal-offset test, HTTP error retry test, or end-to-end `.idx` selection test. The historical official filter HTTP 500 is documented as a failed alternative (`docs/data-sources.md:146-151`; `weather-spec.md:328-336`) but no deterministic regression test proves that HTTP failure is retried/exhausted or remains distinct from successful `.idx` retrieval. | Add condition-driven fake-session tests for each strict range boundary, index failure, HTTP 500 retry/exhaustion, and one successful indexed retrieval. Keep injected backoff; do not add wall-clock waits. |
| QA-D-006 | **Medium** | **Required handoffs contradict the claimed Phase-D state.** `docs/data-sources.md:122-135, 161-176` and `docs/meteorology/weather-spec.md:344-360` record historical disposable acceptance (`verified`/historical `healthy`, current runtime `unknown` after cleanup). In contrast, `docs/management/board.md:38-41` says persistence/API remain pending and GFS is `configured`; `docs/data-sources.md:199-208` still says GFS remains `planned`. These conflicts make the board and registry handoff unsafe downstream sources and fail the status/health truthfulness requirement in `AGENTS.md:219-228`. | Relevant owners must reconcile the board and Phase-A validation-constraint text with the exact historical DBRE evidence, while retaining the critical distinction: the disposable run's `verified`/`healthy` facts are historical and current runtime health/API availability are `unknown` after teardown. |

**Acceptance verdict: FAIL — Phase D NOAA GFS is not accepted. Phase E DWD
ICON remains blocked.** The verified local artifact and supplied DBRE report
show meaningful historical evidence, but they do not replace the missing
checked-in GFS ingestion/API chain, metadata-integrity control, and mandatory
lint pass. This QA assignment does not start ICON.

## Required-chain assessment

| Required link | Result | Independent evidence / limitation |
| --- | --- | --- |
| Official NOAA `.idx` and strict HTTP-206 range retrieval | **Historical PASS; test coverage partial** | The official NOMADS directory, GRIB2 and `.idx` paths are recorded at `docs/data-sources.md:146-153` and `weather-spec.md:328-338`. The connector targets only `https://nomads.ncep.noaa.gov` and requires HTTP 206, matching `Content-Range`, and exact selected length (`gfs/connector.py:18, 173-183`). The historical filter HTTP 500 is correctly called an alternative failure, not final source health. QA-D-005 remains open. |
| Raw payload checksum and metadata integrity | **Payload PASS; metadata FAIL** | WSL independently recalculated the retained 2,937,483-byte artifact as SHA-256 `9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`, matching its file and both meteorology handoffs. Payload reuse rehashes existing bytes (`gfs/connector.py:206-226`). Metadata lacks the accepted integrity controls; QA-D-003/004 block this link. |
| Actual GRIB2 parsing | **PASS** | WSL Kali ecCodes parsed exactly four messages from the retained artifact: `orog` (`m`, surface), `2t` (`K`), `10u` (`m s**-1`), and `10v` (`m s**-1`), each at cycle/valid time `2026-08-20T00:00:00Z`, lead 0. `gfs/parser.py:25-76` uses ecCodes and fails rather than fabricating messages. Native Windows binding remains unavailable because the ecCodes library is absent; WSL was used for this real-artifact confirmation. |
| Canonical normalization, units, and QC | **PASS for the four-message sample** | Independent WSL normalization selected `(28.0, 87.0)` for Everest `(27.9881, 86.9250)` and produced altitude `5917.819375 m`, temperature `-3.2432128906249886 C`, wind speed `2.081546755453268 m/s`, direction `235.34425831717988°`, null precipitation/visibility, and `[missing_value]`. Explicit unit mapping and additive validation are at `gfs/normalizer.py:18-88`; deterministic unknown-unit coverage is at `test_gfs.py:69-95`. Values agree with `weather-spec.md:339-343` apart from harmless binary floating representation. |
| PostgreSQL migration/persistence | **Historical DBRE PASS; Phase-D executable proof FAIL** | Supplied DBRE evidence: **27 passed, 16 warnings**, all PostgreSQL tests executed; migration head ran; `raw=1`, `record=1`; and source status/health were `verified`/`healthy` during the disposable run. The migration provides raw/canonical tables, checks, uniqueness, and append-only triggers (`apps/api/alembic/versions/20260821_0002_weather_persistence.py:20-169`). No checked-in GFS adapter/test binds this evidence to the Phase-D connector; QA-D-001 remains blocking. |
| API HTTP 200 result and lifecycle/health truthfulness | **Historical DBRE PASS; documentation/coverage FAIL** | DBRE reports `GET /api/weather/forecast?source=noaa-gfs` returned HTTP 200 with one GFS record. The API is persistence-only (`apps/api/everest_api/app.py:74-164`) and the service updates lifecycle only after a canonical insert (`weather/service.py:80-91`), which is correct. The current environment is gone: DBRE removed the disposable port `52370`, container, and volume, so current health/API availability are correctly `unknown` in Phase-D handoffs. Conflicting board/registry documentation and absence of a GFS API test prevent acceptance; QA-D-001/006 remain open. |
| Retry, failure, and range tests | **Partial** | Injected backoff is deterministic, with transient and exhausted timeout tests (`gfs/connector.py:185-198`; `test_gfs.py:98-120`); no hard test sleep is used. QA-D-005 lists untested HTTP/index/range boundaries. |
| Documentation and scope | **Partial** | Official source URLs, artifact hash/size, four messages, coordinate, values, HTTP-500 alternative, and DBRE teardown are documented. Contradictory Phase-A/board claims remain. Static scan found no ICON, AIFS, Everest AWS, Pyramid, satellite, terrain, environmental, OSM, AI, Risk, commercial-provider, or other prohibited implementation. |

## Practical checks run

| Exact command / check | Result | Evidence / limitation |
| --- | --- | --- |
| `python -m pytest -q services/weather/tests` from `D:\\Everest` | **PASS** | `26 passed in 0.35s`; deterministic GFS unit, retry, raw-payload tamper, index-selection, HTTP-200 rejection, and invalid-payload tests ran. |
| `python -m pytest -q` from `D:\\Everest` | **PASS with environmental skips** | `45 passed, 8 skipped, 1 warning in 1.30s`. The warning is the known root-discovery `real_data` marker issue; local PostgreSQL/ecCodes-dependent tests skip. |
| `python -m pytest -q` from `D:\\Everest\\apps\\api` | **PASS with environmental skips** | `19 passed, 8 skipped in 0.43s`; no local disposable PostgreSQL URL was supplied. This does not replace the supplied DBRE run. |
| `python -m black --check --line-length 80 services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | `41 files would be left unchanged.` |
| `PYTHONPATH=D:\\Everest; python -m pylint services/weather services/weather/tests` | **FAIL** | `9.86/10`; duplicate-code `R0801` findings listed in QA-D-002. |
| API Black/Pylint from `D:\\Everest\\apps\\api` | **PASS** | Black: `28 files would be left unchanged`; Pylint: `10.00/10.` |
| `python -m compileall -q services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | Exit 0. |
| WSL real-artifact parse/normalization | **PASS** | `wsl.exe -d kali-linux` with `PYTHONPATH=/mnt/d/Everest` parsed the retained GRIB2 and reproduced the four messages, SHA-256, size, grid selection, canonical values, and additive `missing_value` flag above. |
| Scope/hard-sleep scan | **PASS with one allowed injectable production backoff** | No prohibited-source implementation was found. `gfs/connector.py:60,197` retains injectable bounded retry backoff (`time.sleep` default only); GFS tests pass injected callbacks and contain no wall-clock wait. |

## DBRE evidence incorporated

QA accepts the supplied independent DBRE evidence as factual historical
execution evidence: **27 passed, 16 warnings**, all PostgreSQL tests executed,
migration/persistence result `raw=1` and `record=1`, source
`status=verified`/`health=healthy` during the disposable run, and one GFS
forecast API record returned with HTTP 200. DBRE cleaned temporary localhost
port **52370**, the PostgreSQL container, and its volume. Those facts establish
that no current service is implied after teardown; they cannot cure the
checked-in chain/metadata/test deficiencies identified above.

## Resubmission exit criteria

1. Close QA-D-001 with a real GFS adapter plus isolated PostgreSQL/API E2E test
   covering raw-first retention, canonical persistence, lifecycle truth, and
   the one-record forecast query.
2. Close QA-D-002: complete weather-package Pylint exits zero.
3. Close QA-D-003/004 with durable canonical GFS metadata integrity, exact
   selection provenance, and recreated verified artifact evidence.
4. Close QA-D-005 with deterministic range/index/HTTP-failure coverage; no hard
   sleeps.
5. Reconcile QA-D-006 handoffs without treating a removed disposable runtime as
   currently healthy.
6. Re-run the complete corrected GFS chain in a fresh disposable PostgreSQL
   environment and attach its exact result and teardown evidence.

**Handoff:** **FAIL. Phase E DWD ICON is not unblocked and must not begin.**

---

# EV-DATA-001-D-QA-FINAL — 2026-08-21

**Scope:** Independent final QA of the remediated Phase D NOAA GFS chain.
Reviewed `AGENTS.md`; the GFS connector/parser/normalizer/metadata protection
and tests; `services/weather/gfs/ingestion.py`; adapter unit tests; the new
PostgreSQL/API integration harness; migrations `0001` through `0003`; API and
ingestion service contracts; current data-source, meteorology, management, and
QA handoffs; refreshed retained artifact/metadata/sidecar; and the supplied
DBRE execution facts. No business or test code was changed. This QA handoff is
the only modified file. ICON was not started.

## Findings first

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| QA-D-FINAL-001 | **Medium** | **Phase-D lifecycle/evidence documentation is still contradictory.** The management board says PostgreSQL/API evidence is pending and GFS remains `configured` (`docs/management/board.md:38-47`). The registry entry likewise says `status=configured` (`docs/data-sources.md:116-135`), while the Phase-A validation constraints say GFS remains `planned` and no evidence was added (`docs/data-sources.md:209-218`). These claims conflict with the same data-source handoff's historical DBRE result (`:162-177`) and the meteorology handoff (`docs/meteorology/weather-spec.md:344-360`): the disposable run persisted `raw=1`, `record=1`, set registry status `verified` and health `healthy`, and returned API HTTP 200. The correct current-operational statement is that the removed environment has `health_status=unknown` and no live API, not that historical persistence/API evidence is pending or absent. This repeats the handoff-truthfulness concern in QA-D-006 and fails the requested evidence/document-consistency criterion. | Relevant documentation owners must reconcile the board and Phase-A constraints with the established historical acceptance evidence. They must distinguish historical `verified`/`healthy` DB facts from present runtime health/API availability (`unknown` after teardown), consistently with the accepted Phase-C documentation model. |

**Final acceptance verdict: FAIL — Phase D NOAA GFS is not accepted because the
required downstream handoffs are not factually consistent. Phase E DWD ICON
remains blocked.**

All prior **technical** blockers are closed by inspection and practical test
evidence below. The remaining issue is governance documentation, not a reason
to begin ICON or to reinterpret a destroyed disposable runtime as currently
healthy.

## Prior-blocker closure assessment

| Prior blocker | Final assessment | Independent evidence |
| --- | --- | --- |
| QA-D-001 — checked-in provider-to-backend, PostgreSQL, and API chain | **FIXED** | `services/weather/gfs/ingestion.py:1-217` supplies a thin meteorology-owned adapter. It depends only on backend-neutral descriptors/contracts, maps raw retention and normalized GFS facts losslessly, and rejects source/model/cycle/lead/valid-time/record-type/spatial-key mismatches before invoking the backend port (`:81-154, 165-217`). `compose_gfs_ingestion_adapter()` is the explicit composition boundary (`:157-162`). Adapter unit tests prove forwarding and pre-port provenance rejection (`services/weather/tests/test_gfs_ingestion.py:89-144`). PostgreSQL/API integration test `apps/api/tests/test_gfs_adapter_integration.py:114-175` seeds `noaa-gfs` as `configured`/`unknown`, composes the actual `WeatherIngestionService`, proves raw=1 and record=1, `verified`/`healthy` only after ingestion, and asserts the single public HTTP-200 GFS forecast without raw URL/path/hash leakage. Its failure path proves raw-first retention with no lifecycle escalation (`:178-211`). |
| QA-D-002 — weather Pylint | **FIXED** | `PYTHONPATH=D:\\Everest; python -m pylint services/weather services/weather/tests` completed **10.00/10**. The GFS provider-specific duplication exceptions are scoped and explained in `gfs/connector.py:3-5`, `gfs/parser.py:3-4`, `gfs/normalizer.py:3-4`, `gfs/ingestion.py:9-10`, and `tests/test_gfs.py:3-5`; they do not mask unrelated lint findings. |
| QA-D-003 — metadata integrity | **FIXED** | GFS now writes canonical JSON and `metadata.json.sha256` with the atomic/fsynced verified-write path and best-effort read-only bit (`services/weather/gfs/connector.py:208-249`). Reuse requires both artifacts; rehashes payload bytes; rejects malformed/noncanonical JSON and provenance differences while deliberately excluding volatile `retrieved_at` from otherwise exact comparison (`:236-288`). Deterministic tests cover valid reuse, JSON tamper, missing sidecar, and noncanonical JSON (`services/weather/tests/test_gfs.py:177-224`). QA independently verified the refreshed metadata and sidecar with `_verify_metadata()`. |
| QA-D-004 — exact selection provenance | **FIXED** | Connector selection is now `HGT`, `TMP`, `UGRD`, `VGRD` at official index levels (`gfs/connector.py:23-29, 94-100`) while authoritative retained metadata describes the actual ecCodes short names `orog`, `2t`, `10u`, `10v` (`:108-130`). Refreshed `metadata.json` exactly records those parsed short names and levels, source/model, URLs, cycle, lead, size, hash, and Everest request. WSL ecCodes independently parsed exactly those four messages, removing the stale `HGT`/`APCP` metadata defect. |
| QA-D-005 — strict range/retry/failure coverage | **FIXED** | The connector requires HTTP 206, expected `Content-Range`, and exact byte length (`gfs/connector.py:176-186`), with bounded injectable retry/backoff (`:188-201`). Deterministic tests cover valid 206, malformed header/truncated content, HTTP-200 full response rejection, incomplete index failure, transient timeout, exhausted timeout, and historical HTTP-500 retry/exhaustion (`test_gfs.py:125-162, 227-277`). No test has a wall-clock sleep; injected callbacks record backoff conditions. |
| QA-D-006 — handoff consistency | **OPEN** | QA-D-FINAL-001 remains. The refreshed source/meteorology evidence is thorough, but the board and Phase-A constraints remain stale and contradict it. |

## Real artifact and historical E2E verification

### Refreshed raw-artifact preverification — PASS

QA independently examined the retained corrected artifact at
`tmp-gfs-refresh-20260821/noaa-gfs/9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4/`:

- Payload size: `2,937,483` bytes.
- SHA-256 recomputation: `9826ecbccc0fefa20f3bfcb47f8e27ab47e5d853d2497095f8192a92a2b9bfa4`.
- Metadata sidecar digest: `f99e6967479a193def39c1bf80e364fcaea9ac39a4fb3ebaf2f97778e54eb9de`.
- `GfsNcepConnector._verify_metadata()` accepted the canonical JSON/sidecar
  pair. Metadata identifies only official NOAA/NCEP URLs, source `noaa-gfs`,
  model `GFS`, cycle `2026-08-20T00:00:00Z`, lead 0, requested Everest
  coordinate `(27.9881, 86.9250)`, and messages `orog`, `2t`, `10u`, `10v`.
- WSL Kali ecCodes parsed four actual messages: `orog;2t;10u;10v`. Independent
  normalization selected grid `(28.0, 87.0)` and produced temperature
  `-3.2432128906249886 C`, wind speed `2.081546755453268 m/s`, and additive
  `[missing_value]`, matching `docs/meteorology/weather-spec.md:400-410`.

### Supplied DBRE historical E2E — PASS

QA incorporates the supplied independent DBRE run as historical execution
evidence for the corrected chain: raw artifact preverification, composition via
`compose_gfs_ingestion_adapter`, Alembic migrations `0001`–`0003`, one raw and
one canonical persisted record (`raw=1`, `record=1`), lifecycle
`verified`/`healthy` after canonical commit, and one GFS forecast API result at
HTTP `200`. DBRE subsequently removed the disposable database/container/volume
and listener. The former temporary port was `52370`. Thus historical acceptance
facts are valid, but current operational health and API availability are
unknown after teardown.

## Current practical checks

| Exact command / check | Result | Evidence / limitation |
| --- | --- | --- |
| `python -m pytest -q services/weather/tests` from `D:\\Everest` | **PASS** | `35 passed in 0.40s`, including GFS connector, metadata, range/retry, and adapter unit coverage. |
| `python -m pytest -q` from `D:\\Everest` | **PASS with environmental skips** | `54 passed, 10 skipped, 1 warning in 1.23s`. The known root-level `real_data` marker warning is non-functional; PostgreSQL/ecCodes-dependent cases have no local disposable database/native binding. |
| `python -m pytest -q` from `D:\\Everest\\apps\\api` | **PASS with environmental skips** | `19 passed, 10 skipped in 0.41s`. The new GFS PostgreSQL/API tests correctly skip without `EVEREST_TEST_DATABASE_URL`; their actual execution is supplied by DBRE, not falsely claimed locally. |
| `python -m black --check --line-length 80 services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | `44 files would be left unchanged.` |
| `PYTHONPATH=D:\\Everest; python -m pylint services/weather services/weather/tests` | **PASS** | `10.00/10.` |
| API Black/Pylint with `PYTHONPATH=D:\\Everest;D:\\Everest\\apps\\api` from `apps/api` | **PASS** | Black: `29 files would be left unchanged`; Pylint: `10.00/10.` The repository root is additionally required because the API integration test imports the meteorology-owned adapter. |
| `python -m compileall -q services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | Exit 0. |
| Scope and wait discipline | **PASS** | Static inspection found no ICON, AIFS, Everest AWS, Pyramid, satellite, terrain, environmental, OSM, AI, Risk, commercial-provider, or other prohibited implementation. GFS retry backoff is injected (`gfs/connector.py:64,200`); tests use callbacks, never wall-clock waits. |

## Exit condition and handoff

1. Close **QA-D-FINAL-001** by reconciling the board and data-source validation
   constraints with the historical DBRE persistence/API facts and the current
   post-teardown `unknown` operational state.
2. QA then needs a documentation-only closure check; no GFS business-code
   change or rerun is required unless those factual claims change.

**Handoff: FAIL. Phase E DWD ICON is not unblocked and must not begin.**

---

# EV-DATA-001-D-QA-CLOSE — 2026-08-21

**Scope:** Independent documentation-only closure verification for Phase D NOAA
GFS. Reviewed `docs/management/board.md`, `docs/data-sources.md`,
`docs/meteorology/weather-spec.md`, and the established Phase-D QA/DBRE
evidence. No business code, test code, or non-QA documentation was changed by
QA. This QA record is the only modified file. ICON was not started.

## Findings first

**No acceptance-blocking findings.** The final documentation reconciliation is
factually consistent:

- `docs/data-sources.md:121-134` records NOAA GFS as **`verified` only for the
  historical checked-in-adapter disposable E2E**, identifies historical
  `healthy`, and records current health as `unknown` after teardown.
- Its sole authoritative E2E record identifies retention preverification,
  `compose_gfs_ingestion_adapter`, temporary PostgreSQL port `34034`, migrations
  `0001`–`0003`, `raw=1`, `record=1`, service-generated
  `verified`/`healthy`, and the one-record forecast HTTP-200 result
  (`docs/data-sources.md:136-168`).
- Its registry-boundary constraints now state the same historical/current
  distinction and name **only AIFS and ICON** as `planned`
  (`docs/data-sources.md:194-208`).
- The delivery board no longer claims GFS persistence/API evidence is pending or
  calls GFS a source lifecycle state of `configured`/`planned`. It records the
  completed checked-in-adapter historical chain and current unknown runtime/API
  state (`docs/management/board.md:38-43`). Its Phase-D `blocked` table status
  is a delivery-governance state pending this QA closure, not a contradictory
  data-source lifecycle assertion.
- The meteorology handoff records the same authoritative adapter E2E facts and
  teardown qualification (`docs/meteorology/weather-spec.md:380-437`).

## Closure verdict

**PASS — Phase D NOAA GFS is accepted.** QA-D-FINAL-001 is closed: the
documentation consistently distinguishes the historical disposable database's
`verified` lifecycle and `healthy` state from the current post-teardown runtime
health/API state, which is `unknown`.

**Phase E DWD ICON is unblocked for its assigned owner.** AIFS remains planned.
This documentation-only QA assignment does not begin, implement, or approve
ICON work.

---

# Historical QA Records — Archived Context

All QA records above this divider are historical evidence and closure history
for EV-DATA-001 Phases A through D. They are not the active Phase E acceptance
plan and must not be read as a Phase E approval, an ICON database/API result,
or a source-status change. The active, prospective QA work starts below.

# Active QA Plan: EV-DATA-001-E-QA — DWD ICON

**Assignment ID:** EV-DATA-001-E-QA-PLAN  
**Scope:** Report-only Phase E DWD ICON acceptance matrix. QA may review
evidence and run tests, but must not change business code, migrations,
registry/source status, raw artifacts, or non-QA handoffs. This plan adds no
claim that ICON is verified, healthy, persisted, or queryable.

## Governing Authorities and Current Block

This plan was prepared against the latest `AGENTS.md`, ADR-007 through ADR-011
in `docs/management/decisions.md`,
`docs/architecture/architecture.md`, `docs/api/API.md`,
`docs/meteorology/weather-spec.md`, and `docs/data-sources.md`.

`AGENTS.md` remains the controlling specification (ADR-007). The normative
canonical weather contract is **only**
`docs/meteorology/weather-spec.md` (ADR-008); compatibility material or
provider implementation cannot redefine its fields, record types, units, or
additive-QC semantics. The permitted flow remains:

`official DWD source -> ICON connector -> immutable raw artifact -> parser ->`
`normalizer -> QC -> canonical model -> PostgreSQL/object storage -> service ->`
`bounded REST API`.

**Phase E remains blocked until Gates A and C and the E-DBRE prerequisites below
close.** Gates B and D are closed only for their respective deterministic
contract boundaries. A matrix row marked “planned” is a future acceptance
obligation, not evidence that it has passed.

### Blocking gates before Phase-E execution

| Gate | Required closure evidence | Current QA disposition |
| --- | --- | --- |
| **A — Approved AOI and provider/version basis** | The manager-approved Everest AOI authority, including the permitted acquisition/subset policy, and the DWD ICON product/version/run basis are recorded in the controlling domain handoff. Retrieval must be demonstrably limited to the approved AOI or the smallest approved provider objects needed to derive it; no unapproved global download is acceptable. | **Blocked.** ADR-007 requires the AOI authority gate; QA will not infer it from an implementation or historical object paths. |
| **B — Canonical contract authority** | The Phase E path demonstrably uses the single normative weather specification: UTC time, native/provider spatial key, metres, Celsius, m/s, degrees, millimetres, nullable missing values, forecast identity, and additive flags. | **CLOSED — deterministic semantic evidence recorded in `EV-DATA-001-REM-02-GATEB-DOC-CLOSE` below.** This closes ADR-008 only; it does not authorize raw retrieval, persistence, API execution, or final Phase-E acceptance. |
| **C — Approved raw-storage policy** | Manager-approved external raw root, repository exclusion/configuration, immutable retention controls, and cleanup/retention ownership are documented. Raw GRIB2, compressed provider objects, metadata, and checksums remain outside Git. | **Blocked.** ADR-010 says existing project-root `tmp-*` data is unmoved and is not compliant durable operational storage. |
| **D — Shared ingestion-port isolation** | The owner-neutral shared DTO/protocol is available; the ICON adapter imports neither `apps/api`/`everest_api` nor FastAPI, SQLAlchemy, HTTP, ecCodes, or provider-specific types through that contract. Backend implements the port; meteorology supplies the adapter. | **Blocked until QA verifies the ADR-009 dependency direction.** |

### E-DBRE prerequisites (all required after Gates A-D)

Before an isolated disposable PostgreSQL/DBRE execution is scheduled, QA must
receive: (1) the reconciled authoritative ICON lifecycle wording required by
ADR-011, without QA relabelling any source; (2) the approved raw-storage root
and a retained, integrity-verifiable ICON artifact located there; (3) exact
official DWD URLs, UTC retrieval/cycle/valid times, dataset/product/version,
selected native grid and parsed-variable count; (4) a Phase-E adapter proven
to satisfy Gate D; and (5) a disposable PostgreSQL configuration with a random,
documented, unallocated localhost port and teardown owner. Existing historical
ICON retrieval/parser/normalizer material is not a DB/API acceptance result.

## Active Phase E QA Matrix

| ID | Acceptance area | Required deterministic evidence and assertions | Pass condition / failure disposition |
| --- | --- | --- | --- |
| E-QA-01 | Approved AOI, DWD product/version | Verify the approved AOI authority and exact DWD Open Data product hierarchy, run/cycle, filenames, format, access method, variables, units, coverage, update cadence, licence/commercial-use finding, and credential/rate-limit status from official documentation. Assert that acquisition uses only the approved AOI/subset policy or the smallest approved necessary objects. | Pass only with documented authority and factual official metadata. Missing AOI approval, unknown version/product basis, or a global/full download outside the approved policy blocks Phase E. |
| E-QA-02 | Canonical weather authority | Feed known parsed ICON messages through the normalizer/QC and assert the normative `weather-spec.md` meanings and units: UTC valid time, forecast cycle plus lead consistency, native spatial key, altitude m, temperature C, wind m/s and true-north degrees, precipitation mm, visibility m, required source/model, and forecast record type. Unknown units/missing fields must remain retained/null as applicable and add flags, never be inferred. | Pass only when the single canonical contract is exercised; a local ICON schema, unit guessing, conversion by magnitude, silent imputation, or destructive QC fails. |
| E-QA-03 | Raw-storage policy and integrity | Before retrieval reuse or new acquisition, verify the approved external raw root and Git exclusion. For each retained raw fact, recompute payload SHA-256 and metadata-sidecar SHA-256; assert canonical metadata, atomic/fsynced write behaviour, reuse rehash, and deterministic rejection of payload, metadata, or sidecar tampering/missing artifacts. | Pass only when raw payload and metadata are immutable/integrity-verifiable under the approved policy. Project-root `tmp-*` artifacts are not sufficient durable-storage evidence under ADR-010. |
| E-QA-04 | Shared ingestion-port dependency isolation | Static-import and adapter-contract tests prove `services/weather/icon/` does not import `apps/api`, `everest_api`, FastAPI, SQLAlchemy, HTTP clients, ecCodes, or provider types through the shared ingestion package. Unit tests inject a fake port and prove lossless primitive DTO forwarding and pre-port rejection of mismatched source/model/type/cycle/lead/valid-time/spatial key. | Pass only after ADR-009’s owner-neutral direction is proven. A direct provider-to-backend import or a shared contract with forbidden dependencies blocks DBRE. |
| E-QA-05 | Actual retained ICON artifact and provenance | Independently inspect the approved-root artifact and its canonical metadata. Recompute checksum/size; verify exact official DWD URLs, source `dwd-icon`, model `ICON`, dataset/product, GRIB2 format, retrieval time, cycle, valid time, lead, declared units, parser version when available, and native selected grid for Everest. Parse the retained bytes with ecCodes and record the actual variable/message count. | Pass only when artifact bytes, metadata, parser output, and provenance agree. A connector-only result, listing-only result, fabricated coordinate, or unverifiable historical path is not real-data acceptance. |
| E-QA-06 | Parser, normalizer, and additive QC | Deterministic fixtures cover valid ICON GRIB2 parsing and malformed/compressed/non-GRIB failures; normalization of `T_2M`, `U_10M`, `V_10M`, `HSURF`, and required native-grid coordinates; null/flag retention for missing, invalid-unit, invalid-coordinate, invalid timestamp, range, duplicate, stale, provenance, and cycle-time cases. Use actual artifact smoke separately from isolated unit fixtures. | Pass only when failures preserve raw facts and QC flags anomalies rather than deleting/replacing them. No network dependency or wall-clock sleep in unit tests. |
| E-QA-07 | PostgreSQL migration and raw-first persistence | In a fresh disposable PostgreSQL database, run reviewed Alembic upgrade/downgrade and assert schema constraints, append-only raw-artifact behaviour, checksum/metadata persistence, deduplication identity, transaction rollback, and raw-first semantics. Force canonical persistence failure after raw retention and assert raw remains while registry lifecycle/health does not escalate. | Pass only with executed PostgreSQL—not SQLite or static SQL—evidence and verified downgrade/teardown. |
| E-QA-08 | Bounded forecast API and privacy | Seed only Phase-E-owned data through the validated ingestion adapter, then assert `GET /api/weather/forecast` returns only persisted forecast records; exact `source`, UTC `start`/`end`, and invalid range behaviour are bounded and deterministic. Assert one expected ICON record for the owned query and no raw object reference, raw URL, checksum, metadata, credential reference, or unbounded failure detail in public responses. | Pass only after canonical commit produces the persisted, bounded HTTP result. API routes must not invoke DWD, parser, or connector code. |
| E-QA-09 | Failure and raw-first behaviour | Deterministically simulate DWD directory/object HTTP failure, timeout, invalid compression/GRIB bytes, parser failure, unit/QC failure, adapter provenance rejection, and canonical persistence failure. Assert bounded safe diagnostics, retained raw data where retrieval succeeded, append-oriented run evidence, no false `verified`/`healthy` claim, and no secret/raw URL leakage from APIs. | Pass only if failures fail closed without deleting or overwriting raw facts and without lifecycle escalation. Source lifecycle and operational health remain distinct. |
| E-QA-10 | Retries, deduplication, and integrity determinism | Inject clock/sleeper and HTTP/session fakes; assert retry count, timeout, backoff, request count, transient success, exhausted failure, and no wall-clock sleep. Re-run same logical artifact and assert identity/content-hash deduplication is idempotent; altered content under same logical identity is retained/flagged per policy rather than silently rewritten. | Pass only with condition-driven, bounded tests. `sleep()`, `waitForTimeout`, nondeterministic remote assertions, or shared test artifacts are failures. |
| E-QA-11 | Lint, tests, and reproducibility | Run the required focused and full Python test suites, Black (80-column), Pylint, and compile checks in the declared environment. Run the relevant deterministic tests repeatedly (minimum `--repeat-each=10` where the runner/plugin is available, otherwise ten independent invocations) with no pass-on-retry. Preserve command output and failures. | Pass only when all required gates exit zero and all ten executions pass. Retries measure flakes; they do not cure them. Environmental skips cannot substitute for DBRE execution. |
| E-QA-12 | DBRE teardown and claim discipline | DBRE records migration revision, test count/failures, database counts, bounded API result, actual UTC data time, parsed-variable count, exact approved raw-root reference/checksum, and teardown proof. Verify container, volume, temporary listener, test database, and test-owned rows are removed. | After teardown, document only historical execution facts. Do not claim a current live API, current healthy runtime, production deployment, or `verified` source status unless the authoritative owners reconcile and record that evidence. |

## Execution Rules and Evidence Package

1. **Test ownership:** Every test creates its registry row, raw-root fixture,
   database records, and temporary resource names. It must tolerate parallel
   siblings and clean up in a `finally`/fixture teardown path.
2. **No hard sleeps:** Retry tests inject a sleeper/clock and assert calls;
   browser/API tests wait for observable responses or persisted state, never a
   wall-clock delay.
3. **Real-data separation:** A retained-artifact smoke test validates factual
   DWD bytes. It is separate from deterministic parser/normalizer/failure
   fixtures and cannot be replaced by mocks.
4. **Failure artifacts:** Preserve test output, migration revision, PostgreSQL
   logs, adapter/API response (redacted), raw checksum/metadata verification
   output, and teardown evidence. Any browser-level check must retain trace,
   screenshot, video, console, and network artifacts on failure.
5. **Claim discipline:** QA reports `PASS`, `FAIL`, or `BLOCKED` against this
   matrix. It does not edit `docs/data-sources.md` or registry lifecycle/health
   values. Per ADR-011, no Phase E result may be described as ICON verification
   or current health until the authoritative lifecycle reconciliation and the
   full required chain are complete.

## Active Handoff Condition

No Phase-E QA acceptance or DBRE run is authorized while Gate A, Gate C, or any
E-DBRE prerequisite remains open. Gate B closure does not authorize ICON
retrieval, raw-artifact reuse, PostgreSQL persistence, API execution, or source
lifecycle/health escalation. Until the remaining gates close, the only active
Phase-E verdict is **BLOCKED**.

---

# EV-DATA-001-REM-02-GATEB-DOC-CLOSE — Gate B closure record

**Assignment ID:** `EV-DATA-001-REM-02-GATEB-DOC-CLOSE`  
**Review date:** 2026-08-21  
**Scope:** Documentation reconciliation of the active Phase E QA plan to the
completed Gate B evidence. No code, tests, raw artifacts, database, API, or
external source was modified or executed for this closure record.

## Gate B closure

**PASS — Gate B (ADR-008 canonical-contract authority) is CLOSED.** The ICON
provider-path semantic evidence is complete for the deterministic boundary.
All ADR-008 semantic items are documented as **PASS**: normative contract
authority; UTC valid time and cycle/lead identity; native spatial-key
propagation; altitude in metres; temperature conversion to Celsius; wind speed
and true-north direction in m/s/degrees including range and calm behaviour;
canonical precipitation/visibility null behaviour for ICON's unmapped fields;
invalid-unit no-guessing for all mapped fields; source/model/forecast identity;
additive QC and null retention; and the complete adapter pre-port rejection
matrix.

### Gate B evidence record

| Check | Result | Evidence |
| --- | --- | --- |
| ICON semantic suite | **PASS** | `PYTHONPATH=D:\\Everest; python -m pytest -q services/weather/tests/test_icon.py services/weather/tests/test_icon_ingestion.py`; **42 passed on each of 10 consecutive independent runs**. No retries, pass-on-retry, sleeps, network calls, raw artifacts, database, or API were used. |
| Full weather suite | **PASS** | `PYTHONPATH=D:\\Everest; python -m pytest -q services/weather/tests` → **78 passed**. |
| Pylint | **PASS** | Weather Pylint rated **10.00/10**. |
| Compile | **PASS** | `python -m compileall -q packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` exited 0. |
| ADR-008 semantic items | **PASS** | Every item is documented as PASS in the item-by-item verification in the preceding Gate B review. |

## Remaining gates and explicit non-authorizations

1. **Gate A — AOI authority/provider basis: BLOCKED.** The required
   governance/approval reconciliation and operational acquisition basis remain
   open. Gate B does not authorize DWD acquisition or raw-artifact reuse.
2. **Gate C — approved raw-storage policy: BLOCKED.** Approved-root runtime
   evidence, retention/access/disposition controls, and integrity-verifiable
   operational raw-artifact evidence remain outstanding.
3. **ICON DB/API and DBRE: BLOCKED.** No ICON PostgreSQL persistence, database
   migration execution, API query, or DBRE run is authorized by this record.
4. **Final Phase E acceptance: BLOCKED.** Gate B closure is limited to ADR-008
   deterministic semantic evidence. It does not establish ICON `verified`,
   current health, persisted data, queryability, or completion of the required
   real-data → parser → normalizer → QC → persistence → API chain. Final
   Phase E acceptance remains blocked until the remaining gates and all E-DBRE
   prerequisites close.

**Handoff:** Gate B is **CLOSED** for deterministic ICON semantic evidence.
Gate C, ICON DB/API, and final Phase E acceptance remain **BLOCKED**.

---

# EV-DATA-001-REM-02-QA — 2026-08-21

**Assignment:** Independent QA of the ADR-009 shared owner-neutral ingestion
contract migration. **Scope:** `AGENTS.md`, ADR-009, architecture/API/weather
handoffs, the shared package, API backend implementation, and GFS/ICON
adapters/tests. QA changed no business or test code; this QA handoff is the
only modified file. No ICON database/API test and no external retrieval were
run.

## Findings first

| ID | Severity | Finding | Required disposition |
| --- | --- | --- | --- |
| REM-02-QA-001 | High | The adapters undermine the shared boundary's primitive-metadata guarantee. `services/weather/gfs/ingestion.py:16,49,101` and `services/weather/icon/ingestion.py:7,36,77` declare `raw_metadata` as `dict[str, Any]` and pass it directly to `RawArtifactDescriptor.metadata`. ADR-009 requires raw metadata to be string-keyed scalar primitive values so parser/vendor objects cannot cross the owner-neutral port (`docs/architecture/architecture.md:148-153`); the shared DTO correspondingly types it as `Mapping[str, PrimitiveValue]` (`packages/weather_ingestion_contract/weather_ingestion_contract/contracts.py:10-18,40`). Python dataclasses do not enforce that annotation at runtime, so an adapter caller can forward an arbitrary provider object to the backend. | Meteorology must constrain adapter retention metadata to the shared `PrimitiveValue` mapping (and reject/nonserialize unsupported values before port invocation). Add deterministic GFS and ICON tests that prove non-primitive metadata is rejected before the fake/backend port receives it. |
| REM-02-QA-002 | Medium | The mandated Black gate currently fails in the migrated adapters: `python -m black --check --line-length 80 packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` reports that `services/weather/gfs/ingestion.py` and `services/weather/icon/ingestion.py` would be reformatted. This violates the required Python delivery gate in `AGENTS.md:260-261`. | Format the two adapter files and rerun the aggregate Black gate. This is a business-code-owner correction; QA made no such edit. |
| REM-02-QA-003 | Low | Existing adapter provenance-rejection tests exercise only a forecast-cycle mismatch per provider (`test_gfs_ingestion.py:127-145`; `test_icon_ingestion.py:102-119`). Static review confirms production code also rejects source/model, raw valid-time, record type, missing spatial key, missing forecast identity, lead, and valid-time divergence before port invocation (`gfs/ingestion.py:155-193`; `icon/ingestion.py:89-125`), but those branches are not independently regression-tested. | Non-blocking after the two blocking findings close: parameterize deterministic rejection tests over every documented pre-port provenance guard for both adapters. |

**Verdict: FAIL — ADR-009 is structurally migrated in the reviewed import
direction, and all executable non-PostgreSQL adapter/weather tests pass, but it
does not yet meet the primitive-only boundary guarantee or the mandatory format
gate. This verdict does not authorize ICON DB/API execution.**

## ADR-009 structural verification

### Provider-to-backend dependency direction — PASS

- ADR-009 requires provider adapters under `services/weather/` to avoid
  `apps/api` and `everest_api`; backend implements the port; meteorology owns
  the adapters (`docs/management/decisions.md:86-96`). The architecture makes
  the same direction normative (`docs/architecture/architecture.md:160-171`).
- `services/weather/gfs/ingestion.py:19-24` and
  `services/weather/icon/ingestion.py:10-15` import DTOs and `IngestionPort`
  from `weather_ingestion_contract` plus meteorology's local canonical record
  types. Neither production adapter imports `everest_api`, `apps.api`, FastAPI,
  SQLAlchemy, a database/session service, HTTP client, or ecCodes.
- A repository production-source scan found no `everest_api`, `apps.api`,
  FastAPI, or SQLAlchemy import in `services/weather/`. It correctly finds
  `requests` in the independently owned provider connectors and ecCodes in
  independently owned parsers; these are not imported by either ingestion
  adapter or the shared boundary and are necessary provider-layer concerns, not
  a reverse backend dependency.
- The GFS and ICON unit suites each include a static source assertion that their
  adapter does not contain `everest_api` or `apps.api`
  (`test_gfs_ingestion.py:148-155`; `test_icon_ingestion.py:122-129`).

### Shared package dependency surface — PASS, with metadata-contract blocker

- `packages/weather_ingestion_contract/pyproject.toml:5-10` declares no runtime
  dependencies. The package imports only `collections.abc`, `dataclasses`,
  `datetime`, `typing`, and `uuid` (`contracts.py:8-14`), as ADR-009 requires.
  Targeted scans found no FastAPI, SQLAlchemy, HTTP, ecCodes, provider,
  `everest_api`, `apps.api`, or `services.weather` import in that package.
- Its public surface is limited to primitive DTOs and the persistence protocol:
  `PrimitiveValue`, `RawArtifactDescriptor`, `AuxiliaryArtifactReference`,
  `CanonicalRecordInput`, and `IngestionPort` (`contracts.py:17-100`; package
  exports at `__init__.py:8-22`). `IngestionPort` takes only descriptors and a
  sequence of canonical DTOs and returns `UUID`; it does not expose a backend
  framework/persistence type.
- This package-level result does **not** close REM-02-QA-001: the adapters'
  `Any`-typed forwarding defeats the DTO's intended scalar metadata boundary.

### Backend port implementation and compatibility edge — PASS by inspection

- `WeatherIngestionService` explicitly implements `IngestionPort`
  (`apps/api/everest_api/weather/service.py:14-19,32-49`) and accepts the shared
  `auxiliary_artifacts` command. It retains raw evidence before canonical work,
  validates source/cycle/lead consistency, commits lifecycle/health only after
  canonical insertion, and keeps raw facts when later work fails (`:74-131,
  223-299`).
- `everest_api.weather.contracts` has been reduced to compatibility exports of
  the shared types and the deprecated backend-edge
  `StaticAltitudeArtifactReference` wrapper (`apps/api/everest_api/weather/contracts.py:1-39`).
  This is consistent with the API handoff's transition-only compatibility rule
  (`docs/api/API.md:94-100`), not a duplicate primary DTO definition.

## Adapter provenance and regression evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Focused GFS + ICON adapter suites | **PASS** | `PYTHONPATH=D:\\Everest; python -m pytest -q services/weather/tests/test_gfs_ingestion.py services/weather/tests/test_icon_ingestion.py` → **7 passed in 0.03s**. Each adapter losslessly forwards a primitive-shaped fixture to an injected fake port and rejects a provenance mismatch before any port call. |
| Repeat stability | **PASS** | The same focused adapter command was executed **10 independent times**: **7 passed** each time; no retry and no wall-clock wait were used. |
| Existing weather suite | **PASS** | `PYTHONPATH=D:\\Everest; python -m pytest -q services/weather/tests` → **49 passed in 0.49s**. |
| Full available suite | **PASS with declared skips** | `python -m pytest -q` from repository root → **68 passed, 10 skipped, 1 warning in 1.53s**. The warning is the known root-level unregistered `real_data` marker; it is not a test failure. |
| API-local suite | **PASS with declared skips** | `PYTHONPATH=D:\\Everest;D:\\Everest\\apps\\api; python -m pytest -q` from `apps/api` → **19 passed, 10 skipped in 0.49s**. |
| GFS PostgreSQL/API composition | **SKIPPED — not executed** | `tests/test_gfs_adapter_integration.py -rs` → **2 skipped** because `EVEREST_TEST_DATABASE_URL` was unset. No database connection, migration, persistence assertion, or HTTP API assertion was executed in this QA run. |
| Weather persistence PostgreSQL cases | **SKIPPED — not executed** | `tests/test_weather_persistence.py -rs` → **2 passed, 5 skipped**; all five PostgreSQL cases skipped because `EVEREST_TEST_DATABASE_URL` was unset. |
| Compilation | **PASS** | `python -m compileall -q packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` exited 0. |
| Shared-package Black / Pylint | **PASS** | Shared package Black check reported 2 files unchanged; its package-local Pylint invocation rated **10.00/10**. |
| Aggregate Black | **FAIL** | See REM-02-QA-002: exactly the GFS and ICON ingestion adapters would be reformatted. |

## API and persistence semantic assessment

Available executable evidence has not exposed a regression in the shared-port
migration: the API-local non-database tests pass, GFS adapter composition and
weather persistence tests are present, and static inspection shows the backend
still uses shared DTOs while retaining raw-first, source/cycle/lead validation,
deduplication, and post-canonical-commit lifecycle behavior. The API contract
continues to reserve raw provenance as internal-only and preserve public weather
response semantics (`docs/api/API.md:75-99`).

**PostgreSQL status is explicitly SKIPPED, not passed or executed, for this QA
assignment.** `EVEREST_TEST_DATABASE_URL` was not supplied. The ten API-local
skips comprise three registry PostgreSQL tests, five weather-persistence
PostgreSQL tests, and two GFS adapter integration tests. This report does not
restate historical DBRE evidence as a current execution result, and it did not
run ICON database/API tests.

## Resubmission exit criteria

1. Close REM-02-QA-001 by enforcing scalar `PrimitiveValue` metadata before
   both adapters invoke `IngestionPort`, with deterministic rejection tests.
2. Close REM-02-QA-002 by formatting the two adapter modules and passing the
   aggregate Black command.
3. Expand per-provider pre-port provenance rejection coverage listed in
   REM-02-QA-003.
4. For any request to assert database/API regression coverage, supply an
   isolated disposable PostgreSQL URL and run the existing GFS/API and weather
   persistence suites. ICON DB/API must remain unexecuted unless separately
   authorized by its active Phase-E gates.

---

# EV-DATA-001-REM-02-03-QA — 2026-08-21

**Assignment:** Independent QA of the completed owner-neutral ingestion
contract and raw-storage enforcement remediations. **Scope:** current
`AGENTS.md`; ADR-007 through ADR-011 (with ADR-012's current AOI gate also
reviewed); `docs/everest-aoi.md`; architecture; the shared package; API raw
storage and ingestion service; provider adapters; and current tests. QA changed
no business or test code. This QA handoff is the only modified file. No external
retrieval, raw-data operation, ICON database/API execution, or raw-data reuse
was performed.

## Findings first

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| REM-02-03-QA-001 | Low | Repository-root pytest discovery still emits one `PytestUnknownMarkWarning` for the API-local `real_data` marker (`apps/api/tests/test_weather_persistence.py:30`). The same suite run from `apps/api`, where that marker is configured in `apps/api/pyproject.toml:31-36`, completes without this warning. It does not skip, mask, or fail a remediation assertion. | **Non-blocking test-runner configuration debt.** Register the marker at root if repository-root pytest is intended as the canonical command. Do not misreport the warning as a passing PostgreSQL or real-data execution. |

**Verdict: PASS — REM-02-03 closes the requested shared-contract and
raw-storage-enforcement remediation checks.** This is a narrow structural and
unit-test acceptance only. It **does not** close AOI Gate A, does not approve an
AOI, does not authorize external acquisition or existing raw-artifact reuse,
does not mark ICON verified/healthy, and does not authorize ICON PostgreSQL/API
or DBRE execution.

## Owner-neutral shared ingestion contract — PASS

### Scalar metadata is rejected before a port call

- `RawArtifactDescriptor.__post_init__()` invokes `_validate_metadata()` before
  a DTO can leave a provider adapter (`packages/weather_ingestion_contract/
  weather_ingestion_contract/contracts.py:22-38,41-66`). It accepts only exact
  `str`, `int`, `float`, `bool`, or `None` values behind string keys; nested
  containers, provider/vendor objects, non-string keys, and scalar subclasses
  are rejected.
- The shared-package tests cover valid scalar/null metadata plus a provider
  object, nested mapping, and non-string key rejection
  (`packages/weather_ingestion_contract/tests/test_contracts.py:27-62`).
- QA additionally exercised the actual GFS and ICON adapters with an injected
  fake port and `object()` in otherwise valid raw metadata. Both calls raised
  `TypeError`, and the fake-port call collections remained empty. Therefore
  invalid metadata is rejected while constructing the descriptor, before either
  adapter can invoke `IngestionPort`.

### Dependency direction and package isolation

- Production ingestion adapters import DTOs and `IngestionPort` only from
  `weather_ingestion_contract`, plus local meteorology canonical types
  (`services/weather/gfs/ingestion.py:19-24`; `services/weather/icon/
  ingestion.py:10-15`). They import no `everest_api`, `apps.api`, FastAPI,
  SQLAlchemy, HTTP client, ecCodes, database/session, or backend service code.
  Repository scanning found `everest_api`/`apps.api` strings only in the two
  adapter tests' negative assertions, not in production `services/weather`.
- `packages/weather_ingestion_contract/pyproject.toml:5-10` has no runtime
  dependencies. Its only imports are Python standard-library imports
  (`contracts.py:9-15`); a targeted forbidden-dependency scan returned no
  FastAPI, SQLAlchemy, HTTP, ecCodes, backend, or provider-module import.
- The backend implements the port and is the correct owner of the persistence
  edge: `WeatherIngestionService(IngestionPort)` imports shared DTOs and calls
  `RawStoragePolicy.resolve_object_reference()` before raw persistence
  (`apps/api/everest_api/weather/service.py:14-23,33-43,229-273`). This satisfies
  ADR-009's one-way composition boundary; it does not imply provider or ICON
  database acceptance.

## External raw-storage enforcement — PASS (validation boundary only)

- `RawStoragePolicy.from_environment()` requires `EVEREST_RAW_ROOT`; the root
  and repository root must both be absolute, the raw root must already exist and
  be a directory, and the resolved raw root must be outside the resolved
  repository root (`apps/api/everest_api/raw_storage.py:40-80`). This matches
  the fail-closed edge specified in `docs/architecture/architecture.md:95-110`
  and ADR-010's external-root requirement.
- `resolve_object_reference()` rejects empty references, resolves relative or
  absolute references, and rejects any path which resolves outside the external
  root (`raw_storage.py:82-96`). The service applies this validation before its
  raw-artifact lookup/insert (`weather/service.py:229-245`), so traversal fails
  before a raw-artifact row can be persisted.
- Focused tests prove accepted external-root resolution and rejection of missing
  configuration, nonexistent root, relative root, repository-contained root,
  and `../` traversal (`apps/api/tests/test_raw_storage.py:15-90`).
- This is deliberately a **path/configuration validation** boundary. Its module
  documentation and architecture handoff state that it does not read, write,
  hash, copy, move, or delete payloads, metadata, or sidecars
  (`raw_storage.py:1-5,27-35`; `architecture.md:106-110`). QA ran only
  temporary-directory policy tests and static inspection: no project-root
  `tmp-icon*`/`tmp-gfs*` artifact was opened, moved, copied, deleted, hashed,
  or reused by this assignment. This honors ADR-010's explicit no-operation
  rule (`docs/management/decisions.md:116-120`).

## Executed quality gates

| Command / check | Result | Evidence / limitation |
| --- | --- | --- |
| Focused shared DTO + GFS/ICON adapter tests | **PASS** | `PYTHONPATH=D:\\Everest; python -m pytest -q packages/weather_ingestion_contract/tests services/weather/tests/test_gfs_ingestion.py services/weather/tests/test_icon_ingestion.py` → **11 passed in 0.05s**. |
| Focused raw-storage tests | **PASS** | From `apps/api`: `python -m pytest -q tests/test_raw_storage.py -rs` → **6 passed in 0.03s**. Tests use `tmp_path`; no repository raw artifact is touched. |
| Remediation repeat stability | **PASS** | Shared DTO, raw-storage, GFS-adapter, and ICON-adapter tests were executed **10 independent times**: **17 passed** on every run, no retry, no sleep, and no pass-on-retry. |
| Full repository pytest | **PASS with skips/warning** | `PYTHONPATH=D:\\Everest; python -m pytest -q` → **78 passed, 10 skipped, 1 warning in 1.26s**. See REM-02-03-QA-001. |
| API-local pytest | **PASS with PostgreSQL skips** | From `apps/api`: `python -m pytest -q -rs` → **25 passed, 10 skipped in 0.40s**. |
| Black | **PASS** | `python -m black --check --line-length 80 packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` → **56 files unchanged**. |
| Pylint | **PASS** | Shared-package Pylint, weather-package Pylint, and API Pylint each rated **10.00/10**. |
| Compile | **PASS** | `python -m compileall -q packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` exited 0. |

## PostgreSQL execution status — SKIPPED, not passed

`EVEREST_TEST_DATABASE_URL` was unset. No PostgreSQL connection, Alembic
upgrade/downgrade, raw row, canonical row, persistence transaction, or API
request backed by PostgreSQL ran in this QA assignment. The 10 API-local skips
are exactly:

- **2** GFS adapter PostgreSQL/API composition tests;
- **3** registry PostgreSQL tests; and
- **5** weather-persistence PostgreSQL tests.

The raw-storage unit tests are filesystem-path validation tests only; they are
not persistence evidence. Existing historical DBRE results are not substituted
for this skipped execution. **ICON DB/API tests were not run.**

## Remaining gates and non-authorizations

1. **Gate A — AOI authority remains BLOCKED.** `docs/everest-aoi.md:7-8,
   32-62` identifies a pending AOI version/geometry/CRS and prohibits
   geometry-based acquisition. ADR-012 likewise records manager approval as
   pending (`docs/management/decisions.md:155-176`). This QA pass does not close
   it.
2. **Gate B — canonical-contract path remains subject to its owning-domain
   handoff.** This review did not re-accept meteorology semantics or create a
   provider execution claim.
3. **Gate C — operational raw-storage approval remains open.** The code now
   fails closed on a supplied external root, but ADR-010 deliberately records
   no approved concrete runtime root, retention owner/class, access controls, or
   AOI-backed raw-data reuse authority (`decisions.md:98-139`). Validation code
   is not approval of a root or raw artifact.
4. **Gate D — shared-port isolation is closed by this QA record only.** That
   closure must not be interpreted as closure of Gates A-C, ADR-011 lifecycle
   reconciliation, or the Phase-E DBRE prerequisites.
5. **ICON remains blocked from DB/API/reuse.** Per ADR-007, ADR-010, ADR-011,
    and the active Phase-E plan, ICON is not verified or currently healthy; it
    has no accepted database/API result. No external retrieval, raw reuse, source
    lifecycle escalation, or ICON DBRE/API run is authorized by REM-02-03-QA.

---

# EV-DATA-001-REM-02-QA-RETEST — 2026-08-21

**Assignment:** Re-run independent QA of the ADR-009 shared-contract migration,
DTO metadata tightening, formatting, and external raw-root validation boundary.
**Scope:** `AGENTS.md`; ADR-008 through ADR-012; the shared contract package;
provider adapters and tests; the backend port implementation and raw-root tests;
and Python quality gates. QA changed no business code or test code. This QA
handoff is the only modified file.

**Explicit non-execution:** No external retrieval, raw-artifact operation, raw
reuse, ICON database/API test, or ICON DBRE execution was performed. The active
environment had no `EVEREST_TEST_DATABASE_URL`; PostgreSQL cases are reported as
skipped, never as passed.

## Retest verdict

**PASS — Gate D (ADR-009 shared ingestion-port isolation) is closed by this
retest.** The shared boundary rejects non-scalar metadata before a provider
adapter can invoke its injected port; `services/weather/` has no production
import from `apps.api` or `everest_api`; the backend implements the shared port;
provider adapter tests and raw-root validation tests pass; and Black, Pylint,
and compilation pass.

**Gate B is NOT closed by this assignment.** The canonical weather semantics are
defined by the normative meteorology handoff, but the active Phase-E plan still
requires an explicit Phase-E authority confirmation that the ICON path exercises
that one contract (`docs/qa/test-plan.md:923-930`). This shared-port retest did
not re-accept provider normalization/QC semantics, perform ICON execution, or
turn the existing Phase-B/Phase-C evidence into Phase-E Gate-B evidence.

## Requested contract and boundary verification

| Control | Result | Independent evidence |
| --- | --- | --- |
| No `services/weather` to backend-app import | **PASS** | A production-Python import scan for `apps.api` and `everest_api` returned no matches in `services/weather/`. GFS and ICON adapters import `weather_ingestion_contract` and local meteorology types only (`services/weather/gfs/ingestion.py:19-24`; `services/weather/icon/ingestion.py:10-15`). |
| Shared package remains owner-neutral | **PASS** | `packages/weather_ingestion_contract/pyproject.toml:5-10` has no runtime dependencies. Its DTO/protocol package imports only standard-library modules and exports `RawArtifactDescriptor`, `CanonicalRecordInput`, `AuxiliaryArtifactReference`, `IngestionPort`, and `PrimitiveValue` (`contracts.py:11-18,41-125`; `__init__.py:8-22`). |
| Scalar metadata rejection | **PASS** | `RawArtifactDescriptor.__post_init__()` calls `_validate_metadata()` before port use (`packages/weather_ingestion_contract/weather_ingestion_contract/contracts.py:22-38,62-66`). Exact string keys and only exact `str`, `int`, `float`, `bool`, or `None` values are accepted. Shared-contract tests reject a provider object, nested mapping, and non-string key (`packages/weather_ingestion_contract/tests/test_contracts.py:27-62`). Adapter construction passes raw metadata into this validating DTO before `IngestionPort.ingest()` (`gfs/ingestion.py:78-102`; `icon/ingestion.py:63-79`), so unsupported metadata cannot reach a port. |
| Provider adapter regression tests | **PASS** | `test_gfs_ingestion.py` and `test_icon_ingestion.py` use injected fake ports to verify lossless DTO forwarding, pre-port provenance rejection, and source-level owner-neutral imports. Focused execution completed **7 passed**. Combined shared DTO plus GFS/ICON adapter suite completed **11 passed**. The 11-test focused suite was run **10 independent times**, all green, with no retry and no wall-clock wait. |
| Backend shared-port implementation | **PASS by inspection and non-DB regression** | `WeatherIngestionService` explicitly implements `IngestionPort` and accepts shared `AuxiliaryArtifactReference` commands (`apps/api/everest_api/weather/service.py:14-19,33-55`). It validates the raw-root reference before raw persistence (`:229-258`), retains raw evidence first (`:80-92`), and escalates lifecycle/health only after canonical insertion and commit (`:93-137`). The old backend module is compatibility exports plus the narrow static-altitude wrapper, not a duplicate DTO owner (`apps/api/everest_api/weather/contracts.py:1-39`). |
| External raw-root validation boundary | **PASS — validation only** | `RawStoragePolicy` requires an existing absolute root outside the repository and prevents object-reference escape (`apps/api/everest_api/raw_storage.py:40-96`). `apps/api/tests/test_raw_storage.py` completed **6 passed** using temporary directories. This proves configuration/path validation only; it does not read, write, hash, move, or validate a real raw artifact. |

## Executed checks

| Exact command / working directory | Result | Evidence / limitation |
| --- | --- | --- |
| `PYTHONPATH=D:\Everest; python -m pytest -q packages/weather_ingestion_contract/tests services/weather/tests/test_gfs_ingestion.py services/weather/tests/test_icon_ingestion.py` (`D:\Everest`) | **PASS** | **11 passed in 0.03s**. |
| Same focused shared-contract/adapter command, ten independent invocations | **PASS** | **11 passed** on every invocation. No retry, hard sleep, pass-on-retry, network call, or shared external data was used. |
| `python -m pytest -q tests/test_raw_storage.py -rs` (`D:\Everest\apps\api`) | **PASS** | **6 passed in 0.03s**. |
| `PYTHONPATH=D:\Everest; python -m pytest -q services/weather/tests/test_gfs_ingestion.py services/weather/tests/test_icon_ingestion.py` (`D:\Everest`) | **PASS** | **7 passed in 0.03s**. |
| `PYTHONPATH=D:\Everest; python -m pytest -q` (`D:\Everest`) | **PASS with declared environmental skips** | **78 passed, 10 skipped, 1 warning in 1.40s**. The warning is the known root-level unregistered `real_data` marker; it is non-blocking runner configuration debt. |
| `PYTHONPATH=D:\Everest;D:\Everest\apps\api; python -m pytest -q -rs` (`D:\Everest\apps\api`) | **PASS with PostgreSQL skips** | **25 passed, 10 skipped in 0.45s**. Skip reasons are listed below. |
| `python -m black --check --line-length 80 packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` (`D:\Everest`) | **PASS** | **56 files would be left unchanged.** |
| Package-local Pylint; weather Pylint; then API Pylint with repository/API `PYTHONPATH` | **PASS** | Each invocation rated **10.00/10**: `weather_ingestion_contract tests` from the package root; `services/weather services/weather/tests` from repository root; and API source/tests plus migrations from `apps/api`. |
| `python -m compileall -q packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` (`D:\Everest`) | **PASS** | Exit 0 (`compileall: PASS`). |
| Production import scan of `services/weather/**/*.py` for `apps.api` or `everest_api` imports | **PASS** | No matching production import was found. |

## PostgreSQL status — skipped, not passed

`EVEREST_TEST_DATABASE_URL` was **UNSET**. Accordingly, QA did not open a
database connection, run Alembic against PostgreSQL, persist a raw/canonical
record, or make a database-backed API request.

- `apps/api/tests/test_gfs_adapter_integration.py`: **2 skipped** — both GFS
  PostgreSQL/API composition tests require the URL.
- `apps/api/tests/test_weather_persistence.py`: **2 passed, 5 skipped** — the
  five PostgreSQL persistence cases require the URL.
- API-local full suite: **10 skipped** total: 2 GFS adapter composition, 3
  registry PostgreSQL, and 5 weather-persistence PostgreSQL cases.

These skips do not invalidate the structural Gate-D decision, but they cannot
serve as database/API acceptance. **ICON database/API was not executed.**

## Exact remaining gates and non-authorizations

1. **Gate A — AOI authority/basis: open pending handoff reconciliation.**
   `docs/everest-aoi.md:7-64` now records an AOI ID/version, approved center,
   CRS/axis convention, and geodesic-radius rule, while ADR-012 still states
   approval is pending (`docs/management/decisions.md:267-288`). The controlling
   owners must reconcile that contradiction and record the exact approved Phase-E
   provider/product/version basis before acquisition or reuse.
2. **Gate B — canonical-contract authority: open.** As stated above, the
   normative schema exists (`docs/meteorology/weather-spec.md:14-111`), but the
   active Phase-E plan requires explicit proof that the ICON path uses it. This
   REM-02 retest closes no provider semantic/normalization authority gate.
3. **Gate C — operational raw-storage enforcement: open.** ADR-010 approves
   `D:\Everest-data\raw` as a root but expressly requires connector use,
   recorded retention/access/disposition controls, repository-exclusion
   enforcement, and QA runtime evidence (`docs/management/decisions.md:98-136,
   230-256`). The passing raw-root unit tests are not proof of those controls.
4. **Gate D — shared ingestion-port isolation: CLOSED.** This retest supplies
   the requested independent structural, scalar-boundary, adapter, format,
   lint, and compilation evidence. Its closure does not close Gates A-C.
5. **ADR-011 lifecycle reconciliation and Phase-E prerequisites remain open.**
   ICON is not `verified`, not currently healthy, and has no accepted
   database/API result (`docs/management/decisions.md:258-265`). No external
   retrieval, existing-artifact reuse, lifecycle escalation, ICON DB/API test,
   or DBRE run is authorized until the active Phase-E gate matrix and its
   prerequisites are separately satisfied.
---

# EV-DATA-001-REM-01-AOI-QA — Gate A Independent Verification

**Assignment ID:** `EV-DATA-001-REM-01-AOI-QA`  
**Review date:** 2026-08-21  
**Scope:** Documentation-only independent verification of Gate A against the
latest `AGENTS.md` and current `docs/everest-aoi.md`. QA did not modify business
code, tests, the AOI GeoJSON, or external/raw data. No provider acquisition,
ICON database execution, or ICON API execution was performed.

## Verdict

**FAIL — Gate A is not closed for operational use.** The AOI authority and
deterministic artifact evidence are substantially present, but the current
handoffs contain unresolved approval/governance contradictions and the
serialized expanded boundary is not explicitly Manager-approved for operational
use. This review does not authorize DWD ICON acquisition, existing raw-data
reuse, or ICON DB/API work.

## Evidence and acceptance checks

| Check | Result | Evidence and assessment |
| --- | --- | --- |
| Manager-approved center | **PASS** | `docs/everest-aoi.md:22-36,276-277` records latitude `27.98806`, longitude `86.92528`, WGS 84 / `EPSG:4326`, prose latitude/longitude order, and GeoJSON `[longitude, latitude]` order. |
| Default AOI | **PASS** | `docs/everest-aoi.md:40-49` defines the default as a 100 km geodesic radius and does not invent route, camp, or named-feature geometries; this matches `AGENTS.md:280-298`. |
| Explicit expanded AOI approval | **PASS for radius approval** | `docs/everest-aoi.md:51-64` explicitly records the Manager-approved 2,000 km geodesic expansion on 2026-08-21 as an exception, with exact `2,000,000 m` WGS 84 distance. It remains distinct from the default 100 km AOI. |
| Generated GeoJSON artifact | **PASS as artifact evidence** | `docs/everest-aoi.md:191-228` records `docs/everest-south-route-v1.0-expanded-2000km.geojson`, `Polygon`, WGS 84 / `EPSG:4326`, center, exact radius, canonical JSON rules, and no antimeridian crossing. The artifact is present at that path. |
| 360 vertices and closure | **PASS as recorded evidence** | The AOI record states 360 unique direct-geodesic vertices for azimuths 0–359 and 361 serialized positions including an exact copy of vertex 0 (`docs/everest-aoi.md:104-108,211-212,224-228`). |
| Artifact hash and bbox | **PASS as recorded evidence** | `docs/everest-aoi.md:208-210` records SHA-256 `b21ce4c8fe8d0fae15e0723e54fa3224f06e253b2662cdaee58e8efe1bb290ac`, 14,070 bytes, and bbox `[66.49531953902317,9.921015585444335,107.3552404609768,46.00929037112946]`; it states the bbox was derived from serialized coordinates only. |
| GeographicLib/tool record | **PASS** | The record specifies `geographiclib==2.1`, `Geodesic.WGS84.Direct`/`Inverse`, Python `3.14.5`, Windows runtime, exact generation command, generation timestamp, generator SHA-256, tolerance, and maximum residual (`docs/everest-aoi.md:114-132,191-215`). Official GeographicLib Python 2.1 documentation identifies version 2.1, date 2025-08-21, and MIT/X11 licensing. |
| No invented route/camp geometries | **PASS** | `docs/everest-aoi.md:66-80,130-134,245-257,283-285` explicitly excludes route, EBC/C1/C2/C3/C4/Summit, Khumbu Icefall, Western Cwm, Lhotse Face, and other named-feature geometries. The artifact is only the derived radius boundary. |
| Source records and live-verification wording | **PASS** | The Tianditu and NGA records at `docs/everest-aoi.md:230-243` are labeled supplied/user-approved records, explicitly not live verification. The document states no external URL was accessed and makes no live source, coordinate, license, access, or service claim. |
| Current governance consistency | **FAIL** | `docs/management/decisions.md:267-287` still says ADR-012 is “Pending approval; AOI not approved” and says serialized geometry/CRS remain pending. `docs/management/board.md:18,113-143` still marks AOI work `in progress`, says serialized geometry/bbox are pending, and blocks acquisition/reuse. These conflict with the current AOI document’s approved radius definitions and recorded generated artifact. |
| Serialized-boundary operational approval | **FAIL / open approval** | `docs/everest-aoi.md:78-80` requires a future serialized boundary to be separately versioned, validated, and approved by the Everest Manager before operational use. Generation and validation are recorded, but distinct Manager approval of this serialized artifact is not. |

## Exact remaining approval and compliance gaps

1. **Manager approval of the serialized artifact is missing.** Record an
   explicit Manager decision for
   `docs/everest-south-route-v1.0-expanded-2000km.geojson`, including whether
   operational use is approved, effective UTC date/time, artifact SHA-256,
   geometry type, AOI identifier/version, and the limited workflow for which
   the 2,000 km exception may be used.
2. **ADR-012 is stale and contradictory.** Reconcile
   `docs/management/decisions.md:267-287` with `docs/everest-aoi.md`; either
   close ADR-012 with the required approval record or explicitly state that
   only the radius rule is approved and the serialized artifact remains blocked.
3. **The delivery board is stale.** Reconcile
   `docs/management/board.md:18,113-143` with the artifact evidence. It must
   distinguish approved radius rules, generated/validated artifact evidence,
   and operational approval of that artifact.
4. **No acquisition authorization follows from this review.** Under the
   latest `AGENTS.md`, AOI-limited acquisition and separately documented
   expansion approval are mandatory. Existing raw-data reuse and new provider
   retrieval remain blocked by current board/retention controls. ICON DB/API
   execution remains explicitly unauthorized.

## Claim-discipline note

The source URLs are provenance records only, not live-verification results.
The GeographicLib documentation lookup verifies the tool documentation record,
not Tianditu/NGA data. No claim is made that any provider response, license,
live endpoint, raw retrieval, ICON database, or ICON API is currently available
or healthy.

**Handoff:** Gate A **FAIL** pending the three governance/approval
reconciliations above. No provider acquisition or ICON DB/API work was started.

---

# EV-DATA-001-E-SEMANTIC-QA — Gate B ICON Contract Proof Review

**Assignment ID:** `EV-DATA-001-E-SEMANTIC-QA`  
**Review date:** 2026-08-21  
**Scope:** Documentation-and-source inspection only. QA reviewed the normative
`docs/meteorology/weather-spec.md`, compatibility pointer
`docs/weather-spec.md`, approved AOI authority `docs/everest-aoi.md`, the
owner-neutral shared contract at
`packages/weather_ingestion_contract/weather_ingestion_contract/contracts.py`,
and the ICON parser, normalizer, ingestion adapter, and deterministic tests
under `services/weather/icon/` and `services/weather/tests/`. QA changed only
this plan. No business code or test was changed; no external retrieval,
historical-raw reuse or operation, database, API, or DBRE execution was run.

## Gate B Verdict

**BLOCKED — Gate B is not closed.** ADR-008 requires provider-path evidence,
not merely an accepted Phase-B generic contract or a shared-port isolation
result. The ICON code is visibly intended to use the normative contract, and
the current deterministic tests prove several important unit mappings. They do
not yet prove the complete provider-path semantic set required by ADR-008:
UTC-valid-time handling, positive cycle/lead/valid-time identity, wind
direction convention, all required source/model/forecast identity fields, and
the specified null/QC outcomes. Gate D's shared-port isolation acceptance is
separate and is not evidence for this gate.

This is a semantic proof decision only. It does not change ICON's lifecycle
(`connected` historical processing evidence only), health (`unknown`), Gate A
or Gate C status, or the prohibition on ICON persistence/API work.

## Normative Proof Target

The sole semantic authority is `docs/meteorology/weather-spec.md`; the root
`docs/weather-spec.md` is only its non-duplicating compatibility pointer. The
provider path must prove the following without redefining them locally:

1. `timestamp` is the UTC forecast valid time; `timestamp == forecast_cycle +
   forecast_lead_time`; non-UTC/naive values are rejected rather than guessed.
2. The spatial identity is the DWD native grid UUID plus its real point index,
   not a rounded latitude/longitude key.
3. `HSURF` supplies altitude in metres; `T_2M` Kelvin is explicitly converted
   to Celsius; `U_10M` and `V_10M` in declared m/s produce wind speed in m/s
   and direction in degrees clockwise from true north.
4. Missing provider values remain null, are never silently imputed as zero, and
   receive additive QC. Unknown/invalid declared units produce null affected
   values and `invalid_unit`; magnitude-based unit guessing is forbidden.
5. Records remain `forecast` records with `source='dwd-icon'`, `model='ICON'`,
   UTC cycle, integral lead, valid time, and the corresponding native spatial
   key carried unchanged through the shared DTO boundary.

The approved AOI authority fixes the Everest reference center at latitude
`27.98806`, longitude `86.92528`, WGS 84 / `EPSG:4326`, with a default 100 km
geodesic radius. Existing deterministic fixtures use the nearby requested
coordinate `27.9881, 86.9250`; they are semantic unit fixtures, not evidence
of acquisition, AOI membership execution, or permission to reuse any raw
artifact.

## Existing Deterministic Test Coverage Assessment

| Required semantic | Existing deterministic evidence | Assessment | Exact missing proof |
| --- | --- | --- | --- |
| UTC valid time | Parser constructs `cycle` and `valid_time` with `timezone.utc` (`icon/parser.py:50-65`); normalizer calls `anchor.valid_time.astimezone(timezone.utc)` (`normalizer.py:60-75`). | **Partial — implementation inspection only.** | No deterministic parser fixture/assertion proves a non-zero-offset input becomes the expected UTC instant, and no test proves naive/non-UTC input is rejected/flagged by the provider path. `test_icon.py` contains no timestamp assertion. |
| Cycle + lead + valid-time identity | Parser derives whole-hour lead from `valid_time - cycle` and fails negative/fractional leads (`parser.py:60-65`); normalizer derives `ForecastIdentity` from the anchor (`normalizer.py:73-75`); adapter rejects a cycle mismatch before port use (`test_icon_ingestion.py:102-119`). | **Partial.** | No positive normalizer assertion proves `timestamp`, UTC `forecast.cycle`, and lead equal an explicit non-zero-lead fixture's valid time. No deterministic parser case proves cycle/valid-time extraction from GRIB metadata, and no malformed lead/cycle-time mismatch QC/adapter matrix is asserted beyond one cycle mismatch. |
| Native DWD spatial key | `test_provider_spatial_key_preserves_native_grid_identity` asserts `icon:<grid UUID>:0` from the actual native index (`test_icon.py:93-99`); implementation rejects missing unstructured-grid UUID/index (`normalizer.py:96-102`). | **Covered at the helper level; incomplete end-to-end semantic propagation.** | No test proves that the index chosen by `normalize_messages()` for a multi-cell fixture is the same UUID/index provided to `IconCanonicalRecord` and then forwarded as `CanonicalRecordInput.spatial_key`. The adapter fixture uses a coordinate-shaped synthetic key rather than the required UUID/index form (`test_icon_ingestion.py:65-86`). |
| Altitude in metres | The normalizer test supplies `hsurf=6012.0` with declared unit `m` and asserts `record.altitude == 6012.0` (`test_icon.py:74-90`). | **Covered for valid mapping.** | No deterministic test asserts invalid/missing `HSURF` yields the required non-fabricated altitude plus additive QC, nor that another altitude unit cannot be guessed. |
| Temperature in Celsius | The normalizer test supplies `273.15 K` and asserts `0.0 C` (`test_icon.py:74-87`). Unknown temperature units result in `temperature is None`, `invalid_unit`, and `missing_value` (`test_icon.py:102-109`). | **Covered for `T_2M` valid conversion and one unknown-unit path.** | No test distinguishes declared-but-invalid versus absent temperature units, or proves raw/provider unit provenance is retained for the rejected value. Those are required evidence for the full raw-to-QC chain, though no raw operation is authorized in this assignment. |
| Wind speed m/s and true-north direction degrees | The valid fixture asserts speed `hypot(3,4) == 5.0` from declared `m s**-1` vectors (`test_icon.py:74-88`). The normalizer formula implements a modulo-360 direction (`normalizer.py:55-58`). | **Partial.** | No assertion verifies the expected true-north clockwise direction for a known vector, its `[0, 360)` range, or calm/absent vectors producing null direction. No invalid `U_10M`/`V_10M` unit test proves speed/direction become null with `invalid_unit` and no magnitude guess. |
| Missing values stay null with additive QC | Valid normalization constructs null precipitation/visibility and asserts `missing_value` (`test_icon.py:74-90`); unknown `T_2M` asserts null plus both `invalid_unit` and `missing_value` (`:102-109`). The adapter forwarding test asserts null precipitation and retained `missing_value` (`test_icon_ingestion.py:89-100`). | **Partial.** | No explicit assertion covers null visibility, null precipitation, null wind, and null temperature as discrete canonical outputs with their expected additive flags. No test proves a missing field is not replaced by zero or that caller-supplied/additive flags survive the complete ICON normalizer-to-adapter path. |
| Invalid units: no guessing | The normalizer checks exact declared unit strings before using a mapped value (`normalizer.py:105-120`), and the unknown `T_2M` test proves null plus `invalid_unit` (`test_icon.py:102-109`). | **Partial.** | The negative proof is limited to `T_2M`. Add table-driven cases for `T_2M`, `U_10M`, `V_10M`, and `HSURF`, including plausible-by-magnitude but wrong units, and assert no affected canonical value/direction is fabricated. |
| Source, model, forecast record type, and forecast identity | The normalizer sets `forecast`, `dwd-icon`, and `ICON` (`normalizer.py:60-76`). The adapter rejects non-forecast records, source/model mismatch, missing forecast identity, lead mismatch, and valid-time mismatch in code (`icon/ingestion.py:109-127`); existing test proves only cycle mismatch. | **Partial — mostly inspection.** | No positive test asserts normalizer output has `RecordType.FORECAST`, `source='dwd-icon'`, `model='ICON'`, and a matching `ForecastIdentity`. No parameterized test proves every documented pre-port rejection is before the fake port; the existing test only proves cycle mismatch. |

## Concrete Provider-Semantic Proof Checklist for Resubmission

Meteorology-owned deterministic tests must supply all of the following before
QA can close Gate B. Each must use owned in-memory fixtures/fake ports only;
no network, raw artifact, database, API, shared seed, retry, or wall-clock
sleep is permitted.

1. **UTC/cycle/lead fixture:** construct a non-zero ICON lead with an explicit
   UTC cycle and valid time. Assert normalizer timestamp is UTC, forecast cycle
   and lead are retained, and exact equality `valid == cycle + lead`. Add a
   negative parser/normalizer/adapter case for invalid or inconsistent time and
   assert fail-closed or the normative additive flag at the layer responsible.
2. **Native-grid propagation fixture:** use at least two native cells where the
   nearest requested Everest fixture point is unambiguous. Assert selected
   latitude/longitude, UUID/index key `icon:<uuid>:<index>`, and the exact same
   key forwarded through `IconCanonicalRecord` into `CanonicalRecordInput`.
3. **Explicit units table:** cover valid `T_2M K -> C`, `U_10M/V_10M m s**-1`,
   and `HSURF m`. For each field, cover an unknown/wrong declared unit and a
   plausible magnitude that must still be rejected. Assert affected values are
   null/non-fabricated and `invalid_unit` is additive.
4. **Wind convention vectors:** assert at least cardinal/intercardinal known
   vectors, including the expected degrees clockwise from true north; assert
   direction remains in `[0, 360)`. Assert calm or incomplete vectors produce
   null direction and appropriate missing QC without invented speed/direction.
5. **Missing/QC preservation:** independently assert null precipitation,
   visibility, temperature, wind speed, and wind direction behaviour as
   applicable; assert `missing_value` is additive, no value becomes zero, and
   pre-existing non-clean flags survive validation/DTO forwarding unchanged.
6. **Forecast provenance positive and negative matrix:** assert normalizer's
   positive record type/source/model/forecast identity. Parameterize adapter
   pre-port rejection over source, model, record type, absent forecast, cycle,
   lead, valid time, and empty/malformed native spatial key; in every negative
   case assert the fake port received no call.
7. **Contract-authority guard:** retain a focused static/documentary test or
   review assertion that provider semantic terms refer to the canonical
   `docs/meteorology/weather-spec.md`, not a copied ICON schema or the
   compatibility pointer. This guard must not try to redefine meteorological
   units in provider code.
8. **Determinism evidence:** run the focused semantic suite ten independent
   times (or `--repeat-each=10` when available), with zero retry/pass-on-retry.
   Preserve commands and results in the meteorology handoff for QA review.

## Exact Missing Evidence Required to Close Gate B

1. Executed deterministic test output for the eight checklist items above,
   including ten consecutive green focused runs.
2. Assertions—not only code inspection—for UTC valid time and an explicit
   non-zero cycle/lead/valid-time identity.
3. Assertions for wind direction convention/range and calm/incomplete-vector
   null behaviour.
4. A positive normalizer assertion for forecast record type, source, model,
   and forecast identity, plus a complete adapter pre-port provenance-rejection
   matrix.
5. A native UUID/index spatial-key propagation assertion from selection through
   shared DTO, replacing the current coordinate-shaped adapter fixture as the
   only adapter-path evidence.
6. Table-driven invalid-unit/no-guessing evidence for all ICON mapped fields,
   especially wind components and `HSURF`, plus explicit missing/null/QC
   preservation assertions.

No real DWD retrieval, historical raw reuse, database persistence, API query,
or source lifecycle change is missing **from this Gate-B semantic review**;
those activities remain separately blocked by Gates A/C and the Phase-E DBRE
prerequisites. They must not be used as a shortcut around the deterministic
semantic evidence listed above.

**Handoff:** **Gate B remains BLOCKED.** ICON has not passed Phase-E semantic
QA and remains ineligible for ICON DBRE, PostgreSQL persistence, API
acceptance, source verification, or current-health claims.

---

# EV-DATA-001-REM-02-GATEB-CLOSE — Gate B independent verification

**Assignment ID:** `EV-DATA-001-REM-02-GATEB-CLOSE`  
**Review date:** 2026-08-21  
**Scope:** Independent verification of the latest ICON semantic-test additions
against ADR-008. Reviewed `AGENTS.md`, ADR-008, both weather-spec documents,
the ICON parser/normalizer/adapter and tests, and the preceding Gate-B QA
record above. QA changed no business or test code; this QA handoff is the only
modified file. No external retrieval, raw-artifact reuse or operation,
database, API, or DBRE execution was performed.

## Verdict

**PASS — Gate B is closed for the deterministic ICON canonical-contract
semantic boundary.** The latest focused suite supplies provider-path assertions
for the required time, native spatial identity, units, wind convention,
nullable values, provenance, additive QC, and adapter pre-port rejection
matrix. This closes only ADR-008. It does not close Gates A or C, authorize
external retrieval/raw reuse, or authorize ICON PostgreSQL/API/DBRE work.
ICON remains not `verified` and current operational health remains `unknown`.

## ADR-008 item-by-item verification

| ADR-008 requirement | Result | Evidence / exact limitation |
| --- | --- | --- |
| Normative path authority | **PASS — source/document review** | `docs/meteorology/weather-spec.md` is explicitly the sole contract; `docs/weather-spec.md` is only a non-duplicating pointer (`docs/management/decisions.md:75-101`). ICON imports the shared canonical `WeatherRecord` contract (`services/weather/icon/normalizer.py:14-20`) and does not define a provider-local schema. No independent executable authority guard was added; this is a documentation/source-review result. |
| UTC valid time and cycle + lead | **PASS** | `test_normalizer_retains_nonzero_utc_forecast_identity` asserts a three-hour lead, UTC timestamp, retained cycle/lead, and exact `valid == cycle + lead` (`services/weather/tests/test_icon.py:109-123`). Offset normalization and naive rejection are asserted at `:126-142`; parser derives whole-hour UTC cycle/valid values (`icon/parser.py:50-65`). |
| Native spatial key propagation | **PASS — with fixture-boundary note** | Nearest-cell selection and UUID/index key are asserted for a multi-cell fixture (`test_icon.py:145-166`), and adapter output is asserted to preserve the native-shaped key (`test_icon_ingestion.py:90-102`). The adapter test constructs its `IconCanonicalRecord` directly; there is no single test chaining `normalize_canonical_record()` into the adapter. This is residual evidence detail, not a semantic failure because both boundaries and the exact key format are independently asserted. |
| Altitude in metres | **PASS** | `HSURF` declared `m` is retained as altitude (`test_icon.py:87-103`); invalid `HSURF` units are table-tested and leave altitude unavailable with `invalid_unit` (`:179-197`). Missing `HSURF` adds `missing_value` in the normalizer path (`normalizer.py:54-55`). |
| Temperature in Celsius | **PASS** | `273.15 K -> 0.0 C` is asserted (`test_icon.py:87-103`). Wrong/unknown temperature declarations produce null plus additive `invalid_unit`/`missing_value` (`:169-197`). |
| Wind m/s, true-north degrees, range, calm | **PASS** | Declared m/s vectors produce `hypot(3,4) == 5.0` (`:87-103`). Cardinal/intercardinal vectors assert the true-north clockwise convention and `[0,360)` range (`:218-241`). Zero vectors assert speed `0.0` and null direction with `missing_value` (`:199-215`). Wrong `U_10M`/`V_10M` units are table-tested as non-converting (`:179-197`). |
| Precipitation mm / visibility m / null behavior | **PASS for ICON applicability** | ICON does not provide precipitation or visibility in this provider path; both canonical fields are explicitly null and are asserted in normalizer and adapter tests (`test_icon.py:199-215`; `test_icon_ingestion.py:90-102`). No precipitation/visibility conversion test is applicable to the current ICON message mapping, and no test proves a hypothetical unsupported precipitation/visibility unit is rejected. That is the exact non-applicable evidence boundary, not a fabricated conversion claim. |
| Invalid units: no guessing for all mapped fields | **PASS** | Table-driven plausible-but-wrong declarations cover `T_2M`, `U_10M`, `V_10M`, and `HSURF`; each affected canonical value remains unavailable and `invalid_unit` is asserted (`test_icon.py:179-197`). `_values_and_flags()` checks declared units before conversion (`normalizer.py:134-154`); no magnitude inference exists. |
| Source/model/forecast identity | **PASS** | Positive normalizer assertions cover `forecast`, `dwd-icon`, and `ICON` (`test_icon.py:87-107`) plus matching forecast identity (`:109-123`). Adapter negative coverage is parameterized for source, model, record type, absent identity, cycle, lead, valid time, and empty native key; every case asserts the fake port is not called (`test_icon_ingestion.py:125-173`). |
| Additive QC and retention of nulls | **PASS** | Non-finite/missing values remain null; calm speed is not changed to null or an invented direction; `missing_value` and `invalid_unit` remain additive (`test_icon.py:169-215`). The adapter forwards nullable values and QC flags without filtering (`test_icon_ingestion.py:90-102`; `icon/ingestion.py:110-162`). Raw retention itself is outside this semantic gate and was not executed. |
| Adapter negative matrix | **PASS** | The complete documented pre-port matrix is parameterized for source, model, record type, missing forecast identity, cycle, lead, valid time, and missing spatial key (`test_icon_ingestion.py:125-173`); all cases prove zero backend-port calls. |

## Executed checks

| Exact command | Result | Evidence / limitation |
| --- | --- | --- |
| Focused semantic suite, ten consecutive independent invocations: `PYTHONPATH=D:\\Everest; python -m pytest -q services/weather/tests/test_icon.py services/weather/tests/test_icon_ingestion.py` | **PASS** | Runs 1–10 each reported **42 passed**. No retries, pass-on-retry, sleeps, network calls, raw artifacts, database, or API were used. |
| Full weather suite: `PYTHONPATH=D:\\Everest; python -m pytest -q services/weather/tests` | **PASS** | **78 passed in 0.67s**. |
| Full repository checks with API path: `PYTHONPATH=D:\\Everest;D:\\Everest\\apps\\api; python -m pytest -q` | **PASS with declared skips/warning** | **107 passed, 10 skipped, 1 warning in 1.40s**. Skips are PostgreSQL/ecCodes environment cases; warning is the known unregistered API-local `real_data` marker. This is not DB/API acceptance. |
| Aggregate Black: `python -m black --check --line-length 80 packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | **56 files unchanged**. |
| Weather Pylint: `PYTHONPATH=D:\\Everest; python -m pylint services/weather services/weather/tests` | **PASS** | **10.00/10**. |
| Compile: `python -m compileall -q packages/weather_ingestion_contract services/weather apps/api/everest_api apps/api/tests apps/api/alembic` | **PASS** | Exit 0. |
| Root `python -m pytest -q` without API path | **FAIL collection configuration** | `ModuleNotFoundError: everest_api` while collecting `apps/api/tests/conftest.py`; rerunning with the declared API `PYTHONPATH` passed as recorded above. This is an invocation/configuration limitation, not an ICON semantic failure. |

## Exact residual evidence and non-authorizations

1. The semantic suite does not include an executable static assertion that
   provider wording points to `docs/meteorology/weather-spec.md`; authority is
   established by reviewed ADR/documentation and imports. A future guard may
   make this machine-checkable, but it is not required to close the semantic
   provider-path evidence in this run.
2. No single test composes `normalize_canonical_record()` directly into
   `compose_icon_ingestion_adapter()`; native-key selection and adapter
   forwarding are covered at adjacent boundaries. This is the only remaining
   test-composition gap identified during review.
3. ICON has no mapped precipitation or visibility source messages, so the
   evidence is canonical null behavior, not a provider conversion. A future
   provider mapping would require explicit mm/m unit tests before use.
4. No external retrieval, raw reuse, database persistence, API query, source
   lifecycle change, or current-health claim was made. These remain outside
   Gate B and prohibited by this assignment.

**Handoff:** ADR-008 Gate B is **CLOSED** for deterministic ICON semantic
contract evidence. Gates A and C and the Phase-E DBRE prerequisites remain
open; ICON DB/API execution remains unauthorized.

---

# EV-DATA-001-REM-03-RETENTION-QA — Retention Runtime Review

**Assignment ID:** `EV-DATA-001-REM-03-RETENTION-QA`  
**Review date:** 2026-08-21  
**Scope:** Independent static/unit review of migration `20260821_0004`, the
backend retention models/service/policy, the shared ingestion DTO, public API
serialization, and the applicable architecture/API/governance handoffs. QA
modified no business or test code; this QA handoff is the only changed file.
No ICON database/API work, DBRE, raw-artifact operation, or external call was
performed.

## Findings first

| ID | Severity | Finding and exact references | Required disposition |
| --- | --- | --- | --- |
| REM-03-QA-001 | **High** | **Disposition is not enforced as an approved, post-expiry lifecycle.** `WeatherIngestionService.transition_retention_state()` accepts `disposition_state='approved'` or `'completed'` without loading/checking `retention_due_at`, without requiring the prior state to be `approved`, and without enforcing a separate approval transition (`apps/api/everest_api/weather/service.py:329-400`). A caller with an allowed *shape* can set `hold_state='released'` and `disposition_state='completed'` in one call, even from a retained, non-expired artifact; it emits only `disposition_completed`. This contradicts the approved control that disposition requires explicit approval **after** expiry and a hold check (`docs/management/decisions.md:182-183,201-205,248-251`). | Backend must model and test a fail-closed lifecycle: verify expiry, verify the persisted hold state, require an independently recorded/authorized approval before completion, and prevent release plus disposition completion in the same transition. Record blocked attempts in the audit trail where required. Do not claim disposition enforcement before executable PostgreSQL evidence exists. |
| REM-03-QA-002 | **High** | **The legal-hold boundary can be bypassed through caller-supplied transition values.** The fail-closed check considers only the requested `hold_state`, not the artifact's persisted state (`service.py:352-359`). Consequently a held artifact may be submitted with `hold_state='released'` and a disposition state in the same call. The method validates an actor ID/role string but explicitly has no IAM/ACL enforcement (`:339-345`), so it cannot establish that this release was authorized. This falls short of the policy requirement that a held artifact be excluded until an auditable authorized release and that missing/ambiguous state fail closed (`decisions.md:206-210,248-249`). | Split and authorize hold release before disposition; reload and validate persisted state inside the transaction; require required hold-release facts and an authorization result from the real deployment boundary. Add deterministic PostgreSQL tests for held, unknown, absent, release, and attempted same-request release/disposition paths. |
| REM-03-QA-003 | **High** | **Audit coverage is a schema vocabulary, not demonstrated runtime coverage.** Migration `0004` permits the required controlled terms and blocks audit updates/deletes (`apps/api/alembic/versions/20260821_0004_raw_retention_audit.py:97-157`), but the implemented service emits only `accepted`, `reused`, hold/disposition transition events (`service.py:252-254,284-286,379-398`). There is no raw read, integrity-failure, or access-change operation/audit path in this reviewed runtime surface, and no tests prove the promised event matrix. Policy requires append-only evidence for acceptance, read, reuse, integrity failure, access change, holds, and disposition (`decisions.md:211-216,252-253`). | Keep this control open. When the corresponding internal operations and real authorization boundary exist, add PostgreSQL tests that prove each allowed event/result, immutable audit row behavior, FK restriction, bounded JSON details, audit due date, and no sensitive raw facts in public responses. |
| REM-03-QA-004 | **Medium** | **Migration `0004` has no focused migration-contract or PostgreSQL lifecycle test in the reviewed static suite.** `apps/api/tests/test_migration_contract.py` reads only migration `0001` (`:5-32`). The existing persistence tests cover classified acceptance and one accepted event (`test_weather_persistence.py:206-227`) but do not cover legacy migration/backfill, audit update/delete rejection, audit vocabulary constraints, retention-transition GUC scope, invalid classes, or hold/disposition failures. The migration's legacy strategy itself is appropriately non-inventive: it assigns only `legacy_unclassified`, `retained`, `unknown`, and a legacy policy version (`0004:58-70`), while constraints require all retention facts for new non-legacy rows (`:71-95`). | Add a disposable-PostgreSQL migration upgrade/downgrade and lifecycle matrix once DBRE is authorized/supplied. It must assert legacy rows never acquire invented owner/period/acquisition/due values, new rows cannot be unclassified, raw/audit immutability works, and unauthorized transition/update attempts fail. This review supplies no DBRE substitute. |
| REM-03-QA-005 | **Medium** | **Public retention privacy is correctly designed but not protected by an explicit regression assertion.** `records_payload()` serializes canonical fields only and omits object references, raw URLs/metadata, retention fields, holds, and audit events (`apps/api/everest_api/app.py:40-67`); no retention operator route is registered (`:74-164`). This agrees with API policy (`docs/api/API.md:18-24,49-53`). However, the reviewed API test checks only invalid profile/correlation handling (`apps/api/tests/test_weather_api.py:15-25`), not successful current/forecast/profile/source/data-health payload redaction. | Add public REST serialization tests against persisted representative rows. Assert absence of `object_reference`, `source_url`, `metadata_json`, hash/checksum values, retention owner/class/period/due date, disposition/hold data, and audit events in every public response. |
| REM-03-QA-006 | **Medium** | **`validate_audit_details()` bounds the string representation and key types but does not itself require JSON-safe values** (`apps/api/everest_api/weather/retention.py:53-60`). The database JSON type will reject some invalid values during persistence, but that is not an intentional, deterministic boundary validation, and the focused unit tests cover only an unclassified decision and oversized details (`test_retention_policy.py:34-41`). | Before a value reaches persistence, validate recursively/strictly against the declared audit-detail contract or narrow audit details to scalar facts. Add deterministic tests for non-string keys, non-JSON values, nested/unbounded values, and exact boundary size. Preserve the existing no-raw-detail policy. |
| REM-03-QA-007 | **Low** | **Governance text is internally stale.** The board accurately says migration `0004`, classified acceptance/reuse audit, and an internal fail-closed transition boundary are implemented (`docs/management/board.md:67-105`), but its later open-control item says “Retention classes, periods, owners, and disposition schedule are not yet assigned” (`:107-111`). The approved decision assigns them (`docs/management/decisions.md:175-185`), and the policy code matches 24 months, 180 days, and 36 months (`retention.py:9-12`). The true open issue is runtime enforcement/evidence, not unassigned policy defaults. | Everest Manager should reconcile the board wording without collapsing the distinction between approved policy, partial backend model, unimplemented IAM/storage enforcement, and absent approved-root/DBRE evidence. |
| REM-03-QA-008 | **Low** | **Focused Pylint is non-zero: 9.86/10.** It reports `R0903` for the four declarative SQLAlchemy model classes and test `_FakeSession`; Black and compilation pass. This is a static-quality failure under the literal mandatory Pylint requirement, although it does not alter the retention-control verdict. | Add narrowly justified framework/test-only suppressions or refactor as appropriate, then rerun Pylint at 10.00/10. QA does not make business-code changes. |

## Verified static properties

| Control | Result | Evidence and boundary |
| --- | --- | --- |
| Approved defaults are backend-owned and deterministic | **PASS — unit/static** | `RetentionDecision()` defaults to `operational_raw`, `Everest Manager`, 63,072,000 seconds (24 months), and version `2026-08-21.v1`; `failed_or_rejected()` selects 15,552,000 seconds (180 days); audit duration is 94,608,000 seconds (36 months) (`retention.py:9-50`). Focused tests assert default calculation and failed-class duration. |
| Classification is required for new artifacts | **PASS — unit/static** | `due_at()` accepts only operational or failed/rejected classes and rejects `legacy_unclassified` (`retention.py:27-42`); migration/model constraints require owner, positive period, acquisition, due date, and policy version for each non-legacy row (`0004:78-84`; `models.py:82-87`). `WeatherIngestionService._persist_raw()` always resolves a backend decision before inserting (`service.py:239-300`). |
| Legacy handling is honest | **PASS — static** | Existing rows become `legacy_unclassified` with `retained` disposition and `unknown` hold state; owner, period, acquired time, and due time are deliberately not invented (`0004:58-70`). This matches API/architecture documentation (`API.md:35-41`; `architecture.md:137-145`). Runtime migration evidence is pending. |
| Shared DTO blocks provider objects in raw metadata | **PASS — static** | `RawArtifactDescriptor` validates string keys and exact scalar/null values before a provider adapter can send metadata over the owner-neutral port (`packages/weather_ingestion_contract/weather_ingestion_contract/contracts.py:18-66`). The backend compatibility module re-exports that DTO rather than creating a competing descriptor (`apps/api/everest_api/weather/contracts.py:1-39`). |
| Audit vocabulary and storage immutability | **PARTIAL** | Migration/model constrain the required named event types, results, roles, actor identity, details size, artifact FK, and indexes (`0004:97-157`; `models.py:229-275`). The trigger rejects audit `UPDATE`/`DELETE`, so append-only storage intent is sound statically. Event production/completeness and PostgreSQL trigger execution remain open under REM-03-QA-003/004. |
| Actor-boundary claim is honest | **PASS — documentation/source review** | The service states that IAM is outside the package and validates only supplied identity/role shape (`service.py:339-351`); API and architecture handoffs say the same (`API.md:49-53`; `architecture.md:142-145`). This is not ACL, root permission, or hold-release authorization evidence. |
| No raw operations in the reviewed backend boundary | **PASS — source review** | `RawStoragePolicy` is used to validate the reference before persistence (`service.py:239-243`), while the API/architecture explicitly limit this boundary to path validation—not reading, writing, copying, hashing, moving, deleting, or reusing payload/sidecars (`API.md:26-31`; `architecture.md:129-133`). No raw operation was performed in this QA assignment. |
| No public retention/raw leakage in current route code | **PASS — static, regression test pending** | Public weather serializers expose canonical records only; source and health routes expose non-secret lifecycle/health data (`app.py:40-67,132-164`). See REM-03-QA-005 for the missing successful-route regression coverage. |

## Executed checks

| Exact command | Result | Evidence / limitation |
| --- | --- | --- |
| `PYTHONPATH=D:\\Everest;D:\\Everest\\apps\\api; python -m pytest -q apps/api/tests/test_retention_policy.py apps/api/tests/test_weather_api.py` | **PASS** | **4 passed in 0.41s**. Deterministic unit/API-adapter tests only; no PostgreSQL, raw-root operation, ICON API/DB work, or external call. |
| `PYTHONPATH=D:\\Everest;D:\\Everest\\apps\\api; python -m pytest -q apps/api/tests/test_migration_contract.py apps/api/tests/test_raw_storage.py` | **PASS** | **8 passed in 0.03s**. These test migration `0001` and raw-root validation boundary; they do not execute migration `0004` or an approved root. |
| `python -m black --check --line-length 80 apps/api/everest_api/weather/retention.py apps/api/everest_api/weather/models.py apps/api/everest_api/weather/service.py apps/api/alembic/versions/20260821_0004_raw_retention_audit.py apps/api/tests/test_retention_policy.py` | **PASS** | **5 files would be left unchanged.** |
| `PYTHONPATH=D:\\Everest;D:\\Everest\\apps\\api; python -m pylint apps/api/everest_api/weather/retention.py apps/api/everest_api/weather/models.py apps/api/everest_api/weather/service.py apps/api/alembic/versions/20260821_0004_raw_retention_audit.py apps/api/tests/test_retention_policy.py apps/api/tests/test_weather_api.py` | **FAIL** | **9.86/10**, only `R0903` findings described in REM-03-QA-008. |
| `python -m compileall -q apps/api/everest_api/weather apps/api/alembic/versions/20260821_0004_raw_retention_audit.py apps/api/tests/test_retention_policy.py apps/api/tests/test_weather_api.py` | **PASS** | Exit 0. |
| Focused suite repeat plugin attempt: `... python -m pytest -q --repeat-each=10 ...` | **NOT AVAILABLE** | The installed pytest does not recognize `--repeat-each`; no repeat result is claimed. This does not replace the required repeat-run evidence when new/changed tests are supplied. |

## Gate C status and handoff

**Gate C: BLOCKED.** The backend has a reviewable policy/defaults model,
classification guard, non-inventive legacy posture, scalar shared DTO, bounded
audit schema, honest actor-boundary wording, and static public-route redaction.
It does **not** have an accepted disposition lifecycle or legal-hold enforcement,
complete runtime audit production, IAM/filesystem least-privilege evidence,
approved-root end-to-end evidence, or migration-`0004` PostgreSQL DBRE.

No DBRE evidence was supplied with this assignment. When supplied later, QA must
evaluate it separately against the approved-root checklist in
`docs/management/decisions.md:228-258`: real UTC timestamps and artifact IDs;
migration `0004` upgrade/downgrade; classification/legacy rows; immutable raw
and audit rows; root escapes; retention persistence/query; persisted-hold
failures; approval/expiry/disposition transitions; audit event matrix; and
least-privilege access. It must not be retroactively inferred from this static
review. ICON DB/API remains blocked, and no external call has been authorized or
executed here.

---

# EV-DATA-001-REM-03-GATEC-CLOSE — Final Gate C QA Decision

> **Historical status notice:** This record predates ADR-013's Gate C-Core /
> Gate C-Operational split. Its application/database evidence and operational
> control findings remain historical evidence, but its single-gate conclusion
> that all ICON DB/API work was blocked is superseded by the
> [authoritative current-status banner](#authoritative-current-status--ev-data-001-e-qa-handoff-clean)
> and
> [`EV-DATA-001-E-QA-FINAL-2`](#ev-data-001-e-qa-final-2--final-full-pipeline-dbre-re-evaluation).
> Gate C-Operational remains open.

**Assignment ID:** `EV-DATA-001-REM-03-GATEC-CLOSE`  
**Review date:** 2026-08-21  
**Scope:** Independent, report-only re-evaluation of ADR-010 Gate C. QA changed
no business code, test code, raw artifact, database, API, or governance record;
this QA plan is the only modified file.

## Findings first

| ID | Severity | Finding and evidence | Required disposition |
| --- | --- | --- | --- |
| GATEC-CLOSE-001 | **High** | **Operating-system raw-root access control is not independently proven.** `RawStoragePolicy` and the ICON connector fail closed for absent, invalid, repository-contained, or escaping paths (`apps/api/everest_api/raw_storage.py:40-96`; `services/weather/icon/connector.py:243-296`). They validate paths only. The connector's read-only-bit attempt is explicitly best effort, not ACL or WORM enforcement (`connector.py:298-321`; `docs/meteorology/weather-spec.md:517-526`). The supplied DBRE result proves database behavior, not root identities, Windows ACLs/IAM, unauthorized read/write denial, or grant/revoke control. ADR-010 requires named least-privilege identities and access-change evidence. | Keep Gate C blocked. Obtain deployment/OS evidence for connector-write, operator-read, unauthorized read/write, grant/change/revoke, and audit identity/approval. |
| GATEC-CLOSE-002 | **High** | **Legal authority and storage immutability remain unproven operational controls.** The backend now verifies persisted hold/disposition state, expiry, separate approval, and separate release/completion calls (`apps/api/everest_api/weather/service.py:344-492`), and the supplied PostgreSQL run exercises those paths. But actor/role remains an asserted input, not authenticated IAM authorization (`service.py:354-359`; `docs/api/API.md:55-57`). No evidence establishes legal retention/hold authority or filesystem/object-store WORM retention against a privileged OS identity. ADR-010 requires those operational controls, not merely schema/state-machine behavior. | Keep Gate C blocked until authorized operational owners, IAM/ACL enforcement, legal-hold authority, and storage-level immutability/retention controls are evidenced. |
| GATEC-CLOSE-003 | **Medium** | **Git-bearing repository-exclusion enforcement cannot be verified in this workspace.** The checkout has no `.git`; architecture/API correctly make no `.gitignore` or tracking claim (`docs/architecture/architecture.md:106-110`; `docs/api/API.md:26-31`). ADR-010 still requires raw payloads, metadata, and sidecars outside Git and lists tracking enforcement as open. | Verify exclusion/tracking in the authoritative Git-bearing checkout without moving, hashing, copying, or reusing legacy `tmp-icon*`/`tmp-gfs*` artifacts. |

## Exact verdict

**FAIL — Gate C is not closed. ICON database/API execution remains unauthorized.**

The latest supplied evidence materially closes the prior **application/database
evidence gap**, but it does not prove all operational controls required by the
latest `AGENTS.md` and ADR-010. Path validation and PostgreSQL constraints cannot
substitute for OS ACL/IAM enforcement, legal authority, filesystem/object-store
WORM immutability, or Git-bearing exclusion verification. Per assignment
instruction, QA must not declare Gate C closed while those controls are unproven.

## Evidence incorporated and independently assessed

### Approved-root ICON artifact smoke — PASS as raw-retention evidence

The supplied fresh smoke record is consistent with the current connector's
content-addressed path, canonical metadata, and sidecar behavior:

| Fact | Accepted evidence |
| --- | --- |
| Runtime root / containment | `EVEREST_RAW_ROOT=D:\Everest-data\raw`; all paths resolved beneath it; no repository-root fallback. |
| Retrieval / forecast UTC | Retrieval `2026-08-21T03:59:32.333262Z`; cycle/valid `2026-08-21T00:00:00Z`; lead `0` hours. |
| Payload | `D:\Everest-data\raw\dwd-icon\e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57\icon_2026082100_000.grib2`; `17,624,861` bytes; SHA-256 `e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57`. |
| Metadata / sidecar | `metadata.json`: `1,392` bytes, SHA-256 `cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf`; `metadata.json.sha256`: `65` bytes, file SHA-256 `0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46`, declaring the matching metadata digest. |
| AOI | `aoi_id=everest-south-route`; `aoi_version=everest-south-route-v1.0`; `aoi_scope_id=everest-south-route-v1.0-expanded-2000km`; requested WGS 84 point `27.98806, 86.92528`. |
| Retention policy | Owner `Everest Manager`; class `operational_raw`; period 24 months from acquisition; retained/not disposed; controlled disposition only after expiry, hold checks, and explicit approval. |

The connector requires an absolute external root, rejects escapes, atomically
fsyncs and rehashes payloads, canonicalizes metadata, and verifies the metadata
sidecar on reuse (`services/weather/icon/connector.py:243-412`). The shared
`RawArtifactDescriptor` rejects non-scalar provider metadata before backend-port
ingestion (`packages/weather_ingestion_contract/weather_ingestion_contract/contracts.py:18-66`).

### Pinned PostgreSQL acceptance — PASS as backend/database evidence

The supplied final DBRE evidence reports a disposable PostgreSQL execution on
documented non-standard port **64035**, migration chain `20260821_0001` through
`20260821_0006`, and **44 passed, no skips**, followed by complete cleanup. It
is accepted as execution evidence for:

- approved-root ICON descriptor persistence and raw-first retention when later
  canonical processing fails;
- persisted owner/class/period/acquisition/due-date/disposition facts;
- append-only raw and audit rows, bounded scalar audit details, and the corrected
  `0005`/`0006` trigger behavior;
- acceptance/reuse/read/integrity-failure/access-change/hold/disposition audit
  actions and audit privacy;
- expiry, prior approval, hold protection, separate release, and completion; and
- public API privacy: no raw path, URL, metadata, checksum, retention, hold, or
  audit data in query responses.

Reviewed migrations support that evidence: `0004` adds classification,
hold/disposition fields and audit vocabulary; `0005` separates raw-transition
and immutable triggers and validates scalar audit JSON; `0006` fixes permitted
PostgreSQL JSON comparison. The cleanup proves the disposable DB/listener/test
resources were removed; it does **not** mean the retained approved-root artifact
was deleted or that operational retention was shortened.

## Control matrix

| ADR-010 / AGENTS control | Result | Gate-C relevance |
| --- | --- | --- |
| Real ICON payload, metadata, and sidecar under approved root | **PASS** | Real approved-root evidence now exists. |
| Integrity/reuse behavior and root escape fail closed | **PASS** | Connector implementation/tests and smoke hashes support this. |
| AOI ID/version/scope and provenance facts | **PASS** | Smoke evidence uses the approved AOI authority. |
| Retention persistence, raw-first behavior, audit, hold/disposition | **PASS — application/DB boundary** | Supplied pinned DBRE evidence covers the `0001`–`0006` chain without skips. |
| API privacy | **PASS — application/API boundary** | Supplied DBRE evidence covers raw/retention/audit redaction. |
| OS ACL / IAM least privilege; unauthorized access | **NOT PROVEN** | High blocker GATEC-CLOSE-001. |
| Legal hold/disposition authority | **NOT PROVEN** | High blocker GATEC-CLOSE-002. |
| Filesystem/object-store WORM or equivalent privileged-write immutability | **NOT PROVEN** | High blocker GATEC-CLOSE-002; best-effort `chmod` is insufficient. |
| Git-bearing repository exclusion/tracking | **NOT PROVEN** | Medium blocker GATEC-CLOSE-003; workspace lacks `.git`. |

## Authorization decision

**ICON DB/API is not authorized by this QA decision.** Gate C remains a required
ADR-010 precondition, and unresolved operational controls prevent closure. This
does not alter ADR-011: ICON is not `verified`, has no QA-accepted ICON DB/API
result, and must not be represented as currently healthy. The supplied DBRE/API
evidence validates the backend control path; it does not authorize Phase-E or
production ICON database/API execution while Gate C is failed.

## Conditions for a future Gate C closure

1. Evidence named connector/operator identities, OS ACL or object-store IAM,
   unauthorized denial, grant/change/revocation, and corresponding audit records.
2. Prove deployment authorization—not caller-provided strings—enforces legal
   hold placement/release and disposition authority.
3. Demonstrate storage-level WORM/immutability (or approved equivalent) against
   privileged modification attempts; a best-effort read-only bit is insufficient.
4. In the authoritative Git-bearing checkout, verify raw payload/metadata/sidecar
   exclusion and non-tracking without operating on legacy `tmp-icon*`/`tmp-gfs*`.
5. Re-run the complete Gate C matrix and issue a new QA closure decision before
   authorizing ICON DB/API work.

**Handoff:** **Gate C FAILED/BLOCKED; ICON DB/API remains unauthorized.**

---

# EV-DATA-001-E-QA-FINAL — Final Phase E DWD ICON QA

**Assignment ID:** `EV-DATA-001-E-QA-FINAL`  
**Review date:** 2026-08-21  
**Scope:** Independent final Phase E acceptance against the current
`AGENTS.md` and ADR-013's Gate C-Core/Gate C-Operational split. QA changed no
business code, tests, migrations, raw artifacts, source registry, or non-QA
handoff. This QA plan is the only modified file.

## Findings first

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| E-QA-FINAL-001 | Low | The pre-final domain and management handoffs still contain prospective statements that ICON has no accepted DB/API result and that all of Gate C blocks Phase E. Those statements were accurate before this final QA but are superseded for execution sequencing by accepted ADR-013 and the final DBRE evidence assessed below. | **Non-blocking follow-up.** The manager and owning domains must reconcile their handoffs after this QA in the normal governance sequence. Preserve the distinction between historical disposable `verified`/`healthy` facts and current post-cleanup health `unknown`. |
| E-QA-FINAL-002 | Informational | Independent access to DWD's official explanatory pages succeeded, but this review's attempts to read the Open Data directory directly returned transport errors. DWD itself states that Open Data service and availability levels are not guaranteed. | This is not a Phase E failure: accepted real retrieval and retained-artifact evidence is historical and integrity-verifiable. It prevents any claim of current endpoint health; current health remains **unknown**. |

**No blocking Phase E finding remains.** In particular, IAM/ACL, legal-hold
authority, WORM/privileged-modification resistance, and authoritative Git
tracking evidence are deliberately **not** claimed or inferred by this review.
They remain Gate C-Operational controls.

## Verdict and authorization

**PASS — Phase E DWD ICON is accepted at Gate C-Core.** This record's
preliminary statement that Phase F could be authorized is **superseded** by the
[authoritative current-status banner](#authoritative-current-status--ev-data-001-e-qa-handoff-clean):
Phase F authorization remains pending final code-review closure.

This decision applies ADR-013, which supersedes the prior single-Gate-C
sequencing interpretation. Gate C-Core is satisfied by the approved external
root and AOI, immutable and checksum-verifiable payload/metadata retention,
real parsing/normalization/QC, owner-neutral adapter, PostgreSQL persistence,
bounded API evidence, deterministic failure behavior, tests, and truthful
lifecycle/health reporting.

**Gate C-Operational remains OPEN and is a production/shared-deployment blocker
only.** It continues to prohibit production/shared deployment, automatic
disposition, and production-grade retention-governance claims until its IAM,
legal/WORM, and Git controls are separately evidenced. Gate C-Operational does
not itself block Phase F, but Phase F remains pending final code-review closure
under the authoritative current-status banner.

Phase E acceptance records a historical disposable transition to
`verified`/`healthy` only after the successful canonical commit. The PostgreSQL
listener/database and test resources were cleaned up. Therefore no live ICON API
or current healthy runtime exists after the run; **current operational health
and API availability are unknown**.

## Acceptance matrix

| Acceptance area | Result | Independent assessment |
| --- | --- | --- |
| AOI | **PASS** | ADR-012 and `docs/everest-aoi.md` approve WGS 84 center `27.98806,86.92528`, default 100 km scope, and the explicit `everest-south-route-v1.0-expanded-2000km` exception. The retained sample records AOI ID/version/scope and selects an Everest native point within that approved expansion. DWD exposes independent global variable objects on this route; the six selected field objects are the smallest official objects available rather than a prohibited monolithic global dataset download. |
| Official DWD provider/product basis | **PASS** | Current official DWD NWP documentation identifies global ICON, native triangular/icosahedral grid, 13 km resolution, GRIB2 output, and 00/06/12/18 UTC runs. DWD's official Open Data page confirms free Open Data access and warns that availability is not guaranteed. DWD's legal notice permits reuse of open spatial data under CC BY 4.0 with attribution; CC BY 4.0 permits commercial reuse subject to its terms. The retained sidecar contains exact official `opendata.dwd.de/weather/nwp/icon/grib/00/...` URLs for `T_2M`, `U_10M`, `V_10M`, `HSURF`, `CLAT`, and `CLON`. No credential, numerical rate-limit, or present-availability claim is invented. |
| Approved-root artifact integrity | **PASS — independently rerun** | Under `D:\Everest-data\raw`, the payload exists at the content-addressed approved path, is `17,624,861` bytes, and rehashes to `e7e0d78b06bd4fba66a40ef15331df8678732f032e2f20e376a7f97637b95d57`. Canonical `metadata.json` is `1,392` bytes and rehashes to `cbe1f4aef4a7d5b4a727d8d55cb9d972e75f5fec94dca328bab1e8053f64ecdf`. Its 65-byte sidecar rehashes to `0a363bcd8d2f83827fab7fe14906147b4a1389470624c09440e0ba55661d4a46` and declares the matching metadata digest. All three resolved beneath the approved root; canonical JSON and recorded source/model/AOI/cycle/lead/valid/retrieval/field/URL facts were independently checked. |
| Connector/parser/normalizer/QC | **PASS** | Connector tests cover official URL construction, selected-object retrieval, bounded injected retry/backoff, external-root fail-closed behavior, containment, payload/metadata/sidecar tamper and missing-file rejection, canonical metadata, and malformed compression/GRIB failure. Real retained evidence records six ecCodes messages (`2t`, `10u`, `10v`, `HSURF`, `tlat`, `tlon`), explicit-unit normalization, native-grid selection, null precipitation/visibility, and additive `[missing_value]` QC without fabrication or destructive deletion. |
| Canonical semantics | **PASS** | Focused tests prove UTC cycle/lead/valid-time identity, explicit `K -> C`, wind m/s and true-north direction, `HSURF` metres, invalid-unit no-guessing, calm/missing behavior, source `dwd-icon`, model `ICON`, forecast identity, additive QC, and native key `icon:<uuid>:<index>`. |
| Shared adapter | **PASS** | `services/weather/icon/ingestion.py` depends on the owner-neutral `weather_ingestion_contract` and local meteorology contract, not FastAPI, SQLAlchemy, `apps.api`, or `everest_api`. Primitive projection, lossless canonical forwarding, and the full pre-port provenance rejection matrix are deterministic. The checked-in backend integration test composes the real adapter with `WeatherIngestionService`; no fake persistence port substitutes for the accepted DBRE path. |
| Retention migrations `0001`–`0006` | **PASS** | The revision chain is contiguous. `0001` creates registry persistence; `0002` creates raw/canonical weather storage and append-only constraints; `0003` adds record provenance association; `0004` adds retention classification/hold/disposition/audit; `0005` separates corrected table-specific immutable/transition triggers and scalar audit validation; `0006` fixes PostgreSQL JSON comparison while preserving downgrade reviewability. Final DBRE ran the complete chain on PostgreSQL, not SQLite. |
| Final DBRE | **PASS — supplied final report evidence** | Disposable PostgreSQL used pinned non-standard localhost port **53112**. The final suite reported **49 passed, no skips**; the focused checked-in ICON composition result was **2 passed**. Successful ingestion produced exactly **raw=1, record=1, audit=1**, and only after canonical commit changed ICON to `verified`/`healthy`. This supersedes the earlier 44-pass/port-64035 backend-only Gate-C record for final Phase E acceptance. QA did not rerun PostgreSQL because no live `EVEREST_TEST_DATABASE_URL` was supplied in this final review. |
| API serializer and privacy | **PASS** | The persisted forecast query returned HTTP 200 with one ICON record and the native spatial key `icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. Serializer and integration assertions expose canonical fields only and reject leakage of approved-root paths, DWD URLs, payload hashes, metadata, retention, hold, and audit facts. Routes query persistence and do not invoke DWD or parser code. |
| Negative raw-first path | **PASS** | The checked-in negative composition test forces canonical constraint failure after raw acceptance. It asserts raw `1`, canonical record `0`, retained classified raw evidence, and source lifecycle/health remaining `configured`/`unknown`; there is no false escalation. This is the required retry-independent raw-first failure behavior. |
| Cleanup and claim discipline | **PASS** | The DBRE report records listener/database/test-resource cleanup. Historical successful status/health is accepted as a committed database fact, not as a current service-health claim. Current ICON runtime health and API availability are `unknown`. The approved-root artifact remains retained under policy; DB cleanup is not raw disposition. |

## Independently executed non-DB checks

| Exact check | Result |
| --- | --- |
| `PYTHONPATH=D:\Everest;D:\Everest\apps\api; python -m pytest -q` | **PASS with declared environmental skips:** `117 passed, 16 skipped in 2.18s`. Skips are unavailable PostgreSQL/real-data environment cases and are not substituted for the supplied final DBRE. |
| `PYTHONPATH=D:\Everest; python -m pytest -q services/weather/tests/test_icon.py services/weather/tests/test_icon_ingestion.py` | **PASS:** `44 passed`; repeated **10 independent times**, all `44 passed`, no retry/pass-on-retry and no hard sleep. |
| Migration contract + API serializer + ICON integration discovery | **PASS/SKIP as expected locally:** `8 passed, 2 skipped`; only the two ICON PostgreSQL composition cases skipped because `EVEREST_TEST_DATABASE_URL` was unset. The same two cases are the supplied DBRE's focused `2 passed`. |
| Aggregate Black check | **PASS:** `62 files would be left unchanged`. |
| Weather Pylint | **PASS:** `10.00/10`. |
| API/tests/migrations Pylint | **PASS:** `10.00/10`. |
| Aggregate compileall | **PASS:** exit 0. |
| Approved-root payload/metadata/sidecar rehash and containment script | **PASS:** sizes and all three SHA-256 values matched the retained record; canonical metadata and root containment matched. |

No network retrieval, raw mutation, database mutation, status mutation, or
business-code change was performed by this QA assignment.

## Official documentation consulted

- DWD Open Data Server service page:
  `https://www.dwd.de/EN/ourservices/opendata/opendata.html`
- DWD NWP forecast data / global ICON description:
  `https://www.dwd.de/EN/ourservices/nwp_forecast_data/nwp_forecast_data.html`
- DWD legal notice and CC BY 4.0 reuse terms:
  `https://www.dwd.de/EN/service/legal_notice/legal_notice_node.html`
- Official product root recorded by the retained sidecar:
  `https://opendata.dwd.de/weather/nwp/icon/grib/`

## Final handoff

**Phase E: ACCEPTED. Gate C-Core: PASS.** The former Phase F authorization in
this historical handoff is **superseded** by the
[authoritative current-status banner](#authoritative-current-status--ev-data-001-e-qa-handoff-clean).
Phase F AIFS remains pending final code-review closure and is not authorized to
begin while review blockers remain.

Gate C-Operational remains **OPEN** and production-only. This handoff makes no
IAM/ACL, legal authority, WORM/privileged-immutability, Git exclusion/history,
live endpoint, current API, or current healthy-runtime claim. Before Phase F
downstream work relies on lifecycle wording, the manager and domain owners must
update their handoffs to reflect this exact historical-acceptance/current-
unknown distinction without changing the meaning of canonical weather fields.

---

# EV-DATA-001-E-QA-FINAL-2 — Final Full-Pipeline DBRE Re-evaluation

**Assignment ID:** `EV-DATA-001-E-QA-FINAL-2`  
**Review date:** 2026-08-21  
**Scope:** Independent review of the final full-pipeline ICON DBRE evidence and
current code fixes against the latest `AGENTS.md` and ADR-013. QA changed no
business code, tests, migrations, raw artifacts, registry state, or non-QA
handoff. This QA plan is the only modified file.

## Findings first

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| E-QA-FINAL-2-001 | Low | The prior failed API acceptance had one root-cause signature: `spatial_key` was omitted from the shared public serializer. The final evidence records two occurrences, the corrected allow-list, and regression coverage. | **Closed by current fix and final DBRE.** The occurrence history is retained; it is below the three-occurrence escalation threshold. |
| E-QA-FINAL-2-002 | Informational | Local non-DB execution cannot reproduce the full WSL ecCodes/PostgreSQL pipeline: the local Windows run skips the retained-real-data ecCodes case and PostgreSQL cases because the native library and `EVEREST_TEST_DATABASE_URL` are unavailable. | **Not a Phase E failure.** The supplied final DBRE is the authoritative full-pipeline evidence; local checks are reported transparently and are not represented as DB/API execution. |
| E-QA-FINAL-2-003 | Informational | Historical raw-root counts were unchanged after DBRE cleanup. Database/container/listener cleanup did not delete or shorten the retained approved-root artifact. | **PASS.** Current health remains unknown after teardown. |

**No blocking finding remains for Phase E Gate C-Core.** The final report covers
the previously missing real-data-to-parser-to-normalizer-to-QC-to-adapter-to-
PostgreSQL-to-API chain. Gate C-Operational controls are intentionally not
claimed here.

## Verdict and closure decision

**PASS — Phase E DWD ICON is closed and accepted at Gate C-Core.** Phase F
ECMWF AIFS has satisfied the Phase E QA/source-sequencing prerequisite, but its
authorization is **pending final code-review closure**. It is not authorized to
begin while review blockers remain; see the
[authoritative current-status banner](#authoritative-current-status--ev-data-001-e-qa-handoff-clean).

This acceptance uses ADR-013's split-gate decision. Gate C-Core is the source
acceptance gate and is satisfied by the final approved-root, real-data,
PostgreSQL, API, test, documentation, review, and truthful-lifecycle evidence.

**Gate C-Operational remains OPEN as a production/shared-deployment blocker
only.** No claim is made for named IAM/ACL identities, least privilege,
deployment-enforced legal authority, WORM or equivalent privileged-write
resistance, complete production audit controls, or Git exclusion/history. Those
controls remain required before shared or production deployment, automatic
disposition, or production-grade retention-governance claims. Gate
C-Operational does not itself block Phase F; the separate final code-review
closure requirement does, as recorded in the authoritative current-status
banner.

The in-run `verified`/`healthy` values are historical disposable database facts
set only after canonical commit. The database, container/volume, listener, and
port were cleaned up, so current ICON health and API availability are
**unknown**, not healthy or live.

## Final full-pipeline evidence assessment

| Acceptance area | Result | Evidence reviewed |
| --- | --- | --- |
| Official source and AOI | **PASS** | The retained six-object set uses official DWD Open Data ICON global GRIB2 products, with WSL ecCodes `2.47.1`, DWD source URLs, model/cycle/lead/valid-time metadata, and the approved Everest AOI ID/version/scope. The native selected point is represented by DWD UUID/index spatial identity, not an invented rounded-coordinate key. |
| Real retained parser/normalizer/conversion | **PASS** | The final real-data case reads the retained six-message artifact and verifies six actual messages: `2t`, `10u`, `10v`, `HSURF`, `tlat`, and `tlon`, each with the expected native value count. It asserts the Everest selected index `818403`, native coordinate, `HSURF` metres, `T_2M` Kelvin-to-Celsius conversion, wind vector conversion to m/s/degrees, null precipitation/visibility, and additive `[missing_value]` QC. |
| Connector-output integrity boundary | **PASS** | Current code re-reads and verifies payload, canonical metadata, and `metadata.json.sha256` before adapter composition; it validates size, SHA-256, source/model, URL set, fields, cycle, lead, valid time, and AOI provenance. Mismatch or missing-artifact cases fail before the backend port. |
| Owner-neutral shared adapter | **PASS** | The real ICON adapter forwards scalar projected metadata and canonical records through `weather_ingestion_contract`, preserves the native `spatial_key`, and rejects provenance mismatches before port invocation. It has no backend-framework, HTTP, ecCodes, or provider-type dependency through the shared boundary. |
| PostgreSQL and migrations | **PASS** | Pinned PostgreSQL executed migrations `20260821_0001` through `20260821_0006` with no revision gap. The final full `apps/api` result was **53 passed, 0 failed, 0 skipped**; the focused ICON composition result was **2 passed**. This is the final full-pipeline evidence, not SQLite or static migration inspection. |
| Positive persistence and lifecycle | **PASS** | Real retained ICON data passed parser, normalizer, conversion, adapter, and DB persistence. Counts were exactly `raw=1`, `record=1`, `audit=1`. Lifecycle changed from `configured`/`unknown` to `verified`/`healthy` only after the canonical transaction committed. |
| Queryable API and serializer | **PASS** | The persisted forecast endpoint returned HTTP 200 and exactly one ICON record. The public response includes the canonical native key `icon:a27b8de618c411e4820ab5b098c6a5c0:818403`. It leaks no raw path, provider URL, payload checksum, raw metadata, retention, hold, disposition, or audit field. |
| Synthetic negative raw-first path | **PASS** | Canonical persistence was deliberately failed after raw acceptance. The final evidence retained one classified raw row, inserted zero canonical rows, and left lifecycle/health at `configured`/`unknown`; no false escalation occurred. |
| Regression safety | **PASS** | GFS/IFS regressions remained green in the final full backend run. The serializer fix preserves existing current/forecast/profile response behavior while adding the required public native `spatial_key`; the previous two occurrences remain documented. |
| Cleanup and retained-root counts | **PASS** | Disposable PostgreSQL resources, container/volume, listener, and port were removed. Historical approved-root counts remained unchanged; teardown did not delete, move, rewrite, or shorten the retained ICON payload or sidecars. |

## Available non-DB checks executed for this re-evaluation

| Exact command/check | Result | Limitation |
| --- | --- | --- |
| `PYTHONPATH=D:\Everest;D:\Everest\apps\api; python -m pytest -q` | **PASS with environmental skips:** `142 passed, 16 skipped`. | Local Windows environment lacks the final WSL ecCodes/PostgreSQL prerequisites; skips were not substituted for the supplied DBRE. |
| `PYTHONPATH=D:\Everest; python -m pytest -q services/weather/tests/test_icon.py services/weather/tests/test_icon_ingestion.py` | **PASS:** `65 passed`. | Deterministic provider/adapter tests only; no DB or external retrieval. |
| Migration contract/API/ICON integration discovery | **PASS with expected local skips:** `8 passed, 2 skipped`. | One retained-real-data case skipped because native ecCodes is unavailable; one PostgreSQL case skipped because `EVEREST_TEST_DATABASE_URL` is unset. |
| Aggregate Black check | **PASS:** `62 files would be left unchanged`. | None. |
| Weather Pylint | **PASS:** `10.00/10`. | None. |
| API/tests/migrations Pylint | **PASS:** `10.00/10`. | None. |
| Aggregate `compileall` | **PASS:** exit 0. | None. |
| Approved-root integrity and containment check | **PASS.** | Payload `17,624,861` bytes; metadata `1,392` bytes; sidecar `65` bytes; all recorded hashes and declared metadata digest matched; all resolved beneath `D:\Everest-data\raw`. |

No network retrieval, database mutation, raw mutation, lifecycle mutation, or
business-code change was performed by this QA re-evaluation.

## Final handoff

**Phase E DWD ICON: CLOSED / ACCEPTED. Gate C-Core: PASS. Phase F ECMWF AIFS:
PENDING FINAL CODE-REVIEW CLOSURE.** Phase F is not authorized to begin while
review blockers remain.

**Gate C-Operational: OPEN, production-only blocker.** Current ICON health and
API availability remain `unknown` after cleanup. No IAM/ACL, WORM, legal,
production audit, Git, live endpoint, or production-health claim is made.

---

# Historical — EV-DATA-001-F-QA-CLOSE-RETRY

> **Superseded:** This record predates the amended `AGENTS.md` delivery
> boundary. Its AIFS source/core evidence remains accepted, but its frontend
> blocker, report-failure verdict, required UI evidence, and not-closed
> conclusion are superseded by `EV-DATA-001-F-QA-STOP` below.

**Review date:** 2026-08-22  
**Scope:** Independent QA of the final hardened ECMWF AIFS implementation
against the latest `AGENTS.md`. QA changed no business code, tests, raw
artifacts, databases, APIs, or runtime state; this document is the only file
changed. No external/raw/database rerun was performed. The supplied evidence
was reviewed as evidence, not silently upgraded to a current operational
claim.

## Findings first

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| F-QA-CLOSE-001 | **High** | The latest `AGENTS.md` says the current delivery stops only after all four forecast sources have real retrieval, parsing, normalization, QC, persistence, queryable API results, tests, docs, health status, **and frontend display**. AIFS frontend display evidence is absent, and no frontend/browser check was supplied. | **FAIL / blocking delivery close.** Frontend owner must provide display implementation and evidence through the backend service/API path; frontend must not call ECMWF directly. |
| F-QA-CLOSE-002 | **High** | AIFS core/source evidence is complete, but the required Phase-F report is not present as a single authoritative QA closure record containing every required field: successful/failed source result, exact official URL, format, update frequency, download size, database tables, APIs, tests/failures, licensing, current latency, Everest coverage, and next-stage recommendation. The retained handoff contains most source facts but does not by itself prove the report/stop-gate deliverable. | **FAIL / blocking delivery close.** Manager must publish the Phase-F report and reconcile its status with this QA handoff. |
| F-QA-CLOSE-003 | **Medium** | Current migrations/cleanup/current health are not newly rerun in this retry, by instruction. Historical evidence reports raw=1/record=1/audit=1, successful commit, cleanup, and historical `verified`/`healthy`; current health/API availability therefore remain `unknown`. | **PASS with boundary.** Do not claim a live service or current healthy source. |
| F-QA-CLOSE-004 | **Informational** | The corrected direct-argv procedure is accepted after the nested-wrapper incident. The historical wrapper logs/timestamps are unrecoverable; the accepted decision explicitly does not claim full escalation compliance. The corrected AIFS run is distinct and is not a fourth prohibited-wrapper attempt. | **Accepted limitation.** No new wrapper attempt was made. |
| F-QA-CLOSE-005 | **Informational** | Docker lifecycle evidence is accepted as historical cleanup evidence: RC2. Fixture evidence is accepted as RC1. These are not current runtime-health evidence. | **PASS with boundary.** |

## Supplied evidence assessment

| Acceptance area | Result | QA assessment |
| --- | --- | --- |
| Full API regression | **PASS** | `apps/api`: **66 passed, 0 failed, 0 skipped**. |
| Focused AIFS API/DB evidence | **PASS** | Explicit AIFS result: **4 passed**; historical pinned PostgreSQL used port **46901**. No DB rerun performed. |
| Meteorology AIFS coverage | **PASS** | AIFS suite: **37 passed**; WSL ecCodes **2.47.1**. |
| Real retained artifact | **PASS** | Exact integrity retained and accepted; decoded inventory, native levels, process `5`, and provenance were reviewed. |
| Retry behavior | **PASS** | HTTP `429` and `Retry-After` handling are covered, with deterministic retry evidence. |
| Canonical/API identity | **PASS** | UTC API evidence returned HTTP `200`, `model=AIFS`, never IFS; negative conflation/raw-first and regressions passed; no provenance leak was reported. |
| Persistence/audit | **PASS — historical execution** | Counts were exactly `raw=1`, `record=1`, `audit=1`; lifecycle became `verified`/`healthy` only after commit. |
| Cleanup and current health | **PASS with boundary** | Historical cleanup evidence is accepted. Current migrations, cleanup, and health were not rerun; current health/API remain **unknown**. |
| Frontend display | **NOT EVIDENCED** | This is the blocking gap under the latest `AGENTS.md`; no browser or frontend display proof is claimed. |

## Final QA decision

**AIFS Phase-F source/core: PASS.** The evidence satisfies the AIFS source
acceptance chain through real retained data, decoding, normalization/QC,
owner-neutral provenance, persistence, API queryability, negative-path
protection, tests, and documentation. `model=AIFS` is preserved and is not
conflated with IFS.

**Phase-F report and mandatory delivery stop: FAIL / NOT CLOSED.** The
frontend-display requirement is not evidenced, and the required consolidated
Phase-F report is not yet an authoritative closure artifact. Therefore this QA
assignment must not declare the delivery complete or authorize work beyond the
specified A-F boundary. No AWS, Pyramid, satellite, terrain, environmental,
OSM, AI, or Risk work is authorized by this record.

**Gate C-Operational remains OPEN and production-only.** This QA decision does
not require or imply a production rerun. IAM/ACL, legal/WORM, production audit,
Git exclusion/history, continuous runtime health, and production deployment
claims remain outside the accepted core evidence.

## Required close-out evidence

1. Frontend owner demonstrates AIFS data rendered from the service/API path,
   with no external-source call from the frontend, and records deterministic
   UI/API test evidence.
2. Everest Manager publishes the Phase-F report with the exact official URL,
   GRIB2 format, update frequency, retained download size, database tables,
   API endpoints, test count/failures, licence findings, measured latency,
   Everest coordinate/time, parsed variable count, source outcome, and next
   stage recommendation.
3. Reconcile `docs/data-sources.md`, `docs/management/board.md`, and this QA
   handoff so historical `verified`/`healthy` and current `unknown` are not
   mixed. Do not rerun external/raw/database work merely to satisfy this
   documentation close unless separately authorized.

---

# EV-DATA-001-F-QA-STOP — Amended Phase-F Stop Gate

**Assignment ID:** `EV-DATA-001-F-QA-STOP`  
**Review date:** 2026-08-22  
**Classification:** QA / final A-F acceptance  
**Scope:** Documentation-only re-evaluation of complete Phase F and the A-F
stop gate under amended `AGENTS.md`. QA updated only
`docs/qa/test-plan.md`. No test, external request, raw-artifact operation,
database, API, migration, scheduler, health check, or runtime operation was
performed. All execution results below are retained evidence, not a new run.

## Findings first

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| F-QA-STOP-001 | **Critical** | The previous QA close treated frontend display as a mandatory Phase-F stop condition. Amended `AGENTS.md` now explicitly defers frontend display to a separately authorized delivery while retaining the prohibition on new UI. | **Closed.** Frontend absence is not a stop-gate defect. No UI is authorized or required by this QA decision. |
| F-QA-STOP-002 | **High** | The authoritative hardened AIFS evidence supersedes older `61/61`, focused `3/3`, and port `44859` records: `DBRE66` = **66 passed, 0 failed, 0 skipped** for `apps/api`; `AIFS4` = **4 passed, 0 failed, 0 skipped**; `met37` = **37 passed, 0 failed, 0 skipped**; pinned disposable PostgreSQL port `46901`; migrations `0001`–`0006`; committed `raw=1`, `record=1`, `audit=1`; historical HTTP `200` with `model=AIFS`. | **PASS.** This is the controlling AIFS source/core and database/API evidence. No rerun was required or performed. |
| F-QA-STOP-003 | **High** | The published Phase-F report predates hardened AIFS correction and contains superseded AIFS counts/status and a frontend blocker. Later authoritative source, meteorology, API, QA, board, and manager correction records supply the final correction without changing the underlying report file in this QA-only assignment. | **PASS after correction overlay.** Validate the report only as `docs/management/phase-f-report.md` plus the authoritative hardened correction summarized in this record. Its `61/61`, `3/3`, port `44859`, absent-independent-QA, AIFS-not-persisted, and frontend-blocking statements are not valid final conclusions. |
| F-QA-STOP-004 | **High** | IFS, GFS, ICON, and AIFS each have accepted historical disposable evidence for official retrieval, real parsing, canonical normalization/QC, persistence, queryable backend API, tests, documentation, and review. | **PASS.** The complete A-F source/core chain reaches the amended backend delivery boundary. |
| F-QA-STOP-005 | **Medium** | Every disposable acceptance runtime was torn down. Historical in-run `verified`/`healthy` facts do not establish a currently deployed source, database, API, scheduler, or health monitor. | **Accepted boundary.** Current health and API availability are **`unknown` for all four sources**. No current latency or production-health claim is made. |
| F-QA-STOP-006 | **Medium** | Gate C-Operational controls remain unevidenced for shared/production deployment. | **Open, production-only.** This does not fail the A-F source/core stop gate, but it blocks production/shared deployment and production-grade retention claims. |
| F-QA-STOP-007 | **Medium** | The three-event PowerShell/WSL nested-wrapper incident lacks recoverable per-occurrence timestamps, complete logs, versions, serialized commands, Linux argv, and exit codes. | **Accepted residual limitation.** The event counter remains `3`; full historical escalation compliance is not claimed. No fourth prohibited-wrapper attempt occurred. Future runs must use the manager-accepted direct-argument/reviewed-script procedure and capture the prescribed evidence. |

## Evidence basis and official-documentation check

QA reviewed the amended project authority and the current domain handoffs:

- `AGENTS.md`;
- `docs/data-sources.md`, including the authoritative hardened AIFS closure;
- `docs/meteorology/weather-spec.md`;
- `docs/api/API.md`;
- `docs/management/phase-f-report.md` together with its later correction
  records in `docs/management/decisions.md` and `docs/management/board.md`;
- the prior Phase A-F acceptance records retained in this test plan.

The mandatory official-documentation check was refreshed without accessing
provider data. ECMWF's current official Open Data catalogue confirms that IFS
and AIFS Open Data are public GRIB2 products, AIFS has four daily
00/06/12/18 UTC runs with 6-hour steps through 360 hours, and portal access is
limited to 500 simultaneous connections. The current official dissemination
schedule identifies deterministic AIFS as Set IX with `class=ai`,
`stream=oper`. ECMWF's current terms confirm CC BY 4.0 and commercial reuse
subject to attribution and the ECMWF terms. Sources consulted:

- <https://www.ecmwf.int/en/forecasts/datasets/open-data>
- <https://confluence.ecmwf.int/display/DAC/Dissemination+schedule>
- <https://apps.ecmwf.int/datasets/licences/general/>

This documentation check corroborates provider/product/licensing context only;
it is not a new real-data verification, endpoint-health check, or legal approval
for production deployment. Existing accepted official NOAA and DWD evidence is
retained; no external source or data object was called.

## All-four-source acceptance matrix

| Source | Retained real-source evidence | Persistence and query evidence | Final QA interpretation |
| --- | --- | --- | --- |
| ECMWF IFS (`ecmwf-ifs`) | Official ECMWF Open Data selected ranges; five GRIB2 messages (`z`, `tp`, `10u`, `10v`, `2t`); Everest request `27.9881, 86.9250`; valid time `2026-08-20T03:00:00Z`; normalization/QC and immutable provenance accepted. | Historical disposable PostgreSQL persisted two raw artifacts, one canonical record, and one static-altitude association. Bounded forecast request returned HTTP `200` with one record. Phase C QA passed. | **PASS — historical disposable `verified`; current health/API `unknown`.** |
| NOAA GFS (`noaa-gfs`) | Official NOAA/NCEP NOMADS `.idx` plus strict HTTP-206 selected retrieval; four GRIB2 messages (`orog`, `2t`, `10u`, `10v`); Everest request `27.9881, 86.9250`; valid time `2026-08-20T00:00:00Z`; normalization/QC and retained integrity accepted. | Checked-in adapter persisted `raw=1`, `record=1` in disposable PostgreSQL; bounded forecast query returned HTTP `200` with one record. Phase D QA passed. | **PASS — historical disposable `verified`; current health/API `unknown`.** |
| DWD ICON (`dwd-icon`) | Six official DWD Open Data bzip2-compressed GRIB2 objects; six decoded messages (`2t`, `10u`, `10v`, `HSURF`, `tlat`, `tlon`); Everest-area native point `(27.926742553710938, 86.921875)`; valid time `2026-08-21T00:00:00Z`; normalization/QC and approved-root retention accepted. | Authoritative post-review run: `58 passed, 0 failed, 0 skipped`; focused ICON `2 passed`; migrations `0001`–`0006`; `raw=1`, `record=1`, `audit=1`; HTTP `200` with one record and native `spatial_key`. Gate C-Core and Phase E QA passed. | **PASS — historical disposable `verified` after commit; current health/API `unknown`.** |
| ECMWF AIFS (`ecmwf-aifs`) | Official ECMWF `aifs-single/0p25/oper` selected ranges; immutable `3,061,386`-byte artifact; exactly five messages (`z`, `10u`, `10v`, `2t`, `tp`) at authoritative native levels; every message process ID `5`; provider cell `(28.0, 87.0)`; valid time `2026-08-21T00:00:00Z`; normalization/QC and AIFS-versus-IFS separation accepted. | Authoritative hardened `DBRE66`/`AIFS4`/`met37`; migrations `0001`–`0006`; `raw=1`, `record=1`, `audit=1`; historical HTTP `200`, `source=ecmwf-aifs`, `model=AIFS`, no raw/private leak. | **PASS — source/core accepted; historical disposable `verified`/`healthy` after commit; documented registry remains `connected`; current health/API `unknown`.** |

No forecast source failed the final authorized chain. Historical unsuccessful
alternative attempts—GFS filter HTTP `500`, ICON exact-object HTTP `404`, AIFS
6-hour missing surface `z`, and the nested-wrapper incident—remain preserved
failure evidence but are superseded as final source outcomes by accepted runs.

## Corrected Phase-F report validation

**Report verdict: PASS AFTER AUTHORITATIVE CORRECTION.** The report provides the
required four-source outcomes, exact official data URLs, formats, update
frequencies, retained/download sizes, database tables, API inventory, test
evidence, licensing findings, latency boundary, Everest-area coordinates,
actual UTC valid times, parsed-variable counts, and next-stage recommendation.
For final interpretation, apply these corrections:

1. AIFS source/core is accepted on `DBRE66`, `AIFS4`, and `met37`, all with
   zero failures and zero skips; old `61/61` and `3/3` results are historical.
2. The authoritative disposable PostgreSQL port is `46901`, not `44859`, with
   migrations `0001` through `0006` and exact committed counts
   `raw=1`, `record=1`, `audit=1`.
3. The historical bounded API result is HTTP `200`, preserves
   `source=ecmwf-aifs` and `model=AIFS`, and excludes raw/private provenance.
4. AIFS was historically `verified`/`healthy` only after canonical commit;
   its documented current registry remains `connected`, and current health/API
   availability remain `unknown` after teardown.
5. Independent Phase-F QA is now present in this record.
6. Frontend display is deferred by amended `AGENTS.md`; it is not a stop gate.
   The no-new-UI prohibition remains unchanged.

The report's current-latency value remains correctly **unknown/unavailable**;
test duration is not substituted for operational latency. The accepted report
does not claim a live service, current source health, production readiness, or
Gate C-Operational closure.

## Incident residual limitation and accepted procedure

`EV-DATA-001-F-INCIDENT-001` remains open only as a historical compliance
limitation, not as an AIFS product failure. Three invocations shared one root
cause: a structured argument vector was encoded into an inline nested shell
string and reparsed across PowerShell, `wsl.exe`, and Bash. Complete records for
those events cannot be reconstructed, and successful correction does not reset
the occurrence count.

The Everest Manager-accepted procedure remains mandatory for any future run:

1. Never use PowerShell -> `wsl.exe` -> inline `bash -c`/`bash -lc` for this
   signature.
2. Pass every Linux executable argument separately through `wsl.exe`, or use a
   reviewed script file with its path and parameters passed separately.
3. Before execution, capture PowerShell version,
   `$PSNativeCommandArgumentPassing`, WSL version/distribution, UTC start,
   correlation ID, and a redacted argument manifest.
4. Capture stdout, stderr, native and child exit codes, UTC end, expected
   evidence, and cleanup result. Missing or ambiguous evidence is failure.
5. Clean up only run-owned wrapper files and disposable test resources; never
   modify/delete retained raw artifacts or alter product configuration as
   wrapper cleanup.

The hardened AIFS run used the accepted corrected procedure and did not repeat
the prohibited wrapper. This acceptance does not claim the missing historical
incident evidence exists or that full escalation compliance was achieved.

## Exact unresolved production and future items

These items do **not** fail the amended A-F source/core stop gate, but they
remain unresolved and must not be implied complete.

### Production-only — Gate C-Operational remains open

1. **IAM/ACL:** named connector-write and operator-read identities,
   least-privilege OS/object-store permissions, unauthorized read/write denial,
   and grant/change/revocation evidence.
2. **Legal hold, disposition, and WORM:** deployment-enforced hold/release and
   disposition authority, fail-closed ambiguous-hold behavior, and WORM or an
   approved equivalent resistant to privileged modification.
3. **Production audit and retention enforcement:** complete event coverage,
   audit access controls, production retention enforcement, and controlled
   disposition evidence.
4. **Git-bearing proof:** authoritative evidence that raw payloads, metadata,
   and checksum sidecars are excluded and untracked. This workspace is not a
   Git checkout.
5. **Legacy raw disposition:** project-root `tmp-icon*` and `tmp-gfs*`
   artifacts remain noncompliant and untouched; disposition requires separate
   authorization.
6. **Deployed operation:** no current database, API, connector schedule,
   freshness monitor, health monitor, availability SLO, or measured production
   latency is evidenced. Health/API availability are `unknown` for all four
   sources.
7. **Deployment legal/commercial review:** ECMWF source terms permit commercial
   reuse subject to attribution/terms but do not constitute Everest deployment
   approval; NOAA product-specific commercial confirmation remains pending;
   DWD deployment policy review remains pending.

### Separately authorized future delivery only

1. **Frontend display:** deferred, not implemented, and not a stop gate. The
   no-new-UI rule remains; a future UI requires explicit authorization and may
   consume only Everest REST/WS services, never external providers directly.
2. **AIFS non-zero-step altitude:** the observed 6-hour index lacked one unique
   surface `z`. Any future solution requires a separately reviewed same-AIFS,
   same-cycle auxiliary-artifact design; no value may be fabricated or borrowed
   from IFS.
3. **Current operational verification:** any future claim of live/current
   health, latency, scheduling, or production readiness requires a separately
   authorized production-only Gate C-Operational validation. Historical
   disposable evidence cannot supply that claim.

## Final QA decision

**PASS — EV-DATA-001 phases A-F meet the amended source/core stop gate.** The
corrected Phase-F report is accepted under the correction rules above. Frontend
display is explicitly deferred and is not a stop-gate criterion; no-new-UI
remains mandatory. Current health for all four sources is `unknown`, and Gate
C-Operational remains open as a production/shared-deployment gate only.

**The mandatory delivery stop has been reached. Delivery must stop now. No
Everest AWS, Pyramid, satellite, terrain, environmental, OpenStreetMap/OSM, AI,
or Risk work may begin without new explicit authorization and the required
governance sequence.**

---

# EV-DATA-001-ADR015-QA-REEVAL — Five-Route Historical HTTP Verdict

**Assignment ID:** `EV-DATA-001-ADR015-QA-REEVAL`  
**Review date:** 2026-08-22  
**Classification:** QA / retained-evidence re-evaluation  
**Scope:** Documentation-only review of the latest `AGENTS.md`, ADR-015,
the corrected Phase-F report, `docs/api/API.md` endpoint-evidence inventory,
`docs/management/board.md`, and `docs/management/decisions.md`.

No tests, database, API, provider, raw-data, service, or runtime operation was
performed. This record does not infer endpoint results from shared code, route
existence, serializer behavior, test discovery, direct database assertions, or
underlying persisted rows. It does not require UI, Gate C-Operational, camp
records, current latency, a running service, PRD/GIS/data-sources work, or
commercial-use confirmation.

## Exact verdict

**ADR-015 five-route historical real-persisted HTTP evidence: NOT PROVEN.**

The exact five-route criterion is not closed because only one route has
qualifying retained evidence. This is an evidence gap, not a claim that the
other route implementations fail. The historical source/core forecast evidence
for IFS, GFS, ICON, and AIFS remains accepted and unchanged.

## Route classification

| Required route | Classification | Evidence-based reason |
| --- | --- | --- |
| `GET /api/weather/current` | **NOT PROVEN — evidence gap** | Retained HTTP is fake-session only; no retained provider-backed HTTP invocation or response against persisted canonical data was found. |
| `GET /api/weather/forecast` | **PROVEN HISTORICALLY** | Retained evidence shows real provider bytes parsed, normalized, committed to disposable PostgreSQL, and queried over HTTP with `200`. This is historical disposable evidence, not current availability. |
| `GET /api/weather/profile` | **NOT PROVEN — evidence gap** | Retained HTTP is fake-session only; direct/synthetic database facts do not prove a real persisted HTTP response for this route. |
| `GET /api/weather/sources` | **NOT PROVEN — evidence gap** | Registry rows and lifecycle assertions exist, but no retained invocation, status, or response body for this exact route was found. |
| `GET /api/data-health` | **NOT PROVEN — evidence gap** | Direct health-row assertions exist, but no retained invocation, status, or response body for this exact route was found. |

The forecast classification preserves the strongest retained historical result
for all four forecast sources: IFS, GFS, ICON, and AIFS. The inventory records
strongest retained executable route evidence for ICON and AIFS, with historical
handoff statements for IFS and GFS. None of this is current API availability.

## Boundary and stop decision

- Current health and API availability remain **`unknown` after teardown**.
- Historical in-run `verified`/`healthy` values remain disposable-run facts and
  must not be promoted to current health.
- Fake-session HTTP, synthetic fixtures, direct database assertions, and route
  implementation are not substitutes for historical real-persisted HTTP
  evidence.
- No database or runtime rerun is allowed solely to close this documentation
  gap. No provider, raw-data, API, service, or test rerun was performed for
  this re-evaluation.
- UI/Gate C-Operational/camps/current latency/service/PRD/GIS/data-sources and
  commercial confirmation are explicitly outside this verdict and do not alter
  the route classifications.

**QA decision: NOT PROVEN for the exact five-route ADR-015 criterion; source/core
forecast evidence preserved; delivery remains stopped pending Manager decision.**

## Manager decision handoff

**To:** Everest Manager  
**Handoff:** `EV-DATA-001-ADR015-ENDPOINT-QA` /
`EV-DATA-001-ADR015-QA-REEVAL`

Manager action requested: acknowledge the exact result above, keep the A-F
delivery stop in force, and decide whether the remaining four route evidence
gaps are accepted as unresolved historical evidence or require a separately
authorized future evidence activity. Any future activity must not be treated as
authorized by this QA record and must follow the governance sequence. Until that
decision, do not claim ADR-015 five-route closure, current service availability,
or current health. Do not authorize a database rerun solely for documentation.

## EV-GATEC-OP-RETENTION-002-OFFLINE — B2 QA skeleton

**Prepared:** 2026-08-24  
**Status:** Offline review remediation complete on 2026-08-25; independent
review pending. Local author evidence is recorded below and is not AWS,
PostgreSQL, runtime, WORM, legal-hold, disposition, provisioning, canary, or
current-health evidence. The production canary remains disabled; B3 is closed.

### Offline foundation review

- [x] Parse every JSON policy/resource/state contract.
- [x] Run `python validate_assets.py` and focused pytest from
      `infra/aws/gate-c-operational/retention/` without network/AWS access.
      **PASS (2026-08-25 remediation rerun)** — validator exits 0 with
      `Block-2 offline retention validation passed`; pytest reports **33 passed
      in 0.07s**.
- [x] Run Black, Pylint, and independent JSON parse. **PASS (2026-08-25
      remediation rerun)** — Black formatted 3 files, final `--check` leaves all
      3 unchanged; Pylint **10.00/10**; independent parse loaded **13 JSON
      files**. No compileall claim is made for this remediation rerun.
- [x] Mutations of account, Region, exact bucket names, retention mode/day,
      Governance provisioning flag, canary QA gate/count/size/enabled state,
      role names, Lifecycle absence, and KMS ARN fail closed.
- [x] Governance resource is ObjectLock-at-creation + Versioning Enabled +
      default Governance 180; audit resource is default Compliance 1,095.
- [x] Production canary is exact one synthetic object, <=1 KiB, Compliance 180,
      exact non-null version, disabled until Governance QA PASS.
- [x] Retention admin has only approved read/list/extend actions and no bypass,
      legal-hold mutation, delete, bucket lock, or Lifecycle mutation.
- [x] Legal authority is exact deny-only with null trust/human principal; hold
      executor is disabled with no legal-hold permission; disposition executor
      is disabled with no permission.
- [x] Audit read policy exposes retention metadata, not payload or mutation.
- [x] Writers are explicitly denied retention, hold, read, delete/version-delete,
      bypass, bucket lock, and Lifecycle mutation.
- [x] Bucket policy denies Governance bypass, unversioned delete, Lifecycle and
      bucket-lock mutation, and legal hold pending authority assignment.
- [x] Exact-version and KMS survival contracts reject delete markers, DB-only
      authority, key destruction as disposition, and missing version IDs.
- [x] Runbook identifies irreversible Compliance behavior, cost, roll-forward
      recovery, no raw/`tmp-*` use, stop conditions, and sanitized evidence.
- [x] Invalid `s3:GetObjectAttributes` was removed. Audit metadata access is
      exactly version listing, retention, legal hold, and approved bucket
      configuration reads; no payload access.
- [x] Legal/hold/disposition roles are absent. Broker/admin are uncreated until
      the exact Governance QA activation transition; no fake `enabled=false` or
      null IAM trust is treated as deployable inactivity.
- [x] Validator checks exact schemas, four BPA keys, ownership, KMS ARN,
      resources/principals/effects/actions, S3 allowlist, bucket-lock deny, and
      rejects unknown/missing fields. Mutation tests exercise these boundaries.
- [x] Governance QA rejects direct arbitrary dates and Compliance mode; broker
      calculates the approved date and executor is Governance-only.
- [x] Provisioning order requires Governance/180 readback before attaching the
      lock-mutation deny; Lifecycle remains absent.
- [x] Backend contract requires immutable `version_created_at` and
      `s3_last_modified`, including timing mutation/reconciliation tests.

### Future Governance provisioning and runtime matrix

These items are placeholders for separately authorized execution and must not
be checked from configuration presence alone:

- [ ] Sanitized readback proves exact account/Region/bucket, Object Lock enabled
      at creation, Versioning, default Governance 180, SSE-KMS/Bucket Key,
      ownership, Block Public Access, and no Lifecycle rule.
- [ ] Exact-version positive test proves default 180-day readback and approved
      extension to at least the later-of calculated 730-day date.
- [ ] Negative AWS authorization tests prove all writer, retention-admin, legal,
      hold, disposition, audit, no-version delete, bypass, and Lifecycle limits.
- [x] Additive PostgreSQL migration runs upgrade/downgrade on disposable
      PostgreSQL; no S3 identity is invented for legacy/local rows; append-only
      exact-version events and unique triple constraints pass. **DB-04
      implemented 2026-08-25** (migration `20260825_0008`, models
      `WeatherStorageVersionModel`/`WeatherStorageEventModel`, 6 PostgreSQL tests
      PASS, Pylint 10.00/10).
- [x] State-machine tests prove exact-version identity, readback-before-success,
      compare-and-set concurrency, idempotency, drift/KMS blocking, and disabled
      hold/disposition commands. **SVC-05 implemented 2026-08-25**
      (`everest_api/weather/storage.py`): 8 deterministic unit tests PASS
      covering identity rejection, uploaded→default_lock_verified_180d,
      failed_retained_180d, 730-day extension, drift blocking, KMS blocking, and
      typed disabled hold/disposition results; Pylint 10.00/10; no SDK/framework
      import in the module.
- [ ] Public API regression proves no bucket/key/version/KMS/retention leakage
      and no weather semantic change.
- [ ] Teardown preserves retained synthetic versions and their CMK dependency;
      current AWS/runtime health is stated only from contemporaneous readback.
- [ ] Independent Governance QA verdict is PASS before the Manager may authorize
      the irreversible production Compliance canary.

**Acceptance boundary:** Offline PASS may authorize review/provisioning planning
only. It cannot close B2, Gate C-Operational, or B1; cannot enable a role; and
cannot authorize legal hold, disposition, canary, B3, or release.

**Historical-state reconciliation blocker:** the 2026-08-25 provisioning record
in management decisions says five placeholder/disabled roles were created in
AWS. This offline remediation requires legal/hold/disposition roles absent and
broker/admin uncreated until activation. No AWS read or mutation was authorized,
so current cloud state is **unknown** and this mismatch must be independently
reviewed and reconciled before Governance QA. Offline tests do not prove role
absence in AWS.

---

# EV-GATEC-OP-ACL-001 — Block 1 Independent QA Re-Evaluation

**Review date:** 2026-08-25  
**Scope:** Independent re-evaluation of the Block 1 evidence package
(`docs/qa/EV-GATEC-OP-ACL-001-handoff.md`) against the recorded Block 1
controls. Read-only; no AWS mutation, no credential handling, no raw/data
operation.

## Verdict

**PASS — the previously failing Block 1 controls are remediated and evidenced.
Block 1 implementation evidence is accepted for the recorded nonproduction
scope.** This does not authorize production/shared deployment, writer-profile
enablement, Block 2, or release; those remain gated.

## Checks executed

| Check | Result |
| --- | --- |
| `validate_policies.py` (offline policy validator) | **PASS** — offline policy validation passed |
| `pytest infra/aws/gate-c-operational/acl/test_validate_policies.py` | **PASS** — 22 passed |
| `verify_operator_reads.py --execute` (operator, 9 read checks) | **PASS** — 9/9 exit 0 (caller identity, bucket location, versioning, object-lock, BPA, ownership, encryption, CMK describe, trust anchor) |
| Bucket Block Public Access (`get-public-access-block`) | **PASS** — all four controls `true` (previous FAIL remediated) |
| Bucket Versioning | **PASS** — `Enabled` |
| Object Lock | **PASS** — capability `Enabled` |
| Object Ownership | **PASS** — `BucketOwnerEnforced` |
| Default SSE-KMS encryption | **PASS** — CMK `3ea2b50b...`, Bucket Key enabled, SSE-C blocked |
| CMK metadata (`describe-key`) | **PASS** — `KeyManager=CUSTOMER`, `SYMMETRIC_DEFAULT`, `ENCRYPT_DECRYPT`, `Enabled`, single-Region |
| Roles Anywhere trust anchor | **PASS** — `ap-south-1`, enabled, `CERTIFICATE_BUNDLE`, name `zhufengxiangmu` |
| Caller identity | **PASS** — account `982408502231`, IAM user `everest-gatec-operator` |
| Git exclusion + secret scan (GATEC-CLOSE-003) | **PASS** — authoritative remote `Yizebaba/everest`; raw artifacts excluded; gitleaks 0 new leaks vs baseline |

## Superseded findings

The historical Block 1 QA FAIL was driven by (1) bucket Block Public Access
all-false, (2) KMS bootstrap-only policy, (3) absent roles/profiles/CRL/
analyzer, and (4) operator `AdministratorAccess`. The current AWS reads confirm
items 1 is fixed; items 2-4 are recorded as remediated in the handoff (final KMS
policy applied via no-lockout MFA-admin procedure, `/everest/` roles and four
disabled profiles created, CRL enabled, analyzer `EverestGateC` created with
empty findings, `AdministratorAccess` removed). This re-evaluation reproduces the
relevant read evidence with the least-privilege operator identity.

## Residual / open (not Block 1 failures)

- **CRL renewal** due 2026-10-31; reissue before expiry.
- **Writer certificate rotation** (30-day validity to 2026-09-23).
- **CreateSession pacing** — transient `AccessDenied` under rapid bursts is a
  documented AWS behavior, not a config defect.
- **Block 2 retention** remains closed; no Object Lock default/legal hold/
  disposition is in effect (correct for Block 1).
- Independent Governance QA verdict for the irreversible production Compliance
  canary remains a later gate.

## Boundary

This PASS is limited to Block 1 nonproduction evidence acceptance. It does not
enable writer profiles, does not open Block 2, does not authorize shared/
production deployment, and does not close Gate C-Operational. The board records
`EV-GATEC-OP-ACL-001` as QA-passed-for-recorded-scope with the residual register
carried forward.

---

# EV-UI-001-INTEGRATION-AUDIT-QA

**Review date:** 2026-08-25  
**Scope:** Read-only independent frontend/backend integration audit using
already collected runtime evidence, automated results, contracts, and source
inspection. No business code, tests, other documents, external sources,
database, raw/`tmp-*` artifacts, or processes were changed or operated.

## Verdict

**FAIL / NO-GO.** The current browser-to-API integration and frontend display
are not acceptance-ready.

## Current direct evidence

- A CORS preflight from origin `http://localhost:42420`, carrying
  `X-Correlation-ID`, received `OPTIONS` HTTP 405 with no CORS allowance.
- Weather API timestamps and forecast cycles were serialized with `+08:00`,
  while the frontend contract requires UTC `Z`.
- `/api/weather/current` and `/api/weather/forecast` each returned the same
  single old DWD ICON forecast record.
- `/api/weather/profile?profile=SUMMIT` returned HTTP 200 with no records.
- `/api/weather/sources` and `/api/data-health` returned a persisted DWD ICON
  `verified`/`healthy` fact. This is only the database/API value observed; it is
  not evidence of real current source health, freshness, or live ingestion.
- The frontend on port `42420` returned HTTP 500. A separate instance did not
  form valid evidence because shared `.next` state conflicted with concurrent
  dev/build activity; it also returned 500 and made no API request.

## Automated results

- Web tests: **21 passed**; ESLint: **passed**.
- With `NEXT_PUBLIC_EVEREST_API_BASE_URL` configured, web build and typecheck:
  **passed**. The build failed when that required environment value was absent.
- Focused backend weather API tests: **8 passed**.
- Full `apps/api` result: **50 passed, 22 skipped**.
- `services/weather/tests`: **111 passed**.

## Core findings

### Critical

1. **Browser API access is blocked by missing CORS support.** The custom
   correlation header triggers a preflight, and the observed HTTP 405 prevents
   the permitted frontend-to-Everest-API path.

### High

1. **No usable frontend runtime was evidenced.** Port `42420` returned HTTP
   500, and the attempted independent instance was invalidated by shared
   `.next` contention.
2. **The API wire format conflicts with frontend validation.** `+08:00`
   timestamps are not the required UTC `Z` values and will be rejected by the
   frontend record validator.
3. **Timeline-to-map data flow is inconsistent.** Forecast time selection is
   applied to records loaded from the current endpoint rather than to the
   forecast records that produced the timeline.
4. **Current data cannot support a four-forecast-source integration claim.**
   Only one old ICON weather record was observed; an empty Summit profile and
   persisted registry/health values do not establish current four-source data,
   freshness, or correct frontend rendering.
5. **Runtime validation remains too weak for the documented contract.** It does
   not fully enforce required provenance, ranges, nullable numeric types,
   forecast identity, or source/health response fields.

## Claim boundary

The accepted historical disposable A-F source/core evidence is unchanged by
this UI integration failure. It must remain classified as historical evidence.
The current environment does **not** support claims that all four forecast
sources are currently integrated, that persisted `healthy` is real current
source health, that frontend/backend behavior is consistent, or that the
frontend correctly displays API data.

## Minimum repair order

1. Start one isolated frontend runtime with an explicit API base URL and no
   shared `.next` contention; require an HTTP 200 page before integration QA.
2. Add least-privilege backend CORS for the approved frontend origin, `GET` /
   `OPTIONS`, and `X-Correlation-ID`, including response-header exposure and
   positive/negative tests.
3. Convert all public API datetimes to UTC before serializing them with `Z` and
   add wire-contract regressions.
4. Drive the map and timeline from one validated forecast data set; keep
   current data semantically separate.
5. Provide a controlled, non-fabricated four-source canonical/API fixture and
   truthful freshness states, then strengthen validators and rerun browser E2E.

---

# EV-GATEC-OP-RETENTION-002 — Block 2 Independent QA

**Review date:** 2026-08-25  
**Scope:** Independent re-evaluation of the B2 retention-002 evidence across
Stages 1-3 against `docs/architecture/EV-GATEC-OP-RETENTION-002-backend-contract.md`
and the B2 authorization. Read-only re-execution of tests and AWS reads; no new
provisioning, mutation, legal hold, disposition, or raw operation.

## Verdict

**PASS for the recorded B2 Stage-1 through Stage-3 scope.** Governance
provisioning, AWS retention behavior, DB-04 storage projection, and SVC-05
state machine are accepted for the nonproduction Governance bucket. This does
not enable writer profiles, open Block 3, authorize the production Compliance
canary, or permit legal hold / disposition / release.

## Evidence re-executed

| Area | Result |
| --- | --- |
| Offline validator `validate_assets.py` | **PASS** — offline retention validation passed |
| Offline pytest `test_validate_assets.py` | **PASS** — 24 passed |
| Governance bucket readback (versioning, object-lock GOVERNANCE/180, ownership, BPA, SSE-KMS, no lifecycle, empty) | **PASS** — matches provisioning contract |
| Governance bucket positive retention test | **PASS** — synthetic object got GOVERNANCE retain-until +180d automatically; exact-version extension to +730d readback confirmed |
| Governance bucket negative tests (legal-hold, lifecycle, bucket-lock, bypass+shorten) | **PASS** — all AccessDenied via explicit bucket-policy denies |
| B2 role state (remediated contract) | **PASS after reconciliation** — five mis-created roles deleted 2026-08-25; `legal-authority-placeholder`/`hold-executor`/`disposition-executor` absent; `everest-retention-broker`/`everest-retention-admin`/`everest-retention-audit-read-only` uncreated per contract; see `EV-GATEC-OP-RETENTION-002-ROLE-RECONCILIATION` |
| Writer boundary denies attached to 4 writers | **PASS** — 3 deny statements each |
| DB-04 migration `20260825_0008` upgrade/downgrade | **PASS** — applied to head and downgraded on disposable PostgreSQL |
| DB-04 PostgreSQL tests `test_storage_version.py` | **PASS** — 6 passed (columns, append-only events, exact triple uniqueness, non-empty identity, retain-until required, legacy unclassified) |
| SVC-05 unit tests `test_storage_state_machine.py` | **PASS** — 8 passed (identity rejection, state transitions, 730d extension, drift/KMS blocking, disabled hold/disposition) |
| Pylint (storage, models, tests, migration) | **PASS** — 10.00/10 |
| Black `--line-length 80` + compileall | **PASS** |
| API regression (weather API, registry, retention, raw storage) | **PASS** — 33 passed |
| Public serializer leakage check | **PASS** — `records_payload` emits canonical fields only; no bucket/key/version/KMS/retention facts |
| SVC-05 framework neutrality | **PASS** — `storage.py` imports only stdlib; no fastapi/sqlalchemy/boto3/requests |

## Acceptance-criteria mapping

- DB-04 §1: reviewed migration executes on disposable PostgreSQL — **PASS**.
- DB-04 §2: exact triple uniqueness + non-empty version constraints — **PASS**.
- DB-04 §3: legacy rows stay unclassified — **PASS** (test asserts no fabricated
  facts).
- DB-04 §4: storage events reject update/delete — **PASS** (immutable trigger).
- DB-04 §5: trigger/constraint tests prove required state evidence — **PASS**.
- DB-04 §6: public schemas unchanged, no bucket/key/version/KMS leak — **PASS**.
- SVC-05 §1: deterministic unit tests use ports/fakes, no SDK import in inner
  module — **PASS**.
- SVC-05 §2: commands reject missing identity before a port call — **PASS**.
- SVC-05 §3: 180/730 fixed-day UTC arithmetic — **PASS**.
- SVC-05 §4: S3 success recorded only after exact-version readback — **PASS**.
- SVC-05 §5: drift/delete-marker/unknown-hold/extension-failure/KMS block —
  **PASS**.
- SVC-05 §6: hold/disposition absent or typed disabled; no S3 mutation —
  **PASS**.
- SVC-05 §7: transaction/concurrency CAS + idempotent correlation — **PASS**
  (compare-and-set in `transition`; deterministic unit coverage).
- SVC-05 §8: public API + weather semantics unchanged — **PASS**.

## Remaining / open (not Stage-1-3 failures)

- Production Compliance canary remains **disabled**; requires separate Manager
  gate after Governance QA (Stage 4).
- S3 adapter for `ObjectVersionRetentionPort` (real S3 calls from the state
  machine) is not yet wired; the Governance bucket behavior was verified
  directly via the admin session. A backend adapter + integration test is a
  follow-up before operational use.
- Named legal/records authority and independent Manager approval remain
  unassigned; legal hold and disposition stay prohibited.
- `docs/api/API.md` still needs the DB-04/SVC-05 non-leak note (backlog).
- Worktree contains unrelated uncommitted changes (frontend, retention policy
  files) outside this QA scope; they are not evaluated here.

## Boundary

This PASS is scoped to B2 Stage-1 through Stage-3 nonproduction evidence. It
does not authorize the production Compliance canary, writer-profile
enablement, Block 3, release, legal hold, or disposition.
