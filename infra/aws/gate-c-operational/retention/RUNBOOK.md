# B2 human provisioning and QA runbook

## Stop conditions

This runbook is a human handoff, not authorization to execute from this offline
task. Stop if any account, Region, bucket, KMS key, actor, approval, QA state, or
exact version ID differs from the approved contract. Never inspect or use
credentials, private keys, existing raw objects, or project-root `tmp-*`.

Before any AWS action, the human operator must:

1. Read current official S3 Object Lock, Versioning, IAM action, and KMS key
   deletion documentation listed in `README.md`.
2. Obtain a separate task authorization for Governance provisioning.
3. Use an approved MFA-protected administrator session and record only the
   sanitized assumed-role ARN, account, Region, approval reference, and UTC
   window. Never record the MFA code, session token, access key, or private key.
4. Reconcile the open B1 QA residual register. B2 does not make B1 pass.
5. Confirm the Governance and audit names are globally available without
   changing them. A name collision blocks and returns to the Manager; do not
   invent a substitute.
6. Confirm the CMK survival owner and tested recovery path. Do not disable or
   schedule deletion of a key used by retained versions.

## Stage 1 — Governance provisioning (next separate task)

1. Render a fully resolved review package from the exact config. Rendering must
   fail for any unresolved output placeholder, unexpected field, missing field,
   invalid ARN, enabled canary, Lifecycle rule, unknown S3 action, wildcard
   Allow, or secret-shaped text. Legal/hold/disposition roles remain absent.
2. Create the dedicated empty Governance QA bucket with Object Lock enabled at
   creation and Versioning enabled. Configure BucketOwnerEnforced ownership,
   complete Block Public Access, SSE-KMS with Bucket Key, and default
   `GOVERNANCE` retention for exactly 180 days.
3. Set the bucket default to `GOVERNANCE` 180 days and read it back. Only after
   exact readback succeeds, attach the explicit bucket-lock-mutation deny plus
   denies for Governance bypass, unversioned delete, Lifecycle mutation, and
   legal hold. This order avoids denying the provisioning call itself. Attach
   the writer boundary without broadening any put-only prefix policy. Configure
   no Lifecycle rule.
4. Do not create legal-authority, hold-executor, or disposition-executor roles.
   Keep `everest-retention-broker` and `everest-retention-admin` uncreated and
   their policies unattached until the Governance QA activation gate below.
   The audit role may be created only from the resolved named MFA trust.
5. Return sanitized configuration readback. Do not upload a test object until
   an independently reviewed Governance QA task authorizes it.

## Stage 2 — Governance QA

QA uses synthetic, non-sensitive, bounded objects only. Every operation records
the exact bucket, object key, and non-null version ID. QA must positively prove
the 180-day default and readback, exact-version 730-day extension, and audit
metadata access. QA must negatively prove writer read/retention/hold/delete/
bypass denial; retention-admin shortening/bypass/hold/delete denial; no-version
delete denial; Lifecycle absence; legal/hold/disposition disabled state; delete
marker rejection; drift blocking; and KMS survival controls.

Retention mutation is never a direct human `PutObjectRetention` call. At the
approved activation gate, perform this exact transition: create the broker with
the approved service/executor trust; create `everest-retention-admin` trusting
only that broker; attach the exact Governance-only policy; prove no human can
assume the admin; enable only the broker command that calculates
`max(version_created_at + duration, acquired_at + duration)`; then prove that
arbitrary dates and `COMPLIANCE` mode are rejected. Failure rolls back by
deleting the unattached roles/policies before any protected test object exists.

Governance mode can permit a sufficiently privileged bypass in AWS, but Everest
policy prohibits all bypass. A failed negative test is a stop condition, not a
reason to weaken a deny. Synthetic versions remain retained until their
retain-until dates and may incur storage cost.

## Stage 3 — production canary (not authorized by this runbook)

Do not enter this stage unless independent Governance QA is PASS and the Manager
issues a separate canary execution authorization that acknowledges irreversible
cost and retention. The contract allows exactly one synthetic object, at most
1 KiB, in `zhufengxiangmu`, with exact-version `COMPLIANCE` retention for 180
days. No legal hold or deletion is allowed.

Compliance retention cannot be shortened, removed, bypassed, or downgraded,
including by the account root principal. The retained canary and its cost cannot
be rolled back before expiry. A mismatch stops before upload; do not create a
replacement or second canary.

## Rollback and irreversible recovery

Before protected bytes exist, rollback can revoke role access, delete unused
policies/roles, and remove an unapplied Governance default prospectively. Once
Governance protects a version, cleanup waits for retention unless a capability
exists that project policy explicitly prohibits using. Once Compliance protects
a version, destructive rollback does not exist. Roll forward by stopping
writers, revoking roles, preserving or extending retention and the CMK,
quarantining scope, recording drift, and waiting for expiry.

Never suspend Versioning or disable Object Lock as rollback. Never destroy a
KMS key to make retained data unreadable. A database downgrade must preserve an
external inventory of every already protected exact version.

## Sanitized evidence checklist

- [ ] Assignment and approval references; operator role ARN; UTC start/end.
- [ ] Account `982408502231` and Region `ap-south-1`.
- [ ] Exact bucket names; creation timestamps; Object Lock enabled at creation.
- [ ] Versioning `Enabled`; default mode/day readback; Lifecycle absent.
- [ ] Ownership, all four Block Public Access values, SSE-KMS, Bucket Key.
- [ ] CMK ARN and sanitized metadata: customer-managed, symmetric,
      encrypt/decrypt, enabled, single-Region. No key policy secret material.
- [ ] Role names, paths, enabled state, trust type, attached policy ARNs/hashes.
- [ ] Legal authority, hold executor, and disposition executor roles are absent.
- [ ] Retention broker/admin are uncreated until the activation transition; after
      activation, admin trusts only broker and cannot be assumed by a human.
- [ ] Audit role has metadata-only actions and no payload read/mutation.
- [ ] Every synthetic object: opaque correlation ID, byte count, bucket, key,
      exact non-null version ID, mode, retain-until UTC, readback UTC.
- [ ] Positive and negative test IDs/results; AccessDenied error code only,
      with request IDs and credentials/session material redacted.
- [ ] Drift/delete-marker/KMS blocked-state evidence where exercised.
- [ ] Teardown result and retained-version inventory. Never claim deletion of a
      protected version or current production health without readback.
