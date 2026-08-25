"""Fail-closed offline validation for Block-2 retention assets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from render_assets import ROOT, read_json, scalar_strings, validate_config


PLACEHOLDER = re.compile(r"\$\{[A-Z0-9_]+\}")
SECRET = re.compile(
    r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|BEGIN [A-Z ]+ PRIVATE KEY|"
    r"aws_secret_access_key|aws_session_token|password\s*=|client_secret",
    re.IGNORECASE,
)
WRITER_FORBIDDEN = {
    "s3:BypassGovernanceRetention",
    "s3:DeleteObject",
    "s3:DeleteObjectVersion",
    "s3:GetObject",
    "s3:GetObjectLegalHold",
    "s3:GetObjectRetention",
    "s3:GetObjectVersion",
    "s3:PutObjectLegalHold",
    "s3:PutObjectRetention",
}
MUTATION_ACTIONS = {
    "s3:BypassGovernanceRetention",
    "s3:DeleteObject",
    "s3:DeleteObjectVersion",
    "s3:PutBucketObjectLockConfiguration",
    "s3:PutLifecycleConfiguration",
    "s3:PutObjectLegalHold",
    "s3:PutObjectRetention",
}


def actions(statement: dict[str, Any]) -> set[str]:
    """Normalize an IAM Action value."""
    value = statement.get("Action", [])
    return {value} if isinstance(value, str) else set(value)


def all_actions(
    document: dict[str, Any], effect: str | None = None
) -> set[str]:
    """Collect actions, optionally for one statement effect."""
    return {
        action
        for statement in document.get("Statement", [])
        if effect is None or statement.get("Effect") == effect
        for action in actions(statement)
    }


def validate_bucket_contract(path: Path) -> list[str]:
    """Validate an inert, locked bucket resource contract."""
    document = read_json(path)
    errors: list[str] = []
    expected = {
        "governance-qa-bucket.json": (
            "zhufengxiangmu-b2-qa-982408502231",
            "GOVERNANCE",
            180,
        ),
        "audit-bucket.json": (
            "zhufengxiangmu-audit-982408502231",
            "COMPLIANCE",
            1095,
        ),
    }
    bucket, mode, days = expected[path.name]
    if document.get("applyEnabled") is not False:
        errors.append(f"{path.name}: resource must be inert")
    if document.get("accountId") != "982408502231":
        errors.append(f"{path.name}: wrong account")
    if document.get("region") != "ap-south-1":
        errors.append(f"{path.name}: wrong Region")
    if document.get("bucketName") != bucket:
        errors.append(f"{path.name}: wrong bucket")
    if document.get("objectLockEnabledAtCreation") is not True:
        errors.append(f"{path.name}: Object Lock must be enabled at creation")
    if document.get("versioningStatus") != "Enabled":
        errors.append(f"{path.name}: Versioning must be Enabled")
    retention = document.get("defaultRetention", {})
    if (retention.get("mode"), retention.get("days")) != (mode, days):
        errors.append(f"{path.name}: wrong default retention")
    if document.get("lifecycleRules") != []:
        errors.append(f"{path.name}: Lifecycle rules must be absent")
    if not all(document.get("blockPublicAccess", {}).values()):
        errors.append(f"{path.name}: Block Public Access must be complete")
    encryption = document.get("defaultEncryption", {})
    if encryption.get("algorithm") != "aws:kms":
        errors.append(f"{path.name}: SSE-KMS is required")
    if encryption.get("bucketKeyEnabled") is not True:
        errors.append(f"{path.name}: Bucket Key must be enabled")
    return errors


def validate_canary() -> list[str]:
    """Require the exact production canary to remain disabled."""
    document = read_json(ROOT / "resources" / "production-canary.json")
    expected = {
        "enabled": False,
        "requiresGovernanceQaPass": True,
        "accountId": "982408502231",
        "region": "ap-south-1",
        "bucketName": "zhufengxiangmu",
        "syntheticOnly": True,
        "exactObjectCount": 1,
        "maxObjectSizeBytes": 1024,
        "requiresNonNullVersionId": True,
        "legalHoldAllowed": False,
        "deleteAllowed": False,
    }
    errors = [
        f"production-canary.json: invalid {key}"
        for key, value in expected.items()
        if document.get(key) != value
    ]
    if document.get("retention") != {"mode": "COMPLIANCE", "days": 180}:
        errors.append(
            "production-canary.json: retention must be COMPLIANCE/180"
        )
    return errors


def validate_roles() -> list[str]:
    """Validate disabled roles and separation of authority."""
    document = read_json(ROOT / "roles" / "role-contracts.json")
    roles = {role["name"]: role for role in document.get("roles", [])}
    errors: list[str] = []
    expected = {
        "retention-admin",
        "legal-authority-placeholder",
        "hold-executor",
        "disposition-executor",
        "retention-audit-read-only",
    }
    if set(roles) != expected:
        return ["role-contracts.json: exact roles required"]
    for role in roles.values():
        if role.get("enabled") is not False:
            errors.append(
                f"role-contracts.json: {role['name']} must be disabled"
            )
    for name in (
        "legal-authority-placeholder",
        "hold-executor",
        "disposition-executor",
    ):
        role = roles[name]
        if role.get("trustPolicy") is not None:
            errors.append(f"role-contracts.json: {name} trust must be null")
        if role.get("humanPrincipal") is not None:
            errors.append(f"role-contracts.json: {name} principal must be null")
    return errors


def validate_policies() -> list[str]:  # pylint: disable=too-many-branches
    """Validate least privilege and explicit-deny invariants."""
    errors: list[str] = []
    policies = {
        path.name: read_json(path)
        for path in (ROOT / "policies").glob("*.json")
    }
    for name, document in policies.items():
        if document.get("Version") != "2012-10-17":
            errors.append(f"{name}: invalid IAM policy version")
        if any(SECRET.search(value) for value in scalar_strings(document)):
            errors.append(f"{name}: secret-shaped content")
        for statement in document.get("Statement", []):
            if statement.get("Effect") == "Allow" and "*" in actions(statement):
                errors.append(f"{name}: wildcard Allow action")

    retention = policies["retention-admin.json"]
    retention_allowed = all_actions(retention, "Allow")
    expected_retention = {
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetBucketVersioning",
        "s3:GetObjectLegalHold",
        "s3:GetObjectRetention",
        "s3:ListBucketVersions",
        "s3:PutObjectRetention",
    }
    if retention_allowed != expected_retention:
        errors.append("retention-admin.json: action set changed")
    if retention_allowed.intersection(
        MUTATION_ACTIONS - {"s3:PutObjectRetention"}
    ):
        errors.append("retention-admin.json: prohibited mutation")

    legal = policies["legal-authority-deny-only.json"]
    if legal.get("Statement") != [
        {
            "Sid": "DenyAllUntilNamedAuthorityAssignment",
            "Effect": "Deny",
            "Action": "*",
            "Resource": "*",
        }
    ]:
        errors.append("legal authority must be exact deny-only policy")
    for name in (
        "hold-executor-disabled.json",
        "disposition-executor-disabled.json",
    ):
        if policies[name].get("Statement") != []:
            errors.append(f"{name}: must grant no permissions")

    audit_allowed = all_actions(policies["audit-read-only.json"], "Allow")
    if audit_allowed.intersection(MUTATION_ACTIONS):
        errors.append("audit-read-only.json: mutation action present")
    if audit_allowed.intersection({"s3:GetObject", "s3:GetObjectVersion"}):
        errors.append("audit-read-only.json: payload read present")

    bucket_denies = all_actions(policies["bucket-explicit-deny.json"], "Deny")
    required_denies = {
        "s3:BypassGovernanceRetention",
        "s3:DeleteObject",
        "s3:PutLifecycleConfiguration",
        "s3:PutObjectLegalHold",
    }
    if not required_denies.issubset(bucket_denies):
        errors.append("bucket-explicit-deny.json: required deny missing")
    writer_denies = all_actions(policies["writer-boundary-deny.json"], "Deny")
    if not WRITER_FORBIDDEN.issubset(writer_denies):
        errors.append("writer-boundary-deny.json: writer deny missing")
    kms_denies = all_actions(policies["kms-survival-deny.json"], "Deny")
    if kms_denies != {"kms:DisableKey", "kms:ScheduleKeyDeletion"}:
        errors.append(
            "kms-survival-deny.json: exact key survival deny required"
        )
    return errors


def validate_exact_version_and_state() -> list[str]:
    """Validate exact-version identity and disabled dangerous transitions."""
    exact = read_json(ROOT / "exact-version-operation.json")
    state = read_json(ROOT / "state-machine.json")
    errors: list[str] = []
    if set(exact.get("requiredIdentityFields", [])) != {
        "artifactId",
        "bucketName",
        "objectKey",
        "versionId",
    }:
        errors.append("exact-version-operation.json: identity fields changed")
    version = exact.get("versionId", {})
    if version != {
        "nullable": False,
        "emptyAllowed": False,
        "deleteMarkerAllowed": False,
    }:
        errors.append("exact-version-operation.json: version must fail closed")
    if exact.get("unversionedDeleteAllowed") is not False:
        errors.append(
            "exact-version-operation.json: unversioned delete enabled"
        )
    if exact.get("deleteMarkerCompletesDisposition") is not False:
        errors.append("exact-version-operation.json: delete marker accepted")
    if set(state.get("disabledUntilAuthorityAssignment", [])) != {
        "hold_placement",
        "hold_release",
    }:
        errors.append("state-machine.json: hold actions not disabled")
    if set(state.get("disabledThroughoutThisAuthorization", [])) != {
        "disposition_approval",
        "delete_version",
    }:
        errors.append("state-machine.json: disposition not disabled")
    guards = state.get("guards", {})
    if not guards or not all(value is True for value in guards.values()):
        errors.append("state-machine.json: every fail-closed guard is required")
    return errors


def validate_kms_survival() -> list[str]:
    """Validate cryptographic survivability requirements."""
    document = read_json(ROOT / "kms-survival.json")
    errors: list[str] = []
    if document.get("applyEnabled") is not False:
        errors.append("kms-survival.json: must remain inert")
    if set(document.get("ordinaryRoleExplicitDenies", [])) != {
        "kms:DisableKey",
        "kms:ScheduleKeyDeletion",
    }:
        errors.append("kms-survival.json: key destruction denies missing")
    if document.get("failureState") != "kms_access_blocked":
        errors.append("kms-survival.json: failure must block")
    if document.get("destroyingKeyIsDisposition") is not False:
        errors.append("kms-survival.json: key destruction is not disposition")
    if "maximum-30-day-waiting-period" not in document.get(
        "deletionPreconditions", []
    ):
        errors.append("kms-survival.json: maximum wait requirement missing")
    return errors


def validate_all(resolved: bool = False) -> list[str]:
    """Validate all B2 assets without network or AWS access."""
    errors: list[str] = []
    config = read_json(ROOT / "retention-config.json")
    try:
        validate_config(config, resolved)
    except ValueError as error:
        errors.append(f"retention-config.json: {error}")
    for path in sorted((ROOT / "resources").glob("*-bucket.json")):
        errors.extend(validate_bucket_contract(path))
    errors.extend(validate_canary())
    errors.extend(validate_roles())
    errors.extend(validate_policies())
    errors.extend(validate_exact_version_and_state())
    errors.extend(validate_kms_survival())
    for path in ROOT.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {error}")
    return errors


def main() -> int:
    """Run offline validation and return a process status."""
    errors = validate_all(resolved="--resolved" in sys.argv[1:])
    if errors:
        print("\n".join(errors))
        return 1
    print("Block-2 offline retention validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
