"""Fail-closed offline validation for Block-2 retention assets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from render_assets import ROOT, read_json, scalar_strings, validate_config


SECRET = re.compile(
    r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|BEGIN [A-Z ]+ PRIVATE KEY|"
    r"aws_secret_access_key|aws_session_token|password\s*=|client_secret",
    re.IGNORECASE,
)
KMS_ARN = "${B2_KMS_KEY_ARN}"
BUCKET = "${RETENTION_BUCKET}"
BPA = {
    "blockPublicAcls": True,
    "ignorePublicAcls": True,
    "blockPublicPolicy": True,
    "restrictPublicBuckets": True,
}
ORDINARY_ROLES = [
    "arn:aws:iam::982408502231:role/everest/everest-writer-ecmwf-ifs",
    "arn:aws:iam::982408502231:role/everest/everest-writer-noaa-gfs",
    "arn:aws:iam::982408502231:role/everest/everest-writer-dwd-icon",
    "arn:aws:iam::982408502231:role/everest/everest-writer-ecmwf-aifs",
    "arn:aws:iam::982408502231:role/everest/everest-retention-broker",
    "arn:aws:iam::982408502231:role/everest/everest-retention-admin",
    "arn:aws:iam::982408502231:role/everest/everest-retention-audit-read-only",
]
CHECKED_S3_ACTIONS = {
    "s3:BypassGovernanceRetention",
    "s3:DeleteObject",
    "s3:DeleteObjectVersion",
    "s3:GetBucketObjectLockConfiguration",
    "s3:GetBucketVersioning",
    "s3:GetInventoryConfiguration",
    "s3:GetLifecycleConfiguration",
    "s3:GetObject",
    "s3:GetObjectLegalHold",
    "s3:GetObjectRetention",
    "s3:GetObjectVersion",
    "s3:ListBucket",
    "s3:ListBucketVersions",
    "s3:PutBucketObjectLockConfiguration",
    "s3:PutLifecycleConfiguration",
    "s3:PutObjectLegalHold",
    "s3:PutObjectRetention",
}


def actions(statement: dict[str, Any]) -> set[str]:
    """Normalize an IAM Action value."""
    value = statement.get("Action", [])
    return {value} if isinstance(value, str) else set(value)


def _exact(document: Any, expected: Any, label: str) -> list[str]:
    """Return one error when a complete contract differs."""
    return [] if document == expected else [f"{label}: contract changed"]


def _bucket_expected(name: str, mode: str, days: int) -> dict[str, Any]:
    """Build an exact locked-bucket contract."""
    document: dict[str, Any] = {
        "resourceType": "AWS::S3::BucketContract",
        "applyEnabled": False,
        "accountId": "982408502231",
        "region": "ap-south-1",
        "bucketName": name,
        "objectLockEnabledAtCreation": True,
        "versioningStatus": "Enabled",
        "objectOwnership": "BucketOwnerEnforced",
        "blockPublicAccess": BPA,
        "defaultRetention": {"mode": mode, "days": days},
        "defaultEncryption": {
            "algorithm": "aws:kms",
            "kmsKeyArn": KMS_ARN,
            "bucketKeyEnabled": True,
        },
        "lifecycleRules": [],
    }
    if mode == "GOVERNANCE":
        document.update(
            {
                "provisioningOrder": [
                    "create-bucket-with-object-lock-enabled",
                    "set-bucket-owner-enforced-and-four-bpa-and-sse-kms",
                    "set-default-governance-180-days",
                    "read-back-object-lock-governance-180-days",
                    "attach-bucket-lock-mutation-deny",
                ],
                "attachMutationDenyOnlyAfterReadback": True,
            }
        )
    return document


def validate_bucket_contract(path: Path) -> list[str]:
    """Validate every bucket field, including exact BPA and ownership."""
    expected = {
        "governance-qa-bucket.json": _bucket_expected(
            "zhufengxiangmu-b2-qa-982408502231", "GOVERNANCE", 180
        ),
        "audit-bucket.json": _bucket_expected(
            "zhufengxiangmu-audit-982408502231", "COMPLIANCE", 1095
        ),
    }
    return _exact(read_json(path), expected[path.name], path.name)


def validate_canary() -> list[str]:
    """Require the exact production canary to remain disabled."""
    expected = {
        "resourceType": "Everest::S3::ComplianceCanaryContract",
        "enabled": False,
        "requiresGovernanceQaPass": True,
        "accountId": "982408502231",
        "region": "ap-south-1",
        "bucketName": "zhufengxiangmu",
        "syntheticOnly": True,
        "exactObjectCount": 1,
        "maxObjectSizeBytes": 1024,
        "requiresNonNullVersionId": True,
        "retention": {"mode": "COMPLIANCE", "days": 180},
        "legalHoldAllowed": False,
        "deleteAllowed": False,
    }
    return _exact(
        read_json(ROOT / "resources" / "production-canary.json"),
        expected,
        "production-canary.json",
    )


def validate_roles() -> list[str]:
    """Require deployable inactivity and exact activation transition."""
    expected = {
        "path": "/everest/",
        "absentRoles": [
            "legal-authority-placeholder",
            "hold-executor",
            "disposition-executor",
        ],
        "activationTransition": {
            "initialState": "uncreated",
            "gate": "independent-governance-qa-activation-approval",
            "steps": [
                "create-everest-retention-broker-with-approved-service-trust",
                "create-everest-retention-admin-trusting-only-retention-broker",
                "attach-exact-governance-only-retention-admin-policy",
                "verify-no-human-can-assume-retention-admin",
                "enable-approved-calculated-date-command-in-broker",
                "run-negative-arbitrary-date-and-compliance-mode-tests",
            ],
            "rollback": (
                "delete-unattached-roles-and-policies-before-any-protected-object"
            ),
        },
        "roles": [
            {
                "name": "everest-retention-broker",
                "deploymentState": "uncreated",
                "trustPrincipal": "${BROKER_EXECUTOR_PRINCIPAL_ARN}",
                "humanAssumptionAllowed": False,
                "policy": None,
            },
            {
                "name": "everest-retention-admin",
                "deploymentState": "uncreated",
                "trustPrincipal": (
                    "arn:aws:iam::982408502231:role/everest/"
                    "everest-retention-broker"
                ),
                "humanAssumptionAllowed": False,
                "policy": "policies/retention-admin.json",
            },
            {
                "name": "everest-retention-audit-read-only",
                "deploymentState": "uncreated",
                "trustPrincipal": "${AUDIT_HUMAN_PRINCIPAL_ARN}",
                "humanMfaRequired": True,
                "policy": "policies/audit-read-only.json",
            },
        ],
    }
    return _exact(
        read_json(ROOT / "roles" / "role-contracts.json"),
        expected,
        "role-contracts.json",
    )


def _expected_policies() -> dict[str, dict[str, Any]]:
    """Return exact policy documents accepted by B2 offline review."""
    return {
        "audit-read-only.json": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "ReadBucketRetentionConfiguration",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketObjectLockConfiguration",
                        "s3:GetBucketVersioning",
                        "s3:GetInventoryConfiguration",
                        "s3:GetLifecycleConfiguration",
                        "s3:ListBucketVersions",
                    ],
                    "Resource": f"arn:aws:s3:::{BUCKET}",
                },
                {
                    "Sid": "ReadExactVersionRetentionMetadataNotPayload",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObjectLegalHold",
                        "s3:GetObjectRetention",
                    ],
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                },
            ],
        },
        "retention-admin.json": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "ReadBucketLockStateAndVersions",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketObjectLockConfiguration",
                        "s3:GetBucketVersioning",
                        "s3:ListBucketVersions",
                    ],
                    "Resource": f"arn:aws:s3:::{BUCKET}",
                },
                {
                    "Sid": "ReadExactVersionRetentionMetadata",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObjectLegalHold",
                        "s3:GetObjectRetention",
                    ],
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                },
                {
                    "Sid": "ExtendExactVersionGovernanceRetention",
                    "Effect": "Allow",
                    "Action": "s3:PutObjectRetention",
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                    "Condition": {
                        "StringEquals": {"s3:object-lock-mode": "GOVERNANCE"}
                    },
                },
            ],
        },
        "writer-boundary-deny.json": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyWriterRetentionHoldDeleteAndBypass",
                    "Effect": "Deny",
                    "Action": [
                        "s3:BypassGovernanceRetention",
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion",
                        "s3:GetObject",
                        "s3:GetObjectLegalHold",
                        "s3:GetObjectRetention",
                        "s3:GetObjectVersion",
                        "s3:PutObjectLegalHold",
                        "s3:PutObjectRetention",
                    ],
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                },
                {
                    "Sid": "DenyWriterListing",
                    "Effect": "Deny",
                    "Action": ["s3:ListBucket", "s3:ListBucketVersions"],
                    "Resource": f"arn:aws:s3:::{BUCKET}",
                },
                {
                    "Sid": "DenyWriterBucketRetentionMutation",
                    "Effect": "Deny",
                    "Action": [
                        "s3:PutBucketObjectLockConfiguration",
                        "s3:PutLifecycleConfiguration",
                    ],
                    "Resource": f"arn:aws:s3:::{BUCKET}",
                },
            ],
        },
        "bucket-explicit-deny.json": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyGovernanceBypass",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:BypassGovernanceRetention",
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                },
                {
                    "Sid": "DenyUnversionedDelete",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:DeleteObject",
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                },
                {
                    "Sid": "DenyLifecycleMutation",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutLifecycleConfiguration",
                    "Resource": f"arn:aws:s3:::{BUCKET}",
                },
                {
                    "Sid": "DenyBucketLockMutationOutsideInfrastructureBoundary",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutBucketObjectLockConfiguration",
                    "Resource": f"arn:aws:s3:::{BUCKET}",
                },
                {
                    "Sid": "DenyLegalHoldUntilAuthorityAssignment",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutObjectLegalHold",
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                },
            ],
        },
        "kms-survival-deny.json": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyOrdinaryRoleKeyDisableOrDeletion",
                    "Effect": "Deny",
                    "Action": ["kms:DisableKey", "kms:ScheduleKeyDeletion"],
                    "Resource": KMS_ARN,
                }
            ],
        },
    }


def validate_policies() -> list[str]:
    """Validate exact policy set, S3 allowlist, resources, and lock deny."""
    paths = sorted((ROOT / "policies").glob("*.json"))
    policies = {path.name: read_json(path) for path in paths}
    expected = _expected_policies()
    errors: list[str] = []
    if set(policies) != set(expected):
        errors.append("policies: exact file set required")
        return errors
    for name, document in policies.items():
        if any(SECRET.search(item) for item in scalar_strings(document)):
            errors.append(f"{name}: secret-shaped content")
        if document.get("Version") != "2012-10-17":
            errors.append(f"{name}: invalid policy version")
        for statement in document.get("Statement", []):
            s3_actions = {
                item for item in actions(statement) if item.startswith("s3:")
            }
            if not s3_actions.issubset(CHECKED_S3_ACTIONS):
                errors.append(f"{name}: unchecked or invalid S3 action")
        errors.extend(_exact(document, expected[name], name))

    retention = policies["retention-admin.json"]
    expected_retention = {
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetBucketVersioning",
        "s3:ListBucketVersions",
        "s3:GetObjectLegalHold",
        "s3:GetObjectRetention",
        "s3:PutObjectRetention",
    }
    actual_retention = {
        item
        for statement in retention["Statement"]
        for item in actions(statement)
    }
    if actual_retention != expected_retention:
        errors.append("retention-admin.json: action set changed")
    mutation = retention["Statement"][2]
    if mutation.get("Condition") != {
        "StringEquals": {"s3:object-lock-mode": "GOVERNANCE"}
    }:
        errors.append(
            "retention-admin.json: Governance-only condition required"
        )
    if mutation.get("Resource") != f"arn:aws:s3:::{BUCKET}/*":
        errors.append("retention-admin.json: exact object resource required")

    bucket = policies["bucket-explicit-deny.json"]
    lock_statements = [
        statement
        for statement in bucket["Statement"]
        if statement.get("Sid")
        == "DenyBucketLockMutationOutsideInfrastructureBoundary"
    ]
    if len(lock_statements) != 1 or lock_statements[0] != {
        "Sid": "DenyBucketLockMutationOutsideInfrastructureBoundary",
        "Effect": "Deny",
        "Principal": "*",
        "Action": "s3:PutBucketObjectLockConfiguration",
        "Resource": f"arn:aws:s3:::{BUCKET}",
    }:
        errors.append("bucket-explicit-deny.json: exact lock deny required")
    return errors


def validate_exact_version_and_state() -> list[str]:
    """Validate exact-version timing and disabled dangerous transitions."""
    exact = read_json(ROOT / "exact-version-operation.json")
    state = read_json(ROOT / "state-machine.json")
    errors: list[str] = []
    exact_keys = {
        "requiredIdentityFields",
        "versionId",
        "operations",
        "unversionedDeleteAllowed",
        "deleteMarkerCompletesDisposition",
        "immutableTimingFields",
        "retentionMutation",
        "s3IsEnforcementAuthority",
        "databaseIsProjection",
    }
    state_keys = {
        "initialState",
        "states",
        "enabledTransitions",
        "disabledUntilAuthorityAssignment",
        "disabledThroughoutThisAuthorization",
        "globalFailureStates",
        "guards",
    }
    if set(exact) != exact_keys:
        errors.append("exact-version-operation.json: fields must be exact")
    if set(state) != state_keys:
        errors.append("state-machine.json: fields must be exact")
    if set(exact.get("requiredIdentityFields", [])) != {
        "artifactId",
        "bucketName",
        "objectKey",
        "versionId",
        "versionCreatedAt",
        "s3LastModified",
    }:
        errors.append("exact-version-operation.json: identity/timing changed")
    if exact.get("retentionMutation") != {
        "directHumanCallAllowed": False,
        "executorMode": "GOVERNANCE",
        "approvedDateRule": (
            "max(versionCreatedAt+duration,acquiredAt+duration)"
        ),
        "arbitraryDateAllowed": False,
        "complianceModeAllowedInGovernanceQa": False,
    }:
        errors.append("exact-version-operation.json: broker guard changed")
    if exact.get("versionId") != {
        "nullable": False,
        "emptyAllowed": False,
        "deleteMarkerAllowed": False,
    }:
        errors.append("exact-version-operation.json: exact version required")
    if exact.get("immutableTimingFields") != {
        "versionCreatedAt": (
            "authoritative-version-creation-time-used-for-retention-arithmetic"
        ),
        "s3LastModified": "immutable-s3-readback-time-provenance",
    }:
        errors.append("exact-version-operation.json: timing contract changed")
    if set(state.get("disabledUntilAuthorityAssignment", [])) != {
        "hold_placement",
        "hold_release",
    }:
        errors.append("state-machine.json: hold actions must be disabled")
    if set(state.get("disabledThroughoutThisAuthorization", [])) != {
        "disposition_approval",
        "delete_version",
    }:
        errors.append("state-machine.json: disposition must be disabled")
    if not all(state.get("guards", {}).values()):
        errors.append("state-machine.json: guards must all be true")
    return errors


def validate_kms_survival() -> list[str]:
    """Validate named ordinary roles and named admin/recovery boundary."""
    document = read_json(ROOT / "kms-survival.json")
    errors: list[str] = []
    if set(document) != {
        "applyEnabled",
        "kmsKeyArn",
        "requiredKeyProperties",
        "ordinaryRoleExplicitDenies",
        "ordinaryRoleArns",
        "kmsAdministratorRecoveryBoundary",
        "deletionPreconditions",
        "failureState",
        "destroyingKeyIsDisposition",
    }:
        errors.append("kms-survival.json: fields must be exact")
    if set(document.get("requiredKeyProperties", {})) != {
        "accountId",
        "region",
        "keyManager",
        "keySpec",
        "keyUsage",
        "multiRegion",
        "enabled",
    }:
        errors.append("kms-survival.json: key property fields must be exact")
    if document.get("requiredKeyProperties") != {
        "accountId": "982408502231",
        "region": "ap-south-1",
        "keyManager": "CUSTOMER",
        "keySpec": "SYMMETRIC_DEFAULT",
        "keyUsage": "ENCRYPT_DECRYPT",
        "multiRegion": False,
        "enabled": True,
    }:
        errors.append("kms-survival.json: key properties changed")
    if document.get("applyEnabled") is not False:
        errors.append("kms-survival.json: must remain inert")
    if document.get("kmsKeyArn") != KMS_ARN:
        errors.append("kms-survival.json: exact KMS ARN required")
    if document.get("ordinaryRoleArns") != ORDINARY_ROLES:
        errors.append("kms-survival.json: ordinary role set changed")
    if document.get("ordinaryRoleExplicitDenies") != [
        "kms:DisableKey",
        "kms:ScheduleKeyDeletion",
    ]:
        errors.append("kms-survival.json: exact denies required")
    boundary = document.get("kmsAdministratorRecoveryBoundary")
    if boundary != {
        "principalArn": (
            "arn:aws:iam::982408502231:role/everest/admin/"
            "everest-gatec-administrator"
        ),
        "ordinaryRole": False,
        "mayAdministerKey": True,
        "requiresMfaSession": True,
        "requiresSeparateManagerApprovalForDisableOrDeletion": True,
    }:
        errors.append("kms-survival.json: admin/recovery boundary changed")
    if document.get("failureState") != "kms_access_blocked":
        errors.append("kms-survival.json: failure must block")
    if document.get("destroyingKeyIsDisposition") is not False:
        errors.append("kms-survival.json: destruction is not disposition")
    if document.get("deletionPreconditions") != [
        "version-aware-zero-dependency-inventory",
        "no-active-retention",
        "no-active-legal-hold",
        "no-audit-obligation",
        "no-recovery-copy-dependency",
        "separate-manager-approval",
        "cloudtrail-alerting-active",
        "maximum-30-day-waiting-period",
    ]:
        errors.append("kms-survival.json: deletion preconditions changed")
    return errors


def validate_all(resolved: bool = False) -> list[str]:
    """Validate all B2 assets without network or AWS access."""
    errors: list[str] = []
    try:
        validate_config(read_json(ROOT / "retention-config.json"), resolved)
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
    """Run offline validation and return process status."""
    errors = validate_all(resolved="--resolved" in sys.argv[1:])
    if errors:
        print("\n".join(errors))
        return 1
    print("Block-2 offline retention validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
