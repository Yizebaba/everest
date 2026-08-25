"""Deterministically render offline Block-1 AWS policy documents."""

# pylint: disable=too-many-branches,duplicate-code

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED = {
    "region",
    "rawBucket",
    "kmsKeyArn",
    "accountId",
    "trustAnchorArn",
    "maxObjectSizeBytes",
    "multipartUploads",
    "workloads",
}
SOURCES = ("ECMWF IFS", "NOAA GFS", "DWD ICON", "ECMWF AIFS")
SAFE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
KMS_ARN = re.compile(r"^arn:aws:kms:ap-south-1:(\d{12}):key/[A-Za-z0-9-]+$")
ACCOUNT = re.compile(r"^\d{12}$")
BUCKET = re.compile(
    r"^(?!xn--)(?!.*-s3alias$)(?!.*--ol-s3$)"
    r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"
)
TRUST_ANCHOR = re.compile(
    r"^arn:aws:rolesanywhere:ap-south-1:(\d{12}):"
    r"trust-anchor/[A-Za-z0-9-]+$"
)
PLACEHOLDER = re.compile(r"\$\{[A-Z0-9_]+\}")


def read_json(path: Path) -> dict[str, Any]:
    """Read an object JSON document."""
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def validate_config(config: dict[str, Any], production: bool) -> None:
    """Fail closed for malformed, ambiguous, or unsafe configuration."""
    if set(config) != REQUIRED:
        raise ValueError("config keys must exactly match the strict schema")
    if config["region"] != "ap-south-1":
        raise ValueError("region must be ap-south-1")
    if production and any(PLACEHOLDER.search(text) for text in strings(config)):
        raise ValueError("unresolved production placeholder")
    for key in ("rawBucket", "accountId", "trustAnchorArn", "kmsKeyArn"):
        if not isinstance(config[key], str) or not config[key]:
            raise ValueError(f"{key} must be a non-empty string")
    if production and not ACCOUNT.fullmatch(config["accountId"]):
        raise ValueError("accountId must be twelve digits")
    if production and not BUCKET.fullmatch(config["rawBucket"]):
        raise ValueError("rawBucket has an invalid production name")
    kms_match = KMS_ARN.fullmatch(config["kmsKeyArn"])
    if production and not kms_match:
        raise ValueError("kmsKeyArn must be an ap-south-1 key ARN")
    trust_match = TRUST_ANCHOR.fullmatch(config["trustAnchorArn"])
    if production and not trust_match:
        raise ValueError("trustAnchorArn has an invalid production ARN")
    if production and kms_match and kms_match.group(1) != config["accountId"]:
        raise ValueError("kmsKeyArn account must match accountId")
    if (
        production
        and trust_match
        and trust_match.group(1) != config["accountId"]
    ):
        raise ValueError("trustAnchorArn account must match accountId")
    if (
        not isinstance(config["maxObjectSizeBytes"], int)
        or not 1 <= config["maxObjectSizeBytes"] <= 52428800
    ):
        raise ValueError("maxObjectSizeBytes must be 1..52428800")
    if config["multipartUploads"] is not False:
        raise ValueError("Block-1 requires multipartUploads=false")
    workloads = config["workloads"]
    if not isinstance(workloads, list) or len(workloads) != 4:
        raise ValueError("exactly four workloads are required")
    seen: set[str] = set()
    for workload in workloads:
        if set(workload) != {
            "source",
            "prefix",
            "roleName",
            "profileName",
            "certificateSubject",
        }:
            raise ValueError("workload keys do not match strict schema")
        if workload["source"] not in SOURCES or workload["source"] in seen:
            raise ValueError("sources must be unique and approved")
        seen.add(workload["source"])
        for field in ("prefix", "roleName", "profileName"):
            if not isinstance(workload[field], str) or not SAFE.fullmatch(
                workload[field]
            ):
                raise ValueError(f"invalid {field}")
        expected = workload["source"].lower().replace(" ", "-")
        if (
            workload["prefix"] != expected
            or workload["roleName"] != f"everest-writer-{expected}"
        ):
            raise ValueError("source/prefix/role mapping mismatch")
        if workload["profileName"] != f"everest-profile-{expected}":
            raise ValueError("source/profile mapping mismatch")
        if not workload["certificateSubject"].startswith(
            f"everest/{expected}/"
        ):
            raise ValueError("certificate binding mismatch")
    if seen != set(SOURCES):
        raise ValueError("all four approved sources are required")


def strings(value: Any) -> list[str]:
    """Collect scalar strings recursively."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in strings(child)]
    return []


def role_arn(config: dict[str, Any], workload: dict[str, str]) -> str:
    """Build the role ARN."""
    return (
        f"arn:aws:iam::{config['accountId']}:"
        f"role/everest/{workload['roleName']}"
    )


def trust(config: dict[str, Any], workload: dict[str, str]) -> dict[str, Any]:
    """Build a role-specific Roles Anywhere trust policy."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "RolesAnywhereNamedWorkload",
                "Effect": "Allow",
                "Principal": {"Service": "rolesanywhere.amazonaws.com"},
                "Action": [
                    "sts:AssumeRole",
                    "sts:SetSourceIdentity",
                    "sts:TagSession",
                ],
                "Condition": {
                    "ArnEquals": {"aws:SourceArn": config["trustAnchorArn"]},
                    "StringEquals": {
                        "aws:SourceAccount": config["accountId"],
                        "aws:PrincipalTag/x509SAN/URI": (
                            f"spiffe://{workload['certificateSubject']}"
                        ),
                        "sts:SourceIdentity": (
                            f"CN={workload['certificateSubject']}"
                        ),
                    },
                },
            }
        ],
    }


def writer_policy(
    config: dict[str, Any], workload: dict[str, str]
) -> dict[str, Any]:
    """Build a no-multipart, prefix-scoped writer policy."""
    resource = f"arn:aws:s3:::{config['rawBucket']}/{workload['prefix']}/*"
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PutOnlyNamedPrefix",
                "Effect": "Allow",
                "Action": ["s3:PutObject"],
                "Resource": resource,
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-server-side-encryption": "aws:kms",
                        "s3:x-amz-server-side-encryption-aws-kms-key-id": config[
                            "kmsKeyArn"
                        ],
                    },
                },
            }
        ],
    }


def profile(config: dict[str, Any], workload: dict[str, str]) -> dict[str, Any]:
    """Build the documented CreateProfile request shape.

    acceptRoleSessionName must be True because the official AWS signing helper
    (aws_signing_helper credential-process) always sends the end-entity
    certificate serial number as the CreateSession roleSessionName; with False,
    CreateSession returns AccessDenied ("Unable to assume role").
    """
    return {
        "acceptRoleSessionName": True,
        "durationSeconds": 900,
        "enabled": False,
        "managedPolicyArns": [],
        "name": workload["profileName"],
        "requireInstanceProperties": False,
        "roleArns": [role_arn(config, workload)],
        "tags": [{"key": "everest-source", "value": workload["source"]}],
    }


def kms_policy(config: dict[str, Any]) -> dict[str, Any]:
    """Build the Bucket-Key-compatible KMS key-policy fragment."""
    writers = [role_arn(config, workload) for workload in config["workloads"]]
    context = f"arn:aws:s3:::{config['rawBucket']}"
    common = {
        "kms:ViaService": "s3.ap-south-1.amazonaws.com",
        "kms:CallerAccount": config["accountId"],
        "kms:EncryptionContext:aws:s3:arn": context,
    }
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowNamedWritersToEncryptWithBucketKey",
                "Effect": "Allow",
                "Principal": {"AWS": writers},
                "Action": [
                    "kms:Encrypt",
                    "kms:GenerateDataKey",
                    "kms:DescribeKey",
                ],
                "Resource": "*",
                "Condition": {"StringEquals": common},
            }
        ],
    }


def render(config: dict[str, Any], output: Path, production: bool) -> None:
    """Render all deterministic role and resource documents."""
    validate_config(config, production)
    output.mkdir(parents=True, exist_ok=True)
    policies = output / "policies"
    profiles = output / "profiles"
    trusts = output / "trust"
    for directory in (policies, profiles, trusts):
        directory.mkdir(exist_ok=True)
    for workload in config["workloads"]:
        stem = workload["source"].lower().replace(" ", "-")
        for directory, document in (
            (policies, writer_policy(config, workload)),
            (profiles, profile(config, workload)),
            (trusts, trust(config, workload)),
        ):
            (directory / f"{stem}.json").write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    resource = {
        "region": config["region"],
        "bucket": config["rawBucket"],
        "objectLockEnabled": True,
        "objectOwnership": "BucketOwnerEnforced",
        "blockPublicAccess": {
            key: True
            for key in (
                "blockPublicAcls",
                "ignorePublicAcls",
                "blockPublicPolicy",
                "restrictPublicBuckets",
            )
        },
        "defaultEncryption": {
            "algorithm": "aws:kms",
            "kmsKeyArn": config["kmsKeyArn"],
            "bucketKeyEnabled": True,
        },
        "multipartUploads": False,
        "maxObjectSizeBytes": config["maxObjectSizeBytes"],
    }
    (output / "resource-config.json").write_text(
        json.dumps(resource, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "kms-key-policy-fragment.json").write_text(
        json.dumps(kms_policy(config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """Render from a strict config without network access."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    render(read_json(args.config), args.output, args.production)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
