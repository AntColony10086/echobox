"""Alembic environment: reads DB URL from ECHOBOX_APP_DB_URL env var."""

import os
from logging.config import fileConfig

from alembic import context
from echobox_app.db.models import Base
from sqlalchemy import engine_from_config, pool

config = context.config
_db_url: str | None = os.environ.get("ECHOBOX_APP_DB_URL", config.get_main_option("sqlalchemy.url"))
db_url: str = _db_url or "sqlite:///.data/echobox.db"
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite-friendly ALTER
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
