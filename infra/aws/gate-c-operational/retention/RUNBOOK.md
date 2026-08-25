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

1. Produce a separately reviewed deployment package from these contracts. The
   future deployment package must have no unresolved placeholders, enabled
   canary, enabled legal/hold/disposition role, Lifecycle rule, wildcard Allow,
   or secret-shaped text. This offline renderer resolves only the supplied KMS
   parameter and is not itself a deployable package.
2. Create the dedicated empty Governance QA bucket with Object Lock enabled at
   creation and Versioning enabled. Configure BucketOwnerEnforced ownership,
   complete Block Public Access, SSE-KMS with Bucket Key, and default
   `GOVERNANCE` retention for exactly 180 days.
3. Attach explicit denies for Governance bypass, unversioned delete, Object
   Lock/Lifecycle mutation, and legal hold. Attach the writer boundary to each
   B1 writer without broadening its put-only prefix policy.
4. Create `retention-admin` disabled with approved MFA human trust and only the
   exact policy in this package. Create the legal authority deny-only and the
   no-permission hold/disposition placeholders with no trust or principal.
   Create the disabled audit-read role with approved MFA human trust.
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
- [ ] Legal authority has no trust/human principal and deny-only policy.
- [ ] Hold/disposition executors have no trust and no permissions.
- [ ] Audit role has metadata-only actions and no payload read/mutation.
- [ ] Every synthetic object: opaque correlation ID, byte count, bucket, key,
      exact non-null version ID, mode, retain-until UTC, readback UTC.
- [ ] Positive and negative test IDs/results; AccessDenied error code only,
      with request IDs and credentials/session material redacted.
- [ ] Drift/delete-marker/KMS blocked-state evidence where exercised.
- [ ] Teardown result and retained-version inventory. Never claim deletion of a
      protected version or current production health without readback.
