"""Remove SMS OTP challenge table for pure email-based verification.

Revision ID: 0008_remove_sms_otp_challenges
Revises: 0007_add_otp_challenge_tables
Create Date: 2026-10-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0008_remove_sms_otp_challenges"
down_revision: Union[str, None] = "0007_add_otp_challenge_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # Drop sms_otp_challenges table completely
    op.execute("DROP TABLE IF EXISTS sms_otp_challenges CASCADE;")


def downgrade() -> None:
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
