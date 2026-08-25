"""Offline tests for Block-1 policy validation."""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from render_policies import (
    kms_policy,
    read_json,
    render,
    role_arn,
    validate_config,
)
from validate_policies import (
    ROOT,
    validate_all,
    validate_kms_document,
    validate_resource_document,
)
from verify_operator_reads import EXPECTED_CALLER_ARN, build_checks, redact, run


def test_templates_parse_and_pass_static_checks() -> None:
    """All checked-in JSON templates pass offline invariants."""
    assert not validate_all()
    for path in (ROOT / "policies").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_production_mode_rejects_unresolved_placeholders() -> None:
    """Production rendering must fail closed until every value is supplied."""
    assert any(
        "unresolved production placeholder" in error
        for error in validate_all(production=True)
    )


def test_cli_is_offline_and_succeeds_for_templates() -> None:
    """The normal validator performs no network or AWS operation."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "validate_policies.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "offline policy validation passed" in result.stdout


def test_renderer_is_deterministic_and_binds_all_four_sources(
    tmp_path: Path,
) -> None:
    """Rendering the same strict config produces identical role assets."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    first = tmp_path / "first"
    second = tmp_path / "second"
    render(config, first, production=True)
    render(config, second, production=True)
    first_files = sorted(
        path.relative_to(first) for path in first.rglob("*.json")
    )
    second_files = sorted(
        path.relative_to(second) for path in second.rglob("*.json")
    )
    assert first_files == second_files

    for workload in config["workloads"]:
        assert role_arn(config, workload) == (
            f"arn:aws:iam::{config['accountId']}:role/everest/"
            f"{workload['roleName']}"
        )
    for relative in first_files:
        assert (first / relative).read_bytes() == (
            second / relative
        ).read_bytes()
    assert len(list((first / "policies").glob("*.json"))) == 4
    assert len(list((first / "profiles").glob("*.json"))) == 4
    assert len(list((first / "trust").glob("*.json"))) == 4


@pytest.mark.parametrize(
    "field,value",
    [
        ("region", "us-east-1"),
        ("multipartUploads", True),
        ("maxObjectSizeBytes", 0),
    ],
)
def test_renderer_rejects_security_mutations(field: str, value: object) -> None:
    """Each high-risk config mutation fails closed."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    config[field] = value
    with pytest.raises(ValueError):
        validate_config(config, production=True)


def test_renderer_rejects_workload_mapping_mutation() -> None:
    """A prefix/role/source mismatch cannot render."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    mutated = deepcopy(config)
    mutated["workloads"][0]["prefix"] = "noaa-gfs"
    with pytest.raises(ValueError):
        validate_config(mutated, production=True)


def test_validator_rejects_disabled_bucket_key() -> None:
    """BucketKeyEnabled=false cannot pass the Block-1 resource contract."""
    resource = read_json(ROOT / "resource-config.json")
    resource["defaultEncryption"]["bucketKeyEnabled"] = False
    assert "resource: S3 Bucket Key must be enabled" in (
        validate_resource_document(resource, production=False)
    )


@pytest.mark.parametrize(
    "context",
    [
        "arn:aws:s3:::zhufengxiangmu/ecmwf-ifs/object.grib2",
        "arn:aws:s3:::zhufengxiangmu/ecmwf-ifs/*",
        "arn:aws:s3:::wrong-bucket",
    ],
)
def test_validator_rejects_non_bucket_kms_context(context: str) -> None:
    """Object, prefix, and wrong-bucket contexts fail closed."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    config["rawBucket"] = "zhufengxiangmu"
    document = kms_policy(config)
    document["Statement"][0]["Condition"]["StringEquals"][
        "kms:EncryptionContext:aws:s3:arn"
    ] = context
    assert "kms: encryption context must be exact bucket ARN" in (
        validate_kms_document(document, "zhufengxiangmu")
    )


def test_renderer_uses_exact_bucket_key_context() -> None:
    """Rendered KMS policy uses the Bucket Key bucket ARN, not a prefix."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    config["rawBucket"] = "zhufengxiangmu"
    document = kms_policy(config)
    statement = document["Statement"][0]
    equals = statement["Condition"]["StringEquals"]
    assert equals["kms:ViaService"] == "s3.ap-south-1.amazonaws.com"
    assert equals["kms:EncryptionContext:aws:s3:arn"] == (
        "arn:aws:s3:::zhufengxiangmu"
    )


def test_renderer_rejects_ap_east_trust_anchor_for_production() -> None:
    """The quarantined cross-Region trust anchor cannot be promoted."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    config["trustAnchorArn"] = (
        "arn:aws:rolesanywhere:ap-east-1:123456789012:"
        "trust-anchor/quarantined"
    )
    with pytest.raises(ValueError, match="trustAnchorArn"):
        validate_config(config, production=True)


@pytest.mark.parametrize(
    "key_identifier",
    [
        "alias/aws/s3",
        "arn:aws:kms:ap-south-1:123456789012:alias/aws/s3",
    ],
)
def test_renderer_rejects_aws_s3_managed_key_for_production(
    key_identifier: str,
) -> None:
    """An AWS-managed S3 key is not a customer-managed key ARN."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    config["kmsKeyArn"] = key_identifier
    with pytest.raises(ValueError, match="kmsKeyArn"):
        validate_config(config, production=True)


def test_renderer_accepts_supplied_candidate_bucket_name() -> None:
    """The selected valid S3 candidate can be rendered after ARN collection."""
    config = read_json(ROOT / "fixtures" / "render-config.json")
    config["rawBucket"] = "zhufengxiangmu"
    validate_config(config, production=True)


def test_secret_fixture_matches_all_required_patterns() -> None:
    """Synthetic fixture proves every forbidden secret class is covered."""
    fixture = (ROOT / "fixtures" / "secret-patterns.json").read_text(
        encoding="utf-8"
    )
    assert all(
        marker in fixture
        for marker in (
            "AKIA",
            "ASIA",
            "PRIVATE KEY",
            "session_token",
            "client_secret",
            "password",
        )
    )


def test_operator_policy_is_exact_read_only_configuration_scope() -> None:
    """Operator policy cannot mutate, enumerate, or read object payloads."""
    policy = read_json(
        ROOT / "policies" / "operator-configuration-read-only.json"
    )
    statements = policy["Statement"]
    actions = {
        action
        for statement in statements
        for action in (
            [statement["Action"]]
            if isinstance(statement["Action"], str)
            else statement["Action"]
        )
    }
    assert actions == {
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetBucketOwnershipControls",
        "s3:GetEncryptionConfiguration",
        "kms:DescribeKey",
        "rolesanywhere:GetTrustAnchor",
    }
    assert statements[0]["Resource"] == "arn:aws:s3:::zhufengxiangmu"
    assert all(statement["Effect"] == "Allow" for statement in statements)
    assert not actions.intersection(
        {"s3:GetObject", "s3:GetObjectVersion", "s3:GetObjectAttributes"}
    )


def test_operator_verifier_defaults_to_offline_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry-run prints only the fixed command plan and never starts a process."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("dry-run contacted a process"),
    )
    checks = build_checks(
        "aws",
        "default",
        "arn:aws:kms:ap-south-1:982408502231:key/fixture",
        (
            "arn:aws:rolesanywhere:ap-east-1:982408502231:"
            "trust-anchor/00000000-0000-0000-0000-000000000000"
        ),
    )
    assert run(checks, execute=False) == 0
    assert len(checks) == 9
    forbidden = {"put-object", "create-bucket", "delete-object", "get-object"}
    assert all(
        forbidden.isdisjoint(check.arguments)
        and "assume-role" not in check.arguments
        for check in checks
    )


def test_operator_output_redacts_credentials() -> None:
    """Credential-shaped output is removed before display."""
    value = (
        "AKIA0000000000000000 aws_session_token=secret "
        "-----BEGIN PRIVATE KEY-----x-----END PRIVATE KEY-----"
    )
    result = redact(value)
    assert "AKIA" not in result
    assert "secret" not in result
    assert "BEGIN PRIVATE KEY" not in result


def test_operator_verifier_stops_on_unexpected_caller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Execution fails closed before resource reads for another principal."""
    calls = 0

    def fake_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess:
        del args, kwargs
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(
            [],
            0,
            '{"Account":"000000000000","Arn":"unexpected"}',
            "",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    checks = build_checks(
        "aws",
        "default",
        "arn:aws:kms:ap-south-1:982408502231:key/fixture",
        (
            "arn:aws:rolesanywhere:ap-east-1:982408502231:"
            "trust-anchor/00000000-0000-0000-0000-000000000000"
        ),
    )
    assert run(checks, execute=True) == 1
    assert calls == 1
    assert EXPECTED_CALLER_ARN.endswith("user/everest-gatec-operator")
