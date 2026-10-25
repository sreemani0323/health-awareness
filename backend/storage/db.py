"""Database engine, connection pooling, and session management for PostgreSQL.

Designed for Python 3.12, local PostgreSQL, and hosted Neon PostgreSQL.
Provides pool-pre-ping, SSL configuration, and request/service-scoped session lifecycle.
"""

from __future__ import annotations

import logging
import os
import concurrent.futures
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
        connect_args: dict[str, Any] = {
            "connect_timeout": 3,  # Libpq socket connect timeout to prevent TCP hang (replaces 60-120s OS default)
        }
        # Neon PgBouncer pooler rejects startup options packet; only supply statement_timeout on direct connections
        if "-pooler" not in target_url:
            connect_args["options"] = "-c statement_timeout=15000"

        engine_kwargs.update({
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 300,  # recycle connections after 5 minutes (Neon idle timeout)
            "pool_timeout": 3.0,  # Bound pool checkout wait ceiling (replaces 30s default)
            "connect_args": connect_args,
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
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS neon_auth_user_id UUID;"
                ))
                conn.execute(text(
                    "ALTER TABLE staff_applications ADD COLUMN IF NOT EXISTS tracking_token_expires_at TIMESTAMP WITH TIME ZONE;"
                ))
                conn.execute(text(
                    "DROP TABLE IF EXISTS sms_otp_challenges CASCADE;"
                ))
    except Exception as exc:
        logger.warning("Error running idempotent column migrations in init_db: %s", exc)


import threading
import time

_readiness_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="db_readiness_probe",
)
_readiness_lock = threading.Lock()
_active_future: Optional[concurrent.futures.Future] = None
_last_check_time: float = 0.0
_last_check_result: bool = False
_CACHE_TTL_SECONDS = 2.0


def reset_readiness_cache() -> None:
    """Invalidates readiness cache; used by tests and operational recovery resets."""
    global _last_check_time, _last_check_result, _active_future
    with _readiness_lock:
        _last_check_time = 0.0
        _last_check_result = False
        _active_future = None


def _execute_readiness_ping(target_engine: Engine, timeout_ms: int) -> bool:
    """Worker task that checks out connection, applies statement_timeout, and runs SELECT 1."""
    with target_engine.connect() as conn:
        if target_engine.dialect.name == "postgresql":
            # Enforce PostgreSQL server-side statement timeout for this specific probe
            conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        result = conn.execute(text("SELECT 1"))
        return result.scalar() == 1


def check_database_connection(
    engine: Optional[Engine] = None,
    timeout_seconds: float = 2.0,
    bypass_cache: bool = False,
) -> bool:
    """Verifies that the target database can be reached and is responding within bounded timeout.

    Resource Safety & Thread Concurrency Controls:
    1. Singleflight execution: At most 1 worker probe is executed concurrently.
       Under repeated rapid checks (e.g. 100 req/s from monitors), non-blocking lock
       prevents unbounded worker queueing and thread pileup.
    2. Active future tracking: In Python, raising TimeoutError from Future.result(timeout=...)
       does NOT terminate the background worker thread. To guarantee bounded concurrency and
       prevent executor work-queue buildup, subsequent calls check `_active_future`. If a worker
       is still running/lingering on a socket or pool wait, we do NOT submit a new task.
       Instead, we immediately record and return False.
    3. Thread lifecycle termination bounds: The background worker thread is guaranteed to terminate
       on its own because of driver-level timeouts:
       - Connection-pool checkout wait is bounded via QueuePool pool_timeout (3s).
       - PostgreSQL TCP socket connection establishment is bounded via libpq connect_timeout (3s).
       - SQL statement execution is bounded via PostgreSQL statement_timeout (SET LOCAL).
    4. Short TTL caching (2.0s): Avoids connection thrashing while preserving rapid failure/recovery detection.
    5. Overall execution deadline bounded via ThreadPoolExecutor future with timeout_seconds.
    """
    global _last_check_time, _last_check_result, _active_future
    now = time.time()

    # 1. Return fresh cached status if checked within CACHE_TTL_SECONDS
    if not bypass_cache and engine is None and (now - _last_check_time) < _CACHE_TTL_SECONDS and _last_check_time > 0:
        return _last_check_result

    # 2. Acquire lock non-blockingly to avoid thread queue accumulation
    acquired = _readiness_lock.acquire(blocking=False)
    if not acquired:
        # A probe is already actively running. Rather than queuing another thread,
        # return the last known result or False to avoid thread exhaustion
        logger.debug("Readiness probe already in flight, returning last cached status")
        return _last_check_result

    try:
        now = time.time()
        if not bypass_cache and engine is None and (now - _last_check_time) < _CACHE_TTL_SECONDS and _last_check_time > 0:
            return _last_check_result

        # Check if an existing probe future is still active/lingering
        if _active_future is not None and not _active_future.done():
            logger.warning(
                "Previous readiness probe worker is still busy in background; returning failure without queuing additional worker"
            )
            if engine is None:
                _last_check_result = False
                _last_check_time = time.time()
            return False

        eng = engine or get_engine()
        timeout_ms = max(int(timeout_seconds * 1000), 100)
        future = _readiness_executor.submit(_execute_readiness_ping, eng, timeout_ms)
        if engine is None:
            _active_future = future

        res = bool(future.result(timeout=timeout_seconds))

        if engine is None:
            _last_check_result = res
            _last_check_time = time.time()
        return res
    except concurrent.futures.TimeoutError:
        logger.warning(
            "Database readiness check exceeded overall deadline of %.2fs (pool or socket stalled)",
            timeout_seconds,
        )
        if engine is None:
            _last_check_result = False
            _last_check_time = time.time()
        return False
    except Exception as exc:
        logger.warning("Database connection check failed [%s]: %s", type(exc).__name__, exc)
        if engine is None:
            _last_check_result = False
            _last_check_time = time.time()
        return False
    finally:
        _readiness_lock.release()



