"""Remediate and deactivate legacy demo accounts.

Revision ID: 0006_remediate_demo_accounts
Revises: 0005_add_account_setup_and_tracking_expiry
Create Date: 2026-10-20 22:15:00.000000

"""
from typing import Sequence, Union
from datetime import datetime, timezone
import secrets

from alembic import op
import sqlalchemy as sa
from backend.platform.security import hash_password

revision: str = "0006_remediate_demo_accounts"
down_revision: Union[str, None] = "0005_add_account_setup_and_tracking_expiry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely deactivate and rotate passwords for known legacy demo accounts in production
    bind = op.get_bind()
    now = datetime.now(timezone.utc)
    demo_usernames = ("reviewer", "contributor", "admin")
    
    for uname in demo_usernames:
        random_hash = hash_password(f"REVOKED_{secrets.token_urlsafe(32)}")
        bind.execute(
            sa.text(
                "UPDATE users SET is_active = false, password_hash = :hash "
                "WHERE username = :uname AND (user_id LIKE 'user-%' OR username = :uname)"
            ),
            {"hash": random_hash, "uname": uname},
        )



def downgrade() -> None:
    # Security deactivations are irreversible via migration downgrade
    pass
