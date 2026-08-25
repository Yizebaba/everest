# EV-GATEC-OP-AUDIT-008 — Operational audit, observability, and alerting

**Assignment:** `EV-GATEC-OP-AUDIT-008`  
**Status:** Service-side observability COMPLETE 2026-08-25; AWS CloudTrail
component requires an MFA admin session (in progress / pending)  
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

## AWS CloudTrail object data events (PENDING MFA admin session)

Per `architecture.md` (Block-8) and `EV-GATEC-OP-RETENTION-002-AUD-07`, the
approved bucket requires CloudTrail selectors for retention, legal-hold, object
read/write, version listing, and deletion activity. Steps:

1. Create a CloudTrail trail for the Everest account/region that logs the
   approved raw/Governance bucket object data events.
2. Use the audit bucket `zhufengxiangmu-audit-982408502231` (Object Lock +
   Versioning + default Compliance 1,095 days per B2 authorization) as the
   CloudTrail delivery destination, or an approved equivalent.
3. Enable `s3:DataEvents` for the exact buckets, and management events for
   retention/legal-hold/lifecycle actions.
4. Verify a test event is delivered and queryable; record sanitized evidence.
5. Correlate CloudTrail `requestID`/object identity with the append-only
   `raw_artifact_storage_event` / `raw_artifact_audit_event` records where
   applicable (B2 DB-04 projection).

Until the trail is created and verified, the runtime does **not** claim
complete operational audit of S3 object data events (per architecture.md:217-221).

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
