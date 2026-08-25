"""SQLAlchemy models for OSM (Overpass) route and camp features (EV-OSM-002)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from everest_api.persistence.database import Base

OSM_FEATURE_KINDS = ("camp", "route")


class OsmFeatureModel(
    Base
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """One canonical OSM feature: a named camp point or a route polyline vertex.

    The Everest South Col route is a small static snapshot refreshed by the
    ingest script; rows are upserted by (feature_kind, name, sequence) so the
    table is idempotent across runs rather than append-only.
    """

    __tablename__ = "osm_feature"
    feature_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str | None] = mapped_column(String(128))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float | None] = mapped_column(Float)
    osm_ref: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    __table_args__ = (
        CheckConstraint(
            "feature_kind IN ('camp', 'route')", name="ck_osm_feature_kind"
        ),
        CheckConstraint(
            "sequence >= 0", name="ck_osm_feature_sequence"
        ),
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90", name="ck_osm_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180", name="ck_osm_longitude"
        ),
        UniqueConstraint(
            "source_id",
            "dataset",
            "feature_kind",
            "name",
            "sequence",
            name="uq_osm_feature_identity",
        ),
        Index("ix_osm_feature_kind", "feature_kind", "sequence"),
    )


__all__ = ["OsmFeatureModel"]
