# EV-GATEC-OP-ACL-001 — Block 1 QA Handoff Evidence Package

**Prepared:** 2026-08-24 (Everest Manager session)  
**For:** Independent QA (`EV-GATEC-OP-QA-009` dependent)  
**Status of source work:** Block 1 human paths COMPLETE and verified; awaiting
independent QA verdict.

This package is sanitized. It contains no MFA codes, access keys, secrets,
session tokens, or private-key material. All evidence is already recorded in
`docs/management/decisions.md`; this document is the QA entry point.

## 1. Scope

Block 1 of `EV-GATEC-OP-ACL-001` operational identities and raw-root ACL/IAM
for account `982408502231`, Region `ap-south-1`:

- S3 raw bucket security posture
- Customer-managed KMS key and final least-privilege key policy
- IAM Roles Anywhere trust anchor, profiles, and four writer workloads
- MFA-protected human administration (ADR-016), verifier, and audit roles
- Operator least-privilege (read-only) path
- Nonproduction positive/negative authorization test evidence

## 2. Resource inventory (exact identifiers)

| Resource | Identifier |
| --- | --- |
| Raw bucket | `zhufengxiangmu` (ap-south-1) |
| Customer-managed CMK | `arn:aws:kms:ap-south-1:982408502231:key/3ea2b50b-fab0-4b50-b1e0-7a0f464396b0` |
| Trust anchor | `arn:aws:rolesanywhere:ap-south-1:982408502231:trust-anchor/f66ffa5e-1cef-4938-8c2c-b14e078eb84e` (name `zhufengxiangmu`, `CERTIFICATE_BUNDLE`, enabled) |
| CRL | `arn:aws:rolesanywhere:ap-south-1:982408502231:crl/c80b2c2f-7074-41b3-a912-d0d9e2d931df` (name `everest-root-ca`, enabled) |
| Writer profiles (disabled) | `everest-profile-ecmwf-ifs` (`.../profile/750c5739-...`), `everest-profile-noaa-gfs` (`.../2dea93d3-...`), `everest-profile-dwd-icon` (`.../cb2e2f7f-...`), `everest-profile-ecmwf-aifs` (`.../c93a3906-...`) |
| Writer roles (`/everest/`) | `everest-writer-ecmwf-ifs`, `everest-writer-noaa-gfs`, `everest-writer-dwd-icon`, `everest-writer-ecmwf-aifs` |
| Human roles | `/everest/admin/everest-gatec-administrator`, `/everest/everest-raw-verifier`, `/everest/everest-audit-read-only` |
| MFA device | `arn:aws:iam::982408502231:mfa/everest-gatec-operator-mfa` (bound to `everest-gatec-operator`) |
| Operator user | `everest-gatec-operator` (no managed policies; read-only inline policy only) |
| Access Analyzer | `EverestGateC` (account analyzer, ACTIVE, zero findings) |
| Writer certificates | `C:\Users\Hongke\AppData\Local\Temp\opencode\everest-pki\<source>\` (issued from approved local CA; 30-day validity) |

## 3. Test evidence

### 3.1 Operator read-only configuration verification (`verify_operator_reads.py`)

`infra/aws/gate-c-operational/acl/verify_operator_reads.py --execute` as
`everest-gatec-operator`: **9/9 exit 0** — caller identity, bucket location,
versioning, object-lock capability, public-access block, ownership, encryption
(SSE-KMS exact key + Bucket Key), CMK metadata (`KeyManager=CUSTOMER`,
enabled, symmetric, single-Region), trust anchor (enabled, CERTIFICATE_BUNDLE).

### 3.2 Nonproduction S3 authorization matrix (writer `everest-writer-ecmwf-ifs`)

| Test | Result |
| --- | --- |
| `PutObject` own prefix + exact SSE-KMS | PASS |
| `PutObject` cross-prefix (`noaa-gfs/`) | AccessDenied |
| `GetObject` own object | AccessDenied |
| `DeleteObject` own object | AccessDenied |
| `PutObject` without SSE | AccessDenied (bucket policy explicit deny) |
| `ListObjectsV2` bucket / own prefix | AccessDenied |

### 3.3 Revocation enforcement

- Revoked test certificate → CreateSession denied with
  `AccessDeniedException: Certificate revoked`.
- Non-revoked writer certificate → authenticated (not flagged by CRL).

### 3.4 MFA human-path login test (3/3 PASS)

| Role | Result | Assumed-role ARN |
| --- | --- | --- |
| `everest-gatec-administrator` | PASS | `arn:aws:sts::982408502231:assumed-role/everest-gatec-administrator/admin-login-test` |
| `everest-raw-verifier` | PASS | `arn:aws:sts::982408502231:assumed-role/everest-raw-verifier/verifier-login-test` |
| `everest-audit-read-only` | PASS | `arn:aws:sts::982408502231:assumed-role/everest-audit-read-only/audit-login-test` |

Negative: assume without MFA → `AccessDenied`; expired code →
`MultiFactorAuthentication failed with invalid MFA one time pass code`.

### 3.5 Access Analyzer

- `validate-policy` on all live policies: zero findings (identity, resource,
  KMS, bucket, operator).
- Account analyzer active findings: **empty** after fixing the analyzer
  key-policy read grant (see §5).

### 3.6 Consistency sweep (2026-08-24)

Bucket empty; all four profiles disabled; CRL enabled; trust anchor enabled;
KMS policy named-statements only; operator has read-only inline policy + MFA
only; admin actions (`iam:ListUsers`) denied for the operator.

## 4. Key design corrections recorded (ADR)

1. **ADR-016** — MFA-protected IAM-user-to-role administration (replaces
   external-IdP dependency; no IdP exists in the account).
2. **`acceptRoleSessionName=true` required** — the official `aws_signing_helper`
   always sends the certificate serial as the CreateSession role session name;
   `false` causes `AccessDenied: Unable to assume role`.
3. **KMS final policy** — named admin `kms:*`, operator `kms:DescribeKey`,
   writers (Encrypt/GenerateDataKey/DescribeKey, bucket-key context), verifier
   (Decrypt/DescribeKey); account-principal bootstrap removed via no-lockout
   procedure (admin tested first, then applied by the admin session).
4. **Access Analyzer service-role read grant** added to the KMS key policy
   (`kms:DescribeKey`, `GetKeyPolicy`, `ListGrants`, `ListKeyPolicies`) because
   removing the bootstrap also revoked the analyzer's key-policy read.

## 5. Fixes made during this work

- `s3:GetObjectLockConfiguration` → `s3:GetBucketObjectLockConfiguration` in
  the operator read-only policy template (invalid IAM action).
- KMS `kms:DescribeKey` split from the encryption-context statement
  (`UNSUPPORTED_ACTION_FOR_CONDITION_KEY`).
- Empty CRL rejection: AWS requires at least one revoked certificate.
- Access Analyzer `ACCESS_DENIED` on the CMK: added the analyzer service-role
  read grant.

## 6. Operational notes / remaining

- **CreateSession pacing**: AWS intermittently returns `AccessDenied: Unable to
  assume role` under rapid CreateSession bursts; connectors must pace and retry
  with backoff. Not a configuration defect.
- **CRL renewal**: `nextUpdate` 2026-10-31; a renewed CA-issued CRL must be
  imported before expiry and fully cover protected certificates.
- **Writer certificate rotation**: certs valid 30 days (to 2026-09-23); reissue
  before expiry with the same CN/SAN/UUID bindings.
- Block 2 remains CLOSED. No Object Lock default retention / legal hold /
  disposition is in effect (correct for Block 1).

## 7. QA verification guidance (suggested, read-only)

1. `aws sts get-caller-identity` under profiles `everest-admin`,
   `everest-verifier`, `everest-audit` (MFA prompted locally).
2. `python infra/aws/gate-c-operational/acl/verify_operator_reads.py --execute`
   (operator profile).
3. `python infra/aws/gate-c-operational/acl/validate_policies.py` and
   `pytest infra/aws/gate-c-operational/acl/test_validate_policies.py`
   (22 tests).
4. Re-read the KMS key policy (expect 6 statements, no bootstrap), profile
   states (all disabled), and Access Analyzer findings (empty).

Primary references: `docs/management/decisions.md`
(`EV-GATEC-OP-ACL-001-*` sections), `docs/architecture/architecture.md`.
