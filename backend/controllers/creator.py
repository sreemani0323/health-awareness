"""Creator Studio API controllers.

Provides CRUD + workflow endpoints for the authoring and review pipeline.
All endpoints require authentication; write operations require CONTRIBUTOR
or ADMIN role; review operations require REVIEWER or ADMIN role.
"""

from __future__ import annotations

import dataclasses
from datetime import date
from typing import Any

from flask import Response, request

from backend.controllers.auth import auth_required, get_current_user, role_required
from backend.controllers.base import BaseHandler
from backend.controllers.serializers import (
    serialize_card,
    serialize_health_source,
    serialize_topic,
)
from backend.domain import domain_services
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
    UserRole,
    VersionStatus,
)


# ---------------------------------------------------------------------------
# Serializers for creator context (include status, drafts, etc.)
# ---------------------------------------------------------------------------


def _serialize_topic_full(topic: Topic) -> dict[str, Any]:
    """Serialize a topic with all fields for creator view."""
    d = serialize_topic(topic)
    d["status"] = topic.status.value
    return d


def _serialize_lesson_full(lesson) -> dict[str, Any]:
    """Serialize a lesson shell for creator view with rich chapter information."""
    active_version_id = lesson.draft_version_id or lesson.published_version_id
    version_title = None
    version_summary = None
    version_status = "no_version"
    card_count = 0
    version_number = 1
    review_feedback = None
    if active_version_id:
        v = domain_services.get_lesson_version(active_version_id)
        if v:
            version_title = v.title
            version_summary = v.summary
            version_status = v.status.value
            card_count = len(v.cards)
            version_number = v.version_number
            review_feedback = v.review_feedback

    default_title = lesson.lesson_id.replace("lesson-", "").replace("-", " ").title()

    return {
        "id": lesson.lesson_id,
        "topic_id": lesson.topic_id,
        "display_order": lesson.display_order,
        "published_version_id": lesson.published_version_id,
        "draft_version_id": lesson.draft_version_id,
        "title": version_title or default_title,
        "summary": version_summary or "",
        "status": version_status,
        "card_count": card_count,
        "version_number": version_number,
        "review_feedback": review_feedback,
    }


def _serialize_version_full(version) -> dict[str, Any]:
    """Serialize a lesson version with all fields for creator view."""
    sorted_cards = sorted(version.cards, key=lambda c: c.position)
    return {
        "id": version.version_id,
        "lesson_id": version.lesson_id,
        "version_number": version.version_number,
        "title": version.title,
        "summary": version.summary,
        "language": version.language,
        "learning_objectives": list(version.learning_objectives),
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "status": version.status.value,
        "cards": [serialize_card(card) for card in sorted_cards],
        "source_ids": list(version.source_ids),
        "author_id": version.author_id,
        "submitted_by": version.submitted_by,
        "review_feedback": version.review_feedback,
    }


def _parse_cards_from_json(cards_data: list[dict]) -> list[LessonCard]:
    """Parse card data from JSON request body into domain objects."""
    cards = []
    for cd in cards_data:
        blocks = [ContentBlock(block_type=b["block_type"], body=b["body"])
                  for b in cd.get("content_blocks", [])]

        interaction = None
        if cd.get("interaction"):
            idata = cd["interaction"]
            options = [
                AnswerOption(
                    option_id=o["id"],
                    label=o["label"],
                    is_correct=o["is_correct"],
                    feedback=o["feedback"],
                )
                for o in idata.get("options", [])
            ]
            interaction = SingleChoiceInteraction(
                interaction_type=InteractionType(idata.get("interaction_type", "single_choice")),
                question_prompt=idata["question_prompt"],
                options=options,
                incorrect_behaviour=IncorrectBehaviour(idata.get("incorrect_behaviour", "retry")),
            )

        cards.append(LessonCard(
            card_id=cd["id"],
            position=cd["position"],
            card_type=CardType(cd["card_type"]),
            content_blocks=blocks,
            source_ids=cd.get("source_ids", []),
            interaction=interaction,
        ))
    return cards


# ---------------------------------------------------------------------------
# Topic CRUD
# ---------------------------------------------------------------------------


class CreatorTopicListHandler(BaseHandler):
    """GET/POST /api/v1/creator/topics"""

    decorators = [auth_required]

    def get(self) -> tuple[Response, int]:
        """List all topics (any status) for the creator dashboard."""
        topics = domain_services.list_all_topics()
        data = [_serialize_topic_full(t) for t in topics]
        return self.render_json(data)

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def post(self) -> tuple[Response, int]:
        """Create a new draft topic."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        try:
            topic = Topic(
                topic_id=body["id"],
                title=body["title"],
                url_slug=body["slug"],
                description=body["description"],
                display_order=body.get("display_order", 0),
                status=PublicationStatus.DRAFT,
                cover_image_ref=body.get("cover_image_ref"),
                cover_image_alt=body.get("cover_image_alt"),
            )
            created = domain_services.create_topic(topic)
            return self.render_json(_serialize_topic_full(created), status_code=201)
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


class CreatorTopicDetailHandler(BaseHandler):
    """PUT /api/v1/creator/topics/<topic_id>"""

    decorators = [auth_required]

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def put(self, topic_id: str) -> tuple[Response, int]:
        """Update an existing topic."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        try:
            existing = domain_services.get_topic(topic_id)
            if existing is None:
                return self.render_error("NOT_FOUND", f"Topic '{topic_id}' not found.", 404)

            topic = Topic(
                topic_id=topic_id,
                title=body.get("title", existing.title),
                url_slug=body.get("slug", existing.url_slug),
                description=body.get("description", existing.description),
                display_order=body.get("display_order", existing.display_order),
                status=PublicationStatus(body.get("status", existing.status.value)),
                cover_image_ref=body.get("cover_image_ref", existing.cover_image_ref),
                cover_image_alt=body.get("cover_image_alt", existing.cover_image_alt),
            )
            updated = domain_services.update_topic(topic)
            return self.render_json(_serialize_topic_full(updated))
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)

    def get(self, topic_id: str) -> tuple[Response, int]:
        """Get a single topic with full details."""
        topic = domain_services.get_topic(topic_id)
        if topic is None:
            return self.render_error("NOT_FOUND", f"Topic '{topic_id}' not found.", 404)
        return self.render_json(_serialize_topic_full(topic))


# ---------------------------------------------------------------------------
# Lesson CRUD
# ---------------------------------------------------------------------------


class CreatorTopicLessonsHandler(BaseHandler):
    """GET/POST /api/v1/creator/topics/<topic_id>/lessons"""

    decorators = [auth_required]

    def get(self, topic_id: str) -> tuple[Response, int]:
        """List all lessons for a topic (any status)."""
        lessons = domain_services.list_lessons_by_topic(topic_id)
        data = [_serialize_lesson_full(l) for l in lessons]
        return self.render_json(data)

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def post(self, topic_id: str) -> tuple[Response, int]:
        """Create a new lesson/chapter under a topic and initialize a draft version."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        lesson_id = body.get("id")
        if not lesson_id:
            title_slug = body.get("title", "new-chapter").strip().lower().replace(" ", "-")
            import uuid
            lesson_id = f"lesson-{title_slug[:30]}-{uuid.uuid4().hex[:4]}"

        # Calculate display_order if not provided
        display_order = body.get("display_order")
        if display_order is None:
            existing_lessons = domain_services.list_lessons_by_topic(topic_id)
            display_order = (max([l.display_order for l in existing_lessons] or [0])) + 1

        try:
            lesson = Lesson(
                lesson_id=lesson_id,
                topic_id=topic_id,
                display_order=display_order,
            )
            created = domain_services.create_lesson(lesson)

            # Auto-initialize initial draft version with title and card outline
            initial_title = body.get("title") or lesson_id.replace("lesson-", "").replace("-", " ").title()
            initial_summary = body.get("summary", "")
            current_user = get_current_user()
            author_id = current_user.user_id if current_user else None

            sample_card = LessonCard(
                card_id=f"card-{lesson_id}-1",
                position=1,
                card_type=CardType.EXPLANATION,
                content_blocks=[
                    ContentBlock(block_type="heading", body=initial_title),
                    ContentBlock(
                        block_type="text",
                        body=initial_summary or "Introduction and overview of this chapter. Edit this card to begin creating your curriculum.",
                    ),
                ],
                source_ids=[],
            )
            version = LessonVersion(
                version_id=f"ver-{lesson_id}-v1",
                lesson_id=lesson_id,
                version_number=1,
                title=initial_title,
                summary=initial_summary or f"Core curriculum for {initial_title}",
                language=body.get("language", "en"),
                learning_objectives=[f"Understand key concepts of {initial_title}"],
                estimated_duration_minutes=5,
                cards=[sample_card],
                source_ids=[],
                status=VersionStatus.DRAFT,
                author_id=author_id,
            )
            domain_services.create_lesson_version(version)

            # Refresh lesson shell to include version pointers
            reloaded_lesson = domain_services.get_lesson(lesson_id) or created
            return self.render_json(_serialize_lesson_full(reloaded_lesson), status_code=201)
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


class CreatorLessonDetailHandler(BaseHandler):
    """GET/PUT/DELETE /api/v1/creator/lessons/<lesson_id>"""

    decorators = [auth_required]

    def get(self, lesson_id: str) -> tuple[Response, int]:
        """Get chapter details."""
        lesson = domain_services.get_lesson(lesson_id)
        if not lesson:
            return self.render_error("NOT_FOUND", f"Lesson '{lesson_id}' not found.", 404)
        return self.render_json(_serialize_lesson_full(lesson))

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def put(self, lesson_id: str) -> tuple[Response, int]:
        """Update chapter attributes, such as display_order."""
        body = request.get_json(silent=True) or {}
        lesson = domain_services.get_lesson(lesson_id)
        if not lesson:
            return self.render_error("NOT_FOUND", f"Lesson '{lesson_id}' not found.", 404)

        try:
            display_order = body.get("display_order", lesson.display_order)
            topic_id = body.get("topic_id", lesson.topic_id)
            updated_lesson = Lesson(
                lesson_id=lesson.lesson_id,
                topic_id=topic_id,
                display_order=int(display_order),
                published_version_id=lesson.published_version_id,
                draft_version_id=lesson.draft_version_id,
            )
            updated = domain_services.update_lesson(updated_lesson)
            return self.render_json(_serialize_lesson_full(updated))
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def delete(self, lesson_id: str) -> tuple[Response, int]:
        """Delete an unpublished draft chapter."""
        lesson = domain_services.get_lesson(lesson_id)
        if not lesson:
            return self.render_error("NOT_FOUND", f"Lesson '{lesson_id}' not found.", 404)

        if lesson.published_version_id:
            return self.render_error(
                "FORBIDDEN",
                "Cannot delete a chapter that has published content.",
                403,
            )

        domain_services.delete_lesson(lesson_id)
        return self.render_json({"deleted": True, "message": f"Chapter '{lesson_id}' deleted successfully."})


# ---------------------------------------------------------------------------
# LessonVersion CRUD + Workflow
# ---------------------------------------------------------------------------


class CreatorVersionListHandler(BaseHandler):
    """POST /api/v1/creator/lessons/<lesson_id>/versions"""

    decorators = [auth_required]

    def get(self, lesson_id: str) -> tuple[Response, int]:
        """List versions for a lesson filtered by user role and ownership."""
        current_user = get_current_user()
        versions = domain_services.list_versions_for_lesson(lesson_id)

        if current_user and current_user.role == UserRole.CONTRIBUTOR:
            # Contributors see versions they authored, plus published or archived history
            versions = [
                v for v in versions
                if v.author_id == current_user.user_id
                or v.status in (VersionStatus.PUBLISHED, VersionStatus.ARCHIVED)
            ]
        elif current_user and current_user.role == UserRole.REVIEWER:
            # Reviewers see submitted versions awaiting review, published/archived versions, and their own drafts
            versions = [
                v for v in versions
                if v.status in (VersionStatus.SUBMITTED_FOR_REVIEW, VersionStatus.PUBLISHED, VersionStatus.ARCHIVED)
                or v.author_id == current_user.user_id
            ]

        data = [_serialize_version_full(v) for v in versions]
        return self.render_json(data)

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def post(self, lesson_id: str) -> tuple[Response, int]:
        """Create a new draft version stamped with the author's user ID."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        current_user = get_current_user()
        author_id = current_user.user_id if current_user else None

        try:
            cards = _parse_cards_from_json(body.get("cards", []))
            version = LessonVersion(
                version_id=body["id"],
                lesson_id=lesson_id,
                version_number=body.get("version_number", 1),
                title=body["title"],
                summary=body["summary"],
                language=body.get("language", "en"),
                learning_objectives=body.get("learning_objectives", []),
                estimated_duration_minutes=body.get("estimated_duration_minutes", 5),
                cards=cards,
                source_ids=body.get("source_ids", []),
                status=VersionStatus.DRAFT,
                author_id=author_id,
            )
            created = domain_services.create_lesson_version(version)
            return self.render_json(_serialize_version_full(created), status_code=201)
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


class CreatorVersionDetailHandler(BaseHandler):
    """GET/PUT /api/v1/creator/versions/<version_id>"""

    decorators = [auth_required]

    def get(self, version_id: str) -> tuple[Response, int]:
        """Get a version with full detail, enforcing ownership and review boundaries."""
        version = domain_services.get_lesson_version(version_id)
        if version is None:
            return self.render_error("NOT_FOUND", f"Version '{version_id}' not found.", 404)

        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        # Enforce draft privacy: only the author or an admin can access unsubmitted drafts
        if version.status == VersionStatus.DRAFT:
            if current_user.role != UserRole.ADMIN and version.author_id and version.author_id != current_user.user_id:
                return self.render_error(
                    "FORBIDDEN",
                    "You are not authorized to view this draft version.",
                    403,
                )
        # Enforce review boundary: submitted versions can only be viewed by author, reviewers, or admins
        elif version.status == VersionStatus.SUBMITTED_FOR_REVIEW:
            if (
                current_user.role not in (UserRole.REVIEWER, UserRole.ADMIN)
                and version.author_id
                and version.author_id != current_user.user_id
            ):
                return self.render_error(
                    "FORBIDDEN",
                    "You are not authorized to view this submitted version.",
                    403,
                )

        sources = domain_services.get_health_sources_by_ids(version.source_ids)
        data = _serialize_version_full(version)
        data["sources"] = [serialize_health_source(s) for s in sources]
        return self.render_json(data)

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def put(self, version_id: str) -> tuple[Response, int]:
        """Update a draft version. Enforces ownership and DRAFT status immutability."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        existing = domain_services.get_lesson_version(version_id)
        if existing is None:
            return self.render_error("NOT_FOUND", f"Version '{version_id}' not found.", 404)

        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        # Ownership check: contributors can only modify their own drafts
        if current_user.role != UserRole.ADMIN and existing.author_id and existing.author_id != current_user.user_id:
            return self.render_error(
                "FORBIDDEN",
                "You are not authorized to modify this draft version.",
                403,
            )

        # Immutability check: only DRAFT versions can be modified
        if existing.status != VersionStatus.DRAFT:
            return self.render_error(
                "FORBIDDEN",
                f"Cannot edit version in '{existing.status.value}' status. Only drafts can be edited.",
                403,
            )

        try:
            cards = _parse_cards_from_json(body.get("cards", []))
            version = LessonVersion(
                version_id=version_id,
                lesson_id=existing.lesson_id,
                version_number=existing.version_number,
                title=body.get("title", existing.title),
                summary=body.get("summary", existing.summary),
                language=body.get("language", existing.language),
                learning_objectives=body.get("learning_objectives", list(existing.learning_objectives)),
                estimated_duration_minutes=body.get("estimated_duration_minutes", existing.estimated_duration_minutes),
                cards=cards if body.get("cards") else existing.cards,
                source_ids=body.get("source_ids", list(existing.source_ids)),
                status=existing.status,
                author_id=existing.author_id,
                submitted_by=existing.submitted_by,
            )
            updated = domain_services.update_lesson_version(version)
            return self.render_json(_serialize_version_full(updated))
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


class CreatorSubmitHandler(BaseHandler):
    """POST /api/v1/creator/versions/<version_id>/submit"""

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def post(self, version_id: str) -> tuple[Response, int]:
        """Submit a draft version for review. Enforces author ownership."""
        existing = domain_services.get_lesson_version(version_id)
        if existing is None:
            return self.render_error("NOT_FOUND", f"Version '{version_id}' not found.", 404)

        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        # Ownership check: contributors can only submit their own drafts
        if current_user.role != UserRole.ADMIN and existing.author_id and existing.author_id != current_user.user_id:
            return self.render_error(
                "FORBIDDEN",
                "You are not authorized to submit this draft version.",
                403,
            )

        try:
            version = domain_services.submit_for_review(version_id, user_id=current_user.user_id)
            return self.render_json(_serialize_version_full(version))
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


class CreatorApproveHandler(BaseHandler):
    """POST /api/v1/creator/versions/<version_id>/approve"""

    @role_required(UserRole.REVIEWER, UserRole.ADMIN)
    def post(self, version_id: str) -> tuple[Response, int]:
        """Approve and publish a submitted version."""
        current_user = get_current_user()
        reviewer_id = current_user.user_id if current_user else None
        try:
            version = domain_services.approve_version(version_id, reviewer_id=reviewer_id)
            return self.render_json(_serialize_version_full(version))
        except ValueError as exc:
            msg = str(exc)
            if "Self-approval is forbidden" in msg:
                return self.render_error("FORBIDDEN", msg, 403)
            return self.render_error("BAD_REQUEST", msg, 400)


class CreatorRequestChangesHandler(BaseHandler):
    """POST /api/v1/creator/versions/<version_id>/request-changes"""

    @role_required(UserRole.REVIEWER, UserRole.ADMIN)
    def post(self, version_id: str) -> tuple[Response, int]:
        """Request changes on a submitted version."""
        body = request.get_json(silent=True) or {}
        notes = body.get("notes", "")
        try:
            version = domain_services.request_changes(version_id, notes)
            return self.render_json(_serialize_version_full(version))
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


# ---------------------------------------------------------------------------
# Review queue
# ---------------------------------------------------------------------------


class CreatorReviewQueueHandler(BaseHandler):
    """GET /api/v1/creator/reviews — List versions awaiting review."""

    @role_required(UserRole.REVIEWER, UserRole.ADMIN)
    def get(self) -> tuple[Response, int]:
        versions = domain_services.list_submitted_versions()
        data = [_serialize_version_full(v) for v in versions]
        return self.render_json(data)


# ---------------------------------------------------------------------------
# Health Sources CRUD for Creator
# ---------------------------------------------------------------------------


class CreatorSourceListHandler(BaseHandler):
    """GET/POST /api/v1/creator/sources"""

    decorators = [auth_required]

    def get(self) -> tuple[Response, int]:
        """List all health sources."""
        sources = domain_services.list_health_sources()
        data = [serialize_health_source(s) for s in sources]
        return self.render_json(data)

    @role_required(UserRole.CONTRIBUTOR, UserRole.ADMIN)
    def post(self) -> tuple[Response, int]:
        """Create a new health source."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        try:
            pub_date = None
            if body.get("publication_date"):
                pub_date = date.fromisoformat(body["publication_date"])

            access_dt = None
            if body.get("access_date"):
                access_dt = date.fromisoformat(body["access_date"])

            source = HealthSource(
                source_id=body["id"],
                title=body["title"],
                publisher=body["publisher"],
                url=body["url"],
                publication_date=pub_date,
                access_date=access_dt,
                jurisdiction=body.get("jurisdiction"),
                metadata_notes=body.get("metadata_notes"),
            )
            created = domain_services.create_health_source(source)
            return self.render_json(serialize_health_source(created), status_code=201)
        except (ValueError, KeyError) as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
