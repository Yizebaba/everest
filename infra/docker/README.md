# Everest containers

This Compose project keeps the default startup database-only. FastAPI and
Next.js use the opt-in `app` profile; the one-pass forecast scheduler uses the
`jobs` profile. A normal database startup adds no application listener or job.

## Prerequisites

- Docker Engine with Docker Compose v2.
- `EVEREST_DB_PASSWORD` set in the shell or an ignored local environment file.
  Compose intentionally has no default database password.
- External Docker volumes named `everest_raw_data` and
  `everest_derived_data`, owned by UID/GID `10001` for scheduler writes.

Create and initialize the external volumes once before using either profile:

```sh
docker volume create everest_raw_data
docker volume create everest_derived_data
docker run --rm -u 0 \
  -v everest_raw_data:/raw -v everest_derived_data:/derived \
  python:3.13-slim chown -R 10001:10001 /raw /derived
```

The raw directory retains provider payloads. The derived directory holds
materialized wind-field frames. The API mounts derived data read-only; the
scheduler mounts both directories read-write.

## Start PostgreSQL only (default)

From the repository root:

```sh
docker compose -f infra/docker/compose.yml up -d
```

PostgreSQL binds only to `127.0.0.1` on `EVEREST_DB_PORT` (default `56021`).
Inside Compose, application processes always use `postgres:5432`.

## Start the API

```sh
docker compose -f infra/docker/compose.yml --profile app up -d --build
curl http://127.0.0.1:52147/healthz
```

The `app` profile runs a one-shot Alembic migration, then starts API and web.
The browser-facing API origin is embedded into the Next.js bundle at build time
and supplied again at runtime so `next.config.mjs` emits the matching CSP.
Override it before building if the browser does not reach the API at
`http://localhost:52147`:

```sh
NEXT_PUBLIC_EVEREST_API_BASE_URL=https://api.example.test \
EVEREST_CORS_ALLOWED_ORIGINS=https://web.example.test \
docker compose -f infra/docker/compose.yml --profile app up -d --build
```

`EVEREST_CORS_ALLOWED_ORIGINS` is the browser page origin, not the API origin.
The API waits for the migration service and its health check uses `/readyz`.

`NEXT_PUBLIC_CESIUM_ION_TOKEN` is optional and browser-visible by design. Use
only a URL/asset-restricted public `assets:read` token; never a private token.

Set `EVEREST_API_PORT` to another free host port if `52147` is occupied. The
container health check always probes the internal `/healthz` endpoint on
`52147`.

## Run one scheduler pass

```sh
docker compose -f infra/docker/compose.yml --profile jobs run --rm scheduler
```

The jobs profile runs the same one-shot migration first. The worker then runs
`apps/api/schedule_forecast.py` once and exits with that program's status. IFS
and GFS are enabled; AIFS and ICON are explicitly disabled. The worker is
capped at 8 GiB memory. Re-run the command from an external scheduler when
another pass is required; this container does not contain a timer or daemon
loop.

## Build and configuration checks

```sh
docker compose -f infra/docker/compose.yml config
docker compose -f infra/docker/compose.yml --profile app --profile jobs build
```

API and scheduler images run as the non-root `everest` user (UID/GID `10001`);
the web image runs as the base image's non-root `node` user. Application
services drop Linux capabilities in Compose. Database credentials enter only
API/worker containers at runtime; no database credential is copied into images.
