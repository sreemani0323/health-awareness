"""Unit tests for domain object validation.

These tests exercise pure-Python domain objects and their ``validate()``
methods.  No NDB, no emulator, no network access.
"""

from __future__ import annotations

import copy
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


# ---------------------------------------------------------------------------
# Fixtures — valid baseline objects
# ---------------------------------------------------------------------------


@pytest.fixture()
def valid_topic() -> Topic:
    return Topic(
        topic_id="personal-hygiene",
        title="Personal Hygiene",
        url_slug="personal-hygiene",
        description="Learn about daily personal hygiene practices.",
        display_order=0,
        status=PublicationStatus.DRAFT,
    )


@pytest.fixture()
def valid_health_source() -> HealthSource:
    return HealthSource(
        source_id="who-hand-hygiene-2024",
        title="Hand Hygiene Guidelines",
        publisher="World Health Organization",
        url="https://www.who.int/hand-hygiene",
        publication_date=date(2024, 1, 15),
        access_date=date(2025, 6, 1),
        jurisdiction="Global",
    )


@pytest.fixture()
def valid_answer_option_correct() -> AnswerOption:
    return AnswerOption(
        option_id="opt-correct",
        label="Soap and water",
        is_correct=True,
        feedback="Correct!  Soap and water is the most effective method.",
    )


@pytest.fixture()
def valid_answer_option_wrong() -> AnswerOption:
    return AnswerOption(
        option_id="opt-wrong",
        label="Just water",
        is_correct=False,
        feedback="Not quite.  Plain water alone does not remove germs effectively.",
    )


@pytest.fixture()
def valid_interaction(valid_answer_option_correct, valid_answer_option_wrong):
    return SingleChoiceInteraction(
        interaction_type=InteractionType.SINGLE_CHOICE,
        question_prompt="What is the best way to clean your hands?",
        options=[valid_answer_option_correct, valid_answer_option_wrong],
        incorrect_behaviour=IncorrectBehaviour.RETRY,
    )


@pytest.fixture()
def valid_content_block() -> ContentBlock:
    return ContentBlock(block_type="text", body="Wash hands for at least 20 seconds.")


@pytest.fixture()
def valid_explanation_card(valid_content_block) -> LessonCard:
    return LessonCard(
        card_id="card-explain-01",
        position=0,
        card_type=CardType.EXPLANATION,
        content_blocks=[valid_content_block],
        source_ids=["who-hand-hygiene-2024"],
    )


@pytest.fixture()
def valid_interaction_card(valid_content_block, valid_interaction) -> LessonCard:
    return LessonCard(
        card_id="card-interact-01",
        position=1,
        card_type=CardType.INTERACTION,
        content_blocks=[valid_content_block],
        source_ids=[],
        interaction=valid_interaction,
    )


@pytest.fixture()
def valid_lesson_version(valid_explanation_card, valid_interaction_card) -> LessonVersion:
    return LessonVersion(
        version_id="hand-washing-v1",
        lesson_id="hand-washing-lesson",
        version_number=1,
        title="Hand Washing Basics",
        summary="Learn the correct technique for washing hands.",
        language="en",
        learning_objectives=["Understand when to wash hands", "Demonstrate correct technique"],
        estimated_duration_minutes=5,
        cards=[valid_explanation_card, valid_interaction_card],
        source_ids=["who-hand-hygiene-2024"],
        status=VersionStatus.DRAFT,
    )


@pytest.fixture()
def valid_lesson() -> Lesson:
    return Lesson(
        lesson_id="hand-washing-lesson",
        topic_id="personal-hygiene",
        display_order=0,
    )


@pytest.fixture()
def valid_review_record() -> ReviewRecord:
    return ReviewRecord(
        review_id="review-001",
        lesson_id="hand-washing-lesson",
        version_id="hand-washing-v1",
        editorial_status=ReviewStatus.APPROVED,
        health_content_status=ReviewStatus.PENDING,
        reviewer_role=ReviewerRole.EDITORIAL,
        review_date=date(2025, 6, 15),
        next_review_date=date(2026, 6, 15),
        notes="Looks good editorially.  Waiting for health review.",
    )


# ====================================================================
# Topic validation tests
# ====================================================================


class TestTopicValidation:
    def test_valid_topic_passes(self, valid_topic):
        valid_topic.validate()  # Should not raise.

    def test_empty_topic_id_fails(self, valid_topic):
        valid_topic.topic_id = ""
        with pytest.raises(ValueError, match="topic_id"):
            valid_topic.validate()

    def test_short_topic_id_fails(self, valid_topic):
        valid_topic.topic_id = "ab"  # Too short (< 3 chars).
        with pytest.raises(ValueError, match="topic_id"):
            valid_topic.validate()

    def test_uppercase_topic_id_fails(self, valid_topic):
        valid_topic.topic_id = "Personal-Hygiene"
        with pytest.raises(ValueError, match="topic_id"):
            valid_topic.validate()

    def test_empty_title_fails(self, valid_topic):
        valid_topic.title = ""
        with pytest.raises(ValueError, match="title"):
            valid_topic.validate()

    def test_title_too_long_fails(self, valid_topic):
        valid_topic.title = "x" * 201
        with pytest.raises(ValueError, match="title"):
            valid_topic.validate()

    def test_invalid_slug_fails(self, valid_topic):
        valid_topic.url_slug = "Has Spaces"
        with pytest.raises(ValueError, match="url_slug"):
            valid_topic.validate()

    def test_empty_description_fails(self, valid_topic):
        valid_topic.description = "   "
        with pytest.raises(ValueError, match="description"):
            valid_topic.validate()

    def test_negative_display_order_fails(self, valid_topic):
        valid_topic.display_order = -1
        with pytest.raises(ValueError, match="display_order"):
            valid_topic.validate()

    def test_topic_with_cover_image(self, valid_topic):
        valid_topic.cover_image_ref = "images/hygiene.png"
        valid_topic.cover_image_alt = "A person washing hands"
        valid_topic.validate()


# ====================================================================
# HealthSource validation tests
# ====================================================================


class TestHealthSourceValidation:
    def test_valid_source_passes(self, valid_health_source):
        valid_health_source.validate()

    def test_empty_source_id_fails(self, valid_health_source):
        valid_health_source.source_id = ""
        with pytest.raises(ValueError, match="source_id"):
            valid_health_source.validate()

    def test_invalid_url_fails(self, valid_health_source):
        valid_health_source.url = "not-a-url"
        with pytest.raises(ValueError, match="url"):
            valid_health_source.validate()

    def test_ftp_url_fails(self, valid_health_source):
        valid_health_source.url = "ftp://example.com/data"
        with pytest.raises(ValueError, match="url"):
            valid_health_source.validate()

    def test_empty_publisher_fails(self, valid_health_source):
        valid_health_source.publisher = ""
        with pytest.raises(ValueError, match="publisher"):
            valid_health_source.validate()


# ====================================================================
# AnswerOption validation tests
# ====================================================================


class TestAnswerOptionValidation:
    def test_valid_option_passes(self, valid_answer_option_correct):
        valid_answer_option_correct.validate()

    def test_empty_label_fails(self, valid_answer_option_correct):
        valid_answer_option_correct.label = ""
        with pytest.raises(ValueError, match="label"):
            valid_answer_option_correct.validate()

    def test_empty_feedback_fails(self, valid_answer_option_correct):
        valid_answer_option_correct.feedback = ""
        with pytest.raises(ValueError, match="feedback"):
            valid_answer_option_correct.validate()


# ====================================================================
# SingleChoiceInteraction validation tests
# ====================================================================


class TestInteractionValidation:
    def test_valid_interaction_passes(self, valid_interaction):
        valid_interaction.validate()

    def test_fewer_than_two_options_fails(self, valid_interaction):
        valid_interaction.options = valid_interaction.options[:1]
        with pytest.raises(ValueError, match="at least 2"):
            valid_interaction.validate()

    def test_no_correct_option_fails(self, valid_interaction):
        for opt in valid_interaction.options:
            opt.is_correct = False
        with pytest.raises(ValueError, match="Exactly one"):
            valid_interaction.validate()

    def test_multiple_correct_options_fails(self, valid_interaction):
        for opt in valid_interaction.options:
            opt.is_correct = True
        with pytest.raises(ValueError, match="Exactly one"):
            valid_interaction.validate()

    def test_duplicate_option_ids_fails(self, valid_interaction):
        valid_interaction.options[1].option_id = valid_interaction.options[0].option_id
        with pytest.raises(ValueError, match="Duplicate option_id"):
            valid_interaction.validate()

    def test_evaluate_correct(self, valid_interaction):
        is_correct, feedback = valid_interaction.evaluate("opt-correct")
        assert is_correct is True

    def test_evaluate_incorrect(self, valid_interaction):
        is_correct, feedback = valid_interaction.evaluate("opt-wrong")
        assert is_correct is False

    def test_evaluate_unknown_id_raises(self, valid_interaction):
        with pytest.raises(ValueError, match="Unknown option_id"):
            valid_interaction.evaluate("nonexistent")

    def test_multi_select_interaction(self):
        opts = [
            AnswerOption("opt-1", "Step 1", True, "Great 1"),
            AnswerOption("opt-2", "Step 2", True, "Great 2"),
            AnswerOption("opt-3", "Step 3", False, "Incorrect 3"),
        ]
        inter = SingleChoiceInteraction(
            interaction_type=InteractionType.MULTI_SELECT,
            question_prompt="Select all valid",
            options=opts,
            incorrect_behaviour=IncorrectBehaviour.RETRY,
        )
        inter.validate()
        # Evaluate correct multi select
        is_corr, fb = inter.evaluate(["opt-1", "opt-2"])
        assert is_corr is True
        # Evaluate partial or incorrect
        is_corr2, fb2 = inter.evaluate(["opt-1", "opt-3"])
        assert is_corr2 is False

    def test_arrange_steps_interaction(self):
        opts = [
            AnswerOption("step-1", "Wet", False, "Complete sequence"),
            AnswerOption("step-2", "Lather", False, "Complete sequence"),
            AnswerOption("step-3", "Rinse", False, "Complete sequence"),
        ]
        inter = SingleChoiceInteraction(
            interaction_type=InteractionType.ARRANGE_STEPS,
            question_prompt="Arrange in correct sequence",
            options=opts,
            incorrect_behaviour=IncorrectBehaviour.RETRY,
            correct_order=["step-1", "step-2", "step-3"],
        )
        inter.validate()
        is_corr, _ = inter.evaluate(["step-1", "step-2", "step-3"])
        assert is_corr is True
        is_corr_bad, _ = inter.evaluate(["step-3", "step-2", "step-1"])
        assert is_corr_bad is False


# ====================================================================
# ContentBlock validation tests
# ====================================================================


class TestContentBlockValidation:
    def test_valid_text_block(self, valid_content_block):
        valid_content_block.validate()

    def test_valid_heading_block(self):
        block = ContentBlock(block_type="heading", body="Introduction")
        block.validate()

    def test_valid_image_ref_block(self):
        block = ContentBlock(block_type="image_ref", body="images/diagram.png")
        block.validate()

    def test_valid_dialogue_block(self):
        block = ContentBlock(
            block_type="dialogue",
            body="Why are you still at the sink?",
            speaker="Meera",
            avatar="👩🏽",
            side="left",
        )
        block.validate()

    def test_valid_callout_and_takeaway_blocks(self):
        b1 = ContentBlock(block_type="callout", body="Remember this key fact")
        b1.validate()
        b2 = ContentBlock(block_type="key_takeaway", body="Action item today")
        b2.validate()

    def test_invalid_block_type_fails(self):
        block = ContentBlock(block_type="video", body="content")
        with pytest.raises(ValueError, match="Unknown content block_type"):
            block.validate()

    def test_empty_body_fails(self, valid_content_block):
        valid_content_block.body = ""
        with pytest.raises(ValueError, match="body"):
            valid_content_block.validate()


# ====================================================================
# LessonCard validation tests
# ====================================================================


class TestLessonCardValidation:
    def test_valid_explanation_card(self, valid_explanation_card):
        valid_explanation_card.validate()

    def test_valid_interaction_card(self, valid_interaction_card):
        valid_interaction_card.validate()

    def test_explanation_with_interaction_fails(self, valid_explanation_card, valid_interaction):
        valid_explanation_card.interaction = valid_interaction
        with pytest.raises(ValueError, match="must not include an interaction"):
            valid_explanation_card.validate()

    def test_interaction_without_interaction_fails(self, valid_content_block):
        card = LessonCard(
            card_id="card-bad",
            position=0,
            card_type=CardType.INTERACTION,
            content_blocks=[valid_content_block],
            source_ids=[],
            interaction=None,
        )
        with pytest.raises(ValueError, match="must include an interaction"):
            card.validate()

    def test_no_content_blocks_fails(self, valid_explanation_card):
        valid_explanation_card.content_blocks = []
        with pytest.raises(ValueError, match="at least one content block"):
            valid_explanation_card.validate()

    def test_negative_position_fails(self, valid_explanation_card):
        valid_explanation_card.position = -1
        with pytest.raises(ValueError, match="position"):
            valid_explanation_card.validate()


# ====================================================================
# LessonVersion validation tests
# ====================================================================


class TestLessonVersionValidation:
    def test_valid_version_passes(self, valid_lesson_version):
        valid_lesson_version.validate()

    def test_zero_version_number_fails(self, valid_lesson_version):
        valid_lesson_version.version_number = 0
        with pytest.raises(ValueError, match="version_number"):
            valid_lesson_version.validate()

    def test_unsupported_language_fails(self, valid_lesson_version):
        valid_lesson_version.language = "xx"
        with pytest.raises(ValueError, match="language"):
            valid_lesson_version.validate()

    def test_empty_objectives_fails(self, valid_lesson_version):
        valid_lesson_version.learning_objectives = []
        with pytest.raises(ValueError, match="At least one learning objective"):
            valid_lesson_version.validate()

    def test_too_many_objectives_fails(self, valid_lesson_version):
        valid_lesson_version.learning_objectives = ["obj"] * 21
        with pytest.raises(ValueError, match="At most"):
            valid_lesson_version.validate()

    def test_zero_duration_fails(self, valid_lesson_version):
        valid_lesson_version.estimated_duration_minutes = 0
        with pytest.raises(ValueError, match="estimated_duration_minutes"):
            valid_lesson_version.validate()

    def test_empty_cards_fails(self, valid_lesson_version):
        valid_lesson_version.cards = []
        with pytest.raises(ValueError, match="at least one card"):
            valid_lesson_version.validate()

    def test_duplicate_card_ids_fails(self, valid_lesson_version):
        valid_lesson_version.cards[1].card_id = valid_lesson_version.cards[0].card_id
        with pytest.raises(ValueError, match="Duplicate card_id"):
            valid_lesson_version.validate()

    def test_duplicate_card_positions_fails(self, valid_lesson_version):
        valid_lesson_version.cards[1].position = valid_lesson_version.cards[0].position
        with pytest.raises(ValueError, match="Duplicate card position"):
            valid_lesson_version.validate()

    def test_cards_round_trip_serialization(self, valid_lesson_version):
        """Verify cards_as_dicts / cards_from_dicts round-trips cleanly."""
        dicts = valid_lesson_version.cards_as_dicts()
        restored = LessonVersion.cards_from_dicts(dicts)
        assert len(restored) == len(valid_lesson_version.cards)
        for orig, rest in zip(valid_lesson_version.cards, restored):
            assert orig.card_id == rest.card_id
            assert orig.card_type == rest.card_type
            if orig.interaction:
                assert rest.interaction is not None
                assert len(rest.interaction.options) == len(orig.interaction.options)


# ====================================================================
# Lesson validation tests
# ====================================================================


class TestLessonValidation:
    def test_valid_lesson_passes(self, valid_lesson):
        valid_lesson.validate()

    def test_negative_display_order_fails(self, valid_lesson):
        valid_lesson.display_order = -1
        with pytest.raises(ValueError, match="display_order"):
            valid_lesson.validate()


# ====================================================================
# ReviewRecord validation tests
# ====================================================================


class TestReviewRecordValidation:
    def test_valid_review_passes(self, valid_review_record):
        valid_review_record.validate()

    def test_invalid_review_date_fails(self, valid_review_record):
        valid_review_record.review_date = "not-a-date"
        with pytest.raises(ValueError, match="review_date"):
            valid_review_record.validate()

    def test_empty_review_id_fails(self, valid_review_record):
        valid_review_record.review_id = ""
        with pytest.raises(ValueError, match="review_id"):
            valid_review_record.validate()
