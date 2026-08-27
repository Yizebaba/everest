"""Shared immutable contracts and lazy GRIB decoding for weather retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
from typing import Any, Callable

_MAX_RETRIEVED_BYTES = 512 * 1024 * 1024
_O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


@dataclass(frozen=True)
class RetrievalRequest:
    """One explicit run, forecast step, field inventory, and destination."""

    cycle: datetime
    lead_hours: int
    variables: tuple[str, ...]
    target_dir: Path

    def __post_init__(self) -> None:
        if self.cycle.tzinfo is None or self.cycle.utcoffset() is None:
            raise ValueError("retrieval cycle must be timezone-aware")
        if self.lead_hours < 0:
            raise ValueError("retrieval lead_hours must not be negative")
        if not self.variables:
            raise ValueError("retrieval requires at least one variable")
        if any(not variable.strip() for variable in self.variables):
            raise ValueError("retrieval variables must not be blank")
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("retrieval variables must be unique")
        target_dir = Path(self.target_dir)
        if not target_dir.is_absolute():
            raise ValueError("retrieval target_dir must be absolute")
        _reject_symlink_components(target_dir)
        object.__setattr__(self, "cycle", self.cycle.astimezone(timezone.utc))
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "target_dir", target_dir.resolve())


@dataclass(frozen=True, init=False)
class RetrievedArtifact:
    """A verified local artifact produced for one immutable request."""

    path: Path
    provider: str
    request: RetrievalRequest
    sha256: str
    size_bytes: int
    media_type: str = "application/x-grib2"

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("RetrievedArtifact must be created with from_path")

    @classmethod
    def from_path(
        cls,
        path: Path,
        provider: str,
        request: RetrievalRequest,
    ) -> "RetrievedArtifact":
        """Verify a provider result and derive deterministic integrity facts."""
        candidate = Path(path)
        if not candidate.is_absolute():
            raise ValueError("retrieved artifact path must be absolute")
        verified_path, size_bytes, sha256 = _verified_artifact_facts(
            candidate, request.target_dir
        )
        if size_bytes == 0:
            raise ValueError("retrieved artifact is empty")
        if size_bytes > _MAX_RETRIEVED_BYTES:
            raise ValueError("retrieved artifact exceeds byte limit")
        artifact = object.__new__(cls)
        object.__setattr__(artifact, "path", verified_path)
        object.__setattr__(artifact, "provider", provider)
        object.__setattr__(artifact, "request", request)
        object.__setattr__(artifact, "sha256", sha256)
        object.__setattr__(artifact, "size_bytes", size_bytes)
        object.__setattr__(artifact, "media_type", "application/x-grib2")
        return artifact


def _reject_symlink_components(path: Path) -> None:
    """Inspect the lexical path, without resolving away any symlink."""
    candidate = Path(path)
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("retrieval path must not contain symlinks")


def _verified_artifact_facts(
    candidate: Path, target_dir: Path
) -> tuple[Path, int, str]:
    """Open within target_dir and derive facts from the held descriptor."""
    if _supports_secure_dir_fd_traversal():
        relative_parts = _relative_artifact_parts(candidate, target_dir)
        descriptor = _open_beneath_target(target_dir, relative_parts)
        size_bytes, sha256 = _file_facts_from_descriptor(descriptor, candidate)
        return candidate, size_bytes, sha256

    # Some platforms (notably Windows) cannot perform openat-style traversal.
    # Retain strict static rejection there rather than silently dropping checks.
    _reject_symlink_components(target_dir)
    _reject_symlink_components(candidate)
    target_root = target_dir.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    if resolved != target_root and target_root not in resolved.parents:
        raise ValueError("retrieved artifact must remain under target_dir")
    size_bytes, sha256 = _verified_file_facts(resolved)
    return resolved, size_bytes, sha256


def _supports_secure_dir_fd_traversal() -> bool:
    """Return whether this runtime supports race-safe component traversal."""
    return (
        os.name == "posix"
        and os.open in os.supports_dir_fd
        and _O_NOFOLLOW != 0
        and _O_DIRECTORY != 0
    )


def _relative_artifact_parts(
    candidate: Path, target_dir: Path
) -> tuple[str, ...]:
    """Return a lexical child path without permitting parent traversal."""
    try:
        relative = candidate.relative_to(target_dir)
    except ValueError as error:
        raise ValueError(
            "retrieved artifact must remain under target_dir"
        ) from error
    if not relative.parts or any(
        part in ("", ".", "..") for part in relative.parts
    ):
        raise ValueError("retrieved artifact must remain under target_dir")
    return relative.parts


def _directory_open_flags() -> int:
    return (
        os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    )


def _open_at(component: str, flags: int, *, dir_fd: int) -> int:
    """Injectable openat seam used by deterministic substitution tests."""
    return os.open(component, flags, dir_fd=dir_fd)


def _open_directory_path(path: Path) -> int:
    """Open an absolute directory one no-follow component at a time."""
    flags = _directory_open_flags()
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            next_descriptor = _open_at(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except OSError as error:
        os.close(descriptor)
        raise ValueError(
            "retrieval path failed secure no-follow symlink traversal"
        ) from error


def _open_beneath_target(
    target_dir: Path, relative_parts: tuple[str, ...]
) -> int:
    """Open a child without resolving names outside held directory fds."""
    descriptor = _open_directory_path(target_dir)
    try:
        for component in relative_parts[:-1]:
            next_descriptor = _open_at(
                component, _directory_open_flags(), dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = next_descriptor
        file_flags = (
            os.O_RDONLY
            | _O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_BINARY", 0)
        )
        return _open_at(relative_parts[-1], file_flags, dir_fd=descriptor)
    except OSError as error:
        raise ValueError(
            "retrieval path failed secure no-follow symlink traversal"
        ) from error
    finally:
        os.close(descriptor)


def _verified_file_facts(path: Path) -> tuple[int, str]:
    """Fallback open without following the final link where supported."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise FileNotFoundError(
            f"retrieved artifact does not exist: {path}"
        ) from error

    return _file_facts_from_descriptor(descriptor, path)


def _file_facts_from_descriptor(descriptor: int, path: Path) -> tuple[int, str]:
    """Validate and hash the exact file represented by descriptor."""
    digest = hashlib.sha256()
    with os.fdopen(descriptor, "rb") as stream:
        file_status = os.fstat(stream.fileno())
        if not stat.S_ISREG(file_status.st_mode):
            raise FileNotFoundError(
                f"retrieved artifact does not exist: {path}"
            )
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return file_status.st_size, digest.hexdigest()


def _import_xarray() -> Any:
    """Import the ingestion-only xarray dependency on first use."""
    try:
        import xarray as xr  # pylint: disable=import-outside-toplevel
    except ImportError as error:
        raise RuntimeError(
            "weather ingestion requires the optional xarray/cfgrib extras"
        ) from error
    return xr


def open_grib_dataset(
    path: Path,
    *,
    filter_by_keys: dict[str, Any],
    opener: Callable[..., Any] | None = None,
) -> Any:
    """Open one homogeneous GRIB group without creating a cfgrib index file."""
    if not filter_by_keys:
        raise ValueError("cfgrib filter_by_keys must be explicit and nonempty")
    open_dataset = opener or _import_xarray().open_dataset
    return open_dataset(
        Path(path),
        engine="cfgrib",
        backend_kwargs={
            "indexpath": "",
            "filter_by_keys": dict(filter_by_keys),
            # cfgrib's process-global geography cache can grow across many
            # grid/cycle reads in a long-running scheduler worker.
            "cache_geo_coords": False,
        },
    )


__all__ = [
    "RetrievalRequest",
    "RetrievedArtifact",
    "open_grib_dataset",
]
