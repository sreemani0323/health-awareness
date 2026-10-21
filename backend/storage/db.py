"""Database engine, connection pooling, and session management for PostgreSQL.

Designed for Python 3.12, local PostgreSQL, and hosted Neon PostgreSQL.
Provides pool-pre-ping, SSL configuration, and request/service-scoped session lifecycle.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.storage.postgres_models import Base

# Load .env if present
load_dotenv()

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker[Session]] = None


def normalize_database_url(raw_url: str) -> str:
    """Normalizes database URLs for SQLAlchemy 2 compatibility.
    
    Converts legacy 'postgres://' or driverless 'postgresql://' scheme to 'postgresql+psycopg2://'.
    Encodes special characters in user credentials if necessary.
    Preserves query parameters such as sslmode=require for Neon.
    """
    if not raw_url:
        return ""
    
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    
    # Defensive handling if password contains unencoded '@'
    if (url.startswith("postgresql://") or url.startswith("postgresql+psycopg2://")) and url.count("@") > 1:
        scheme, rest = url.split("://", 1)
        prefix, host_part = rest.rsplit("@", 1)
        parts = prefix.split(":", 1)
        if len(parts) == 2:
            user, pwd = parts
            from urllib.parse import quote_plus, unquote
            url = f"{scheme}://{user}:{quote_plus(unquote(pwd))}@{host_part}"
    
    return url


def get_database_url() -> str:
    """Resolves the configured primary DATABASE_URL from environment."""
    raw = os.environ.get("DATABASE_URL", "").strip()
    return normalize_database_url(raw)


def get_test_database_url() -> str:
    """Resolves the configured TEST_DATABASE_URL from environment."""
    raw = os.environ.get("TEST_DATABASE_URL", "").strip()
    return normalize_database_url(raw)


def create_app_engine(database_url: Optional[str] = None) -> Engine:
    """Creates a SQLAlchemy Engine with connection health checks and Neon compatibility."""
    target_url = normalize_database_url(database_url or get_database_url())
    if not target_url:
        raise ValueError(
            "DATABASE_URL is not set. Please configure DATABASE_URL in your environment or .env file."
        )

    engine_kwargs: dict[str, any] = {
        "future": True,
        "echo": False,
    }

    # PostgreSQL specific engine configurations (connection pooling & ping)
    if target_url.startswith("postgresql"):
        engine_kwargs.update({
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 300,  # recycle connections after 5 minutes (Neon idle timeout)
        })
    elif target_url.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool
        if ":memory:" in target_url:
            engine_kwargs.update({
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            })
        else:
            engine_kwargs.update({
                "connect_args": {"check_same_thread": False},
            })

    return create_engine(target_url, **engine_kwargs)


def get_engine() -> Engine:
    """Returns the process-wide SQLAlchemy engine, initializing if necessary."""
    global _engine
    if _engine is None:
        _engine = create_app_engine()
    return _engine


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker[Session]:
    """Returns a sessionmaker factory bound to the provided or default engine."""
    global _SessionFactory
    if engine is not None:
        return sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    if _SessionFactory is None:
        eng = get_engine()
        _SessionFactory = sessionmaker(
            bind=eng,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SessionFactory


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit and rollback."""
    factory = get_session_factory(engine)
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine: Optional[Engine] = None) -> None:
    """Creates all registered PostgreSQL tables if they do not exist."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    try:
        with eng.begin() as conn:
            if eng.dialect.name == "postgresql":
                conn.execute(text(
                    "ALTER TABLE staff_mfa_credentials ADD COLUMN IF NOT EXISTS session_revoked_at TIMESTAMP WITH TIME ZONE;"
                ))
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;"
                ))
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS setup_token_hash VARCHAR(64);"
                ))
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS setup_token_expires_at TIMESTAMP WITH TIME ZONE;"
                ))
                conn.execute(text(
                    "ALTER TABLE staff_applications ADD COLUMN IF NOT EXISTS tracking_token_expires_at TIMESTAMP WITH TIME ZONE;"
                ))
    except Exception as exc:
        logger.warning("Error running idempotent column migrations in init_db: %s", exc)


def check_database_connection(engine: Optional[Engine] = None) -> bool:
    """Verifies that the target database can be reached and is responding."""
    try:
        eng = engine or get_engine()
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)
        return False
