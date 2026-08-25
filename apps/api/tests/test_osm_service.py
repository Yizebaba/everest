"""Integration tests for OSM feature persistence and the route API (EV-OSM-002).

Requires EVEREST_TEST_DATABASE_URL (real PostgreSQL). The conftest fixture
migrates a disposable database to head, which includes the OSM feature table.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from everest_api.app import create_app
from everest_api.osm.models import OsmFeatureModel
from everest_api.osm.service import OsmFeatureService


def _session_factory(engine: Engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_osm_sync_persists_camps_and_route(
    migrated_postgres_engine: Engine,
) -> None:
    """sync replaces the snapshot with the provided camps and route vertices."""
    factory = _session_factory(migrated_postgres_engine)
    service = OsmFeatureService(factory)
    retrieved = datetime(2026, 8, 26, 6, 0, tzinfo=UTC)
    count = service.sync(
        [
            ("Everest Base Camp", 27.9996646, 86.8487946, None, "5225912921"),
            ("Camp 1S", 27.9864173, 86.8765224, None, "4880806686"),
        ],
        [(27.9988062, 86.8651070), (27.9987493, 86.8673166)],
        retrieved_at=retrieved,
    )
    assert count == 4
    with factory() as session:
        rows = session.scalars(select(OsmFeatureModel)).all()
        assert len(rows) == 4
        camps = [row for row in rows if row.feature_kind == "camp"]
        route = [row for row in rows if row.feature_kind == "route"]
        assert len(camps) == 2
        assert len(route) == 2
        assert all(row.retrieved_at == retrieved for row in rows)
        assert sorted(c.name for c in camps) == [
            "Camp 1S",
            "Everest Base Camp",
        ]
        assert route[0].latitude == 27.9988062


def test_osm_sync_is_idempotent(migrated_postgres_engine: Engine) -> None:
    """Repeated sync replaces rows rather than accumulating duplicates."""
    factory = _session_factory(migrated_postgres_engine)
    service = OsmFeatureService(factory)
    camps = [("Everest Base Camp", 27.9996646, 86.8487946, None, "1")]
    route = [(27.9988062, 86.8651070)]
    assert service.sync(camps, route) == 2
    assert service.sync(camps, route) == 2
    with factory() as session:
        assert len(session.scalars(select(OsmFeatureModel)).all()) == 2


def test_osm_route_api_returns_persisted_features_no_leak(
    migrated_postgres_engine: Engine,
) -> None:
    """Route API returns camps and polyline without raw or internal fields."""
    factory = _session_factory(migrated_postgres_engine)
    OsmFeatureService(factory).sync(
        [
            ("Everest Base Camp", 27.9996646, 86.8487946, 5364.0, "5225912921"),
            ("Camp 4S South Col", 27.9733654, 86.9302508, 7906.0, "576713400"),
        ],
        [(27.9988062, 86.8651070), (27.9733654, 86.9302508)],
    )
    client = TestClient(create_app(lambda: Session(migrated_postgres_engine)))
    response = client.get("/api/everest/route")
    assert response.status_code == 200
    body = response.json()
    assert body["source_id"] == "osm-overpass"
    assert body["dataset"] == "osm-south-col"
    assert [c["name"] for c in body["camps"]] == [
        "Everest Base Camp",
        "Camp 4S South Col",
    ]
    assert body["route"] == [[27.9988062, 86.8651070], [27.9733654, 86.9302508]]
    leaked = body.keys() & {"feature_id", "created_at", "retrieved_at"}
    assert not leaked
    for camp in body["camps"]:
        assert "feature_id" not in camp
        assert "created_at" not in camp


def test_osm_route_api_empty_returns_empty_lists(
    migrated_postgres_engine: Engine,
) -> None:
    """Route API returns empty lists when no snapshot is persisted."""
    client = TestClient(create_app(lambda: Session(migrated_postgres_engine)))
    response = client.get("/api/everest/route")
    assert response.status_code == 200
    assert response.json()["camps"] == []
    assert response.json()["route"] == []
