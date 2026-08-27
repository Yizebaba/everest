"""Best-effort persistence adapter for existing data_source_run storage."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from everest_api.registry.models import (
    DataSourceRegistryModel,
    DataSourceRunModel,
)
from everest_api.scheduler.runner import ProviderOutcome


class DataSourceRunRecorder:  # pylint: disable=too-few-public-methods
    """Append terminal provider outcomes using the existing schema."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __call__(self, outcome: ProviderOutcome) -> None:
        with self._session_factory() as session:
            source = session.get(DataSourceRegistryModel, outcome.source_id)
            if source is None:
                raise LookupError(f"Unknown source: {outcome.source_id}")
            session.add(
                DataSourceRunModel(
                    source_id=outcome.source_id,
                    outcome=outcome.outcome,
                    started_at=outcome.started_at,
                    finished_at=outcome.finished_at,
                    retryable=outcome.retryable,
                    failure_code=outcome.failure_code,
                    failure_detail=outcome.failure_detail,
                )
            )
            if outcome.outcome == "succeeded":
                source.health_status = "healthy"
                source.last_success_at = outcome.finished_at
            else:
                source.health_status = "failed"
                source.last_failure_at = outcome.finished_at
            session.commit()
