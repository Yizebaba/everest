"""Mutation-heavy offline tests for Block-2 retention contracts."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from render_assets import (
    ROOT,
    read_json,
    render,
    scalar_strings,
    validate_config,
)
from validate_assets import (
    validate_all,
    validate_bucket_contract,
    validate_canary,
    validate_exact_version_and_state,
    validate_kms_survival,
    validate_policies,
    validate_roles,
)


def _resolved_config() -> dict[str, Any]:
    """Return a syntactically resolved offline fixture."""
    config = read_json(ROOT / "retention-config.json")
    config["kmsKeyArn"] = (
        "arn:aws:kms:ap-south-1:982408502231:key/"
        "00000000-0000-0000-0000-000000000000"
    )
    config["principals"][
        "brokerExecutorPrincipalArn"
    ] = "arn:aws:iam::982408502231:role/everest/b2-broker-executor"
    config["principals"][
        "auditHumanPrincipalArn"
    ] = "arn:aws:iam::982408502231:role/everest/b2-audit-reviewer"
    return config


def _mutating_reader(
    target: str, mutation: Any
) -> Any:  # pylint: disable=unnecessary-lambda-assignment
    """Build a read_json replacement that mutates one named document."""
    original = read_json

    def reader(path: Path) -> dict[str, Any]:
        document = deepcopy(original(path))
        if path.name == target:
            mutation(document)
        return document

    return reader


def test_all_checked_in_assets_pass_offline_validation() -> None:
    """The complete B2 review package satisfies every invariant."""
    assert not validate_all()


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("governanceQa", "bucketName", "wrong"),
        ("governanceQa", "mode", "COMPLIANCE"),
        ("governanceQa", "days", 179),
        ("audit", "days", 1094),
        ("productionCanary", "enabled", True),
        ("productionCanary", "objectCount", 2),
    ],
)
def test_config_scope_mutations_fail_closed(
    section: str, field: str, value: object
) -> None:
    """Authorized names, modes, durations, and gates are immutable."""
    config = read_json(ROOT / "retention-config.json")
    config[section][field] = value
    with pytest.raises(ValueError):
        validate_config(config, resolved=False)


@pytest.mark.parametrize("mutation", ["missing", "unknown"])
def test_config_rejects_missing_and_unknown_fields(mutation: str) -> None:
    """Top-level schema drift never passes silently."""
    config = read_json(ROOT / "retention-config.json")
    if mutation == "missing":
        del config["lifecycleRules"]
    else:
        config["unexpected"] = True
    with pytest.raises(ValueError, match="fields must be exact"):
        validate_config(config, resolved=False)


def test_resolved_config_requires_exact_arns_and_no_placeholders() -> None:
    """A rendered package requires account-scoped named role and KMS ARNs."""
    validate_config(_resolved_config(), resolved=True)
    config = _resolved_config()
    config["principals"]["auditHumanPrincipalArn"] = "${STILL_FAKE}"
    with pytest.raises(ValueError):
        validate_config(config, resolved=True)


def test_renderer_outputs_every_json_and_no_placeholder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The resolved package contains all JSON assets and no marker."""
    written: dict[str, dict[str, Any]] = {}

    def capture(path: Path, document: dict[str, Any]) -> None:
        written[path.as_posix()] = document

    monkeypatch.setattr("render_assets.write_json", capture)
    output = Path("resolved-package")
    render(_resolved_config(), output)
    expected = {
        (output / path.relative_to(ROOT)).as_posix()
        for path in ROOT.rglob("*.json")
    }
    assert set(written) == expected
    assert not any(
        "${" in value
        for document in written.values()
        for value in scalar_strings(document)
    )
    contract = written["resolved-package/roles/role-contracts.json"]
    role_names = {role["name"] for role in contract["roles"]}
    absent_names = {
        "legal-authority-placeholder",
        "hold-executor",
        "disposition-executor",
    }
    assert set(contract["absentRoles"]) == absent_names
    assert role_names.isdisjoint(absent_names)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["blockPublicAccess"].pop("blockPublicAcls"),
        lambda value: value["blockPublicAccess"].update({"extra": True}),
        lambda value: value["blockPublicAccess"].update(
            {"restrictPublicBuckets": False}
        ),
        lambda value: value.update({"objectOwnership": "ObjectWriter"}),
        lambda value: value["defaultEncryption"].update(
            {"kmsKeyArn": "arn:wrong"}
        ),
        lambda value: value.update({"unknown": True}),
    ],
)
def test_bucket_mutations_fail_closed(
    monkeypatch: pytest.MonkeyPatch, mutation: Any
) -> None:
    """BPA, ownership, KMS resource, and schema drift are rejected."""
    monkeypatch.setattr(
        "validate_assets.read_json",
        _mutating_reader("governance-qa-bucket.json", mutation),
    )
    assert validate_bucket_contract(
        ROOT / "resources" / "governance-qa-bucket.json"
    )


def test_provisioning_order_is_create_set_readback_then_deny() -> None:
    """The lock-mutation deny cannot block default-retention provisioning."""
    document = read_json(ROOT / "resources" / "governance-qa-bucket.json")
    assert document["provisioningOrder"][-2:] == [
        "read-back-object-lock-governance-180-days",
        "attach-bucket-lock-mutation-deny",
    ]
    assert document["lifecycleRules"] == []


def test_canary_unknown_field_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The canary schema rejects additive authorization drift."""
    monkeypatch.setattr(
        "validate_assets.read_json",
        _mutating_reader(
            "production-canary.json",
            lambda value: value.update({"unexpected": True}),
        ),
    )
    assert validate_canary()


def test_roles_use_real_inactivity_and_exact_activation() -> None:
    """Dangerous identities are absent; admin and broker are uncreated."""
    assert validate_roles() == []
    document = read_json(ROOT / "roles" / "role-contracts.json")
    states = {
        role["name"]: role["deploymentState"] for role in document["roles"]
    }
    assert states["everest-retention-admin"] == "uncreated"
    assert set(document["absentRoles"]) == {
        "legal-authority-placeholder",
        "hold-executor",
        "disposition-executor",
    }


def test_fake_enabled_role_shape_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An enabled flag cannot masquerade as IAM role inactivity."""

    def mutate(value: dict[str, Any]) -> None:
        value["roles"][0]["enabled"] = False

    monkeypatch.setattr(
        "validate_assets.read_json",
        _mutating_reader("role-contracts.json", mutate),
    )
    assert validate_roles()


@pytest.mark.parametrize(
    ("target", "mutation"),
    [
        (
            "audit-read-only.json",
            lambda value: value["Statement"][1]["Action"].append(
                "s3:GetObjectAttributes"
            ),
        ),
        (
            "audit-read-only.json",
            lambda value: value["Statement"][1].update({"Effect": "Deny"}),
        ),
        (
            "audit-read-only.json",
            lambda value: value["Statement"][1].update({"Resource": "*"}),
        ),
        (
            "retention-admin.json",
            lambda value: value["Statement"][2]["Condition"].clear(),
        ),
        (
            "bucket-explicit-deny.json",
            lambda value: value["Statement"].__setitem__(
                3, value["Statement"][2]
            ),
        ),
        (
            "kms-survival-deny.json",
            lambda value: value["Statement"][0].update({"Resource": "*"}),
        ),
    ],
)
def test_policy_action_effect_resource_principal_mutations_fail(
    monkeypatch: pytest.MonkeyPatch, target: str, mutation: Any
) -> None:
    """Exact policy semantics reject invalid actions and weakened boundaries."""
    monkeypatch.setattr(
        "validate_assets.read_json", _mutating_reader(target, mutation)
    )
    assert validate_policies()


def test_audit_policy_is_valid_metadata_only_action_set() -> None:
    """Audit reads versions, retention, and legal hold without payload access."""
    document = read_json(ROOT / "policies" / "audit-read-only.json")
    actions = {
        action
        for statement in document["Statement"]
        for action in statement["Action"]
    }
    assert {
        "s3:ListBucketVersions",
        "s3:GetObjectRetention",
        "s3:GetObjectLegalHold",
    }.issubset(actions)
    assert "s3:GetObjectAttributes" not in actions
    assert actions.isdisjoint({"s3:GetObject", "s3:GetObjectVersion"})


def test_governance_qa_rejects_compliance_and_arbitrary_date() -> None:
    """Only the broker's calculated Governance extension is authorized."""
    assert not validate_exact_version_and_state()
    operation = read_json(ROOT / "exact-version-operation.json")
    guard = operation["retentionMutation"]
    assert guard["directHumanCallAllowed"] is False
    assert guard["executorMode"] == "GOVERNANCE"
    assert guard["arbitraryDateAllowed"] is False
    assert guard["complianceModeAllowedInGovernanceQa"] is False


def test_timing_fields_are_required_and_immutable_contract_facts() -> None:
    """Retention arithmetic is based on immutable S3 timing evidence."""
    operation = read_json(ROOT / "exact-version-operation.json")
    assert {"versionCreatedAt", "s3LastModified"}.issubset(
        operation["requiredIdentityFields"]
    )
    assert set(operation["immutableTimingFields"]) == {
        "versionCreatedAt",
        "s3LastModified",
    }


def test_timing_contract_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing a timing meaning is rejected by the offline validator."""
    monkeypatch.setattr(
        "validate_assets.read_json",
        _mutating_reader(
            "exact-version-operation.json",
            lambda value: value["immutableTimingFields"].update(
                {"s3LastModified": "mutable"}
            ),
        ),
    )
    assert validate_exact_version_and_state()


def test_kms_survival_names_ordinary_and_admin_recovery_roles() -> None:
    """Ordinary-role deny excludes only the named MFA recovery boundary."""
    assert not validate_kms_survival()
    document = read_json(ROOT / "kms-survival.json")
    assert len(document["ordinaryRoleArns"]) == 7
    boundary = document["kmsAdministratorRecoveryBoundary"]
    assert boundary["principalArn"].endswith("everest-gatec-administrator")
    assert boundary["requiresMfaSession"] is True


def test_kms_required_property_mutation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CMK type and survivability schema cannot drift."""
    monkeypatch.setattr(
        "validate_assets.read_json",
        _mutating_reader(
            "kms-survival.json",
            lambda value: value["requiredKeyProperties"].update(
                {"keyManager": "AWS"}
            ),
        ),
    )
    assert validate_kms_survival()
