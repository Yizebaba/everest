"""Alembic environment for reviewed Everest PostgreSQL migrations."""

# pylint: disable=no-member,wrong-import-order,unused-import
# Alembic exposes runtime proxy members; importing models registers metadata.

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from everest_api.persistence.database import Base, resolve_database_url
from everest_api.registry import models  # Registers registry metadata.
from everest_api.osm import models as osm_models  # Registers OSM metadata.
from everest_api.weather import (
    models as weather_models,
)  # Registers weather metadata.

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The database target is resolved by the one shared resolver so migrations
# can never be applied to a different store than the API and the scheduler
# use, and alembic.ini deliberately carries no URL. A caller that sets one
# explicitly must still win: overriding it unconditionally meant an
# integration-test fixture pointing at a disposable database was ignored,
# and the ``downgrade base`` at the end of that fixture dropped every table
# in the served database instead.
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", resolve_database_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without opening a database connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations within a database-managed transaction."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
