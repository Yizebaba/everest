# Everest Architecture

## EV-GATEC-OP-ACL-001-TEMPLATE: Block-1 ACL/IAM template boundary

**Status:** Offline Bucket Key templates and human runbook reconciled; AWS
implementation and QA evidence remain pending.

The security-owned offline assets at `infra/aws/gate-c-operational/acl/` define
parameterized S3, KMS, IAM Roles Anywhere, identity-mapping, and rollback
contracts for the approved Block-1 decisions. They are deliberately
non-deployable: no resources, roles, trust anchors, profiles, users, keys,
credentials, CA material, AWS account, bucket, or secret is created or read.
`${RAW_BUCKET}` remains unresolved and the selected region is `ap-south-1`.

The four writer roles are exactly ECMWF IFS, NOAA GFS, DWD ICON, and ECMWF
AIFS. Each has a distinct prefix, role, profile, and certificate subject.
Writers can put only under their own prefix and cannot read or delete. Block-1
chooses no multipart uploads; the renderer enforces a 10 MiB maximum object
size and grants no abort or multipart KMS permissions. Verifier and audit
access are separate. Bucket denies require TLS, SSE-KMS with the exact key,
deny public ACLs, and deny Object Lock mutation/bypass. Resource configuration
represents Object Lock, BucketOwnerEnforced ownership, and all four Block
Public Access settings. Roles Anywhere trust uses all three required STS
actions and X.509 subject/SAN/source-identity conditions; profiles are valid
CreateProfile requests, disabled, and set to 900 seconds.

The identity chain is explicit rather than inherited:
Windows service account -> controlled WSL/Docker launcher -> dedicated
container identity -> unique X.509 workload certificate -> Roles Anywhere
profile -> named IAM role. Account ID, bucket, organization CA path, trust
anchor, and non-production validation are dependencies, not assumptions.

The Block-1 human runbook binds the intended nonproduction deployment to account
`982408502231`, Region `ap-south-1`, candidate bucket `zhufengxiangmu`, and the
public organization CA PEM path supplied by the Manager. The existing
`ap-east-1` trust anchor and AWS-managed `aws/s3` key are quarantined: the
single-Region design requires a new `ap-south-1` trust-anchor ARN and a symmetric
customer-managed KMS key in the same account and Region, evidenced by
`KeyManager=CUSTOMER`. The renderer now accepts valid general-purpose S3 names,
requires exact same-account `ap-south-1` KMS key and trust-anchor ARNs, and still
fails closed on aliases, wrong Regions, placeholders, and mapping changes.

The four machine writers retain one role, one 900-second disabled Roles Anywhere
profile, and one unique certificate requirement each. Verifier and audit are
separate human-federated roles using explicit 900-second test assumptions; their
federation principal remains an external input and must not be invented. S3
object data-event logging is recorded as a Block-8 requirement only.

The approved Block-1 design now enables S3 Bucket Keys. The KMS fragment
requires `kms:ViaService=s3.ap-south-1.amazonaws.com` and exact
`kms:EncryptionContext:aws:s3:arn=arn:aws:s3:::${RAW_BUCKET}`. Object and prefix
contexts are invalid with a Bucket Key. Source isolation remains in each S3
writer policy's prefix-scoped resource; KMS context cannot enforce per-prefix
isolation in this mode. Bucket Keys reduce KMS request and CloudTrail event
density. S3 object data events remain the future Block-8 audit source.

No AWS call, certificate/key issuance, Block-2 WORM/legal-hold/disposition
implementation, runtime authorization test, or CloudTrail deployment is
included.

### EV-GATEC-OP-ACL-001-LIVE-EVIDENCE reconciliation

Manager-supplied sanitized AWS reads on 2026-08-24 partially establish the
Block 1 resource state. The operator currently has `AdministratorAccess`; this
is a critical least-privilege failure and must not become the workload or final
operator path. Account-level S3 Block Public Access has all four controls true,
so S3 currently applies those effective protections even though all four bucket
controls are false. The bucket therefore is effectively protected from public
access, but it still fails this template's defence-in-depth and drift-resistant
invariant that all four controls also be explicitly true on the bucket.

Bucket Region, Versioning, Object Lock capability, `BucketOwnerEnforced`, and
SSE-KMS with Bucket Keys pass. Object Lock has no default retention rule; that
is correct because retention mode/period, legal holds, and disposition belong
only to closed Block 2.

S3 reports SSE-KMS with actual key ARN
`arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0`.
Exact-key evidence now proves `KeyManager=CUSTOMER`, `KeySpec=SYMMETRIC_DEFAULT`,
`KeyUsage=ENCRYPT_DECRYPT`, enabled state, and `MultiRegion=false`; alias
`alias/everest-gatec-cmk` resolves to this key. The key metadata therefore
passes. Its current account-principal `kms:*` statement is the documented AWS
default bootstrap: it does not directly grant every principal key use, but it
enables broad IAM-policy delegation. That is acceptable only while establishing
and testing a recoverable named-administrator path. It fails the final Block 1
least-privilege policy. Before workload profiles are enabled, replace broad IAM
delegation with explicit named key-administrator/recovery statements and the
four-writer/verifier statements, after testing the replacement administrator;
never replace the policy with the workload fragment or remove the last working
key administrator. The old AWS-managed key remains quarantined.

An enabled `CERTIFICATE_BUNDLE` trust anchor named `zhufengxiangmu` with ID
beginning `f66ffa5e` exists in `ap-south-1`; `ap-east-1` has no anchors. Regional
presence passes, while approved-CA provenance remains pending until the PKI
owner proves that its source certificate is the approved organization CA.
Profiles, CRLs, roles under `/everest/`, and an account external-access Analyzer
are absent. Empty Analyzer inventory means no analyzer exists, not that there
are zero findings.

The exact IAM names are `/everest/everest-writer-ecmwf-ifs`,
`/everest/everest-writer-noaa-gfs`, `/everest/everest-writer-dwd-icon`,
`/everest/everest-writer-ecmwf-aifs`, `/everest/everest-raw-verifier`, and
`/everest/everest-audit-read-only`. Only the four writers receive disabled
Roles Anywhere profiles named `everest-profile-<source>` with one role each and
`durationSeconds=900`; verifier and audit use an approved human federation
principal and request 900-second sessions, not workload certificates or Roles
Anywhere profiles. Each writer certificate is X.509v3 with digital-signature
usage, client-auth EKU, SHA-256 or stronger, `CA=false`, a unique serial and
UUID, subject CN `everest/<source>/<uuid>`, and first SAN URI
`spiffe://everest/<source>/<uuid>`, where source is exactly `ecmwf-ifs`,
`noaa-gfs`, `dwd-icon`, or `ecmwf-aifs`. UUID values cannot be invented.

Creation order is: establish and test a replacement federated administrator;
set bucket BPA true; prove key/anchor provenance; create the account external
access Analyzer `everest-gatec-external-access` in `ap-south-1`; choose UUIDs
and validate the four trust/identity policies offline; create the four writer
roles under `/everest/`; create verifier and audit roles under `/everest/` from
separately approved human trusts; attach least-privilege identity policies;
merge and validate the named-principal KMS policy while retaining a tested
recovery path; attach the explicit-deny bucket policy; create the four profiles
disabled; import and enable an approved CA-issued CRL; then perform separately
authorized nonproduction QA before any profile enablement. CloudTrail state is
unknown and its deployment remains Block 8. Block 1 stays open; no Block 2 work
is authorized.

## EV-GATEC-OP-RETENTION-002: Block-2 S3 retention architecture

**Assignment:** `EV-GATEC-OP-RETENTION-002-ARCH-DOC`  
**Status:** Architecture only under the Manager Option-3 exception. Block 1
(`EV-GATEC-OP-ACL-001`) remains open with an independent QA **FAIL** and its
residual risks unchanged. Block-2 implementation remains blocked pending
architecture approval, the decisions below, and separate explicit Manager
authorization. Block 3 remains closed. This record made no AWS, raw/`tmp-*`,
PostgreSQL, service, credential, or other runtime mutation.

### Retention decision

Use S3 Object Lock **GOVERNANCE** in nonproduction for reversible control
testing and **COMPLIANCE** in production/shared deployment after an explicit
irreversibility checkpoint. Production Compliance cannot be shortened,
removed, bypassed, or downgraded, including by the account root principal.
Governance bypass is prohibited: no normal role or writer receives
`s3:BypassGovernanceRetention`, and policy boundaries/SCPs should explicitly
deny it where available.

Use a bucket default as a universal floor, then extend exact versions by class:

| Policy class | S3 control |
| --- | --- |
| `failed_or_rejected_raw` | Default 180 days (Governance nonproduction; Compliance production) |
| `operational_raw` | Default 180 days, then retention administrator extends the exact version to 730 days |
| Audit evidence | 1,095 days; use a separately controlled Compliance audit destination when approved |

A 730-day bucket default is rejected because production Compliance could not
be shortened to the approved 180-day failed/rejected period. Writers do not
select retention. An operational artifact cannot become canonically accepted
or be reported retention-compliant until S3 readback confirms the 730-day
extension. Extension failure leaves the version protected by the 180-day floor
and moves it to a blocked state.

For each version, the required retain-until value is the later of S3 version
creation plus the class duration and PostgreSQL `acquired_at` plus that
duration. The existing policy constants map to 180, 730, and 1,095 days; the
Manager must decide whether policy wording means these fixed durations or
calendar months/years before implementation.

### Version, deletion, Lifecycle, and KMS rules

- Bucket, key, and non-null S3 `version_id` form the mandatory storage
  identity. Retention, legal-hold, reconciliation, and disposition operations
  must always name the exact version.
- A delete without a version ID is prohibited: it can return success while
  creating a delete marker that hides, but does not delete, a retained version.
  Delete markers are not WORM-protected and never prove disposition. Inventory
  and reconciliation must enumerate versions and delete markers; an unexpected
  marker creates `drift_blocked` and an alert.
- No expiration or noncurrent-version expiration Lifecycle rule is enabled in
  the initial rollout. Object Lock prevents permanent deletion of protected
  versions but does not prevent Lifecycle from creating delete markers, and a
  bucket policy cannot stop Lifecycle processing. Any future transition-only
  rule requires separate inventory review and approval; automatic disposition
  remains prohibited.
- Object Lock does not protect the KMS key. Ordinary roles are denied
  `kms:DisableKey` and `kms:ScheduleKeyDeletion`. The CMK remains usable until
  every retained version, legal hold, audit obligation, and recovery copy has
  cleared. Any future deletion requires a version-aware zero-dependency
  inventory, separate approval, CloudTrail alerting, and the maximum 30-day
  waiting period. Disabled or pending-deletion KMS state produces
  `kms_access_blocked`; destroying the key is never disposition.
- Retention may only be extended to an approved calculated date. Production
  Compliance shortening/removal is impossible; project policy also prohibits
  Governance shortening/removal even in nonproduction.

### Role separation and exact S3 actions

All grants are constrained to the approved account, bucket, and applicable
prefixes. Human sessions require MFA. Approval and execution identities are
distinct.

| Role | Allowed S3 actions | Explicit exclusions |
| --- | --- | --- |
| Writer (one source prefix each) | `s3:PutObject` only | No retention/legal-hold read or write, bypass, list, read, or delete permissions |
| Retention administrator | `s3:GetObjectRetention`, `s3:PutObjectRetention`, `s3:GetObjectLegalHold`, `s3:ListBucketVersions`, `s3:GetBucketObjectLockConfiguration`, `s3:GetBucketVersioning` | No bypass, legal-hold mutation, delete, bucket Object Lock mutation, or Lifecycle mutation |
| Hold executor | `s3:GetObjectLegalHold`, `s3:PutObjectLegalHold`, `s3:GetObjectRetention`, `s3:ListBucketVersions` | No retention change, bypass, delete, or bucket mutation |
| Disposition executor | `s3:ListBucketVersions`, `s3:GetObjectRetention`, `s3:GetObjectLegalHold`, `s3:DeleteObjectVersion` | No unversioned `s3:DeleteObject`, retention/hold mutation, bypass, bucket/Lifecycle mutation, or KMS administration |
| Audit read-only | `s3:GetBucketObjectLockConfiguration`, `s3:GetBucketVersioning`, `s3:GetLifecycleConfiguration`, `s3:GetInventoryConfiguration`, `s3:ListBucketVersions`, `s3:GetObjectRetention`, `s3:GetObjectLegalHold`, `s3:GetObjectAttributes` | No payload read or mutation |

`s3:PutObjectLegalHold` controls both hold placement and release, so IAM cannot
separate `ON` from `OFF`. A brokered hold executor must require an authenticated
legal/records approval to place a hold and two distinct approvals (legal/records
authority plus the Manager or delegated records owner) to release one. Place,
release, disposition approval, and deletion are separate requests,
transactions, identities, and audit events. Bucket-level
`s3:PutBucketObjectLockConfiguration` and Lifecycle mutation remain restricted
infrastructure-administrator actions and are not assigned to these roles.

S3 object data events are not logged by CloudTrail by default. Block 8 must
enable selectors for the approved bucket, including retention, legal-hold,
object read/write, version listing, and deletion activity. B2 can define and
test expected correlation but cannot claim complete operational audit while
that Block-8 control is absent.

### S3 authority and PostgreSQL projection

S3 object-version retention mode/date and legal-hold status are the WORM
enforcement authority. PostgreSQL is the workflow, approval, correlation, and
query projection; a database `retained` or `held` value is never proof of S3
enforcement. On disagreement, use the more restrictive observed state and
block disposition until reconciliation succeeds.

An additive backend migration should create an immutable
`raw_artifact_storage_version` mapping with `artifact_id`, provider, bucket,
object key, non-null version ID, ETag/checksum, KMS key ARN, observed retention
mode/date, legal-hold status, storage state, first/last verification times, and
policy version. `(bucket_name, object_key, version_id)` is unique. Legacy/local
rows become `storage_unclassified`; migration must not invent S3 identities or
retention facts. Append-only events cover version/default-lock verification,
extension request/result, hold request/result, drift, disposition approval,
delete request/result, and blocked failures. Existing PostgreSQL retention and
audit columns remain policy projections, not substitutes for S3 or CloudTrail.

### State machine

```text
uploaded
  -> default_lock_pending
  -> default_lock_verified_180d
       -> failed_retained_180d
       -> operational_extension_pending
            -> operational_retained_730d
            -> lock_failed / drift_blocked

failed_retained_180d | operational_retained_730d
  -> held -> hold_release_pending -> hold_released -> retained/retained_expired
  -> retained_expired -> disposition_pending_approval
  -> disposition_approved -> delete_requested -> disposed_verified

any state -> drift_blocked | kms_access_blocked
```

Expiry is determined from S3 readback, not database time alone. A hold overrides
expiry and disposition. Disposition requires no active hold, prior independent
approval, an expired exact version, and post-delete verification that the exact
version no longer exists. Hold release and disposition cannot share a
transition; a delete marker cannot complete disposition.

### Rollout, QA, and rollback

Rollout order is: (1) reconcile the authoritative B1 QA FAIL handoff and
residual register; (2) review offline IAM/bucket-policy templates; (3) add and
test the PostgreSQL projection in an authorized disposable database; (4)
implement the version-aware orchestrator; (5) run report-only S3
Inventory/PostgreSQL reconciliation; (6) execute synthetic, non-sensitive
Governance QA in a dedicated nonproduction bucket or prefix; (7) hold the
Manager Compliance irreversibility checkpoint; (8) apply the production
180-day Compliance default only under separate authorization; (9) enable one
writer/prefix canary at a time; and (10) obtain independent B2 QA. Existing raw
and project-root `tmp-*` artifacts are not test inputs.

QA must positively prove default lock, exact version ID, operational extension,
readback, legal hold/release separation, expired approved exact-version delete,
DB/S3 correlation, and audit retention. Negative tests must prove that writers
cannot read/change/delete; retention admin cannot shorten, bypass, hold, or
delete; hold executor cannot retain/delete; disposition executor cannot use an
unversioned delete or delete before expiry/under hold; release and disposition
cannot combine; delete markers do not complete disposition; DB-only changes
cannot authorize S3; drift/KMS failure blocks; Lifecycle expiration is absent;
and public APIs expose no storage or retention facts.

Before Compliance, rollback may revoke roles, disable writers, remove an
unapplied/default Governance rule prospectively, and clean synthetic versions
only when Governance retention permits. After Compliance protects a version,
there is no destructive rollback: Object Lock cannot be disabled, versioning
cannot be suspended, and retention cannot be shortened or removed. Recovery is
roll-forward only—stop writers, revoke roles, preserve/extend retention and the
CMK, quarantine scope, and wait for expiry. A database downgrade must not erase
the inventory needed to manage already retained versions.

### Implementation tasks and Manager decisions

| Task ID | Owner | Dependency and handoff |
| --- | --- | --- |
| `EV-GATEC-OP-RETENTION-002-DEC-01` | Everest Manager | Decide the items below; update management decisions/board outside this assignment |
| `EV-GATEC-OP-RETENTION-002-B1DEP-02` | Manager + B1 owner + QA | Reconcile B1 QA FAIL/residual register; update the B1 QA handoff and test plan |
| `EV-GATEC-OP-RETENTION-002-IAM-03` | Release/platform AWS owner | After DEC-01/B1 dependency; hand off reviewed IAM/bucket controls and runbook |
| `EV-GATEC-OP-RETENTION-002-DB-04` | Backend | Add version projection/events; update `docs/api/API.md` |
| `EV-GATEC-OP-RETENTION-002-SVC-05` | Backend | After IAM-03/DB-04; add fail-closed orchestration; update API handoff |
| `EV-GATEC-OP-RETENTION-002-S3-06` | Release/platform AWS owner | Separately authorized Governance QA and Compliance rollout; return sanitized operational evidence |
| `EV-GATEC-OP-RETENTION-002-AUD-07` | Release/platform + audit owner | Define Block-8 CloudTrail selectors, 1,095-day audit control, correlation, and alerts |
| `EV-GATEC-OP-RETENTION-002-QA-08` | QA | Independently execute the positive/negative matrix; update `docs/qa/test-plan.md` and a B2 QA handoff |
| `EV-GATEC-OP-RETENTION-002-CLOSE-09` | Everest Manager | Accept/reject B2 without changing B1 status; Block 3 opens only by later explicit decision |

At architecture approval, implementation was gated on the Manager deciding:
fixed-day versus calendar
period semantics; named legal authority and second hold-release approver;
brokered versus direct hold execution; dedicated nonproduction bucket versus
prefix; acceptance of the 180-day production Compliance floor plus 730-day
extension; whether production may retain a synthetic Compliance canary or use
Governance synthetic evidence followed by a controlled real canary; the audit
destination and 1,095-day Compliance policy; KMS recovery/deletion authority;
the authoritative B1 QA residual record; and separate B2 implementation
authorization. Those decisions and the staged B2 authorization were later
supplied in `docs/management/decisions.md`; the offline foundation below does
not consume or waive any still-open B1 residual.

### EV-GATEC-OP-RETENTION-002-OFFLINE foundation

**Status (2026-08-24):** Offline B2 policy/resource contracts implemented under
the later Manager implementation authorization. No AWS, PostgreSQL, service,
raw/`tmp-*`, credential, private-key, Git, Docker, or canary operation was
performed. Governance provisioning is the next separate task; B3 remains
closed.

The inert contracts, validator, tests, human runbook, rollback warnings, and
sanitized evidence checklist are under
`infra/aws/gate-c-operational/retention/`. They pin the exact Governance QA and
Compliance audit buckets/defaults, keep the one-object production Compliance
canary disabled until Governance QA PASS, deny Governance bypass/unversioned
delete/Lifecycle mutation, preserve KMS survivability, require exact non-null S3
version IDs, and leave legal hold and disposition without usable authority.

The additive PostgreSQL projection and application state-machine implementation
contracts are normative at
`docs/architecture/EV-GATEC-OP-RETENTION-002-backend-contract.md`. They preserve
S3 as enforcement authority, PostgreSQL as a projection, and inward dependency
direction. This architecture task changes no `apps/api` business code.

## Phase A: Data Registry

The data registry is a backend-owned modular monolith boundary. It establishes
approved-source metadata, lifecycle status, configuration-driven scheduling,
and operational health without retrieving external data or implementing a
weather connector.

## Data Flow

`external source -> connector -> raw data -> parser -> normalizer -> QC ->`
`canonical model -> PostgreSQL/PostGIS or object storage -> service -> REST/WS`
`-> frontend`

Phase A implements only the registry/configuration foundation before the
connector portion of this flow. The frontend must never call an external source.

## Canonical Weather Contract Authority

There is exactly one normative weather-contract path:
`docs/meteorology/weather-spec.md`. It is the semantic authority for weather
field meanings, units, nullability, record types, forecast identity,
normalization, and additive QC behavior. Meteorology owns every semantic change
to that contract.

`docs/weather-spec.md` is a compatibility entry point only. It must link to the
normative meteorology handoff and must not define, copy, extend, or provide an
editable alternative weather schema. Transport DTOs, API response shapes,
provider mappings, persistence schemas, and tests implement or verify the
normative contract; none becomes a semantic authority or changes a field's
meaning by implication.

Downstream owners and QA must read the normative meteorology handoff before
implementing, reviewing, or accepting weather behavior. They may use the
compatibility entry point solely to locate that document and must not infer
semantics from the entry point, provider documentation, code, DTOs, API
contracts, or historical evidence. This ADR-008 authority gate is independent
of ADR-009 dependency isolation: a closed owner-neutral ingestion port does not
prove that a provider path exercises the normative weather contract.

## Module Boundaries

### Registry Contract

Defines source identity, descriptive metadata, allowed lifecycle statuses, and
non-secret schedule settings. It has no dependency on FastAPI, ORM, PostgreSQL,
scheduler libraries, HTTP clients, weather connectors, or frontend code.

### Registry Application Service

Registers and updates source definitions, validates status transitions, reads
registry data for future scheduler/API adapters, and updates health through
explicit commands. It coordinates transactions through repository interfaces
and does not contact external data providers.

### Persistence Adapter

Owned by backend under `apps/api/`. It owns PostgreSQL tables, constraints,
indexes, repositories, and reviewed Alembic migrations.

### Scheduler Configuration Adapter

Translates declarative registry settings into future scheduler jobs. Settings
include interval, retry limit, timeout, backoff, misfire behavior, and
concurrency limits. Phase A defines this boundary only: no job execution or
hard-coded source cron behavior is allowed.

### Health and Run History

Tracks current operational health, last success/failure timestamps, bounded
failure details, and append-oriented run history. Health is operational fact,
not verification evidence.

### Future API Adapter

Reserves `GET /api/data-sources` and `GET /api/data-health`. Controllers must
use application services, never repositories or external providers directly.

## Registry Data Model

`data_source_registry` contains the required fields from `AGENTS.md`:
`source_id`, `name`, `provider`, `category`, `status`, `access_method`,
`endpoint`, `format`, `update_frequency`, `spatial_resolution`,
`temporal_resolution`, `coverage`, `license`, `commercial_allowed`,
`credentials_required`, `last_success_at`, `last_failure_at`, and
`health_status`.

It also records UTC `created_at`, `updated_at`, and a metadata version. Source
IDs are stable primary keys. Registry entries begin as `planned` or
`configured`; real connector acceptance is required for `connected` or
`verified`.

`data_source_schedule` holds one schedule per source: enablement, trigger
configuration, interval, retry and timeout settings, backoff settings, misfire
and concurrency settings, and projected run timestamps. Invalid or negative
values are rejected. A schedule is configuration, not execution state.

`data_source_run` is an append-oriented record of source attempts, outcomes,
timings, safe failure data, retryability, and later content hashes. Phase A
creates its schema but does not create actual runs.

Use database constraints for required fields, enumerations, unique source IDs,
foreign keys, and valid numeric ranges. Index source status, health status,
next run time, last success time, and child-table source IDs.

## Configuration and Operations

PostgreSQL is the runtime authority. Version-controlled configuration may seed
or reconcile entries but cannot be a competing runtime source of truth. Secret
values are never stored in registry records; only credential reference names
may be stored.

All configuration must validate as a complete document before it is applied.
Invalid input fails closed without partially replacing active schedules. Only
one future scheduler owner may execute jobs across API processes.

### External Raw-Storage Enforcement

ADR-010 is implemented at the backend raw-persistence edge by
`everest_api.raw_storage.RawStoragePolicy`. Runtime composition must load the
required `EVEREST_RAW_ROOT` environment value and provide the resulting policy
to `WeatherIngestionService`. The configured root must be an existing absolute
directory outside the resolved repository root. Raw object references may be
relative to that root or absolute, but their resolved path must remain beneath
it; empty, traversal, and otherwise escaping references fail closed before a
raw-artifact row is persisted.

This boundary verifies the payload immediately before database persistence: it
requires a regular non-symlink file beneath the approved root and recomputes
SHA-256 against the descriptor. This controlled read/hash check neither writes,
moves, nor deletes payloads. Metadata and checksum-sidecar integrity remains
provider-owned; crossing attestations must be scalar descriptor metadata, not
provider objects. This checkout has no
Git repository metadata, so no repository-exclusion/tracking assertion or
`.gitignore` change is made by this implementation.

### Raw Retention Runtime Boundary

Migrations `0004`–`0006` add explicit retention classification, owner, period,
acquisition and due-date facts, disposition/hold state, and policy version to
raw artifacts. Existing rows are `legacy_unclassified` without invented facts;
new acceptance resolves approved backend defaults. The append-only audit table
uses bounded controlled fields, foreign keys, indexes, and immutable triggers.
The corrective `0006` trigger compares JSON metadata through `::text`, avoiding
unsupported PostgreSQL `json = json` operations while preserving raw identity.
Provider adapters remain neutral and pass scalar factual metadata only. Internal
retention transitions require an actor/role supplied by deployment IAM; local
validation is not ACL enforcement. Gate C remains open pending approved-root
real E2E and QA evidence.

## Migration and Test Strategy

Backend owns reviewed Alembic migrations with upgrade and downgrade tests in a
disposable PostgreSQL database. Autogenerated migrations require manual review.

QA coverage must include contract validation, lifecycle transitions, idempotent
registration, secret redaction, schedule validation, persistence constraints,
migration upgrade/downgrade, transaction rollback, and scheduler-adapter
configuration translation using a fake scheduler. Phase A must not test GRIB,
NetCDF, providers, weather normalization, QC, or frontend behavior.

## Phase A Exit Criteria

- Architecture defines the registry, schedule, run-history, and API boundaries.
- Approved source metadata can be represented without invented source facts.
- Scheduler configuration is declarative and has no connector execution.
- Lifecycle status and health state remain distinct.
- Persistence migration and test expectations are documented.
- No Phase B weather schema or Phase C-F connector work has begun.

## ADR-009 Implementation: Owner-Neutral Weather Ingestion Contract

### Context

The existing provider ingestion adapters in `services/weather/gfs/` and
`services/weather/icon/` import DTOs from `everest_api.weather.contracts` and
each redeclare an equivalent ingestion protocol. That dependency direction
makes meteorology depend on the backend application package and allows backend
contract changes to leak into provider adapters.

### Decision

`packages/weather_ingestion_contract/` is the new owner-neutral, standard
library-only boundary package. Its importable API is:

```python
from weather_ingestion_contract import (
    AuxiliaryArtifactReference,
    CanonicalRecordInput,
    IngestionPort,
    PrimitiveValue,
    RawArtifactDescriptor,
)
```

`RawArtifactDescriptor` is the immutable primary raw-artifact identity and
provenance command. `CanonicalRecordInput` carries the existing canonical
weather fields, their units, source/model provenance, forecast identity, and
additive QC flags without transformation. `AuxiliaryArtifactReference` carries
an optional separately retained artifact plus a backend-interpreted role (such
as `static_altitude`). `IngestionPort.ingest(primary_artifact, records,
auxiliary_artifacts=()) -> UUID` is the sole persistence port.

The package imports only the Python standard library (`collections.abc`,
`dataclasses`, `datetime`, `typing`, and `uuid`). In particular, it must never
import FastAPI, SQLAlchemy, HTTP clients, ecCodes, `apps.api`, `everest_api`, or
provider parser/connector types. Raw metadata is deliberately limited to a
mapping of string keys to scalar primitive values (`str`, `int`, `float`,
`bool`, or `null`). `RawArtifactDescriptor` validates both keys and values at
construction time, so unsupported nested containers and provider/vendor
objects are rejected before an adapter can invoke the persistence port.

The normative field semantics remain in
`docs/meteorology/weather-spec.md`; this package does not duplicate QC or
normalization rules. The contract is intentionally a transport DTO/port, not a
second canonical-weather model.

### Dependency Direction

```text
provider connector/parser/normalizer (meteorology)
    -> weather_ingestion_contract (DTOs + Protocol)
    <- backend persistence implementation (backend)
```

Composition may inject a backend `IngestionPort` implementation into a provider
adapter, but provider modules must not import backend application or persistence
modules. The backend similarly must not import provider parser types. The
contract package has no dependency on either side.

### Consequences and Migration Tasks

This removes a cross-owner import and consolidates the duplicated port, at the
cost of a small separately packaged compatibility surface. The package is
deliberately narrow: it adds only metadata-boundary validation; it does not add
serialization, retries, or a provider abstraction that would obscure
provider-specific provenance rules.

**Backend migration (owner: backend):**

1. Replace `everest_api.weather.contracts` DTO imports with the shared package
   imports and remove the duplicate DTO definitions after all consumers migrate.
2. Change `WeatherIngestionService.ingest` to structurally implement
   `IngestionPort`, accepting `auxiliary_artifacts`; preserve its existing raw
   retention, deduplication, provenance validation, transaction, and QC
   behavior.
3. Translate the existing `StaticAltitudeArtifactReference` at the backend
   edge into `AuxiliaryArtifactReference(role='static_altitude', ...)` and keep
   the existing strict same-source/same-cycle/step-zero validation there.
4. Update backend migration/API composition tests to assert the shared contract
   is used without changing public weather-field meanings or response shapes.

**Meteorology migration (owner: meteorology):**

1. Replace imports from `everest_api.weather.contracts` in GFS and ICON
   adapters with `weather_ingestion_contract`; delete each locally redeclared
   `WeatherIngestionPort` and use `IngestionPort`.
2. Preserve every existing lossless mapping: null weather values, ordered QC
   flags, source/model identity, cycle, lead seconds, valid time, spatial key,
   and raw metadata.
3. Update IFS and future AIFS adapter composition to use the same port. Supply
   auxiliary references only when a separately retained artifact is factual
   provenance for the records.
4. Run adapter tests and add a dependency-direction check that provider modules
   do not import `apps.api` or `everest_api` before declaring ADR-009 complete.

ADR-009 remains only structurally implemented by this task. It is not verified
for provider-to-database ingestion until the two owner migrations and their QA
evidence are complete.

## EV-DATA-001-F Amended Delivery Boundary

### Context

The EV-DATA-001 A-F delivery is a backend data-delivery boundary. Its stop
criterion is evidence that each approved forecast source can complete the
source-to-service path: official retrieval, parsing, normalization, QC,
persistence, and queryable Everest REST/WS API results. A frontend display is
not required to demonstrate that this path works and is outside the scope of
this delivery.

### Decision

The delivery boundary is amended as follows:

- API evidence is the stop criterion for EV-DATA-001 A-F. Evidence must cover
  the persisted, queryable results and real health state exposed by the
  backend service APIs; source presence or connector configuration alone is
  insufficient.
- Frontend implementation and display are deferred to a separate, future
  governed delivery. The current delivery must not create new UI or add
  frontend consumers for the forecast sources.
- Provider isolation remains mandatory. Each of ECMWF IFS, NOAA GFS, DWD ICON,
  and ECMWF AIFS retains an independent connector/parser/normalization path,
  with the owner-neutral ingestion contract and canonical weather semantics
  described above. No frontend or provider adapter may bypass the backend
  service boundary.
- When frontend work is later authorized, it must pass the project's full
  delivery stages and their applicable reviews, implementation, QA, and
  release gates. It may consume data only from Everest-owned REST/WS APIs,
  never directly from ECMWF, NOAA, DWD, or any other external source.

The architecture for the EV-DATA-001 source integrations and canonical weather
core is therefore reconciled and closed. No further architecture work is
required for source/core boundaries, provider isolation, or the deferred
frontend decision. Remaining source/core activity is implementation,
real-data evidence, tests, documentation, and review against the already
defined contracts and acceptance gates; it must not be treated as a new
architecture phase.

### Consequences

This permits EV-DATA-001 to conclude on independently verifiable backend API
evidence without coupling delivery to a visualization. It preserves the
external-source isolation rule and avoids prematurely fixing a frontend
contract through UI assumptions. The deferred frontend delivery will incur a
later integration and QA cost, but its boundary is explicit: the backend REST/
WS contracts are the only permitted input path, and no provider credentials or
external-source access belongs in the frontend.

## EV-UI-001 Frontend Architecture

**Status:** Proposed (append-only update for delivery line EV-UI-001)
**Delivery:** EV-UI-001 — Frontend UI, Milestone 1: Weather/Forecast Display
**Inputs:** `docs/product/PRD.md` v0.2 (ADR-017/ADR-018), `docs/api/API.md`,
`docs/meteorology/weather-spec.md` (normative weather contract),
`docs/everest-aoi.md`, `AGENTS.md`
**Owners:** frontend leads; gis-3d owns `apps/web/src/cesium*` and
`apps/web/src/map*`; backend and meteorology are consulted, not changed
(AC-09: zero contract/semantic changes).

### Context

EV-UI-001 builds the first human-readable surface over the five Everest-owned
REST APIs produced in EV-DATA-001 A-F. The MVP is a read-only 3D weather/
forecast display: a CesiumJS baseline scene centered on the approved AOI,
canonical weather panels, a Summit Window presentation panel (scoreboard,
ladder, disagreement, provenance, time animation), and truthful source/health
rendering. It consumes exactly the five documented endpoints, invents no
endpoints, data, geometry, or verification, calls no external provider, and
ends at QA-accepted validation against a controlled environment (release stays
blocked by Gate C-Operational). The five scope expansions adopted in ADR-018
(scoreboard, time animation, click-to-provenance, camp altitude ladder, model
disagreement) are all presentation-layer derivations over canonical values and
never Risk/AI/derived records.

```text
Browser (Next.js, React, CesiumJS)
  |
  |  only Everest-owned REST (five endpoints), X-Correlation-ID per request
  v
FastAPI (apps/api) -> PostgreSQL/PostGIS (canonical model)
  |
  ^  never: ECMWF, NOAA, DWD, or any external provider
```

### 1. Module Boundaries and Ownership

`apps/web` does not exist yet; the following structure is the proposed
implementation boundary. It respects the AGENTS.md ownership globs exactly:
`apps/web/src/cesium*` and `apps/web/src/map*` are gis-3d-owned; everything
else under `apps/web/src` is frontend-owned. The map never fetches HTTP; panels
own all fetching through the shared API client.

| Proposed path under `apps/web/` | Owner | Responsibility |
| --- | --- | --- |
| `src/cesium/*`, `src/map/*` | gis-3d | Scene init, default camera, AOI polygon rendering, record markers, WebGL fallback, scene smoke test (FR-MAP-001–007) |
| `src/app/*` | frontend | Next.js App Router layout and route(s), page composition, loading shells |
| `src/api/*` | frontend | Typed API client for the five endpoints, contract validation, X-Correlation-ID |
| `src/components/panels/*` | frontend | Current, Forecast, Profile, Summit Window, Scoreboard, Ladder, Disagreement, Sources/Health, Provenance, Error/Empty/Loading states |
| `src/components/layout/*` | frontend | Header, chrome, accessibility scaffolding |
| `src/lib/*` | frontend | Pure logic: `geo.ts` (WGS-84 geodesic), `utc.ts` (RFC 3339 Z), `units.ts`, `forecast.ts` (valid-time/cycle grouping), `summit.ts` (basis selection + bands + scoreboard), `disagreement.ts` (alignment + min/max/median) |
| `src/state/*` | frontend | Per-panel fetch hooks, refresh policy, active-time state |
| `src/i18n/*` | frontend | Message catalog (`messages.ts`) and typed `t()` accessor (NFR-I18N-001) |
| `src/config/*` | frontend | `env.ts` (API base URL), `summitWindow.ts` (threshold mechanism), `refresh.ts` (interval policy) |
| `public/everest-south-route-v1.0-expanded-2000km.geojson` | gis-3d | Canonical AOI artifact copy, pinned by SHA-256 `b21ce4c8...90ac` (from `docs/everest-aoi.md`) |

Dependency direction: `cesium/*` and `map/*` import the typed contracts and
`lib/geo.ts` from frontend-owned leaf modules and never import panels, state,
or the API client's fetch functions. Panels import the API client and pure
logic only. No module performs HTTP except `src/api/client.ts`. This keeps the
gis-3d scene testable without a backend and keeps every panel renderable
without WebGL (NFR-AVAIL-001, FR-MAP-007).

### 2. Application Structure

- **Next.js App Router** with a single dashboard route (`src/app/page.tsx`)
  inside `src/app/layout.tsx`. There is exactly one page in the MVP; route
  structure stays flat to avoid premature routing.
- **Cesium mounting:** the map is a client-only island. `EverestScene` lives
  under `src/cesium/` and is mounted with `next/dynamic(..., { ssr: false })`
  so the CesiumJS bundle is a lazy chunk and never blocks initial load
  (NFR-PERF-001). The page renders the scene plus the data panels; the scene
  receives typed, validated records and the active valid time as props, not as
  its own fetches.
- **Lazy-loading boundary:** CesiumJS is the only heavyweight dependency
  (~10+ MB gzipped). Everything else ships in the main chunk. The Cesium chunk
  is loaded only when the scene mounts; WebGL-unsupported clients skip it and
  get the FR-MAP-007 fallback while panels remain functional.
- **State management:** intentionally minimal. No Redux/Zustand/React Query.
  Per-panel fetch state via a small `useApiFetch` hook in `src/state/`
  (`status: idle | loading | success | error`, `data`, `error`,
  `correlationId`, `refetch`). Derived presentation (scoreboard, disagreement,
  ladder, active time) is computed by pure functions in `src/lib/` and memoized
  at the component boundary. Shared cross-panel state is limited to the active
  forecast valid time (lifted to the page, driven by time animation,
  FR-TIME-004) and the validated sources/health payloads reused by the
  provenance panel (FR-PRV-002). No global store is justified for a read-only
  dashboard.
- **Records flow to the scene:** the page passes the current validated records
  and the active forecast time to `EverestScene`; gis-3d renders markers from
  those props. This is the single cross-ownership data handoff.

### 3. Typed API Client

One module, `src/api/client.ts`, owns all HTTP for the five endpoints. It
exposes typed functions `getCurrent`, `getForecast`, `getProfile`,
`getSources`, `getDataHealth` with request types and response contracts derived
from `docs/api/API.md` and the wire shape in
`apps/api/everest_api/app.py::records_payload`.

**CanonicalWeatherRecord contract (client-side):** fields and invariants
follow the normative weather contract (`docs/meteorology/weather-spec.md`) as
constrained by the documented API projection:

- Required: `record_type` (one of `forecast | observation | satellite |
  derived`), `timestamp` (UTC ISO-8601 with trailing `Z`), `latitude`
  (`[-90, 90]`), `longitude` (`[-180, 180]`), `altitude` (finite, m),
  `spatial_key`, `source`, `model`.
- Nullable core values (null renders as unavailable, never zero/imputed,
  FR-SW-004): `wind_speed` (`>= 0`, m/s), `wind_direction`
  (`[0, 360)` degrees, null for calm), `temperature` (°C), `precipitation`
  (`>= 0`, mm), `visibility` (`>= 0`, m).
- Forecast identity when present: `forecast_cycle` (UTC `Z`),
  `forecast_lead_time` (number, **seconds** from cycle to valid time — the API
  serializes `forecast_lead_seconds` under this key).
- Recommended fields (`pressure`, `relative_humidity`, `dew_point`,
  `cloud_cover`, `cloud_base`, `cloud_top`, `snowfall`, `gust_speed`) are
  rendered only if the backend projection ever includes them; they are optional
  in the client type.

**Validation (NFR-ENG-002):** `src/api/validate.ts` runs on every response.
Unknown fields are ignored; required fields are checked; unit/range/record-type
invariants above are enforced. A record failing required-field validation is
excluded from rendering and counted as a per-source data-quality warning —
never fabricated, never silently corrected. The validator is unit-tested against
fixtures and against real validation-run payloads.

**`quality_flags` wire-key decision (array):** the client contract uses the
plural wire key `quality_flags` (array of strings) exactly as emitted by the
backend and pinned by PRD section 7.2. `docs/meteorology/weather-spec.md`
spells the concept `quality_flag` (singular). **Escalation:** this naming
conflict is escalated to the meteorology and backend owners for reconciliation
in their handoffs; the frontend does not block on it and does not rename the
wire field. Flags are additive labels (`clean`, `missing_value`,
`out_of_range`, `invalid_timestamp`, `invalid_coordinate`, `invalid_unit`,
`duplicate`, `stale`, `provenance_error`, `cycle_time_mismatch`); the UI shows
flagged records, never hides or corrects them (FR-WX-006), and Summit Window
treats any non-clean flag on a basis value as "unavailable" (FR-SW-004).

**X-Correlation-ID:** the client generates a new `crypto.randomUUID()` per
request, sends it as the `X-Correlation-ID` header (FR-ERR-001), and surfaces
the backend's echoed value (response header, echoed even on 422) on error.
Errors are extracted defensively: the documented error envelope
`{ "error": { "code", "message", "correlation_id" } }` (API.md) is parsed when
present; the current FastAPI implementation emits `{ "detail": ... }` on 422.
The client accepts both shapes, maps 422 detail text to the offending
parameter (FR-ERR-002), and the exact observed validation-run error shape is
recorded in the API-client contract tests and flagged to backend for
reconciliation (see section 11).

**UTC-only query rules:** `getForecast` accepts only RFC 3339 timezone-aware
values with an explicit zero offset (`Z` or `+00:00`). `src/lib/utc.ts`
validates client-side before request: naive and non-UTC values are rejected
immediately, and `start > end` is rejected before request (FR-WX-004). The
backend enforces the same rules with HTTP 422; the client treats 422 as an
input-validation error, never a server failure.

### 4. Scene Composition (gis-3d)

Resolves OQ-01 and OQ-02 for the MVP baseline. gis-3d owns the implementation;
the architecture fixes the constraints.

- **Baseline (OQ-01):** CesiumJS on the **ellipsoid only**. No imagery, no
  terrain, no 3D Tiles, no external provider requests (FR-MAP-005/006).
  Everest-owned terrain/tileset consumption is deferred entirely to
  `EV-TERRAIN-001` and must not be consumed in the MVP. The only local static
  scene asset is the canonical expanded-AOI GeoJSON
  (`docs/everest-south-route-v1.0-expanded-2000km.geojson`, ~14 KB, project
  owned; OQ-05: no additional imagery/terrain asset is approved or bundled).
- **AOI rendering (FR-MAP-002):** the scene renders the approved boundary from
  that canonical artifact (a single `Polygon`, WGS 84, GeoJSON
  `[longitude, latitude]` order). Record markers are restricted to records
  whose coordinates pass the **100 km geodesic-membership test** from center
  `27.98806, 86.92528` (WGS-84 ellipsoid geodesic distance `<= 100,000 m`,
  per `docs/everest-aoi.md`); the default camera frames that 100 km operational
  scope. No other geometry is rendered (no route line, no camp points;
  FR-MAP-004).
- **Default camera (OQ-02):** camera located above the AOI center
  `27.98806, 86.92528` looking straight down (heading `0`, pitch `-90`), with
  slant range that frames the 100 km operational radius with margin
  (target ≈ 230 km; exact value is set by gis-3d's scene smoke test and
  recorded in `docs/gis/terrain-spec.md`). Navigation is constrained to the
  scene; zooming out may reveal the full 2,000 km expanded polygon, which is
  the only serialized boundary and remains an overlay, not an operational
  frame.
- **Markers (FR-MAP-003):** markers are placed at record `latitude` /
  `longitude` / `altitude` on the ellipsoid and **deliberately not
  terrain-clamped** (clamping would invent ground height). gis-3d records the
  height-datum approximation (record altitude in metres above mean sea level
  treated as ellipsoid height for the baseline) in the terrain-spec until
  `EV-TERRAIN-001` supplies a geoid/terrain model. Markers are styled by
  `source` and `record_type`; selecting a marker opens the provenance panel
  (FR-PRV-001) with canonical values, units, and UTC time.
- **WebGL fallback (FR-MAP-007):** WebGL2 support is detected before scene
  mount. Without it, the map area renders a clear, accessible fallback message;
  all data panels remain functional, and the non-visual alternative (textual
  table of loaded canonical records, NFR-ACC-002) is always available.

### 5. Component / Data Flows

All panels fetch through `src/api/client.ts`, validate (NFR-ENG-002), and
render one of four states: loading (FR-ERR-004), success, empty (FR-ERR-003),
or error with retry + correlation ID (FR-ERR-001/002). Flows below are
widget-level.

**Current weather (US-02):**

```text
CurrentPanel
  -> getCurrent(source?)  [server cap: <= 100 records, descending valid time]
  200 {records} -> validate() -> [CanonicalWeatherRecord]
    |-- records > 0 -> render list: canonical units, UTC Z, flags (FR-WX-*)
    |-- records == 0 -> EmptyState (FR-ERR-003)
  non-200 / network error -> ErrorState with retry + X-Correlation-ID echo
```

**Forecast timeline + filters (US-03/US-08/US-09):**

```text
ForecastPanel
  -> getForecast({start?, end?, source?})   [UTC Z rules; client pre-validates]
  200 -> validate -> derive distinct valid times + cycles (lib/forecast.ts)
    |-- default view: latest available cycle's lead extent
    |-- source filter chips (IFS/AIFS/GFS/ICON from loaded data)
    |-- UTC time-range filter (validated client-side; 422 mapped to field)
    |-- records == 0 -> EmptyState ("no data for this selection and time range")
  422 -> ErrorState naming the offending parameter (FR-ERR-002)
```

**Profile view + camp ladder (US-04/US-18):** the profile API accepts exactly
one label per call, so the ladder issues six parallel profile queries
(FR-LAD-001):

```text
Ladder
  -> getProfile(EBC), getProfile(C1), ..., getProfile(SUMMIT)   [parallel]
  per label:
    200 + records > 0 -> cell renders actual altitude + canonical values
    200 + records == 0 -> cell empty state with explanation (FR-PRO-004)
    error -> cell unavailable + error hint; never substitutes values (FR-LAD-002)
ProfilePanel (single label via chips)
  -> getProfile(label) -> chart: y = actual record altitude, x = canonical value
  forecast vs observation rendered distinctly, toggleable (FR-PRO-002)
```

**Summit Window panel + scoreboard (US-05/US-15):**

```text
SummitWindowPanel
  -> getCurrent() + getForecast() + getProfile(SUMMIT)   [parallel]
  basis selection (FR-SW-001):
    profile=SUMMIT records present? use them
    else forecast/current records minimizing WGS-84 geodesic distance to
      center (27.98806, 86.92528) within 25 km, tie-broken by highest altitude
    none -> EmptyState (FR-ERR-003)
  values with non-clean quality_flags -> "unavailable" + flag (FR-SW-004)
  scoreboard (FR-SW-006..008):
    band classification via src/config/summitWindow.ts thresholds
    per-source agreement (count of present sources per band)
    staleness from record timestamp and source last_success_at
    labeled non-authoritative; no services/risk, no AI (FR-SW-005)
  degradation (FR-SW-009): compose from successfully loaded inputs only;
    failed inputs listed as unavailable with error hint; no inputs -> empty
```

**Sources / health (US-06/US-12):**

```text
SourcesPanel -> getSources() + getDataHealth()   [parallel]
  table: lifecycle status | operational health | last_success_at | last_failure_at
  lifecycle: planned/configured/connected/verified/degraded/disabled
  health: unknown/healthy/stale/failed/degraded/disabled  (two distinct labeled
  fields per ADR-004; unknown rendered truthfully; presence != verified, FR-SRC-004)
  only public allow-list fields; restricted fields never requested (FR-SRC-005)
```

**Provenance (US-17):**

```text
click any displayed value (map marker, panel cell, ladder cell, scoreboard,
                            disagreement point)
  -> ProvenancePanel (FR-PRV-001):
       record identity: timestamp, source, model, forecast_cycle,
         forecast_lead_time, spatial_key, record_type, quality_flags
       + source lifecycle/health from already-loaded sources/health payloads
         (FR-PRV-002) — no extra fetch, no restricted fields
```

**Model disagreement (US-19):**

```text
DisagreementView (selected valid time + variable in {temperature, wind_speed,
                                                     visibility})
  uses loaded forecast records only — no extra fetch
  alignment (FR-DIS-001): exact valid-time match across sources when present;
    otherwise each source's nearest valid time, labeled as such
  min/max/median across present sources/models only; absent sources noted,
    never imputed; cross-grid/cross-spatial_key comparison disclosed as
    presentation-layer choice (FR-DIS-002)
```

**Time animation (US-16):**

```text
TimeNav (play / pause / step / scrub; keyboard accessible, NFR-ACC)
  extent = distinct valid times present in fetched forecast (clamped to fetched
           extent and active server range, FR-TIME-002/005)
  play advances activeTime over present times only — intermediate timestamps
    are never fabricated (US-16, FR-TIME-005)
  activeTime drives ForecastPanel + EverestScene markers (FR-TIME-004)
  every rendered value at a scrubbed time remains provenance-traceable
```

### 6. State, Caching, and Refresh

Resolves OQ-04.

- **Refresh policy (OQ-04):** read-only MVP uses **manual refresh** as the
  default (a per-panel refresh action and the error-state retry, FR-ERR-001).
  An optional bounded auto-refresh may be enabled by configuration in
  `src/config/refresh.ts`, applied only to `current` and the sources/health
  panels, with a documented minimum interval of 60 seconds and default
  `enabled: false`. Forecast, profile, ladder, and disagreement are refreshed
  only by explicit user action. No polling loop exists for profile calls.
- **Fetch bounds (NFR-PERF-002):**
  - `current`: server cap `<= 100` records; the client renders whatever is
    returned and never paginates (no pagination contract exists).
  - `forecast`: default fetch is unfiltered (latest available cycle's lead-time
    extent for the selected source or all sources, per NFR-PERF-002); the
    client derives distinct cycles from the response and presents the latest
    cycle's extent by default. Assumed validation-dataset bound: `<= ~300`
    records for one latest cycle across all four sources (provider lead grids
    differ — 3/6/12-hourly, FR-DIS-001). A documented guard (threshold
    recorded at M2 against the manager-controlled validation dataset) limits
    rendering to the latest cycle and shows a notice rather than rendering an
    oversized payload; NFR-PERF-002/003 targets are measured against that
    recorded bound (contingent, not self-referential, per PRD section 10).
  - `profile`: exactly one label per call; six calls total for the ladder.
  - `sources` / `data-health`: small registry payloads, no bound needed.
- **No client-side fabrication (FR-ERR-005):** no interpolation, no imputed
  values, no fabricated intermediate timestamps, no cached-fallback data
  rendered as canonical. Missing values render as unavailable with the
  quality flag when present.
- **Caching:** in-memory per-panel React state only. No `localStorage`,
  IndexedDB, or service-worker caching of API data; every render derives from
  validated fetch results, so a manual refresh can never show stale invented
  data. Staleness indicators derive exclusively from record timestamps and
  health fields (FR-ERR-004, FR-WX-007).

### 7. CORS / Environment / Deployment Plan

- **CORS (NFR-SEC-003, OQ-06):** the backend CORS allow-list is configured for
  exactly the documented frontend origin(s) with a minimal allow-list —
  `GET` and `OPTIONS` only, no credentials — injected via backend environment
  (non-secret). Architecture resolves the **pattern**; the concrete origin pair
  is fixed by backend + release before M6: the frontend is served from
  `http://localhost:48237` and the API from `http://localhost:50149` (random,
  non-standard, unallocated, documented — AGENTS.md port rule). The production
  origin is deferred until Gate C-Operational and release are authorized.
- **Environment:** the API base URL is injected at build time as
  `NEXT_PUBLIC_EVEREST_API_BASE_URL` (non-secret, read by `src/config/env.ts`).
  No secrets, API keys, tokens, or credentials exist in the bundle or repo
  (NFR-SEC-001). `env.ts` validates at module load that the value is an
  `http(s)` origin; the AC-02 network-inspection test asserts the built app's
  only fetch targets are that Everest-owned origin.
- **CSP (NFR-SEC-004):** the app ships a Content-Security-Policy with no inline
  scripts and subresource integrity where feasible. Baseline directives:
  `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
  connect-src 'self' <API_ORIGIN>; img-src 'self' data:; font-src 'self';
  worker-src 'self' blob:` (CesiumJS loads Web Workers from `blob:`). Exact
  directives — including whether Cesium's production build requires
  `unsafe-eval` — are verified during implementation and locked at
  `/plan-eng-review`; no CSP decision here is treated as verified until that
  check.
- **Deployment:** standard Next.js production build (`next build` +
  `next start`) on the documented random non-standard port for the validation
  run; `next.config.ts` applies the CSP headers. Release/GA remains blocked by
  Gate C-Operational (ADR-013/ADR-017); this delivery ends at QA-accepted
  validation with teardown.

### 8. i18n Readiness

- All user-facing strings live in a message catalog
  (`src/i18n/messages.ts`, `export const en = { ... } as const`) accessed
  through a typed `t(key)` helper (`src/i18n/t.ts`). No hard-coded UI text in
  components (NFR-I18N-001). Canonical technical labels (units, field names,
  record types, status enums) render from constants shared with the contracts
  so they cannot drift from the canonical vocabulary.
- MVP displays English only. The catalog/typed-key design means a future
  language milestone adds a second catalog and a locale selector without
  component refactoring. A test asserts every key referenced by components
  exists in the catalog.

### 9. Testing Strategy

- **Unit tests (frontend-owned, Vitest + Testing Library):**
  - API client contract validation: required fields, unit/range/record-type
    invariants (NFR-ENG-002), unknown-field ignoring, null handling,
    `quality_flags` array wire key, X-Correlation-ID send + echo surfacing,
    422 mapping (envelope and `detail` shapes).
  - `lib/utc.ts`: RFC 3339 `Z` acceptance; naive/non-UTC/reversed rejection.
  - `lib/geo.ts`: WGS-84 geodesic distance validated against the AOI spec's
    GeographicLib reference values (e.g., 2,000 km vertices at cardinal
    azimuths from `docs/everest-aoi.md`); 100 km membership test and 25 km
    Summit basis selection.
  - State logic: scoreboard bands and per-source agreement, staleness,
    ladder partial degradation (FR-LAD-002), disagreement alignment and
    min/max/median with absent sources (FR-DIS-001), no-fabrication guards.
  - i18n: catalog key completeness.
- **Component tests:** each panel renders happy / nil / empty / error paths;
  empty vs error states are visually and semantically distinct (AC-06);
  provenance panel renders canonical identity + health without restricted
  fields (AC-12); error/empty states are announced (NFR-ACC-003).
- **gis-3d scene smoke test:** mounts `EverestScene` with mocked/absent WebGL
  and asserts the AOI polygon loads from the pinned local artifact, marker
  membership filtering (100 km), no external requests, and the FR-MAP-007
  fallback path. gis-3d owns this test.
- **Controlled validation run (AC-01..AC-14):** per ADR-016 and the PRD M6
  gate — a Manager-authorized assignment with a substantive validation
  objective, an explicit QA plan, a disposable environment, random
  non-standard ports, and a documented teardown procedure. The frontend runs
  against a disposable backend + PostgreSQL populated with real canonical data;
  QA records evidence (including actual record counts, API error shapes,
  latency) in `docs/qa/test-plan.md`; teardown removes the environment and the
  evidence remains as historical disposable acceptance, never current health.
- **AC-02 network inspection:** review/QA inspects the built app's network
  traffic and asserts zero requests to ECMWF, NOAA, DWD, or any external
  provider.
- **Quality gates (AC-10):** `prettier --write`, `eslint`, `tsc --noEmit`
  before delivery per AGENTS.md / NFR-ENG-001.

### 10. Resolved Architecture Decisions (OQ-01..OQ-07)

| OQ | Question | Resolution | Owner |
| --- | --- | --- | --- |
| OQ-01 | Baseline scene composition without external providers | **Resolved:** bare CesiumJS ellipsoid + locally bundled canonical AOI polygon only; no imagery/terrain/tileset; Everest-owned tileset deferred to EV-TERRAIN-001 (section 4) | architect + gis-3d |
| OQ-02 | Default camera and AOI presentation scope | **Resolved (constraints):** camera frames the 100 km operational scope from above the AOI center; exact params recorded by gis-3d in terrain-spec + scene smoke test (section 4) | gis-3d |
| OQ-03 | Summit Window threshold values and basis | **Partially resolved:** mechanism fixed (config-driven, presentation-only, displayed non-authoritative, FR-SW-003/006); **concrete values deferred to UI/design** (owner: product + meteorology) | product + meteorology |
| OQ-04 | Refresh/polling policy | **Resolved:** manual refresh default; optional bounded 60 s auto-refresh for `current` + sources/health only, disabled by default; no polling for forecast/profile (section 6) | architect + product |
| OQ-05 | Project-owned imagery/terrain asset for bundling | **Resolved:** none in MVP; the AOI GeoJSON (~14 KB, project-owned) is the only bundled geometric asset; any future asset requires Manager approval + license/size assessment | Everest Manager + gis-3d |
| OQ-06 | Validation environment origin / CORS | **Resolved (pattern):** disposable local env, random non-standard ports, minimal GET/OPTIONS CORS allow-list injected via backend env; **concrete origin pair recorded by backend + release before M6** (section 7) | backend + release |
| OQ-07 | WebSocket live display | **Resolved:** out of scope for MVP; the five REST APIs are the only data path; live-stream display is a later-milestone decision and is not architected here | architect |

**Escalation note (quality_flag/quality_flags):** the API wire key is
`quality_flags` (array) per `docs/api/API.md` and the backend serializer; the
normative `docs/meteorology/weather-spec.md` spells `quality_flag` (singular).
The PRD pins the wire key; this naming conflict is escalated to the meteorology
and backend owners for reconciliation in their handoffs. The frontend contract
uses `quality_flags` and does not block on the reconciliation.

### 11. Dependencies and Risks

**Dependencies:**

| Dependency | Owner | Status / note |
| --- | --- | --- |
| Five API contracts (frozen) | backend | No backend changes expected (AC-09); the client is built to the documented contract |
| `docs/gis/terrain-spec.md` baseline | gis-3d | **Missing (does not yet exist)** — required to record baseline scene camera/model constraints and the height-datum approximation; flagged to gis-3d |
| Canonical AOI artifact | gis-3d | Exists: `docs/everest-south-route-v1.0-expanded-2000km.geojson` (~14 KB, SHA-256 pinned) |
| Validated API run with real canonical data | backend + QA + Everest Manager | Required for AC-01; Manager-authorized disposable validation run per ADR-016 |
| EV-TERRAIN-001 (terrain/3D Tiles) | gis-3d | **Not a dependency of the MVP**; explicitly deferred |
| EV-SAT-001 and observation lines (AWS/Pyramid) | gis-3d / meteorology | **Not a dependency**; MVP renders only what the five APIs return |

**Open risks (added to PRD section 14):**

- **Error-body envelope discrepancy:** `docs/api/API.md` declares
  `{ "error": { "code", "message", "correlation_id" } }`, while the current
  FastAPI implementation emits `{ "detail": ... }`. The client parses both
  shapes defensively; the discrepancy is flagged to backend for reconciliation
  and the observed shape is recorded during the validation run (non-blocking
  for UI).
- **No retained real-data evidence for 4/5 APIs (R-01):** the UI cannot be
  validated against real data without the Manager-authorized validation run;
  empty/error states are first-class requirements.
- **Sparse baseline scene (R-02) and route/camp expectations (R-03):** explicit
  non-goals; the only geometric overlay is the AOI artifact; terrain and route
  visualization belong to later lines.
- **Scoreboard drift toward Risk/AI (R-04):** prevented by labeling
  (FR-SW-008) and no `services/risk/` integration (FR-SW-005).
- **WebGL availability (R-05) and 3D-canvas accessibility (R-06):** fallback +
  non-visual table (FR-MAP-007, NFR-ACC-002).
- **Health semantics misread (R-09):** lifecycle and health rendered as two
  distinct labeled fields; `unknown` rendered truthfully; presence never
  rendered as verified (FR-SRC-002/004).
- **CORS/env misconfiguration (R-07) and release blocked by Gate C-Operational
  (R-08):** handled by the documented origin pair before M6 and by ending the
  delivery at QA-accepted validation, respectively.

**Items resolved at `/plan-eng-review` (2026-08-24):**

1. **Geodesic implementation (`lib/geo.ts`):** **resolved — in-repo Vincenty
   inverse**, validated against the AOI GeographicLib reference values; no new
   dependency (`geographiclib` npm package not used).
2. **Profile chart rendering:** **resolved — a chart library** (Recharts
   proposed) instead of hand-rolled SVG; dependency addition requires the
   standard AGENTS.md dependency approval/documentation at implementation.
3. **CSP directives** including the Cesium Web Worker / `unsafe-eval`:
   verification at implementation, locked before delivery (not yet verified).
4. **OQ-03 concrete Summit Window threshold values:** deferred to UI/design
   (owner: product + meteorology), mechanism already fixed.
5. **Validation-run fetch bound + observed error-body shape evidence:**
   recorded during the M2/M6 validation run against the manager-controlled
   dataset.
