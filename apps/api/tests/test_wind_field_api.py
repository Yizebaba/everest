"""Materialized wind-field API tests with no provider access."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import xarray as xr
from fastapi.testclient import TestClient

from services.weather.wind_field import (  # pylint: disable=import-error
    build_wind_field_frame,
    materialize_wind_field_frame,
)
from everest_api.app import create_app


def _session_must_not_be_opened():
    raise AssertionError("wind-field GET must not open a database session")


def test_unconfigured_wind_field_is_explicitly_unavailable(monkeypatch) -> None:
    """An absent root yields a bounded response without touching dependencies."""
    monkeypatch.delenv("EVEREST_WIND_FIELD_DERIVED_ROOT", raising=False)

    response = TestClient(create_app(_session_must_not_be_opened)).get(
        "/api/weather/wind-field"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "unavailable",
        "reason": "not_configured",
        "frame": None,
    }


def test_configured_empty_root_is_explicitly_unavailable(tmp_path) -> None:
    """A configured root with no latest frame remains an honest empty result."""
    response = TestClient(
        create_app(_session_must_not_be_opened, wind_field_root=tmp_path)
    ).get("/api/weather/wind-field")

    assert response.status_code == 200
    assert response.json() == {
        "status": "unavailable",
        "reason": "no_valid_materialized_frame",
        "frame": None,
    }


def test_get_reads_latest_local_frame_without_provider_or_raw_path(
    tmp_path,
) -> None:
    """GET serves only the latest integrity-checked derived JSON frame."""
    cycle = datetime(2026, 8, 27, tzinfo=UTC)
    dataset = xr.Dataset(
        {
            "u": (("latitude", "longitude"), [[1.0]]),
            "v": (("latitude", "longitude"), [[2.0]]),
        },
        coords={"latitude": [28.0], "longitude": [87.0]},
    )
    frame = build_wind_field_frame(
        dataset,
        source="ecmwf-ifs",
        model="IFS",
        cycle=cycle,
        valid_time=cycle + timedelta(hours=3),
        lead=timedelta(hours=3),
        level=400.0,
        level_units="hPa",
        bounds=(86.5, 27.5, 87.5, 28.5),
    )
    materialize_wind_field_frame(frame, tmp_path)

    response = TestClient(
        create_app(_session_must_not_be_opened, wind_field_root=tmp_path)
    ).get("/api/weather/wind-field")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["frame"] == frame.to_dict()
    assert "path" not in response.text.lower()
    assert "url" not in response.text.lower()
