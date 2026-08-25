"""Unit tests for the external raw-storage enforcement boundary."""

import hashlib
from pathlib import Path

import pytest

from everest_api.raw_storage import (
    RAW_ROOT_ENVIRONMENT_VARIABLE,
    RawStorageArtifactError,
    RawStorageConfigurationError,
    RawStoragePolicy,
    RawStorageReferenceError,
)


def _policy(tmp_path: Path) -> tuple[RawStoragePolicy, Path]:
    """Create an external policy and raw root for verification tests."""
    repository_root = tmp_path / "repository"
    raw_root = tmp_path / "external-raw"
    repository_root.mkdir()
    raw_root.mkdir()
    return RawStoragePolicy(raw_root, repository_root), raw_root


def test_environment_root_outside_repository_resolves_reference(
    tmp_path: Path,
) -> None:
    """Accept an absolute external root and resolve a root-relative artifact."""
    repository_root = tmp_path / "repository"
    raw_root = tmp_path / "external-raw"
    repository_root.mkdir()
    raw_root.mkdir()

    policy = RawStoragePolicy.from_environment(
        repository_root, {RAW_ROOT_ENVIRONMENT_VARIABLE: str(raw_root)}
    )

    assert policy.resolve_object_reference("gfs/example.grib2") == (
        raw_root / "gfs" / "example.grib2"
    )


def test_missing_environment_root_is_rejected(tmp_path: Path) -> None:
    """Fail closed when the required external-root configuration is absent."""
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    with pytest.raises(
        RawStorageConfigurationError, match="must be configured"
    ):
        RawStoragePolicy.from_environment(repository_root, {})


def test_absent_configured_root_directory_is_rejected(tmp_path: Path) -> None:
    """Reject a configured location when its external directory does not exist."""
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    with pytest.raises(
        RawStorageConfigurationError, match="existing directory"
    ):
        RawStoragePolicy.from_environment(
            repository_root,
            {RAW_ROOT_ENVIRONMENT_VARIABLE: str(tmp_path / "absent-raw")},
        )


def test_relative_environment_root_is_rejected(tmp_path: Path) -> None:
    """Reject relative storage locations rather than resolving them implicitly."""
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    with pytest.raises(RawStorageConfigurationError, match="absolute"):
        RawStoragePolicy.from_environment(
            repository_root, {RAW_ROOT_ENVIRONMENT_VARIABLE: "external-raw"}
        )


def test_repository_root_is_rejected_as_raw_storage(tmp_path: Path) -> None:
    """Reject an existing raw root located inside repository content."""
    repository_root = tmp_path / "repository"
    raw_root = repository_root / "data" / "raw"
    raw_root.mkdir(parents=True)

    with pytest.raises(RawStorageConfigurationError, match="outside"):
        RawStoragePolicy.from_environment(
            repository_root, {RAW_ROOT_ENVIRONMENT_VARIABLE: str(raw_root)}
        )


def test_traversal_reference_is_rejected(tmp_path: Path) -> None:
    """Reject an artifact path that escapes the configured external root."""
    repository_root = tmp_path / "repository"
    raw_root = tmp_path / "external-raw"
    repository_root.mkdir()
    raw_root.mkdir()
    policy = RawStoragePolicy(raw_root, repository_root)

    with pytest.raises(RawStorageReferenceError, match="under the configured"):
        policy.resolve_object_reference("../outside.grib2")


def test_missing_artifact_is_rejected(tmp_path: Path) -> None:
    """Reject a descriptor whose payload is absent."""
    policy, _ = _policy(tmp_path)
    with pytest.raises(RawStorageArtifactError, match="regular file"):
        policy.verify_artifact("missing.grib2", "a" * 64, 1)


def test_replaced_artifact_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    """Reject a replaced payload whose bytes no longer match its descriptor."""
    policy, raw_root = _policy(tmp_path)
    (raw_root / "artifact.grib2").write_bytes(b"replacement")
    with pytest.raises(RawStorageArtifactError, match="does not match"):
        policy.verify_artifact("artifact.grib2", "a" * 64, 11)


def test_replaced_artifact_size_mismatch_is_rejected(tmp_path: Path) -> None:
    """Reject a descriptor whose byte size differs from the bytes hashed."""
    policy, raw_root = _policy(tmp_path)
    payload = raw_root / "artifact.grib2"
    payload.write_bytes(b"approved payload")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    with pytest.raises(RawStorageArtifactError, match="byte size"):
        policy.verify_artifact("artifact.grib2", digest, 1)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    """Reject a payload path redirected outside the approved root."""
    policy, raw_root = _policy(tmp_path)
    outside = tmp_path / "outside.grib2"
    outside.write_bytes(b"secret")
    link = raw_root / "escaped.grib2"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable in this environment")
    with pytest.raises(RawStorageArtifactError, match="symlinks"):
        policy.verify_artifact("escaped.grib2", "a" * 64, 6)


def test_valid_file_is_verified(tmp_path: Path) -> None:
    """Accept a regular approved-root file with the expected SHA-256."""
    policy, raw_root = _policy(tmp_path)
    payload = raw_root / "valid.grib2"
    payload.write_bytes(b"approved payload")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    assert policy.verify_artifact("valid.grib2", digest, 16) == payload
