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


@dataclass(frozen=True)
class RetrievedArtifact:
    """A verified local artifact produced for one immutable request."""

    path: Path
    provider: str
    request: RetrievalRequest
    sha256: str
    size_bytes: int
    media_type: str = "application/x-grib2"

    def __post_init__(self) -> None:
        artifact_path = Path(self.path)
        if not artifact_path.is_absolute():
            raise ValueError("retrieved artifact path must be absolute")
        object.__setattr__(self, "path", artifact_path)

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
        _reject_symlink_components(request.target_dir)
        _reject_symlink_components(candidate)
        target_root = request.target_dir.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        if resolved != target_root and target_root not in resolved.parents:
            raise ValueError("retrieved artifact must remain under target_dir")
        size_bytes, sha256 = _verified_file_facts(resolved)
        if size_bytes == 0:
            raise ValueError("retrieved artifact is empty")
        if size_bytes > _MAX_RETRIEVED_BYTES:
            raise ValueError("retrieved artifact exceeds byte limit")
        return cls(
            path=resolved,
            provider=provider,
            request=request,
            sha256=sha256,
            size_bytes=size_bytes,
        )


def _reject_symlink_components(path: Path) -> None:
    """Inspect the lexical path, without resolving away any symlink."""
    candidate = Path(path)
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("retrieval path must not contain symlinks")


def _verified_file_facts(path: Path) -> tuple[int, str]:
    """Open without following the final link where supported, then hash."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise FileNotFoundError(
            f"retrieved artifact does not exist: {path}"
        ) from error

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
        },
    )


__all__ = [
    "RetrievalRequest",
    "RetrievedArtifact",
    "open_grib_dataset",
]
