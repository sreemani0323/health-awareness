"""CLI tool to provision or update an administrator account for HealthAware.

Writes directly to PostgreSQL via SQLAlchemy ORM (with Datastore fallback if running legacy emulator).

Usage:
    python backend/provision_admin.py --username admin [--password <password>] [--name "Administrator"] [--database-url <url>]

If --password is not provided on the command line, it will prompt securely via getpass.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.domain.domain_objects import User, UserRole
from backend.platform.security import hash_password
from backend.storage.db import create_app_engine, get_database_url, get_db_session, init_db
from backend.storage.postgres_models import UserModel


def _provision_postgres(username: str, password: str, display_name: str | None = None, database_url: str | None = None) -> bool:
    """Provisions or updates an administrator account in PostgreSQL."""
    target_url = database_url or get_database_url()
    if not target_url:
        return False

    user_id = f"user-{username.strip().lower()}"
    display = display_name or username.strip().capitalize()
    pw_hash = hash_password(password)

    engine = create_app_engine(target_url)
    init_db(engine)

    with get_db_session(engine) as session:
        existing = session.query(UserModel).filter_by(username=username.strip()).first()
        if existing:
            existing.display_name = display
            existing.role = UserRole.ADMIN.value
            existing.password_hash = pw_hash
            existing.is_active = True
            session.commit()
            print(f"[SUCCESS] Existing PostgreSQL user '{username}' promoted to ADMINISTRATOR and password updated.")
        else:
            new_user = UserModel(
                user_id=user_id,
                username=username.strip(),
                display_name=display,
                role=UserRole.ADMIN.value,
                password_hash=pw_hash,
                is_active=True,
            )
            session.add(new_user)
            session.commit()
            print(f"[SUCCESS] Successfully provisioned new PostgreSQL ADMINISTRATOR account '{username}' (ID: {user_id}).")

    return True


def _provision_datastore(username: str, password: str, display_name: str | None = None) -> None:
    """Fallback provisioner for legacy Datastore emulator."""
    from backend.domain import domain_services
    from backend.platform.ndb_client import get_ndb_client
    from google.cloud import ndb

    def _do():
        user_id = f"user-{username.strip().lower()}"
        display = display_name or username.strip().capitalize()
        pw_hash = hash_password(password)

        existing = domain_services.get_user_by_username(username.strip())
        if existing:
            model = domain_services.UserModel.get_by_id(existing.user_id)
            if model:
                model.display_name = display
                model.role = UserRole.ADMIN.value
                model.password_hash = pw_hash
                model.put()
            print(f"[SUCCESS] Existing Datastore user '{username}' promoted to ADMINISTRATOR and password updated.")
        else:
            new_user = User(
                user_id=user_id,
                username=username.strip(),
                display_name=display,
                role=UserRole.ADMIN,
                password_hash=pw_hash,
                is_active=True,
            )
            domain_services.create_user(new_user)
            print(f"[SUCCESS] Successfully provisioned new Datastore ADMINISTRATOR account '{username}' (ID: {user_id}).")

    if ndb.get_context(raise_context_error=False) is not None:
        _do()
    else:
        client = get_ndb_client()
        with client.context():
            _do()


def provision_admin(username: str, password: str, display_name: str | None = None, database_url: str | None = None) -> None:
    if not username or not username.strip():
        print("[ERROR] Username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if not password or len(password) < 12:
        print("[ERROR] Administrator password must be at least 12 characters long according to OWASP guidelines.", file=sys.stderr)
        sys.exit(1)

    # 1. Attempt PostgreSQL provisioning first
    try:
        if _provision_postgres(username, password, display_name, database_url):
            return
    except Exception as e:
        print(f"[INFO] PostgreSQL provisioning attempt: {e}")

    # 2. Fall back to Datastore if PostgreSQL is not configured
    try:
        _provision_datastore(username, password, display_name)
    except Exception as e:
        print(f"[ERROR] Failed to provision admin in either PostgreSQL or Datastore: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision first administrator account for HealthAware.")
    parser.add_argument("--username", "-u", required=True, help="Administrator username")
    parser.add_argument("--password", "-p", default=None, help="Password (interactive prompt preferred)")
    parser.add_argument("--name", "-n", default=None, help="Display name for administrator")
    parser.add_argument("--database-url", default=None, help="Target PostgreSQL connection URL")

    args = parser.parse_args()

    password = args.password or os.environ.get("INITIAL_ADMIN_PASSWORD")
    if password:
        if not args.password:
            print("[INFO] Read admin password from INITIAL_ADMIN_PASSWORD environment variable.")
        else:
            print(
                "[WARNING] Supplying passwords via command-line arguments can expose credentials in process lists and shell history. Prefer interactive entry.",
                file=sys.stderr,
            )
    else:
        password = getpass.getpass(f"Enter password for admin '{args.username}' (min 12 chars): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    provision_admin(args.username, password, args.name, args.database_url)


if __name__ == "__main__":
    main()
