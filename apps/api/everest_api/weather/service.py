"""Transaction-safe weather ingestion and database read application services."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from collections.abc import Mapping, Sequence
from typing import Callable
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from weather_ingestion_contract import (
    AuxiliaryArtifactReference,
    CanonicalRecordInput,
    IngestionPort,
    RawArtifactDescriptor,
)

from everest_api.raw_storage import RawStoragePolicy
from everest_api.registry.models import DataSourceRegistryModel
from everest_api.weather.contracts import StaticAltitudeArtifactReference
from everest_api.weather.models import (
    RawArtifactAuditEventModel,
    WeatherRawArtifactModel,
    WeatherRecordModel,
    WeatherRecordRawArtifactModel,
)
from everest_api.weather.retention import (
    AUDIT_SECONDS,
    RetentionDecision,
    validate_audit_details,
)

SUPPORTED_PROFILES = frozenset({"EBC", "C1", "C2", "C3", "C4", "SUMMIT"})


class WeatherIngestionService(IngestionPort):
    """Persists raw artifacts before attempting append-only canonical records."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        raw_storage_policy: RawStoragePolicy,
        retention_decision: RetentionDecision | None = None,
        actor_id: str = "weather-ingestion-service",
    ):
        """Create an ingestion service with a session factory owned by the API."""
        self._session_factory = session_factory
        self._raw_storage_policy = raw_storage_policy
        self._retention_decision = retention_decision or RetentionDecision()
        self._actor_id = actor_id

    def ingest(  # pylint: disable=arguments-renamed,too-many-branches,too-many-locals
        self,
        artifact: RawArtifactDescriptor,
        records: Sequence[CanonicalRecordInput],
        auxiliary_artifacts: (
            Sequence[AuxiliaryArtifactReference]
            | StaticAltitudeArtifactReference
        ) = (),
        *,
        static_altitude: StaticAltitudeArtifactReference | None = None,
    ) -> UUID:
        """Persist raw inputs, records, and optional auxiliary provenance.

        ``static_altitude`` is retained only for source compatibility with the
        pre-ADR-009 backend call shape. New callers must pass the shared
        ``AuxiliaryArtifactReference`` sequence.
        """
        # Accept the former third positional argument while callers migrate
        # to the shared sequence-shaped port signature.
        if isinstance(auxiliary_artifacts, StaticAltitudeArtifactReference):
            if static_altitude is not None:
                raise ValueError(
                    "Static altitude provenance was supplied twice"
                )
            static_altitude = auxiliary_artifacts
            auxiliary = []
        else:
            auxiliary = list(auxiliary_artifacts)
        if static_altitude is not None:
            auxiliary.append(
                AuxiliaryArtifactReference(
                    role="static_altitude",
                    artifact=static_altitude.descriptor,
                )
            )
        artifact_id = self._persist_raw(artifact)
        static_altitude_id = None
        for auxiliary_reference in auxiliary:
            if auxiliary_reference.role != "static_altitude":
                raise ValueError(
                    "Unsupported auxiliary artifact provenance role"
                )
            self._validate_static_altitude_descriptor(
                artifact, auxiliary_reference.artifact, records
            )
            static_altitude_id = self._persist_raw(auxiliary_reference.artifact)
        if not records:
            return artifact_id
        with self._session_factory() as session:
            try:
                inserted = 0
                associated = 0
                for record in records:
                    self._validate_record_source(artifact, record)
                    weather_record = self._canonical_record(
                        session, artifact, record
                    )
                    if weather_record is not None:
                        if static_altitude_id is not None:
                            associated += self._associate_static_altitude(
                                session,
                                weather_record.record_id,
                                static_altitude_id,
                            )
                        continue
                    weather_record = self._record_model(
                        artifact_id, artifact, record
                    )
                    session.add(weather_record)
                    session.flush()
                    if static_altitude_id is not None:
                        associated += self._associate_static_altitude(
                            session,
                            weather_record.record_id,
                            static_altitude_id,
                        )
                    inserted += 1
                if inserted == 0 and associated == 0:
                    session.rollback()
                    return artifact_id
                source = session.get(
                    DataSourceRegistryModel, artifact.source_id
                )
                if source is None:
                    raise LookupError(f"Unknown source: {artifact.source_id}")
                source.status = "verified"
                source.health_status = "healthy"
                source.last_success_at = artifact.retrieved_at
                session.commit()
            except Exception:
                session.rollback()
                self._record_artifact_event(
                    artifact_id,
                    "integrity_failure",
                    "failure",
                    self._actor_id,
                    "service",
                    {"stage": "canonical_persistence"},
                )
                raise
        return artifact_id

    @staticmethod
    def _canonical_record(
        session: Session,
        artifact: RawArtifactDescriptor,
        record: CanonicalRecordInput,
    ) -> WeatherRecordModel | None:
        """Load the null-safe canonical deduplication identity when it exists."""
        statement = select(WeatherRecordModel).where(
            WeatherRecordModel.source_id == artifact.source_id,
            WeatherRecordModel.dataset == artifact.dataset,
            WeatherRecordModel.timestamp == record.timestamp,
            WeatherRecordModel.spatial_key == record.spatial_key,
            WeatherRecordModel.forecast_cycle.is_not_distinct_from(
                record.forecast_cycle
            ),
            WeatherRecordModel.forecast_lead_seconds.is_not_distinct_from(
                record.forecast_lead_seconds
            ),
        )
        return session.scalar(statement)

    @staticmethod
    def _associate_static_altitude(
        session: Session, weather_record_id: UUID, raw_artifact_id: UUID
    ) -> int:
        """Add the allowed auxiliary association once without rewriting provenance."""
        existing = session.get(
            WeatherRecordRawArtifactModel,
            (weather_record_id, raw_artifact_id, "static_altitude"),
        )
        if existing is None:
            session.add(
                WeatherRecordRawArtifactModel(
                    weather_record_id=weather_record_id,
                    raw_artifact_id=raw_artifact_id,
                    provenance_role="static_altitude",
                )
            )
            return 1
        return 0

    @staticmethod
    def _validate_static_altitude_descriptor(
        primary: RawArtifactDescriptor,
        auxiliary: RawArtifactDescriptor,
        records: Sequence[CanonicalRecordInput],
    ) -> None:
        """Require factual same-source, same-cycle, step-zero surface-z evidence."""
        metadata = auxiliary.metadata or {}
        if auxiliary.source_id != primary.source_id:
            raise ValueError(
                "Static altitude artifact source must match primary"
            )
        if auxiliary.sha256 == primary.sha256:
            raise ValueError(
                "Static altitude artifact must differ from primary"
            )
        if auxiliary.forecast_cycle != primary.forecast_cycle:
            raise ValueError(
                "Static altitude artifact cycle must match primary"
            )
        if auxiliary.forecast_lead_seconds != 0:
            raise ValueError("Static altitude artifact must be step zero")
        if auxiliary.valid_time != auxiliary.forecast_cycle:
            raise ValueError(
                "Static altitude artifact valid time must equal cycle"
            )
        if (
            metadata.get("parameter") != "z"
            or metadata.get("level_type") != "sfc"
            or metadata.get("step_seconds") != 0
        ):
            raise ValueError(
                "Static altitude metadata must evidence step-zero surface z"
            )
        for record in records:
            if (
                primary.metadata is None
                or primary.metadata.get("model") != record.model
            ):
                raise ValueError("Primary metadata model must match record")
            if metadata.get("model") != record.model:
                raise ValueError(
                    "Static altitude metadata model must match record"
                )
            if metadata.get("spatial_key") != record.spatial_key:
                raise ValueError(
                    "Static altitude metadata spatial key must match record"
                )

    def _persist_raw(self, artifact: RawArtifactDescriptor) -> UUID:
        """Commit immutable raw retention separately so downstream errors retain it."""
        self._validate_artifact_descriptor(artifact)
        self._raw_storage_policy.verify_artifact(
            artifact.object_reference, artifact.sha256, artifact.size_bytes
        )
        with self._session_factory() as session:
            existing = session.scalar(
                select(WeatherRawArtifactModel.artifact_id).where(
                    WeatherRawArtifactModel.source_id == artifact.source_id,
                    WeatherRawArtifactModel.sha256 == artifact.sha256,
                )
            )
            if existing is not None:
                self._append_audit(
                    session, existing, "reused", "success", artifact
                )
                session.commit()
                return existing
            if session.get(DataSourceRegistryModel, artifact.source_id) is None:
                raise LookupError(f"Unknown source: {artifact.source_id}")
            due_at = self._retention_decision.due_at(artifact.retrieved_at)
            model = WeatherRawArtifactModel(
                source_id=artifact.source_id,
                dataset=artifact.dataset,
                object_reference=artifact.object_reference,
                sha256=artifact.sha256,
                retrieved_at=artifact.retrieved_at,
                data_format=artifact.data_format,
                size_bytes=artifact.size_bytes,
                source_url=artifact.source_url,
                forecast_cycle=artifact.forecast_cycle,
                forecast_lead_seconds=artifact.forecast_lead_seconds,
                valid_time=artifact.valid_time,
                metadata_json=artifact.metadata,
                retention_owner=self._retention_decision.owner,
                retention_class=self._retention_decision.retention_class,
                retention_period_seconds=self._retention_decision.period_seconds,
                acquired_at=artifact.retrieved_at,
                retention_due_at=due_at,
                disposition_state="retained",
                hold_state="none",
                retention_policy_version=self._retention_decision.policy_version,
            )
            session.add(model)
            session.flush()
            self._append_audit(
                session, model.artifact_id, "accepted", "success", artifact
            )
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                duplicate = session.scalar(
                    select(WeatherRawArtifactModel.artifact_id).where(
                        WeatherRawArtifactModel.source_id == artifact.source_id,
                        WeatherRawArtifactModel.sha256 == artifact.sha256,
                    )
                )
                if duplicate is None:
                    raise
                self._append_audit(
                    session, duplicate, "reused", "success", artifact
                )
                session.commit()
                return duplicate
            return model.artifact_id

    @staticmethod
    def _validate_artifact_descriptor(
        artifact: RawArtifactDescriptor,
    ) -> None:
        """Reject inconsistent generic payload projections before persistence."""
        sha256 = artifact.sha256
        if (  # pylint: disable=unidiomatic-typecheck
            type(sha256) is not str
            or len(sha256) != 64
            or any(
                character not in "0123456789abcdefABCDEF"
                for character in sha256
            )
        ):
            raise ValueError(
                "Raw artifact SHA-256 must be 64 hexadecimal characters"
            )
        # Exact type rejects booleans, which Python otherwise treats as integers.
        if (  # pylint: disable=unidiomatic-typecheck
            type(artifact.size_bytes) is not int or artifact.size_bytes < 0
        ):
            raise ValueError("Raw artifact size must be a non-negative integer")
        metadata = artifact.metadata or {}
        if "provider_payload_sha256" in metadata:
            projected_sha256 = metadata["provider_payload_sha256"]
            if (  # pylint: disable=unidiomatic-typecheck
                type(projected_sha256) is not str
                or len(projected_sha256) != 64
                or any(
                    character not in "0123456789abcdefABCDEF"
                    for character in projected_sha256
                )
            ):
                raise ValueError(
                    "Projected payload SHA-256 must be 64 hexadecimal characters"
                )
            if projected_sha256 != sha256:
                raise ValueError(
                    "Projected payload SHA-256 must match the descriptor"
                )
        if "provider_payload_size_bytes" in metadata:
            projected_size = metadata["provider_payload_size_bytes"]
            if (  # pylint: disable=unidiomatic-typecheck
                type(projected_size) is not int or projected_size < 0
            ):
                raise ValueError(
                    "Projected payload size must be a non-negative integer"
                )
            if projected_size != artifact.size_bytes:
                raise ValueError(
                    "Projected payload size must match the descriptor"
                )

    def _append_audit(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        session: Session,
        artifact_id: UUID,
        event_type: str,
        result: str,
        artifact: RawArtifactDescriptor,
    ) -> None:
        """Append bounded audit evidence at the backend authorization edge."""
        details = validate_audit_details(
            {
                "source_id": artifact.source_id,
                "dataset": artifact.dataset,
            }
        )
        event_time = artifact.retrieved_at
        session.add(
            RawArtifactAuditEventModel(
                artifact_id=artifact_id,
                event_type=event_type,
                result=result,
                actor_id=self._actor_id,
                actor_role="service",
                correlation_id=str(artifact.sha256),
                event_time=event_time,
                details=details,
                audit_due_at=event_time + timedelta(seconds=AUDIT_SECONDS),
            )
        )

    def transition_retention_state(  # pylint: disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements
        self,
        artifact_id: UUID,
        *,
        disposition_state: str | None = None,
        hold_state: str | None = None,
        hold_details: dict[str, object] | None = None,
        actor_id: str,
        actor_role: str,
    ) -> None:
        """Apply an authorized internal retention transition, fail-closed.

        IAM is intentionally outside this local service.  The caller must
        provide an identity and role from the deployment's authorization
        boundary; this method validates the role shape but does not claim ACL
        enforcement.
        """
        if (
            actor_role
            not in {"operator", "retention_authority", "audit_authority"}
            or not actor_id
        ):
            raise PermissionError("retention actor authorization is required")
        if hold_state == "released" and disposition_state == "completed":
            raise ValueError("hold release and completion cannot be combined")
        with self._session_factory() as session:
            artifact = session.get(WeatherRawArtifactModel, artifact_id)
            if artifact is None:
                raise LookupError("Unknown raw artifact")
            if hold_state == "held" and hold_details is None:
                raise ValueError("held artifacts require hold details")
            if hold_state == "released":
                if artifact.hold_state != "held":
                    raise ValueError("only a persisted hold may be released")
            if disposition_state == "approved":
                if artifact.retention_due_at is None or (
                    artifact.retention_due_at > datetime.now(UTC)
                ):
                    raise ValueError("disposition approval requires expiry")
                if artifact.disposition_state != "retained":
                    raise ValueError(
                        "disposition approval requires retained state"
                    )
                if artifact.hold_state not in {"none", "released"}:
                    raise ValueError(
                        "disposition approval requires no active hold"
                    )
            if disposition_state == "completed":
                approved = session.scalar(
                    select(RawArtifactAuditEventModel.event_id).where(
                        RawArtifactAuditEventModel.artifact_id == artifact_id,
                        RawArtifactAuditEventModel.event_type
                        == "disposition_approved",
                        RawArtifactAuditEventModel.result == "success",
                    )
                )
                if artifact.disposition_state != "approved" or approved is None:
                    raise ValueError("completion requires prior approval audit")
                if artifact.retention_due_at is None or (
                    artifact.retention_due_at > datetime.now(UTC)
                ):
                    raise ValueError("disposition completion requires expiry")
                if artifact.hold_state not in {"none", "released"}:
                    raise ValueError(
                        "disposition completion requires released hold"
                    )
                if artifact.hold_state == "none":
                    accepted = session.scalar(
                        select(RawArtifactAuditEventModel.event_id).where(
                            RawArtifactAuditEventModel.artifact_id
                            == artifact_id,
                            RawArtifactAuditEventModel.event_type == "accepted",
                            RawArtifactAuditEventModel.result == "success",
                        )
                    )
                    if accepted is None:
                        raise ValueError(
                            "not-held state requires acceptance audit"
                        )
                if artifact.hold_state == "released":
                    released = session.scalar(
                        select(RawArtifactAuditEventModel.event_id).where(
                            RawArtifactAuditEventModel.artifact_id
                            == artifact_id,
                            RawArtifactAuditEventModel.event_type
                            == "hold_released",
                            RawArtifactAuditEventModel.result == "success",
                        )
                    )
                    if released is None:
                        raise ValueError(
                            "released state requires release audit"
                        )
                if hold_state is not None:
                    raise ValueError(
                        "hold release and completion cannot be combined"
                    )
            if hold_state == "released" and disposition_state is not None:
                raise ValueError(
                    "hold release and disposition cannot be combined"
                )
            values = {
                key: value
                for key, value in {
                    "disposition_state": disposition_state,
                    "hold_state": hold_state,
                    "hold_details": (
                        validate_audit_details(hold_details)
                        if hold_details is not None
                        else None
                    ),
                }.items()
                if value is not None
            }
            session.execute(
                text("SET LOCAL everest.retention_transition = 'on'")
            )
            for key, value in values.items():
                setattr(artifact, key, value)
            session.flush()
            if hold_state == "held":
                event_type = "hold_placed"
            elif hold_state == "released":
                event_type = "hold_released"
            elif disposition_state == "approved":
                event_type = "disposition_approved"
            else:
                event_type = "disposition_completed"
            session.add(
                RawArtifactAuditEventModel(
                    artifact_id=artifact_id,
                    event_type=event_type,
                    result="success",
                    actor_id=actor_id,
                    actor_role=actor_role,
                    correlation_id=str(artifact_id),
                    details=validate_audit_details(
                        {
                            "disposition_state": values.get(
                                "disposition_state"
                            ),
                            "hold_state": values.get("hold_state"),
                        }
                    ),
                    audit_due_at=datetime.now(UTC)
                    + timedelta(seconds=AUDIT_SECONDS),
                )
            )
            session.commit()

    def _record_artifact_event(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        artifact_id: UUID,
        event_type: str,
        result: str,
        actor_id: str,
        actor_role: str,
        details: Mapping[str, object],
    ) -> None:
        """Commit one internal audit event without exposing raw facts."""
        with self._session_factory() as session:
            artifact = session.get(WeatherRawArtifactModel, artifact_id)
            if artifact is None:
                return
            event_time = datetime.now(UTC)
            session.add(
                RawArtifactAuditEventModel(
                    artifact_id=artifact_id,
                    event_type=event_type,
                    result=result,
                    actor_id=actor_id,
                    actor_role=actor_role,
                    correlation_id=str(artifact_id),
                    event_time=event_time,
                    details=validate_audit_details(details),
                    audit_due_at=event_time + timedelta(seconds=AUDIT_SECONDS),
                )
            )
            session.commit()

    def record_raw_read(self, artifact_id: UUID, actor_id: str) -> None:
        """Audit an internal raw read; public APIs never call this method."""
        self._record_artifact_event(
            artifact_id, "read", "success", actor_id, "service", {}
        )

    def record_access_change(
        self, artifact_id: UUID, actor_id: str, result: str = "success"
    ) -> None:
        """Audit an access-boundary change without claiming ACL enforcement."""
        self._record_artifact_event(
            artifact_id, "access_change", result, actor_id, "operator", {}
        )

    @staticmethod
    def _validate_record_source(
        artifact: RawArtifactDescriptor, record: CanonicalRecordInput
    ) -> None:
        """Reject a payload whose canonical provenance diverges from raw provenance."""
        if record.source != artifact.source_id:
            raise ValueError(
                "Canonical record source must match raw artifact source"
            )
        if record.forecast_cycle != artifact.forecast_cycle:
            raise ValueError(
                "Canonical record cycle must match raw artifact cycle"
            )
        if record.forecast_lead_seconds != artifact.forecast_lead_seconds:
            raise ValueError(
                "Canonical record lead must match raw artifact lead"
            )

    @staticmethod
    def _record_model(
        artifact_id: UUID,
        artifact: RawArtifactDescriptor,
        record: CanonicalRecordInput,
    ) -> WeatherRecordModel:
        """Translate neutral canonical data to the persistence model."""
        values = record.__dict__.copy()
        values.pop("source")
        values["quality_flags"] = list(record.quality_flags)
        return WeatherRecordModel(
            raw_artifact_id=artifact_id,
            source_id=artifact.source_id,
            dataset=artifact.dataset,
            **values,
        )


class WeatherQueryService:
    """Read-only canonical weather queries; it never contacts providers."""

    def __init__(self, session: Session):
        """Bind queries to an API-owned read session."""
        self._session = session

    def current(self, source_id: str | None = None) -> list[WeatherRecordModel]:
        """Return latest valid records per request ordering, without provider I/O."""
        statement = select(WeatherRecordModel).order_by(
            WeatherRecordModel.timestamp.desc()
        )
        if source_id:
            statement = statement.where(
                WeatherRecordModel.source_id == source_id
            )
        return list(self._session.scalars(statement.limit(100)))

    def forecast(
        self,
        start: datetime | None,
        end: datetime | None,
        source_id: str | None,
    ) -> list[WeatherRecordModel]:
        """Return forecast records filtered by valid-time interval."""
        statement = select(WeatherRecordModel).where(
            WeatherRecordModel.record_type == "forecast"
        )
        if start:
            statement = statement.where(WeatherRecordModel.timestamp >= start)
        if end:
            statement = statement.where(WeatherRecordModel.timestamp <= end)
        if source_id:
            statement = statement.where(
                WeatherRecordModel.source_id == source_id
            )
        return list(
            self._session.scalars(
                statement.order_by(WeatherRecordModel.timestamp)
            )
        )

    def profile(self, profile: str) -> list[WeatherRecordModel]:
        """Return records explicitly labeled by a connector with one route profile."""
        normalized = profile.upper()
        if normalized not in SUPPORTED_PROFILES:
            raise ValueError("Unsupported route profile")
        statement = select(WeatherRecordModel).where(
            WeatherRecordModel.route_profile == normalized
        )
        return list(
            self._session.scalars(
                statement.order_by(WeatherRecordModel.timestamp)
            )
        )
