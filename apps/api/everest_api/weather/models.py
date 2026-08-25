"""SQLAlchemy models for immutable raw weather and append-only records."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey
from sqlalchemy import (
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from everest_api.persistence.database import Base


class WeatherRawArtifactModel(
    Base
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Content-addressed provider payload retained before downstream processing."""

    __tablename__ = "weather_raw_artifact"
    artifact_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("data_source_registry.source_id", ondelete="RESTRICT"),
        nullable=False,
    )
    dataset: Mapped[str] = mapped_column(String(128), nullable=False)
    object_reference: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_format: Mapped[str] = mapped_column(String(32), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    forecast_cycle: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    forecast_lead_seconds: Mapped[int | None] = mapped_column(Integer)
    valid_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    retention_owner: Mapped[str | None] = mapped_column(String(128))
    retention_class: Mapped[str] = mapped_column(String(32), nullable=False)
    retention_period_seconds: Mapped[int | None] = mapped_column(BigInteger)
    acquired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    retention_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    disposition_state: Mapped[str] = mapped_column(String(24), nullable=False)
    hold_state: Mapped[str] = mapped_column(String(24), nullable=False)
    hold_details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    retention_policy_version: Mapped[str | None] = mapped_column(String(64))
    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_weather_raw_size"),
        CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_weather_raw_sha256"
        ),
        UniqueConstraint(
            "source_id", "sha256", name="uq_weather_raw_source_hash"
        ),
        Index("ix_weather_raw_source_cycle", "source_id", "forecast_cycle"),
        CheckConstraint(
            "retention_class IN ('operational_raw', 'failed_or_rejected_raw', "
            "'legacy_unclassified')",
            name="ck_weather_raw_retention_class",
        ),
        CheckConstraint(
            "retention_class = 'legacy_unclassified' OR "
            "(retention_owner IS NOT NULL AND retention_period_seconds > 0 "
            "AND acquired_at IS NOT NULL AND retention_due_at IS NOT NULL "
            "AND retention_policy_version IS NOT NULL)",
            name="ck_weather_raw_retention_period",
        ),
        CheckConstraint(
            "disposition_state IN ('retained', 'approved', 'completed', 'blocked')",
            name="ck_weather_raw_disposition",
        ),
        CheckConstraint(
            "hold_state IN ('none', 'held', 'released', 'unknown') AND "
            "(hold_state <> 'held' OR hold_details IS NOT NULL)",
            name="ck_weather_raw_hold",
        ),
    )


class WeatherRecordModel(
    Base
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Append-only canonical weather view derived from one raw artifact."""

    __tablename__ = "weather_record"
    record_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    raw_artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("weather_raw_artifact.artifact_id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset: Mapped[str] = mapped_column(String(128), nullable=False)
    record_type: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude: Mapped[float] = mapped_column(Float, nullable=False)
    spatial_key: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    forecast_cycle: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    forecast_lead_seconds: Mapped[int | None] = mapped_column(Integer)
    route_profile: Mapped[str | None] = mapped_column(String(16))
    quality_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    wind_speed: Mapped[float | None] = mapped_column(Float)
    wind_direction: Mapped[float | None] = mapped_column(Float)
    temperature: Mapped[float | None] = mapped_column(Float)
    precipitation: Mapped[float | None] = mapped_column(Float)
    visibility: Mapped[float | None] = mapped_column(Float)
    pressure: Mapped[float | None] = mapped_column(Float)
    relative_humidity: Mapped[float | None] = mapped_column(Float)
    dew_point: Mapped[float | None] = mapped_column(Float)
    cloud_cover: Mapped[float | None] = mapped_column(Float)
    cloud_base: Mapped[float | None] = mapped_column(Float)
    cloud_top: Mapped[float | None] = mapped_column(Float)
    snowfall: Mapped[float | None] = mapped_column(Float)
    gust_speed: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    __table_args__ = (
        CheckConstraint(
            "record_type IN ('forecast', 'observation', 'satellite', 'derived')",
            name="ck_weather_record_type",
        ),
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90", name="ck_weather_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_weather_longitude",
        ),
        CheckConstraint(
            "wind_speed IS NULL OR wind_speed >= 0",
            name="ck_weather_wind_speed",
        ),
        CheckConstraint(
            "wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction < 360)",
            name="ck_weather_wind_direction",
        ),
        CheckConstraint(
            "precipitation IS NULL OR precipitation >= 0",
            name="ck_weather_precipitation",
        ),
        CheckConstraint(
            "visibility IS NULL OR visibility >= 0",
            name="ck_weather_visibility",
        ),
        CheckConstraint(
            "route_profile IS NULL OR route_profile IN ('EBC', 'C1', 'C2', 'C3', 'C4', 'SUMMIT')",
            name="ck_weather_route_profile",
        ),
        UniqueConstraint(
            "source_id",
            "dataset",
            "timestamp",
            "spatial_key",
            "forecast_cycle",
            "forecast_lead_seconds",
            name="uq_weather_record_identity",
        ),
        Index(
            "ix_weather_record_query",
            "source_id",
            "timestamp",
            "forecast_cycle",
        ),
        Index("ix_weather_record_profile", "route_profile", "timestamp"),
    )


class WeatherRecordRawArtifactModel(
    Base
):  # pylint: disable=too-few-public-methods
    """Append-only auxiliary raw provenance for a canonical weather record."""

    __tablename__ = "weather_record_raw_artifact"
    weather_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("weather_record.record_id", ondelete="RESTRICT"),
        primary_key=True,
    )

    raw_artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("weather_raw_artifact.artifact_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    provenance_role: Mapped[str] = mapped_column(String(32), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    __table_args__ = (
        CheckConstraint(
            "provenance_role = 'static_altitude'",
            name="ck_weather_record_raw_artifact_role",
        ),
        Index(
            "ix_weather_record_raw_artifact_reverse",
            "raw_artifact_id",
            "weather_record_id",
        ),
    )


class RawArtifactAuditEventModel(
    Base
):  # pylint: disable=too-few-public-methods
    """Append-only, bounded audit evidence for raw artifact lifecycle actions."""

    __tablename__ = "raw_artifact_audit_event"
    event_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("weather_raw_artifact.artifact_id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # SQLAlchemy's dynamic SQL function namespace is callable at runtime.
    # pylint: disable=not-callable
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    # pylint: enable=not-callable
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    audit_due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('accepted', 'read', 'reused', 'integrity_failure', "
            "'access_change', 'hold_placed', 'hold_released', "
            "'disposition_approved', 'disposition_completed')",
            name="ck_raw_audit_event_type",
        ),
        CheckConstraint(
            "result IN ('success', 'failure', 'blocked')",
            name="ck_raw_audit_result",
        ),
        CheckConstraint(
            "actor_role IN ('service', 'operator', 'retention_authority', "
            "'audit_authority')",
            name="ck_raw_audit_actor_role",
        ),
        CheckConstraint("length(actor_id) > 0", name="ck_raw_audit_actor"),
        CheckConstraint(
            "octet_length(details::text) <= 4096",
            name="ck_raw_audit_details_size",
        ),
        Index("ix_raw_audit_artifact_time", "artifact_id", "event_time"),
        Index("ix_raw_audit_due", "audit_due_at"),
    )
