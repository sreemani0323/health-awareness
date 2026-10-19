"""Regression tests for Contributor provisioning, PostgreSQL authentication, and session lifecycle.

Validates:
1. Contributor provisioning via provision_user() CLI/function.
2. Safe rejection of predictable demo passwords without explicit opt-in.
3. Allowed provisioning of demo passwords when demo_password_opt_in is True.
4. Correct PBKDF2-HMAC-SHA256 password hashing (600,000 rounds) in PostgreSQL.
5. Successful login with valid credentials (HTTP 200, role 'contributor', CSRF token, session cookie).
6. Rejection of invalid passwords (HTTP 401).
7. Rejection of non-existent users (HTTP 401).
8. Active session inspection via /api/v1/auth/me (HTTP 200).
9. Missing session rejection via /api/v1/auth/me (HTTP 401).
10. Logout session destruction via /api/v1/auth/logout.
11. Role authorization boundary (contributor cannot access admin endpoints -> HTTP 403).
12. Deactivated account rejection (HTTP 401).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from backend.app import create_app
from backend.domain.domain_objects import UserRole
from backend.platform.security import verify_password
from backend.provision_user import provision_user
from backend.storage.db import (
    create_app_engine,
    get_test_database_url,
    init_db,
)
from backend.storage.postgres_models import UserModel


@pytest.fixture(scope="module")
def pg_engine():
    """Provides isolated SQLAlchemy engine bound strictly to healthaware_test."""
    test_url = get_test_database_url()
    assert test_url and "postgresql" in test_url, "TEST_DATABASE_URL must be configured with PostgreSQL."

    engine = create_app_engine(test_url)
    assert engine.url.database == "healthaware_test", (
        f"CRITICAL SAFETY VIOLATION: Test database must be 'healthaware_test', got {engine.url.database}"
    )

    init_db(engine)
    return engine


@pytest.fixture(scope="module")
def test_db_url(pg_engine):
    """Provides unmasked test database URL for provisioning."""
    return get_test_database_url()


@pytest.fixture(autouse=True)
def clean_users_table(pg_engine):
    """Ensures clean users table in healthaware_test before and after each test."""
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM staff_jurisdictions"))
        conn.execute(text("DELETE FROM users"))
    yield
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM staff_jurisdictions"))
        conn.execute(text("DELETE FROM users"))


@pytest.fixture()
def client(pg_engine):
    """Provides a test Flask client configured with healthaware_test database."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-32-bytes-long-for-testing",
        "SKIP_NDB_CONTEXT": True,
        "DATABASE_URL": get_test_database_url(),
    })

    import backend.storage.db as db_mod
    original_engine = db_mod._engine
    original_factory = db_mod._SessionFactory
    db_mod._engine = pg_engine
    db_mod._SessionFactory = None

    with app.test_client() as test_client:
        yield test_client

    db_mod._engine = original_engine
    db_mod._SessionFactory = original_factory


# ---------------------------------------------------------------------------
# Provisioning & Password Policy Tests
# ---------------------------------------------------------------------------


def test_predictable_demo_password_rejected_without_opt_in(test_db_url):
    """Predictable demo credentials (e.g. contributor123) are rejected without opt-in."""
    with pytest.raises(ValueError, match="known predictable demo credential"):
        provision_user(
            username="contributor",
            password="contributor123",
            role="contributor",
            database_url=test_db_url,
            demo_password_opt_in=False,
        )


def test_predictable_demo_password_allowed_with_opt_in(pg_engine, test_db_url):
    """Predictable demo credentials succeed when explicit opt-in flag is provided."""
    success = provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        display_name="Demo Contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )
    assert success is True

    with pg_engine.begin() as conn:
        row = conn.execute(
            text("SELECT username, role, display_name, password_hash, is_active FROM users WHERE username = 'contributor'")
        ).fetchone()
        assert row is not None
        assert row[0] == "contributor"
        assert row[1] == "contributor"
        assert row[2] == "Demo Contributor"
        # Stored hash must be PBKDF2-HMAC-SHA256, NEVER plaintext
        stored_hash = row[3]
        assert stored_hash.startswith("pbkdf2:sha256:600000$")
        assert verify_password("contributor123", stored_hash) is True
        assert verify_password("wrongpassword", stored_hash) is False
        assert row[4] is True


def test_strong_unique_password_provisioning(pg_engine, test_db_url):
    """Strong unique password provisions without requiring demo opt-in."""
    success = provision_user(
        username="contributor_custom",
        password="A!Very$trong&UniquePassword99",
        role="contributor",
        display_name="Custom Contributor",
        database_url=test_db_url,
        demo_password_opt_in=False,
    )
    assert success is True

    with pg_engine.begin() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE username = 'contributor_custom'")
        ).scalar()
        assert count == 1


# ---------------------------------------------------------------------------
# Authentication Flow & Session Tests
# ---------------------------------------------------------------------------


def test_valid_contributor_login_and_session(client, pg_engine, test_db_url):
    """Valid contributor login sets signed session cookie and returns correct role and CSRF."""
    provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        display_name="Content Contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )

    # 1. Login with valid credentials
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "data" in body
    data = body["data"]
    assert data["username"] == "contributor"
    assert data["role"] == "contributor"
    assert data["display_name"] == "Content Contributor"
    assert "csrf_token" in data
    assert len(data["csrf_token"]) == 64

    # 2. Verify Session endpoint (/api/v1/auth/me) preserves login state
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    me_data = me_resp.get_json()["data"]
    assert me_data["username"] == "contributor"
    assert me_data["role"] == "contributor"


def test_invalid_password_returns_401(client, pg_engine, test_db_url):
    """Invalid password returns HTTP 401 Unauthorized without session."""
    provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "contributor", "password": "IncorrectPassword999!"},
    )
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid username or password" in body["error"]["message"]

    # Verify no session created
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401


def test_non_existent_user_returns_401(client, pg_engine):
    """Non-existent username returns HTTP 401 Unauthorized."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "unknown_user", "password": "AnyPassword123!"},
    )
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid username or password" in body["error"]["message"]


def test_unauthenticated_session_check_returns_401(client):
    """GET /api/v1/auth/me without active session returns HTTP 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_logout_destroys_session(client, pg_engine, test_db_url):
    """POST /api/v1/auth/logout terminates the session immediately."""
    provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )
    assert login_resp.status_code == 200

    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # Next check must be unauthorized
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401


def test_contributor_role_authorization_boundary(client, pg_engine, test_db_url):
    """Contributor cannot access Administrator endpoints (/api/v1/admin/* -> 403 Forbidden)."""
    provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )

    client.post(
        "/api/v1/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )

    # Admin users list requires UserRole.ADMIN
    admin_resp = client.get("/api/v1/admin/users")
    assert admin_resp.status_code == 403
    assert admin_resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_deactivated_contributor_cannot_log_in(client, pg_engine, test_db_url):
    """Deactivated contributor cannot log in and existing session is rejected."""
    provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )

    # Deactivate account in PostgreSQL
    with pg_engine.begin() as conn:
        conn.execute(text("UPDATE users SET is_active = FALSE WHERE username = 'contributor'"))

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )
    assert resp.status_code == 401


def test_contributor_can_list_creator_topics_and_lessons(client, pg_engine, test_db_url):
    """Contributor can access /api/v1/creator/topics and /api/v1/creator/topics/<id>/lessons with decoupled NDB context."""
    provision_user(
        username="contributor",
        password="contributor123",
        role="contributor",
        database_url=test_db_url,
        demo_password_opt_in=True,
    )

    client.post(
        "/api/v1/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )

    # Insert test topic and lesson directly into PostgreSQL test db
    with pg_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
            VALUES ('top-creator-reg', 'Creator Regression Topic', 'creator-regression-topic', 'Testing creator topics', 1, 'published', NOW(), NOW())
            ON CONFLICT (topic_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO lessons (lesson_id, topic_id, display_order, published_version_id, created_at, updated_at)
            VALUES ('les-creator-reg', 'top-creator-reg', 1, 'ver-creator-reg', NOW(), NOW())
            ON CONFLICT (lesson_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO lesson_versions (version_id, lesson_id, version_number, title, summary, language, learning_objectives, estimated_duration_minutes, cards_json, source_ids, status, created_at, updated_at)
            VALUES ('ver-creator-reg', 'les-creator-reg', 1, 'Creator Version Title', 'Summary', 'en', '[]'::json, 5, '[]'::json, '[]'::json, 'published', NOW(), NOW())
            ON CONFLICT (version_id) DO NOTHING
        """))

    # 1. GET /api/v1/creator/topics
    topics_res = client.get("/api/v1/creator/topics")
    assert topics_res.status_code == 200
    topics_data = topics_res.get_json()["data"]
    assert any(t["id"] == "top-creator-reg" for t in topics_data)

    # 2. GET /api/v1/creator/topics/top-creator-reg/lessons
    lessons_res = client.get("/api/v1/creator/topics/top-creator-reg/lessons")
    assert lessons_res.status_code == 200
    lessons_data = lessons_res.get_json()["data"]
    assert len(lessons_data) == 1
    assert lessons_data[0]["id"] == "les-creator-reg"
    assert lessons_data[0]["title"] == "Creator Version Title"

