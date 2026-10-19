"""CLI tool to provision or update user accounts (contributor, reviewer, admin, etc.) for HealthAware.

Writes directly to PostgreSQL via SQLAlchemy ORM (with Datastore fallback if running legacy emulator).

Usage:
    python backend/provision_user.py --username contributor [--role contributor] [--password <password>] [--name "Contributor"] [--database-url <url>] [--demo-password-opt-in]

If --password is not provided on the command line or environment, it will prompt securely via getpass.
Known predictable demo passwords (e.g. contributor123) strictly require the explicit --demo-password-opt-in flag.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

# Ensure repo root is on sys.path and remove script directory to prevent shadowing stdlib platform
backend_dir = os.path.abspath(os.path.dirname(__file__))
while backend_dir in sys.path:
    sys.path.remove(backend_dir)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

if "platform" in sys.modules and not hasattr(sys.modules["platform"], "python_implementation"):
    del sys.modules["platform"]
import platform

from backend.domain.domain_objects import User, UserRole
from backend.platform.security import hash_password
from backend.storage.db import create_app_engine, get_database_url, get_db_session, init_db
from backend.storage.postgres_models import UserModel

PREDICTABLE_PASSWORDS = frozenset({
    "contributor123",
    "reviewer123",
    "admin123",
    "password",
    "password123",
    "changeme",
    "healthaware123",
    "12345678",
})


def is_predictable_password(password: str, username: str, role: str) -> bool:
    """Check if the provided password matches known predictable demo credentials."""
    pwd_lower = password.strip().lower()
    if pwd_lower in PREDICTABLE_PASSWORDS:
        return True
    if pwd_lower == f"{username.strip().lower()}123":
        return True
    if pwd_lower == f"{role.strip().lower()}123":
        return True
    return False


def _provision_postgres(
    username: str,
    password: str,
    role: UserRole,
    display_name: str | None = None,
    database_url: str | None = None,
) -> bool:
    """Provisions or updates a user account in PostgreSQL."""
    target_url = database_url or get_database_url()
    if not target_url:
        return False

    clean_user = username.strip()
    user_id = f"user-{clean_user.lower()}"
    display = display_name or clean_user.capitalize()
    pw_hash = hash_password(password)

    engine = create_app_engine(target_url)
    init_db(engine)

    with get_db_session(engine) as session:
        existing = session.query(UserModel).filter_by(username=clean_user).first()
        if existing:
            existing.display_name = display
            existing.role = role.value
            existing.password_hash = pw_hash
            existing.is_active = True
            session.commit()
            print(f"[SUCCESS] Existing PostgreSQL user '{clean_user}' updated with role '{role.value.upper()}'.")
        else:
            new_user = UserModel(
                user_id=user_id,
                username=clean_user,
                display_name=display,
                role=role.value,
                password_hash=pw_hash,
                is_active=True,
            )
            session.add(new_user)
            session.commit()
            print(f"[SUCCESS] Successfully provisioned new PostgreSQL user '{clean_user}' with role '{role.value.upper()}' (ID: {user_id}).")

    return True


def _provision_datastore(
    username: str,
    password: str,
    role: UserRole,
    display_name: str | None = None,
) -> None:
    """Fallback provisioner for legacy Datastore emulator."""
    from backend.domain import domain_services
    from backend.platform.ndb_client import get_ndb_client
    from google.cloud import ndb

    clean_user = username.strip()
    user_id = f"user-{clean_user.lower()}"
    display = display_name or clean_user.capitalize()
    pw_hash = hash_password(password)

    def _do():
        existing = domain_services.get_user_by_username(clean_user)
        if existing:
            model = domain_services.UserModel.get_by_id(existing.user_id)
            if model:
                model.display_name = display
                model.role = role.value
                model.password_hash = pw_hash
                model.put()
            print(f"[SUCCESS] Existing Datastore user '{clean_user}' updated with role '{role.value.upper()}'.")
        else:
            new_user = User(
                user_id=user_id,
                username=clean_user,
                display_name=display,
                role=role,
                password_hash=pw_hash,
                is_active=True,
            )
            domain_services.create_user(new_user)
            print(f"[SUCCESS] Successfully provisioned new Datastore user '{clean_user}' with role '{role.value.upper()}' (ID: {user_id}).")

    if ndb.get_context(raise_context_error=False) is not None:
        _do()
    else:
        client = get_ndb_client()
        with client.context():
            _do()


def provision_user(
    username: str,
    password: str,
    role: str = "contributor",
    display_name: str | None = None,
    database_url: str | None = None,
    demo_password_opt_in: bool = False,
) -> bool:
    """Validates and provisions a user into PostgreSQL (or Datastore fallback).

    Enforces:
    - Non-empty username
    - Valid UserRole enum
    - Minimum password length (12 for admin, 8 for other roles)
    - Rejection of predictable demo passwords unless demo_password_opt_in is True.
    """
    clean_username = username.strip() if username else ""
    if not clean_username:
        print("[ERROR] Username cannot be empty.", file=sys.stderr)
        raise ValueError("Username cannot be empty.")

    try:
        user_role = UserRole(role.strip().lower())
    except (ValueError, AttributeError):
        valid_roles = [r.value for r in UserRole]
        print(f"[ERROR] Invalid role '{role}'. Must be one of: {valid_roles}", file=sys.stderr)
        raise ValueError(f"Invalid role '{role}'. Must be one of: {valid_roles}")

    # Check predictable demo passwords
    if is_predictable_password(password, clean_username, user_role.value):
        if not demo_password_opt_in:
            err_msg = (
                f"[ERROR] The password supplied is a known predictable demo credential. "
                f"To provision an account with this password for controlled demonstration/evaluation, "
                f"you must explicitly supply the --demo-password-opt-in flag. "
                f"For production, use a strong, unique password."
            )
            print(err_msg, file=sys.stderr)
            raise ValueError(err_msg)
        else:
            print(
                "[SECURITY WARNING] Provisioning with a known demo password (--demo-password-opt-in active). "
                "Predictable credentials must NEVER be used in permanent public production deployments.",
                file=sys.stderr,
            )

    # Password length validation
    min_length = 12 if user_role == UserRole.ADMIN else 8
    if not password or len(password) < min_length:
        err_msg = f"[ERROR] Password for role '{user_role.value}' must be at least {min_length} characters long."
        print(err_msg, file=sys.stderr)
        raise ValueError(err_msg)

    target_url = database_url or get_database_url()
    if target_url:
        try:
            return _provision_postgres(clean_username, password, user_role, display_name, target_url)
        except Exception as e:
            print(f"[ERROR] PostgreSQL provisioning failed: {e}", file=sys.stderr)
            raise RuntimeError(f"PostgreSQL provisioning failed: {e}")

    # Fall back to Datastore only if PostgreSQL is not configured
    try:
        _provision_datastore(clean_username, password, user_role, display_name)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to provision user in Datastore: {e}", file=sys.stderr)
        raise RuntimeError(f"Failed to provision user: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision or update a user account for HealthAware.")
    parser.add_argument("--username", "-u", required=True, help="Account username (e.g. contributor)")
    parser.add_argument("--role", "-r", default="contributor", choices=[r.value for r in UserRole], help="Account role (default: contributor)")
    parser.add_argument("--password", "-p", default=None, help="Password (interactive prompt preferred)")
    parser.add_argument("--name", "-n", default=None, help="Display name for user")
    parser.add_argument("--database-url", default=None, help="Target PostgreSQL connection URL")
    parser.add_argument(
        "--demo-password-opt-in",
        action="store_true",
        default=False,
        help="Explicitly opt in to using a known predictable demo password (e.g. contributor123) for controlled testing/evaluation.",
    )

    args = parser.parse_args()

    password = args.password or os.environ.get("PROVISION_USER_PASSWORD")
    if not password and args.role == "admin":
        password = os.environ.get("INITIAL_ADMIN_PASSWORD")

    if password:
        if not args.password:
            print("[INFO] Read password from environment variable.")
        else:
            print(
                "[WARNING] Supplying passwords via command-line arguments can expose credentials in process lists and shell history. Prefer interactive entry.",
                file=sys.stderr,
            )
    else:
        min_len = 12 if args.role == "admin" else 8
        password = getpass.getpass(f"Enter password for '{args.username}' (role: {args.role}, min {min_len} chars): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    try:
        provision_user(
            username=args.username,
            password=password,
            role=args.role,
            display_name=args.name,
            database_url=args.database_url,
            demo_password_opt_in=args.demo_password_opt_in,
        )
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
