# Everest Delivery Board

## EV-DATA-001

| ID | Phase | Owner | Status | Dependency | Handoff |
| --- | --- | --- | --- | --- | --- |
| EV-DATA-001-ARCH-A | A: Registry architecture | architect | complete | `AGENTS.md` | `docs/architecture/architecture.md` |
| EV-DATA-001-A-METADATA | A: Approved source metadata | meteorology | complete | architecture decision | `docs/data-sources.md` |
| EV-DATA-001-A-BACKEND | A: Registry persistence/configuration | backend | complete | none | `docs/api/API.md` |
| EV-DATA-001-A-QA | A: Registry verification | qa | complete | none | `docs/qa/test-plan.md` |
| EV-DATA-001-B | B: Weather schema | meteorology | complete | none | `docs/meteorology/weather-spec.md` |
| EV-DATA-001-C | C: ECMWF IFS | meteorology + backend | complete | none | `docs/meteorology/weather-spec.md` |
| EV-DATA-001-C-QA | C: ECMWF IFS verification | qa | complete | none | `docs/qa/test-plan.md` |
| EV-DATA-001-D | D: NOAA GFS | meteorology + backend | complete | none | `docs/meteorology/weather-spec.md` |
| EV-DATA-001-D-QA | D: NOAA GFS verification | qa | complete | none | `docs/qa/test-plan.md` |
| EV-DATA-001-E | E: DWD ICON | meteorology + backend | complete (Gate C-Core passed; historical disposable acceptance) | Gate C-Operational remains open for production/shared deployment | `docs/meteorology/weather-spec.md` |
| EV-DATA-001-E-QA | E: DWD ICON verification/review | qa + reviewer | complete (post-review: 58 passed, zero failed/skipped; focused ICON: 2 passed) | none | `docs/qa/test-plan.md` |
| EV-DATA-001-E-POSTREVIEW-BOARD | E: Post-review board reconciliation | Everest Manager | complete | Final reviewer PASS | `docs/management/board.md` |
| EV-DATA-001-REM-01-AOI | Updated spec: AOI authority | Everest Manager + gis-3d | complete | Manager approval | `docs/everest-aoi.md` |
| EV-DATA-001-REM-02-CONTRACT | Updated spec: contract path/port | architect + backend + meteorology | complete (Gate B/D evidence recorded) | none | `docs/architecture/architecture.md` |
| EV-DATA-001-REM-03-RAW-POLICY | Gate C-Core raw acceptance | Everest Manager + backend + meteorology | complete (historical disposable acceptance) | Final DBRE and Phase E QA | `docs/management/decisions.md` |
| EV-DATA-001-REM-03-OPERATIONAL | Gate C-Operational hardening | Everest Manager + security + release | blocked | IAM/WORM/legal/Git evidence | `docs/management/decisions.md` |
| EV-DATA-001-REM-04-ICON-STATE | Updated spec: ICON reconciliation | meteorology + Everest Manager | complete (historical verified; current health/API unknown) | none | `docs/data-sources.md` |
| EV-DATA-001-F | F: ECMWF AIFS | meteorology + backend | complete (source/core PASS; historical disposable `verified` after commit; current health/API unknown; documented current registry remains `connected`) | Phase E final review PASS | `docs/meteorology/weather-spec.md` |
| EV-DATA-001-F-UI-WAIVER | F: Option B delivery-boundary decision | Everest Manager | complete; `AGENTS.md` amended and ADR-014 accepted | none | `docs/management/decisions.md` |
| EV-DATA-001-F-QA | F: AIFS verification | qa | complete | none | `docs/qa/test-plan.md` |
| EV-DATA-001-F-REPORT | Phase-F report/stop gate | Everest Manager | published; exact ADR-015 criterion not proven | historical evidence limitation accepted | `docs/management/phase-f-report.md` |
| EV-DATA-001-F-QA-RETEST-DISPLAY | F: historical final closure QA | qa | complete for source/core and UI deferral; does not evidence all ADR-015 endpoints | none | `docs/qa/test-plan.md` |
| EV-DATA-001-ADR015-RECONCILE-MGMT | ADR-015 management evidence reconciliation | Everest Manager | complete; forecast proven, four-route gap recorded | architecture audit | `docs/management/decisions.md` |
| EV-DATA-001-ADR015-ENDPOINT-QA | ADR-015 endpoint evidence QA | qa | complete; exact five-route criterion not proven | no rerun authorized | `docs/qa/test-plan.md` |

## Delivery Stop

**Current delivery status: STOPPED with an accepted historical ADR-015 evidence
limitation.** The source/core work remains historically accepted. The exact
five-route display criterion is not proven: forecast is evidenced; current,
profile, sources, and data-health are not. No database/provider/service rerun is
authorized solely for documentation closure. No additional data
domains, frontend work, release, production/shared deployment, UI, database or
provider rerun, or raw-artifact operation is authorized. Work may resume only
after a new explicit Everest Manager instruction and the required governance
stages.

## Post-A-F Roadmap

| ID | Block | Status | Dependency | Handoff |
| --- | --- | --- | --- | --- |
| EV-GATEC-OP-ARCH-001 | Gate C-Operational architecture decomposition | complete | Manager sequence decision | `docs/management/decisions.md` |
| EV-GATEC-OP-ACL-001 | Operational identities and raw-root ACL/IAM | PASS for recorded nonproduction scope (independent QA re-evaluation 2026-08-25); Git exclusion + gitleaks clean-scan evidence recorded | residual-risk register carried forward; no writer-profile enablement or production deployment; Block 2 remains closed | `docs/management/decisions.md`, `docs/qa/test-plan.md` |
| EV-GATEC-OP-RETENTION-002 | WORM, legal hold, and disposition | B2 offline remediation + role reconciliation COMPLETE (2026-08-25); Stage 1-3 nonproduction evidence QA PASS; **Stage-4 production canary AUTHORIZED by Manager** (`EV-GATEC-OP-RETENTION-002-CANARY-AUTH`), execution pending human MFA admin session via the broker-activation procedure | AWS role state reconciled with remediated contract (mis-created roles deleted; broker/admin/audit uncreated; legal/hold/disposition absent); bucket + policy retained; legal hold/disposition prohibited; canary disabled until activation | `docs/management/decisions.md`, `docs/architecture/EV-GATEC-OP-RETENTION-002-backend-contract.md` |
| EV-GATEC-OP-GIT-003 | Authoritative Git exclusion evidence | evidence complete + **independent QA ACCEPTED 2026-08-25** (`EV-GATEC-OP-GIT-003-QA`): 47 commits / 247 tracked files, no raw payloads tracked, `.gitignore` exclusions in force, manual secret scan clean except intentional redaction fixtures, authoritative remote `Yizebaba/everest` | authoritative remote `Yizebaba/everest` established; raw artifacts excluded; gitleaks clean (0 new leaks vs baseline) | `docs/management/decisions.md` |
| EV-GATEC-OP-TMP-004 | Legacy `tmp-*` inventory/disposition | COMPLETE (2026-08-25): all legacy `tmp-gfs*`/`tmp-icon*` raw artifacts (11 files, 34,466,828 B) relocated non-destructively to `D:\Everest-data\raw\legacy-tmp-004\` with content-addressed structure preserved and a disposition manifest (`tmp-004-disposition.json`); empty legacy dirs removed from the workspace; GFS payload hash matches the authoritative data-sources record | ACL, retention, Git evidence, separate Manager authorization | `docs/management/decisions.md` |
| EV-GATEC-OP-DB-005 | Persistent PostgreSQL and recovery | COMPLETE (2026-08-25): Docker compose persistent PostgreSQL (port 56021, healthy, persistent volume), backup/restore scripts with non-empty-db protection, migrations applied to head | none | `infra/docker/compose.yml`, `infra/docker/backup.sh`, `infra/docker/restore.sh` |
| EV-GATEC-OP-RUNTIME-006 | Supervised service and current health | COMPLETE (2026-08-25): systemd-managed API on 52147 (active, restart on failure); 6-hourly scheduler timer ingests latest IFS 0-72h (25 leads) with cycle fallback; API verified returning persisted forecast. Ports 50149/50151 re-homed to 52147/52148 under ADR-020 because Windows excluded range 50060-50159 blocked WSL mirrored-mode binds | persistent PostgreSQL (DB-005) | `infra/docker/systemd/`, `apps/api/schedule_forecast.py` |
| EV-GATEC-OP-SECRETS-007 | Secrets/configuration management | COMPLETE (2026-08-25): runtime secrets via operator env file (chmod 600); non-secret config committed; registry stores reference names only; redaction + gitleaks verified | identity and runtime composition (DB-005/RUNTIME-006) | `docs/architecture/EV-GATEC-OP-SECRETS-007.md` |
| EV-GATEC-OP-AUDIT-008 | Audit/observability/alerting | COMPLETE (2026-08-25): healthz/readyz + 5-min monitor; CloudTrail trail `everest-operational-audit` logging object data events for approved buckets; audit bucket (COMPLIANCE 1095d) created | Blocks 1-7 | `docs/architecture/EV-GATEC-OP-AUDIT-008.md` |
| EV-GATEC-OP-QA-009 | Independent operational QA | COMPLETE (2026-08-25): PASS for recorded nonproduction runtime; live probes + block evidence re-confirmed | Blocks 1-8 | `docs/qa/test-plan.md` |
| EV-GATEC-OP-RELEASE-010 | Release gate definition | DEFINED + Manager decision recorded 2026-08-25: WSL/Docker local runtime (API 52147, frontend 52148, PG 56021), not public; RELEASE-010-STATUS update records Gate C progression (TMP-004 complete, GIT-003 QA accepted, B1 partial, B2 canary pending); CloudTrail delivery confirmed; no shared/production deployment | Gate C-Operational QA pass (QA-009) | `docs/architecture/EV-GATEC-OP-RELEASE-010.md`, `docs/management/decisions.md` |

Only one block may be `in progress`. The read-only frontend is now integrated
(port 52148, CORS-verified); GIS-3D/Cesium scene exists in `apps/web`; ADR-019
sources (terrain, Everest AWS station, Himawari satellite) are `connected` with
QA-recorded connected-scope PASS. OSM, Risk, additional satellite/terrain, and
persisted ADR-019 record ingestion into the running database remain future,
separately authorized work.

### ADR-015 endpoint evidence boundary

- Retained evidence supports `GET /api/weather/forecast` returning a persisted
  real canonical record through a disposable PostgreSQL run.
- The completed inventory found no retained real-persisted HTTP response for
  `GET /api/weather/current`, `GET /api/weather/profile`,
  `GET /api/weather/sources`, or `GET /api/data-health`.
- Route implementation, PostgreSQL-only design, source/core acceptance, or
  evidence from the forecast route must not be used to infer results for those
  four routes.
- Current health and API availability remain `unknown` after teardown. This is
  an evidence reconciliation only, not a live-service claim.

## EV-DATA-001-F-REPORT — 2026-08-22 Manager Continuation

The latest `AGENTS.md` was reread before this continuation. Workspace audit
against that specification:

- Phases A-E remain historically accepted at Gate C-Core. Gate C-Operational
  remains open and production-only.
- Phase F AIFS source/core is accepted by QA `EV-DATA-001-F-QA-CLOSE-RETRY`:
  retained real GRIB2, WSL ecCodes `2.47.1`, parser/normalizer/QC, owner-neutral
  adapter, PostgreSQL `raw=1`/`record=1`/`audit=1` on disposable port `46901`,
  bounded forecast API HTTP 200 with `model=AIFS`, tests `66/66` plus AIFS `4`
  and meteorology AIFS `37`.
- Current health and API availability remain `unknown` after teardown. AIFS
  current documented registry status remains `connected`; historical in-run
  `verified`/`healthy` is not current health.
- Manager-approved Option B is recorded by ADR-014 and the amended `AGENTS.md`:
  A-F ends at persisted, queryable, independently tested backend API results.
  ADR-015 defines five required endpoints, but the completed retained-evidence
  inventory establishes only the forecast endpoint. QA completed and recorded
  the other four as a historical evidence limitation accepted by the Everest
  Manager under ADR-016. Frontend display is deferred and is not a stop gate. No new UI is
  authorized, and frontends remain prohibited from calling external sources
  directly.
- The Phase-F report was published at `docs/management/phase-f-report.md`; its
  older AIFS evidence and frontend-stop-gate wording are superseded by this
  board and the authoritative current domain/QA handoffs. ADR-015 endpoint
  evidence inventory and QA are complete; they do not claim the missing four
  routes were proven.
- No AWS, Pyramid, satellite, terrain, OSM, AI, Risk, or UI work was started.
- Existing project-root `tmp-icon*`/`tmp-gfs*` artifacts remain untouched.

**A-F source/core chain: PASS as historical disposable evidence.**
**Authoritative AIFS evidence: `final66` / `AIFS4` / `met37` / port `46901`.**
**EV-DATA-001 delivery closure: STOPPED by Manager confirmation and controlling
QA record `EV-DATA-001-F-QA-STOP`.**
**Live service / production / Gate C-Operational: not claimed.**
**New UI: not authorized and not implemented.**

## Delivery Boundary

Only EV-DATA-001 phases A through F are authorized. Phase B is blocked until
Phase A has passed architecture review and QA. Connector work for ECMWF, GFS,
ICON, and AIFS is not authorized during Phase A.

## Current QA Blockers

- AIFS source/core QA is PASS. Authoritative evidence is `apps/api` **66
  passed, 0 failed, 0 skipped**, focused AIFS **4 passed, 0 failed, 0
  skipped**, and meteorology AIFS **37 passed, 0 failed, 0 skipped**. This
  supersedes the historical `61/61`, focused `3/3`, and port `44859` evidence.
- Final source/core code review reports no source/core code blocker.
- `docs/management/phase-f-report.md` has been created. Report creation is no
  longer a blocker.
- Manager-approved Option B resolves the frontend stop-gate conflict: frontend
  display is deferred and is not required to close A-F. ADR-015 endpoint
  evidence remains a separate stop-gate requirement. Forecast is evidenced;
  current, profile, weather/sources, and data-health remain pending retained-
  evidence inventory and QA and are not inferred. No frontend implementation,
  database/provider rerun, or other runtime recreation is authorized by this
  board.
- AIFS was historically disposable `verified`/`healthy` only after the
  canonical commit. Current health and API availability are `unknown` after
  teardown.

## EV-DATA-001-FULL-AUDIT: From-Scratch Audit

The latest `AGENTS.md` was reread and the project was audited from the current
workspace. The three-failure escalation rule is now part of `AGENTS.md` and
`docs/management/decisions.md`. No identical root-cause signature is currently
proven to have reached three occurrences, so no fourth-attempt escalation is
claimed. Future failures must pause at the third identical occurrence and use
the official-documents/logs procedure before retrying.

Current audit conclusion: A-D remain historically documented and Phase E is
accepted at Gate C-Core on historical disposable evidence. ICON's in-run
`verified`/`healthy` state is historical; current health and API availability
are unknown after teardown. The workspace is not a Git checkout; project-root
`tmp-icon*`/`tmp-gfs*` raw artifacts remain untouched and noncompliant. Gate
C-Operational remains open for production/shared deployment, automatic
disposition, and production-grade retention claims. Phase E post-review
evidence and finding dispositions are recorded; AIFS remains pending and is not
authorized until the final reviewer verdict.

ADR-013 supersedes the single-gate interpretation for execution sequencing.
Gate C-Core may proceed in a controlled disposable environment; Gate
C-Operational remains blocked and continues to prohibit production/shared
deployment, automatic disposition, and production-grade retention claims.

### Audit Verification Snapshot

- Root test command with API and workspace paths: `114 passed, 14 skipped, 1
  warning`.
- `compileall` for weather, shared contract, and API: passed.
- Pylint currently reports `9.92/10`; the quality gate is not green because the
  scan includes build-copy duplicate code and declarative ORM/DTO findings.
- `D:\Everest-data\raw`, `docs/everest-aoi.md`, and `docs/weather-spec.md`
  exist.
- The workspace has no `.git` metadata; Git tracking/exclusion evidence is not
  available here.
- No identical root-cause failure signature is evidenced at three occurrences;
  the repeated-failure escalation rule has not required a fourth-attempt pause
  during this audit.
- Phase E post-review passed with `58 passed, 0 failed, 0 skipped`; the focused
  ICON composition result passed `2` tests.
- The E-001 through E-010 disposition mapping is recorded in
  `docs/management/decisions.md`: E-001 through E-006 and E-008 through E-009
  are closed, E-007 remains assigned to Gate C-Operational, and E-010 is closed
  by the authoritative current-status records.

Phase A passed final QA on 2026-08-21. The disposable PostgreSQL acceptance run
executed all 19 tests, including migration/persistence checks, and its container,
volume, and random-port listener were removed afterward. Phase B is authorized.

Phase B passed QA with non-blocking test debt on 2026-08-21. Phase C ECMWF IFS
is authorized. This historical sequencing note is superseded by the later
Phase C and Phase D acceptance records below.

Phase C completed historical disposable end-to-end evidence: real IFS GRIB2
retrieval, parsing, QC, PostgreSQL persistence, and API query. The temporary
database was removed, so current runtime health is unknown. All Phase C QA
findings were remediated and final QA passed. Phase D NOAA GFS was subsequently
accepted; the later Phase E acceptance record below is authoritative.

Phase D passed final QA after historical disposable end-to-end evidence through the
checked-in GFS adapter: official NOAA range retrieval, metadata integrity,
GRIB2 parsing, normalization, PostgreSQL persistence, and forecast API query.
The test environment was removed, so current runtime health and API
availability are unknown. The Everest Manager approved the external operational
raw root `D:\Everest-data\raw`, which was created on 2026-08-21. Gate C-Core is
closed for the accepted historical ICON run; Gate C-Operational remains open:
retention/access/disposition enforcement, repository exclusions, and production
hardening remain implementation work.
Existing project-root `tmp-icon*` and `tmp-gfs*` artifacts remain unmoved
pending disposition and are noncompliant durable-storage evidence. This update
does not move or otherwise operate on those artifacts. No reuse or new
acquisition may occur before root use is implemented and validated.
AOI Gate A is complete under ADR-012 and the approved authority at
`docs/everest-aoi.md`. Gates B and D are closed for the Phase E path, and Gate
C-Core passed through the final controlled disposable DBRE/API evidence. ICON
is historically `verified`/`healthy`; the disposable database and listener were
removed, so current health and API availability are unknown. Gate C-Operational
remains the production-only blocker. Phase F source/core is complete and passed
final source/core QA; code review has no source/core code blockers. The Phase-F
report is published at `docs/management/phase-f-report.md`. ADR-015 endpoint
evidence QA remains pending: forecast is evidenced, while current, profile,
weather/sources, and data-health await retained-evidence inventory and are not
inferred. Frontend display is deferred and is not a stop gate. This board does
not close EV-DATA-001 or authorize work beyond Phase F.

## EV-DATA-001-REM-03-RETENTION: Board Acceptance

The approved retention policy is recorded in `docs/management/decisions.md`
under `EV-DATA-001-REM-03-RETENTION`. It defines the required retention,
access, disposition, legal-hold, audit, artifact-identity, and root-boundary
controls for `D:\Everest-data\raw`.

The backend migrations `0004`–`0006`, corrected table-safe append-only triggers,
classified acceptance/reuse audit, bounded append-only audit table, and internal
fail-closed transition boundary are implemented runtime components. The final
DBRE evidence additionally accepts the approved-root ICON artifact,
PostgreSQL persistence, and bounded API result for Gate C-Core. These facts do
not establish IAM/ACL, legal/WORM, or Git enforcement for Gate C-Operational.

### QA gate checklist

- [ ] Fail-closed validation of the configured external root is demonstrated.
- [ ] Escape, traversal, empty-reference, and link/junction boundary cases are
  rejected before persistence.
- [ ] A real connector artifact set is retained under the approved root with
  payload, metadata, sidecar, provenance, AOI version, and integrity evidence.
- [ ] Write/reuse integrity verification rejects changed or missing artifact
  facts without deleting raw data.
- [ ] Executed PostgreSQL evidence proves retention owner/class/period/due date
  and disposition state are persisted and queryable for every accepted artifact.
- [x] Backend migration `0004` persists approved classification for new rows and
  explicit `legacy_unclassified` state for existing rows.
- [x] Acceptance and reuse audit events are append-only, bounded, and private.
- [ ] Least-privilege access, unauthorized access rejection, grant, change, and
  revocation are tested with named identities/roles.
- [ ] Legal hold protects artifacts from disposition and release is authorized
  and audited; missing or ambiguous hold state fails closed.
- [ ] Disposition approval, hold check, completion evidence, and non-automatic
  deletion behavior are verified.
- [ ] Append-only audit events cover acceptance, reads, reuse, integrity
  failures, access changes, holds, and disposition actions.
- [ ] QA records real UTC evidence, failed paths, artifact IDs, and test output.
- [x] QA records the final ICON DB/API acceptance under Gate C-Core and keeps
  Gate C-Operational open for production hardening.

**Current status:** Gate C-Core is accepted on the final approved-root,
disposable ICON DBRE/API evidence. Gate C-Operational remains blocked pending
ACL/IAM, legal/WORM, Git, and related production-hardening evidence. The final
run's database and listener were removed; current ICON health and API
availability are unknown.

### Open controls at board update

1. Approved retention classes, periods, owners, and policy disposition rules
   are recorded; per-artifact lifecycle facts are not yet proven in an executed
   PostgreSQL approved-root flow.
2. Runtime retention persistence/enforcement has partial implementation but is
   not yet evidenced by an executed approved-root PostgreSQL/QA run.
3. Root IAM/filesystem permissions and least-privilege identities are not yet
   approved or tested.
4. Legal-hold lifecycle and fail-closed enforcement are not yet evidenced.
5. Disposition authorization, execution, and audit evidence are not yet
   evidenced.
6. Append-only audit storage has partial implementation; executed PostgreSQL
   evidence, complete event coverage, retention, and access controls are not
   yet evidenced.
7. End-to-end approved-root artifact-retention evidence is not yet accepted.
8. Repository exclusion/tracking enforcement and disposition of existing
    `tmp-icon*`/`tmp-gfs*` artifacts remain open.
9. Canonical weather-contract QA acceptance remains an independent Phase E
   prerequisite.
10. Owner-neutral ingestion-port QA acceptance remains an independent Phase E
    prerequisite.
11. Gate C-Operational hardening remains open; it does not invalidate the
    accepted historical ICON database/API result or Phase E QA.

## EV-GATEC-OP-ACL-001-RUNBOOK: Block 1 operator handoff

**Update date:** 2026-08-24  
**Status:** Offline runbook/templates complete; human AWS execution and QA
evidence pending

- [x] Account `982408502231`, Region `ap-south-1`, candidate bucket
  `zhufengxiangmu`, and public CA PEM path are recorded as supplied identifiers.
- [x] Existing `ap-east-1` trust-anchor state and AWS-managed `aws/s3` key are
  quarantined from production renderer inputs.
- [x] Human Console/CLI procedures, one-way Object Lock warnings, evidence
  checklist, rollback, CloudTrail Block-8 requirement, and nonproduction QA
  handoff are documented under `infra/aws/gate-c-operational/acl/`.
- [x] Offline renderer tests reject wrong-Region trust anchors and `aws/s3`
  managed-key identifiers as production inputs.
- [x] `BucketKeyEnabled=true` is reconciled in the resource config, renderer,
  exact bucket-ARN KMS context, validator, negative tests, and runbooks.
- [x] Prefix isolation remains in S3 writer resources; reduced KMS event density
  and the future Block-8 S3 object-data-event dependency are documented.
- [ ] Human administrator confirms/creates the dedicated empty Object-Lock
  bucket and returns sanitized S3 evidence.
- [ ] Human administrator creates a symmetric customer-managed KMS key and
  returns `KeyManager=CUSTOMER` plus exact ARN evidence.
- [ ] Human administrator creates the new `ap-south-1` trust anchor from the
  public PEM and returns its exact ARN.
- [ ] Exact rendered policies pass IAM Access Analyzer and four writer
  roles/profiles plus verifier/audit roles are created and evidenced.
- [ ] Separately approved nonproduction positive/negative authorization QA is
  executed. Gate C-Operational remains open; Block 2 remains closed.

### EV-GATEC-OP-ACL-001-OPERATOR-READ continuation

AWS CLI `2.36.29` default-profile login is confirmed as account
`982408502231` IAM user `everest-gatec-operator`; `sts:GetCallerIdentity`
succeeded. One verification event produced eight AccessDenied results sharing
the missing-identity-policy root cause: six exact bucket-configuration reads,
`kms:DescribeKey`, and `rolesanywhere:GetTrustAnchor`. No retry was made.
Offline exact policy, admin attachment/removal runbook, dry-run-first CLI
template, redaction rules, and tests are complete. This paragraph records the
historical blocked state; the evidence-review section below supersedes it after
sanitized reads were supplied. KMS and trust-anchor Region/control mismatches
remain unresolved. Git
authentication is confirmed, but the authoritative repository is missing, so
Git evidence remains blocked. No Block 2 or resource operation is authorized.

### EV-GATEC-OP-ACL-001-AWS-EVIDENCE-REVIEW

**Update date:** 2026-08-24  
**Status:** Historical intermediate review; superseded by
`EV-GATEC-OP-ACL-001-LIVE-EVIDENCE` below

Bucket Key design reconciliation is complete offline. This does not change the
remaining failed/pending AWS controls or authorize an AWS mutation.

- [x] Caller is account `982408502231`, IAM user
  `everest-gatec-operator`; bucket `zhufengxiangmu` is in `ap-south-1`.
- [x] Versioning `Enabled`, Object Lock capability `Enabled`, and
  `BucketOwnerEnforced` are evidenced.
- [x] No Object Lock default retention rule was returned; this is intentionally
  deferred to Block 2 and must not be changed under Block 1.
- [ ] **FAIL:** all four bucket Block Public Access values are `false`; an
  administrator must enable all four and return sanitized read evidence showing
  all four `true`.
- [ ] **PENDING:** bucket SSE-KMS uses actual key ARN
  `arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`,
  but exact-key `DescribeKey` evidence proving `KeyManager=CUSTOMER`, symmetric
  encrypt/decrypt, enabled, and single-Region is required.
- [ ] **PENDING RECONCILIATION:** observed `BucketKeyEnabled=true` differs from
  the approved offline template value `false`; no change is authorized by this
  review, and KMS encryption-context/policy compatibility must be decided before
  rendering or QA.
- [x] **QUARANTINED:** the old supplied key ending `72e66` is AWS managed and
  cannot satisfy Block 1.
- [ ] **FAIL:** the supplied wrong-Region `ap-east-1` trust-anchor UUID returned
  `ResourceNotFound`; create/evidence an approved public-CA trust anchor in
  `ap-south-1`, then collect exact writer/profile and verifier/audit ARNs.
- [ ] Remove the temporary operator inline read policy and return sanitized
  absence/removal proof with administrator, approval reference, target user,
  policy name, and UTC removal time.

The prior AccessDenied event (missing identity allow) and current
`ResourceNotFound` response for the supplied trust-anchor UUID are distinct
root-cause signatures, each at count 1. No three-failure escalation applies.
No AWS/resource/object mutation, object read, Block 2, Docker/DB, Git, raw, or
`tmp-*` operation was performed by this documentation review.

### EV-GATEC-OP-ACL-001-LIVE-EVIDENCE

**Update date:** 2026-08-24  
**Status:** **BLOCKED — partial PASS; admin remediation and QA pending**

Three identical OpenCode subagent stream interruptions triggered the repeated-
failure escalation rule. The incident, exact UTC log evidence, and accepted
direct-primary-session corrective procedure are recorded in
`docs/management/decisions.md`. No fourth subagent attempt is authorized for
this task.

- [x] Account BPA has all four controls true; effective public-access blocking
  currently passes because S3 applies the most restrictive account/bucket
  combination.
- [ ] Bucket BPA has all four controls false and fails the explicit template
  invariant. Admin must set all four true without weakening account BPA.
- [x] Bucket Region, Versioning, Object Lock capability,
  `BucketOwnerEnforced`, SSE-KMS CMK, and Bucket Key pass.
- [x] Exact key ending `3ea2b50b...` is customer-managed, enabled, symmetric
  encrypt/decrypt, single-Region; alias is `alias/everest-gatec-cmk`.
- [ ] Default root-account `kms:*` delegation is bootstrap-only. Final Block 1
  needs a tested named administrator/recovery path and explicit writer/verifier
  key use before broad IAM delegation is removed.
- [ ] `AdministratorAccess` on the operator fails least privilege. Remove it
  only after a replacement federated admin and break-glass path are tested in a
  separate session; never self-lock out.
- [ ] Enabled `ap-south-1` `CERTIFICATE_BUNDLE` anchor `zhufengxiangmu`
  (`f66ffa5e...`) exists, but exact ARN and approved-organization-CA provenance
  remain pending. `ap-east-1` correctly contributes no anchor.
- [ ] Six roles under `/everest/`, four disabled one-role/900-second profiles,
  approved certificate CN/SAN UUIDs, enabled CRL, bucket/KMS policies, and
  nonproduction authorization QA remain pending.
- [ ] No Access Analyzer exists. Create the account external-access Analyzer
  `everest-gatec-external-access` in `ap-south-1`; empty inventory is not a
  clean-findings result.
- [x] Corrected CloudTrail read returned an empty trail list. CloudTrail is
  absent; creation and S3 object data-event configuration remain deferred to
  Block 8 and are not a Block 1 resource-creation task.

## EV-DATA-001-REM-03-GOVERNANCE: Gate C Blocker Register

**Review date:** 2026-08-21  
**Status:** Gate C failed/blocked; no closure claimed

The latest Gate C QA decision accepts the disposable PostgreSQL result only as
backend/database evidence: migrations `20260821_0001` through `20260821_0006`,
`44 passed, no skips`, documented non-standard port `64035`, and complete
database/listener cleanup. PostgreSQL remains the required acceptance path.
That result does not prove the following operational controls:

| Blocker | Exact unresolved evidence | Required status |
| --- | --- | --- |
| ACL/IAM | Named connector/operator identities, least-privilege OS ACL or object-store IAM, unauthorized read/write denial, grant/change/revocation, and approval/audit identity evidence | Open; Gate C blocker `GATEC-CLOSE-001` |
| Legal/WORM | Deployment-enforced legal-hold and disposition authority, fail-closed hold behavior, and filesystem/object-store WORM or approved equivalent against privileged modification | Open; Gate C blocker `GATEC-CLOSE-002` |
| Git evidence | Raw payload/metadata/sidecar exclusion and non-tracking in an authoritative Git-bearing checkout; legacy `tmp-icon*`/`tmp-gfs*` disposition remains separate and open | Open; Gate C blocker `GATEC-CLOSE-003` |

This governance update changes no approved policy, does not operate on raw
data, and does not modify code. Gate C-Core is accepted by the final Phase E
QA and DBRE evidence. ICON's `verified`/`healthy` values are historical
disposable acceptance facts only; current health and API availability are
unknown after teardown. Gate C-Operational remains open and continues to
block production/shared deployment, automatic disposition, and
production-grade retention claims.

## AOI Authority Review

`docs/everest-aoi.md` records the approved AOI identifier
`everest-south-route`, version `everest-south-route-v1.0`, WGS 84 center and
default 100 km radius definitions, plus a separately approved 2,000 km
expansion. The authority also records the approved, generated, validated
canonical `Polygon` artifact
`docs/everest-south-route-v1.0-expanded-2000km.geojson`, including its
checksum and serialized-coordinate bbox. It introduces no route, camp, or other
named-feature geometry. External acquisition and reuse must remain within the
applicable approved radius and retain the AOI identifier/version; Gate C and the
other Phase E controls still prohibit ICON operational use.

## EV-DATA-001-REM-01-APPROVAL: Manager Checklist

**Status:** Complete; approved serialized expanded geometry recorded

| Check | Status |
| --- | --- |
| AOI authority document exists | Complete: `docs/everest-aoi.md` |
| Precise radius-based AOI definition | Complete: `docs/everest-aoi.md` |
| Authoritative CRS and axis order | Complete: WGS 84 / `EPSG:4326` |
| AOI identifier/version | Complete: `everest-south-route-v1.0` |
| 100 km implementation method | Complete: WGS 84 geodesic radius rule |
| Serialized geometry/bounding box | Complete: approved canonical `Polygon`; SHA-256 `b21ce4c8fe8d0fae15e0723e54fa3224f06e253b2662cdaee58e8efe1bb290ac` |
| Manager decision, approver, and effective date | Complete: 2026-08-21 record |
| New external acquisition | AOI-permitted only; blocked by Gate C and applicable provider gates |
| Existing-data reuse for acceptance | Blocked by Gate C and applicable provider gates |

The authority document approves the radius definitions and the recorded
serialized expanded boundary, not route, camp, or other named-feature geometry.
Gate A is complete. No new ICON acquisition or reuse for acceptance may proceed
while Gate C and the remaining Phase E controls are open.


## EV-DELIVERY-017: New delivery lines (ADR-017)

Authorized 2026-08-24 by Everest Manager. Each line follows the full delivery
lifecycle; frontend never calls external providers.

| ID | Line | Owner (lead) | Status | Handoff |
| --- | --- | --- | --- | --- |
| EV-UI-001 | Frontend UI (deferred A-F display) | frontend + gis-3d | **Integration re-verification PASS (2026-08-25):** API on 52147 and frontend on 52148 (ADR-020 port re-home); CORS preflight 200 with `X-Correlation-ID`, UTC `Z` datetimes on all public routes, forecast/current separation via `weatherFlow`, duplicate-key and OSM-CSP fixes; web tests 37 passed, API 67 passed, weather 111 passed, build/typecheck/eslint/prettier clean, browser E2E PASS with panels rendering real IFS canonical data and zero console errors. Historical A-F source/core acceptance is unchanged; four-source data remains scheduler-scoped (only IFS currently ingested) and truthful health semantics are preserved. | `docs/product/PRD.md`, `docs/architecture/architecture.md`, `docs/design/DESIGN.md`, `docs/qa/test-plan.md` |
| EV-AWS-STATION-001 | Everest AWS observation stations | meteorology + backend | **connected + persisted + API + integration PASS; QA PASS for connected scope (2026-08-25)** — real rows for Base Camp/Camp 2/South Col persisted and served by `/api/observations/current`; registry seeded `everest-aws` (connected, unknown); commercial NOT authorized; full per-record verified pending provider-backed endpoint | docs/meteorology/weather-spec.md |
| EV-PYRAMID-001 | Pyramid meteorological network | meteorology + backend | planned (registered 2026-08-25 in `docs/data-sources.md` and weather-spec: Ev-K2-CNR 7-station network, 2660-7986 m, CC BY 4.0, Zenodo DOI 10.5281/zenodo.15211352 + geoportal; connector/ingestion requires separate authorization) | docs/meteorology/weather-spec.md |
| EV-SAT-001 | Satellite (Himawari-8/9, Sentinel-1/2, Landsat 8/9) | meteorology + gis-3d | **connected + persisted + API + integration PASS; QA PASS for connected scope (2026-08-25)** (real sha256; no leak; SQL dedup; mocked network test; atomic download); band-3 segment persisted and served by `/api/satellite/segments`; registry seeded `himawari-9` (connected, unknown); field decode pending JMA guide | docs/meteorology/weather-spec.md |
| EV-TERRAIN-001 | Terrain/GIS (Copernicus DEM GLO-30, Cesium/3D Tiles, PostGIS) | gis-3d | **connected + persisted + API + integration PASS; QA PASS for connected scope (2026-08-25)** (no leak; input validation; atomic download; black clean); GLO-30 Everest tile persisted and served by `/api/terrain/tile`; registry seeded `copernicus-dem` (connected, unknown); PostGIS raster sampling + full verified pending | docs/gis/terrain-spec.md |
| EV-ENV-OSM-AI-RISK | Environmental / OSM / AI / Risk | OSM base layer COMPLETE (EV-OSM-001); Risk engine COMPLETE (EV-RISK-001, rules-only, non-AI); AI / additional environmental layers remain future | individually scoped | - |
