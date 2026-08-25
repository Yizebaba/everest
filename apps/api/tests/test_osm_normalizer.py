"""Unit tests for the OSM (Overpass) South Col normalizer (EV-OSM-002).

Pure Python; no database or network required.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Iterator

import pytest

import everest_api.osm.overpass as overpass
from everest_api.osm.overpass import (
    OVERPASS_ENDPOINTS,
    SOUTH_COL_BBOX,
    SOUTH_COL_CAMPS,
    SOUTH_COL_RELATION_ID,
    _relation_order,
    normalize_camps,
)


class _FakeResponse:
    """Minimal urllib response wrapper returning preloaded bytes."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _FakeOpener:
    """Stub for urllib.request.urlopen keyed by POSTed query."""

    def __init__(self, by_query: dict[str, bytes]) -> None:
        self._by_query = by_query
        self.calls: list[dict[str, object]] = []

    def __call__(self, request: urllib.request.Request, timeout: float = 0):
        del timeout
        self.calls.append({"url": request.full_url, "data": request.data})
        data = request.data.decode() if isinstance(request.data, bytes) else ""
        for query, payload in self._by_query.items():
            if query in data:
                return _FakeResponse(payload)
        raise RuntimeError(f"unexpected Overpass query: {data}")


@pytest.fixture
def fake_open(monkeypatch: pytest.MonkeyPatch) -> Iterator[_FakeOpener]:
    """Install a stub urlopen that returns per-query fixtures."""

    def _envelope(elements: list[dict[str, object]]) -> bytes:
        return json.dumps({"elements": elements}).encode("utf-8")

    def _node(oid: int, name: str, lat: float, lon: float) -> dict[str, object]:
        return {
            "type": "node",
            "id": oid,
            "lat": lat,
            "lon": lon,
            "tags": {"name": name, "tourism": "camp_site"},
        }

    camps = _envelope(
        [
            _node(5225912921, "Everest Base Camp", 27.9996646, 86.8487946),
            _node(4880806686, "Camp 1S", 27.9864173, 86.8765224),
            _node(4880806685, "Camp 2S", 27.9815643, 86.8991408),
            _node(5058632244, "Camp 3S", 27.9688883, 86.9178104),
            _node(576713400, "Camp 4S South Col", 27.9733654, 86.9302508),
            # Nearby non-route camps must be filtered out by the allowlist.
            _node(5786165781, "Island Peak High Camp", 27.9089791, 86.9347668),
            _node(12771599701, "Asian Trekking", 27.9983698, 86.8488755),
        ]
    )
    route = _envelope(
        [
            {
                "type": "way",
                "id": 518618562,
                "geometry": [
                    {"lat": 27.9988062, "lon": 86.8651070},
                    {"lat": 27.9987493, "lon": 86.8673166},
                ],
            },
            {
                "type": "way",
                "id": 1380301536,
                "geometry": [
                    {"lat": 28.0016993, "lon": 86.8589289},
                    {"lat": 27.9990386, "lon": 86.8649214},
                    {"lat": 27.9988062, "lon": 86.8651070},
                ],
            },
            {
                "type": "way",
                "id": 1274622141,
                "geometry": [
                    {"lat": 28.0029111, "lon": 86.8557320},
                    {"lat": 28.0016993, "lon": 86.8589289},
                ],
            },
        ]
    )
    opener = _FakeOpener(
        {
            "tourism": camps,
            "relation": route,
        }
    )
    monkeypatch.setattr(overpass.urllib.request, "urlopen", opener)
    yield opener


def test_constants_are_approved_osm_scope() -> None:
    """Constants pin the approved OSM source and the South Col AOI."""
    assert OVERPASS_ENDPOINTS
    assert all(endpoint.startswith("https://") for endpoint in OVERPASS_ENDPOINTS)
    assert SOUTH_COL_RELATION_ID == 17822898
    assert SOUTH_COL_BBOX == (27.90, 86.75, 28.05, 87.10)
    assert "Everest Base Camp" in SOUTH_COL_CAMPS
    assert "Camp 4S South Col" in SOUTH_COL_CAMPS


def test_fetch_camps_filters_non_route_camps(fake_open: _FakeOpener) -> None:
    """Overpass camp fetch returns only the allowlisted South Col camps."""
    camps = overpass.fetch_camps()
    names = {str(camp["name"]) for camp in camps}
    assert names == set(SOUTH_COL_CAMPS)
    assert "Island Peak High Camp" not in names
    assert "Asian Trekking" not in names
    assert len(fake_open.calls) == 1


def test_fetch_route_vertices_chains_ways_head_to_tail(
    fake_open: _FakeOpener,
) -> None:
    """Route vertices form one continuous polyline across member ways."""
    route = overpass.fetch_route_vertices()
    assert route[0] == (27.9988062, 86.8651070)
    # The three ways connect: 518618562 -> 1380301536 -> 1274622141,
    # so the last fetched vertex equals the first (closed loop).
    assert route[-1] == (28.0029111, 86.8557320)
    assert len(route) == 7


def test_relation_order_uses_member_sequence() -> None:
    """Ways are sorted by the relation member order, not by id."""
    envelope = {
        "elements": [
            {
                "type": "relation",
                "members": [
                    {"type": "way", "ref": 518618562},
                    {"type": "way", "ref": 1380301536},
                    {"type": "way", "ref": 1274622141},
                ],
            }
        ]
    }
    key = _relation_order(envelope)
    ways = [
        {"id": 1274622141},
        {"id": 518618562},
        {"id": 1380301536},
    ]
    ordered = sorted(ways, key=key)
    assert [w["id"] for w in ordered] == [
        518618562,
        1380301536,
        1274622141,
    ]


def test_normalize_camps_projects_sync_shape() -> None:
    """Normalizer projects raw camp dicts into the service sync shape."""
    raw = [
        {
            "osm_id": "5225912921",
            "name": "Everest Base Camp",
            "latitude": 27.9996646,
            "longitude": 86.8487946,
        }
    ]
    normalized = normalize_camps(raw)
    assert normalized == [
        ("Everest Base Camp", 27.9996646, 86.8487946, None, "5225912921")
    ]
