"""PostgreSQL-only setup for reviewed Phase A integration tests."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import os
from pathlib import Path
import sys
from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from alembic import command
from alembic.config import Config

from everest_api.raw_storage import RawStoragePolicy

_DATABASE_URL_ENV = "EVEREST_TEST_DATABASE_URL"
_PROJECT_ROOT = Path(__file__).parent.parent
_WORKSPACE_ROOT = _PROJECT_ROOT.parent.parent

if str(_WORKSPACE_ROOT) not in sys.path:
    # Integration composition imports the checked-in meteorology adapter.
    sys.path.insert(0, str(_WORKSPACE_ROOT))


def _test_database_url() -> str:
    """Return PostgreSQL test URL; never substitute SQLite for these tests."""
    url = os.environ.get(_DATABASE_URL_ENV)
    if not url:
        pytest.skip(f"{_DATABASE_URL_ENV} is required for PostgreSQL tests")
    if not url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail(f"{_DATABASE_URL_ENV} must name a PostgreSQL database")
    return url


@pytest.fixture(name="migrated_postgres_engine")
def _migrated_postgres_engine() -> Iterator[Engine]:
    """Upgrade then downgrade one disposable PostgreSQL database per test."""
    url = _test_database_url()
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    engine = create_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()
        command.downgrade(config, "base")


@pytest.fixture
def postgres_session(migrated_postgres_engine: Engine) -> Iterator[Session]:
    """Provide one session against the migration-created PostgreSQL schema."""
    factory = sessionmaker(
        bind=migrated_postgres_engine, expire_on_commit=False
    )
    with factory() as session:
        yield session


@pytest.fixture(name="raw_storage_policy")
def _raw_storage_policy(tmp_path: Path) -> RawStoragePolicy:
    """Provide a temporary external root without touching checked-in raw paths."""
    raw_root = tmp_path / "approved-raw"
    raw_root.mkdir()
    return RawStoragePolicy(raw_root, _WORKSPACE_ROOT)


@pytest.fixture(name="write_raw_fixture")
def _write_raw_fixture(
    raw_storage_policy: RawStoragePolicy,
) -> Callable[[str, bytes], tuple[str, int]]:
    """Write deterministic test bytes and return their actual hash and size."""

    def _write(object_reference: str, payload: bytes) -> tuple[str, int]:
        artifact_path = raw_storage_policy.resolve_object_reference(
            object_reference
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest(), len(payload)

    return _write
