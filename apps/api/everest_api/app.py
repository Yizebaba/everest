"""Minimal backend REST adapter for persisted weather data."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from pydantic import AfterValidator
from sqlalchemy import select
from sqlalchemy.orm import Session

from everest_api.registry.models import DataSourceRegistryModel
from everest_api.sources.models import (
    AwsObservationModel,
    SatelliteSegmentModel,
    TerrainTileModel,
)
from everest_api.weather.models import WeatherRecordModel
from everest_api.weather.service import WeatherQueryService


def _require_utc(value: datetime) -> datetime:
    """Require an explicitly timezone-aware datetime with a zero offset."""
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(
            "datetime must be timezone-aware UTC with offset +00:00"
        )
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_require_utc)]


def create_app(session_factory: Callable[[], Session]) -> FastAPI:
    """Create API routes whose only data dependency is PostgreSQL."""
    app = FastAPI()

    @app.middleware("http")
    async def echo_correlation_id(
        request: Request, call_next: object
    ) -> Response:
        """Echo correlation IDs even when request validation returns an error."""
        response = await call_next(request)  # type: ignore[operator]
        correlation_id = request.headers.get("X-Correlation-ID")
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        return response

    def get_session() -> Session:
        """Provide and always close an API request session."""
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def records_payload(
        records: list[WeatherRecordModel],
    ) -> list[dict[str, object]]:
        """Serialize canonical persisted fields without raw metadata or URLs."""
        return [
            {
                "record_type": item.record_type,
                "timestamp": item.timestamp.isoformat().replace("+00:00", "Z"),
                "latitude": item.latitude,
                "longitude": item.longitude,
                "altitude": item.altitude,
                "spatial_key": item.spatial_key,
                "wind_speed": item.wind_speed,
                "wind_direction": item.wind_direction,
                "temperature": item.temperature,
                "precipitation": item.precipitation,
                "visibility": item.visibility,
                "source": item.source_id,
                "model": item.model,
                "forecast_cycle": (
                    item.forecast_cycle.isoformat().replace("+00:00", "Z")
                    if item.forecast_cycle
                    else None
                ),
                "forecast_lead_time": item.forecast_lead_seconds,
                "quality_flags": item.quality_flags,
            }
            for item in records
        ]

    def correlation(response: Response, value: str | None) -> None:
        """Echo a caller-provided correlation ID without generating sensitive data."""
        if value:
            response.headers["X-Correlation-ID"] = value

    @app.get("/api/weather/current")
    def current(
        response: Response,
        source: str | None = None,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return persisted latest weather records; no external call is made."""
        correlation(response, correlation_id)
        return {
            "records": records_payload(
                WeatherQueryService(session).current(source)
            )
        }

    # FastAPI injects response, query, header, and database dependencies.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    @app.get("/api/weather/forecast")
    def forecast(
        response: Response,
        start: UtcDateTime | None = None,
        end: UtcDateTime | None = None,
        source: str | None = None,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return persisted forecast records filtered by valid time."""
        correlation(response, correlation_id)
        if start and end and start > end:
            raise HTTPException(
                status_code=422, detail="start must not exceed end"
            )
        records = WeatherQueryService(session).forecast(start, end, source)
        return {"records": records_payload(records)}

    # pylint: enable=too-many-arguments,too-many-positional-arguments

    @app.get("/api/weather/profile")
    def profile(
        profile: str,
        response: Response,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return connector-labeled profile records without inventing coordinates."""
        correlation(response, correlation_id)
        try:
            records = WeatherQueryService(session).profile(profile)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"profile": profile.upper(), "records": records_payload(records)}

    @app.get("/api/weather/sources")
    def sources(session: Session = Depends(get_session)) -> dict[str, object]:
        """Return non-secret source lifecycle and operational health facts."""
        rows = session.scalars(select(DataSourceRegistryModel)).all()
        return {
            "sources": [
                {
                    "source_id": row.source_id,
                    "status": row.status,
                    "health_status": row.health_status,
                    "last_success_at": row.last_success_at,
                }
                for row in rows
            ]
        }

    @app.get("/api/data-health")
    def data_health(
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return persisted health evidence only; no inferred verification exists."""
        rows = session.scalars(select(DataSourceRegistryModel)).all()
        return {
            "sources": [
                {
                    "source_id": row.source_id,
                    "health_status": row.health_status,
                    "last_success_at": row.last_success_at,
                    "last_failure_at": row.last_failure_at,
                }
                for row in rows
            ]
        }

    @app.get("/api/terrain/tile")
    def terrain_tile(
        response: Response,
        latitude: float,
        longitude: float,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return the retained GLO-30 tile covering the requested point.

        Only persisted tile metadata is returned; no external fetch and no raw
        reference or hash is disclosed. This is the terrain extension point for
        the UI (EV-TERRAIN-001).
        """
        correlation(response, correlation_id)
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise HTTPException(
                status_code=422, detail="coordinate out of range"
            )
        row = session.scalars(
            select(TerrainTileModel).where(
                TerrainTileModel.west <= longitude,
                TerrainTileModel.east > longitude,
                TerrainTileModel.south <= latitude,
                TerrainTileModel.north > latitude,
            )
        ).first()
        if row is None:
            return {"tile": None}
        return {
            "tile": {
                "tile_name": row.tile_name,
                "crs": row.crs,
                "bounds": [row.west, row.south, row.east, row.north],
                "resolution_degrees": row.resolution_degrees,
                "min_elevation": row.min_elevation,
                "max_elevation": row.max_elevation,
                "retrieved_at": row.retrieved_at,
            }
        }

    @app.get("/api/observations/current")
    def observations_current(
        response: Response,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return the latest persisted Everest AWS observation per station.

        One row per station is selected in SQL (DISTINCT ON) rather than
        materializing the full table.
        """
        correlation(response, correlation_id)
        rows = (
            session.execute(
                select(AwsObservationModel)
                .distinct(AwsObservationModel.station)
                .order_by(
                    AwsObservationModel.station,
                    AwsObservationModel.timestamp.desc(),
                )
            )
            .scalars()
            .all()
        )
        by_station: dict[str, object] = {
            row.station: {
                "timestamp": row.timestamp,
                "station": row.station,
                "temperature_c": row.temperature_c,
                "relative_humidity": row.relative_humidity,
                "precipitation": row.precipitation,
                "weather_code": row.weather_code,
                "missing": row.missing,
                "quality_flags": row.quality_flags,
            }
            for row in rows
        }
        return {"observations": by_station}

    @app.get("/api/satellite/segments")
    def satellite_segments(
        response: Response,
        band: int | None = None,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return retained Himawari segment records (optionally by band).

        Raw object references and content hashes are never disclosed.
        """
        correlation(response, correlation_id)
        if band is not None and not 1 <= band <= 16:
            raise HTTPException(status_code=422, detail="band must be 1..16")
        statement = select(SatelliteSegmentModel).order_by(
            SatelliteSegmentModel.timestamp.desc()
        )
        if band is not None:
            statement = statement.where(SatelliteSegmentModel.band == band)
        rows = session.scalars(statement).all()
        return {
            "segments": [
                {
                    "timestamp": row.timestamp,
                    "band": row.band,
                    "segment": row.segment,
                    "satellite_name": row.satellite_name,
                    "observation_area": row.observation_area,
                    "size_bytes": row.size_bytes,
                }
                for row in rows
            ]
        }

    return app
