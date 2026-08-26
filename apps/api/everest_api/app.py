"""Minimal backend REST adapter for persisted weather data."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
import os
import re
from typing import Annotated, Callable, Sequence
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AfterValidator
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint

from everest_api.registry.models import DataSourceRegistryModel
from everest_api.osm.models import OsmFeatureModel
from everest_api.sources.models import (
    AwsObservationModel,
    SatelliteSegmentModel,
    TerrainTileModel,
)
from everest_api.weather.models import WeatherRecordModel
from everest_api.weather.service import WeatherQueryService


_CORRELATION_HEADER = "X-Correlation-ID"
_CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:42420",
    "http://localhost:52148",
)
_LOGGER = logging.getLogger(__name__)


def _utc_z(value: datetime | None) -> str | None:
    """Serialize a database datetime as an explicit UTC trailing-Z value."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _correlation_id(request: Request) -> str:
    """Retain a bounded safe caller ID or generate an opaque request ID."""
    supplied = request.headers.get(_CORRELATION_HEADER, "")
    if _CORRELATION_PATTERN.fullmatch(supplied):
        return supplied
    return str(uuid4())


def _configured_cors_origins(
    cors_origins: Sequence[str] | None,
) -> tuple[str, ...]:
    """Return an explicit validated CORS allow-list from args or environment."""
    if cors_origins is None:
        configured = os.environ.get("EVEREST_CORS_ALLOWED_ORIGINS")
        cors_origins = (
            configured.split(",") if configured else _DEFAULT_CORS_ORIGINS
        )
    normalized = tuple(origin.strip().rstrip("/") for origin in cors_origins)
    for origin in normalized:
        parsed = urlsplit(origin)
        invalid_location = not parsed.netloc or bool(parsed.path)
        has_extra_parts = bool(parsed.query or parsed.fragment)
        if (
            origin == "*"
            or parsed.scheme
            not in {
                "http",
                "https",
            }
            or invalid_location
            or has_extra_parts
        ):
            raise ValueError(f"invalid CORS origin: {origin!r}")
    return normalized


def _error_response(
    status_code: int,
    code: str,
    message: str,
    correlation_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Create the public bounded error contract with correlation header."""
    response_headers = dict(headers or {})
    response_headers[_CORRELATION_HEADER] = correlation_id
    return JSONResponse(
        status_code=status_code,
        headers=response_headers,
        content={
            "error": {
                "code": code,
                "message": message[:256],
                "correlation_id": correlation_id,
            }
        },
    )


def _require_utc(value: datetime) -> datetime:
    """Require an explicitly timezone-aware datetime with a zero offset."""
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(
            "datetime must be timezone-aware UTC with offset +00:00"
        )
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_require_utc)]


def create_app(
    session_factory: Callable[[], Session],
    cors_origins: Sequence[str] | None = None,
) -> FastAPI:
    """Create API routes whose only data dependency is PostgreSQL."""
    # Route handlers remain colocated in this small REST adapter; their local
    # names intentionally count toward the factory's local-variable total.
    # pylint: disable=too-many-locals
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_configured_cors_origins(cors_origins)),
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=[_CORRELATION_HEADER],
        expose_headers=[_CORRELATION_HEADER],
    )

    @app.middleware("http")
    async def echo_correlation_id(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Assign and echo a safe correlation ID on every completed response."""
        request.state.correlation_id = _correlation_id(request)
        response = await call_next(request)
        response.headers[_CORRELATION_HEADER] = request.state.correlation_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, error: StarletteHTTPException
    ) -> JSONResponse:
        """Convert intentional HTTP failures to the shared public envelope."""
        message = (
            error.detail if isinstance(error.detail, str) else "Request failed"
        )
        return _error_response(
            error.status_code,
            f"HTTP_{error.status_code}",
            message,
            request.state.correlation_id,
            error.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, _error: RequestValidationError
    ) -> JSONResponse:
        """Return bounded validation information without body or stack details."""
        return _error_response(
            422,
            "VALIDATION_ERROR",
            "Request validation failed",
            request.state.correlation_id,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, error: Exception
    ) -> JSONResponse:
        """Log unexpected failures and return a non-disclosing envelope."""
        _LOGGER.error(
            "Unhandled API error",
            exc_info=error,
            extra={"correlation_id": request.state.correlation_id},
        )
        return _error_response(
            500,
            "INTERNAL_SERVER_ERROR",
            "Internal server error",
            request.state.correlation_id,
        )

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
                "timestamp": _utc_z(item.timestamp),
                "latitude": item.latitude,
                "longitude": item.longitude,
                "altitude": item.altitude,
                "spatial_key": item.spatial_key,
                "wind_speed": item.wind_speed,
                "wind_direction": item.wind_direction,
                "temperature": item.temperature,
                "precipitation": item.precipitation,
                "visibility": item.visibility,
                "pressure": item.pressure,
                "source": item.source_id,
                "model": item.model,
                "forecast_cycle": (_utc_z(item.forecast_cycle)),
                "forecast_lead_time": item.forecast_lead_seconds,
                # The camp or summit this record was interpolated to. It is the
                # same label callers already filter on via ?profile= and that the
                # profile route echoes, so withholding it from the record left
                # the client unable to tell which height a row described once
                # rows for several profiles were mixed in one response.
                "route_profile": item.route_profile,
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
                    "last_success_at": _utc_z(row.last_success_at),
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
                    "last_success_at": _utc_z(row.last_success_at),
                    "last_failure_at": _utc_z(row.last_failure_at),
                }
                for row in rows
            ]
        }

    @app.get("/healthz")
    def liveness() -> dict[str, str]:
        """Process liveness: the API process is up (no dependency probe)."""
        return {"status": "ok"}

    @app.get("/readyz")
    def readiness(session: Session = Depends(get_session)) -> dict[str, str]:
        """Readiness: the API can reach the persistent database."""
        session.execute(select(1))
        return {"status": "ready"}

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
                "retrieved_at": _utc_z(row.retrieved_at),
            }
        }

    @app.get("/api/everest/route")
    def everest_route(
        response: Response,
        correlation_id: str | None = Header(
            default=None, alias="X-Correlation-ID"
        ),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        """Return the persisted OSM South Col camps and route polyline.

        Only persisted snapshot rows are returned; no external call is made.
        Camps are named points; route is an ordered list of [latitude,
        longitude] vertices. This is the EV-OSM-002 display endpoint.
        """
        correlation(response, correlation_id)
        rows = session.scalars(
            select(OsmFeatureModel)
            .order_by(OsmFeatureModel.feature_kind, OsmFeatureModel.sequence)
        ).all()
        camps = [
            {
                "name": row.name,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "elevation_m": row.elevation_m,
                "osm_ref": row.osm_ref,
            }
            for row in rows
            if row.feature_kind == "camp"
        ]
        route = [
            [row.latitude, row.longitude]
            for row in rows
            if row.feature_kind == "route"
        ]
        summit = next(
            (
                {
                    "name": row.name,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "elevation_m": row.elevation_m,
                    "osm_ref": row.osm_ref,
                }
                for row in rows
                if row.feature_kind == "summit"
            ),
            None,
        )
        return {
            "source_id": "osm-overpass",
            "dataset": "osm-south-col",
            "camps": camps,
            "route": route,
            # Null until the OSM peak node has been ingested; the scene must not
            # substitute a hard-coded 8848 m marker when it is absent.
            "summit": summit,
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
                "timestamp": _utc_z(row.timestamp),
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
                    "timestamp": _utc_z(row.timestamp),
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
