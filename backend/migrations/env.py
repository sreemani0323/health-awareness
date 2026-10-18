"""Alembic environment configuration for HealthAware PostgreSQL migrations."""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure backend package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.storage.db import get_database_url, normalize_database_url
from backend.storage.postgres_models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
try:
    config = context.config
except AttributeError:
    config = None

# Interpret the config file for Python logging if running under Alembic CLI
if config is not None and config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """Retrieve connection URL with fail-closed environment validation.
    
    1. Validates APP_ENV: accepts only 'development' or 'production'.
    2. For 'production': strictly requires MIGRATION_DATABASE_URL and never falls back to DATABASE_URL.
    3. For 'development': prioritizes MIGRATION_DATABASE_URL, permits fallback to DATABASE_URL.
    4. For missing or unsupported APP_ENV: raises ValueError configuration error immediately.
    """
    app_env = os.environ.get("APP_ENV", "").strip()

    if app_env == "production":
        migration_url = os.environ.get("MIGRATION_DATABASE_URL", "").strip()
        if not migration_url:
            raise ValueError(
                "Configuration error: MIGRATION_DATABASE_URL is required for production schema migrations. "
                "Alembic must use a direct, unpooled connection (port 5432) and will not fall back to DATABASE_URL in production."
            )
        target_url = migration_url
    elif app_env == "development":
        target_url = os.environ.get("MIGRATION_DATABASE_URL", "").strip() or get_database_url()
        if not target_url and config is not None:
            target_url = config.get_main_option("sqlalchemy.url")
        if not target_url:
            raise ValueError("Configuration error: Neither MIGRATION_DATABASE_URL nor DATABASE_URL is configured for development.")
    else:
        raise ValueError(
            f"Configuration error: Unsupported or missing APP_ENV '{app_env}'. "
            "Alembic environment must be explicitly configured as 'development' or 'production'."
        )

    return normalize_database_url(target_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()
    if not url:
        raise ValueError(
            "Cannot run migrations online: Database connection URL is not resolved."
        )

    configuration = config.get_section(config.config_ini_section) if config is not None else {}
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if config is not None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
