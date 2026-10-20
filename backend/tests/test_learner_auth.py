"""Comprehensive test suite for Hybrid Learner Authentication and Progress Sync.

Validates all 20 security, precedence, and regression requirements:
1. Anonymous learning still works.
2. Valid bearer identity provisions exactly one learner.
3. Client/token role claims cannot create admin/staff privileges.
4. Expired token -> 401.
5. Forged token -> 401.
6. Wrong issuer -> rejected (401).
7. Invalid bearer + valid staff session -> rejected (401); no session fallback.
8. Concurrent first login creates exactly one HealthAware learner.
9. Inactive learner -> forbidden (403).
10. Learner cannot access Creator Studio (403).
11. Learner cannot access staff/case-management endpoints (403).
12. Progress belongs exclusively to authenticated learner.
13. Learner A cannot read/write Learner B's progress.
14. Deterministic progress merge works.
15. Existing contributor/reviewer authentication still works.
16. Existing self-approval prohibition still works.
17. Existing staff jurisdiction restrictions still work.
18. Existing citizen concern privacy behavior remains unchanged.
19. Existing CSRF tests continue passing.
20. Direct Render/proxy-secret protection remains unchanged.
"""

from __future__ import annotations

import concurrent.futures
import time
import uuid
from typing import Any

import jwt
import pytest
from flask import Flask
from sqlalchemy import text

from backend.app import create_app
from backend.domain.domain_objects import UserRole
from backend.platform.security import hash_password
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    get_test_database_url,
    init_db,
)
from backend.storage.postgres_models import (
    Base,
    LearnerProgressModel,
    LessonModel,
    LessonVersionModel,
    StaffJurisdictionModel,
    TopicModel,
    UserModel,
)

TEST_SECRET = "test-jwt-signing-secret-32-chars-long!"
TEST_ALGORITHM = "HS256"
TEST_ISSUER = "https://ep-raspy-moon-a1st7amb.neon.tech/neondb/auth"


def make_test_jwt(
    sub: str | uuid.UUID | None = None,
    name: str = "Test Learner",
    role: str | None = None,
    iss: str = TEST_ISSUER,
    aud: str | None = None,
    exp_offset: int = 3600,
    secret: str = TEST_SECRET,
    alg: str = TEST_ALGORITHM,
) -> str:
    """Generate a signed test JWT for unit testing."""
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": str(sub or uuid.uuid4()),
        "name": name,
        "iss": iss,
        "exp": now + exp_offset,
    }
    if role is not None:
        payload["role"] = role
    if aud is not None:
        payload["aud"] = aud
    return jwt.encode(payload, secret, algorithm=alg)


@pytest.fixture(scope="module")
def pg_engine():
    """Provides an isolated SQLAlchemy engine bound strictly to healthaware_test."""
    test_url = get_test_database_url()
    assert test_url and "postgresql" in test_url, "TEST_DATABASE_URL must be configured with PostgreSQL."
    engine = create_app_engine(test_url)
    assert engine.url.database == "healthaware_test", (
        f"CRITICAL SAFETY VIOLATION: Test database must be 'healthaware_test', got {engine.url.database}"
    )
    init_db(engine)

    import backend.storage.db as db_mod
    original_engine = db_mod._engine
    original_factory = db_mod._SessionFactory
    db_mod._engine = engine
    db_mod._SessionFactory = None

    yield engine

    db_mod._engine = original_engine
    db_mod._SessionFactory = original_factory


@pytest.fixture(autouse=True)
def clean_test_db(pg_engine):
    """Cleans test tables before and after each test."""
    tables = [
        "learner_progress",
        "staff_jurisdictions",
        "concern_status_events",
        "concern_attachments",
        "concern_reports",
        "review_records",
        "lesson_versions",
        "lessons",
        "topics",
        "users",
    ]
    with pg_engine.begin() as conn:
        for t in tables:
            try:
                conn.execute(text(f"DELETE FROM {t}"))
            except Exception:
                pass
    yield
    with pg_engine.begin() as conn:
        for t in tables:
            try:
                conn.execute(text(f"DELETE FROM {t}"))
            except Exception:
                pass


@pytest.fixture()
def app(pg_engine):
    """Create Flask application configured for test JWT verification and testing."""
    test_config = {
        "TESTING": True,
        "DATABASE_URL": get_test_database_url(),
        "TEST_JWT_SECRET": TEST_SECRET,
        "TEST_JWT_ALGORITHM": TEST_ALGORITHM,
        "NEON_AUTH_ISSUER": TEST_ISSUER,
        "SKIP_NDB_CONTEXT": True,
    }
    app = create_app(test_config)
    return app


@pytest.fixture()
def client(app: Flask):
    """Flask test client."""
    with app.test_client() as c:
        yield c


class TestLearnerAuthentication:
    """Tests 1–11: Core authentication precedence, provisioning, and role boundaries."""

    def test_1_anonymous_learning_still_works(self, client):
        """1. Verify public access to topics and health check functions without headers."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

        resp = client.get("/api/v1/topics")
        assert resp.status_code == 200

    def test_2_valid_bearer_identity_provisions_exactly_one_learner(self, client):
        """2. Valid bearer token auto-provisions a new learner in public.users."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id, name="Alice Learner")

        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

        with get_db_session() as session:
            user = session.query(UserModel).filter_by(neon_auth_user_id=neon_id).first()
            assert user is not None
            assert user.role == UserRole.LEARNER.value
            assert user.password_hash is None
            assert user.is_active is True
            assert user.username.startswith("lrn_")
            assert user.display_name == "Alice Learner"

    def test_3_client_token_role_claims_cannot_create_privileged_roles(self, client):
        """3. Token role claims (e.g. role='admin') are completely ignored by provisioning."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id, name="Attacker", role="admin")

        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

        with get_db_session() as session:
            user = session.query(UserModel).filter_by(neon_auth_user_id=neon_id).first()
            assert user is not None
            # Authoritative server store: strictly learner
            assert user.role == UserRole.LEARNER.value

    def test_4_expired_token_returns_401(self, client):
        """4. Expired token fails closed with 401 UNAUTHORIZED."""
        token = make_test_jwt(exp_offset=-100)
        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_5_forged_token_returns_401(self, client):
        """5. Forged token with invalid signature returns 401 UNAUTHORIZED."""
        token = make_test_jwt(secret="wrong-secret-key-that-does-not-match")
        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_6_wrong_issuer_rejected(self, client):
        """6. Token signed by different issuer returns 401 UNAUTHORIZED."""
        token = make_test_jwt(iss="https://malicious-project.neon.tech/neondb/auth")
        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_6b_audience_validation(self, pg_engine):
        """6b. When audience is configured, tokens must match expected audience."""
        aud_app = create_app({
            "TESTING": True,
            "DATABASE_URL": get_test_database_url(),
            "TEST_JWT_SECRET": TEST_SECRET,
            "TEST_JWT_ALGORITHM": TEST_ALGORITHM,
            "NEON_AUTH_ISSUER": TEST_ISSUER,
            "NEON_AUTH_AUDIENCE": "healthaware-prod-api",
            "SKIP_NDB_CONTEXT": True,
        })
        with aud_app.test_client() as aud_client:
            # 1. Matching audience succeeds
            valid_aud_token = make_test_jwt(aud="healthaware-prod-api")
            resp_ok = aud_client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {valid_aud_token}"})
            assert resp_ok.status_code == 200

            # 2. Mismatched audience rejected (401)
            wrong_aud_token = make_test_jwt(aud="other-service-api")
            resp_bad = aud_client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {wrong_aud_token}"})
            assert resp_bad.status_code == 401
            assert resp_bad.get_json()["error"]["code"] == "UNAUTHORIZED"

            # 3. Missing audience rejected when audience required (401)
            no_aud_token = make_test_jwt(aud=None)
            resp_missing = aud_client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {no_aud_token}"})
            assert resp_missing.status_code == 401

    def test_7_invalid_bearer_with_valid_staff_session_fails_closed(self, client):
        """7. Invalid bearer token combined with valid staff session fails closed (401)."""
        staff_id = f"usr_{uuid.uuid4().hex[:16]}"
        with get_db_session() as session:
            staff = UserModel(
                user_id=staff_id,
                username=f"staff_{uuid.uuid4().hex[:8]}",
                display_name="Staff Member",
                role=UserRole.CONTRIBUTOR.value,
                password_hash=hash_password("StaffPass123!"),
                is_active=True,
            )
            session.add(staff)
            session.commit()

        with client.session_transaction() as sess:
            sess["user_id"] = staff_id
            sess["role"] = UserRole.CONTRIBUTOR.value

        bad_token = make_test_jwt(exp_offset=-500)
        resp = client.get(
            "/api/v1/creator/topics",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_8_concurrent_first_login_creates_exactly_one_learner(self, app):
        """8. Concurrent first-login requests for same neon_auth_user_id produce exactly 1 user."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id, name="Concurrent Learner")

        def call_endpoint():
            with app.test_client() as c:
                return c.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_endpoint) for _ in range(5)]
            results = [f.result() for f in futures]

        for r in results:
            assert r.status_code == 200

        with get_db_session() as session:
            count = session.query(UserModel).filter_by(neon_auth_user_id=neon_id).count()
            assert count == 1

    def test_9_inactive_learner_forbidden(self, client):
        """9. Deactivated learner returns 403 FORBIDDEN."""
        neon_id = uuid.uuid4()
        with get_db_session() as session:
            user = UserModel(
                user_id=f"usr_{uuid.uuid4().hex[:16]}",
                username=f"lrn_{neon_id.hex[:16]}",
                display_name="Banned Learner",
                role=UserRole.LEARNER.value,
                neon_auth_user_id=neon_id,
                is_active=False,
            )
            session.add(user)
            session.commit()

        token = make_test_jwt(sub=neon_id)
        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    def test_10_learner_cannot_access_creator_studio(self, client):
        """10. Learner cannot access Creator Studio endpoints (403 FORBIDDEN)."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id)

        resp = client.get("/api/v1/creator/topics", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    def test_11_learner_cannot_access_staff_case_management(self, client):
        """11. Learner cannot access staff case management endpoints (403 FORBIDDEN)."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id)

        resp = client.get("/api/v1/staff/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"


class TestLearnerProgressSync:
    """Tests 12–14: Progress isolation and deterministic merge engine."""

    def test_12_progress_belongs_exclusively_to_authenticated_learner(self, client):
        """12. Progress endpoint reads data strictly by authenticated user_id."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id, name="Bob")

        resp = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["completed_lesson_ids"] == []

    def test_13_learner_a_cannot_read_or_write_learner_b_progress(self, client):
        """13. Learner A cannot read or overwrite Learner B's progress."""
        neon_a = uuid.uuid4()
        neon_b = uuid.uuid4()
        token_a = make_test_jwt(sub=neon_a)
        token_b = make_test_jwt(sub=neon_b)

        client.put(
            "/api/v1/learner/progress",
            json={"completed_lesson_ids": ["lesson-1"]},
            headers={"Authorization": f"Bearer {token_a}"},
        )

        client.put(
            "/api/v1/learner/progress",
            json={"completed_lesson_ids": ["lesson-2"]},
            headers={"Authorization": f"Bearer {token_b}"},
        )

        resp_a = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token_a}"})
        assert resp_a.get_json()["data"]["completed_lesson_ids"] == ["lesson-1"]

        resp_b = client.get("/api/v1/learner/progress", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.get_json()["data"]["completed_lesson_ids"] == ["lesson-2"]

    def test_14_deterministic_progress_merge(self, client):
        """14. Deterministic merge combines lessons, activities, milestones, and newest resume state."""
        neon_id = uuid.uuid4()
        token = make_test_jwt(sub=neon_id)

        client.put(
            "/api/v1/learner/progress",
            json={
                "completed_lesson_ids": ["lesson-1"],
                "completed_activity_ids": ["act-1"],
                "achieved_milestones": [{"id": "m1", "title": "First", "achievedAt": "2026-10-01T10:00:00Z"}],
                "last_lesson": {"lessonId": "lesson-1", "cardIndex": 1, "totalCards": 5, "updatedAt": "2026-10-01T10:00:00Z"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.put(
            "/api/v1/learner/progress",
            json={
                "completed_lesson_ids": ["lesson-2"],
                "completed_activity_ids": ["act-2"],
                "achieved_milestones": [{"id": "m1", "title": "First", "achievedAt": "2026-10-02T12:00:00Z"}, {"id": "m2", "title": "Second"}],
                "last_lesson": {"lessonId": "lesson-2", "cardIndex": 3, "totalCards": 5, "updatedAt": "2026-10-02T12:00:00Z"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        merged = resp.get_json()["data"]

        assert set(merged["completed_lesson_ids"]) == {"lesson-1", "lesson-2"}
        assert set(merged["completed_activity_ids"]) == {"act-1", "act-2"}
        m1 = next(m for m in merged["achieved_milestones"] if m["id"] == "m1")
        assert m1["achievedAt"] == "2026-10-01T10:00:00Z"
        assert any(m["id"] == "m2" for m in merged["achieved_milestones"])
        assert merged["last_lesson"]["lessonId"] == "lesson-2"


class TestExistingStaffAndSecurityRegressions:
    """Tests 15–20: Existing staff, review workflow, jurisdictions, concerns, CSRF, and proxy secret."""

    def test_15_existing_contributor_reviewer_authentication_still_works(self, client):
        """15. Existing staff password login via POST /api/v1/auth/login works unchanged."""
        staff_id = f"usr_{uuid.uuid4().hex[:16]}"
        staff_user = f"contrib_{uuid.uuid4().hex[:8]}"
        with get_db_session() as session:
            user = UserModel(
                user_id=staff_id,
                username=staff_user,
                display_name="Contributor One",
                role=UserRole.CONTRIBUTOR.value,
                password_hash=hash_password("ValidPassword123!"),
                is_active=True,
            )
            session.add(user)
            session.commit()

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": staff_user, "password": "ValidPassword123!"},
        )
        assert login_resp.status_code == 200
        data = login_resp.get_json()["data"]
        assert data["user_id"] == staff_id
        assert data["role"] == UserRole.CONTRIBUTOR.value
        assert "csrf_token" in data

    def test_16_existing_self_approval_prohibition_still_works(self, client):
        """16. Content author cannot approve their own version (enforced in creator.py)."""
        author_id = f"usr_{uuid.uuid4().hex[:16]}"
        with get_db_session() as session:
            user = UserModel(
                user_id=author_id,
                username=f"author_{uuid.uuid4().hex[:8]}",
                display_name="Author Admin",
                role=UserRole.ADMIN.value,
                password_hash=hash_password("Pass123!"),
                is_active=True,
            )
            session.add(user)
            topic = TopicModel(
                topic_id=f"top-{uuid.uuid4().hex[:8]}",
                title="Test Topic",
                url_slug=f"slug-{uuid.uuid4().hex[:8]}",
                description="Desc",
                display_order=1,
                status="published",
            )
            session.add(topic)
            lesson = LessonModel(
                lesson_id=f"les-{uuid.uuid4().hex[:8]}",
                topic_id=topic.topic_id,
                display_order=1,
            )
            session.add(lesson)
            ver = LessonVersionModel(
                version_id=f"ver-{uuid.uuid4().hex[:8]}",
                lesson_id=lesson.lesson_id,
                version_number=1,
                title="Ver 1",
                summary="Summ",
                language="en",
                learning_objectives=["Obj"],
                estimated_duration_minutes=5,
                cards_json=[{"card_id": "c1", "position": 0, "card_type": "explanation", "content_blocks": [{"block_type": "text", "body": "Body"}], "source_ids": []}],
                source_ids=[],
                status="submitted_for_review",
                author_id=author_id,
            )
            session.add(ver)
            session.commit()
            ver_id = ver.version_id

        with client.session_transaction() as sess:
            sess["user_id"] = author_id
            sess["role"] = UserRole.ADMIN.value
            sess["csrf_token"] = "valid-csrf-token"

        resp = client.post(
            f"/api/v1/creator/versions/{ver_id}/approve",
            headers={"X-XSRF-TOKEN": "valid-csrf-token"},
        )
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"
        assert "Self-approval is forbidden" in resp.get_json()["error"]["message"]

    def test_17_existing_staff_jurisdiction_restrictions_still_work(self, client):
        """17. Case management endpoints enforce staff jurisdiction boundaries."""
        officer_id = f"usr_{uuid.uuid4().hex[:16]}"
        with get_db_session() as session:
            officer = UserModel(
                user_id=officer_id,
                username=f"officer_{uuid.uuid4().hex[:8]}",
                display_name="Officer Vizag",
                role=UserRole.JURISDICTION_OFFICER.value,
                password_hash=hash_password("OfficerPass123!"),
                is_active=True,
            )
            session.add(officer)
            jur = StaffJurisdictionModel(
                id=f"jur_{uuid.uuid4().hex[:16]}",
                user_id=officer_id,
                state="Andhra Pradesh",
                district="Visakhapatnam",
            )
            session.add(jur)
            session.commit()

        with client.session_transaction() as sess:
            sess["user_id"] = officer_id
            sess["role"] = UserRole.JURISDICTION_OFFICER.value

        resp = client.get("/api/v1/staff/me")
        assert resp.status_code == 200
        jurs = resp.get_json()["data"]["jurisdictions"]
        assert len(jurs) == 1
        assert jurs[0]["district"] == "Visakhapatnam"

    def test_18_existing_citizen_concern_privacy_unchanged(self, client):
        """18. Concern submission and tracking requires private token; internal notes hidden."""
        sub_resp = client.post(
            "/api/v1/concerns",
            data={
                "category": "garbage",
                "state": "Andhra Pradesh",
                "district": "Visakhapatnam",
                "locality": "4th Cross Road",
                "description": "Garbage pile near market",
                "duration": "< 3 days",
            },
        )
        assert sub_resp.status_code == 201
        body = sub_resp.get_json()
        ref_id = body["data"]["reference_id"]
        token = body["data"]["tracking_token"]

        track_resp = client.post(
            "/api/v1/concerns/track",
            json={"reference_id": ref_id, "tracking_token": token},
        )
        assert track_resp.status_code == 200
        track_data = track_resp.get_json()["data"]
        assert "internal_notes" not in track_data

    def test_19_existing_csrf_tests_continue_passing(self, pg_engine):
        """19. Cookie-authenticated mutating requests require valid X-XSRF-TOKEN header."""
        user_id = f"usr_{uuid.uuid4().hex[:16]}"
        with get_db_session() as session:
            user = UserModel(
                user_id=user_id,
                username=f"admin_{uuid.uuid4().hex[:8]}",
                display_name="Admin",
                role=UserRole.ADMIN.value,
                password_hash="fake",
                is_active=True,
            )
            session.add(user)
            session.commit()

        csrf_app = create_app({
            "TESTING": True,
            "CSRF_ENABLED": True,
            "DATABASE_URL": get_test_database_url(),
            "SKIP_NDB_CONTEXT": True,
        })
        with csrf_app.test_client() as csrf_client:
            with csrf_client.session_transaction() as sess:
                sess["user_id"] = user_id
                sess["role"] = UserRole.ADMIN.value
                sess["csrf_token"] = "super-secret-csrf"

            resp = csrf_client.post(
                "/api/v1/creator/topics",
                json={
                    "id": f"topic-csrf-{uuid.uuid4().hex[:6]}",
                    "title": "CSRF Topic",
                    "slug": f"csrf-{uuid.uuid4().hex[:6]}",
                    "description": "CSRF test",
                },
            )
            assert resp.status_code == 403
            assert resp.get_json()["error"]["code"] == "CSRF_ERROR"

    def test_20_direct_render_proxy_secret_protection_unchanged(self):
        """20. In production environment, direct requests without PROXY_SECRET return 403."""
        import os
        orig_env = os.environ.get("APP_ENV")
        orig_secret = os.environ.get("PROXY_SECRET")
        try:
            os.environ["APP_ENV"] = "production"
            os.environ["PROXY_SECRET"] = "valid-production-proxy-secret-12345"
            prod_app = create_app({
                "TESTING": False,
                "FLASK_SECRET_KEY": "a" * 32,
                "DATABASE_URL": get_test_database_url(),
                "SKIP_NDB_CONTEXT": True,
            })
            with prod_app.test_client() as prod_client:
                resp = prod_client.get("/api/v1/health")
                assert resp.status_code == 200

                resp2 = prod_client.get("/api/v1/topics")
                assert resp2.status_code == 403
                assert resp2.get_json()["error"]["code"] == "DIRECT_ACCESS_FORBIDDEN"

                resp3 = prod_client.get(
                    "/api/v1/topics",
                    headers={"X-HealthAware-Proxy-Secret": "valid-production-proxy-secret-12345"},
                )
                assert resp3.status_code == 200
        finally:
            if orig_env is not None:
                os.environ["APP_ENV"] = orig_env
            else:
                os.environ.pop("APP_ENV", None)
            if orig_secret is not None:
                os.environ["PROXY_SECRET"] = orig_secret
            else:
                os.environ.pop("PROXY_SECRET", None)
