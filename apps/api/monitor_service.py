"""Everest AUDIT-008 observability monitor: probe API liveness/readiness and
the persistent database; write a structured audit record and exit non-zero on
failure so a systemd timer / alerting hook can react.

Runs inside WSL. Read-only; never modifies application data.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import sys
import urllib.request

API = "http://127.0.0.1:52147"
LOG_PATH = "/mnt/d/Everest-data/audit/observability.jsonl"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _probe(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status, resp.read().decode()[:200]
    except Exception as exc:  # noqa: BLE001 - report any probe failure
        return 0, str(exc)


def _append(entry: dict[str, object]) -> None:
    import os

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def main() -> int:
    liveness_status, liveness_body = _probe(f"{API}/healthz")
    readiness_status, readiness_body = _probe(f"{API}/readyz")
    ok = liveness_status == 200 and readiness_status == 200
    entry = {
        "event": "observability_probe",
        "occurred_at": _now(),
        "liveness": {"status": liveness_status, "body": liveness_body},
        "readiness": {"status": readiness_status, "body": readiness_body},
        "ok": ok,
    }
    _append(entry)
    print(json.dumps(entry))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
