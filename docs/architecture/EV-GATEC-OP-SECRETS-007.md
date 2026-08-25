# EV-GATEC-OP-SECRETS-007 — Secrets and configuration management

**Assignment:** `EV-GATEC-OP-SECRETS-007`  
**Status:** Implemented 2026-08-25 for the WSL/Docker runtime (ADR-018)  
**Owner:** backend + release

## Principle

Secret values are never stored in the repository, the registry, the API, logs,
or any committed configuration. The runtime reads secrets only from the
operator-controlled environment file (or process environment); the repository
carries non-secret configuration templates and credential *reference names*
only.

## Non-secret vs secret configuration

| Class | Examples | Storage |
| --- | --- | --- |
| Non-secret | Ports (`52147`, `52148`, `56021`), API base URL, source metadata, AOI, policy versions | Committed (`compose.yml`, `.env.example`, `docs/*`) |
| Secret | `EVEREST_DB_PASSWORD`, future provider keys/tokens, CA private keys, AWS access keys | Operator env file `~/.everest/db.env` (chmod 600) or process environment; never committed |

## Implemented controls

1. **Runtime DB password** is supplied via `~/.everest/db.env` (created with
   `umask 077`, `chmod 600`, outside the repository) and consumed by the
   compose file (`${EVEREST_DB_PASSWORD:?}`), the systemd units
   (`EnvironmentFile`), and the backend (`EVEREST_DATABASE_URL` built from it).
   The compose file requires the variable and fails closed if absent.
2. **Frontend** reads only the non-secret `NEXT_PUBLIC_EVEREST_API_BASE_URL`
   (validated origin) from `.env.example`; no credential, token, or provider
   key exists in the client bundle or repo.
3. **Registry** stores only `credential_reference` names (never values); a
   non-null reference requires `credentials_required=true`
   (`everest_api/registry/models.py` check constraint, `validation.py`).
4. **Redaction** (`everest_api/registry/redaction.py`) masks common credential
   patterns in persisted failure details and audit events.
5. **Repository scanning**: `.gitignore` excludes `*.key`, `*.pem`, `*.p12`,
   `credentials`, `.aws/`, and `.env.*` (except `.env.example`); gitleaks runs
   over history with a recorded baseline. Verified clean (0 new leaks).
6. **No hardcoded secret** in any committed source, config, or infra asset;
   the only secret-required env value in committed files is the `${...}` /
   `${VAR:?}` placeholder reference.

## Runtime composition

```text
~/.everest/db.env (chmod 600, operator-only)
  -> docker compose (EVEREST_DB_PASSWORD)
  -> systemd EnvironmentFile (everest-api, everest-scheduler)
  -> EVEREST_DATABASE_URL -> SQLAlchemy session factory
```

Future provider credentials (e.g., a registered ECMWF or NOAA token, or the
writer Roles Anywhere certificates) must follow the same pattern: store in the
operator env file or an approved secret store, reference by name in the
registry, and never commit. Credential rotation/revocation records already
exist for AWS/GitHub and must be maintained (see the credential-incident
records in `docs/management/decisions.md`).

## Acceptance boundary

This covers secrets/configuration management for the WSL/Docker runtime. It
does not open AUDIT-008, QA-009, or RELEASE-010; does not change source/API
contracts; and does not authorize a production shared-deployment secret store.
A production deployment must re-review this boundary against the deployment
platform's native secret handling before RELEASE-010.