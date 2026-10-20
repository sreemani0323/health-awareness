"""NDB storage models for the Health Awareness application.

Each NDB Model class mirrors a domain object and provides ``to_domain()`` /
``from_domain()`` conversion methods so the domain layer stays free of
infrastructure concerns.

Structured card content and interaction data are stored as NDB ``JsonProperty``
fields because the schema is deeply nested and varies by card type.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from google.cloud import ndb

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
    ReviewRecord,
    ReviewerRole,
    ReviewStatus,
    SingleChoiceInteraction,
    Topic,
    User,
    UserRole,
    VersionStatus,
)


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------


class TopicModel(ndb.Model):
    """Persistent representation of a health-education topic."""

    title = ndb.StringProperty(required=True)
    url_slug = ndb.StringProperty(required=True)
    description = ndb.TextProperty(required=True)
    display_order = ndb.IntegerProperty(required=True)
    status = ndb.StringProperty(
        required=True, choices=[s.value for s in PublicationStatus]
    )
    cover_image_ref = ndb.StringProperty()
    cover_image_alt = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_domain(self) -> Topic:
        return Topic(
            topic_id=self.key.string_id(),
            title=self.title,
            url_slug=self.url_slug,
            description=self.description,
            display_order=self.display_order,
            status=PublicationStatus(self.status),
            cover_image_ref=self.cover_image_ref,
            cover_image_alt=self.cover_image_alt,
        )

    @classmethod
    def from_domain(cls, obj: Topic) -> "TopicModel":
        obj.validate()
        return cls(
            id=obj.topic_id,
            title=obj.title,
            url_slug=obj.url_slug,
            description=obj.description,
            display_order=obj.display_order,
            status=obj.status.value,
            cover_image_ref=obj.cover_image_ref,
            cover_image_alt=obj.cover_image_alt,
        )


# ---------------------------------------------------------------------------
# Lesson
# ---------------------------------------------------------------------------


class LessonModel(ndb.Model):
    """Persistent representation of a lesson shell.

    The lesson shell links to version entities and belongs to a topic.
    """

    topic_id = ndb.StringProperty(required=True)
    display_order = ndb.IntegerProperty(required=True)
    published_version_id = ndb.StringProperty()
    draft_version_id = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_domain(self) -> Lesson:
        return Lesson(
            lesson_id=self.key.string_id(),
            topic_id=self.topic_id,
            display_order=self.display_order,
            published_version_id=self.published_version_id,
            draft_version_id=self.draft_version_id,
        )

    @classmethod
    def from_domain(cls, obj: Lesson) -> "LessonModel":
        obj.validate()
        return cls(
            id=obj.lesson_id,
            topic_id=obj.topic_id,
            display_order=obj.display_order,
            published_version_id=obj.published_version_id,
            draft_version_id=obj.draft_version_id,
        )


# ---------------------------------------------------------------------------
# LessonVersion
# ---------------------------------------------------------------------------


class LessonVersionModel(ndb.Model):
    """Persistent representation of a lesson version with card content."""

    lesson_id = ndb.StringProperty(required=True)
    version_number = ndb.IntegerProperty(required=True)
    title = ndb.StringProperty(required=True)
    summary = ndb.TextProperty(required=True)
    language = ndb.StringProperty(required=True)
    learning_objectives = ndb.JsonProperty(required=True)
    estimated_duration_minutes = ndb.IntegerProperty(required=True)
    cards_json = ndb.JsonProperty(required=True)
    source_ids = ndb.JsonProperty(required=True)
    status = ndb.StringProperty(
        required=True, choices=[s.value for s in VersionStatus]
    )
    author_id = ndb.StringProperty()
    submitted_by = ndb.StringProperty()
    review_feedback = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_domain(self) -> LessonVersion:
        return LessonVersion(
            version_id=self.key.string_id(),
            lesson_id=self.lesson_id,
            version_number=self.version_number,
            title=self.title,
            summary=self.summary,
            language=self.language,
            learning_objectives=list(self.learning_objectives),
            estimated_duration_minutes=self.estimated_duration_minutes,
            cards=LessonVersion.cards_from_dicts(self.cards_json),
            source_ids=list(self.source_ids),
            status=VersionStatus(self.status),
            author_id=self.author_id,
            submitted_by=self.submitted_by,
            review_feedback=self.review_feedback,
        )

    @classmethod
    def from_domain(cls, obj: LessonVersion) -> "LessonVersionModel":
        obj.validate()
        return cls(
            id=obj.version_id,
            lesson_id=obj.lesson_id,
            version_number=obj.version_number,
            title=obj.title,
            summary=obj.summary,
            language=obj.language,
            learning_objectives=list(obj.learning_objectives),
            estimated_duration_minutes=obj.estimated_duration_minutes,
            cards_json=obj.cards_as_dicts(),
            source_ids=list(obj.source_ids),
            status=obj.status.value,
            author_id=obj.author_id,
            submitted_by=obj.submitted_by,
            review_feedback=obj.review_feedback,
        )


# ---------------------------------------------------------------------------
# HealthSource
# ---------------------------------------------------------------------------


class HealthSourceModel(ndb.Model):
    """Persistent representation of a health information source / citation."""

    title = ndb.StringProperty(required=True)
    publisher = ndb.StringProperty(required=True)
    url = ndb.StringProperty(required=True)
    publication_date = ndb.DateProperty()
    access_date = ndb.DateProperty()
    jurisdiction = ndb.StringProperty()
    metadata_notes = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_domain(self) -> HealthSource:
        return HealthSource(
            source_id=self.key.string_id(),
            title=self.title,
            publisher=self.publisher,
            url=self.url,
            publication_date=self.publication_date,
            access_date=self.access_date,
            jurisdiction=self.jurisdiction,
            metadata_notes=self.metadata_notes,
        )

    @classmethod
    def from_domain(cls, obj: HealthSource) -> "HealthSourceModel":
        obj.validate()
        return cls(
            id=obj.source_id,
            title=obj.title,
            publisher=obj.publisher,
            url=obj.url,
            publication_date=obj.publication_date,
            access_date=obj.access_date,
            jurisdiction=obj.jurisdiction,
            metadata_notes=obj.metadata_notes,
        )


# ---------------------------------------------------------------------------
# ReviewRecord
# ---------------------------------------------------------------------------


class ReviewRecordModel(ndb.Model):
    """Persistent representation of an editorial / health-content review."""

    lesson_id = ndb.StringProperty(required=True)
    version_id = ndb.StringProperty(required=True)
    editorial_status = ndb.StringProperty(
        required=True, choices=[s.value for s in ReviewStatus]
    )
    health_content_status = ndb.StringProperty(
        required=True, choices=[s.value for s in ReviewStatus]
    )
    reviewer_role = ndb.StringProperty(
        required=True, choices=[r.value for r in ReviewerRole]
    )
    review_date = ndb.DateProperty(required=True)
    next_review_date = ndb.DateProperty()
    notes = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_domain(self) -> ReviewRecord:
        return ReviewRecord(
            review_id=self.key.string_id(),
            lesson_id=self.lesson_id,
            version_id=self.version_id,
            editorial_status=ReviewStatus(self.editorial_status),
            health_content_status=ReviewStatus(self.health_content_status),
            reviewer_role=ReviewerRole(self.reviewer_role),
            review_date=self.review_date,
            next_review_date=self.next_review_date,
            notes=self.notes,
        )

    @classmethod
    def from_domain(cls, obj: ReviewRecord) -> "ReviewRecordModel":
        obj.validate()
        return cls(
            id=obj.review_id,
            lesson_id=obj.lesson_id,
            version_id=obj.version_id,
            editorial_status=obj.editorial_status.value,
            health_content_status=obj.health_content_status.value,
            reviewer_role=obj.reviewer_role.value,
            review_date=obj.review_date,
            next_review_date=obj.next_review_date,
            notes=obj.notes,
        )


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserModel(ndb.Model):
    """Persistent representation of an application user."""

    username = ndb.StringProperty(required=True)
    display_name = ndb.StringProperty(required=True)
    role = ndb.StringProperty(
        required=True, choices=[r.value for r in UserRole]
    )
    password_hash = ndb.StringProperty(required=True)
    is_active = ndb.BooleanProperty(required=True, default=True)
    must_change_password = ndb.BooleanProperty(default=False)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def to_domain(self) -> User:
        return User(
            user_id=self.key.string_id(),
            username=self.username,
            display_name=self.display_name,
            role=UserRole(self.role),
            password_hash=self.password_hash,
            is_active=self.is_active,
            must_change_password=bool(self.must_change_password),
        )

    @classmethod
    def from_domain(cls, obj: User) -> "UserModel":
        obj.validate()
        return cls(
            id=obj.user_id,
            username=obj.username,
            display_name=obj.display_name,
            role=obj.role.value,
            password_hash=obj.password_hash,
            is_active=obj.is_active,
            must_change_password=obj.must_change_password,
        )

