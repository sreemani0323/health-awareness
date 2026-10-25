"""Add email and SMS OTP challenge tables for role-request and password recovery.

Revision ID: 0007_add_otp_challenge_tables
Revises: 0006_remediate_demo_accounts
Create Date: 2026-10-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007_add_otp_challenge_tables"
down_revision: Union[str, None] = "0006_remediate_demo_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # 1. Email OTP Challenges Table
    op.create_table(
        "email_otp_challenges",
        sa.Column("challenge_id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("otp_hash", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pending_payload", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_email_otp_challenges_email", "email_otp_challenges", ["email"])
    op.create_index("ix_email_otp_challenges_purpose", "email_otp_challenges", ["purpose"])
    op.create_index("ix_email_otp_challenges_expires_at", "email_otp_challenges", ["expires_at"])

    # 2. SMS OTP Challenges Table
    op.create_table(
        "sms_otp_challenges",
        sa.Column("challenge_id", sa.String(64), primary_key=True),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("otp_hash", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pending_payload", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sms_otp_challenges_phone_number", "sms_otp_challenges", ["phone_number"])
    op.create_index("ix_sms_otp_challenges_purpose", "sms_otp_challenges", ["purpose"])
    op.create_index("ix_sms_otp_challenges_expires_at", "sms_otp_challenges", ["expires_at"])


def downgrade() -> None:
    # Drop SMS OTP table & indexes
    op.drop_index("ix_sms_otp_challenges_expires_at", table_name="sms_otp_challenges")
    op.drop_index("ix_sms_otp_challenges_purpose", table_name="sms_otp_challenges")
    op.drop_index("ix_sms_otp_challenges_phone_number", table_name="sms_otp_challenges")
    op.drop_table("sms_otp_challenges")

    # Drop Email OTP table & indexes
    op.drop_index("ix_email_otp_challenges_expires_at", table_name="email_otp_challenges")
    op.drop_index("ix_email_otp_challenges_purpose", table_name="email_otp_challenges")
    op.drop_index("ix_email_otp_challenges_email", table_name="email_otp_challenges")
    op.drop_table("email_otp_challenges")
