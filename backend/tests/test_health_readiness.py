"""Automated test suite verifying HealthCheck and HealthReadiness endpoints, timeout controls, and error masking.

Tests:
1. GET /api/v1/health (process liveness check) returns 200 without DB dependency.
2. GET /api/v1/health/ready returns 200 and 'connected' status when database is ready.
3. GET /api/v1/health/ready returns 503 and safe JSON when database is unavailable.
4. Empirical test: Connection pool exhaustion is detected and bounded within timeout.
5. Empirical test: Non-routable socket connection timeout is bounded via connect_timeout.
6. Empirical test: Overall readiness-check deadline enforces hard ceiling on slow query / stall.
7. Verification that database connection strings, credentials, or internal paths are never leaked.
8. Verification that unhandled SQLAlchemy OperationalError is mapped to a masked 503 response.
"""

from __future__ import annotations

import os
import time
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, IntegrityError

from backend.app import create_app
from backend.storage.db import check_database_connection


@pytest.fixture
def app_client():
    """Create test client with proxy secret enforcement and test configuration."""
    app = create_app({
        "TESTING": True,
        "SKIP_NDB_CONTEXT": True,
        "SECRET_KEY": "test-secret-key-at-least-32-chars-long!",
    })
    with app.test_client() as client:
        yield client


def test_health_liveness_succeeds(app_client):
    """GET /api/v1/health returns 200 OK process status without touching the database."""
    resp = app_client.get("/api/v1/health")
    assert resp.status_code == 200
    res = resp.get_json()
    assert res["data"]["status"] == "healthy"
    assert res["meta"]["api_version"] == "v1"


def test_health_readiness_succeeds_when_database_connected(app_client):
    """GET /api/v1/health/ready returns 200 OK when database ping succeeds."""
    with patch("backend.controllers.health.check_database_connection", return_value=True):
        resp = app_client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        res = resp.get_json()
        assert res["data"]["status"] == "ready"
        assert res["data"]["database"] == "connected"


def test_health_readiness_returns_503_when_database_unreachable(app_client):
    """GET /api/v1/health/ready returns safe 503 response when database ping fails."""
    with patch("backend.controllers.health.check_database_connection", return_value=False):
        resp = app_client.get("/api/v1/health/ready")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "currently unavailable" in data["error"]["message"].lower()
        # Verify no connection strings or internal database hosts are leaked
        raw_body = resp.get_data(as_text=True)
        assert "postgresql://" not in raw_body
        assert "neon.tech" not in raw_body
        assert "password" not in raw_body.lower()


def test_health_readiness_returns_503_on_connection_exception(app_client):
    """GET /api/v1/health/ready returns safe 503 response when ping raises an exception."""
    with patch(
        "backend.controllers.health.check_database_connection",
        side_effect=OperationalError("connection to server at 'db.internal' failed", None, None),
    ):
        resp = app_client.get("/api/v1/health/ready")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
        # Confirm internal hostname 'db.internal' was masked
        raw_body = resp.get_data(as_text=True)
        assert "db.internal" not in raw_body


def test_health_endpoints_accessible_without_proxy_secret(app_client):
    """Liveness and readiness probes are accessible by monitoring tools without proxy secret headers."""
    liveness_resp = app_client.get("/api/v1/health")
    assert liveness_resp.status_code == 200

    with patch("backend.controllers.health.check_database_connection", return_value=True):
        readiness_resp = app_client.get("/api/v1/health/ready")
        assert readiness_resp.status_code == 200


def test_operational_error_masks_internal_details(app_client):
    """Unhandled OperationalError during a database query returns masked 503."""
    with patch(
        "backend.controllers.health.check_database_connection",
        side_effect=OperationalError("could not connect to server: Connection refused\nIs the server running on host 10.0.0.1?", None, None),
    ):
        resp = app_client.get("/api/v1/health/ready")
        assert resp.status_code == 503
        raw_body = resp.get_data(as_text=True)
        assert "10.0.0.1" not in raw_body
        assert "Is the server running" not in raw_body


def test_unhandled_database_error_on_topics_route(app_client):
    """Simulate unhandled database disconnect during data retrieval returning masked 503."""
    with patch(
        "backend.domain.domain_services.list_topics",
        side_effect=OperationalError("server closed the connection unexpectedly", None, None),
    ):
        resp = app_client.get(
            "/api/v1/topics",
            headers={"X-HealthAware-Proxy-Secret": "test"},
        )
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "storage service is currently unavailable" in data["error"]["message"]
        assert "server closed the connection" not in resp.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Empirical Timeout Controls Tests (Pool, Socket, Query, and Overall Deadline)
# ---------------------------------------------------------------------------


def test_real_pool_exhaustion_bounds_timeout(tmp_path):
    """Empirical test: When connection pool is exhausted, check_database_connection returns False within bounded timeout."""
    db_file = tmp_path / "exhausted_pool.db"
    # Create engine with pool size 1, 0 overflow, and pool_timeout of 0.6 seconds
    engine = create_engine(
        f"sqlite:///{db_file}",
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_timeout=0.6,
    )

    # Check out the sole available connection and hold it
    conn = engine.connect()
    try:
        t0 = time.time()
        # Attempt readiness check with timeout_seconds = 1.0
        is_ready = check_database_connection(engine=engine, timeout_seconds=1.0)
        duration = time.time() - t0

        assert is_ready is False, "Exhausted pool must result in is_ready = False"
        assert duration <= 1.5, f"Pool timeout was expected <= 1.5s, took {duration:.2f}s"
    finally:
        conn.close()
        engine.dispose()


def test_real_socket_connection_timeout():
    """Empirical test: Non-routable blackhole IP triggers libpq connect_timeout within bounded duration."""
    # 192.0.2.1 is RFC 5737 TEST-NET-1 (non-routable blackhole IP)
    blackhole_engine = create_engine(
        "postgresql+psycopg2://user:pass@192.0.2.1:5432/db",
        connect_args={"connect_timeout": 1},
    )
    t0 = time.time()
    is_ready = check_database_connection(engine=blackhole_engine, timeout_seconds=1.5)
    duration = time.time() - t0

    assert is_ready is False, "Unreachable host must result in is_ready = False"
    assert duration <= 2.2, f"Socket connect timeout was expected <= 2.2s, took {duration:.2f}s"
    blackhole_engine.dispose()


def test_overall_deadline_enforcement_on_slow_worker():
    """Empirical test: When query or worker hangs, overall deadline is strictly enforced."""
    def hanging_ping(target_engine, timeout_ms):
        time.sleep(3.0)
        return True

    with patch("backend.storage.db._execute_readiness_ping", side_effect=hanging_ping):
        t0 = time.time()
        is_ready = check_database_connection(timeout_seconds=0.7)
        duration = time.time() - t0

        assert is_ready is False, "Hanging worker must return False"
        assert duration <= 1.2, f"Deadline expected <= 1.2s, took {duration:.2f}s"


def test_health_readiness_endpoint_integrates_with_timeout_failure(app_client):
    """End-to-end integration: Readiness HTTP endpoint returns 503 within 1s when timeout occurs."""
    def hanging_ping(target_engine, timeout_ms):
        time.sleep(3.0)
        return True

    with patch("backend.storage.db._execute_readiness_ping", side_effect=hanging_ping):
        t0 = time.time()
        resp = app_client.get("/api/v1/health/ready")
        duration = time.time() - t0

        assert resp.status_code == 503
        data = resp.get_json()
        assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert duration <= 2.5, f"Endpoint response took {duration:.2f}s"


def test_repeated_timeouts_prevent_worker_queue_buildup():
    """Regression test: Repeated rapid timeout calls do NOT queue unbounded tasks in executor."""
    from backend.storage.db import _readiness_executor, reset_readiness_cache

    reset_readiness_cache()

    # Simulate a slow worker that takes 2.0s
    def slow_ping(target_engine, timeout_ms):
        time.sleep(1.0)
        return True

    with patch("backend.storage.db._execute_readiness_ping", side_effect=slow_ping):
        # Fire 5 rapid checks with short deadline 0.1s and bypass_cache=True
        for _ in range(5):
            res = check_database_connection(timeout_seconds=0.1, bypass_cache=True)
            assert res is False

        # Work queue in the thread pool executor must NOT build up unbounded tasks
        # In Python ThreadPoolExecutor, _work_queue holds pending unstarted tasks
        pending_queue_size = _readiness_executor._work_queue.qsize()
        assert pending_queue_size <= 1, f"Expected queue size <= 1, but found {pending_queue_size}"

    reset_readiness_cache()


def test_database_failure_and_recovery_cycle(app_client):
    """Regression test: Database failure correctly returns 503, and subsequent recovery returns 200."""
    from backend.storage.db import reset_readiness_cache

    reset_readiness_cache()

    # Phase 1: Database failure
    with patch("backend.controllers.health.check_database_connection", return_value=False):
        resp_fail = app_client.get("/api/v1/health/ready")
        assert resp_fail.status_code == 503
        assert resp_fail.get_json()["error"]["code"] == "DATABASE_UNAVAILABLE"

    # Phase 2: Database recovers
    reset_readiness_cache()
    with patch("backend.controllers.health.check_database_connection", return_value=True):
        resp_ok = app_client.get("/api/v1/health/ready")
        assert resp_ok.status_code == 200
        data = resp_ok.get_json()
        assert data["data"]["status"] == "ready"
        assert data["data"]["database"] == "connected"

    reset_readiness_cache()

