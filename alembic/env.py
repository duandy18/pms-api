# alembic/env.py
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.metadata import metadata
from app.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata
VERSION_TABLE = "pms_api_alembic_version"


def _database_url() -> str:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("PMS_DATABASE_URL is required for Alembic")
    return url


def include_name(name, type_, parent_names):
    """
    PMS API currently shares the WMS dev database during transition.

    Until PMS-owned SQLAlchemy models are introduced in this repository,
    Alembic must not compare unrelated WMS tables. Only tables present in
    pms-api target_metadata are included.
    """

    _ = parent_names

    if type_ == "table":
        return name in target_metadata.tables

    return True


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
        version_table=VERSION_TABLE,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
            version_table=VERSION_TABLE,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
