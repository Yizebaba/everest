"""Everest EV-OSM-002 ingest: refresh the OSM South Col camps and route.

Fetches the Everest South Col camps and route polyline from the public Overpass
API (approved OSM source), normalizes them, and upserts them into the
persistent database via OsmFeatureService. Safe to run repeatedly; each run
replaces the snapshot for the osm-south-col dataset.

Usage:  python ingest_osm_route.py
"""

# pylint: disable=wrong-import-position,wrong-import-order,import-outside-toplevel
# sys.path insertion before local imports is required for this standalone script.

from __future__ import annotations

import sys

sys.path.insert(0, "/mnt/d/Everest")
sys.path.insert(0, "/mnt/d/Everest/apps/api")

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from everest_api.osm import (  # noqa: E402
    OsmFeatureService,
    fetch_camps,
    fetch_route_vertices,
    normalize_camps,
)
from everest_api.osm.overpass import fetch_summit  # noqa: E402
from everest_api.registry.models import DataSourceRegistryModel  # noqa: E402


def _env_db_url() -> str:
    from everest_api.persistence.database import resolve_database_url

    return resolve_database_url()


def _seed(session) -> None:
    """Register the OSM Overpass source if it is not already present."""
    existing = session.scalars(
        select(DataSourceRegistryModel).where(
            DataSourceRegistryModel.source_id == "osm-overpass"
        )
    ).first()
    if existing is None:
        session.add(
            DataSourceRegistryModel(
                source_id="osm-overpass",
                name="OpenStreetMap Overpass API",
                provider="OpenStreetMap Foundation",
                category="cartographic",
                status="connected",
                access_method="Overpass API",
                endpoint="https://overpass-api.de/api/interpreter",
                data_format="OSM XML/JSON",
                update_frequency="on demand",
                license_name="ODbL 1.0",
                commercial_allowed=True,
                credentials_required=False,
                health_status="unknown",
                metadata_version=1,
            )
        )
        session.commit()


def main() -> None:
    """Fetch Overpass data and sync the South Col snapshot to PostgreSQL."""
    camps = fetch_camps()
    route = fetch_route_vertices()
    summit = fetch_summit()
    if not camps and not route:
        print("no OSM features returned; aborting without writing")
        raise SystemExit(1)
    engine = create_engine(_env_db_url())
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        _seed(session)
    service = OsmFeatureService(factory)
    count = service.sync(
        normalize_camps(camps),
        route,
        normalize_camps([summit])[0] if summit else None,
    )
    missing = [c["name"] for c in camps if c.get("elevation_m") is None]
    print(f"synced {count} OSM features "
          f"({len(camps)} camps, {len(route)} route vertices, "
          f"summit={'yes' if summit else 'no'})")
    if missing:
        # Reported rather than filled in: a camp with no OSM ele would be drawn
        # at sea level, and inventing a height here would hide that.
        print(f"camps without an OSM ele tag: {', '.join(missing)}")


if __name__ == "__main__":
    main()
