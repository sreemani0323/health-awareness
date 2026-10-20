"""Add staff multi-factor authentication (MFA / TOTP) credentials table.

Revision ID: 0003_add_staff_mfa
Revises: 0002_add_learner_support
Create Date: 2026-10-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_staff_mfa"
down_revision: Union[str, None] = "0002_add_learner_support"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure alembic_version column is wide enough for descriptive revision slugs (>32 chars)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64);")

    op.create_table(
        "staff_mfa_credentials",
        sa.Column(
            "user_id",
            sa.String(64),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("totp_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recovery_codes_hash_json", sa.Text(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("last_used_step", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("session_revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("staff_mfa_credentials")
