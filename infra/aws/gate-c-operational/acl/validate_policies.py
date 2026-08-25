"""Offline validation for Block-1 AWS policy and renderer assets."""

# pylint: disable=too-many-branches,duplicate-code

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
POLICY_DIR = ROOT / "policies"
PLACEHOLDER = re.compile(r"\$\{[A-Z0-9_]+\}")
SECRETS = re.compile(
    r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|BEGIN [A-Z ]+ PRIVATE KEY|"
    r"aws_session_token|client_secret|password\s*=|aws_secret_access_key",
    re.IGNORECASE,
)
WRITERS = {
    "writer-ecmwf-ifs.json": ("ecmwf-ifs", "ECMWF IFS"),
    "writer-noaa-gfs.json": ("noaa-gfs", "NOAA GFS"),
    "writer-dwd-icon.json": ("dwd-icon", "DWD ICON"),
    "writer-ecmwf-aifs.json": ("ecmwf-aifs", "ECMWF AIFS"),
}
TRUST_ACTIONS = {"sts:AssumeRole", "sts:SetSourceIdentity", "sts:TagSession"}


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: root must be an object")
    return value


def strings(value: Any) -> list[str]:
    """Collect scalar strings recursively."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in strings(child)]
    return []


def actions(statement: dict[str, Any]) -> set[str]:
    """Normalize an IAM Action member."""
    value = statement.get("Action", [])
    return {value} if isinstance(value, str) else set(value)


def validate_policy(path: Path, production: bool) -> list[str]:
    """Validate JSON policy invariants and supported AWS fields."""
    document = load_json(path)
    errors: list[str] = []
    if (
        path.name != "roles-anywhere-profile.json"
        and document.get("Version") != "2012-10-17"
    ):
        errors.append(f"{path.name}: invalid policy version")
    for text in strings(document):
        if SECRETS.search(text):
            errors.append(f"{path.name}: secret pattern")
        if production and PLACEHOLDER.search(text):
            errors.append(f"{path.name}: unresolved production placeholder")
    for statement in document.get("Statement", []):
        current = actions(statement)
        if "*" in current or any(action.endswith("*") for action in current):
            errors.append(f"{path.name}: broad action")
        if statement.get("Effect") == "Allow" and statement.get(
            "Principal"
        ) in ("*", {"AWS": "*"}):
            errors.append(f"{path.name}: broad allow principal")
        if statement.get("Resource") == "*" and path.name not in {
            "kms-key-policy-fragment.json",
            "disabled-backup.json",
        }:
            errors.append(f"{path.name}: broad resource")
    if path.name in WRITERS:
        prefix, _ = WRITERS[path.name]
        allowed = {"s3:PutObject"}
        for statement in document["Statement"]:
            if not actions(statement).issubset(allowed):
                errors.append(f"{path.name}: writer action mismatch")
            if f"${{RAW_BUCKET}}/{prefix}/*" not in str(statement):
                errors.append(f"{path.name}: writer prefix mismatch")
            condition = statement.get("Condition", {})
            conditions = condition.get("StringEquals", {})
            if conditions.get("s3:x-amz-server-side-encryption") != "aws:kms":
                errors.append(f"{path.name}: missing SSE-KMS condition")
            if (
                "s3:x-amz-server-side-encryption-aws-kms-key-id"
                not in conditions
            ):
                errors.append(f"{path.name}: missing exact KMS condition")
            if "kms:EncryptionContext:aws:s3:arn" in str(condition):
                errors.append(
                    f"{path.name}: writer must not constrain KMS context"
                )
    if path.name == "verifier.json" and "s3:HeadObject" in strings(document):
        errors.append("verifier.json: unsupported HeadObject action")
    if path.name == "roles-anywhere-trust.json":
        statement = document["Statement"][0]
        if actions(statement) != TRUST_ACTIONS:
            errors.append("trust: exact Roles Anywhere actions required")
        condition = statement.get("Condition", {})
        values = str(condition)
        for required in (
            "aws:SourceArn",
            "aws:SourceAccount",
            "aws:PrincipalTag/x509SAN/URI",
            "sts:SourceIdentity",
        ):
            if required not in values:
                errors.append(f"trust: missing {required}")
    if path.name == "roles-anywhere-profile.json":
        supported = {
            "acceptRoleSessionName",
            "durationSeconds",
            "enabled",
            "managedPolicyArns",
            "name",
            "requireInstanceProperties",
            "roleArns",
            "tags",
        }
        if set(document) != supported or document.get("durationSeconds") != 900:
            errors.append("profile: invalid CreateProfile schema or duration")
        if document.get("enabled") is not False:
            errors.append("profile: must start disabled")
        if document.get("acceptRoleSessionName") is not True:
            errors.append(
                "profile: acceptRoleSessionName must be true for the official "
                "aws_signing_helper (it always sends the cert serial as the "
                "CreateSession roleSessionName)"
            )
    if path.name == "kms-key-policy-fragment.json":
        errors.extend(validate_kms_document(document, "${RAW_BUCKET}"))
    return errors


def validate_kms_document(
    document: dict[str, Any], expected_bucket: str
) -> list[str]:
    """Require S3 ViaService and exact Bucket Key encryption context."""
    errors: list[str] = []
    expected_context = f"arn:aws:s3:::{expected_bucket}"
    for statement in document.get("Statement", []):
        condition = statement.get("Condition", {})
        if set(condition) != {"StringEquals"}:
            errors.append("kms: conditions must use exact StringEquals")
            continue
        equals = condition["StringEquals"]
        if equals.get("kms:ViaService") != "s3.ap-south-1.amazonaws.com":
            errors.append("kms: ViaService must be ap-south-1 S3")
        if equals.get("kms:EncryptionContext:aws:s3:arn") != expected_context:
            errors.append("kms: encryption context must be exact bucket ARN")
    return errors


def validate_resource_document(
    document: dict[str, Any], production: bool
) -> list[str]:
    """Validate S3 resource security configuration document."""
    errors: list[str] = []
    for text in strings(document):
        if production and PLACEHOLDER.search(text):
            errors.append(
                "resource-config.json: unresolved production placeholder"
            )
    if document.get("objectOwnership") != "BucketOwnerEnforced":
        errors.append("resource: ownership must be BucketOwnerEnforced")
    block = document.get("blockPublicAccess", {})
    if set(block) != {
        "blockPublicAcls",
        "ignorePublicAcls",
        "blockPublicPolicy",
        "restrictPublicBuckets",
    } or not all(value is True for value in block.values()):
        errors.append("resource: all Block Public Access settings are required")
    if document.get("multipartUploads") is not False:
        errors.append("resource: multipart must be disabled")
    encryption = document.get("defaultEncryption", {})
    if encryption.get("bucketKeyEnabled") is not True:
        errors.append("resource: S3 Bucket Key must be enabled")
    return errors


def validate_resource(path: Path, production: bool) -> list[str]:
    """Load and validate S3 resource security configuration."""
    return validate_resource_document(load_json(path), production)


def validate_all(production: bool = False) -> list[str]:
    """Validate every offline asset without contacting AWS."""
    errors: list[str] = []
    for path in sorted(POLICY_DIR.glob("*.json")):
        errors.extend(validate_policy(path, production))
    errors.extend(validate_resource(ROOT / "resource-config.json", production))
    return errors


def main() -> int:
    """Run the offline validator."""
    errors = validate_all("--production" in sys.argv[1:])
    if errors:
        print("\n".join(errors))
        return 1
    print("offline policy validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
