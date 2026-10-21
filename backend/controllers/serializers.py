"""Serializers for public REST API responses.

Controls precisely which fields leave the backend to prevent leaking internal
domain fields, drafts, private review notes, or storage model attributes.
"""

from __future__ import annotations

from typing import Any

from backend.domain.domain_objects import (
    HealthSource,
    Lesson,
    LessonCard,
    LessonVersion,
    SingleChoiceInteraction,
    Topic,
)


def serialize_topic(topic: Topic) -> dict[str, Any]:
    """Serialize a Topic entity for public listing."""
    return {
        "id": topic.topic_id,
        "title": topic.title,
        "slug": topic.url_slug,
        "description": topic.description,
        "display_order": topic.display_order,
        "cover_image_ref": topic.cover_image_ref,
        "cover_image_alt": topic.cover_image_alt,
    }


def serialize_lesson_summary(lesson: Lesson, version: LessonVersion) -> dict[str, Any]:
    """Serialize a lesson summary for public topic lessons listing."""
    return {
        "id": lesson.lesson_id,
        "topic_id": lesson.topic_id,
        "title": version.title,
        "summary": version.summary,
        "language": version.language,
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "published_version_id": lesson.published_version_id,
        "display_order": lesson.display_order,
    }


def serialize_interaction(interaction: SingleChoiceInteraction) -> dict[str, Any]:
    """Serialize an educational interaction for lesson playback."""
    res = {
        "interaction_type": interaction.interaction_type.value,
        "question_prompt": interaction.question_prompt,
        "incorrect_behaviour": interaction.incorrect_behaviour.value,
        "options": [
            {
                "id": opt.option_id,
                "label": opt.label,
                "is_correct": opt.is_correct,
                "feedback": opt.feedback,
            }
            for opt in interaction.options
        ],
    }
    if interaction.correct_order is not None:
        res["correct_order"] = list(interaction.correct_order)
    if interaction.hint is not None:
        res["hint"] = interaction.hint
    if interaction.scene_description is not None:
        res["scene_description"] = interaction.scene_description
    return res


def serialize_card(card: LessonCard) -> dict[str, Any]:
    """Serialize an individual lesson card."""
    blocks = []
    for block in card.content_blocks:
        b: dict[str, Any] = {"block_type": block.block_type, "body": block.body}
        if block.speaker:
            b["speaker"] = block.speaker
        if block.avatar:
            b["avatar"] = block.avatar
        if block.side:
            b["side"] = block.side
        blocks.append(b)

    return {
        "id": card.card_id,
        "position": card.position,
        "card_type": card.card_type.value,
        "content_blocks": blocks,
        "source_ids": list(card.source_ids),
        "interaction": (
            serialize_interaction(card.interaction)
            if card.interaction is not None
            else None
        ),
    }


def serialize_health_source(source: HealthSource) -> dict[str, Any]:
    """Serialize public citation fields for a HealthSource.

    Explicitly excludes internal curation metadata_notes.
    """
    return {
        "id": source.source_id,
        "title": source.title,
        "publisher": source.publisher,
        "url": source.url,
        "publication_date": (
            source.publication_date.isoformat()
            if source.publication_date is not None
            else None
        ),
        "access_date": (
            source.access_date.isoformat()
            if source.access_date is not None
            else None
        ),
        "jurisdiction": source.jurisdiction,
    }


def serialize_lesson_detail(
    lesson: Lesson,
    version: LessonVersion,
    sources: list[HealthSource],
) -> dict[str, Any]:
    """Serialize complete public lesson detail including ordered cards and sources."""
    sorted_cards = sorted(version.cards, key=lambda c: c.position)
    return {
        "id": lesson.lesson_id,
        "topic_id": lesson.topic_id,
        "version_id": version.version_id,
        "version_number": version.version_number,
        "title": version.title,
        "summary": version.summary,
        "language": version.language,
        "learning_objectives": list(version.learning_objectives),
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "cards": [serialize_card(card) for card in sorted_cards],
        "sources": [serialize_health_source(s) for s in sources],
    }
