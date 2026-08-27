"""Environment-backed provider enablement without implied live integrations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SchedulerConfig:
    """Explicit source switches; only IFS is enabled by default."""

    ifs_enabled: bool = True
    gfs_enabled: bool = False
    aifs_enabled: bool = False
    icon_enabled: bool = False

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "SchedulerConfig":
        """Load strict boolean source switches from an environment mapping."""
        values = os.environ if environment is None else environment
        return cls(
            ifs_enabled=_enabled(values, "EVEREST_SCHEDULER_IFS_ENABLED", True),
            gfs_enabled=_enabled(
                values, "EVEREST_SCHEDULER_GFS_ENABLED", False
            ),
            aifs_enabled=_enabled(
                values, "EVEREST_SCHEDULER_AIFS_ENABLED", False
            ),
            icon_enabled=_enabled(
                values, "EVEREST_SCHEDULER_ICON_ENABLED", False
            ),
        )


def _enabled(values: Mapping[str, str], name: str, default: bool) -> bool:
    raw = values.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")
