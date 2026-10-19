"""Domain services for the Health Awareness application.

Services orchestrate domain-level business logic.  They sit between
controllers (HTTP layer) and storage models (NDB layer).

Each public function in this module:
1. Accepts and returns domain objects (never NDB models).
2. Validates every domain object before persistence.
3. Delegates NDB operations to storage model classes.
4. Assumes it is called inside an active ``ndb.Client.context()``.

Publication logic
-----------------
A lesson version progresses through: DRAFT → PUBLISHED → ARCHIVED.
Publishing a version:
  - Sets the version status to PUBLISHED.
  - Updates the owning lesson's ``published_version_id``.
  - Archives any previously-published version.
"""

from __future__ import annotations

from typing import Optional

from google.cloud import ndb

from backend.domain.domain_objects import (
    HealthSource,
    Lesson,
    LessonVersion,
    PublicationStatus,
    ReviewRecord,
    Topic,
    User,
    UserRole,
    VersionStatus,
)
from backend.platform.security import hash_password, needs_rehash, verify_password
from backend.storage.storage_models import (
    HealthSourceModel,
    LessonModel,
    LessonVersionModel,
    ReviewRecordModel,
    TopicModel,
    UserModel,
)


# ---------------------------------------------------------------------------
# Topic services
# ---------------------------------------------------------------------------


def create_topic(topic: Topic) -> Topic:
    """Create a new topic.  Raises ValueError on validation failure or
    if a topic with the same ID already exists."""
    topic.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import TopicModel as PgTopicModel
            with get_db_session() as session:
                existing = session.query(PgTopicModel).filter_by(topic_id=topic.topic_id).first()
                if existing is not None:
                    raise ValueError(f"Topic with id {topic.topic_id!r} already exists.")
                m = PgTopicModel.from_domain(topic)
                session.add(m)
                session.commit()
                return m.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    existing = TopicModel.get_by_id(topic.topic_id)
    if existing is not None:
        raise ValueError(f"Topic with id {topic.topic_id!r} already exists.")
    model = TopicModel.from_domain(topic)
    model.put()
    return model.to_domain()


def get_topic(topic_id: str) -> Optional[Topic]:
    """Retrieve a topic by ID, or None if not found."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import TopicModel as PgTopicModel
            with get_db_session() as session:
                m = session.query(PgTopicModel).filter_by(topic_id=topic_id).first()
                return m.to_domain() if m is not None else None
        except Exception:
            pass

    model = TopicModel.get_by_id(topic_id)
    if model is None:
        return None
    return model.to_domain()


def list_topics(
    status: Optional[PublicationStatus] = None,
) -> list[Topic]:
    """List topics, optionally filtered by publication status.
    Results are ordered by display_order ascending."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import TopicModel as PgTopicModel
            with get_db_session() as session:
                q = session.query(PgTopicModel)
                if status is not None:
                    q = q.filter(PgTopicModel.status == status.value)
                q = q.order_by(PgTopicModel.display_order.asc())
                return [m.to_domain() for m in q.all()]
        except Exception:
            pass

    query = TopicModel.query()
    if status is not None:
        query = query.filter(TopicModel.status == status.value)
    query = query.order(TopicModel.display_order)
    return [m.to_domain() for m in query.fetch()]


def update_topic(topic: Topic) -> Topic:
    """Update an existing topic.  Raises ValueError if not found."""
    topic.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import TopicModel as PgTopicModel
            with get_db_session() as session:
                model = session.query(PgTopicModel).filter_by(topic_id=topic.topic_id).first()
                if model is None:
                    raise ValueError(f"Topic {topic.topic_id!r} not found.")
                model.title = topic.title
                model.url_slug = topic.url_slug
                model.description = topic.description
                model.display_order = topic.display_order
                model.status = topic.status.value
                model.cover_image_ref = topic.cover_image_ref
                model.cover_image_alt = topic.cover_image_alt
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = TopicModel.get_by_id(topic.topic_id)
    if model is None:
        raise ValueError(f"Topic {topic.topic_id!r} not found.")
    model.title = topic.title
    model.url_slug = topic.url_slug
    model.description = topic.description
    model.display_order = topic.display_order
    model.status = topic.status.value
    model.cover_image_ref = topic.cover_image_ref
    model.cover_image_alt = topic.cover_image_alt
    model.put()
    return model.to_domain()


def delete_topic(topic_id: str) -> None:
    """Delete a topic.  Raises ValueError if not found."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import TopicModel as PgTopicModel
            with get_db_session() as session:
                model = session.query(PgTopicModel).filter_by(topic_id=topic_id).first()
                if model is None:
                    raise ValueError(f"Topic {topic_id!r} not found.")
                session.delete(model)
                session.commit()
                return
        except ValueError:
            raise
        except Exception:
            pass

    model = TopicModel.get_by_id(topic_id)
    if model is None:
        raise ValueError(f"Topic {topic_id!r} not found.")
    model.key.delete()


# ---------------------------------------------------------------------------
# Lesson services
# ---------------------------------------------------------------------------


def create_lesson(lesson: Lesson) -> Lesson:
    """Create a new lesson shell under an existing topic."""
    lesson.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import (
                LessonModel as PgLessonModel,
                TopicModel as PgTopicModel,
            )
            with get_db_session() as session:
                parent_topic = session.query(PgTopicModel).filter_by(topic_id=lesson.topic_id).first()
                if parent_topic is None:
                    raise ValueError(f"Parent topic {lesson.topic_id!r} not found.")
                existing = session.query(PgLessonModel).filter_by(lesson_id=lesson.lesson_id).first()
                if existing is not None:
                    raise ValueError(f"Lesson with id {lesson.lesson_id!r} already exists.")
                m = PgLessonModel.from_domain(lesson)
                session.add(m)
                session.commit()
                return m.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    parent_topic = TopicModel.get_by_id(lesson.topic_id)
    if parent_topic is None:
        raise ValueError(f"Parent topic {lesson.topic_id!r} not found.")
    existing = LessonModel.get_by_id(lesson.lesson_id)
    if existing is not None:
        raise ValueError(f"Lesson with id {lesson.lesson_id!r} already exists.")
    model = LessonModel.from_domain(lesson)
    model.put()
    return model.to_domain()


def get_lesson(lesson_id: str) -> Optional[Lesson]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonModel as PgLessonModel
            with get_db_session() as session:
                m = session.query(PgLessonModel).filter_by(lesson_id=lesson_id).first()
                return m.to_domain() if m is not None else None
        except Exception:
            pass

    model = LessonModel.get_by_id(lesson_id)
    if model is None:
        return None
    return model.to_domain()


def list_lessons_by_topic(topic_id: str) -> list[Lesson]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonModel as PgLessonModel
            with get_db_session() as session:
                q = (
                    session.query(PgLessonModel)
                    .filter_by(topic_id=topic_id)
                    .order_by(PgLessonModel.display_order.asc())
                )
                return [m.to_domain() for m in q.all()]
        except Exception:
            pass

    query = (
        LessonModel.query()
        .filter(LessonModel.topic_id == topic_id)
        .order(LessonModel.display_order)
    )
    return [m.to_domain() for m in query.fetch()]


def delete_lesson(lesson_id: str) -> None:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonModel as PgLessonModel
            with get_db_session() as session:
                model = session.query(PgLessonModel).filter_by(lesson_id=lesson_id).first()
                if model is None:
                    raise ValueError(f"Lesson {lesson_id!r} not found.")
                session.delete(model)
                session.commit()
                return
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonModel.get_by_id(lesson_id)
    if model is None:
        raise ValueError(f"Lesson {lesson_id!r} not found.")
    model.key.delete()


# ---------------------------------------------------------------------------
# LessonVersion services
# ---------------------------------------------------------------------------


def create_lesson_version(version: LessonVersion) -> LessonVersion:
    """Create a new lesson version in DRAFT status."""
    if version.status != VersionStatus.DRAFT:
        raise ValueError("New versions must be created with status DRAFT.")
    version.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import (
                LessonModel as PgLessonModel,
                LessonVersionModel as PgVersionModel,
            )
            with get_db_session() as session:
                parent_lesson = session.query(PgLessonModel).filter_by(lesson_id=version.lesson_id).first()
                if parent_lesson is None:
                    raise ValueError(f"Parent lesson {version.lesson_id!r} not found.")
                existing = session.query(PgVersionModel).filter_by(version_id=version.version_id).first()
                if existing is not None:
                    raise ValueError(f"LessonVersion with id {version.version_id!r} already exists.")
                m = PgVersionModel.from_domain(version)
                session.add(m)
                parent_lesson.draft_version_id = version.version_id
                session.commit()
                return m.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    # Verify parent lesson exists.
    parent_lesson = LessonModel.get_by_id(version.lesson_id)
    if parent_lesson is None:
        raise ValueError(f"Parent lesson {version.lesson_id!r} not found.")
    existing = LessonVersionModel.get_by_id(version.version_id)
    if existing is not None:
        raise ValueError(
            f"LessonVersion with id {version.version_id!r} already exists."
        )
    model = LessonVersionModel.from_domain(version)
    model.put()
    # Update parent lesson's draft pointer.
    parent_lesson.draft_version_id = version.version_id
    parent_lesson.put()
    return model.to_domain()


def get_lesson_version(version_id: str) -> Optional[LessonVersion]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonVersionModel as PgVersionModel
            with get_db_session() as session:
                m = session.query(PgVersionModel).filter_by(version_id=version_id).first()
                return m.to_domain() if m is not None else None
        except Exception:
            pass

    model = LessonVersionModel.get_by_id(version_id)
    if model is None:
        return None
    return model.to_domain()


def publish_lesson_version(version_id: str) -> LessonVersion:
    """Publish a draft lesson version.

    1. The version's status changes from DRAFT to PUBLISHED.
    2. The parent lesson's published_version_id is updated.
    3. Any previously-published version is archived.
    """
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import (
                LessonModel as PgLessonModel,
                LessonVersionModel as PgVersionModel,
                TopicModel as PgTopicModel,
            )
            with get_db_session() as session:
                model = session.query(PgVersionModel).filter_by(version_id=version_id).first()
                if model is None:
                    raise ValueError(f"LessonVersion {version_id!r} not found.")
                if model.status != VersionStatus.DRAFT.value:
                    raise ValueError(
                        f"Only DRAFT versions can be published. Current status: {model.status!r}"
                    )
                parent = session.query(PgLessonModel).filter_by(lesson_id=model.lesson_id).first()
                if parent is None:
                    raise ValueError(f"Parent lesson {model.lesson_id!r} not found.")
                if parent.published_version_id:
                    old_pub = session.query(PgVersionModel).filter_by(version_id=parent.published_version_id).first()
                    if old_pub is not None and old_pub.status == VersionStatus.PUBLISHED.value:
                        old_pub.status = VersionStatus.ARCHIVED.value
                model.status = VersionStatus.PUBLISHED.value
                parent.published_version_id = version_id
                if parent.draft_version_id == version_id:
                    parent.draft_version_id = None
                topic_model = session.query(PgTopicModel).filter_by(topic_id=parent.topic_id).first()
                if topic_model is not None and topic_model.status != PublicationStatus.PUBLISHED.value:
                    topic_model.status = PublicationStatus.PUBLISHED.value
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonVersionModel.get_by_id(version_id)
    if model is None:
        raise ValueError(f"LessonVersion {version_id!r} not found.")
    if model.status != VersionStatus.DRAFT.value:
        raise ValueError(
            f"Only DRAFT versions can be published.  "
            f"Current status: {model.status!r}"
        )

    # Archive the currently-published version, if any.
    parent = LessonModel.get_by_id(model.lesson_id)
    if parent is None:
        raise ValueError(f"Parent lesson {model.lesson_id!r} not found.")

    if parent.published_version_id:
        old_pub = LessonVersionModel.get_by_id(parent.published_version_id)
        if old_pub is not None and old_pub.status == VersionStatus.PUBLISHED.value:
            old_pub.status = VersionStatus.ARCHIVED.value
            old_pub.put()

    # Publish the new version.
    model.status = VersionStatus.PUBLISHED.value
    model.put()

    # Update parent pointers.
    parent.published_version_id = version_id
    if parent.draft_version_id == version_id:
        parent.draft_version_id = None
    parent.put()

    return model.to_domain()


# ---------------------------------------------------------------------------
# HealthSource services
# ---------------------------------------------------------------------------


def create_health_source(source: HealthSource) -> HealthSource:
    source.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import HealthSourceModel as PgSourceModel
            with get_db_session() as session:
                existing = session.query(PgSourceModel).filter_by(source_id=source.source_id).first()
                if existing is not None:
                    raise ValueError(f"HealthSource with id {source.source_id!r} already exists.")
                m = PgSourceModel.from_domain(source)
                session.add(m)
                session.commit()
                return m.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    existing = HealthSourceModel.get_by_id(source.source_id)
    if existing is not None:
        raise ValueError(f"HealthSource with id {source.source_id!r} already exists.")
    model = HealthSourceModel.from_domain(source)
    model.put()
    return model.to_domain()


def get_health_source(source_id: str) -> Optional[HealthSource]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import HealthSourceModel as PgSourceModel
            with get_db_session() as session:
                m = session.query(PgSourceModel).filter_by(source_id=source_id).first()
                return m.to_domain() if m is not None else None
        except Exception:
            pass

    model = HealthSourceModel.get_by_id(source_id)
    if model is None:
        return None
    return model.to_domain()


def list_health_sources() -> list[HealthSource]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import HealthSourceModel as PgSourceModel
            with get_db_session() as session:
                sources = session.query(PgSourceModel).all()
                return [m.to_domain() for m in sources]
        except Exception:
            pass

    return [m.to_domain() for m in HealthSourceModel.query().fetch()]


def delete_health_source(source_id: str) -> None:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import HealthSourceModel as PgSourceModel
            with get_db_session() as session:
                model = session.query(PgSourceModel).filter_by(source_id=source_id).first()
                if model is None:
                    raise ValueError(f"HealthSource {source_id!r} not found.")
                session.delete(model)
                session.commit()
                return
        except ValueError:
            raise
        except Exception:
            pass

    model = HealthSourceModel.get_by_id(source_id)
    if model is None:
        raise ValueError(f"HealthSource {source_id!r} not found.")
    model.key.delete()


# ---------------------------------------------------------------------------
# ReviewRecord services
# ---------------------------------------------------------------------------


def create_review_record(review: ReviewRecord) -> ReviewRecord:
    review.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import ReviewRecordModel as PgReviewModel
            with get_db_session() as session:
                existing = session.query(PgReviewModel).filter_by(review_id=review.review_id).first()
                if existing is not None:
                    raise ValueError(
                        f"ReviewRecord with id {review.review_id!r} already exists."
                    )
                m = PgReviewModel.from_domain(review)
                session.add(m)
                session.commit()
                return m.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    existing = ReviewRecordModel.get_by_id(review.review_id)
    if existing is not None:
        raise ValueError(
            f"ReviewRecord with id {review.review_id!r} already exists."
        )
    model = ReviewRecordModel.from_domain(review)
    model.put()
    return model.to_domain()


def get_review_record(review_id: str) -> Optional[ReviewRecord]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import ReviewRecordModel as PgReviewModel
            with get_db_session() as session:
                m = session.query(PgReviewModel).filter_by(review_id=review_id).first()
                return m.to_domain() if m is not None else None
        except Exception:
            pass

    model = ReviewRecordModel.get_by_id(review_id)
    if model is None:
        return None
    return model.to_domain()


def list_reviews_for_lesson(lesson_id: str) -> list[ReviewRecord]:
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import ReviewRecordModel as PgReviewModel
            with get_db_session() as session:
                reviews = session.query(PgReviewModel).filter_by(lesson_id=lesson_id).all()
                return [m.to_domain() for m in reviews]
        except Exception:
            pass

    query = ReviewRecordModel.query().filter(
        ReviewRecordModel.lesson_id == lesson_id
    )
    return [m.to_domain() for m in query.fetch()]


# ---------------------------------------------------------------------------
# Public reading services (read-only publication queries)
# ---------------------------------------------------------------------------


def get_published_lessons_for_topic(
    topic_id: str,
) -> Optional[list[tuple[Lesson, LessonVersion]]]:
    """Retrieve all published lessons and their corresponding published version
    for a published topic, ordered by lesson display_order.

    Returns None if the parent topic does not exist or is not in PUBLISHED status.
    Returns an empty list if the topic exists and is published, but has no published lessons.
    """
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import (
                LessonModel as PgLessonModel,
                LessonVersionModel as PgVersionModel,
                TopicModel as PgTopicModel,
            )
            with get_db_session() as session:
                t = session.query(PgTopicModel).filter_by(topic_id=topic_id).first()
                if t is None or t.status != PublicationStatus.PUBLISHED.value:
                    return None
                lessons = (
                    session.query(PgLessonModel)
                    .filter_by(topic_id=topic_id)
                    .order_by(PgLessonModel.display_order.asc())
                    .all()
                )
                results: list[tuple[Lesson, LessonVersion]] = []
                for l in lessons:
                    if l.published_version_id:
                        v = (
                            session.query(PgVersionModel)
                            .filter_by(version_id=l.published_version_id)
                            .first()
                        )
                        if v and v.status == VersionStatus.PUBLISHED.value:
                            results.append((l.to_domain(), v.to_domain()))
                return results
        except Exception:
            pass

    topic_model = TopicModel.get_by_id(topic_id)
    if topic_model is None or topic_model.status != PublicationStatus.PUBLISHED.value:
        return None

    lessons = list_lessons_by_topic(topic_id)
    results: list[tuple[Lesson, LessonVersion]] = []
    for lesson in lessons:
        if not lesson.published_version_id:
            continue
        version = get_lesson_version(lesson.published_version_id)
        if version is not None and version.status == VersionStatus.PUBLISHED:
            results.append((lesson, version))
    return results


def get_published_lesson(
    lesson_id: str,
) -> Optional[tuple[Lesson, LessonVersion]]:
    """Retrieve a lesson and its published version if both the lesson and its
    parent topic are published.

    Returns None if the lesson is missing, has no published version, the published
    version is missing/not PUBLISHED, or if the parent topic is missing/not PUBLISHED.
    """
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import (
                LessonModel as PgLessonModel,
                LessonVersionModel as PgVersionModel,
                TopicModel as PgTopicModel,
            )
            with get_db_session() as session:
                l = session.query(PgLessonModel).filter_by(lesson_id=lesson_id).first()
                if l and l.published_version_id:
                    t = session.query(PgTopicModel).filter_by(topic_id=l.topic_id).first()
                    if t and t.status == PublicationStatus.PUBLISHED.value:
                        v = (
                            session.query(PgVersionModel)
                            .filter_by(version_id=l.published_version_id)
                            .first()
                        )
                        if v and v.status == VersionStatus.PUBLISHED.value:
                            return (l.to_domain(), v.to_domain())
                return None
        except Exception:
            pass

    lesson = get_lesson(lesson_id)
    if lesson is None or not lesson.published_version_id:
        return None

    topic_model = TopicModel.get_by_id(lesson.topic_id)
    if topic_model is None or topic_model.status != PublicationStatus.PUBLISHED.value:
        return None

    version = get_lesson_version(lesson.published_version_id)
    if version is None or version.status != VersionStatus.PUBLISHED:
        return None

    return lesson, version


def get_health_sources_by_ids(source_ids: list[str]) -> list[HealthSource]:
    """Retrieve health sources by a list of IDs, preserving order and omitting missing ones."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import HealthSourceModel as PgSourceModel
            with get_db_session() as session:
                objs = (
                    session.query(PgSourceModel)
                    .filter(PgSourceModel.source_id.in_(source_ids))
                    .all()
                )
                by_id = {s.source_id: s.to_domain() for s in objs}
                ordered = [by_id[sid] for sid in source_ids if sid in by_id]
                return ordered
        except Exception:
            pass

    sources: list[HealthSource] = []
    seen: set[str] = set()
    for sid in source_ids:
        if sid in seen:
            continue
        seen.add(sid)
        s = get_health_source(sid)
        if s is not None:
            sources.append(s)
    return sources


# ---------------------------------------------------------------------------
# User services
# ---------------------------------------------------------------------------


def create_user(user: User) -> User:
    """Create a new user.  Raises ValueError on validation failure or
    if a user with the same ID already exists."""
    user.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                existing_id = session.query(PgUserModel).filter_by(user_id=user.user_id).first()
                if existing_id is not None:
                    raise ValueError(f"User with id {user.user_id!r} already exists.")
                dupe_name = session.query(PgUserModel).filter_by(username=user.username).first()
                if dupe_name is not None:
                    raise ValueError(f"Username {user.username!r} is already taken.")
                pg_model = PgUserModel.from_domain(user)
                session.add(pg_model)
                session.commit()
                return pg_model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    existing = UserModel.get_by_id(user.user_id)
    if existing is not None:
        raise ValueError(f"User with id {user.user_id!r} already exists.")
    # Check username uniqueness
    dupes = UserModel.query().filter(UserModel.username == user.username).fetch(1)
    if dupes:
        raise ValueError(f"Username {user.username!r} is already taken.")
    model = UserModel.from_domain(user)
    model.put()
    return model.to_domain()


def get_user(user_id: str) -> Optional[User]:
    """Retrieve a user by ID, or None if not found."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                pg_u = session.query(PgUserModel).filter_by(user_id=user_id).first()
                return pg_u.to_domain() if pg_u is not None else None
        except Exception:
            pass

    model = UserModel.get_by_id(user_id)
    if model is None:
        return None
    return model.to_domain()


def get_user_by_username(username: str) -> Optional[User]:
    """Retrieve a user by username, or None if not found."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                pg_u = session.query(PgUserModel).filter_by(username=username).first()
                return pg_u.to_domain() if pg_u is not None else None
        except Exception:
            pass

    results = UserModel.query().filter(UserModel.username == username).fetch(1)
    if not results:
        return None
    return results[0].to_domain()


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and plaintext password.

    Verifies against PBKDF2-HMAC-SHA256 (600,000 iterations) or legacy SHA-256.
    If credentials match and the hash uses a legacy scheme, transparently upgrades
    the stored hash in-place to the 600,000-iteration standard.
    """
    user = get_user_by_username(username)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None

    # Transparent hash upgrade to OWASP 600k standard
    if needs_rehash(user.password_hash):
        new_hash = hash_password(password)
        from google.cloud import ndb
        if ndb.get_context(raise_context_error=False) is None:
            try:
                from backend.storage.db import get_db_session
                from backend.storage.postgres_models import UserModel as PgUserModel
                with get_db_session() as session:
                    pg_u = session.query(PgUserModel).filter_by(user_id=user.user_id).first()
                    if pg_u:
                        pg_u.password_hash = new_hash
                        session.commit()
                        user.password_hash = new_hash
            except Exception:
                pass
        else:
            model = UserModel.get_by_id(user.user_id)
            if model is not None:
                model.password_hash = new_hash
                model.put()
                user.password_hash = new_hash

    return user


def list_users() -> list[User]:
    """List all registered users ordered by creation date."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                pg_users = session.query(PgUserModel).order_by(PgUserModel.created_at.asc()).all()
                return [u.to_domain() for u in pg_users]
        except Exception:
            pass

    query = UserModel.query().order(UserModel.created_at)
    return [m.to_domain() for m in query.fetch()]


def update_user_role(user_id: str, new_role: UserRole) -> User:
    """Update a user's role. Raises ValueError if user not found."""
    if not isinstance(new_role, UserRole):
        raise ValueError(f"Invalid user role: {new_role!r}")
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                pg_u = session.query(PgUserModel).filter_by(user_id=user_id).first()
                if pg_u is None:
                    raise ValueError(f"User {user_id!r} not found.")
                pg_u.role = new_role.value
                session.commit()
                return pg_u.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = UserModel.get_by_id(user_id)
    if model is None:
        raise ValueError(f"User {user_id!r} not found.")
    model.role = new_role.value
    model.put()
    return model.to_domain()


def set_user_active_status(user_id: str, is_active: bool) -> User:
    """Activate or deactivate a user account. Raises ValueError if user not found."""
    if not isinstance(is_active, bool):
        raise ValueError("is_active must be a boolean.")
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                pg_u = session.query(PgUserModel).filter_by(user_id=user_id).first()
                if pg_u is None:
                    raise ValueError(f"User {user_id!r} not found.")
                pg_u.is_active = is_active
                session.commit()
                return pg_u.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = UserModel.get_by_id(user_id)
    if model is None:
        raise ValueError(f"User {user_id!r} not found.")
    model.is_active = is_active
    model.put()
    return model.to_domain()


# ---------------------------------------------------------------------------
# Creator workflow services
# ---------------------------------------------------------------------------


def update_lesson_version(version: LessonVersion) -> LessonVersion:
    """Update an existing draft lesson version.  Only DRAFT versions can be edited."""
    version.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonVersionModel as PgVersionModel
            with get_db_session() as session:
                model = session.query(PgVersionModel).filter_by(version_id=version.version_id).first()
                if model is None:
                    raise ValueError(f"LessonVersion {version.version_id!r} not found.")
                if model.status != VersionStatus.DRAFT.value:
                    raise ValueError(
                        f"Only DRAFT versions can be updated. Current status: {model.status!r}"
                    )
                model.title = version.title
                model.summary = version.summary
                model.language = version.language
                model.learning_objectives = list(version.learning_objectives)
                model.estimated_duration_minutes = version.estimated_duration_minutes
                model.cards_json = version.cards_as_dicts()
                model.source_ids = list(version.source_ids)
                if version.author_id:
                    model.author_id = version.author_id
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonVersionModel.get_by_id(version.version_id)
    if model is None:
        raise ValueError(f"LessonVersion {version.version_id!r} not found.")
    if model.status != VersionStatus.DRAFT.value:
        raise ValueError(
            f"Only DRAFT versions can be updated.  "
            f"Current status: {model.status!r}"
        )
    model.title = version.title
    model.summary = version.summary
    model.language = version.language
    model.learning_objectives = list(version.learning_objectives)
    model.estimated_duration_minutes = version.estimated_duration_minutes
    model.cards_json = version.cards_as_dicts()
    model.source_ids = list(version.source_ids)
    if version.author_id:
        model.author_id = version.author_id
    model.put()
    return model.to_domain()


def submit_for_review(version_id: str, user_id: Optional[str] = None) -> LessonVersion:
    """Submit a draft version for review."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonVersionModel as PgVersionModel
            with get_db_session() as session:
                model = session.query(PgVersionModel).filter_by(version_id=version_id).first()
                if model is None:
                    raise ValueError(f"LessonVersion {version_id!r} not found.")
                if model.status != VersionStatus.DRAFT.value:
                    raise ValueError(
                        f"Only DRAFT versions can be submitted for review. Current status: {model.status!r}"
                    )
                if user_id:
                    model.submitted_by = user_id
                model.status = VersionStatus.SUBMITTED_FOR_REVIEW.value
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonVersionModel.get_by_id(version_id)
    if model is None:
        raise ValueError(f"LessonVersion {version_id!r} not found.")
    if model.status != VersionStatus.DRAFT.value:
        raise ValueError(
            f"Only DRAFT versions can be submitted for review.  "
            f"Current status: {model.status!r}"
        )
    if user_id:
        model.submitted_by = user_id
    model.status = VersionStatus.SUBMITTED_FOR_REVIEW.value
    model.put()
    return model.to_domain()


def approve_version(version_id: str, reviewer_id: Optional[str] = None) -> LessonVersion:
    """Approve a submitted version — this publishes it.

    1. Enforces self-approval restriction (contributors cannot approve their own submissions).
    2. The version's status changes from SUBMITTED_FOR_REVIEW to PUBLISHED.
    3. The parent lesson's published_version_id is updated.
    4. Any previously-published version is archived.
    """
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import (
                LessonModel as PgLessonModel,
                LessonVersionModel as PgVersionModel,
                TopicModel as PgTopicModel,
            )
            with get_db_session() as session:
                model = session.query(PgVersionModel).filter_by(version_id=version_id).first()
                if model is None:
                    raise ValueError(f"LessonVersion {version_id!r} not found.")
                if model.status != VersionStatus.SUBMITTED_FOR_REVIEW.value:
                    raise ValueError(
                        f"Only SUBMITTED_FOR_REVIEW versions can be approved. Current status: {model.status!r}"
                    )
                if reviewer_id:
                    if model.submitted_by and model.submitted_by == reviewer_id:
                        raise ValueError("Self-approval is forbidden. A contributor cannot approve their own submission.")
                    if model.author_id and model.author_id == reviewer_id:
                        raise ValueError("Self-approval is forbidden. An author cannot approve their own lesson version.")
                parent = session.query(PgLessonModel).filter_by(lesson_id=model.lesson_id).first()
                if parent is None:
                    raise ValueError(f"Parent lesson {model.lesson_id!r} not found.")
                if parent.published_version_id:
                    old_pub = session.query(PgVersionModel).filter_by(version_id=parent.published_version_id).first()
                    if old_pub is not None and old_pub.status == VersionStatus.PUBLISHED.value:
                        old_pub.status = VersionStatus.ARCHIVED.value
                model.status = VersionStatus.PUBLISHED.value
                parent.published_version_id = version_id
                if parent.draft_version_id == version_id:
                    parent.draft_version_id = None
                topic_model = session.query(PgTopicModel).filter_by(topic_id=parent.topic_id).first()
                if topic_model is not None and topic_model.status != PublicationStatus.PUBLISHED.value:
                    topic_model.status = PublicationStatus.PUBLISHED.value
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonVersionModel.get_by_id(version_id)
    if model is None:
        raise ValueError(f"LessonVersion {version_id!r} not found.")
    if model.status != VersionStatus.SUBMITTED_FOR_REVIEW.value:
        raise ValueError(
            f"Only SUBMITTED_FOR_REVIEW versions can be approved.  "
            f"Current status: {model.status!r}"
        )

    # Self-approval check: Contributors/Authors cannot approve their own submissions!
    if reviewer_id:
        if model.submitted_by and model.submitted_by == reviewer_id:
            raise ValueError("Self-approval is forbidden. A contributor cannot approve their own submission.")
        if model.author_id and model.author_id == reviewer_id:
            raise ValueError("Self-approval is forbidden. An author cannot approve their own lesson version.")

    # Archive the currently-published version, if any.
    parent = LessonModel.get_by_id(model.lesson_id)
    if parent is None:
        raise ValueError(f"Parent lesson {model.lesson_id!r} not found.")

    if parent.published_version_id:
        old_pub = LessonVersionModel.get_by_id(parent.published_version_id)
        if old_pub is not None and old_pub.status == VersionStatus.PUBLISHED.value:
            old_pub.status = VersionStatus.ARCHIVED.value
            old_pub.put()

    # Publish the new version.
    model.status = VersionStatus.PUBLISHED.value
    model.put()

    # Update parent pointers.
    parent.published_version_id = version_id
    if parent.draft_version_id == version_id:
        parent.draft_version_id = None
    parent.put()

    # Also ensure the parent topic is published.
    topic_model = TopicModel.get_by_id(parent.topic_id)
    if topic_model is not None and topic_model.status != PublicationStatus.PUBLISHED.value:
        topic_model.status = PublicationStatus.PUBLISHED.value
        topic_model.put()

    return model.to_domain()


def request_changes(version_id: str, notes: str = "") -> LessonVersion:
    """Request changes on a submitted version — reverts it to DRAFT and records notes."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonVersionModel as PgVersionModel
            with get_db_session() as session:
                model = session.query(PgVersionModel).filter_by(version_id=version_id).first()
                if model is None:
                    raise ValueError(f"LessonVersion {version_id!r} not found.")
                if model.status != VersionStatus.SUBMITTED_FOR_REVIEW.value:
                    raise ValueError(
                        f"Only SUBMITTED_FOR_REVIEW versions can have changes requested. Current status: {model.status!r}"
                    )
                model.status = VersionStatus.DRAFT.value
                model.review_feedback = notes.strip() if notes else None
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonVersionModel.get_by_id(version_id)
    if model is None:
        raise ValueError(f"LessonVersion {version_id!r} not found.")
    if model.status != VersionStatus.SUBMITTED_FOR_REVIEW.value:
        raise ValueError(
            f"Only SUBMITTED_FOR_REVIEW versions can have changes requested.  "
            f"Current status: {model.status!r}"
        )
    model.status = VersionStatus.DRAFT.value
    model.review_feedback = notes.strip() if notes else None
    model.put()
    return model.to_domain()


def list_all_topics() -> list[Topic]:
    """List all topics regardless of publication status (for creator dashboard)."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import TopicModel as PgTopicModel
            with get_db_session() as session:
                q = session.query(PgTopicModel).order_by(PgTopicModel.display_order.asc())
                return [m.to_domain() for m in q.all()]
        except Exception:
            pass

    query = TopicModel.query().order(TopicModel.display_order)
    return [m.to_domain() for m in query.fetch()]


def list_versions_for_lesson(lesson_id: str) -> list[LessonVersion]:
    """List all versions for a lesson (for creator editing)."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonVersionModel as PgVersionModel
            with get_db_session() as session:
                q = (
                    session.query(PgVersionModel)
                    .filter_by(lesson_id=lesson_id)
                    .order_by(PgVersionModel.version_number.asc())
                )
                return [m.to_domain() for m in q.all()]
        except Exception:
            pass

    query = LessonVersionModel.query().filter(
        LessonVersionModel.lesson_id == lesson_id
    )
    return [m.to_domain() for m in query.fetch()]


def list_submitted_versions() -> list[LessonVersion]:
    """List all versions submitted for review (for reviewer queue)."""
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonVersionModel as PgVersionModel
            with get_db_session() as session:
                q = (
                    session.query(PgVersionModel)
                    .filter_by(status=VersionStatus.SUBMITTED_FOR_REVIEW.value)
                    .order_by(PgVersionModel.updated_at.desc())
                )
                return [m.to_domain() for m in q.all()]
        except Exception:
            pass

    query = LessonVersionModel.query().filter(
        LessonVersionModel.status == VersionStatus.SUBMITTED_FOR_REVIEW.value
    )
    return [m.to_domain() for m in query.fetch()]


def update_health_source(source: HealthSource) -> HealthSource:
    """Update an existing health source."""
    source.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import HealthSourceModel as PgSourceModel
            with get_db_session() as session:
                model = session.query(PgSourceModel).filter_by(source_id=source.source_id).first()
                if model is None:
                    raise ValueError(f"HealthSource {source.source_id!r} not found.")
                model.title = source.title
                model.publisher = source.publisher
                model.url = source.url
                model.publication_date = source.publication_date
                model.access_date = source.access_date
                model.jurisdiction = source.jurisdiction
                model.metadata_notes = source.metadata_notes
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = HealthSourceModel.get_by_id(source.source_id)
    if model is None:
        raise ValueError(f"HealthSource {source.source_id!r} not found.")
    model.title = source.title
    model.publisher = source.publisher
    model.url = source.url
    model.publication_date = source.publication_date
    model.access_date = source.access_date
    model.jurisdiction = source.jurisdiction
    model.metadata_notes = source.metadata_notes
    model.put()
    return model.to_domain()


def update_lesson(lesson: Lesson) -> Lesson:
    """Update an existing lesson."""
    lesson.validate()
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import LessonModel as PgLessonModel
            with get_db_session() as session:
                model = session.query(PgLessonModel).filter_by(lesson_id=lesson.lesson_id).first()
                if model is None:
                    raise ValueError(f"Lesson {lesson.lesson_id!r} not found.")
                model.topic_id = lesson.topic_id
                model.display_order = lesson.display_order
                model.published_version_id = lesson.published_version_id
                model.draft_version_id = lesson.draft_version_id
                session.commit()
                return model.to_domain()
        except ValueError:
            raise
        except Exception:
            pass

    model = LessonModel.get_by_id(lesson.lesson_id)
    if model is None:
        raise ValueError(f"Lesson {lesson.lesson_id!r} not found.")
    model.topic_id = lesson.topic_id
    model.display_order = lesson.display_order
    model.published_version_id = lesson.published_version_id
    model.draft_version_id = lesson.draft_version_id
    model.put()
    return model.to_domain()

