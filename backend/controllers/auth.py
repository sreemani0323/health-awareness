"""Authentication controller for Creator Studio.

Provides session-based authentication using Flask's built-in signed-cookie session
mechanism, PBKDF2-HMAC-SHA256 password verification, active account checking,
and CSRF protection with double-submit cookies.
"""

from __future__ import annotations

import functools
import secrets
from typing import Callable

from flask import Response, current_app, jsonify, request, session

from backend.controllers.base import BaseHandler
from backend.domain import domain_services
from backend.domain.domain_objects import User, UserRole


def get_current_user() -> User | None:
    """Retrieve the current user from session, verifying against Datastore.

    Validates that:
    1. A user_id exists in the session.
    2. The user entity exists in Datastore.
    3. The account is active (is_active is True).
    4. The session role reflects the database record.

    If the user has been deleted or deactivated, the session is cleared immediately.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    # 1. Check PostgreSQL persistence
    try:
        from backend.storage.db import get_db_session
        from backend.storage.postgres_models import UserModel as PgUserModel
        with get_db_session() as db_sess:
            pg_u = db_sess.query(PgUserModel).filter_by(user_id=user_id).first()
            if pg_u is not None:
                if not pg_u.is_active:
                    session.clear()
                    return None
                user = pg_u.to_domain()
                if session.get("role") != user.role.value:
                    session["role"] = user.role.value
                return user
    except Exception:
        pass

    # 2. Fall back to Datastore domain services
    user = domain_services.get_user(user_id)
    if user is None or not user.is_active:
        session.clear()
        return None

    # Keep session role consistent with Datastore
    if session.get("role") != user.role.value:
        session["role"] = user.role.value

    return user


def auth_required(fn: Callable) -> Callable:
    """Decorator requiring an authenticated session."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required.",
                }
            }), 401
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles: UserRole) -> Callable:
    """Decorator requiring the current user to have one of the specified roles."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return jsonify({
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                    }
                }), 401
            if user.role not in roles:
                return jsonify({
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Requires one of: {[r.value for r in roles]}",
                    }
                }), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _issue_csrf_token(response: Response) -> str:
    """Ensure a CSRF token exists in the session and attach the XSRF-TOKEN cookie."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["csrf_token"] = token

    is_secure = current_app.config.get("SESSION_COOKIE_SECURE", False)
    response.set_cookie(
        "XSRF-TOKEN",
        token,
        httponly=False,  # Must be readable by Angular HttpClient
        samesite="Lax",
        secure=is_secure,
        path="/",
    )
    return token


from backend.platform.rate_limiter import limiter


class LoginHandler(BaseHandler):
    """POST /api/v1/auth/login — Authenticate and create session."""

    decorators = [limiter.limit("5 per 15 minutes")]

    def post(self) -> tuple[Response, int]:

        data = request.get_json(silent=True)
        if not data:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return self.render_error(
                "BAD_REQUEST", "username and password are required.", 400
            )

        # Authenticate against PostgreSQL first
        user = None
        pg_user_found = False
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            from backend.platform.security import verify_password
            with get_db_session() as db_sess:
                pg_u = db_sess.query(PgUserModel).filter_by(username=username).first()
                if pg_u is not None:
                    pg_user_found = True
                    if pg_u.is_active and verify_password(password, pg_u.password_hash):
                        user = pg_u.to_domain()
        except Exception:
            pass

        # Fall back to Datastore domain services ONLY if not already handled in PostgreSQL
        if user is None and not pg_user_found:
            try:
                user = domain_services.authenticate_user(username, password)
            except Exception:
                user = None

        if user is None:
            return self.render_error(
                "UNAUTHORIZED", "Invalid username or password.", 401
            )

        # Session fixation protection: clear old session before populating
        session.clear()
        session["user_id"] = user.user_id
        session["username"] = user.username
        session["role"] = user.role.value
        csrf_token = secrets.token_hex(32)
        session["csrf_token"] = csrf_token

        resp, status = self.render_json({
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role.value,
            "csrf_token": csrf_token,
        })
        _issue_csrf_token(resp)
        return resp, status


class LogoutHandler(BaseHandler):
    """POST /api/v1/auth/logout — Destroy session."""

    def post(self) -> tuple[Response, int]:
        session.clear()
        resp, status = self.render_json({"message": "Logged out successfully."})
        resp.delete_cookie("XSRF-TOKEN", path="/")
        return resp, status


class MeHandler(BaseHandler):
    """GET /api/v1/auth/me — Get current authenticated user info and refresh CSRF cookie."""

    def get(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Not authenticated.", 401)

        token = session.get("csrf_token")
        if not token:
            token = secrets.token_hex(32)
            session["csrf_token"] = token

        resp, status = self.render_json({
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role.value,
            "csrf_token": token,
        })
        _issue_csrf_token(resp)
        return resp, status
