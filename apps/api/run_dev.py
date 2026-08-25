"""Development launcher: serve the Everest API on the documented port.

Usage (from apps/api):
  python run_dev.py
Requires PostgreSQL with migrated schema (revision 20260824_0007) and the
documented database URL. Defaults to the disposable everest_test database.
"""

from __future__ import annotations

import os

import uvicorn

from everest_api.app import create_app
from everest_api.persistence.database import create_session_factory

DEFAULT_URL = "postgresql+psycopg://everest:everest@127.0.0.1:5432/everest_test"
PORT = int(os.environ.get("EVEREST_API_PORT", "50149"))


def main() -> None:
    """Run uvicorn on the documented non-standard port."""
    database_url = os.environ.get("EVEREST_DATABASE_URL", DEFAULT_URL)
    factory = create_session_factory(database_url)
    app = create_app(factory)
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
