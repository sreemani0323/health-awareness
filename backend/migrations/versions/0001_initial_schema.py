"""Initial schema for HealthAware PostgreSQL persistence and Case Management.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # 1. Topics
    op.create_table(
        "topics",
        sa.Column("topic_id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url_slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("cover_image_ref", sa.String(255), nullable=True),
        sa.Column("cover_image_alt", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_topics_display_order", "topics", ["display_order"])
    op.create_index("ix_topics_status", "topics", ["status"])

    # 2. Lessons
    op.create_table(
        "lessons",
        sa.Column("lesson_id", sa.String(64), primary_key=True),
        sa.Column(
            "topic_id",
            sa.String(64),
            sa.ForeignKey("topics.topic_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("published_version_id", sa.String(64), nullable=True),
        sa.Column("draft_version_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lessons_topic_id", "lessons", ["topic_id"])
    op.create_index("ix_lessons_display_order", "lessons", ["display_order"])

    # 3. Lesson Versions
    op.create_table(
        "lesson_versions",
        sa.Column("version_id", sa.String(64), primary_key=True),
        sa.Column(
            "lesson_id",
            sa.String(64),
            sa.ForeignKey("lessons.lesson_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("language", sa.String(16), nullable=False, server_default="en"),
        sa.Column("learning_objectives", json_type, nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("cards_json", json_type, nullable=False),
        sa.Column("source_ids", json_type, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("author_id", sa.String(64), nullable=True),
        sa.Column("submitted_by", sa.String(64), nullable=True),
        sa.Column("review_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lesson_versions_lesson_id", "lesson_versions", ["lesson_id"])
    op.create_index("ix_lesson_versions_status", "lesson_versions", ["status"])
    op.create_index("idx_lesson_version_order", "lesson_versions", ["lesson_id", "version_number"])

    # 4. Health Sources
    op.create_table(
        "health_sources",
        sa.Column("source_id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("publisher", sa.String(255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("access_date", sa.Date(), nullable=True),
        sa.Column("jurisdiction", sa.String(128), nullable=True),
        sa.Column("metadata_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Review Records
    op.create_table(
        "review_records",
        sa.Column("review_id", sa.String(64), primary_key=True),
        sa.Column("lesson_id", sa.String(64), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=False),
        sa.Column("editorial_status", sa.String(32), nullable=False),
        sa.Column("health_content_status", sa.String(32), nullable=False),
        sa.Column("reviewer_role", sa.String(32), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_records_lesson_id", "review_records", ["lesson_id"])
    op.create_index("ix_review_records_version_id", "review_records", ["version_id"])

    # 6. Users
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(64), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_role", "users", ["role"])

    # 7. Concern Reports
    op.create_table(
        "concern_reports",
        sa.Column("report_id", sa.String(64), primary_key=True),
        sa.Column("reference_id", sa.String(32), nullable=False, unique=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("district", sa.String(128), nullable=False),
        sa.Column("municipality", sa.String(128), nullable=True),
        sa.Column("locality", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="received"),
        sa.Column("assigned_handler_id", sa.String(64), nullable=True),
        sa.Column("assigned_handler_name", sa.String(255), nullable=True),
        sa.Column("assigned_jurisdiction", sa.String(128), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("citizen_reply_requested", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_concern_reports_reference_id", "concern_reports", ["reference_id"])
    op.create_index("ix_concern_reports_token_hash", "concern_reports", ["token_hash"])
    op.create_index("ix_concern_reports_status", "concern_reports", ["status"])
    op.create_index("ix_concern_reports_category", "concern_reports", ["category"])
    op.create_index("ix_concern_reports_district", "concern_reports", ["district"])
    op.create_index("ix_concern_reports_created_at", "concern_reports", ["created_at"])

    # 8. Concern Status Events (Append-only audit trail)
    op.create_table(
        "concern_status_events",
        sa.Column("event_id", sa.String(64), primary_key=True),
        sa.Column(
            "report_id",
            sa.String(64),
            sa.ForeignKey("concern_reports.report_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=True),
        sa.Column("actor_name", sa.String(255), nullable=True),
        sa.Column("public_notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_concern_status_events_report_id", "concern_status_events", ["report_id"])
    op.create_index("ix_concern_status_events_created_at", "concern_status_events", ["created_at"])

    # 9. Concern Attachments
    op.create_table(
        "concern_attachments",
        sa.Column("attachment_id", sa.String(64), primary_key=True),
        sa.Column(
            "report_id",
            sa.String(64),
            sa.ForeignKey("concern_reports.report_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(128), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_checksum", sa.String(64), nullable=False),
        sa.Column("uploaded_by", sa.String(32), nullable=False, server_default="citizen"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_concern_attachments_report_id", "concern_attachments", ["report_id"])

    # 10. Staff Jurisdictions
    op.create_table(
        "staff_jurisdictions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(64),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("district", sa.String(128), nullable=False),
        sa.Column("municipality", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "state", "district", "municipality", name="uq_staff_jurisdiction"),
    )
    op.create_index("ix_staff_jurisdictions_user_id", "staff_jurisdictions", ["user_id"])


def downgrade() -> None:
    op.drop_table("staff_jurisdictions")
    op.drop_table("concern_attachments")
    op.drop_table("concern_status_events")
    op.drop_table("concern_reports")
    op.drop_table("users")
    op.drop_table("review_records")
    op.drop_table("health_sources")
    op.drop_table("lesson_versions")
    op.drop_table("lessons")
    op.drop_table("topics")
