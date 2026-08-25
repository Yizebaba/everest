"""Fail-closed validation for externally retained raw artifacts.

This backend boundary validates locations and performs controlled, read-only
payload verification. It never writes, moves, or deletes raw payloads or
metadata sidecars.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


RAW_ROOT_ENVIRONMENT_VARIABLE = "EVEREST_RAW_ROOT"


class RawStorageConfigurationError(ValueError):
    """Raised when the configured raw-storage root is unsafe or unavailable."""


class RawStorageReferenceError(ValueError):
    """Raised when an artifact object reference escapes the configured root."""


class RawStorageArtifactError(ValueError):
    """Raised when an approved-root artifact fails payload verification."""


@dataclass(frozen=True)
class RawStoragePolicy:
    """Validated external raw root and safe object-reference resolver.

    ``raw_root`` must be an existing absolute directory outside
    ``repository_root``. Object references may be root-relative or absolute,
    but their resolved path must remain below ``raw_root``. ``verify_artifact``
    additionally checks that the payload is a regular non-symlink file and
    matches its descriptor SHA-256 and byte size. Provider metadata and sidecar
    attestations remain provider-owned scalar facts.
    """

    raw_root: Path
    repository_root: Path

    def __post_init__(self) -> None:
        """Normalize and validate the configured root without changing storage."""
        if not self.raw_root.is_absolute():
            raise RawStorageConfigurationError(
                "Raw storage root must be an absolute path"
            )
        if not self.repository_root.is_absolute():
            raise RawStorageConfigurationError(
                "Repository root must be an absolute path"
            )
        raw_root = self.raw_root.resolve()
        repository_root = self.repository_root.resolve()
        if not raw_root.exists() or not raw_root.is_dir():
            raise RawStorageConfigurationError(
                "Raw storage root must be an existing directory"
            )
        if raw_root.is_relative_to(repository_root):
            raise RawStorageConfigurationError(
                "Raw storage root must be outside the repository"
            )
        object.__setattr__(self, "raw_root", raw_root)
        object.__setattr__(self, "repository_root", repository_root)

    @classmethod
    def from_environment(
        cls,
        repository_root: Path,
        environment: Mapping[str, str] | None = None,
    ) -> "RawStoragePolicy":
        """Load the required raw root from environment configuration.

        ``environment`` permits deterministic configuration tests while normal
        runtime composition reads the process environment.
        """
        values = os.environ if environment is None else environment
        configured_root = values.get(RAW_ROOT_ENVIRONMENT_VARIABLE)
        if not configured_root:
            raise RawStorageConfigurationError(
                f"{RAW_ROOT_ENVIRONMENT_VARIABLE} must be configured"
            )
        return cls(Path(configured_root), repository_root)

    def resolve_object_reference(self, object_reference: str) -> Path:
        """Return an absolute artifact path only when it remains under raw root."""
        if not object_reference:
            raise RawStorageReferenceError(
                "Raw object reference must not be empty"
            )
        reference = Path(object_reference)
        candidate = (
            reference if reference.is_absolute() else self.raw_root / reference
        ).resolve()
        if not candidate.is_relative_to(self.raw_root):
            raise RawStorageReferenceError(
                "Raw object reference must resolve under the configured root"
            )
        return candidate

    def verify_artifact(
        self,
        object_reference: str,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> Path:
        """Verify payload hash and bytes beneath the approved root."""
        if (  # pylint: disable=unidiomatic-typecheck
            type(expected_sha256) is not str
            or len(expected_sha256) != 64
            or any(
                character not in "0123456789abcdefABCDEF"
                for character in expected_sha256
            )
        ):
            raise RawStorageArtifactError(
                "Raw artifact SHA-256 must be 64 hexadecimal characters"
            )
        # Exact type rejects booleans, which Python otherwise treats as integers.
        if (  # pylint: disable=unidiomatic-typecheck
            type(expected_size_bytes) is not int or expected_size_bytes < 0
        ):
            raise RawStorageArtifactError(
                "Raw artifact size must be a non-negative integer"
            )
        reference = Path(object_reference)
        lexical_candidate = (
            reference if reference.is_absolute() else self.raw_root / reference
        )
        try:
            lexical_parts = lexical_candidate.relative_to(self.raw_root).parts
        except ValueError as error:
            raise RawStorageArtifactError(
                "Raw artifact path must remain beneath the approved root"
            ) from error
        current = self.raw_root
        for part in lexical_parts:
            current /= part
            if current.is_symlink():
                raise RawStorageArtifactError(
                    "Raw artifact path must not contain symlinks"
                )
        candidate = self.resolve_object_reference(object_reference)
        current = self.raw_root
        try:
            for part in candidate.relative_to(self.raw_root).parts:
                current /= part
                if current.is_symlink():
                    raise RawStorageArtifactError(
                        "Raw artifact path must not contain symlinks"
                    )
            if not candidate.is_file():
                raise RawStorageArtifactError(
                    "Raw artifact must exist as a regular file"
                )
            digest = hashlib.sha256()
            size_bytes = 0
            with candidate.open("rb") as payload:
                for block in iter(lambda: payload.read(1024 * 1024), b""):
                    digest.update(block)
                    size_bytes += len(block)
        except OSError as error:
            raise RawStorageArtifactError(
                "Raw artifact could not be read for verification"
            ) from error
        if digest.hexdigest().lower() != expected_sha256.lower():
            raise RawStorageArtifactError("Raw artifact SHA-256 does not match")
        if size_bytes != expected_size_bytes:
            raise RawStorageArtifactError(
                "Raw artifact byte size does not match"
            )
        return candidate
