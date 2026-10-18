"""API Integration tests executed against the local Datastore emulator.

Tests verify end-to-end HTTP request processing through controllers, domain services,
and NDB persistence, strictly enforcing publication rules and data segregation.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Generator

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
from backend.domain.domain_services import (
    create_health_source,
    create_lesson,
    create_lesson_version,
    create_topic,
    delete_health_source,
    delete_lesson,
    delete_topic,
    publish_lesson_version,
)
from backend.storage.storage_models import LessonVersionModel


def _uid(prefix: str = "") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}" if prefix else f"e-{uuid.uuid4().hex[:12]}"


@pytest.fixture()
def app(ndb_ctx) -> Flask:
    """Create Flask application integrated with the active emulator NDB context."""
    test_app = create_app({"TESTING": True})
    return test_app


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


# ---------------------------------------------------------------------------
# Test Data Fixtures & Teardown
# ---------------------------------------------------------------------------


@pytest.fixture()
def seeded_content(ndb_ctx) -> Generator[dict, None, None]:
    """Seed a rich, realistic scenario in the Datastore emulator:

    1. A Published Topic with:
       - Lesson 1 (Published v1) with cards, interaction, and WHO citation.
       - Lesson 2 (Draft only) - must NOT be visible publicly.
       - Lesson 3 (Published v2, while v1 is Archived) - only v2 should be returned.
    2. A Draft Topic with:
       - Lesson 4 (Published within a draft topic) - must NOT be visible publicly!

    Cleans up all entities upon completion.
    """
    topic_pub_id = _uid("top-pub")
    topic_draft_id = _uid("top-draft")
    lesson1_id = _uid("les-1")
    lesson2_id = _uid("les-2")
    lesson3_id = _uid("les-3")
    lesson4_id = _uid("les-4")
    source_id = _uid("src-who")

    cleanup_topics = [topic_pub_id, topic_draft_id]
    cleanup_lessons = [lesson1_id, lesson2_id, lesson3_id, lesson4_id]
    cleanup_versions = []
    cleanup_sources = [source_id]

    try:
        # 1. Authoritative Health Source
        source = HealthSource(
            source_id=source_id,
            title="WHO Global Handwashing Guidelines",
            publisher="World Health Organization",
            url="https://www.who.int/campaigns/world-hand-hygiene-day",
            publication_date=date(2024, 5, 5),
            access_date=date(2025, 6, 1),
            jurisdiction="Global",
            metadata_notes="INTERNAL_TEAM_REVIEW_NOTE",
        )
        create_health_source(source)

        # 2. Published Topic
        topic_pub = Topic(
            topic_id=topic_pub_id,
            title="Community Sanitation",
            url_slug=f"community-sanitation-{uuid.uuid4().hex[:6]}",
            description="Best practices for community health and sanitation.",
            display_order=0,
            status=PublicationStatus.PUBLISHED,
            cover_image_ref="images/sanitation.png",
            cover_image_alt="Sanitation workers in community",
        )
        create_topic(topic_pub)

        # 3. Draft Topic
        topic_draft = Topic(
            topic_id=topic_draft_id,
            title="Experimental Health Topic",
            url_slug=f"experimental-health-{uuid.uuid4().hex[:6]}",
            description="Unapproved content currently in internal draft.",
            display_order=10,
            status=PublicationStatus.DRAFT,
        )
        create_topic(topic_draft)

        # 4. Lesson 1 (Published under Published Topic)
        lesson1 = Lesson(
            lesson_id=lesson1_id,
            topic_id=topic_pub_id,
            display_order=0,
        )
        create_lesson(lesson1)

        card1 = LessonCard(
            card_id=_uid("card"),
            position=0,
            card_type=CardType.EXPLANATION,
            content_blocks=[ContentBlock(block_type="text", body="Always wash hands with clean water.")],
            source_ids=[source_id],
        )
        card2 = LessonCard(
            card_id=_uid("card"),
            position=1,
            card_type=CardType.INTERACTION,
            content_blocks=[ContentBlock(block_type="text", body="Check your understanding:")],
            source_ids=[],
            interaction=SingleChoiceInteraction(
                interaction_type=InteractionType.SINGLE_CHOICE,
                question_prompt="How long should you scrub hands with soap?",
                options=[
                    AnswerOption(
                        option_id="opt-20s",
                        label="At least 20 seconds",
                        is_correct=True,
                        feedback="Correct! 20 seconds is recommended by WHO.",
                    ),
                    AnswerOption(
                        option_id="opt-5s",
                        label="5 seconds",
                        is_correct=False,
                        feedback="Too short! 20 seconds is necessary to remove pathogens.",
                    ),
                ],
                incorrect_behaviour=IncorrectBehaviour.RETRY,
            ),
        )
        v1_id = _uid("ver-1")
        cleanup_versions.append(v1_id)
        version1 = LessonVersion(
            version_id=v1_id,
            lesson_id=lesson1_id,
            version_number=1,
            title="Hand Hygiene Essentials",
            summary="Essential daily handwashing techniques.",
            language="en",
            learning_objectives=["Identify key hand hygiene moments"],
            estimated_duration_minutes=5,
            cards=[card1, card2],
            source_ids=[source_id],
            status=VersionStatus.DRAFT,
        )
        create_lesson_version(version1)
        publish_lesson_version(v1_id)

        # 5. Lesson 2 (Draft-only under Published Topic)
        lesson2 = Lesson(
            lesson_id=lesson2_id,
            topic_id=topic_pub_id,
            display_order=1,
        )
        create_lesson(lesson2)
        v2_draft_id = _uid("ver-draft")
        cleanup_versions.append(v2_draft_id)
        version2_draft = LessonVersion(
            version_id=v2_draft_id,
            lesson_id=lesson2_id,
            version_number=1,
            title="Draft Lesson Subject",
            summary="Not yet approved for public release.",
            language="en",
            learning_objectives=["Draft objective"],
            estimated_duration_minutes=3,
            cards=[card1],
            source_ids=[],
            status=VersionStatus.DRAFT,
        )
        create_lesson_version(version2_draft)
        # Note: Lesson 2 is NOT published!

        # 6. Lesson 3 (Has v1 archived, v2 published)
        lesson3 = Lesson(
            lesson_id=lesson3_id,
            topic_id=topic_pub_id,
            display_order=2,
        )
        create_lesson(lesson3)
        v3_old_id = _uid("ver-v1")
        cleanup_versions.append(v3_old_id)
        version3_old = LessonVersion(
            version_id=v3_old_id,
            lesson_id=lesson3_id,
            version_number=1,
            title="Old Lesson Content",
            summary="Deprecated text.",
            language="en",
            learning_objectives=["Old objective"],
            estimated_duration_minutes=4,
            cards=[card1],
            source_ids=[],
            status=VersionStatus.DRAFT,
        )
        create_lesson_version(version3_old)
        publish_lesson_version(v3_old_id)

        v3_new_id = _uid("ver-v2")
        cleanup_versions.append(v3_new_id)
        version3_new = LessonVersion(
            version_id=v3_new_id,
            lesson_id=lesson3_id,
            version_number=2,
            title="Updated Lesson Content",
            summary="Current modern guidance.",
            language="en",
            learning_objectives=["Modern objective"],
            estimated_duration_minutes=4,
            cards=[card1],
            source_ids=[],
            status=VersionStatus.DRAFT,
        )
        create_lesson_version(version3_new)
        publish_lesson_version(v3_new_id)

        # 7. Lesson 4 (Published, BUT parent topic is DRAFT)
        lesson4 = Lesson(
            lesson_id=lesson4_id,
            topic_id=topic_draft_id,
            display_order=0,
        )
        create_lesson(lesson4)
        v4_id = _uid("ver-4")
        cleanup_versions.append(v4_id)
        version4 = LessonVersion(
            version_id=v4_id,
            lesson_id=lesson4_id,
            version_number=1,
            title="Lesson in Draft Topic",
            summary="Should never be visible publicly.",
            language="en",
            learning_objectives=["Unpublished objective"],
            estimated_duration_minutes=2,
            cards=[card1],
            source_ids=[],
            status=VersionStatus.DRAFT,
        )
        create_lesson_version(version4)
        publish_lesson_version(v4_id)

        yield {
            "topic_pub_id": topic_pub_id,
            "topic_draft_id": topic_draft_id,
            "lesson1_id": lesson1_id,
            "lesson2_id": lesson2_id,
            "lesson3_id": lesson3_id,
            "lesson4_id": lesson4_id,
            "v1_id": v1_id,
            "v3_old_id": v3_old_id,
            "v3_new_id": v3_new_id,
            "source_id": source_id,
        }

    finally:
        # Teardown: delete all test entities from Datastore
        for vid in cleanup_versions:
            m = LessonVersionModel.get_by_id(vid)
            if m:
                m.key.delete()
        for lid in cleanup_lessons:
            try:
                delete_lesson(lid)
            except Exception:
                pass
        for tid in cleanup_topics:
            try:
                delete_topic(tid)
            except Exception:
                pass
        for sid in cleanup_sources:
            try:
                delete_health_source(sid)
            except Exception:
                pass


# ====================================================================
# Topic API Integration Tests
# ====================================================================


class TestTopicsApiIntegration:
    def test_list_topics_includes_published_only(self, client, seeded_content):
        resp = client.get("/api/v1/topics")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()

        topic_ids = [t["id"] for t in body["data"]]
        # Published topic must be present
        assert seeded_content["topic_pub_id"] in topic_ids
        # Draft topic must NOT be present
        assert seeded_content["topic_draft_id"] not in topic_ids

        # Verify attributes on published topic
        pub_topic = [t for t in body["data"] if t["id"] == seeded_content["topic_pub_id"]][0]
        assert pub_topic["title"] == "Community Sanitation"
        assert pub_topic["cover_image_ref"] == "images/sanitation.png"
        assert pub_topic["cover_image_alt"] == "Sanitation workers in community"


# ====================================================================
# Topic Lessons API Integration Tests
# ====================================================================


class TestTopicLessonsApiIntegration:
    def test_list_published_lessons_in_topic(self, client, seeded_content):
        pub_id = seeded_content["topic_pub_id"]
        resp = client.get(f"/api/v1/topics/{pub_id}/lessons")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()

        lesson_ids = [l["id"] for l in body["data"]]
        # Lesson 1 (Published) must be present
        assert seeded_content["lesson1_id"] in lesson_ids
        # Lesson 3 (Published v2) must be present
        assert seeded_content["lesson3_id"] in lesson_ids
        # Lesson 2 (Draft only) must NOT be present
        assert seeded_content["lesson2_id"] not in lesson_ids

        # Verify ordering: Lesson 1 has display_order 0, Lesson 3 has display_order 2
        assert lesson_ids.index(seeded_content["lesson1_id"]) < lesson_ids.index(seeded_content["lesson3_id"])

        # Verify Lesson 3 references v2, not archived v1
        l3 = [l for l in body["data"] if l["id"] == seeded_content["lesson3_id"]][0]
        assert l3["published_version_id"] == seeded_content["v3_new_id"]
        assert l3["title"] == "Updated Lesson Content"

    def test_draft_topic_lessons_returns_404(self, client, seeded_content):
        draft_id = seeded_content["topic_draft_id"]
        resp = client.get(f"/api/v1/topics/{draft_id}/lessons")
        assert resp.status_code == 404
        assert resp.content_type == "application/json"
        body = resp.get_json()
        assert body["error"]["code"] == "NOT_FOUND"

    def test_nonexistent_topic_lessons_returns_404(self, client):
        resp = client.get("/api/v1/topics/completely-missing-topic/lessons")
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "NOT_FOUND"


# ====================================================================
# Lesson Detail API Integration Tests
# ====================================================================


class TestLessonDetailApiIntegration:
    def test_get_published_lesson_detail(self, client, seeded_content):
        l1_id = seeded_content["lesson1_id"]
        resp = client.get(f"/api/v1/lessons/{l1_id}")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        body = resp.get_json()

        data = body["data"]
        assert data["id"] == l1_id
        assert data["topic_id"] == seeded_content["topic_pub_id"]
        assert data["version_id"] == seeded_content["v1_id"]
        assert data["version_number"] == 1
        assert data["title"] == "Hand Hygiene Essentials"
        assert data["learning_objectives"] == ["Identify key hand hygiene moments"]
        assert data["estimated_duration_minutes"] == 5

        # Check ordered cards
        assert len(data["cards"]) == 2
        card0 = data["cards"][0]
        assert card0["position"] == 0
        assert card0["card_type"] == "explanation"
        assert card0["content_blocks"][0]["body"] == "Always wash hands with clean water."

        card1 = data["cards"][1]
        assert card1["position"] == 1
        assert card1["card_type"] == "interaction"
        assert card1["interaction"]["interaction_type"] == "single_choice"
        assert card1["interaction"]["incorrect_behaviour"] == "retry"
        assert len(card1["interaction"]["options"]) == 2

        # Check sources
        assert len(data["sources"]) == 1
        src = data["sources"][0]
        assert src["id"] == seeded_content["source_id"]
        assert src["title"] == "WHO Global Handwashing Guidelines"
        assert src["publisher"] == "World Health Organization"
        assert src["url"] == "https://www.who.int/campaigns/world-hand-hygiene-day"
        assert src["publication_date"] == "2024-05-05"
        assert src["jurisdiction"] == "Global"
        # Confirm internal metadata_notes is NOT exposed!
        assert "metadata_notes" not in src

    def test_draft_only_lesson_returns_404(self, client, seeded_content):
        l2_id = seeded_content["lesson2_id"]
        resp = client.get(f"/api/v1/lessons/{l2_id}")
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "NOT_FOUND"

    def test_lesson_in_draft_topic_returns_404(self, client, seeded_content):
        l4_id = seeded_content["lesson4_id"]
        resp = client.get(f"/api/v1/lessons/{l4_id}")
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "NOT_FOUND"

    def test_nonexistent_lesson_returns_404(self, client):
        resp = client.get("/api/v1/lessons/nonexistent-lesson-id-0")
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "NOT_FOUND"
