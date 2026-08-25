"""Render a complete, deterministic Block-2 offline review package."""

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
ROLE_ARN = re.compile(r"^arn:aws:iam::982408502231:role/[A-Za-z0-9+=,.@_/-]+$")
EXPECTED_CONFIG_KEYS = {
    "accountId",
    "region",
    "policyVersion",
    "kmsKeyArn",
    "governanceQa",
    "audit",
    "productionCanary",
    "operationalExtensionDays",
    "lifecycleRules",
    "roles",
    "principals",
}
EXPECTED_ROLES = {
    "retentionBroker": "everest-retention-broker",
    "retentionAdmin": "everest-retention-admin",
    "auditRead": "everest-retention-audit-read-only",
    "kmsAdministratorRecovery": "everest-gatec-administrator",
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


def _require_exact_keys(
    value: dict[str, Any], expected: set[str], label: str
) -> None:
    """Reject missing and unknown object fields."""
    if set(value) != expected:
        raise ValueError(f"{label} fields must be exact")


def validate_config(  # pylint: disable=too-many-branches
    config: dict[str, Any], resolved: bool
) -> None:
    """Fail closed on deviations from the Manager-authorized B2 scope."""
    _require_exact_keys(config, EXPECTED_CONFIG_KEYS, "config")
    if config["accountId"] != "982408502231":
        raise ValueError("accountId must be the authorized account")
    if config["region"] != "ap-south-1":
        raise ValueError("region must be ap-south-1")
    if config["policyVersion"] != "2026-08-25.b2.v2":
        raise ValueError("policyVersion is not authorized")
    kms_key_arn = config["kmsKeyArn"]
    if not isinstance(kms_key_arn, str) or not kms_key_arn:
        raise ValueError("kmsKeyArn must be a non-empty string")
    if resolved and not KMS_ARN.fullmatch(kms_key_arn):
        raise ValueError("resolved KMS ARN must match account and Region")

    expected_sections = {
        "governanceQa": {
            "bucketName": "zhufengxiangmu-b2-qa-982408502231",
            "mode": "GOVERNANCE",
            "days": 180,
            "provisioningEnabled": False,
        },
        "audit": {
            "bucketName": "zhufengxiangmu-audit-982408502231",
            "mode": "COMPLIANCE",
            "days": 1095,
            "provisioningEnabled": False,
        },
        "productionCanary": {
            "bucketName": "zhufengxiangmu",
            "mode": "COMPLIANCE",
            "days": 180,
            "objectCount": 1,
            "maxObjectSizeBytes": 1024,
            "syntheticOnly": True,
            "requiresGovernanceQaPass": True,
            "enabled": False,
        },
    }
    for name, expected in expected_sections.items():
        if config[name] != expected:
            raise ValueError(f"{name} contract changed")
    if config["operationalExtensionDays"] != 730:
        raise ValueError("operational extension must be 730 days")
    if config["lifecycleRules"] != []:
        raise ValueError("Lifecycle rules must remain absent")
    if config["roles"] != EXPECTED_ROLES:
        raise ValueError("role names must exactly match the contract")

    principals = config["principals"]
    _require_exact_keys(
        principals,
        {
            "brokerExecutorPrincipalArn",
            "auditHumanPrincipalArn",
            "kmsAdministratorRecoveryArn",
        },
        "principals",
    )
    expected_admin = (
        "arn:aws:iam::982408502231:role/everest/admin/"
        "everest-gatec-administrator"
    )
    if principals["kmsAdministratorRecoveryArn"] != expected_admin:
        raise ValueError("KMS administrator/recovery principal changed")
    if resolved:
        for field in ("brokerExecutorPrincipalArn", "auditHumanPrincipalArn"):
            if not ROLE_ARN.fullmatch(principals[field]):
                raise ValueError(f"resolved {field} must be a named role ARN")
        if any(PLACEHOLDER.search(item) for item in scalar_strings(config)):
            raise ValueError("resolved rendering forbids placeholders")


def substitute(value: Any, replacements: dict[str, str]) -> Any:
    """Recursively replace declared template markers."""
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
    """Write stable formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render(config: dict[str, Any], output: Path) -> None:
    """Render a complete resolved package without contacting AWS."""
    validate_config(config, resolved=True)
    replacements = {
        "B2_KMS_KEY_ARN": config["kmsKeyArn"],
        "RETENTION_BUCKET": config["governanceQa"]["bucketName"],
        "BROKER_EXECUTOR_PRINCIPAL_ARN": config["principals"][
            "brokerExecutorPrincipalArn"
        ],
        "AUDIT_HUMAN_PRINCIPAL_ARN": config["principals"][
            "auditHumanPrincipalArn"
        ],
    }
    paths = [
        path for path in ROOT.rglob("*.json") if "__pycache__" not in path.parts
    ]
    for path in sorted(paths):
        document = (
            config if path.name == "retention-config.json" else read_json(path)
        )
        rendered = substitute(deepcopy(document), replacements)
        if any(PLACEHOLDER.search(item) for item in scalar_strings(rendered)):
            relative = path.relative_to(ROOT)
            raise ValueError(f"{relative}: output contains a placeholder")
        write_json(output / path.relative_to(ROOT), rendered)


def main() -> int:
    """Run the offline renderer."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "retention-config.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    render(read_json(arguments.config), arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
