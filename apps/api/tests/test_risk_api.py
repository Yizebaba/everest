"""Persisted Summit Window risk API tests; provider access is forbidden."""

# Response fixtures intentionally mirror the bounded public projection.
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from everest_api.app import create_app
from everest_api.risk import service as risk_service
from everest_api.weather.models import WeatherRecordModel


def _row(
    *,
    timestamp: datetime,
    profile: str | None = "SUMMIT",
    altitude: float = 8848.0,
    wind_speed: float | None = 12.0,
) -> WeatherRecordModel:
    return WeatherRecordModel(
        record_id=uuid4(),
        raw_artifact_id=uuid4(),
        source_id="ecmwf-ifs",
        dataset="ifs-pressure",
        record_type="forecast",
        timestamp=timestamp,
        latitude=27.98806,
        longitude=86.92528,
        altitude=altitude,
        spatial_key=f"ifs:{profile or '400hpa'}:{timestamp.hour}",
        model="IFS",
        forecast_cycle=timestamp - timedelta(hours=6),
        forecast_lead_seconds=21600,
        route_profile=profile,
        quality_flags=["missing_value"],
        wind_speed=wind_speed,
        wind_direction=90.0,
        temperature=-24.0,
        precipitation=None,
        visibility=None,
        pressure=337.0,
    )


class _ScalarRows:  # pylint: disable=too-few-public-methods
    def __init__(self, rows: list[WeatherRecordModel]) -> None:
        self._rows = rows

    def all(self) -> list[WeatherRecordModel]:
        """Return configured scalar rows."""
        return self._rows


class _Session:
    def __init__(self, rows: list[WeatherRecordModel]) -> None:
        self.rows = rows
        self.closed = False

    def scalars(self, _statement: object) -> _ScalarRows:
        """Return a SQLAlchemy-like scalar result."""
        return _ScalarRows(self.rows)

    def close(self) -> None:
        """Record dependency cleanup."""
        self.closed = True


def test_get_uses_persisted_record_and_never_calls_provider(
    monkeypatch,
) -> None:
    """GET reads the canonical table only; connector calls cannot occur."""
    now = datetime(2026, 8, 27, 12, tzinfo=UTC)
    session = _Session([_row(timestamp=now)])

    def forbidden_provider_call(*_args, **_kwargs):
        raise AssertionError("provider called during GET")

    monkeypatch.setattr(
        "services.weather.ecmwf.EcmwfOpenDataConnector.retrieve",
        forbidden_provider_call,
    )

    response = TestClient(create_app(lambda: session)).get(
        "/api/risk/summit-window"
    )

    assert response.status_code == 200
    assert response.json()["risk"]["level"] in {"go", "caution", "block"}
    assert session.closed


def test_adapter_maps_record_to_existing_engine_unchanged(monkeypatch) -> None:
    """The API adapter passes canonical units and identity into risk.assess."""
    timestamp = datetime(2026, 8, 27, 18, tzinfo=UTC)
    captured = {}

    def fake_assess(record, profile="SUMMIT"):
        captured["record"] = record
        captured["profile"] = profile
        return SimpleNamespace(
            valid_time=record.timestamp,
            profile=profile,
            altitude_metres=record.altitude,
            level=SimpleNamespace(value="caution"),
            confidence=0.75,
            factors=({"name": "wind", "value": 12.0, "risk": "go"},),
            inputs={
                "source": record.source,
                "model": record.model,
                "cycle": "2026-08-27T12:00:00Z",
                "lead_s": 21600,
            },
        )

    monkeypatch.setattr(risk_service, "assess", fake_assess)
    response = TestClient(
        create_app(lambda: _Session([_row(timestamp=timestamp)]))
    ).get("/api/risk/summit-window")

    assert response.status_code == 200
    record = captured["record"]
    assert captured["profile"] == "SUMMIT"
    assert record.timestamp == timestamp
    assert record.altitude == 8848.0
    assert record.wind_speed == 12.0
    assert record.source == "ecmwf-ifs"
    assert record.forecast.lead_time == timedelta(hours=6)
    assert response.json()["risk"]["level"] == "caution"


def test_no_persisted_basis_returns_bounded_unknown() -> None:
    """An empty canonical store is an explicit unknown, not false safety."""
    response = TestClient(create_app(lambda: _Session([]))).get(
        "/api/risk/summit-window"
    )

    assert response.status_code == 200
    assert response.json() == {
        "risk": {
            "level": "unknown",
            "confidence": 0.0,
            "valid_time": None,
            "profile": "SUMMIT",
            "altitude_metres": None,
            "factors": [],
            "inputs": {},
            "basis": "no_persisted_record",
        }
    }


def test_persisted_record_with_no_scoreable_values_maps_to_unknown() -> None:
    """The unchanged engine's unknown outcome remains explicit at the API."""
    row = _row(timestamp=datetime(2026, 8, 27, 12, tzinfo=UTC), wind_speed=None)
    row.temperature = None

    response = TestClient(create_app(lambda: _Session([row]))).get(
        "/api/risk/summit-window"
    )

    assert response.status_code == 200
    assert response.json()["risk"]["level"] == "unknown"
    assert response.json()["risk"]["basis"] == "persisted_canonical_weather"


def test_selection_prefers_summit_profile_then_newest_valid_time(
    monkeypatch,
) -> None:
    """A newer non-summit row loses to the newest persisted SUMMIT row."""
    base = datetime(2026, 8, 27, tzinfo=UTC)
    rows = [
        _row(timestamp=base + timedelta(hours=12), profile=None, altitude=9797),
        _row(timestamp=base + timedelta(hours=3)),
        _row(timestamp=base + timedelta(hours=6)),
    ]
    selected = {}

    def fake_assess(record, profile="SUMMIT"):
        selected["timestamp"] = record.timestamp
        return SimpleNamespace(
            valid_time=record.timestamp,
            profile=profile,
            altitude_metres=record.altitude,
            level=SimpleNamespace(value="go"),
            confidence=1.0,
            factors=(),
            inputs={},
        )

    monkeypatch.setattr(risk_service, "assess", fake_assess)
    response = TestClient(create_app(lambda: _Session(rows))).get(
        "/api/risk/summit-window"
    )

    assert response.status_code == 200
    assert selected["timestamp"] == base + timedelta(hours=6)
    assert response.json()["risk"]["basis"] == "persisted_canonical_weather"
