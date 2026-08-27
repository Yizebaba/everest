"""Shared immutable contracts and lazy GRIB decoding for weather retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
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
        object.__setattr__(self, "cycle", self.cycle.astimezone(timezone.utc))
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "target_dir", Path(self.target_dir))


@dataclass(frozen=True)
class RetrievedArtifact:
    """A verified local artifact produced for one immutable request."""

    path: Path
    provider: str
    request: RetrievalRequest
    sha256: str
    size_bytes: int
    media_type: str = "application/x-grib2"

    @classmethod
    def from_path(
        cls,
        path: Path,
        provider: str,
        request: RetrievalRequest,
    ) -> "RetrievedArtifact":
        """Verify a provider result and derive deterministic integrity facts."""
        target_root = request.target_dir.resolve(strict=True)
        resolved = Path(path).resolve(strict=True)
        if resolved != target_root and target_root not in resolved.parents:
            raise ValueError("retrieved artifact must remain under target_dir")
        _reject_symlink_components(Path(path), target_root)
        if not resolved.is_file() or resolved.is_symlink():
            raise FileNotFoundError(
                f"retrieved artifact does not exist: {resolved}"
            )
        size_bytes = resolved.stat().st_size
        if size_bytes == 0:
            raise ValueError("retrieved artifact is empty")
        if size_bytes > _MAX_RETRIEVED_BYTES:
            raise ValueError("retrieved artifact exceeds byte limit")
        return cls(
            path=resolved,
            provider=provider,
            request=request,
            sha256=_file_sha256(resolved),
            size_bytes=size_bytes,
        )


def _reject_symlink_components(path: Path, target_root: Path) -> None:
    """Reject symlinks from the target root through the returned artifact."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = target_root / candidate
    current = candidate
    checked: list[Path] = []
    while True:
        checked.append(current)
        if current in (target_root, current.parent):
            break
        current = current.parent
    if target_root not in checked:
        raise ValueError("retrieved artifact path escapes target_dir")
    if any(component.is_symlink() for component in checked):
        raise ValueError("retrieved artifact path must not contain symlinks")


def _file_sha256(path: Path) -> str:
    """Hash a potentially large GRIB artifact without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
