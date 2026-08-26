"""Database primitives used by the Phase A registry persistence adapter."""

from __future__ import annotations

import os
from urllib.parse import quote

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DB_HOST = "127.0.0.1"


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base metadata for reviewed Everest persistence models."""


def resolve_database_url() -> str:
    """Return the one database URL every Everest process must agree on.

    Resolution order:

    1. ``EVEREST_DATABASE_URL`` verbatim, when set.
    2. Composed from ``EVEREST_DB_USER``, ``EVEREST_DB_PASSWORD``,
       ``EVEREST_DB_NAME``, ``EVEREST_DB_PORT`` and optional
       ``EVEREST_DB_HOST``.

    There is deliberately no built-in fallback target. A process that cannot
    resolve its database must fail loudly: silently defaulting to a different
    database is what let the writer and the reader drift onto two separate
    stores (scheduler -> ``everest``, hand-started API -> ``everest_test``).
    """
    explicit = os.environ.get("EVEREST_DATABASE_URL", "").strip()
    if explicit:
        return explicit
    missing = [
        name
        for name in (
            "EVEREST_DB_USER",
            "EVEREST_DB_PASSWORD",
            "EVEREST_DB_NAME",
            "EVEREST_DB_PORT",
        )
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(
            "cannot resolve the Everest database: set EVEREST_DATABASE_URL, "
            f"or provide {', '.join(missing)}"
        )
    user = quote(os.environ["EVEREST_DB_USER"], safe="")
    password = quote(os.environ["EVEREST_DB_PASSWORD"], safe="")
    host = os.environ.get("EVEREST_DB_HOST", DEFAULT_DB_HOST)
    port = os.environ["EVEREST_DB_PORT"]
    name = os.environ["EVEREST_DB_NAME"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create an application-owned transactional session factory."""
    engine: Engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)
