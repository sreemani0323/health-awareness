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


def get_url() -> str:
    """Retrieve connection URL with fail-closed environment validation.
    
    1. Validates APP_ENV: strictly requires explicit 'development' or 'production'.
       Missing, empty, or unexpected values fail closed immediately.
    2. For 'production':
       - Strictly requires MIGRATION_DATABASE_URL (direct, unpooled connection).
       - Never falls back to DATABASE_URL.
       - Disallows pooled connection hosts (e.g. '-pooler.').
    3. For 'development':
       - Strictly uses the explicitly selected local/test DATABASE_URL (or TEST_DATABASE_URL).
       - Never falls back to or permits MIGRATION_DATABASE_URL to override local targets.
       - If no development URL is configured, fails closed immediately.
    4. Never prints credentials, tokens, or full connection strings in logs or exceptions.
    """
    app_env = os.environ.get("APP_ENV", "").strip()

    if not app_env:
        raise ValueError(
            "Configuration error: Unsupported or missing APP_ENV. "
            "Alembic environment must be explicitly configured as 'development' or 'production'."
        )

    if app_env == "production":
        migration_url = os.environ.get("MIGRATION_DATABASE_URL", "").strip()
        if not migration_url:
            raise ValueError(
                "Configuration error: MIGRATION_DATABASE_URL is required for production schema migrations. "
                "Alembic must use a direct, unpooled connection (port 5432) and will not fall back to DATABASE_URL in production."
            )
        if "-pooler." in migration_url:
            raise ValueError(
                "Configuration error: MIGRATION_DATABASE_URL points to a pooled connection host. "
                "Production schema migrations must use a direct, unpooled connection to preserve transaction locks."
            )
        target_url = migration_url

    elif app_env == "development":
        # Strictly prioritize explicit DATABASE_URL, followed by TEST_DATABASE_URL
        dev_url = os.environ.get("DATABASE_URL", "").strip() or os.environ.get("TEST_DATABASE_URL", "").strip()
        if not dev_url and config is not None:
            dev_url = (config.get_main_option("sqlalchemy.url") or "").strip()
        
        if not dev_url:
            raise ValueError(
                "Configuration error: DATABASE_URL is required for development migrations. "
                "MIGRATION_DATABASE_URL cannot be used in development mode."
            )
        
        target_url = dev_url

    else:
        raise ValueError(
            f"Configuration error: Unsupported or missing APP_ENV '{app_env}'. "
            "Alembic environment must be explicitly configured as 'development' or 'production'."
        )

    normalized = normalize_database_url(target_url)
    if not normalized:
        raise ValueError("Configuration error: Resolved database URL is empty or invalid.")

    return normalized



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
