"""Offline tests for Block-2 retention policy/resource contracts."""

from copy import deepcopy

import pytest

from render_assets import ROOT, read_json, substitute, validate_config
from validate_assets import (
    validate_all,
    validate_bucket_contract,
    validate_canary,
    validate_exact_version_and_state,
    validate_kms_survival,
    validate_policies,
    validate_roles,
)


def test_all_checked_in_assets_pass_offline_validation() -> None:
    """The complete inert B2 foundation satisfies every invariant."""
    assert not validate_all()


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("governanceQa", "bucketName", "wrong-bucket"),
        ("governanceQa", "mode", "COMPLIANCE"),
        ("governanceQa", "days", 179),
        ("governanceQa", "provisioningEnabled", True),
        ("audit", "bucketName", "wrong-audit"),
        ("audit", "mode", "GOVERNANCE"),
        ("audit", "days", 1094),
        ("audit", "provisioningEnabled", True),
        ("productionCanary", "enabled", True),
        ("productionCanary", "objectCount", 2),
        ("productionCanary", "maxObjectSizeBytes", 1025),
    ],
)
def test_config_rejects_authorization_scope_mutation(
    section: str, field: str, value: object
) -> None:
    """Names, defaults, provisioning, and canary limits fail closed."""
    config = read_json(ROOT / "retention-config.json")
    config[section][field] = value
    with pytest.raises(ValueError):
        validate_config(config, resolved=False)


def test_resolved_mode_rejects_placeholder_and_wrong_region_key() -> None:
    """A resolved package requires an exact same-account regional key ARN."""
    config = read_json(ROOT / "retention-config.json")
    with pytest.raises(ValueError, match="KMS ARN"):
        validate_config(config, resolved=True)
    config["kmsKeyArn"] = (
        "arn:aws:kms:us-east-1:982408502231:key/"
        "00000000-0000-0000-0000-000000000000"
    )
    with pytest.raises(ValueError, match="KMS ARN"):
        validate_config(config, resolved=True)


def test_resolved_mode_accepts_only_exact_account_region_key() -> None:
    """A syntactically exact supplied CMK ARN can pass offline rendering."""
    config = read_json(ROOT / "retention-config.json")
    config["kmsKeyArn"] = (
        "arn:aws:kms:ap-south-1:982408502231:key/"
        "00000000-0000-0000-0000-000000000000"
    )
    validate_config(config, resolved=True)


def test_substitution_is_deterministic_and_bounded() -> None:
    """Rendering replaces declared values without changing other facts."""
    value = {
        "kms": "${B2_KMS_KEY_ARN}",
        "trust": "${APPROVED_HUMAN_MFA_TRUST_POLICY}",
    }
    replacements = {"B2_KMS_KEY_ARN": "arn:fixture"}
    assert substitute(value, replacements) == substitute(value, replacements)
    assert substitute(value, replacements) == {
        "kms": "arn:fixture",
        "trust": "${APPROVED_HUMAN_MFA_TRUST_POLICY}",
    }


def test_bucket_resources_are_inert_locked_and_lifecycle_free() -> None:
    """Both authorized bucket contracts preserve their exact defaults."""
    for name in ("governance-qa-bucket.json", "audit-bucket.json"):
        assert not validate_bucket_contract(ROOT / "resources" / name)


def test_production_canary_is_exact_and_disabled() -> None:
    """No production canary can be enabled by this offline foundation."""
    assert validate_canary() == []


def test_role_separation_is_deny_or_disabled_by_default() -> None:
    """Legal, hold, and disposition identities have no usable authority."""
    assert not validate_roles()
    legal = read_json(ROOT / "policies" / "legal-authority-deny-only.json")
    assert legal["Statement"][0]["Effect"] == "Deny"
    assert legal["Statement"][0]["Action"] == "*"
    for name in (
        "hold-executor-disabled.json",
        "disposition-executor-disabled.json",
    ):
        assert read_json(ROOT / "policies" / name)["Statement"] == []


def test_policies_enforce_writer_and_bucket_negative_boundaries() -> None:
    """Bypass, no-version delete, Lifecycle, hold, and writer powers are denied."""
    assert not validate_policies()


def test_retention_admin_cannot_bypass_hold_delete_or_mutate_bucket() -> None:
    """Retention administration is exact readback plus retention extension."""
    document = read_json(ROOT / "policies" / "retention-admin.json")
    actions = {
        action
        for statement in document["Statement"]
        for action in statement["Action"]
    }
    assert "s3:PutObjectRetention" in actions
    assert actions.isdisjoint(
        {
            "s3:BypassGovernanceRetention",
            "s3:DeleteObject",
            "s3:DeleteObjectVersion",
            "s3:PutObjectLegalHold",
            "s3:PutLifecycleConfiguration",
        }
    )


def test_audit_policy_reads_metadata_but_not_payload_or_mutation() -> None:
    """Audit readers see retention controls without raw object payloads."""
    document = read_json(ROOT / "policies" / "audit-read-only.json")
    actions = {
        action
        for statement in document["Statement"]
        for action in statement["Action"]
    }
    assert "s3:GetObjectRetention" in actions
    assert "s3:GetObjectAttributes" in actions
    assert actions.isdisjoint(
        {
            "s3:GetObject",
            "s3:GetObjectVersion",
            "s3:DeleteObjectVersion",
            "s3:PutObjectLegalHold",
            "s3:PutObjectRetention",
        }
    )


def test_exact_version_and_state_machine_are_fail_closed() -> None:
    """Storage workflows require exact versions and disable B2 destructive work."""
    assert not validate_exact_version_and_state()


def test_kms_survival_blocks_cryptographic_deletion_shortcuts() -> None:
    """Retained bytes remain dependent on a surviving customer-managed key."""
    assert not validate_kms_survival()
    policy = read_json(ROOT / "policies" / "kms-survival-deny.json")
    assert set(policy["Statement"][0]["Action"]) == {
        "kms:DisableKey",
        "kms:ScheduleKeyDeletion",
    }


def test_mutated_canary_validator_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The validator rejects any attempt to enable the canary."""
    original = read_json

    def mutated_read(path):  # type annotation intentionally inferred by pytest
        document = deepcopy(original(path))
        if path.name == "production-canary.json":
            document["enabled"] = True
        return document

    monkeypatch.setattr("validate_assets.read_json", mutated_read)
    assert "production-canary.json: invalid enabled" in validate_canary()
