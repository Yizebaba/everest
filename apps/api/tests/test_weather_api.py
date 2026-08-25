"""Minimal REST adapter tests that do not contact external weather providers."""

from datetime import UTC, datetime
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
    "source",
    "model",
    "forecast_cycle",
    "forecast_lead_time",
    "quality_flags",
}
_PRIVATE_WEATHER_FIELDS = {
    "raw_artifact_id",
    "record_id",
    "dataset",
    "route_profile",
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
    assert response.json()["detail"] == "start must not exceed end"
