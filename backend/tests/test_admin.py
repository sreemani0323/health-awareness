"""Unit and integration tests for Creator Studio Administrator features.

Covers:
1. Role-based access control for /api/v1/admin/* endpoints (anonymous -> 401, contributor/reviewer -> 403, admin -> 200).
2. User management listing (ensuring password hashes are never exposed).
3. User provisioning (password length validation, role validation, duplicate username rejection, credentials work upon creation).
4. Role mutation (changing contributor to reviewer).
5. Account deactivation (self-deactivation forbidden, deactivated user immediately locked out on next request).
6. Administrative overview summary metrics.
7. Reviewer written feedback persistence and return via creator serialization.
"""

from __future__ import annotations

import uuid
import pytest

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
from backend.platform.security import hash_password


@pytest.fixture()
def client(ndb_ctx):
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


def _create_user(username: str, role: UserRole, password: str = "testpass123") -> User:
    uid = f"user-{uuid.uuid4().hex[:8]}"
    u = User(
        user_id=uid,
        username=username,
        display_name=username.title(),
        role=role,
        password_hash=hash_password(password),
        is_active=True,
    )
    return domain_services.create_user(u)


def _login(client, username: str, password: str = "testpass123") -> str:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.get_json()["data"]["csrf_token"]


class TestAdminEndpoints:
    def test_admin_endpoints_require_admin_role(self, client, ndb_ctx):
        """Anonymous, Contributor, and Reviewer accounts cannot access admin endpoints."""
        u_suffix = uuid.uuid4().hex[:6]
        c_user = _create_user(f"contrib_{u_suffix}", UserRole.CONTRIBUTOR)
        r_user = _create_user(f"reviewer_{u_suffix}", UserRole.REVIEWER)

        # Anonymous -> 401
        res = client.get("/api/v1/admin/users")
        assert res.status_code == 401

        res = client.get("/api/v1/admin/overview")
        assert res.status_code == 401

        # Contributor -> 403
        _login(client, c_user.username)
        res = client.get("/api/v1/admin/users")
        assert res.status_code == 403

        res = client.get("/api/v1/admin/overview")
        assert res.status_code == 403

        # Reviewer -> 403
        _login(client, r_user.username)
        res = client.get("/api/v1/admin/users")
        assert res.status_code == 403

    def test_admin_can_list_users_without_exposing_passwords(self, client, ndb_ctx):
        """Admin can list accounts and password_hash is never exposed."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        _login(client, admin.username)

        res = client.get("/api/v1/admin/users")
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert len(data) >= 1
        for u in data:
            assert "password_hash" not in u
            assert "password" not in u
            assert "username" in u
            assert "role" in u
            assert "is_active" in u

    def test_admin_can_create_user(self, client, ndb_ctx):
        """Admin can provision a new account and user can immediately log in."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        csrf = _login(client, admin.username)

        new_username = f"new_contributor_{u_suffix}"
        res = client.post(
            "/api/v1/admin/users",
            json={
                "username": new_username,
                "display_name": "New Community Educator",
                "role": "contributor",
                "password": "strongPassword123",
            },
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 201
        user_data = res.get_json()["data"]
        assert user_data["username"] == new_username
        assert user_data["role"] == "contributor"
        assert "password" not in user_data
        assert "password_hash" not in user_data

        # Verify new user can sign in
        client.post("/api/v1/auth/logout", headers={"X-CSRF-TOKEN": csrf})
        login_res = client.post(
            "/api/v1/auth/login",
            json={"username": new_username, "password": "strongPassword123"},
        )
        assert login_res.status_code == 200
        assert login_res.get_json()["data"]["role"] == "contributor"

    def test_admin_create_user_validations(self, client, ndb_ctx):
        """Validation errors on short password, duplicate username, invalid role."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        csrf = _login(client, admin.username)

        # Short password
        res = client.post(
            "/api/v1/admin/users",
            json={
                "username": f"user_short_{u_suffix}",
                "display_name": "Short Pwd",
                "role": "contributor",
                "password": "short",
            },
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 400
        assert "at least 8 characters" in res.get_json()["error"]["message"]

        # Invalid role
        res = client.post(
            "/api/v1/admin/users",
            json={
                "username": f"user_role_{u_suffix}",
                "display_name": "Bad Role",
                "role": "superman",
                "password": "strongPassword123",
            },
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 400

        # Duplicate username
        res = client.post(
            "/api/v1/admin/users",
            json={
                "username": admin.username,
                "display_name": "Dup Admin",
                "role": "admin",
                "password": "strongPassword123",
            },
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 400
        assert "already taken" in res.get_json()["error"]["message"]

    def test_admin_can_update_user_role(self, client, ndb_ctx):
        """Admin can change a user's role."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        target = _create_user(f"target_{u_suffix}", UserRole.CONTRIBUTOR)
        csrf = _login(client, admin.username)

        res = client.put(
            f"/api/v1/admin/users/{target.user_id}/role",
            json={"role": "reviewer"},
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 200
        assert res.get_json()["data"]["role"] == "reviewer"

        # Verify persisted in Datastore
        updated_target = domain_services.get_user(target.user_id)
        assert updated_target.role == UserRole.REVIEWER

    def test_admin_can_deactivate_and_locks_out_session(self, client, ndb_ctx):
        """Deactivating an account immediately blocks their active session and login."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        target = _create_user(f"target_{u_suffix}", UserRole.CONTRIBUTOR, password="targetpass123")

        # Target logs in
        _login(client, target.username, "targetpass123")
        assert client.get("/api/v1/auth/me").status_code == 200

        # Deactivate target via domain service (as admin endpoint does)
        domain_services.set_user_active_status(target.user_id, False)

        # Target's existing session is immediately rejected with 401
        blocked_res = client.get("/api/v1/auth/me")
        assert blocked_res.status_code == 401

        # Also verify deactivation prevents new logins
        login_res = client.post(
            "/api/v1/auth/login",
            json={"username": target.username, "password": "targetpass123"},
        )
        assert login_res.status_code == 401

        # Now test admin deactivation endpoint directly
        admin_csrf = _login(client, admin.username)
        target2 = _create_user(f"target2_{u_suffix}", UserRole.CONTRIBUTOR)
        res = client.put(
            f"/api/v1/admin/users/{target2.user_id}/status",
            json={"is_active": False},
            headers={"X-CSRF-TOKEN": admin_csrf},
        )
        assert res.status_code == 200
        assert res.get_json()["data"]["is_active"] is False
        assert domain_services.get_user(target2.user_id).is_active is False

    def test_admin_cannot_deactivate_self(self, client, ndb_ctx):
        """Admin cannot deactivate their own active account."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        csrf = _login(client, admin.username)

        res = client.put(
            f"/api/v1/admin/users/{admin.user_id}/status",
            json={"is_active": False},
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 400
        assert "cannot deactivate their own" in res.get_json()["error"]["message"]

    def test_admin_overview_metrics(self, client, ndb_ctx):
        """Admin overview returns expected health and operational counts."""
        u_suffix = uuid.uuid4().hex[:6]
        admin = _create_user(f"admin_{u_suffix}", UserRole.ADMIN)
        _login(client, admin.username)

        res = client.get("/api/v1/admin/overview")
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "total_users" in data
        assert "active_users" in data
        assert "users_by_role" in data
        assert "total_topics" in data
        assert "pending_reviews" in data

    def test_review_feedback_persists_on_request_changes(self, client, ndb_ctx):
        """When reviewer requests changes, notes are saved in review_feedback and returned."""
        u_suffix = uuid.uuid4().hex[:6]
        author = _create_user(f"author_{u_suffix}", UserRole.CONTRIBUTOR)
        reviewer = _create_user(f"rev_{u_suffix}", UserRole.REVIEWER)

        topic_id = f"topic-{u_suffix}"
        lesson_id = f"lesson-{u_suffix}"
        ver_id = f"ver-{u_suffix}"

        domain_services.create_topic(Topic(
            topic_id=topic_id,
            title="Topic",
            url_slug=f"slug-{u_suffix}",
            description="D",
            display_order=1,
            status=PublicationStatus.DRAFT,
        ))
        domain_services.create_lesson(Lesson(
            lesson_id=lesson_id,
            topic_id=topic_id,
            display_order=1,
            draft_version_id=ver_id,
        ))
        card = LessonCard(
            card_id=f"c-{u_suffix}",
            position=0,
            card_type=CardType.EXPLANATION,
            content_blocks=[ContentBlock(block_type="text", body="Explanation")],
            source_ids=[],
        )
        ver = LessonVersion(
            version_id=ver_id,
            lesson_id=lesson_id,
            version_number=1,
            title="Chapter 1",
            summary="S",
            language="en",
            learning_objectives=["O"],
            estimated_duration_minutes=5,
            cards=[card],
            source_ids=[],
            status=VersionStatus.DRAFT,
            author_id=author.user_id,
        )
        domain_services.create_lesson_version(ver)
        domain_services.submit_for_review(ver_id, user_id=author.user_id)

        # Reviewer requests changes with specific notes
        csrf = _login(client, reviewer.username)
        res = client.post(
            f"/api/v1/creator/versions/{ver_id}/request-changes",
            json={"notes": "Please add medical citation from WHO regarding handwashing time."},
            headers={"X-CSRF-TOKEN": csrf},
        )
        assert res.status_code == 200
        ver_data = res.get_json()["data"]
        assert ver_data["status"] == "draft"
        assert ver_data["review_feedback"] == "Please add medical citation from WHO regarding handwashing time."

        # Verify that get_lesson also includes the review_feedback
        lesson_res = client.get(f"/api/v1/creator/lessons/{lesson_id}")
        assert lesson_res.status_code == 200
        assert lesson_res.get_json()["data"]["review_feedback"] == "Please add medical citation from WHO regarding handwashing time."
