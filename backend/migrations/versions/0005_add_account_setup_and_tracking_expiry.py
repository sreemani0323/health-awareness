"""Add account setup state and staff application tracking expiry columns.

Revision ID: 0005_add_account_setup_and_tracking_expiry
Revises: 0004_add_staff_applications
Create Date: 2026-10-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_add_account_setup_and_tracking_expiry"
down_revision: Union[str, None] = "0004_add_staff_applications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. User account-setup columns
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("setup_token_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("setup_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_setup_token_hash", "users", ["setup_token_hash"])

    # 2. Staff application tracking token expiration column
    op.add_column(
        "staff_applications",
        sa.Column("tracking_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_staff_applications_tracking_expires", "staff_applications", ["tracking_token_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_staff_applications_tracking_expires", table_name="staff_applications")
    op.drop_column("staff_applications", "tracking_token_expires_at")
    op.drop_index("ix_users_setup_token_hash", table_name="users")
    op.drop_column("users", "setup_token_expires_at")
    op.drop_column("users", "setup_token_hash")
    op.drop_column("users", "must_change_password")
