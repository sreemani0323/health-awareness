"""Admin controller for Creator Studio administration.

Provides authenticated user management, role assignment, account activation,
and administrative health overview. All endpoints strictly require UserRole.ADMIN.
"""

from __future__ import annotations

import uuid
from typing import Any

from flask import Response, request

from backend.controllers.auth import get_current_user, role_required
from backend.controllers.base import BaseHandler
from backend.domain import domain_services
from backend.domain.domain_objects import User, UserRole, VersionStatus, PublicationStatus
from backend.platform.security import hash_password
from backend.storage.storage_models import UserModel


def _serialize_user_admin(user: User) -> dict[str, Any]:
    """Serialize user for admin view, strictly omitting password_hash."""
    # Lookup created_at if available in Datastore model
    created_at_iso = None
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
