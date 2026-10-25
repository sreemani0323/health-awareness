"""SQLAlchemy ORM models for PostgreSQL persistence in HealthAware.

Compatible with Python 3.12, local PostgreSQL, and hosted Neon PostgreSQL.
Uses JSON types with PostgreSQL JSONB variants to preserve rich lesson card,
interaction, and citation schemas without semantic loss.
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON

from backend.domain.domain_objects import (
    HealthSource,
    Lesson,
    LessonVersion,
    PublicationStatus,
    ReviewRecord,
    ReviewerRole,
    ReviewStatus,
    Topic,
    User,
    UserRole,
    VersionStatus,
)

Base = declarative_base()

# Use JSONB on PostgreSQL for optimal indexing, falling back to JSON elsewhere
JsonType = JSON().with_variant(JSONB, "postgresql")


# ---------------------------------------------------------------------------
# Curriculum Models
# ---------------------------------------------------------------------------


class TopicModel(Base):
    """PostgreSQL table for health education topics."""

    __tablename__ = "topics"

    topic_id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    url_slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    display_order = Column(Integer, nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    cover_image_ref = Column(String(255), nullable=True)
    cover_image_alt = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    lessons = relationship(
        "LessonModel",
        back_populates="topic",
        order_by="LessonModel.display_order.asc()",
        cascade="all, delete-orphan",
    )

    def to_domain(self) -> Topic:
        return Topic(
            topic_id=self.topic_id,
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
            topic_id=obj.topic_id,
            title=obj.title,
            url_slug=obj.url_slug,
            description=obj.description,
            display_order=obj.display_order,
            status=obj.status.value,
            cover_image_ref=obj.cover_image_ref,
            cover_image_alt=obj.cover_image_alt,
        )


class LessonModel(Base):
    """PostgreSQL table for lesson shells."""

    __tablename__ = "lessons"

    lesson_id = Column(String(64), primary_key=True)
    topic_id = Column(
        String(64),
        ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_order = Column(Integer, nullable=False, index=True)
    published_version_id = Column(String(64), nullable=True)
    draft_version_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    topic = relationship("TopicModel", back_populates="lessons")
    versions = relationship(
        "LessonVersionModel",
        back_populates="lesson",
        order_by="LessonVersionModel.version_number.asc()",
        cascade="all, delete-orphan",
        foreign_keys="[LessonVersionModel.lesson_id]",
    )

    def to_domain(self) -> Lesson:
        return Lesson(
            lesson_id=self.lesson_id,
            topic_id=self.topic_id,
            display_order=self.display_order,
            published_version_id=self.published_version_id,
            draft_version_id=self.draft_version_id,
        )

    @classmethod
    def from_domain(cls, obj: Lesson) -> "LessonModel":
        obj.validate()
        return cls(
            lesson_id=obj.lesson_id,
            topic_id=obj.topic_id,
            display_order=obj.display_order,
            published_version_id=obj.published_version_id,
            draft_version_id=obj.draft_version_id,
        )


class LessonVersionModel(Base):
    """PostgreSQL table for versioned lesson content and card structures."""

    __tablename__ = "lesson_versions"

    version_id = Column(String(64), primary_key=True)
    lesson_id = Column(
        String(64),
        ForeignKey("lessons.lesson_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    language = Column(String(16), nullable=False, default="en")
    learning_objectives = Column(JsonType, nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False, default=5)
    cards_json = Column(JsonType, nullable=False)
    source_ids = Column(JsonType, nullable=False)
    status = Column(String(32), nullable=False, index=True)
    author_id = Column(String(64), nullable=True)
    submitted_by = Column(String(64), nullable=True)
    review_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    lesson = relationship("LessonModel", back_populates="versions", foreign_keys=[lesson_id])

    __table_args__ = (
        Index("idx_lesson_version_order", "lesson_id", "version_number"),
    )

    def to_domain(self) -> LessonVersion:
        return LessonVersion(
            version_id=self.version_id,
            lesson_id=self.lesson_id,
            version_number=self.version_number,
            title=self.title,
            summary=self.summary,
            language=self.language,
            learning_objectives=list(self.learning_objectives or []),
            estimated_duration_minutes=self.estimated_duration_minutes,
            cards=LessonVersion.cards_from_dicts(self.cards_json or []),
            source_ids=list(self.source_ids or []),
            status=VersionStatus(self.status),
            author_id=self.author_id,
            submitted_by=self.submitted_by,
            review_feedback=self.review_feedback,
        )

    @classmethod
    def from_domain(cls, obj: LessonVersion) -> "LessonVersionModel":
        obj.validate()
        return cls(
            version_id=obj.version_id,
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


class HealthSourceModel(Base):
    """PostgreSQL table for health authority citations."""

    __tablename__ = "health_sources"

    source_id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    publication_date = Column(Date, nullable=True)
    access_date = Column(Date, nullable=True)
    jurisdiction = Column(String(128), nullable=True)
    metadata_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_domain(self) -> HealthSource:
        return HealthSource(
            source_id=self.source_id,
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
            source_id=obj.source_id,
            title=obj.title,
            publisher=obj.publisher,
            url=obj.url,
            publication_date=obj.publication_date,
            access_date=obj.access_date,
            jurisdiction=obj.jurisdiction,
            metadata_notes=obj.metadata_notes,
        )


class ReviewRecordModel(Base):
    """PostgreSQL table for editorial and medical content reviews."""

    __tablename__ = "review_records"

    review_id = Column(String(64), primary_key=True)
    lesson_id = Column(String(64), nullable=False, index=True)
    version_id = Column(String(64), nullable=False, index=True)
    editorial_status = Column(String(32), nullable=False)
    health_content_status = Column(String(32), nullable=False)
    reviewer_role = Column(String(32), nullable=False)
    review_date = Column(Date, nullable=False)
    next_review_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_domain(self) -> ReviewRecord:
        return ReviewRecord(
            review_id=self.review_id,
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
            review_id=obj.review_id,
            lesson_id=obj.lesson_id,
            version_id=obj.version_id,
            editorial_status=obj.editorial_status.value,
            health_content_status=obj.health_content_status.value,
            reviewer_role=obj.reviewer_role.value,
            review_date=obj.review_date,
            next_review_date=obj.next_review_date,
            notes=obj.notes,
        )


class UserModel(Base):
    """PostgreSQL table for application and staff users."""

    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True)
    username = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(64), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=False)
    setup_token_hash = Column(String(64), nullable=True, index=True)
    setup_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    neon_auth_user_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        nullable=True,
        unique=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    jurisdictions = relationship(
        "StaffJurisdictionModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    learner_progress = relationship(
        "LearnerProgressModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_domain(self) -> User:
        return User(
            user_id=self.user_id,
            username=self.username,
            display_name=self.display_name,
            role=UserRole(self.role),
            password_hash=self.password_hash,
            is_active=self.is_active,
            neon_auth_user_id=str(self.neon_auth_user_id) if self.neon_auth_user_id else None,
            must_change_password=bool(self.must_change_password),
        )

    @classmethod
    def from_domain(cls, obj: User) -> "UserModel":
        obj.validate()
        import uuid as _uuid
        neon_uuid = None
        if obj.neon_auth_user_id:
            neon_uuid = _uuid.UUID(str(obj.neon_auth_user_id)) if not isinstance(obj.neon_auth_user_id, _uuid.UUID) else obj.neon_auth_user_id
        return cls(
            user_id=obj.user_id,
            username=obj.username,
            display_name=obj.display_name,
            role=obj.role.value,
            password_hash=obj.password_hash,
            is_active=obj.is_active,
            neon_auth_user_id=neon_uuid,
            must_change_password=obj.must_change_password,
        )


class LearnerProgressModel(Base):
    """PostgreSQL table for cross-device synchronized learner progress."""

    __tablename__ = "learner_progress"

    progress_id = Column(String(64), primary_key=True)
    user_id = Column(
        String(64),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    version = Column(Integer, nullable=False, default=1)
    last_lesson = Column(JsonType, nullable=True)
    completed_lesson_ids = Column(JsonType, nullable=False, default=list)
    completed_activity_ids = Column(JsonType, nullable=False, default=list)
    achieved_milestones = Column(JsonType, nullable=False, default=list)
    client_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("UserModel", back_populates="learner_progress")


# ---------------------------------------------------------------------------
# Report a Concern & Staff Case Management Models
# ---------------------------------------------------------------------------


class ConcernReportModel(Base):
    """PostgreSQL table for citizen concerns."""

    __tablename__ = "concern_reports"

    report_id = Column(String(64), primary_key=True)
    reference_id = Column(String(32), nullable=False, unique=True, index=True)
    token_hash = Column(String(64), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    state = Column(String(64), nullable=False, index=True)
    district = Column(String(128), nullable=False, index=True)
    municipality = Column(String(128), nullable=True, index=True)
    locality = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    duration = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="received", index=True)
    assigned_handler_id = Column(String(64), nullable=True, index=True)
    assigned_handler_name = Column(String(255), nullable=True)
    assigned_jurisdiction = Column(String(128), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    citizen_reply_requested = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    events = relationship(
        "ConcernStatusEventModel",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ConcernStatusEventModel.created_at.asc()",
    )
    attachments = relationship(
        "ConcernAttachmentModel",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ConcernAttachmentModel.created_at.asc()",
    )


class ConcernStatusEventModel(Base):
    """Append-only audit trail and lifecycle transitions for concern reports."""

    __tablename__ = "concern_status_events"

    event_id = Column(String(64), primary_key=True)
    report_id = Column(
        String(64),
        ForeignKey("concern_reports.report_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    actor_type = Column(String(32), nullable=False)  # citizen, staff, system
    actor_id = Column(String(64), nullable=True)
    actor_name = Column(String(255), nullable=True)
    public_notes = Column(Text, nullable=True)       # Visible to citizens tracking report
    internal_notes = Column(Text, nullable=True)     # Strictly internal staff notes
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    report = relationship("ConcernReportModel", back_populates="events")


class ConcernAttachmentModel(Base):
    """Protected metadata for photo evidence stored outside public assets."""

    __tablename__ = "concern_attachments"

    attachment_id = Column(String(64), primary_key=True)
    report_id = Column(
        String(64),
        ForeignKey("concern_reports.report_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_key = Column(String(128), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=True)
    content_type = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_checksum = Column(String(64), nullable=False)
    uploaded_by = Column(String(32), nullable=False, default="citizen")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    report = relationship("ConcernReportModel", back_populates="attachments")


class StaffJurisdictionModel(Base):
    """Authorized jurisdiction scopes for municipal officers and staff."""

    __tablename__ = "staff_jurisdictions"

    id = Column(String(64), primary_key=True)
    user_id = Column(
        String(64),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state = Column(String(64), nullable=False)
    district = Column(String(128), nullable=False)
    municipality = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("UserModel", back_populates="jurisdictions")

    __table_args__ = (
        UniqueConstraint("user_id", "state", "district", "municipality", name="uq_staff_jurisdiction"),
    )


class StaffMfaModel(Base):
    """PostgreSQL table for staff Multi-Factor Authentication credentials."""

    __tablename__ = "staff_mfa_credentials"

    user_id = Column(
        String(64),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    totp_secret_encrypted = Column(Text, nullable=False)
    totp_enabled = Column(Boolean, nullable=False, default=False)
    recovery_codes_hash_json = Column(Text, nullable=False, default="[]")
    last_used_step = Column(Integer, nullable=False, default=0)
    session_revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Staff Application & Multi-Stage Vetting Models
# ---------------------------------------------------------------------------


class StaffApplicationModel(Base):
    """PostgreSQL table for public staff applications and multi-stage vetting."""

    __tablename__ = "staff_applications"

    application_id = Column(String(64), primary_key=True)
    reference_id = Column(String(32), nullable=False, unique=True, index=True)
    tracking_token_hash = Column(String(64), nullable=False, index=True)
    tracking_token_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    applicant_name = Column(String(255), nullable=False)
    applicant_email = Column(String(255), nullable=False, index=True)
    applicant_phone = Column(String(64), nullable=True)
    requested_role = Column(String(64), nullable=False, index=True)
    organization = Column(String(255), nullable=True)
    professional_title = Column(String(255), nullable=True)
    credential_reference = Column(Text, nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    statement_of_purpose = Column(Text, nullable=False)
    evidence_standards_acknowledged = Column(Boolean, nullable=False, default=False)
    child_safety_acknowledged = Column(Boolean, nullable=False, default=False)
    status = Column(String(32), nullable=False, default="pending_review", index=True)
    assigned_reviewer_id = Column(
        String(64),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_reviewer_name = Column(String(255), nullable=True)
    approved_role = Column(String(64), nullable=True)
    assigned_jurisdiction = Column(String(128), nullable=True)
    provisioned_user_id = Column(
        String(64),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason = Column(Text, nullable=True)
    info_request_details = Column(Text, nullable=True)
    applicant_notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    verification_checklist = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    history = relationship(
        "StaffApplicationHistoryModel",
        back_populates="application",
        order_by="StaffApplicationHistoryModel.created_at.asc()",
        cascade="all, delete-orphan",
    )


class StaffApplicationHistoryModel(Base):
    """PostgreSQL table recording state transitions and decision rationale for staff applications."""

    __tablename__ = "staff_application_history"

    history_id = Column(String(64), primary_key=True)
    application_id = Column(
        String(64),
        ForeignKey("staff_applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status = Column(String(32), nullable=False)
    to_status = Column(String(32), nullable=False)
    actor_id = Column(String(64), nullable=False)
    actor_name = Column(String(255), nullable=False)
    actor_role = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    decision_rationale = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    application = relationship("StaffApplicationModel", back_populates="history")


class EmailOtpChallengeModel(Base):
    """PostgreSQL / SQLite table for temporary cryptographic OTP verification challenges."""

    __tablename__ = "email_otp_challenges"

    challenge_id = Column(String(64), primary_key=True)
    email = Column(String(255), nullable=False, index=True)
    purpose = Column(String(32), nullable=False, index=True)  # 'signup' or 'reset_password'
    otp_hash = Column(String(64), nullable=False)  # SHA-256 hash of 6-digit OTP
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    is_verified = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    pending_payload = Column(JsonType, nullable=True)  # Stores registration data safely until verified
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class SmsOtpChallengeModel(Base):
    """PostgreSQL / SQLite table for temporary mobile phone SMS verification challenges."""

    __tablename__ = "sms_otp_challenges"

    challenge_id = Column(String(64), primary_key=True)
    phone_number = Column(String(32), nullable=False, index=True)
    purpose = Column(String(32), nullable=False, index=True)  # 'signup', 'role_request', or 'reset_password'
    otp_hash = Column(String(64), nullable=False)  # SHA-256 hash of 6-digit OTP
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    is_verified = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    pending_payload = Column(JsonType, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )




