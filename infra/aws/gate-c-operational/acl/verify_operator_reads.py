"""Dry-run-first AWS configuration verification for the Gate C operator."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence


ACCOUNT_ID = "982408502231"
BUCKET = "zhufengxiangmu"
S3_REGION = "ap-south-1"
EXPECTED_CALLER_ARN = "arn:aws:iam::982408502231:user/everest-gatec-operator"
ARN = re.compile(
    r"^arn:aws:(?P<service>kms|rolesanywhere):"
    r"(?P<region>[a-z0-9-]+):982408502231:"
    r"(?P<resource>key/[A-Za-z0-9-]+|trust-anchor/[A-Za-z0-9-]+)$"
)


@dataclass(frozen=True)
class Check:
    """One allowed AWS read command."""

    name: str
    arguments: tuple[str, ...]


def parse_arn(
    value: str, service: str, resource_prefix: str
) -> tuple[str, str]:
    """Validate a supplied resource ARN and return its Region and resource ID."""
    match = ARN.fullmatch(value)
    if not match or match.group("service") != service:
        raise ValueError(f"invalid {service} ARN for account {ACCOUNT_ID}")
    resource = match.group("resource")
    prefix = f"{resource_prefix}/"
    if not resource.startswith(prefix):
        raise ValueError(f"invalid {service} resource type")
    return match.group("region"), resource.removeprefix(prefix)


def build_checks(
    aws_executable: str,
    profile: str,
    kms_key_arn: str,
    trust_anchor_arn: str,
) -> list[Check]:
    """Build the fixed allowlist of identity and configuration reads."""
    kms_region, _ = parse_arn(kms_key_arn, "kms", "key")
    anchor_region, anchor_id = parse_arn(
        trust_anchor_arn, "rolesanywhere", "trust-anchor"
    )
    common = ("--profile", profile, "--no-cli-pager", "--no-cli-auto-prompt")
    bucket = (
        "--bucket",
        BUCKET,
        "--expected-bucket-owner",
        ACCOUNT_ID,
        "--region",
        S3_REGION,
    )
    return [
        Check(
            "caller-identity",
            (
                aws_executable,
                "sts",
                "get-caller-identity",
                *common,
                "--query",
                "{Account:Account,Arn:Arn}",
                "--output",
                "json",
            ),
        ),
        *[
            Check(
                operation,
                (aws_executable, "s3api", operation, *bucket, *common),
            )
            for operation in (
                "get-bucket-location",
                "get-bucket-versioning",
                "get-object-lock-configuration",
                "get-public-access-block",
                "get-bucket-ownership-controls",
                "get-bucket-encryption",
            )
        ],
        Check(
            "describe-key",
            (
                aws_executable,
                "kms",
                "describe-key",
                "--key-id",
                kms_key_arn,
                "--region",
                kms_region,
                *common,
                "--query",
                "KeyMetadata.{AWSAccountId:AWSAccountId,Arn:Arn,"
                "KeyManager:KeyManager,KeySpec:KeySpec,KeyUsage:KeyUsage,"
                "KeyState:KeyState,Enabled:Enabled,MultiRegion:MultiRegion}",
                "--output",
                "json",
            ),
        ),
        Check(
            "get-trust-anchor",
            (
                aws_executable,
                "rolesanywhere",
                "get-trust-anchor",
                "--trust-anchor-id",
                anchor_id,
                "--region",
                anchor_region,
                *common,
                "--query",
                "trustAnchor.{trustAnchorId:trustAnchorId,"
                "trustAnchorArn:trustAnchorArn,name:name,enabled:enabled,"
                "sourceType:source.sourceType,createdAt:createdAt,"
                "updatedAt:updatedAt}",
                "--output",
                "json",
            ),
        ),
    ]


def redact(text: str) -> str:
    """Redact credential-shaped text defensively from process output."""
    patterns = (
        (r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "[REDACTED_ACCESS_KEY_ID]"),
        (
            r"(?i)(aws_secret_access_key|aws_session_token)\s*[:=]\s*\S+",
            r"\1=[REDACTED]",
        ),
        (
            r"-----BEGIN [^-]*PRIVATE KEY-----.*?"
            r"-----END [^-]*PRIVATE KEY-----",
            "[REDACTED_PRIVATE_KEY]",
        ),
    )
    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted, flags=re.DOTALL)
    return redacted


def render_command(arguments: Sequence[str]) -> str:
    """Render a readable command without shell execution semantics."""
    return subprocess.list2cmdline(list(arguments))


def run(checks: Sequence[Check], execute: bool) -> int:
    """Print the plan or execute each fixed read and sanitize its output."""
    if not execute:
        print("DRY RUN: no AWS request was sent; add --execute to run.")
        for check in checks:
            print(f"[{check.name}] {render_command(check.arguments)}")
        return 0

    failures = 0
    for check in checks:
        result = subprocess.run(
            check.arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if check.name == "caller-identity" and result.returncode == 0:
            try:
                identity = json.loads(result.stdout)
            except json.JSONDecodeError:
                result = subprocess.CompletedProcess(
                    result.args,
                    1,
                    result.stdout,
                    "caller identity did not return valid JSON",
                )
            else:
                if identity != {
                    "Account": ACCOUNT_ID,
                    "Arn": EXPECTED_CALLER_ARN,
                }:
                    result = subprocess.CompletedProcess(
                        result.args,
                        1,
                        "",
                        "unexpected caller account or principal; stopping",
                    )
        print(json.dumps({"check": check.name, "exitCode": result.returncode}))
        if result.stdout:
            print(redact(result.stdout.rstrip()))
        if result.stderr:
            print(redact(result.stderr.rstrip()), file=sys.stderr)
        failures += result.returncode != 0
        if check.name == "caller-identity" and result.returncode != 0:
            print("No resource reads were attempted.", file=sys.stderr)
            return 1
    return 1 if failures else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse non-secret parameters and perform dry-run or explicit execution."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--aws-executable", default="aws")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--kms-key-arn", required=True)
    parser.add_argument("--trust-anchor-arn", required=True)
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        checks = build_checks(
            arguments.aws_executable,
            arguments.profile,
            arguments.kms_key_arn,
            arguments.trust_anchor_arn,
        )
    except ValueError as error:
        parser.error(str(error))
    return run(checks, arguments.execute)


if __name__ == "__main__":
    raise SystemExit(main())
