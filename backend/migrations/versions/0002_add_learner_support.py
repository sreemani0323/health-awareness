"""Add learner role support and Neon Auth identity mapping.

Revision ID: 0002_add_learner_support
Revises: 0001_initial_schema
Create Date: 2026-10-19 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002_add_learner_support"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # 1. Identity Mapping Column on public.users
    op.add_column(
        "users",
        sa.Column(
            "neon_auth_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_users_neon_auth_user_id",
        "users",
        ["neon_auth_user_id"],
        unique=True,
    )

    # 2. Relax password_hash to nullable for external auth accounts
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=True,
    )

    # 3. Dedicated Learner Progress Table
    op.create_table(
        "learner_progress",
        sa.Column("progress_id", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(64),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_lesson", json_type, nullable=True),
        sa.Column("completed_lesson_ids", json_type, nullable=False, server_default="[]"),
        sa.Column("completed_activity_ids", json_type, nullable=False, server_default="[]"),
        sa.Column("achieved_milestones", json_type, nullable=False, server_default="[]"),
        sa.Column("client_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_learner_progress_user_id",
        "learner_progress",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    # -----------------------------------------------------------------------
    # Safe Downgrade Guard
    # -----------------------------------------------------------------------
    # If any learner rows exist with NULL password_hash or neon_auth_user_id,
    # restoring NOT NULL on password_hash would fail with constraint violations,
    # and dropping columns would permanently destroy learner progress/identities.
    # To protect learner data and prevent partial migration failures, refuse downgrade.
    context = op.get_context()
    if not context.as_sql:
        conn = op.get_bind()

        null_passwords = conn.execute(
            sa.text("SELECT COUNT(*) FROM users WHERE password_hash IS NULL")
        ).scalar()
        if null_passwords and null_passwords > 0:
            raise RuntimeError(
                f"Downgrade aborted: {null_passwords} user record(s) exist with NULL password_hash. "
                "Restoring NOT NULL on users.password_hash without data resolution is prohibited. "
                "Automatic deletion of learner accounts or progress is forbidden. "
                "Operator intervention is required: archive learner data and remove or resolve records "
                "before executing downgrade."
            )

        learner_count = conn.execute(
            sa.text("SELECT COUNT(*) FROM users WHERE neon_auth_user_id IS NOT NULL OR role = 'learner'")
        ).scalar()
        if learner_count and learner_count > 0:
            raise RuntimeError(
                f"Downgrade aborted: {learner_count} learner user record(s) exist. "
                "Dropping neon_auth_user_id and learner_progress would destroy learner identities and progress. "
                "Automatic deletion of learner accounts or progress is forbidden. "
                "Operator intervention is required: archive learner data and remove records before executing downgrade."
            )

    op.drop_table("learner_progress")
    op.drop_index("ix_users_neon_auth_user_id", table_name="users")
    op.drop_column("users", "neon_auth_user_id")
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=False,
    )
