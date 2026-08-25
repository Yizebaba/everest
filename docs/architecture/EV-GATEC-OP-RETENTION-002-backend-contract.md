# EV-GATEC-OP-RETENTION-002 backend implementation contracts

**Assignment:** `EV-GATEC-OP-RETENTION-002-OFFLINE`  
**Status:** Architecture/specification only; no `apps/api` business code or
database was changed or executed.  
**Dependency:** Offline AWS assets reviewed; Governance provisioning and backend
implementation are separate assignments; B1 residuals remain open; B3 closed.

## Problem and authority boundary

S3 Object Lock on an exact object version is the enforcement authority.
PostgreSQL is an additive workflow and query projection. Existing
`weather_raw_artifact` retention fields represent policy intent and cannot
prove S3 mode, retain-until date, legal hold, deletion, or disposition. A
database-only update must never authorize an S3 mutation.

Two implementation options were considered:

1. Add S3 columns directly to `weather_raw_artifact`. This is initially smaller,
   but conflates immutable artifact provenance with a storage version that has
   independent observations and workflow state. It also makes multiple storage
   copies or recovery versions difficult.
2. Add an immutable storage-version mapping plus append-only events. This adds
   one join and more migration work, but preserves dependency direction,
   supports exact S3 identity and reconciliation, and leaves legacy/local rows
   truthful. **Selected.**

## Additive migration contract — backend task DB-04

**Owner:** backend  
**Objective:** Add exact-version S3 projection and events without rewriting,
backfilling invented facts, or weakening existing append-only controls.

Create `raw_artifact_storage_version` with:

| Column | Contract |
| --- | --- |
| `storage_version_id` | UUID primary key |
| `artifact_id` | Required FK to `weather_raw_artifact`, `ON DELETE RESTRICT` |
| `provider` | Required bounded source/provider identity copied only from trusted canonical provenance |
| `bucket_name` | Required non-empty S3 bucket name |
| `object_key` | Required non-empty key; never exposed by public API |
| `version_id` | Required, non-empty, non-`null`; exact S3 version ID |
| `etag` | Nullable bounded readback fact; not treated as a cryptographic checksum |
| `checksum_algorithm`, `checksum_value` | Nullable pair; both null or both present |
| `kms_key_arn` | Required exact key ARN for protected encrypted versions |
| `observed_retention_mode` | `GOVERNANCE`, `COMPLIANCE`, or `UNKNOWN` |
| `observed_retain_until` | Nullable UTC timestamp; required when mode is not `UNKNOWN` |
| `observed_legal_hold` | `ON`, `OFF`, or `UNKNOWN` |
| `storage_state` | One state from the approved machine below |
| `first_verified_at`, `last_verified_at` | Nullable/required according to state; UTC readback timestamps |
| `policy_version` | Required `2026-08-24.b2.v1` for new B2 projections |
| `created_at` | Immutable UTC insertion time |

Required uniqueness is `(bucket_name, object_key, version_id)`. Index
`artifact_id`, `storage_state`, `last_verified_at`, and retain-until for
reconciliation. Constraints reject empty identities, a retain-until without a
known mode, a verified state without verification time, and a disposed state
without a prior successful exact-version delete result.

Create append-only `raw_artifact_storage_event` with event UUID, storage-version
FK, exact bucket/key/version snapshot, event type, result, bounded actor and
correlation IDs, UTC event time, bounded scalar/redacted details, policy
version, and optional S3 request ID. Event types cover:

- `version_observed`, `default_lock_verified`;
- `extension_requested`, `extension_succeeded`, `extension_blocked`;
- `hold_requested`, `hold_succeeded`, `hold_released`, `hold_blocked`;
- `drift_detected`, `kms_access_blocked`, `lock_failed`;
- `disposition_requested`, `disposition_approved`;
- `delete_requested`, `delete_succeeded`, `delete_blocked`;
- `version_absence_verified`, `delete_marker_observed`.

The existing `raw_artifact_audit_event` remains intact. A later reviewed
projection may correlate both event streams; do not rewrite historical events.
Storage events are insert-only by database trigger, and deletes are prohibited.

Migration behavior:

- Existing and local artifacts receive no fabricated bucket, key, version,
  mode, date, hold, KMS, or verification facts. Their effective storage state is
  `storage_unclassified` until an actual S3 exact-version mapping is observed.
- Upgrade is additive. Downgrade may remove empty/new projection structures in
  a disposable test database, but production rollback must first export and
  preserve every exact-version identity. A downgrade must refuse or be
  operationally blocked when protected mappings exist.
- PostgreSQL migration acceptance requires a separately authorized disposable
  PostgreSQL run; SQLite/static SQL is not acceptance evidence.

### DB-04 acceptance criteria

1. Alembic upgrade/downgrade is reviewed and executes on disposable PostgreSQL.
2. Exact triple uniqueness and non-null/non-empty version constraints pass.
3. Legacy rows stay unclassified; no S3 fact is invented.
4. Storage events reject update/delete and unsafe/unbounded details.
5. Trigger/constraint tests prove a DB row cannot skip required state evidence.
6. Public REST/WS schemas remain unchanged and leak no bucket/key/version/KMS or
   retention facts.
7. `docs/api/API.md` and backend handoff are updated before service work.

## Application state-machine contract — backend task SVC-05

**Owner:** backend  
**Objective:** Implement a framework-neutral, fail-closed orchestrator through
ports. It does not embed an AWS SDK in domain policy.

### Ports

- `ObjectVersionRetentionPort`: get exact-version retention, extend to an
  approved calculated date, get exact-version legal hold, enumerate versions
  and delete markers for reconciliation.
- Future methods for put legal hold and delete exact version remain absent or
  hard-disabled in this authorization.
- `StorageVersionRepository`: append mapping observations and events, perform
  compare-and-set state transitions, and never represent intent as S3 success.
- `Clock` and `ApprovalRepository`: injected. Database/current wall time alone
  cannot establish S3 expiry or approval.

AWS SDK, IAM, HTTP, ORM, and FastAPI types stay in adapters. Application commands
carry `artifact_id`, bucket, key, non-null exact `version_id`, actor,
correlation ID, expected prior state, and policy version. The application
rejects an empty/`null` version before invoking any adapter.

### Enabled foundation transitions

```text
uploaded -> default_lock_pending -> default_lock_verified_180d
default_lock_verified_180d -> failed_retained_180d
default_lock_verified_180d -> operational_extension_pending
operational_extension_pending -> operational_retained_730d
```

Any readback disagreement moves to `drift_blocked`; inaccessible KMS-encrypted
content moves to `kms_access_blocked`; missing/invalid default retention or
failed extension moves to `lock_failed` or `drift_blocked`. The more restrictive
observed state wins. Operational canonical acceptance is blocked until exact S3
readback proves retain-until is at least the later of version creation + 730
fixed days and `acquired_at` + 730 fixed days.

Hold placement/release remain disabled until named legal authority, independent
Manager approval, separate executor trust/permission, and broker workflow are
authorized. Disposition approval and deletion remain disabled throughout this
authorization. No transition may combine hold release and disposition.

Future disposition must require S3-observed expiry, no active/unknown hold,
independently persisted approval, exact-version delete, and post-delete proof
that the version is absent. An unversioned delete, delete marker, database-only
completion, KMS destruction, or missing readback never completes disposition.

### SVC-05 acceptance criteria

1. Deterministic unit tests use ports/fakes and prove no SDK/framework import in
   inner policy/application modules.
2. Every command rejects missing bucket/key/version/correlation facts before a
   port call.
3. 180-day default and 730-day extension use fixed-day UTC arithmetic and later-
   of version-created/acquired semantics.
4. S3 success is recorded only after exact-version readback.
5. Drift, delete marker, unknown hold, extension failure, and KMS access failure
   block rather than infer success.
6. Hold and disposition commands are absent or return a typed disabled result;
   no S3 mutation is attempted.
7. Transaction/concurrency tests prove expected-state compare-and-set and
   idempotent correlation behavior.
8. Public API responses and existing weather field meanings remain unchanged.

## Handoffs and sequence

1. Platform/release reviews the offline contracts and provisions only the
   dedicated Governance resources under a separate task.
2. Backend completes DB-04 and updates `docs/api/API.md`.
3. Backend completes SVC-05 after DB-04 and reviewed Governance identity
   contracts; no legal hold/disposition implementation opens implicitly.
4. QA independently executes the B2 matrix and records sanitized evidence.
5. Production canary remains a separate post-QA Manager gate. B3 does not open.
