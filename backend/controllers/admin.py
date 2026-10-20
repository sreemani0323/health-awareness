"""Admin controller for Creator Studio administration.

Provides authenticated user management, role assignment, account activation,
and administrative health overview. All endpoints strictly require UserRole.ADMIN.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from flask import Response, request

logger = logging.getLogger(__name__)

from backend.controllers.auth import get_current_user, role_required
from backend.controllers.base import BaseHandler
from backend.domain import domain_services
from backend.domain.domain_objects import User, UserRole, VersionStatus, PublicationStatus
from backend.platform.security import hash_password
from backend.storage.storage_models import UserModel


def _serialize_user_admin(user: User) -> dict[str, Any]:
    """Serialize user for admin view, strictly omitting password_hash."""
    # Lookup created_at if available in Datastore model or PostgreSQL
    created_at_iso = None
    from google.cloud import ndb
    if ndb.get_context(raise_context_error=False) is None:
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as session:
                pg_u = session.query(PgUserModel).filter_by(user_id=user.user_id).first()
                if pg_u and pg_u.created_at:
                    created_at_iso = pg_u.created_at.isoformat()
        except Exception:
            pass
    else:
        model = UserModel.get_by_id(user.user_id)
        if model and model.created_at:
            created_at_iso = model.created_at.isoformat()

    return {
        "user_id": user.user_id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": created_at_iso,
    }


class AdminUserListHandler(BaseHandler):
    """GET /api/v1/admin/users — List all accounts.
    POST /api/v1/admin/users — Provision new contributor/reviewer account.
    """

    @role_required(UserRole.ADMIN)
    def get(self) -> tuple[Response, int]:
        """List all users."""
        users = domain_services.list_users()
        data = [_serialize_user_admin(u) for u in users]
        return self.render_json(data)

    @role_required(UserRole.ADMIN)
    def post(self) -> tuple[Response, int]:
        """Create a new user account."""
        body = request.get_json(silent=True)
        if not body:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        username = body.get("username", "").strip()
        display_name = body.get("display_name", "").strip()
        role_str = body.get("role", "").strip().lower()
        password = body.get("password", "").strip()

        if not username:
            return self.render_error("BAD_REQUEST", "username is required.", 400)
        if not display_name:
            return self.render_error("BAD_REQUEST", "display_name is required.", 400)
        if not password or len(password) < 8:
            return self.render_error(
                "BAD_REQUEST", "password must be at least 8 characters long.", 400
            )

        try:
            role = UserRole(role_str)
        except ValueError:
            return self.render_error(
                "BAD_REQUEST",
                f"Invalid role '{role_str}'. Must be one of: {[r.value for r in UserRole]}",
                400,
            )

        # Check existing username
        if domain_services.get_user_by_username(username) is not None:
            return self.render_error(
                "BAD_REQUEST", f"Username '{username}' is already taken.", 400
            )

        user_id = f"user-{uuid.uuid4().hex[:12]}"
        pwd_hash = hash_password(password)

        try:
            new_user = User(
                user_id=user_id,
                username=username,
                display_name=display_name,
                role=role,
                password_hash=pwd_hash,
                is_active=True,
            )
            created = domain_services.create_user(new_user)
            return self.render_json(_serialize_user_admin(created), status_code=201)
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)


class AdminUserRoleHandler(BaseHandler):
    """PUT /api/v1/admin/users/<user_id>/role — Update account role."""

    @role_required(UserRole.ADMIN)
    def put(self, user_id: str) -> tuple[Response, int]:
        body = request.get_json(silent=True)
        if not body or "role" not in body:
            return self.render_error("BAD_REQUEST", "role field is required.", 400)

        role_str = body["role"].strip().lower()
        try:
            new_role = UserRole(role_str)
        except ValueError:
            return self.render_error(
                "BAD_REQUEST",
                f"Invalid role '{role_str}'. Must be one of: {[r.value for r in UserRole]}",
                400,
            )

        try:
            updated = domain_services.update_user_role(user_id, new_role)
            return self.render_json(_serialize_user_admin(updated))
        except ValueError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)


class AdminUserStatusHandler(BaseHandler):
    """PUT /api/v1/admin/users/<user_id>/status — Activate or deactivate account."""

    @role_required(UserRole.ADMIN)
    def put(self, user_id: str) -> tuple[Response, int]:
        body = request.get_json(silent=True)
        if not body or "is_active" not in body:
            return self.render_error("BAD_REQUEST", "is_active field is required.", 400)

        is_active = body["is_active"]
        if not isinstance(is_active, bool):
            return self.render_error("BAD_REQUEST", "is_active must be a boolean.", 400)

        current_user = get_current_user()
        if current_user and current_user.user_id == user_id and not is_active:
            return self.render_error(
                "BAD_REQUEST",
                "Administrators cannot deactivate their own active account.",
                400,
            )

        try:
            updated = domain_services.set_user_active_status(user_id, is_active)
            return self.render_json(_serialize_user_admin(updated))
        except ValueError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)


class AdminOverviewHandler(BaseHandler):
    """GET /api/v1/admin/overview — Summary metrics for administrator dashboard."""

    @role_required(UserRole.ADMIN)
    def get(self) -> tuple[Response, int]:
        users = domain_services.list_users()
        active_count = sum(1 for u in users if u.is_active)
        deactivated_count = len(users) - active_count
        by_role = {
            "contributor": sum(1 for u in users if u.role == UserRole.CONTRIBUTOR),
            "reviewer": sum(1 for u in users if u.role == UserRole.REVIEWER),
            "admin": sum(1 for u in users if u.role == UserRole.ADMIN),
        }

        topics = domain_services.list_all_topics()
        draft_topics = sum(1 for t in topics if t.status == PublicationStatus.DRAFT)
        published_topics = sum(1 for t in topics if t.status == PublicationStatus.PUBLISHED)

        submitted_versions = domain_services.list_submitted_versions()

        overview = {
            "total_users": len(users),
            "active_users": active_count,
            "deactivated_users": deactivated_count,
            "users_by_role": by_role,
            "total_topics": len(topics),
            "draft_topics": draft_topics,
            "published_topics": published_topics,
            "pending_reviews": len(submitted_versions),
        }
        return self.render_json(overview)


class AdminMfaResetHandler(BaseHandler):
    """POST /api/v1/admin/users/<user_id>/mfa/reset — Reset MFA for locked-out staff."""

    @role_required(UserRole.ADMIN)
    def post(self, user_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        admin_id = current_user.user_id if current_user else "admin"

        # Verify target user exists
        target_user = domain_services.get_user(user_id)
        if target_user is None:
            try:
                from backend.storage.db import get_db_session
                from backend.storage.postgres_models import UserModel as PgUserModel
                with get_db_session() as db_sess:
                    pg_u = db_sess.query(PgUserModel).filter_by(user_id=user_id).first()
                    if not pg_u:
                        return self.render_error("NOT_FOUND", f"User '{user_id}' does not exist.", 404)
            except Exception:
                return self.render_error("NOT_FOUND", f"User '{user_id}' does not exist.", 404)

        from backend.platform.mfa_service import get_mfa_service, MfaStorageError
        mfa_service = get_mfa_service()

        try:
            success = mfa_service.admin_reset_mfa(target_user_id=user_id, admin_user_id=admin_id)
        except MfaStorageError as exc:
            logger.error("Database error during admin MFA reset for user '%s': %s", user_id, exc)
            return self.render_error(
                "SERVICE_UNAVAILABLE", "Authentication service temporarily unavailable.", 503
            )
        except Exception as exc:
            logger.error("Failed to reset MFA for user '%s': %s", user_id, exc)
            return self.render_error("INTERNAL_SERVER_ERROR", "Failed to reset MFA.", 500)

        if success:
            return self.render_json({
                "message": f"MFA has been successfully reset for user '{user_id}'.",
                "user_id": user_id,
                "mfa_enabled": False,
            })
        return self.render_error("INTERNAL_SERVER_ERROR", "Failed to reset MFA.", 500)


class AdminThrottleResetHandler(BaseHandler):
    """POST /api/v1/admin/users/<username>/throttle/reset — Clear failed login lockout."""

    @role_required(UserRole.ADMIN)
    def post(self, username: str) -> tuple[Response, int]:
        current_user = get_current_user()
        admin_id = current_user.user_id if current_user else "admin"

        # Verify target user exists
        target_user = domain_services.get_user_by_username(username)
        if target_user is None:
            try:
                from backend.storage.db import get_db_session
                from backend.storage.postgres_models import UserModel as PgUserModel
                with get_db_session() as db_sess:
                    pg_u = db_sess.query(PgUserModel).filter_by(username=username).first()
                    if not pg_u:
                        return self.render_error("NOT_FOUND", f"User '{username}' does not exist.", 404)
            except Exception:
                return self.render_error("NOT_FOUND", f"User '{username}' does not exist.", 404)

        from backend.platform.login_throttle import get_login_throttle_manager
        from backend.platform.audit_log import SecurityAuditEvent, log_security_event

        throttle_mgr = get_login_throttle_manager()
        throttle_mgr.admin_reset_throttle(username)

        log_security_event(
            SecurityAuditEvent.THROTTLE_ADMIN_RESET,
            actor_id=admin_id,
            target_id=username,
            status="SUCCESS",
        )

        return self.render_json({
            "message": f"Login throttling and lockouts cleared for user '{username}'.",
            "username": username,
        })

