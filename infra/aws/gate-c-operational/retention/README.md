# Block-2 offline retention foundation

**Assignment:** `EV-GATEC-OP-RETENTION-002-OFFLINE-FIX-RETRY`  
**Status:** B2 offline review remediation complete; independent review pending.
No AWS mutation or current operational control is claimed.

This directory encodes the Manager-authorized B2 boundaries without providing
an apply/deploy command. The JSON files are policy and resource contracts, not
CloudFormation, Terraform, or evidence that a resource exists. The Python tools
read and write local JSON only and import no AWS SDK.

## Boundaries

- Governance QA: exact bucket
  `zhufengxiangmu-b2-qa-982408502231`, `ap-south-1`, Object Lock and Versioning
  at creation, default `GOVERNANCE` 180 fixed days.
- Audit: exact bucket `zhufengxiangmu-audit-982408502231`, `ap-south-1`, Object
  Lock and Versioning at creation, default `COMPLIANCE` 1,095 fixed days.
- Production canary: exact existing candidate bucket `zhufengxiangmu`, one
  synthetic object, no more than 1 KiB, exact non-null version ID,
  `COMPLIANCE` 180 fixed days. It is disabled and blocked until independent
  Governance QA passes and the Manager separately authorizes execution.
- Accepted operational raw requires exact-version readback and extension to
  730 fixed days. A database value is never proof of S3 enforcement.
- Writers have no retention, hold, read, delete, version-delete, bypass, Object
  Lock, or Lifecycle mutation authority. The separate writer boundary is an
  explicit deny and must accompany—not replace—the B1 prefix-scoped put-only
  policy.
- Legal authority, hold executor, and disposition executor roles are absent and
  are not rendered as IAM resources. Disposition remains prohibited throughout
  this authorization. `everest-retention-admin` and its broker are uncreated
  until the independent Governance QA activation gate.
- There are no Lifecycle rules. Unversioned delete and Governance bypass are
  explicitly denied. Every retention, hold, reconciliation, and future delete
  operation must carry bucket, key, and a non-null exact version ID.
- The CMK must survive every protected version, hold, audit obligation, and
  recovery dependency. Key destruction is not disposition.

## Offline use

From this directory, future reviewers may run:

```powershell
python validate_assets.py
python -m pytest -q test_validate_assets.py
black --line-length 80 --check render_assets.py validate_assets.py test_validate_assets.py
pylint render_assets.py validate_assets.py test_validate_assets.py
```

Rendering always requires a fully resolved config: exact same-account
`ap-south-1` KMS key ARN and named broker-executor/audit role ARNs. It renders
every JSON contract, resolves the exact Governance bucket and all declared
parameters, and rejects any placeholder in any output. It does not call AWS and
does not prove that an ARN exists or that the key is customer-managed.

## Official references recorded for the future operator

These current official AWS references were consulted during the offline
remediation on 2026-08-25:

- <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObjectRetention.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObjectLegalHold.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html>
- <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html>
- <https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html>
- <https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html>

Before provisioning, the AWS owner must consult the current official versions
and record any changed API, IAM action, or irreversibility semantics. The
integration cannot be called verified until actual readback and independent QA.
