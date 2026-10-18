"""Controllers for Lesson public endpoints."""

from __future__ import annotations

from flask import Response

from backend.controllers.base import BaseHandler
from backend.controllers.serializers import serialize_lesson_detail
from backend.domain import domain_services


class LessonDetailHandler(BaseHandler):
    """Endpoint C: Retrieve a published lesson.

    GET /api/v1/lessons/<lesson_id>
    """

    def get(self, lesson_id: str) -> tuple[Response, int]:
        result = domain_services.get_published_lesson(lesson_id)
        if result is None:
            return self.render_error(
                code="NOT_FOUND",
                message=f"Lesson '{lesson_id}' was not found or is not published.",
                status_code=404,
            )

        lesson, version = result

        # Collect all referenced source IDs across version and cards
        source_ids = list(version.source_ids)
        for card in version.cards:
            for sid in card.source_ids:
                if sid not in source_ids:
                    source_ids.append(sid)

        sources = domain_services.get_health_sources_by_ids(source_ids)
        data = serialize_lesson_detail(lesson, version, sources)
        return self.render_json(data)
