"""Integration tests for storage models and domain services.

These tests require:
- The local Datastore emulator running on 127.0.0.1:8080.
- DATASTORE_EMULATOR_HOST set appropriately.

Each test operates inside an NDB context and creates entities with unique IDs
(UUID-suffixed) to avoid collisions between test runs.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

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
    ReviewerRole,
    ReviewRecord,
    ReviewStatus,
    SingleChoiceInteraction,
    Topic,
    VersionStatus,
)
from backend.domain.domain_services import (
    create_health_source,
    create_lesson,
    create_lesson_version,
    create_review_record,
    create_topic,
    delete_health_source,
    delete_lesson,
    delete_topic,
    get_health_source,
    get_lesson,
    get_lesson_version,
    get_review_record,
    get_topic,
    list_health_sources,
    list_lessons_by_topic,
    list_reviews_for_lesson,
    list_topics,
    publish_lesson_version,
    update_topic,
)
from backend.storage.storage_models import (
    HealthSourceModel,
    LessonModel,
    LessonVersionModel,
    ReviewRecordModel,
    TopicModel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid(prefix: str = "") -> str:
    """Generate a unique, valid domain ID for test isolation."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}" if prefix else f"t-{uuid.uuid4().hex[:12]}"


def _make_topic(**overrides) -> Topic:
    uid = _uid("topic")
    defaults = dict(
        topic_id=uid,
        title="Test Topic",
        url_slug=uid,
        description="A test topic for integration tests.",
        display_order=0,
        status=PublicationStatus.DRAFT,
    )
    defaults.update(overrides)
    return Topic(**defaults)


def _make_lesson(topic_id: str, **overrides) -> Lesson:
    uid = _uid("lesson")
    defaults = dict(
        lesson_id=uid,
        topic_id=topic_id,
        display_order=0,
    )
    defaults.update(overrides)
    return Lesson(**defaults)


def _make_health_source(**overrides) -> HealthSource:
    uid = _uid("source")
    defaults = dict(
        source_id=uid,
        title="WHO Hand Hygiene",
        publisher="WHO",
        url="https://www.who.int/hand-hygiene",
        publication_date=date(2024, 1, 1),
        access_date=date(2025, 1, 1),
    )
    defaults.update(overrides)
    return HealthSource(**defaults)


def _make_content_block() -> ContentBlock:
    return ContentBlock(block_type="text", body="Example content for testing.")


def _make_explanation_card(position: int = 0) -> LessonCard:
    return LessonCard(
        card_id=_uid("card"),
        position=position,
        card_type=CardType.EXPLANATION,
        content_blocks=[_make_content_block()],
        source_ids=[],
    )


def _make_interaction_card(position: int = 1) -> LessonCard:
    return LessonCard(
        card_id=_uid("card"),
        position=position,
        card_type=CardType.INTERACTION,
        content_blocks=[_make_content_block()],
        source_ids=[],
        interaction=SingleChoiceInteraction(
            interaction_type=InteractionType.SINGLE_CHOICE,
            question_prompt="What is the correct answer?",
            options=[
                AnswerOption(
                    option_id="opt-a",
                    label="Option A",
                    is_correct=True,
                    feedback="Correct!",
                ),
                AnswerOption(
                    option_id="opt-b",
                    label="Option B",
                    is_correct=False,
                    feedback="Try again.",
                ),
            ],
            incorrect_behaviour=IncorrectBehaviour.RETRY,
        ),
    )


def _make_lesson_version(lesson_id: str, **overrides) -> LessonVersion:
    uid = _uid("version")
    defaults = dict(
        version_id=uid,
        lesson_id=lesson_id,
        version_number=1,
        title="Test Lesson Version",
        summary="A test lesson version.",
        language="en",
        learning_objectives=["Objective one"],
        estimated_duration_minutes=5,
        cards=[_make_explanation_card(0), _make_interaction_card(1)],
        source_ids=[],
        status=VersionStatus.DRAFT,
    )
    defaults.update(overrides)
    return LessonVersion(**defaults)


def _make_review_record(lesson_id: str, version_id: str, **overrides) -> ReviewRecord:
    uid = _uid("review")
    defaults = dict(
        review_id=uid,
        lesson_id=lesson_id,
        version_id=version_id,
        editorial_status=ReviewStatus.APPROVED,
        health_content_status=ReviewStatus.PENDING,
        reviewer_role=ReviewerRole.EDITORIAL,
        review_date=date(2025, 7, 1),
    )
    defaults.update(overrides)
    return ReviewRecord(**defaults)


# ====================================================================
# Topic storage + service tests
# ====================================================================


class TestTopicIntegration:
    def test_create_and_get(self, ndb_ctx):
        topic = _make_topic()
        created = create_topic(topic)
        assert created.topic_id == topic.topic_id
        assert created.title == topic.title

        fetched = get_topic(topic.topic_id)
        assert fetched is not None
        assert fetched.title == topic.title

    def test_duplicate_id_raises(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        with pytest.raises(ValueError, match="already exists"):
            create_topic(topic)

    def test_update_topic(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        topic.title = "Updated Title"
        updated = update_topic(topic)
        assert updated.title == "Updated Title"

    def test_update_nonexistent_raises(self, ndb_ctx):
        topic = _make_topic()
        with pytest.raises(ValueError, match="not found"):
            update_topic(topic)

    def test_delete_topic(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        delete_topic(topic.topic_id)
        assert get_topic(topic.topic_id) is None

    def test_delete_nonexistent_raises(self, ndb_ctx):
        with pytest.raises(ValueError, match="not found"):
            delete_topic("nonexistent-id-000")

    def test_list_topics(self, ndb_ctx):
        t1 = _make_topic(display_order=1)
        t2 = _make_topic(display_order=0)
        create_topic(t1)
        create_topic(t2)
        # list_topics returns ordered by display_order;
        # we just verify both are returned.
        all_topics = list_topics()
        ids = {t.topic_id for t in all_topics}
        assert t1.topic_id in ids
        assert t2.topic_id in ids

    def test_list_topics_filtered_by_status(self, ndb_ctx):
        draft = _make_topic(status=PublicationStatus.DRAFT)
        published = _make_topic(status=PublicationStatus.PUBLISHED)
        create_topic(draft)
        create_topic(published)
        drafts = list_topics(status=PublicationStatus.DRAFT)
        draft_ids = {t.topic_id for t in drafts}
        assert draft.topic_id in draft_ids
        assert published.topic_id not in draft_ids

    def test_storage_model_round_trip(self, ndb_ctx):
        """Verify NDB model <-> domain object conversion is lossless."""
        topic = _make_topic(
            cover_image_ref="img/test.png", cover_image_alt="Test image"
        )
        model = TopicModel.from_domain(topic)
        model.put()
        restored = TopicModel.get_by_id(topic.topic_id).to_domain()
        assert restored.topic_id == topic.topic_id
        assert restored.cover_image_ref == "img/test.png"
        assert restored.cover_image_alt == "Test image"


# ====================================================================
# Lesson storage + service tests
# ====================================================================


class TestLessonIntegration:
    def test_create_and_get(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        lesson = _make_lesson(topic.topic_id)
        created = create_lesson(lesson)
        assert created.lesson_id == lesson.lesson_id

        fetched = get_lesson(lesson.lesson_id)
        assert fetched is not None
        assert fetched.topic_id == topic.topic_id

    def test_create_without_parent_topic_raises(self, ndb_ctx):
        lesson = _make_lesson("nonexistent-topic-0")
        with pytest.raises(ValueError, match="Parent topic"):
            create_lesson(lesson)

    def test_duplicate_lesson_raises(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        lesson = _make_lesson(topic.topic_id)
        create_lesson(lesson)
        with pytest.raises(ValueError, match="already exists"):
            create_lesson(lesson)

    def test_list_by_topic(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        l1 = _make_lesson(topic.topic_id, display_order=1)
        l2 = _make_lesson(topic.topic_id, display_order=0)
        create_lesson(l1)
        create_lesson(l2)
        lessons = list_lessons_by_topic(topic.topic_id)
        ids = [ll.lesson_id for ll in lessons]
        assert l1.lesson_id in ids
        assert l2.lesson_id in ids

    def test_delete_lesson(self, ndb_ctx):
        topic = _make_topic()
        create_topic(topic)
        lesson = _make_lesson(topic.topic_id)
        create_lesson(lesson)
        delete_lesson(lesson.lesson_id)
        assert get_lesson(lesson.lesson_id) is None


# ====================================================================
# LessonVersion + publication logic tests
# ====================================================================


class TestLessonVersionIntegration:
    def _setup_topic_and_lesson(self):
        topic = _make_topic()
        create_topic(topic)
        lesson = _make_lesson(topic.topic_id)
        create_lesson(lesson)
        return topic, lesson

    def test_create_and_get_version(self, ndb_ctx):
        _, lesson = self._setup_topic_and_lesson()
        version = _make_lesson_version(lesson.lesson_id)
        created = create_lesson_version(version)
        assert created.version_id == version.version_id
        assert created.status == VersionStatus.DRAFT

        fetched = get_lesson_version(version.version_id)
        assert fetched is not None
        assert fetched.title == version.title

    def test_create_non_draft_raises(self, ndb_ctx):
        _, lesson = self._setup_topic_and_lesson()
        version = _make_lesson_version(
            lesson.lesson_id, status=VersionStatus.PUBLISHED
        )
        with pytest.raises(ValueError, match="DRAFT"):
            create_lesson_version(version)

    def test_create_without_parent_lesson_raises(self, ndb_ctx):
        version = _make_lesson_version("nonexistent-lesson-0")
        with pytest.raises(ValueError, match="Parent lesson"):
            create_lesson_version(version)

    def test_create_sets_draft_pointer(self, ndb_ctx):
        _, lesson = self._setup_topic_and_lesson()
        version = _make_lesson_version(lesson.lesson_id)
        create_lesson_version(version)
        updated_lesson = get_lesson(lesson.lesson_id)
        assert updated_lesson.draft_version_id == version.version_id

    def test_publish_version(self, ndb_ctx):
        _, lesson = self._setup_topic_and_lesson()
        version = _make_lesson_version(lesson.lesson_id)
        create_lesson_version(version)
        published = publish_lesson_version(version.version_id)
        assert published.status == VersionStatus.PUBLISHED

        updated_lesson = get_lesson(lesson.lesson_id)
        assert updated_lesson.published_version_id == version.version_id
        assert updated_lesson.draft_version_id is None

    def test_publish_archives_previous_version(self, ndb_ctx):
        _, lesson = self._setup_topic_and_lesson()
        v1 = _make_lesson_version(lesson.lesson_id, version_number=1)
        create_lesson_version(v1)
        publish_lesson_version(v1.version_id)

        v2 = _make_lesson_version(lesson.lesson_id, version_number=2)
        create_lesson_version(v2)
        publish_lesson_version(v2.version_id)

        # v1 should now be ARCHIVED.
        archived = get_lesson_version(v1.version_id)
        assert archived.status == VersionStatus.ARCHIVED

        # v2 is the current published version.
        current = get_lesson_version(v2.version_id)
        assert current.status == VersionStatus.PUBLISHED

        lesson_now = get_lesson(lesson.lesson_id)
        assert lesson_now.published_version_id == v2.version_id

    def test_publish_already_published_raises(self, ndb_ctx):
        _, lesson = self._setup_topic_and_lesson()
        version = _make_lesson_version(lesson.lesson_id)
        create_lesson_version(version)
        publish_lesson_version(version.version_id)
        with pytest.raises(ValueError, match="Only DRAFT"):
            publish_lesson_version(version.version_id)

    def test_cards_survive_storage_round_trip(self, ndb_ctx):
        """Cards with nested interactions persist correctly through NDB."""
        _, lesson = self._setup_topic_and_lesson()
        version = _make_lesson_version(lesson.lesson_id)
        create_lesson_version(version)
        fetched = get_lesson_version(version.version_id)
        assert len(fetched.cards) == 2
        interaction_card = [c for c in fetched.cards if c.card_type == CardType.INTERACTION][0]
        assert interaction_card.interaction is not None
        assert len(interaction_card.interaction.options) == 2


# ====================================================================
# HealthSource storage + service tests
# ====================================================================


class TestHealthSourceIntegration:
    def test_create_and_get(self, ndb_ctx):
        source = _make_health_source()
        created = create_health_source(source)
        assert created.source_id == source.source_id

        fetched = get_health_source(source.source_id)
        assert fetched is not None
        assert fetched.publisher == "WHO"

    def test_duplicate_raises(self, ndb_ctx):
        source = _make_health_source()
        create_health_source(source)
        with pytest.raises(ValueError, match="already exists"):
            create_health_source(source)

    def test_list_sources(self, ndb_ctx):
        s1 = _make_health_source()
        s2 = _make_health_source()
        create_health_source(s1)
        create_health_source(s2)
        all_sources = list_health_sources()
        ids = {s.source_id for s in all_sources}
        assert s1.source_id in ids
        assert s2.source_id in ids

    def test_delete_source(self, ndb_ctx):
        source = _make_health_source()
        create_health_source(source)
        delete_health_source(source.source_id)
        assert get_health_source(source.source_id) is None

    def test_storage_round_trip_dates(self, ndb_ctx):
        source = _make_health_source(
            publication_date=date(2023, 6, 15),
            access_date=date(2025, 3, 20),
            jurisdiction="USA",
            metadata_notes="Updated guidelines.",
        )
        create_health_source(source)
        fetched = get_health_source(source.source_id)
        assert fetched.publication_date == date(2023, 6, 15)
        assert fetched.access_date == date(2025, 3, 20)
        assert fetched.jurisdiction == "USA"
        assert fetched.metadata_notes == "Updated guidelines."


# ====================================================================
# ReviewRecord storage + service tests
# ====================================================================


class TestReviewRecordIntegration:
    def _setup_full_chain(self):
        """Create topic -> lesson -> version chain."""
        topic = _make_topic()
        create_topic(topic)
        lesson = _make_lesson(topic.topic_id)
        create_lesson(lesson)
        version = _make_lesson_version(lesson.lesson_id)
        create_lesson_version(version)
        return topic, lesson, version

    def test_create_and_get_review(self, ndb_ctx):
        _, lesson, version = self._setup_full_chain()
        review = _make_review_record(lesson.lesson_id, version.version_id)
        created = create_review_record(review)
        assert created.review_id == review.review_id

        fetched = get_review_record(review.review_id)
        assert fetched is not None
        assert fetched.editorial_status == ReviewStatus.APPROVED

    def test_duplicate_review_raises(self, ndb_ctx):
        _, lesson, version = self._setup_full_chain()
        review = _make_review_record(lesson.lesson_id, version.version_id)
        create_review_record(review)
        with pytest.raises(ValueError, match="already exists"):
            create_review_record(review)

    def test_list_reviews_for_lesson(self, ndb_ctx):
        _, lesson, version = self._setup_full_chain()
        r1 = _make_review_record(lesson.lesson_id, version.version_id)
        r2 = _make_review_record(lesson.lesson_id, version.version_id)
        create_review_record(r1)
        create_review_record(r2)
        reviews = list_reviews_for_lesson(lesson.lesson_id)
        ids = {r.review_id for r in reviews}
        assert r1.review_id in ids
        assert r2.review_id in ids

    def test_review_round_trip_dates(self, ndb_ctx):
        _, lesson, version = self._setup_full_chain()
        review = _make_review_record(
            lesson.lesson_id,
            version.version_id,
            review_date=date(2025, 8, 1),
            next_review_date=date(2026, 8, 1),
            notes="Comprehensive review.",
        )
        create_review_record(review)
        fetched = get_review_record(review.review_id)
        assert fetched.review_date == date(2025, 8, 1)
        assert fetched.next_review_date == date(2026, 8, 1)
        assert fetched.notes == "Comprehensive review."
