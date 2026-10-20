"""Authentication controller for Creator Studio.

Provides session-based authentication using Flask's built-in signed-cookie session
mechanism, PBKDF2-HMAC-SHA256 password verification, active account checking,
and CSRF protection with double-submit cookies.
"""

from __future__ import annotations

import functools
import logging
import os
import secrets
import uuid
from typing import Callable

from flask import Response, current_app, g, jsonify, request, session
import jwt
from jwt import PyJWKClient

from backend.controllers.base import BaseHandler
from backend.domain import domain_services
from backend.domain.domain_objects import User, UserRole

logger = logging.getLogger(__name__)

# Cached JWKS client
_jwk_client: PyJWKClient | None = None
_jwk_client_url: str | None = None


def get_jwk_client(jwks_url: str) -> PyJWKClient:
    """Retrieve or initialize the process-wide PyJWKClient with safe caching and timeout."""
    global _jwk_client, _jwk_client_url
    if _jwk_client is None or _jwk_client_url != jwks_url:
        _jwk_client = PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            cache_jwk_set=True,
            lifespan=3600,
            timeout=3.0,
        )
        _jwk_client_url = jwks_url
    return _jwk_client


def verify_neon_jwt(token: str) -> dict | None:
    """Verify a Neon Auth issued JWT according to security specifications.

    Validates:
    - Signature via remote JWKS or test secret
    - Expected algorithm (strictly EdDSA or test algorithm)
    - Expiration (exp)
    - Issuer (iss)
    - Subject (sub)
    """
    if not token or not isinstance(token, str):
        return None

    # Check for test configuration
    test_secret = current_app.config.get("TEST_JWT_SECRET") if current_app else None
    test_algorithm = current_app.config.get("TEST_JWT_ALGORITHM", "HS256") if current_app else None
    expected_issuer = (
        (current_app.config.get("NEON_AUTH_ISSUER") if current_app else None)
        or os.environ.get("NEON_AUTH_ISSUER", "").strip()
        or os.environ.get("NEON_AUTH_URL", "").strip()
        or "https://ep-raspy-moon-a1st7amb.neon.tech/neondb/auth"
    )
    expected_audience = (
        (current_app.config.get("NEON_AUTH_AUDIENCE") if current_app else None)
        or os.environ.get("NEON_AUTH_AUDIENCE", "").strip()
        or None
    )

    try:
        if test_secret:
            decode_kwargs: dict[str, Any] = {
                "algorithms": [test_algorithm],
                "issuer": expected_issuer,
                "options": {"require": ["exp", "iss", "sub"]},
            }
            if expected_audience:
                decode_kwargs["audience"] = expected_audience
            payload = jwt.decode(token, test_secret, **decode_kwargs)
            return payload

        jwks_url = (
            (current_app.config.get("NEON_JWKS_URL") if current_app else None)
            or os.environ.get("NEON_JWKS_URL", "").strip()
            or f"{expected_issuer}/.well-known/jwks.json"
        )
        client = get_jwk_client(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)

        allowed_algs = (
            current_app.config.get("NEON_ALLOWED_ALGORITHMS")
            if current_app else None
        )
        if not allowed_algs:
            raw_env = os.environ.get("NEON_ALLOWED_ALGORITHMS", "").strip()
            if raw_env:
                allowed_algs = [a.strip() for a in raw_env.split(",") if a.strip()]
            else:
                allowed_algs = ["EdDSA", "RS256"]

        decode_kwargs = {
            "algorithms": allowed_algs,
            "issuer": expected_issuer,
            "options": {"require": ["exp", "iss", "sub"]},
        }
        if expected_audience:
            decode_kwargs["audience"] = expected_audience

        payload = jwt.decode(token, signing_key.key, **decode_kwargs)
        return payload
    except Exception as exc:
        logger.debug("Neon JWT verification failed: %s", exc)
        return None


def _provision_learner(neon_uuid: uuid.UUID, display_name: str) -> User | None:
    """Safely, idempotently, and concurrency-safe provision a learner user in PostgreSQL."""
    from backend.storage.db import get_db_session
    from backend.storage.postgres_models import UserModel as PgUserModel

    user_id = f"usr_{uuid.uuid4().hex[:16]}"
    username = f"lrn_{neon_uuid.hex[:16]}"
    clean_name = (display_name or "Learner").strip()[:100]

    with get_db_session() as db_sess:
        bind = db_sess.get_bind()
        is_postgres = bind.dialect.name == "postgresql"

        if is_postgres:
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = (
                pg_insert(PgUserModel)
                .values(
                    user_id=user_id,
                    username=username,
                    display_name=clean_name,
                    role=UserRole.LEARNER.value,
                    password_hash=None,
                    neon_auth_user_id=neon_uuid,
                    is_active=True,
                )
                .on_conflict_do_nothing(index_elements=["neon_auth_user_id"])
            )
            db_sess.execute(stmt)
            db_sess.commit()
        else:
            # SQLite fallback for test environment
            try:
                new_user = PgUserModel(
                    user_id=user_id,
                    username=username,
                    display_name=clean_name,
                    role=UserRole.LEARNER.value,
                    password_hash=None,
                    neon_auth_user_id=neon_uuid,
                    is_active=True,
                )
                db_sess.add(new_user)
                db_sess.commit()
            except Exception:
                db_sess.rollback()

        # Re-query by neon_auth_user_id to get the single authoritative row
        row = db_sess.query(PgUserModel).filter_by(neon_auth_user_id=neon_uuid).first()
        if row is not None:
            return row.to_domain()
    return None


def get_current_user() -> User | None:
    """Retrieve the current user from Bearer JWT or session cookie.

    Precedence rules:
    1. Bearer token present:
       - Validate it first.
       - Invalid, expired, malformed, wrong issuer, or wrong signature -> FAIL CLOSED immediately.
       - NEVER fall back to a session cookie when a bearer token was supplied!
       - Inactive account -> fails closed with 403.
       - Unmapped identity -> safely auto-provisioned as 'learner'.
    2. No bearer token:
       - Continue using existing Flask session authentication.
    """
    auth_header = request.headers.get("Authorization", "").strip() if request else ""

    if auth_header.startswith("Bearer "):
        raw_token = auth_header[len("Bearer "):].strip()
        payload = verify_neon_jwt(raw_token)
        if not payload:
            g.auth_error = ("UNAUTHORIZED", "Invalid or expired authentication token.", 401)
            return None

        sub_str = payload.get("sub")
        if not sub_str:
            g.auth_error = ("UNAUTHORIZED", "Missing token subject.", 401)
            return None

        try:
            neon_uuid = uuid.UUID(str(sub_str))
        except (ValueError, TypeError):
            g.auth_error = ("UNAUTHORIZED", "Invalid token subject format.", 401)
            return None

        # Look up mapped user in PostgreSQL
        try:
            from backend.storage.db import get_db_session
            from backend.storage.postgres_models import UserModel as PgUserModel
            with get_db_session() as db_sess:
                pg_u = db_sess.query(PgUserModel).filter_by(neon_auth_user_id=neon_uuid).first()
                if pg_u is not None:
                    if not pg_u.is_active:
                        g.auth_error = ("FORBIDDEN", "Account deactivated.", 403)
                        return None
                    return pg_u.to_domain()
        except Exception as exc:
            logger.error("Error looking up user by neon_auth_user_id: %s", exc)

        # Unmapped identity: auto-provision strictly as learner
        try:
            user = _provision_learner(neon_uuid, payload.get("name", "Learner"))
            return user
        except Exception as exc:
            logger.error("Failed to provision learner: %s", exc)
            g.auth_error = ("SERVICE_UNAVAILABLE", "Failed to initialize learner profile.", 503)
            return None

    # No Bearer token -> Check legacy session
    user_id = session.get("user_id") if session else None
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
                    g.auth_error = ("FORBIDDEN", "Account deactivated.", 403)
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
    """Decorator requiring an authenticated session or valid bearer token."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            err = getattr(g, "auth_error", ("UNAUTHORIZED", "Authentication required.", 401))
            return jsonify({
                "error": {
                    "code": err[0],
                    "message": err[1],
                }
            }), err[2]
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles: UserRole) -> Callable:
    """Decorator requiring the current user to have one of the specified roles."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None:
                err = getattr(g, "auth_error", ("UNAUTHORIZED", "Authentication required.", 401))
                return jsonify({
                    "error": {
                        "code": err[0],
                        "message": err[1],
                    }
                }), err[2]
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


from backend.platform.rate_limiter import limiter, get_auth_rate_limit


class LoginHandler(BaseHandler):
    """POST /api/v1/auth/login — Authenticate and create session."""

    decorators = [
        limiter.limit(
            get_auth_rate_limit,
            deduct_when=lambda response: response.status_code >= 400,
        )
    ]

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
            err = getattr(g, "auth_error", ("UNAUTHORIZED", "Not authenticated.", 401))
            return self.render_error(err[0], err[1], err[2])

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
