# EV-GATEC-OP-RELEASE-010 — Release gate definition

**Assignment:** `EV-GATEC-OP-RELEASE-010`  
**Status:** DEFINED 2026-08-25; defines the gate only, does not authorize any
deployment  
**Owner:** release + Everest Manager

## Purpose

Define the release gate for the Gate C-Operational runtime. Passing this gate
records the decision authority and required evidence; it does not by itself
deploy anything. Any actual shared/production deployment requires a separate,
explicit Manager instruction plus the applicable provider/platform approvals.

## Gate inputs (must all be satisfied)

1. **QA-009 PASS** for the recorded nonproduction runtime (recorded 2026-08-25).
2. **All Gate C-Operational blocks closed or explicitly waived** for the target
   scope:
   - B1 ACL/IAM — PASS (nonproduction evidence).
   - B2 retention — Stage 1-3 PASS; Stage 4 canary and broker/admin activation
     remain separate gated tasks and are **not** release prerequisites for a
     nonproduction runtime.
   - GIT-003, DB-005, RUNTIME-006, SECRETS-007, AUDIT-008 — PASS.
3. **Live runtime health**: API active, `/healthz`/`/readyz` 200, PostgreSQL
   healthy, scheduler + monitor timers active.
4. **CloudTrail delivery confirmed** for at least one object data event on the
   approved buckets (pending check at release time; not confirmed in the QA-009
   window).
5. **No open credential incidents**: GitHub/AWS credential-incident records
   remain CLOSED (rotated, no exposure).
6. **No release-critical findings** outstanding in the security/QA registers.

## Manager release decision

The Everest Manager records an explicit release decision with:

- target scope (nonproduction vs shared vs production);
- approved region/account and deployment environment;
- the exact evidence referenced (QA-009, board, decisions);
- any waivers and their owners;
- effective date and approver;
- rollback/stop conditions.

## Release actions that remain PROHIBITED without separate authorization

- Enabling writer Roles Anywhere profiles.
- The production Compliance canary (B2 Stage 4) and Object Lock default/
  legal-hold/disposition changes.
- Legal-hold placement/release or disposition.
- Everest AWS / Pyramid / satellite / terrain / OSM / AI / Risk / new-UI work.
- Any deployment to a shared or production environment.

## Checkpoint: CloudTrail delivery

Before a shared/production release, confirm the CloudTrail trail delivered at
least one object data event (e.g., an S3 read/write to a test object) for the
approved buckets, and record the delivery timestamp and event ID (sanitized).

## Acceptance boundary

This is the release **gate definition**. It authorizes no deployment. A release
proceeds only after the Manager records the decision above and all gate inputs
are satisfied.