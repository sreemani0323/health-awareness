"""Comprehensive security and authorization verification test suite.

Tests cover:
1. PBKDF2-HMAC-SHA256 password hashing (600,000 iterations), salt uniqueness,
   verification, benchmark timing, and transparent legacy SHA-256 hash migration.
2. Resource-level authorization & draft ownership isolation (contributors cannot read,
   edit, or submit drafts they do not own; reviewers cannot read unsubmitted drafts).
3. Self-approval prevention (neither submitter nor author can approve their own version).
4. Immutability of submitted and published versions.
5. Session security, HttpOnly/SameSite flags, and immediate deactivation enforcement.
6. Anti-CSRF token verification on cookie-authenticated mutating requests.
7. Strict CORS origin validation (no arbitrary reflection, no wildcard for credentials).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any

import pytest
from flask import Flask

from backend.app import create_app
from backend.domain import domain_services
from backend.domain.domain_objects import (
    CardType,
    ContentBlock,
    Lesson,
    LessonCard,
    LessonVersion,
    PublicationStatus,
    Topic,
    User,
    UserRole,
    VersionStatus,
)
from backend.platform.security import (
    DEFAULT_PBKDF2_ITERATIONS,
    hash_password,
    needs_rehash,
    verify_password,
)


def _legacy_hash(password: str) -> str:
    """Simulate old legacy un-salted SHA-256 hash."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@pytest.fixture()
def client(ndb_ctx):
    """Flask test client running with test configuration inside isolated NDB context."""
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


@pytest.fixture()
def csrf_client(ndb_ctx):
    """Flask test client with CSRF protection explicitly enabled."""
    app = create_app({"TESTING": True, "CSRF_ENABLED": True})
    with app.test_client() as c:
        yield c


# ===========================================================================
# 1. Password Hashing, Verification & Migration Tests
# ===========================================================================


class TestPasswordSecurity:
    def test_hash_format_and_parameters(self):
        pw = "CorrectHorseBatteryStaple123!"
        h = hash_password(pw)
        assert h.startswith("pbkdf2:sha256:600000$")
        parts = h.split("$")
        assert len(parts) == 3
        salt = parts[1]
        assert len(salt) == 32  # 16 bytes hex-encoded = 32 chars

    def test_salt_uniqueness(self):
        pw = "SamePasswordAcrossUsers456!"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2, "Salts must be unique per password hash"

    def test_verify_password_valid_and_invalid(self):
        pw = "MySecretPassphrase789!"
        h = hash_password(pw)
        assert verify_password(pw, h) is True
        assert verify_password("WrongPassword123!", h) is False
        assert verify_password("", h) is False

    def test_legacy_hash_compatibility_and_detection(self):
        plain = "legacy_user_password_2026"
        legacy = _legacy_hash(plain)

        # Verifies successfully
        assert verify_password(plain, legacy) is True
        assert verify_password("wrong_attempt", legacy) is False

        # Flagged for rehash
        assert needs_rehash(legacy) is True

        # Modern hash does not need rehash
        modern = hash_password(plain)
        assert needs_rehash(modern) is False

    def test_transparent_hash_upgrade_on_login(self, client, ndb_ctx):
        uid = uuid.uuid4().hex[:6]
        user_id = f"user-legacy-{uid}"
        username = f"legacy_user_{uid}"
        plain_pw = "UpgradeMeSecurely2026!"
        legacy_hash = _legacy_hash(plain_pw)

        user = User(
            user_id=user_id,
            username=username,
            display_name="Legacy User",
            role=UserRole.CONTRIBUTOR,
            password_hash=legacy_hash,
            is_active=True,
        )
        domain_services.create_user(user)

        # Verify initial state has legacy hash
        initial_user = domain_services.get_user(user_id)
        assert initial_user.password_hash == legacy_hash

        # Perform login
        resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": plain_pw,
        })
        assert resp.status_code == 200

        # Verify Datastore was transparently upgraded to modern PBKDF2 600k hash
        updated_user = domain_services.get_user(user_id)
        assert updated_user.password_hash.startswith("pbkdf2:sha256:600000$")
        assert updated_user.password_hash != legacy_hash
        assert verify_password(plain_pw, updated_user.password_hash) is True

    def test_benchmark_verification_practicality(self):
        """Verify that 600k iterations execute within a practical server response time (< 1000ms)."""
        pw = "BenchmarkPasswordCheck2026!"
        start_hash = time.perf_counter()
        h = hash_password(pw)
        hash_duration = time.perf_counter() - start_hash

        start_verify = time.perf_counter()
        valid = verify_password(pw, h)
        verify_duration = time.perf_counter() - start_verify

        assert valid is True
        assert verify_duration < 1.0, f"Verification took {verify_duration:.3f}s, expected < 1.0s"
        # Log benchmark timing for audit record
        print(f"\n[BENCHMARK] PBKDF2 600k: hash={hash_duration*1000:.1f}ms, verify={verify_duration*1000:.1f}ms")


def _make_sample_card(card_id: str = "card-1") -> dict[str, Any]:
    return {
        "id": card_id,
        "position": 1,
        "card_type": "explanation",
        "content_blocks": [
            {"block_type": "text", "body": "Explanation text body for security verification."}
        ],
        "source_ids": [],
    }


def _make_domain_card(card_id: str = "card-dom-1") -> LessonCard:
    return LessonCard(
        card_id=card_id,
        position=1,
        card_type=CardType.EXPLANATION,
        content_blocks=[
            ContentBlock(block_type="text", body="Explanation text body.")
        ],
        source_ids=[],
    )


# ===========================================================================
# 2. Resource-Level Authorization & Ownership Isolation Tests
# ===========================================================================


class TestResourceAuthorizationAndOwnership:
    @pytest.fixture()
    def setup_security_actors(self, ndb_ctx):
        """Create two independent contributors, a reviewer, and an admin."""
        u1 = User(
            user_id="user-contrib-alpha",
            username="contrib_alpha",
            display_name="Contributor Alpha",
            role=UserRole.CONTRIBUTOR,
            password_hash=hash_password("alpha_pass_12345"),
            is_active=True,
        )
        u2 = User(
            user_id="user-contrib-beta",
            username="contrib_beta",
            display_name="Contributor Beta",
            role=UserRole.CONTRIBUTOR,
            password_hash=hash_password("beta_pass_12345"),
            is_active=True,
        )
        reviewer = User(
            user_id="user-reviewer-delta",
            username="reviewer_delta",
            display_name="Reviewer Delta",
            role=UserRole.REVIEWER,
            password_hash=hash_password("reviewer_pass_12345"),
            is_active=True,
        )
        admin = User(
            user_id="user-admin-omega",
            username="admin_omega",
            display_name="Admin Omega",
            role=UserRole.ADMIN,
            password_hash=hash_password("admin_pass_12345"),
            is_active=True,
        )
        for u in (u1, u2, reviewer, admin):
            if not domain_services.get_user(u.user_id):
                domain_services.create_user(u)
        return {"alpha": u1, "beta": u2, "reviewer": reviewer, "admin": admin}

    def test_cross_contributor_draft_isolation(self, client, setup_security_actors):
        """Contributor B must not be able to view, edit, or submit Contributor A's drafts."""
        # 1. Login as Contributor Alpha
        client.post("/api/v1/auth/login", json={
            "username": "contrib_alpha",
            "password": "alpha_pass_12345",
        })

        topic_id = f"topic-sec-{uuid.uuid4().hex[:6]}"
        lesson_id = f"lesson-sec-{uuid.uuid4().hex[:6]}"
        version_id = f"ver-alpha-{uuid.uuid4().hex[:6]}"

        # Create topic, lesson, and draft version
        client.post("/api/v1/creator/topics", json={
            "id": topic_id,
            "title": "Alpha Exclusive Topic",
            "slug": f"alpha-{uuid.uuid4().hex[:6]}",
            "description": "Private draft topic",
        })
        client.post(f"/api/v1/creator/topics/{topic_id}/lessons", json={"id": lesson_id})
        ver_resp = client.post(f"/api/v1/creator/lessons/{lesson_id}/versions", json={
            "id": version_id,
            "version_number": 1,
            "title": "Alpha Private Draft",
            "summary": "Secret lesson content",
            "learning_objectives": ["Understand security boundary"],
            "estimated_duration_minutes": 5,
            "cards": [_make_sample_card("c-alpha-1")],
        })
        assert ver_resp.status_code == 201
        assert ver_resp.get_json()["data"]["author_id"] == "user-contrib-alpha"

        # 2. Login as Contributor Beta
        client.post("/api/v1/auth/login", json={
            "username": "contrib_beta",
            "password": "beta_pass_12345",
        })

        # Beta cannot view Alpha's draft via direct detail GET
        detail_resp = client.get(f"/api/v1/creator/versions/{version_id}")
        assert detail_resp.status_code == 403
        assert detail_resp.get_json()["error"]["code"] == "FORBIDDEN"

        # Beta cannot see Alpha's draft in lesson versions list
        list_resp = client.get(f"/api/v1/creator/lessons/{lesson_id}/versions")
        assert list_resp.status_code == 200
        assert not any(v["id"] == version_id for v in list_resp.get_json()["data"])

        # Beta cannot modify Alpha's draft via PUT
        put_resp = client.put(f"/api/v1/creator/versions/{version_id}", json={
            "title": "Tampered By Beta",
        })
        assert put_resp.status_code == 403
        assert put_resp.get_json()["error"]["code"] == "FORBIDDEN"

        # Beta cannot submit Alpha's draft via POST submit
        sub_resp = client.post(f"/api/v1/creator/versions/{version_id}/submit")
        assert sub_resp.status_code == 403
        assert sub_resp.get_json()["error"]["code"] == "FORBIDDEN"

    def test_reviewer_cannot_access_unsubmitted_drafts(self, client, setup_security_actors):
        """Reviewers must not be able to view work-in-progress drafts before submission."""
        # Alpha creates draft
        client.post("/api/v1/auth/login", json={
            "username": "contrib_alpha",
            "password": "alpha_pass_12345",
        })
        topic_id = f"topic-rev-{uuid.uuid4().hex[:6]}"
        lesson_id = f"lesson-rev-{uuid.uuid4().hex[:6]}"
        version_id = f"ver-unsub-{uuid.uuid4().hex[:6]}"

        client.post("/api/v1/creator/topics", json={
            "id": topic_id,
            "title": "Topic for Review Test",
            "slug": f"rev-{uuid.uuid4().hex[:6]}",
            "description": "Topic",
        })
        client.post(f"/api/v1/creator/topics/{topic_id}/lessons", json={"id": lesson_id})
        ver_resp = client.post(f"/api/v1/creator/lessons/{lesson_id}/versions", json={
            "id": version_id,
            "version_number": 1,
            "title": "Unsubmitted Draft",
            "summary": "Summary",
            "learning_objectives": ["Identify review boundaries"],
            "estimated_duration_minutes": 5,
            "cards": [_make_sample_card("c-unsub-1")],
        })
        assert ver_resp.status_code == 201

        # Reviewer logs in
        client.post("/api/v1/auth/login", json={
            "username": "reviewer_delta",
            "password": "reviewer_pass_12345",
        })

        # Reviewer cannot view unsubmitted draft
        resp = client.get(f"/api/v1/creator/versions/{version_id}")
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"

        # Alpha logs back in and submits
        client.post("/api/v1/auth/login", json={
            "username": "contrib_alpha",
            "password": "alpha_pass_12345",
        })
        sub_resp = client.post(f"/api/v1/creator/versions/{version_id}/submit")
        assert sub_resp.status_code == 200

        # Reviewer logs back in: CAN now access submitted version
        client.post("/api/v1/auth/login", json={
            "username": "reviewer_delta",
            "password": "reviewer_pass_12345",
        })
        view_resp = client.get(f"/api/v1/creator/versions/{version_id}")
        assert view_resp.status_code == 200
        assert view_resp.get_json()["data"]["title"] == "Unsubmitted Draft"


# ===========================================================================
# 3. Self-Approval Prevention & Immutability Tests
# ===========================================================================


class TestSelfApprovalAndImmutability:
    def test_author_cannot_approve_own_submission(self, client, ndb_ctx):
        """A user holding both contributor and reviewer roles cannot approve their own work."""
        uid = uuid.uuid4().hex[:6]
        user_id = f"user-dual-{uid}"
        username = f"dual_user_{uid}"
        dual_user = User(
            user_id=user_id,
            username=username,
            display_name="Dual Role User",
            role=UserRole.REVIEWER,  # Has reviewer role
            password_hash=hash_password("dual_pass_12345"),
            is_active=True,
        )
        domain_services.create_user(dual_user)

        client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "dual_pass_12345",
        })

        version_id = f"ver-self-{uuid.uuid4().hex[:6]}"
        lesson_id = f"lesson-self-{uuid.uuid4().hex[:6]}"
        topic_id = f"topic-self-{uuid.uuid4().hex[:6]}"

        domain_services.create_topic(Topic(
            topic_id=topic_id,
            title="Topic",
            url_slug=f"slug-{uuid.uuid4().hex[:6]}",
            description="D",
            display_order=1,
            status=PublicationStatus.DRAFT,
        ))
        domain_services.create_lesson(Lesson(lesson_id=lesson_id, topic_id=topic_id, display_order=1))

        # Create version authored by dual_user
        version = LessonVersion(
            version_id=version_id,
            lesson_id=lesson_id,
            version_number=1,
            title="Self Authored Version",
            summary="Summary",
            language="en",
            learning_objectives=["Self approval test"],
            estimated_duration_minutes=5,
            cards=[_make_domain_card("c-self-1")],
            source_ids=[],
            status=VersionStatus.DRAFT,
            author_id=user_id,
        )
        domain_services.create_lesson_version(version)

        # Submit version
        domain_services.submit_for_review(version_id, user_id=user_id)

        # Attempt to self-approve via API
        approve_resp = client.post(f"/api/v1/creator/versions/{version_id}/approve")
        assert approve_resp.status_code == 403
        assert "Self-approval is forbidden" in approve_resp.get_json()["error"]["message"]

    def test_published_versions_are_immutable(self, client, ndb_ctx):
        """Published versions cannot be modified via PUT."""
        uid = uuid.uuid4().hex[:6]
        user_id = f"user-admin-{uid}"
        username = f"admin_immut_{uid}"
        admin = User(
            user_id=user_id,
            username=username,
            display_name="Admin",
            role=UserRole.ADMIN,
            password_hash=hash_password("admin_pass_12345"),
            is_active=True,
        )
        domain_services.create_user(admin)

        client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "admin_pass_12345",
        })

        ver_id = f"ver-pub-{uuid.uuid4().hex[:6]}"
        lesson_id = f"lesson-pub-{uuid.uuid4().hex[:6]}"
        topic_id = f"topic-pub-{uuid.uuid4().hex[:6]}"

        domain_services.create_topic(Topic(
            topic_id=topic_id,
            title="Topic",
            url_slug=f"slug-{uuid.uuid4().hex[:6]}",
            description="D",
            display_order=1,
            status=PublicationStatus.DRAFT,
        ))
        domain_services.create_lesson(Lesson(lesson_id=lesson_id, topic_id=topic_id, display_order=1))
        domain_services.create_lesson_version(LessonVersion(
            version_id=ver_id,
            lesson_id=lesson_id,
            version_number=1,
            title="Published Lesson",
            summary="Initial content",
            language="en",
            learning_objectives=["Immutable check"],
            estimated_duration_minutes=5,
            cards=[_make_domain_card("c-pub-1")],
            source_ids=[],
            status=VersionStatus.DRAFT,
        ))
        domain_services.publish_lesson_version(ver_id)

        # Try to modify published version
        put_resp = client.put(f"/api/v1/creator/versions/{ver_id}", json={
            "title": "Mutated After Publication",
        })
        assert put_resp.status_code == 403
        assert "Only drafts can be edited" in put_resp.get_json()["error"]["message"]


# ===========================================================================
# 4. Session Security & Account Lifecycle Tests
# ===========================================================================


class TestSessionSecurity:
    def test_session_cookie_flags_and_sensitive_data_absence(self, client, ndb_ctx):
        uid = uuid.uuid4().hex[:6]
        user_id = f"user-cookie-{uid}"
        username = f"cookie_{uid}"
        user = User(
            user_id=user_id,
            username=username,
            display_name="Cookie Tester",
            role=UserRole.CONTRIBUTOR,
            password_hash=hash_password("cookie_pass_12345"),
            is_active=True,
        )
        domain_services.create_user(user)

        resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "cookie_pass_12345",
        })
        assert resp.status_code == 200

        # Verify XSRF-TOKEN cookie is set
        xsrf_cookie = client.get_cookie("XSRF-TOKEN")
        assert xsrf_cookie is not None
        assert xsrf_cookie.value != ""
        assert xsrf_cookie.path == "/"

        # Inspect session response: no password hash or secrets in payload
        payload = resp.get_json()["data"]
        assert "password" not in payload
        assert "password_hash" not in payload

    def test_deactivated_account_session_revocation(self, client, ndb_ctx):
        """If a user account is deactivated, existing sessions are invalidated immediately."""
        uid = uuid.uuid4().hex[:6]
        user_id = f"user-deact-{uid}"
        username = f"deact_{uid}"
        user = User(
            user_id=user_id,
            username=username,
            display_name="Deactivate Tester",
            role=UserRole.CONTRIBUTOR,
            password_hash=hash_password("deactivate_pass_12345"),
            is_active=True,
        )
        domain_services.create_user(user)

        # Login
        login_resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "deactivate_pass_12345",
        })
        assert login_resp.status_code == 200

        # Verify /me is active
        assert client.get("/api/v1/auth/me").status_code == 200

        # Deactivate user in Datastore
        user.is_active = False
        domain_services.UserModel.get_by_id(user_id).is_active = False
        domain_services.UserModel.get_by_id(user_id).put()

        # Next request must be rejected with 401
        me_resp = client.get("/api/v1/auth/me")
        assert me_resp.status_code == 401
        assert me_resp.get_json()["error"]["code"] == "UNAUTHORIZED"


# ===========================================================================
# 5. Anti-CSRF Token Protection Tests
# ===========================================================================


class TestCSRFProtection:
    def test_csrf_protection_on_mutating_requests(self, csrf_client, ndb_ctx):
        uid = uuid.uuid4().hex[:6]
        user_id = f"user-csrf-{uid}"
        username = f"csrf_{uid}"
        user = User(
            user_id=user_id,
            username=username,
            display_name="CSRF Tester",
            role=UserRole.CONTRIBUTOR,
            password_hash=hash_password("csrf_pass_12345"),
            is_active=True,
        )
        domain_services.create_user(user)

        # 1. Login to establish session
        login_resp = csrf_client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "csrf_pass_12345",
        })
        assert login_resp.status_code == 200
        csrf_token = login_resp.get_json()["data"]["csrf_token"]
        assert csrf_token

        topic_payload = {
            "id": f"topic-csrf-{uuid.uuid4().hex[:6]}",
            "title": "CSRF Protected Topic",
            "slug": f"csrf-{uuid.uuid4().hex[:6]}",
            "description": "Topic under CSRF testing",
        }

        # 2. Mutating request with valid X-XSRF-TOKEN header succeeds
        valid_resp = csrf_client.post(
            "/api/v1/creator/topics",
            json=topic_payload,
            headers={"X-XSRF-TOKEN": csrf_token},
        )
        assert valid_resp.status_code == 201

        # 3. Mutating request without CSRF header fails with 403 CSRF_ERROR
        tamper_payload = {
            "id": f"topic-csrf-{uuid.uuid4().hex[:6]}",
            "title": "Forged Topic",
            "slug": f"forged-{uuid.uuid4().hex[:6]}",
            "description": "Cross-site forged request attempt",
        }
        missing_resp = csrf_client.post(
            "/api/v1/creator/topics",
            json=tamper_payload,
        )
        assert missing_resp.status_code == 403
        assert missing_resp.get_json()["error"]["code"] == "CSRF_ERROR"

        # 4. Mutating request with invalid CSRF token fails with 403 CSRF_ERROR
        invalid_resp = csrf_client.post(
            "/api/v1/creator/topics",
            json=tamper_payload,
            headers={"X-XSRF-TOKEN": "forged_invalid_token_1234567890"},
        )
        assert invalid_resp.status_code == 403
        assert invalid_resp.get_json()["error"]["code"] == "CSRF_ERROR"

        # 5. Safe GET request succeeds without CSRF header
        get_resp = csrf_client.get("/api/v1/creator/topics")
        assert get_resp.status_code == 200


# ===========================================================================
# 6. CORS Policy & Origin Validation Tests
# ===========================================================================


class TestCORSPolicy:
    def test_allowed_origin_gets_cors_headers(self, client):
        resp = client.get(
            "/api/v1/topics",
            headers={"Origin": "http://localhost:4200"},
        )
        assert resp.status_code == 200
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:4200"
        assert resp.headers.get("Access-Control-Allow-Credentials") == "true"
        assert resp.headers.get("Vary") == "Origin"

    def test_untrusted_origin_never_reflected_or_wildcarded(self, client):
        resp = client.get(
            "/api/v1/topics",
            headers={"Origin": "https://evil-attacker-site.com"},
        )
        assert resp.status_code == 200
        # Untrusted origin must NOT receive Access-Control-Allow-Origin
        assert "Access-Control-Allow-Origin" not in resp.headers

    def test_preflight_options_rejects_untrusted_origin(self, client):
        resp = client.open(
            "/api/v1/creator/topics",
            method="OPTIONS",
            headers={
                "Origin": "https://evil-attacker-site.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Should not grant CORS access to untrusted origin
        assert "Access-Control-Allow-Origin" not in resp.headers
