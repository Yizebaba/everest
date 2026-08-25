"""Render deterministic Block-2 offline retention assets."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PLACEHOLDER = re.compile(r"\$\{[A-Z0-9_]+\}")
KMS_ARN = re.compile(r"^arn:aws:kms:ap-south-1:982408502231:key/[A-Za-z0-9-]+$")
EXPECTED_BUCKETS = {
    "governanceQa": "zhufengxiangmu-b2-qa-982408502231",
    "audit": "zhufengxiangmu-audit-982408502231",
}
EXPECTED_ROLES = {
    "retentionAdmin": "retention-admin",
    "legalAuthorityPlaceholder": "legal-authority-placeholder",
    "holdExecutor": "hold-executor",
    "dispositionExecutor": "disposition-executor",
    "auditRead": "retention-audit-read-only",
}


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: root must be an object")
    return value


def scalar_strings(value: Any) -> list[str]:
    """Return all nested string scalar values."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in scalar_strings(child)]
    if isinstance(value, dict):
        return [
            item for child in value.values() for item in scalar_strings(child)
        ]
    return []


def validate_config(  # pylint: disable=too-many-branches
    config: dict[str, Any], resolved: bool
) -> None:
    """Fail closed on any deviation from the Manager-authorized B2 scope."""
    if config.get("accountId") != "982408502231":
        raise ValueError("accountId must be the authorized account")
    if config.get("region") != "ap-south-1":
        raise ValueError("region must be ap-south-1")
    if config.get("policyVersion") != "2026-08-24.b2.v1":
        raise ValueError("policyVersion is not authorized")
    kms_key_arn = config.get("kmsKeyArn")
    if not isinstance(kms_key_arn, str) or not kms_key_arn:
        raise ValueError("kmsKeyArn must be a non-empty string")
    if resolved and not KMS_ARN.fullmatch(kms_key_arn):
        raise ValueError(
            "resolved KMS ARN must be the authorized account/Region"
        )
    if resolved and any(
        PLACEHOLDER.search(value) for value in scalar_strings(config)
    ):
        raise ValueError("resolved rendering forbids placeholders")

    governance = config.get("governanceQa", {})
    audit = config.get("audit", {})
    if governance.get("bucketName") != EXPECTED_BUCKETS["governanceQa"]:
        raise ValueError("Governance QA bucket name changed")
    if (governance.get("mode"), governance.get("days")) != (
        "GOVERNANCE",
        180,
    ):
        raise ValueError("Governance QA default must be GOVERNANCE/180")
    if governance.get("provisioningEnabled") is not False:
        raise ValueError(
            "offline foundation cannot enable Governance provisioning"
        )
    if audit.get("bucketName") != EXPECTED_BUCKETS["audit"]:
        raise ValueError("audit bucket name changed")
    if (audit.get("mode"), audit.get("days")) != ("COMPLIANCE", 1095):
        raise ValueError("audit default must be COMPLIANCE/1095")
    if audit.get("provisioningEnabled") is not False:
        raise ValueError("offline foundation cannot enable audit provisioning")

    canary = config.get("productionCanary", {})
    expected_canary = {
        "bucketName": "zhufengxiangmu",
        "mode": "COMPLIANCE",
        "days": 180,
        "objectCount": 1,
        "maxObjectSizeBytes": 1024,
        "syntheticOnly": True,
        "requiresGovernanceQaPass": True,
        "enabled": False,
    }
    if canary != expected_canary:
        raise ValueError("production canary contract changed or became enabled")
    if config.get("operationalExtensionDays") != 730:
        raise ValueError("operational extension must be 730 days")
    if config.get("lifecycleRules") != []:
        raise ValueError("Lifecycle rules must remain absent")
    if config.get("roles") != EXPECTED_ROLES:
        raise ValueError(
            "role names must exactly match the authorized contract"
        )


def substitute(value: Any, replacements: dict[str, str]) -> Any:
    """Recursively replace only declared template values."""
    if isinstance(value, str):
        rendered = value
        for marker, replacement in replacements.items():
            rendered = rendered.replace(f"${{{marker}}}", replacement)
        return rendered
    if isinstance(value, list):
        return [substitute(child, replacements) for child in value]
    if isinstance(value, dict):
        return {
            key: substitute(child, replacements) for key, child in value.items()
        }
    return value


def write_json(path: Path, document: dict[str, Any]) -> None:
    """Write stable, formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render(config: dict[str, Any], output: Path, resolved: bool) -> None:
    """Render inert contracts; never contact AWS or enable a resource."""
    validate_config(config, resolved)
    replacements = {"B2_KMS_KEY_ARN": config["kmsKeyArn"]}
    sources = (
        ROOT / "resources",
        ROOT / "policies",
        ROOT / "roles",
    )
    for source in sources:
        for path in sorted(source.glob("*.json")):
            document = read_json(path)
            rendered = substitute(deepcopy(document), replacements)
            write_json(output / source.name / path.name, rendered)
    write_json(output / "retention-config.json", config)


def main() -> int:
    """Run the offline renderer."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "retention-config.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resolved", action="store_true")
    arguments = parser.parse_args()
    render(read_json(arguments.config), arguments.output, arguments.resolved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
