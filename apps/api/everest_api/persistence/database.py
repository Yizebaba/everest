"""Database primitives used by the Phase A registry persistence adapter."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base metadata for reviewed Everest persistence models."""


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create an application-owned transactional session factory."""
    engine: Engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)
