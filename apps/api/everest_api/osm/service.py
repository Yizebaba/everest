"""Upsert and read application services for OSM (Overpass) features.

The Everest South Col route and its camps are a small, slowly changing
snapshot. The ingest script fetches Overpass output, normalizes it, and calls
``OsmFeatureService.sync`` which replaces the persisted rows for the source
dataset in one transaction. Reads never contact the provider.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from everest_api.osm.models import OsmFeatureModel

SOURCE_ID = "osm-overpass"
DATASET = "osm-south-col"


class OsmFeatureService:
    """Idempotent sync and read access to persisted OSM features."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """Bind the service to an application-owned session factory."""
        self._session_factory = session_factory

    def sync(
        self,
        camps: list[tuple[str | None, float, float, float | None, str | None]],
        route: list[tuple[float, float]],
        *,
        retrieved_at: datetime | None = None,
    ) -> int:
        """Replace all persisted features for the South Col dataset.

        ``camps`` items are ``(name, latitude, longitude, elevation_m,
        osm_ref)``. ``route`` items are ``(latitude, longitude)`` vertices in
        travel order. Returns the number of rows persisted.
        """
        timestamp = retrieved_at or datetime.now(UTC)
        rows = [
            OsmFeatureModel(
                source_id=SOURCE_ID,
                dataset=DATASET,
                feature_kind="camp",
                name=name,
                sequence=sequence,
                latitude=latitude,
                longitude=longitude,
                elevation_m=elevation_m,
                osm_ref=osm_ref,
                retrieved_at=timestamp,
            )
            for sequence, (name, latitude, longitude, elevation_m, osm_ref) in (
                enumerate(camps)
            )
        ]
        rows.extend(
            OsmFeatureModel(
                source_id=SOURCE_ID,
                dataset=DATASET,
                feature_kind="route",
                name=None,
                sequence=sequence,
                latitude=latitude,
                longitude=longitude,
                elevation_m=None,
                osm_ref=None,
                retrieved_at=timestamp,
            )
            for sequence, (latitude, longitude) in enumerate(route)
        )
        with self._session_factory() as session:
            session.execute(
                delete(OsmFeatureModel).where(
                    OsmFeatureModel.source_id == SOURCE_ID,
                    OsmFeatureModel.dataset == DATASET,
                )
            )
            session.add_all(rows)
            session.commit()
        return len(rows)

    def route(self, session: Session) -> list[OsmFeatureModel]:
        """Return all persisted South Col features in display order."""
        statement = (
            select(OsmFeatureModel)
            .where(
                OsmFeatureModel.source_id == SOURCE_ID,
                OsmFeatureModel.dataset == DATASET,
            )
            .order_by(OsmFeatureModel.feature_kind, OsmFeatureModel.sequence)
        )
        return list(session.scalars(statement))


__all__ = ["DATASET", "SOURCE_ID", "OsmFeatureService"]
