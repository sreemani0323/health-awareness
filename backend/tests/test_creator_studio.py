"""Comprehensive tests for HealthAware Creator Studio.

Tests cover:
1. User domain & authentication (login, logout, session state).
2. Role-based access control (401 for anonymous, 403 for unauthorized roles).
3. Draft isolation (draft topics/lessons never leak into public learner APIs).
4. Full authoring lifecycle: create topic -> add lesson -> build cards -> submit.
5. Self-approval prevention (contributors cannot approve their own submissions).
6. Reviewer workflow: inspection -> request changes (revert to draft) -> resubmit -> approve & publish.
7. Public availability verification post-publication.
8. Secure first-admin provisioning.
"""

from __future__ import annotations

import hashlib
from typing import Any

import pytest
from flask import Flask

from backend.app import create_app
from backend.domain import domain_services
from backend.domain.domain_objects import (
    AnswerOption,
    CardType,
    ContentBlock,
    InteractionType,
    Lesson,
    LessonCard,
    LessonVersion,
    PublicationStatus,
    SingleChoiceInteraction,
    Topic,
    User,
    UserRole,
    VersionStatus,
)
from backend.provision_admin import provision_admin


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


@pytest.fixture()
def client(ndb_ctx):
    """Flask test client running with test configuration inside isolated NDB context."""
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


@pytest.fixture()
def seeded_users(ndb_ctx):
    """Seed test contributor and reviewer users in the test namespace."""
    contributor = User(
        user_id="user-test-contributor",
        username="contributor_test",
        display_name="Test Contributor",
        role=UserRole.CONTRIBUTOR,
        password_hash=_hash("contributor123"),
    )
    reviewer = User(
        user_id="user-test-reviewer",
        username="reviewer_test",
        display_name="Test Reviewer",
        role=UserRole.REVIEWER,
        password_hash=_hash("reviewer123"),
    )
    admin = User(
        user_id="user-test-admin",
        username="admin_test",
        display_name="Test Admin",
        role=UserRole.ADMIN,
        password_hash=_hash("admin123"),
    )
    for u in (contributor, reviewer, admin):
        if not domain_services.get_user(u.user_id):
            domain_services.create_user(u)
    return {
        "contributor": contributor,
        "reviewer": reviewer,
        "admin": admin,
    }


# ===========================================================================
# 1. Authentication Tests
# ===========================================================================


class TestAuthentication:
    def test_login_success(self, client, seeded_users):
        resp = client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["username"] == "contributor_test"
        assert data["role"] == "contributor"

    def test_login_invalid_password(self, client, seeded_users):
        resp = client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_login_missing_fields(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400

    def test_me_endpoint_authenticated(self, client, seeded_users):
        # Login
        client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        # Check /me
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["username"] == "contributor_test"

    def test_me_endpoint_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_logout(self, client, seeded_users):
        client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

        # After logout, /me is unauthorized
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ===========================================================================
# 2. Permission and Role Security Tests
# ===========================================================================


class TestPermissionsAndSecurity:
    def test_anonymous_access_to_creator_topics_denied(self, client):
        resp = client.get("/api/v1/creator/topics")
        assert resp.status_code == 401

    def test_anonymous_topic_creation_denied(self, client):
        resp = client.post("/api/v1/creator/topics", json={"id": "topic-test"})
        assert resp.status_code == 401

    def test_contributor_cannot_access_review_queue(self, client, seeded_users):
        client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        resp = client.get("/api/v1/creator/reviews")
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    def test_contributor_cannot_approve_version_directly(self, client, seeded_users):
        client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        resp = client.post("/api/v1/creator/versions/ver-test/approve")
        assert resp.status_code == 403

    def test_reviewer_can_access_review_queue(self, client, seeded_users):
        client.post("/api/v1/auth/login", json={
            "username": "reviewer_test",
            "password": "reviewer123",
        })
        resp = client.get("/api/v1/creator/reviews")
        assert resp.status_code == 200


# ===========================================================================
# 3. End-to-End Contributor & Reviewer Lifecycle Tests
# ===========================================================================


class TestCreatorLifecycleWorkflow:
    def test_full_authoring_review_publication_journey(self, client, seeded_users):
        import uuid
        uid = uuid.uuid4().hex[:8]
        test_topic_id = f"topic-nutri-{uid}"
        test_lesson_id = f"lesson-macro-{uid}"
        test_version_id = f"ver-macro-{uid}"

        # 1. Sign in as Contributor
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        assert login_resp.status_code == 200

        # 2. Create Topic Draft
        topic_payload = {
            "id": test_topic_id,
            "title": "Healthy Nutrition Basics",
            "slug": f"healthy-nutrition-{uid}",
            "description": "Essential nutritional guidelines for balanced health.",
            "display_order": 3,
        }
        create_top_resp = client.post("/api/v1/creator/topics", json=topic_payload)
        assert create_top_resp.status_code == 201
        topic_data = create_top_resp.get_json()["data"]
        assert topic_data["status"] == "draft"

        # 3. DRAFT ISOLATION: Verify draft topic does NOT leak into public API!
        pub_topics_resp = client.get("/api/v1/topics")
        assert pub_topics_resp.status_code == 200
        pub_ids = [t["id"] for t in pub_topics_resp.get_json()["data"]]
        assert test_topic_id not in pub_ids

        # 4. Add Lesson shell
        lesson_payload = {"id": test_lesson_id, "display_order": 1}
        create_les_resp = client.post(
            f"/api/v1/creator/topics/{test_topic_id}/lessons",
            json=lesson_payload,
        )
        assert create_les_resp.status_code == 201

        # 5. Create Draft Version with cards & quiz interaction
        version_payload = {
            "id": test_version_id,
            "version_number": 1,
            "title": "Macronutrients Explained",
            "summary": "Learn the roles of carbohydrates, proteins, and healthy fats.",
            "learning_objectives": ["Identify the 3 major macronutrients", "Understand balanced intake"],
            "estimated_duration_minutes": 5,
            "cards": [
                {
                    "id": f"card-exp-{uid}",
                    "position": 0,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "What are Macronutrients?"},
                        {"block_type": "text", "body": "Macronutrients provide the bulk of energy needed for bodily functions."},
                    ],
                },
                {
                    "id": f"card-quiz-{uid}",
                    "position": 1,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "text", "body": "Test your knowledge on macronutrients."},
                    ],
                    "interaction": {
                        "question_prompt": "Which macronutrient is the primary fuel source for high-intensity activity?",
                        "options": [
                            {"id": "opt-1", "label": "Carbohydrates", "is_correct": True, "feedback": "Correct! Carbohydrates break down into glucose."},
                            {"id": "opt-2", "label": "Fiber only", "is_correct": False, "feedback": "Fiber cannot be broken down for fast fuel."},
                        ],
                    },
                },
                {
                    "id": f"card-recap-{uid}",
                    "position": 2,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary"},
                        {"block_type": "text", "body": "A balanced diet contains proteins, carbs, and fats in suitable proportions."},
                    ],
                },
            ],
            "source_ids": [],
        }
        create_ver_resp = client.post(
            f"/api/v1/creator/lessons/{test_lesson_id}/versions",
            json=version_payload,
        )
        assert create_ver_resp.status_code == 201
        ver_data = create_ver_resp.get_json()["data"]
        assert ver_data["status"] == "draft"

        # 6. DRAFT ISOLATION: Public lesson endpoint returns 404 for draft lesson
        pub_les_resp = client.get(f"/api/v1/lessons/{test_lesson_id}")
        assert pub_les_resp.status_code == 404

        # 7. Contributor submits for review
        submit_resp = client.post(f"/api/v1/creator/versions/{test_version_id}/submit")
        assert submit_resp.status_code == 200
        assert submit_resp.get_json()["data"]["status"] == "submitted_for_review"

        # 8. SELF-APPROVAL PREVENTION:
        # Contributor attempts to approve their own submission -> MUST FAIL (403)!
        self_approve_resp = client.post(f"/api/v1/creator/versions/{test_version_id}/approve")
        assert self_approve_resp.status_code == 403

        # Logout contributor
        client.post("/api/v1/auth/logout")

        # 9. Sign in as Reviewer
        client.post("/api/v1/auth/login", json={
            "username": "reviewer_test",
            "password": "reviewer123",
        })

        # Check review queue has submitted version
        queue_resp = client.get("/api/v1/creator/reviews")
        assert queue_resp.status_code == 200
        queue_items = queue_resp.get_json()["data"]
        assert any(item["id"] == test_version_id for item in queue_items)

        # 10. Reviewer requests changes with written feedback
        changes_resp = client.post(
            f"/api/v1/creator/versions/{test_version_id}/request-changes",
            json={"notes": "Please verify dietary fibre terminology in explanation."},
        )
        assert changes_resp.status_code == 200
        # Version reverts to DRAFT
        assert changes_resp.get_json()["data"]["status"] == "draft"

        # Review queue is now empty of this item
        queue_resp2 = client.get("/api/v1/creator/reviews")
        assert not any(item["id"] == test_version_id for item in queue_resp2.get_json()["data"])

        # Logout reviewer
        client.post("/api/v1/auth/logout")

        # 11. Contributor updates draft and resubmits
        client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        update_ver_resp = client.put(
            f"/api/v1/creator/versions/{test_version_id}",
            json={"summary": "Updated summary with clarified dietary fiber details."},
        )
        assert update_ver_resp.status_code == 200

        resubmit_resp = client.post(f"/api/v1/creator/versions/{test_version_id}/submit")
        assert resubmit_resp.status_code == 200
        assert resubmit_resp.get_json()["data"]["status"] == "submitted_for_review"

        client.post("/api/v1/auth/logout")

        # 12. Reviewer approves & publishes
        client.post("/api/v1/auth/login", json={
            "username": "reviewer_test",
            "password": "reviewer123",
        })
        approve_resp = client.post(f"/api/v1/creator/versions/{test_version_id}/approve")
        assert approve_resp.status_code == 200
        assert approve_resp.get_json()["data"]["status"] == "published"

        # 13. PUBLIC LEARNER VERIFICATION POST-PUBLICATION!
        # The topic is now live and published!
        pub_topics_after = client.get("/api/v1/topics")
        assert pub_topics_after.status_code == 200
        after_ids = [t["id"] for t in pub_topics_after.get_json()["data"]]
        assert test_topic_id in after_ids

        # The published lesson is now available to learners!
        pub_lesson_after = client.get(f"/api/v1/lessons/{test_lesson_id}")
        assert pub_lesson_after.status_code == 200
        les_data = pub_lesson_after.get_json()["data"]
        assert les_data["title"] == "Macronutrients Explained"
        assert len(les_data["cards"]) == 3


# ===========================================================================
# 3b. Creator Chapter Management Tests (Reorder, Detail, Delete)
# ===========================================================================


class TestCreatorChapterManagement:
    def test_chapter_lifecycle_reorder_and_delete(self, ndb_ctx, client, seeded_users):
        import uuid
        uid = uuid.uuid4().hex[:6]
        test_topic_id = f"topic-cardio-{uid}"
        ch1_id = f"lesson-cardio-intro-{uid}"
        ch2_id = f"lesson-cardio-exercise-{uid}"

        # 1. Contributor logs in
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "contributor_test",
            "password": "contributor123",
        })
        assert login_resp.status_code == 200

        # 2. Create topic
        topic_resp = client.post("/api/v1/creator/topics", json={
            "id": test_topic_id,
            "title": "Cardiovascular Health",
            "slug": f"cardio-health-{uid}",
            "description": "Heart health basics",
        })
        assert topic_resp.status_code == 201

        # 3. Add Chapter 1
        ch1_resp = client.post(f"/api/v1/creator/topics/{test_topic_id}/lessons", json={
            "id": ch1_id,
            "title": "Introduction to Heart Anatomy",
            "summary": "Heart chambers and valves",
            "display_order": 1,
        })
        assert ch1_resp.status_code == 201
        ch1_data = ch1_resp.get_json()["data"]
        assert ch1_data["title"] == "Introduction to Heart Anatomy"
        assert ch1_data["display_order"] == 1
        assert ch1_data["card_count"] == 1

        # 4. Add Chapter 2
        ch2_resp = client.post(f"/api/v1/creator/topics/{test_topic_id}/lessons", json={
            "id": ch2_id,
            "title": "Cardio Exercises",
            "summary": "Aerobic workouts",
            "display_order": 2,
        })
        assert ch2_resp.status_code == 201

        # 5. Fetch Chapter details
        ch1_get = client.get(f"/api/v1/creator/lessons/{ch1_id}")
        assert ch1_get.status_code == 200
        assert ch1_get.get_json()["data"]["title"] == "Introduction to Heart Anatomy"

        # 6. Reorder chapters: Swap ch1 and ch2
        reorder_resp = client.put(f"/api/v1/creator/lessons/{ch1_id}", json={
            "display_order": 2,
        })
        assert reorder_resp.status_code == 200
        assert reorder_resp.get_json()["data"]["display_order"] == 2

        # 7. Delete an unpublished draft chapter
        del_resp = client.delete(f"/api/v1/creator/lessons/{ch2_id}")
        assert del_resp.status_code == 200
        assert del_resp.get_json()["data"]["deleted"] is True

        # Check it is gone from list
        list_resp = client.get(f"/api/v1/creator/topics/{test_topic_id}/lessons")
        assert list_resp.status_code == 200
        remaining_ids = [l["id"] for l in list_resp.get_json()["data"]]
        assert ch2_id not in remaining_ids
        assert ch1_id in remaining_ids


# ===========================================================================
# 4. Administrator Provisioning Test
# ===========================================================================


class TestAdminProvisioning:
    def test_provision_admin_cli_tool(self, ndb_ctx, client):
        provision_admin(
            username="superadmin",
            password="supersecurepassword123",
            display_name="Super Administrator",
        )

        # Admin can now log in
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "superadmin",
            "password": "supersecurepassword123",
        })
        assert login_resp.status_code == 200
        data = login_resp.get_json()["data"]
        assert data["role"] == "admin"
        assert data["display_name"] == "Super Administrator"
