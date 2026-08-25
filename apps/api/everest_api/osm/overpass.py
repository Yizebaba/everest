"""Overpass API connector and normalizer for the Everest South Col route.

The connector performs two read-only queries against the public Overpass
endpoint (approved OSM source): one for named camp sites inside the AOI and
one for the Everest South Col hiking relation's member-way geometries. The
normalizers convert the raw Overpass JSON into the camp/route shapes consumed
by ``OsmFeatureService.sync``. No credentials are required.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence

#: Public Overpass interpreter endpoints, tried in order.
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

#: AOI bounding box for the Everest South Col route in
#: (south=min_lat, west=min_lon, north=max_lat, east=max_lon) order.
SOUTH_COL_BBOX = (27.90, 86.75, 28.05, 87.10)

#: Everest South Col hiking relation id (OSM).
SOUTH_COL_RELATION_ID = 17822898

#: Named camps that belong to the South Col route. Overpass also returns
#: nearby camp sites (Island Peak, trekking operators, Chinese-named nodes);
#: the allowlist keeps the persisted snapshot scoped to the South Col route.
SOUTH_COL_CAMPS = frozenset(
    {
        "Everest Base Camp",
        "Camp 1S",
        "Camp 2S",
        "Camp 3S",
        "Camp 4S South Col",
    }
)

_USER_AGENT = "Everest/0.1 (local demo; research use only)"


def _post_query(endpoint: str, query: str, timeout: float = 45.0) -> dict[str, object]:
    """POST one Overpass QL query and return the decoded JSON envelope."""
    request = urllib.request.Request(
        endpoint,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": _USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def _run_query(query: str, timeout: float = 45.0) -> dict[str, object]:
    """Try Overpass mirrors in order and raise the first non-transient error."""
    last_error: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            return _post_query(endpoint, query, timeout)
        except Exception as error:  # pylint: disable=broad-exception-caught
            last_error = error
    assert last_error is not None
    raise RuntimeError(f"Overpass query failed: {last_error}")


def fetch_camps() -> list[dict[str, object]]:
    """Return named ``tourism=camp_site`` nodes inside the South Col AOI."""
    south, west, north, east = SOUTH_COL_BBOX
    query = (
        "[out:json][timeout:30];"
        "node[\"tourism\"=\"camp_site\"]"
        f"({south},{west},{north},{east});"
        "out body;"
    )
    envelope = _run_query(query)
    elements = envelope.get("elements", [])
    camps: list[dict[str, object]] = []
    for element in elements:
        tags = element.get("tags") or {}
        name = tags.get("name")
        if not name or name not in SOUTH_COL_CAMPS:
            continue
        camps.append(
            {
                "osm_id": str(element.get("id", "")),
                "name": str(name),
                "latitude": float(element.get("lat", 0.0)),
                "longitude": float(element.get("lon", 0.0)),
            }
        )
    camps.sort(key=lambda camp: str(camp["name"]))
    return camps


def fetch_route_vertices() -> list[tuple[float, float]]:
    """Return ordered ``(latitude, longitude)`` vertices of the South Col route.

    The relation's member ways are fetched with their node geometry and chained
    head-to-tail so the returned list forms one continuous polyline.
    """
    query = (
        f"[out:json][timeout:40];relation({SOUTH_COL_RELATION_ID});"
        "way(r);out geom;"
    )
    envelope = _run_query(query)
    elements = envelope.get("elements", [])
    ways = [
        element
        for element in elements
        if element.get("type") == "way" and element.get("geometry")
    ]
    if not ways:
        return []
    ways.sort(key=_relation_order(envelope))
    polyline: list[tuple[float, float]] = []
    for way in ways:
        geometry = way["geometry"]
        points = [
            (float(point["lat"]), float(point["lon"])) for point in geometry
        ]
        if polyline and points:
            if _distance(points[0], polyline[-1]) > _distance(
                points[-1], polyline[-1]
            ):
                points.reverse()
        polyline.extend(points)
    return polyline


def _relation_order(envelope: dict[str, object]) -> Callable[[dict[str, object]], int]:
    """Return a sort key for ways based on the relation's member order."""
    order: dict[str, int] = {}
    for element in envelope.get("elements", []):
        if element.get("type") != "relation":
            continue
        for index, member in enumerate(element.get("members", [])):
            if member.get("type") == "way":
                order[str(member.get("ref"))] = index
    return lambda way: order.get(str(way.get("id")), 0)


def _distance(
    left: tuple[float, float], right: tuple[float, float]
) -> float:
    """Approximate squared Euclidean distance in degrees (ordering only)."""
    return (left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2


def normalize_camps(camps: Sequence[dict[str, object]]) -> list[tuple]:
    """Project raw Overpass camp nodes into the sync shape."""
    return [
        (
            str(item["name"]),
            float(item["latitude"]),
            float(item["longitude"]),
            None,
            str(item["osm_id"]),
        )
        for item in camps
    ]


__all__ = [
    "OVERPASS_ENDPOINTS",
    "SOUTH_COL_BBOX",
    "SOUTH_COL_CAMPS",
    "SOUTH_COL_RELATION_ID",
    "fetch_camps",
    "fetch_route_vertices",
    "normalize_camps",
]
