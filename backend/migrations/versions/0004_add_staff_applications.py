"""Add staff applications and multi-stage vetting history tables.

Revision ID: 0004_add_staff_applications
Revises: 0003_add_staff_mfa
Create Date: 2026-10-20 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004_add_staff_applications"
down_revision: Union[str, None] = "0003_add_staff_mfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    json_col = sa.JSON().with_variant(JSONB, "postgresql")

    op.create_table(
        "staff_applications",
        sa.Column("application_id", sa.String(64), primary_key=True),
        sa.Column("reference_id", sa.String(32), nullable=False, unique=True),
        sa.Column("tracking_token_hash", sa.String(64), nullable=False),
        sa.Column("applicant_name", sa.String(255), nullable=False),
        sa.Column("applicant_email", sa.String(255), nullable=False),
        sa.Column("applicant_phone", sa.String(64), nullable=True),
        sa.Column("requested_role", sa.String(64), nullable=False),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("professional_title", sa.String(255), nullable=True),
        sa.Column("credential_reference", sa.Text(), nullable=True),
        sa.Column("portfolio_url", sa.String(500), nullable=True),
        sa.Column("statement_of_purpose", sa.Text(), nullable=False),
        sa.Column("evidence_standards_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("child_safety_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'pending_review'")),
        sa.Column("assigned_reviewer_id", sa.String(64), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_reviewer_name", sa.String(255), nullable=True),
        sa.Column("approved_role", sa.String(64), nullable=True),
        sa.Column("assigned_jurisdiction", sa.String(128), nullable=True),
        sa.Column("provisioned_user_id", sa.String(64), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("info_request_details", sa.Text(), nullable=True),
        sa.Column("applicant_notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("verification_checklist", json_col, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_staff_applications_ref_id", "staff_applications", ["reference_id"], unique=True)
    op.create_index("ix_staff_applications_email", "staff_applications", ["applicant_email"])
    op.create_index("ix_staff_applications_status", "staff_applications", ["status"])
    op.create_index("ix_staff_applications_token_hash", "staff_applications", ["tracking_token_hash"])

    op.create_table(
        "staff_application_history",
        sa.Column("history_id", sa.String(64), primary_key=True),
        sa.Column(
            "application_id",
            sa.String(64),
            sa.ForeignKey("staff_applications.application_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(32), nullable=False),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("actor_name", sa.String(255), nullable=False),
        sa.Column("actor_role", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column("metadata_json", json_col, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_staff_app_hist_app_id", "staff_application_history", ["application_id"])


def downgrade() -> None:
    op.drop_table("staff_application_history")
    op.drop_table("staff_applications")
