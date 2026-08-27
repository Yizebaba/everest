"""Optional Herbie-based NOAA GFS retrieval."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Callable

from services.weather.retrieval import RetrievalRequest, RetrievedArtifact


DEFAULT_SOURCE_PRIORITY = ("aws", "google", "nomads")


def _herbie_factory(*args: Any, **kwargs: Any) -> Any:
    try:
        from herbie import Herbie  # pylint: disable=import-outside-toplevel
    except ImportError as error:
        raise RuntimeError(
            "Herbie GFS retrieval requires the optional weather ingestion extras"
        ) from error
    return Herbie(*args, **kwargs)


class HerbieGfsClient:  # pylint: disable=too-few-public-methods
    """Retrieve an explicit GFS pgrb2.0p25 field subset through Herbie."""

    def __init__(
        self,
        *,
        source_priority: tuple[str, ...] = DEFAULT_SOURCE_PRIORITY,
        herbie_factory: Callable[..., Any] | None = None,
    ) -> None:
        if not source_priority:
            raise ValueError("Herbie source priority must not be empty")
        self.source_priority = tuple(source_priority)
        self._factory = herbie_factory or _herbie_factory

    def retrieve(self, request: RetrievalRequest) -> RetrievedArtifact:
        """Download the request's fields and return verified local metadata."""
        request.target_dir.mkdir(parents=True, exist_ok=True)
        client = self._factory(
            request.cycle,
            model="gfs",
            product="pgrb2.0p25",
            fxx=request.lead_hours,
            priority=list(self.source_priority),
        )
        alternatives = "|".join(re.escape(value) for value in request.variables)
        search = f":({alternatives}):"
        result = client.download(search, save_dir=request.target_dir)
        path = _single_path(result)
        return RetrievedArtifact.from_path(path, "noaa-gfs", request)


def _single_path(result: Any) -> Path:
    if isinstance(result, (str, Path)):
        return Path(result)
    if isinstance(result, (list, tuple)) and len(result) == 1:
        return Path(result[0])
    raise ValueError("Herbie download must return exactly one artifact path")


__all__ = ["DEFAULT_SOURCE_PRIORITY", "HerbieGfsClient"]
