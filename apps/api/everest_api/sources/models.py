"""SQLAlchemy models for terrain, observation, and satellite canonical records."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from everest_api.persistence.database import Base


class TerrainTileModel(
    Base
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Append-only canonical record of one retained GLO-30 tile."""

    __tablename__ = "terrain_tile"
    tile_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tile_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset: Mapped[str] = mapped_column(String(32), nullable=False)
    crs: Mapped[str] = mapped_column(String(32), nullable=False)
    west: Mapped[float] = mapped_column(Float, nullable=False)
    south: Mapped[float] = mapped_column(Float, nullable=False)
    east: Mapped[float] = mapped_column(Float, nullable=False)
    north: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_degrees: Mapped[float] = mapped_column(Float, nullable=False)
    min_elevation: Mapped[float] = mapped_column(Float, nullable=False)
    max_elevation: Mapped[float] = mapped_column(Float, nullable=False)
    object_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
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
            "west < east AND south < north", name="ck_terrain_bounds"
        ),
        CheckConstraint("size_bytes >= 0", name="ck_terrain_size"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_terrain_sha256"),
        UniqueConstraint("tile_name", "sha256", name="uq_terrain_tile_hash"),
        Index("ix_terrain_bounds", "west", "south", "east", "north"),
    )


class AwsObservationModel(
    Base
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Append-only canonical Everest AWS observation record."""

    __tablename__ = "aws_observation"
    observation_id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    station: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset: Mapped[str] = mapped_column(String(32), nullable=False)
    record_type: Mapped[str] = mapped_column(String(16), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    relative_humidity: Mapped[float | None] = mapped_column(Float)
    precipitation: Mapped[float | None] = mapped_column(Float)
    weather_code: Mapped[str | None] = mapped_column(String(8))
    missing: Mapped[bool] = mapped_column(default=False, nullable=False)
    quality_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    __table_args__ = (
        CheckConstraint(
            "station IN ('Base Camp', 'Camp 2', 'South Col')",
            name="ck_aws_observation_station",
        ),
        CheckConstraint(
            "record_type = 'observation'", name="ck_aws_observation_type"
        ),
        CheckConstraint(
            "temperature_c IS NULL OR (temperature_c >= -60 AND temperature_c <= 60)",
            name="ck_aws_observation_temperature",
        ),
        CheckConstraint(
            "relative_humidity IS NULL OR (relative_humidity >= 0 AND relative_humidity <= 100)",
            name="ck_aws_observation_humidity",
        ),
        CheckConstraint(
            "precipitation IS NULL OR precipitation >= 0",
            name="ck_aws_observation_precipitation",
        ),
        UniqueConstraint(
            "source_id",
            "dataset",
            "timestamp",
            "station",
            name="uq_aws_observation_identity",
        ),
        Index("ix_aws_observation_time", "station", "timestamp"),
    )


class SatelliteSegmentModel(
    Base
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Append-only canonical record of one retained Himawari band segment."""

    __tablename__ = "satellite_segment"
    segment_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset: Mapped[str] = mapped_column(String(32), nullable=False)
    band: Mapped[int] = mapped_column(Integer, nullable=False)
    segment: Mapped[int] = mapped_column(Integer, nullable=False)
    satellite_name: Mapped[str] = mapped_column(String(16), nullable=False)
    observation_area: Mapped[str] = mapped_column(String(8), nullable=False)
    object_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    __table_args__ = (
        CheckConstraint("band >= 1 AND band <= 16", name="ck_satellite_band"),
        CheckConstraint(
            "segment >= 1 AND segment <= 10", name="ck_satellite_segment"
        ),
        CheckConstraint("size_bytes >= 0", name="ck_satellite_size"),
        CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_satellite_sha256"
        ),
        UniqueConstraint(
            "source_id",
            "dataset",
            "timestamp",
            "band",
            "segment",
            name="uq_satellite_segment_identity",
        ),
        Index("ix_satellite_segment_time", "timestamp", "band"),
    )


__all__ = ["AwsObservationModel", "SatelliteSegmentModel", "TerrainTileModel"]
