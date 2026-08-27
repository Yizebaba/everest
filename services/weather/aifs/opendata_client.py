"""Optional ecmwf-opendata retrieval for AIFS Single forecasts."""

# Optional dependencies are deliberately imported only at first retrieval use.
# pylint: disable=import-outside-toplevel

from __future__ import annotations

from typing import Any, Callable

from services.weather.ecmwf.opendata_client import _filename
from services.weather.retrieval import RetrievalRequest, RetrievedArtifact


def _client_factory(**kwargs: Any) -> Any:
    try:
        from ecmwf.opendata import (
            Client,
        )
    except ImportError as error:
        raise RuntimeError(
            "AIFS retrieval requires the optional weather ingestion extras"
        ) from error
    return Client(**kwargs)


class EcmwfAifsOpenDataClient:  # pylint: disable=too-few-public-methods
    """Retrieve explicit AIFS Single fields with bounded retries."""

    def __init__(
        self,
        *,
        maximum_retries: int = 3,
        retry_after: int = 5,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        if maximum_retries < 0 or retry_after < 0:
            raise ValueError("AIFS retry bounds must not be negative")
        self._client = (client_factory or _client_factory)(
            source="ecmwf",
            model="aifs-single",
            resol="0p25",
            maximum_retries=maximum_retries,
            retry_after=retry_after,
            use_server_retry_after=True,
        )

    def retrieve(self, request: RetrievalRequest) -> RetrievedArtifact:
        """Retrieve one immutable AIFS request into its destination directory."""
        request.target_dir.mkdir(parents=True, exist_ok=True)
        target = request.target_dir / _filename("aifs-single", request)
        self._client.retrieve(
            {
                "date": request.cycle.strftime("%Y%m%d"),
                "time": request.cycle.hour,
                "type": "fc",
                "step": request.lead_hours,
                "param": list(request.variables),
                "target": str(target),
            }
        )
        return RetrievedArtifact.from_path(target, "ecmwf-aifs", request)


__all__ = ["EcmwfAifsOpenDataClient"]
