"""Development launcher: serve the Everest API on the documented port.

Usage (from apps/api):
  python run_dev.py
Requires PostgreSQL with the migrated schema and an explicitly resolvable
database target: either ``EVEREST_DATABASE_URL`` or the ``EVEREST_DB_*``
variables (see ``everest_api.persistence.database.resolve_database_url``).
There is no default target -- the launcher fails rather than connect to a
different database than the ingestion path writes to.
"""

from __future__ import annotations

import os

import uvicorn

from everest_api.app import create_app
from everest_api.persistence.database import (
    create_session_factory,
    resolve_database_url,
)

# Cloud Run injects PORT; local Docker keeps the documented Everest port.
PORT = int(os.environ.get("PORT", os.environ.get("EVEREST_API_PORT", "52147")))
HOST = os.environ.get("EVEREST_API_HOST", "0.0.0.0")


def main() -> None:
    """Run uvicorn on the documented non-standard port."""
    database_url = resolve_database_url()
    factory = create_session_factory(database_url)
    app = create_app(factory)
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
