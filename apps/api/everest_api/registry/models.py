"""SQLAlchemy models for registry configuration and append-only run history."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy import Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from everest_api.persistence.database import Base
from everest_api.registry.redaction import redact_failure_detail


class DataSourceRegistryModel(Base):
    """Runtime-authoritative data-source metadata with no secret values."""

    __tablename__ = "data_source_registry"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    access_method: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_format: Mapped[Optional[str]] = mapped_column("format", String(64))
    update_frequency: Mapped[Optional[str]] = mapped_column(String(128))
    spatial_resolution: Mapped[Optional[str]] = mapped_column(String(128))
    temporal_resolution: Mapped[Optional[str]] = mapped_column(String(128))
    coverage: Mapped[Optional[str]] = mapped_column(Text)
    license_name: Mapped[Optional[str]] = mapped_column("license", Text)
    commercial_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    credentials_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    credential_reference: Mapped[Optional[str]] = mapped_column(String(255))
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    health_status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'configured', 'connected', 'verified', "
            "'degraded', 'disabled')",
            name="ck_data_source_registry_status",
        ),
        CheckConstraint(
            "health_status IN ('unknown', 'healthy', 'stale', 'failed', "
            "'degraded', 'disabled')",
            name="ck_data_source_registry_health_status",
        ),
        CheckConstraint(
            "metadata_version >= 1",
            name="ck_data_source_registry_metadata_version",
        ),
        CheckConstraint(
            "(credential_reference IS NULL) OR credentials_required",
            name="ck_data_source_registry_credential_reference",
        ),
        Index("ix_data_source_registry_status", "status"),
        Index("ix_data_source_registry_health_status", "health_status"),
        Index("ix_data_source_registry_last_success_at", "last_success_at"),
    )


class DataSourceScheduleModel(Base):
    """One complete declarative schedule per source, without execution ownership."""

    __tablename__ = "data_source_schedule"

    source_id: Mapped[str] = mapped_column(
        ForeignKey("data_source_registry.source_id", ondelete="CASCADE"),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    initial_backoff_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    max_backoff_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    misfire_grace_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    max_concurrent_runs: Mapped[int] = mapped_column(Integer, nullable=False)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    __table_args__ = (
        CheckConstraint("interval_seconds > 0", name="ck_schedule_interval"),
        CheckConstraint("retry_limit >= 0", name="ck_schedule_retry_limit"),
        CheckConstraint("timeout_seconds > 0", name="ck_schedule_timeout"),
        CheckConstraint(
            "initial_backoff_seconds >= 0", name="ck_schedule_backoff"
        ),
        CheckConstraint(
            "max_backoff_seconds >= initial_backoff_seconds",
            name="ck_schedule_max_backoff",
        ),
        CheckConstraint(
            "misfire_grace_seconds >= 0", name="ck_schedule_misfire"
        ),
        CheckConstraint(
            "max_concurrent_runs > 0", name="ck_schedule_concurrency"
        ),
        Index("ix_data_source_schedule_next_run_at", "next_run_at"),
    )


class DataSourceRunModel(Base):
    """Append-oriented safe run audit record; no Phase A process creates rows."""

    __tablename__ = "data_source_run"

    run_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("data_source_registry.source_id", ondelete="RESTRICT"),
        nullable=False,
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_code: Mapped[Optional[str]] = mapped_column(String(128))
    failure_detail: Mapped[Optional[str]] = mapped_column(String(1024))
    content_hash: Mapped[Optional[str]] = mapped_column(String(128))

    __table_args__ = (
        CheckConstraint(
            "outcome IN ('started', 'succeeded', 'failed', 'skipped')",
            name="ck_data_source_run_outcome",
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_data_source_run_time_order",
        ),
        CheckConstraint(
            "failure_detail IS NULL OR length(failure_detail) <= 1024",
            name="ck_data_source_run_failure_detail",
        ),
        Index("ix_data_source_run_source_id", "source_id"),
    )

    @validates("failure_detail")
    def redact_failure_detail(self, key: str, detail: str | None) -> str | None:
        """Redact known credential formats before SQLAlchemy persists a detail."""
        del key
        return redact_failure_detail(detail) if detail else detail
