# EV-GATEC-OP-AUDIT-008 — Operational audit, observability, and alerting

**Assignment:** `EV-GATEC-OP-AUDIT-008`  
**Status:** COMPLETE 2026-08-25 (service observability + CloudTrail trail)  
**Owner:** release + backend + audit owner

## Scope

Operational audit, observability, and alerting for the Gate C-Operational
runtime: service liveness/readiness, structured monitoring, and AWS CloudTrail
object data-event selectors for the approved storage boundary.

## Service observability (COMPLETE)

- **`GET /healthz`** — process liveness (no dependency probe). Returns
  `{"status":"ok"}`.
- **`GET /readyz`** — readiness: executes `SELECT 1` against the persistent
  database; returns `{"status":"ready"}` or 500 on failure.
- **`apps/api/monitor_service.py`** — probes `/healthz` + `/readyz`, writes a
  structured UTC JSON line to `D:\Everest-data\audit\observability.jsonl`, and
  exits non-zero on failure so an alerting hook can react.
- **systemd timer** `everest-monitor.timer` — runs the monitor every 5 minutes
  (OnBootSec=2min, OnUnitActiveSec=5min).
- **systemd service** `everest-api.service` — `Restart=on-failure`; the API
  serves the health endpoints.
- **Existing** `GET /api/data-health` and `GET /api/weather/sources` report
  persisted source health truthfully (no presence-as-verified).

## AWS CloudTrail object data events (COMPLETE 2026-08-25)

Per `architecture.md` (Block-8) and `EV-GATEC-OP-RETENTION-002-AUD-07`, the
approved buckets now have CloudTrail object data-event selectors.

Created:

- **Audit bucket** `zhufengxiangmu-audit-982408502231` (ap-south-1): Object Lock
  enabled at creation, Versioning enabled, BucketOwnerEnforced, Block Public
  Access all true, SSE-S3 (CloudTrail-compatible, avoids a KMS dependency),
  default Object Lock retention `COMPLIANCE` 1,095 days.
- **CloudTrail trail** `everest-operational-audit`
  (`arn:aws:cloudtrail:ap-south-1:982408502231:trail/everest-operational-audit`),
  single-region `ap-south-1`, `IsLogging=true`.
- **Event selectors**: `ReadWriteType=All`, `IncludeManagementEvents=true`,
  data events for `AWS::S3::Object` on `zhufengxiangmu/`,
  `zhufengxiangmu-b2-qa-982408502231/`, and the audit bucket.
- Bucket policy grants CloudTrail `s3:GetBucketAcl` and
  `s3:PutObject` to `AWSLogs/<account>/*` with `bucket-owner-full-control`.

The trail records retention/legal-hold/read/write/version-listing/deletion
activity on the approved buckets. CloudTrail log delivery has an internal delay
(typically minutes); the trail status confirms logging is enabled. Correlation
with the append-only `raw_artifact_storage_event` / `raw_artifact_audit_event`
records is available for the B2 DB-04 projection.

## Alerting

- Service failure is surfaced by the monitor exit code + audit JSONL line; a
  systemd timer failure or a monitoring alerting hook may consume it.
- Source freshness/health is available through `/api/data-health` for a
  consumer to alert on stale data.
- No SMTP/chat/queue alerting is wired in this assignment; the observability
  record and exit codes are the alerting substrate. Production alerting should
  be selected at RELEASE-010.

## Acceptance boundary

Completes service observability and defines the CloudTrail audit contract.
Does not open QA-009 or RELEASE-010; does not change source/API contracts or
weather semantics; does not authorize release or shared deployment.
