"""Controller and Application unit tests (isolated, fast, no emulator required).

These tests verify Flask controllers, routing, response formatting, status codes,
error handling, and security boundaries using mocks where appropriate.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from backend.app import create_app
from backend.domain.domain_objects import (
    AnswerOption,
    CardType,
    ContentBlock,
    HealthSource,
    IncorrectBehaviour,
    InteractionType,
    Lesson,
    LessonCard,
    LessonVersion,
    PublicationStatus,
    SingleChoiceInteraction,
    Topic,
    VersionStatus,
)


@pytest.fixture()
def app() -> Flask:
    """Create Flask application in isolated testing mode."""
    test_app = create_app(
        {
            "TESTING": True,
            "SKIP_NDB_CONTEXT": True,
        }
    )
    return test_app


@pytest.fixture()
def client(app: Flask):
    """Flask test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Sample Domain Objects for Controller Mocks
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_topic() -> Topic:
    return Topic(
        topic_id="water-safety",
        title="Safe Drinking Water",
        url_slug="safe-drinking-water",
        description="Household water safety practices.",
        display_order=1,
        status=PublicationStatus.PUBLISHED,
        cover_image_ref="images/water.png",
        cover_image_alt="Clean glass of water",
    )


@pytest.fixture()
def mock_lesson_and_version() -> tuple[Lesson, LessonVersion]:
    lesson = Lesson(
        lesson_id="chlorination-basics",
        topic_id="water-safety",
        display_order=0,
        published_version_id="chlorination-basics-v1",
    )
    card = LessonCard(
        card_id="card-01",
        position=0,
        card_type=CardType.INTERACTION,
        content_blocks=[ContentBlock(block_type="text", body="Chlorine dosage instructions.")],
        source_ids=["who-water-2023"],
        interaction=SingleChoiceInteraction(
            interaction_type=InteractionType.SINGLE_CHOICE,
            question_prompt="How long should treated water sit before drinking?",
            options=[
                AnswerOption(
                    option_id="opt-30min",
                    label="30 minutes",
                    is_correct=True,
                    feedback="Correct! 30 minutes is the standard contact time.",
                ),
                AnswerOption(
                    option_id="opt-1min",
                    label="1 minute",
                    is_correct=False,
                    feedback="Incorrect. Chlorine requires at least 30 minutes.",
                ),
            ],
            incorrect_behaviour=IncorrectBehaviour.RETRY,
        ),
    )
    version = LessonVersion(
        version_id="chlorination-basics-v1",
        lesson_id="chlorination-basics",
        version_number=1,
        title="Water Chlorination Basics",
        summary="Safe chemical water treatment.",
        language="en",
        learning_objectives=["Understand chlorine contact time"],
        estimated_duration_minutes=6,
        cards=[card],
        source_ids=["who-water-2023"],
        status=VersionStatus.PUBLISHED,
    )
    return lesson, version


@pytest.fixture()
def mock_source() -> HealthSource:
    return HealthSource(
        source_id="who-water-2023",
        title="Guidelines for Drinking-water Quality",
        publisher="World Health Organization",
        url="https://www.who.int/water-quality",
        publication_date=date(2023, 3, 1),
        access_date=date(2025, 1, 15),
        jurisdiction="Global",
        metadata_notes="CONFIDENTIAL_CURATION_NOTE_DO_NOT_EXPOSE",
    )


# ====================================================================
# Endpoint D: Application Liveness (/api/v1/health)
# ====================================================================


class TestHealthEndpoint:
    def test_health_returns_200_json(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body == {
            "data": {"status": "healthy"},
            "meta": {"api_version": "v1"},
        }

    def test_health_does_not_leak_internals(self, client):
        resp = client.get("/api/v1/health")
        raw = resp.get_data(as_text=True)
        # Verify no sensitive keywords or paths appear
        assert "password" not in raw.lower()
        assert "secret" not in raw.lower()
        assert "database" not in raw.lower()
        assert "datastore" not in raw.lower()
        assert "C:\\" not in raw
        assert "/home" not in raw

    def test_cors_headers_present(self, client):
        resp = client.get("/api/v1/health", headers={"Origin": "http://localhost:4200"})
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:4200"
        assert "GET" in resp.headers.get("Access-Control-Allow-Methods", "")


# ====================================================================
# Endpoint A: List Topics (/api/v1/topics)
# ====================================================================


class TestTopicsEndpoint:
    @patch("backend.controllers.topics.domain_services.list_topics")
    def test_list_topics_success(self, mock_list, client, mock_topic):
        mock_list.return_value = [mock_topic]

        resp = client.get("/api/v1/topics")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()

        assert "data" in body
        assert "meta" in body
        assert body["meta"]["api_version"] == "v1"

        topics = body["data"]
        assert len(topics) == 1
        t = topics[0]
        assert t["id"] == "water-safety"
        assert t["title"] == "Safe Drinking Water"
        assert t["slug"] == "safe-drinking-water"
        assert t["description"] == "Household water safety practices."
        assert t["display_order"] == 1
        assert t["cover_image_ref"] == "images/water.png"
        assert t["cover_image_alt"] == "Clean glass of water"

        mock_list.assert_called_once_with(status=PublicationStatus.PUBLISHED)

    @patch("backend.controllers.topics.domain_services.list_topics")
    def test_list_topics_empty(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/v1/topics")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"] == []


# ====================================================================
# Endpoint B: List Topic Lessons (/api/v1/topics/<id>/lessons)
# ====================================================================


class TestTopicLessonsEndpoint:
    @patch("backend.controllers.topics.domain_services.get_published_lessons_for_topic")
    def test_list_topic_lessons_success(self, mock_get_lessons, client, mock_lesson_and_version):
        lesson, version = mock_lesson_and_version
        mock_get_lessons.return_value = [(lesson, version)]

        resp = client.get("/api/v1/topics/water-safety/lessons")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()

        lessons = body["data"]
        assert len(lessons) == 1
        l = lessons[0]
        assert l["id"] == "chlorination-basics"
        assert l["topic_id"] == "water-safety"
        assert l["title"] == "Water Chlorination Basics"
        assert l["summary"] == "Safe chemical water treatment."
        assert l["language"] == "en"
        assert l["estimated_duration_minutes"] == 6
        assert l["published_version_id"] == "chlorination-basics-v1"
        assert l["display_order"] == 0

    @patch("backend.controllers.topics.domain_services.get_published_lessons_for_topic")
    def test_list_topic_lessons_topic_not_found(self, mock_get_lessons, client):
        mock_get_lessons.return_value = None  # Topic missing or unpublished

        resp = client.get("/api/v1/topics/nonexistent/lessons")
        assert resp.status_code == 404
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body["error"]["code"] == "NOT_FOUND"
        assert "not found or is not published" in body["error"]["message"]


# ====================================================================
# Endpoint C: Lesson Detail (/api/v1/lessons/<lesson_id>)
# ====================================================================


class TestLessonDetailEndpoint:
    @patch("backend.controllers.lessons.domain_services.get_health_sources_by_ids")
    @patch("backend.controllers.lessons.domain_services.get_published_lesson")
    def test_get_lesson_detail_success(
        self, mock_get_lesson, mock_get_sources, client, mock_lesson_and_version, mock_source
    ):
        lesson, version = mock_lesson_and_version
        mock_get_lesson.return_value = (lesson, version)
        mock_get_sources.return_value = [mock_source]

        resp = client.get("/api/v1/lessons/chlorination-basics")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()

        data = body["data"]
        assert data["id"] == "chlorination-basics"
        assert data["topic_id"] == "water-safety"
        assert data["version_id"] == "chlorination-basics-v1"
        assert data["version_number"] == 1
        assert data["title"] == "Water Chlorination Basics"
        assert data["learning_objectives"] == ["Understand chlorine contact time"]

        # Check cards & interactions
        assert len(data["cards"]) == 1
        card = data["cards"][0]
        assert card["id"] == "card-01"
        assert card["position"] == 0
        assert card["card_type"] == "interaction"
        assert card["interaction"]["interaction_type"] == "single_choice"
        assert card["interaction"]["incorrect_behaviour"] == "retry"
        assert len(card["interaction"]["options"]) == 2

        # Check sources
        assert len(data["sources"]) == 1
        source = data["sources"][0]
        assert source["id"] == "who-water-2023"
        assert source["title"] == "Guidelines for Drinking-water Quality"
        assert source["publisher"] == "World Health Organization"
        assert source["publication_date"] == "2023-03-01"
        # Verify confidential metadata_notes is NOT serialized!
        assert "metadata_notes" not in source

    @patch("backend.controllers.lessons.domain_services.get_published_lesson")
    def test_get_lesson_detail_not_found(self, mock_get_lesson, client):
        mock_get_lesson.return_value = None  # Lesson missing or unpublished

        resp = client.get("/api/v1/lessons/nonexistent")
        assert resp.status_code == 404
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body["error"]["code"] == "NOT_FOUND"


# ====================================================================
# HTTP Method Enforcement & Error Handling
# ====================================================================


class TestHttpMethodsAndErrors:
    def test_post_disallowed(self, client):
        for path in ["/api/v1/topics", "/api/v1/topics/t1/lessons", "/api/v1/lessons/l1", "/api/v1/health"]:
            resp = client.post(path)
            assert resp.status_code == 405
            assert resp.content_type == "application/json"
            body = resp.get_json()
            assert body["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_put_disallowed(self, client):
        resp = client.put("/api/v1/topics")
        assert resp.status_code == 405
        assert resp.get_json()["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_delete_disallowed(self, client):
        resp = client.delete("/api/v1/lessons/l1")
        assert resp.status_code == 405
        assert resp.get_json()["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_patch_disallowed(self, client):
        resp = client.patch("/api/v1/topics")
        assert resp.status_code == 405
        assert resp.get_json()["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_unknown_route_returns_404(self, client):
        resp = client.get("/api/v1/nonexistent-route")
        assert resp.status_code == 404
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body["error"]["code"] == "NOT_FOUND"

    @patch("backend.controllers.topics.domain_services.list_topics")
    def test_unexpected_server_error_returns_sanitized_500(self, mock_list, client):
        mock_list.side_effect = RuntimeError("Simulated internal catastrophic failure")
        resp = client.get("/api/v1/topics")
        assert resp.status_code == 500
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # Ensure raw exception message / stack trace is NEVER returned to client
        assert "Simulated" not in body["error"]["message"]
        assert "catastrophic" not in body["error"]["message"]
        assert "Traceback" not in resp.get_data(as_text=True)

    @patch("backend.controllers.topics.domain_services.list_topics")
    def test_storage_connectivity_error_returns_503(self, mock_list, client):
        mock_list.side_effect = ConnectionRefusedError("Connection refused to 127.0.0.1:8080")
        resp = client.get("/api/v1/topics")
        assert resp.status_code == 503
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "storage service is currently unavailable" in body["error"]["message"]
