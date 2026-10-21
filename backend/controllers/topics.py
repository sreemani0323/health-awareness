"""Controllers for Topic public endpoints."""

from __future__ import annotations

from flask import Response

from backend.controllers.base import BaseHandler
from backend.controllers.serializers import (
    serialize_lesson_summary,
    serialize_topic,
)
from backend.domain import domain_services
from backend.domain.domain_objects import PublicationStatus


class TopicListHandler(BaseHandler):
    """Endpoint A: List published topics.

    GET /api/v1/topics
    """

    def get(self) -> tuple[Response, int]:
        topics = domain_services.list_topics(status=PublicationStatus.PUBLISHED)
        data = [serialize_topic(t) for t in topics]
        return self.render_json(data)


class TopicLessonsHandler(BaseHandler):
    """Endpoint B: List published lessons within a topic.

    GET /api/v1/topics/<topic_id>/lessons
    """

    def get(self, topic_id: str) -> tuple[Response, int]:
        results = domain_services.get_published_lessons_for_topic(topic_id)
        if results is None:
            return self.render_error(
                code="NOT_FOUND",
                message=f"Topic '{topic_id}' was not found or is not published.",
                status_code=404,
            )
        data = [serialize_lesson_summary(lesson, version) for lesson, version in results]
        return self.render_json(data)


class TopicMasteryHandler(BaseHandler):
    """Endpoint: Retrieve topic mastery challenge for a topic.

    GET /api/v1/topics/<topic_id>/mastery
    """

    def get(self, topic_id: str) -> tuple[Response, int]:
        challenge = domain_services.get_topic_mastery_challenge(topic_id)
        if challenge is None:
            return self.render_error(
                code="NOT_FOUND",
                message=f"Topic mastery challenge for '{topic_id}' was not found.",
                status_code=404,
            )
        return self.render_json(challenge)
