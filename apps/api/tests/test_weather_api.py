"""Minimal REST adapter tests that do not contact external weather providers."""

from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from everest_api.app import create_app
from everest_api.weather.models import WeatherRecordModel


_PUBLIC_WEATHER_FIELDS = {
    "record_type",
    "timestamp",
    "latitude",
    "longitude",
    "altitude",
    "spatial_key",
    "wind_speed",
    "wind_direction",
    "temperature",
    "precipitation",
    "visibility",
    "pressure",
    "source",
    "model",
    "forecast_cycle",
    "forecast_lead_time",
    "route_profile",
    "quality_flags",
}
# Raw-provenance, storage, and retention internals. ``route_profile`` is not
# among them: it is a canonical label the profile route already accepts as a
# query parameter and echoes at the top level, so serving it on the record
# discloses nothing the caller did not supply.
_PRIVATE_WEATHER_FIELDS = {
    "raw_artifact_id",
    "record_id",
    "dataset",
    "created_at",
    "object_reference",
    "source_url",
    "sha256",
    "metadata_json",
    "retention_owner",
    "retention_class",
    "retention_period_seconds",
    "retention_due_at",
    "retention_policy_version",
    "disposition_state",
    "hold_state",
    "hold_details",
    "audit_events",
}


def _weather_record() -> WeatherRecordModel:
    """Build one transient persisted-model shape without a database."""
    timestamp = datetime(2026, 8, 21, tzinfo=UTC)
    return WeatherRecordModel(
        record_id=UUID("11111111-1111-1111-1111-111111111111"),
        raw_artifact_id=UUID("22222222-2222-2222-2222-222222222222"),
        source_id="dwd-icon",
        dataset="private/raw/dataset",
        record_type="forecast",
        timestamp=timestamp,
        latitude=27.926742553710938,
        longitude=86.921875,
        altitude=5830.964752197266,
        spatial_key="icon:a27b8de618c411e4820ab5b098c6a5c0:818403",
        model="ICON",
        forecast_cycle=timestamp,
        forecast_lead_seconds=0,
        route_profile="SUMMIT",
        quality_flags=["missing_value"],
        wind_speed=2.0440636678148207,
        wind_direction=286.0613838292081,
        temperature=-3.3708862304687273,
        precipitation=None,
        visibility=None,
        pressure=None,
        relative_humidity=None,
        dew_point=None,
        cloud_cover=None,
        cloud_base=None,
        cloud_top=None,
        snowfall=None,
        gust_speed=None,
        created_at=timestamp,
    )


class _FakeSession:  # pylint: disable=too-few-public-methods
    """Read-session stand-in for deterministic non-database API tests."""

    def scalars(self, _statement: object) -> list[WeatherRecordModel]:
        """Return one canonical model for every supported weather query."""
        return [_weather_record()]

    def close(self) -> None:
        """Match the SQLAlchemy session lifecycle used by the dependency."""


class _FailingSession(_FakeSession):
    """Session stand-in that proves unexpected errors stay private."""

    def scalars(self, _statement: object) -> list[WeatherRecordModel]:
        """Raise a detail that must not cross the API boundary."""
        raise RuntimeError("private database password=do-not-leak")


class _Rows:
    """Small SQLAlchemy result shape for public serialization tests."""

    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        """Return all configured rows."""
        return self._rows

    def first(self) -> object | None:
        """Return the first configured row when present."""
        return self._rows[0] if self._rows else None

    def scalars(self) -> "_Rows":
        """Match an execute result's scalar projection."""
        return self


class _PublicDateTimeSession(_FakeSession):
    """Return endpoint-specific rows carrying a positive UTC offset."""

    timestamp = datetime(2026, 8, 21, 8, tzinfo=timezone(timedelta(hours=8)))

    def __init__(self, row: object) -> None:
        self._row = row

    def scalars(self, _statement: object) -> _Rows:
        """Return one row for registry, terrain, or satellite queries."""
        return _Rows([self._row])

    def execute(self, _statement: object) -> _Rows:
        """Return one row for the observation query."""
        return _Rows([self._row])


@pytest.mark.parametrize(
    "path",
    [
        "/api/weather/current?source=dwd-icon",
        "/api/weather/forecast?source=dwd-icon",
        "/api/weather/profile?profile=summit",
    ],
)
def test_weather_responses_include_spatial_key_without_private_fields(
    path: str,
) -> None:
    """All canonical weather views expose spatial identity, never raw facts."""
    response = TestClient(create_app(_FakeSession)).get(path)

    assert response.status_code == 200
    public_record = response.json()["records"][0]
    assert set(public_record) == _PUBLIC_WEATHER_FIELDS
    assert (
        public_record["spatial_key"]
        == "icon:a27b8de618c411e4820ab5b098c6a5c0:818403"
    )
    assert _PRIVATE_WEATHER_FIELDS.isdisjoint(public_record)
    assert "private/raw/dataset" not in response.text


class _ProfileColumnSession(_FakeSession):
    """Return one profile record carrying a height label and a pressure level."""

    def scalars(self, _statement: object) -> list[WeatherRecordModel]:
        """Return a summit-labelled record with its interpolated pressure."""
        record = _weather_record()
        record.pressure = 314.0
        return [record]


def test_profile_records_carry_their_height_label_and_pressure() -> None:
    """A vertical record states which camp it is for and at what pressure.

    Both columns were persisted but omitted from the payload, so every profile
    row reached the client with ``route_profile`` and ``pressure`` absent and the
    vertical dimension could not be rendered from the API alone.
    """
    response = TestClient(create_app(_ProfileColumnSession)).get(
        "/api/weather/profile?profile=summit"
    )

    assert response.status_code == 200
    record = response.json()["records"][0]
    assert record["route_profile"] == "SUMMIT"
    assert record["pressure"] == 314.0
    assert record["altitude"] == pytest.approx(5830.964752197266)


def test_profile_rejects_unsupported_profile_and_echoes_correlation_id() -> (
    None
):
    """The route validates names rather than inventing route coordinates."""
    app = create_app(_FakeSession)
    response = TestClient(app).get(
        "/api/weather/profile?profile=unsupported",
        headers={"X-Correlation-ID": "test-correlation"},
    )
    assert response.status_code == 422
    assert response.headers["X-Correlation-ID"] == "test-correlation"


def test_forecast_accepts_explicit_utc_query_datetimes() -> None:
    """Forecast range parameters accept aware datetimes with zero offset."""
    response = TestClient(create_app(_FakeSession)).get(
        "/api/weather/forecast?start=2026-08-21T00:00:00Z&"
        "end=2026-08-22T00:00:00%2B00:00"
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "value",
    ["2026-08-21T00:00:00", "2026-08-21T05:00:00%2B05:00"],
)
def test_forecast_rejects_naive_and_non_utc_query_datetimes(
    value: str,
) -> None:
    """Forecast range parameters reject ambiguous or non-UTC timestamps."""
    response = TestClient(create_app(_FakeSession)).get(
        f"/api/weather/forecast?start={value}"
    )

    assert response.status_code == 422


def test_forecast_retains_start_end_order_validation() -> None:
    """UTC validation does not replace the existing range-order contract."""
    response = TestClient(create_app(_FakeSession)).get(
        "/api/weather/forecast?start=2026-08-22T00:00:00Z&"
        "end=2026-08-21T00:00:00Z"
    )

    assert response.status_code == 422
    assert response.json()["error"]["message"] == "start must not exceed end"


def test_cors_allows_approved_origin_and_rejects_other_origin() -> None:
    """CORS permits only configured browser origins and minimal capabilities."""
    client = TestClient(
        create_app(_FakeSession, cors_origins=["http://localhost:42420"])
    )
    headers = {
        "Origin": "http://localhost:42420",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Correlation-ID",
    }
    allowed = client.options("/api/weather/current", headers=headers)
    denied = client.options(
        "/api/weather/current",
        headers={**headers, "Origin": "http://localhost:9999"},
    )
    simple = client.get(
        "/api/weather/current",
        headers={
            "Origin": headers["Origin"],
            "X-Correlation-ID": "cors-request",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == headers["Origin"]
    assert "GET" in allowed.headers["access-control-allow-methods"]
    assert (
        "x-correlation-id"
        in allowed.headers["access-control-allow-headers"].lower()
    )
    assert "access-control-allow-credentials" not in allowed.headers
    assert "access-control-allow-origin" not in denied.headers
    assert simple.headers["access-control-expose-headers"] == (
        "X-Correlation-ID"
    )
    assert simple.headers["X-Correlation-ID"] == "cors-request"


def test_public_datetimes_convert_positive_offset_to_utc_z() -> None:
    """Weather serialization normalizes aware database values to UTC Z."""
    record = _weather_record()
    record.timestamp = datetime(
        2026, 8, 21, 8, tzinfo=timezone(timedelta(hours=8))
    )
    record.forecast_cycle = record.timestamp

    class OffsetSession(_FakeSession):
        """Return the positive-offset record."""

        def scalars(self, _statement: object) -> list[WeatherRecordModel]:
            return [record]

    body = (
        TestClient(create_app(OffsetSession))
        .get("/api/weather/current")
        .json()["records"][0]
    )
    assert body["timestamp"] == "2026-08-21T00:00:00Z"
    assert body["forecast_cycle"] == "2026-08-21T00:00:00Z"


def test_other_public_datetime_endpoints_convert_positive_offset_to_utc_z() -> (
    None
):
    """Sources, health, and all three extension routes emit UTC Z."""
    timestamp = _PublicDateTimeSession.timestamp
    registry = SimpleNamespace(
        source_id="source",
        status="connected",
        health_status="unknown",
        last_success_at=timestamp,
        last_failure_at=timestamp,
    )
    terrain = SimpleNamespace(
        tile_name="tile",
        crs="EPSG:4326",
        west=86.0,
        south=27.0,
        east=87.0,
        north=28.0,
        resolution_degrees=0.1,
        min_elevation=1.0,
        max_elevation=2.0,
        retrieved_at=timestamp,
    )
    observation = SimpleNamespace(
        timestamp=timestamp,
        station="Base Camp",
        temperature_c=1.0,
        relative_humidity=2.0,
        precipitation=0.0,
        weather_code=None,
        missing=False,
        quality_flags=[],
    )
    satellite = SimpleNamespace(
        timestamp=timestamp,
        band=3,
        segment=1,
        satellite_name="Himawari-9",
        observation_area="FLDK",
        size_bytes=1,
    )

    source_client = TestClient(
        create_app(lambda: _PublicDateTimeSession(registry))
    )
    assert (
        source_client.get("/api/weather/sources").json()["sources"][0][
            "last_success_at"
        ]
        == "2026-08-21T00:00:00Z"
    )
    health = source_client.get("/api/data-health").json()["sources"][0]
    assert health["last_success_at"] == "2026-08-21T00:00:00Z"
    assert health["last_failure_at"] == "2026-08-21T00:00:00Z"

    terrain_client = TestClient(
        create_app(lambda: _PublicDateTimeSession(terrain))
    )
    terrain_body = terrain_client.get(
        "/api/terrain/tile?latitude=27.5&longitude=86.5"
    ).json()
    assert terrain_body["tile"]["retrieved_at"] == "2026-08-21T00:00:00Z"

    observation_client = TestClient(
        create_app(lambda: _PublicDateTimeSession(observation))
    )
    observation_body = observation_client.get(
        "/api/observations/current"
    ).json()
    assert (
        observation_body["observations"]["Base Camp"]["timestamp"]
        == "2026-08-21T00:00:00Z"
    )

    satellite_client = TestClient(
        create_app(lambda: _PublicDateTimeSession(satellite))
    )
    satellite_body = satellite_client.get(
        "/api/satellite/segments?band=3"
    ).json()
    assert satellite_body["segments"][0]["timestamp"] == (
        "2026-08-21T00:00:00Z"
    )


def test_validation_error_uses_envelope_and_safe_correlation_header() -> None:
    """422 responses echo safe IDs in both the body and response header."""
    response = TestClient(create_app(_FakeSession)).get(
        "/api/weather/forecast?start=not-a-datetime",
        headers={"X-Correlation-ID": "ui-request-42"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "correlation_id": "ui-request-42",
        }
    }
    assert response.headers["X-Correlation-ID"] == "ui-request-42"


def test_unhandled_error_uses_safe_envelope_without_exception_detail() -> None:
    """500 responses include an ID but do not expose internal exception text."""
    client = TestClient(
        create_app(_FailingSession), raise_server_exceptions=False
    )
    response = client.get("/api/weather/current")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_SERVER_ERROR"
    assert error["message"] == "Internal server error"
    assert error["correlation_id"] == response.headers["X-Correlation-ID"]
    assert "password" not in response.text
