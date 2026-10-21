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


def get_learner_signing_secret() -> str:
    """Retrieve or derive process-wide learner JWT signing secret."""
    return (
        (current_app.config.get("TEST_JWT_SECRET") if current_app else None)
        or os.environ.get("LEARNER_JWT_SECRET", "").strip()
        or os.environ.get("FLASK_SECRET_KEY", "").strip()
        or "healthaware-production-learner-signing-key-32chars-min!"
    )


def verify_neon_jwt(token: str) -> dict | None:
    """Verify a Neon Auth or HealthAware issued learner JWT according to security specifications.

    Validates:
    - Signature via local signing secret or remote JWKS
    - Expected algorithm (HS256, EdDSA, RS256)
    - Expiration (exp)
    - Issuer (iss)
    - Subject (sub)
    """
    if not token or not isinstance(token, str):
        return None

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

    # 1. Check local signing secret (HS256) for direct learner registration/auth
    local_secret = get_learner_signing_secret()
    if local_secret:
        try:
            decode_kwargs: dict[str, Any] = {
                "algorithms": ["HS256"],
                "options": {"require": ["exp", "iss", "sub"]},
            }
            if expected_audience:
                decode_kwargs["audience"] = expected_audience
            payload = jwt.decode(token, local_secret, **decode_kwargs)
            iss = payload.get("iss")
            if iss in (expected_issuer, "healthaware-auth", "https://health-awareness.pages.dev"):
                return payload
        except Exception:
            pass

    # 2. Check remote JWKS (Neon Auth EdDSA/RS256)
    try:
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

    # Server-side session revocation check
    session_auth_time = session.get("auth_time", 0)
    try:
        from backend.platform.mfa_service import get_mfa_service, MfaStorageError
        mfa_service = get_mfa_service()
        revoked_at = mfa_service.get_session_revoked_at(user_id)
        if revoked_at is not None:
            revoked_ts = revoked_at.timestamp()
            if session_auth_time < revoked_ts:
                session.clear()
                g.auth_error = (
                    "UNAUTHORIZED",
                    "Session has been revoked due to a security credential change. Please log in again.",
                    401,
                )
                return None
    except MfaStorageError as exc:
        logger.error("Session revocation check failed for user '%s': %s", user_id, exc)
        g.auth_error = (
            "SERVICE_UNAVAILABLE",
            "Authentication service temporarily unavailable.",
            503,
        )
        return None
    except Exception as exc:
        logger.debug("Unexpected error during session revocation check: %s", exc)

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


STAFF_ADMIN_ROLES = frozenset({
    UserRole.CONTRIBUTOR,
    UserRole.REVIEWER,
    UserRole.ADMIN,
    UserRole.CASE_HANDLER,
    UserRole.JURISDICTION_OFFICER,
})


def role_required(*roles: UserRole) -> Callable:
    """Decorator requiring the current user to have one of the specified roles.

    Enforces strict session isolation:
    Staff administrative APIs (Contributor, Reviewer, Admin, Case Handler, Jurisdiction Officer)
    strictly require an authentic, signed Flask session cookie. Public learner Bearer JWTs
    are rejected immediately on staff administrative routes.
    """
    target_staff = any(r in STAFF_ADMIN_ROLES for r in roles)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if target_staff:
                auth_header = request.headers.get("Authorization", "").strip() if request else ""
                if auth_header.startswith("Bearer "):
                    raw_token = auth_header[len("Bearer "):].strip()
                    payload = verify_neon_jwt(raw_token)
                    if not payload:
                        return jsonify({
                            "error": {
                                "code": "UNAUTHORIZED",
                                "message": "Invalid or expired authentication token.",
                            }
                        }), 401
                    return jsonify({
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "Staff administrative APIs require a valid staff session cookie. Bearer tokens are not permitted.",
                        }
                    }), 403
                if not session or not session.get("user_id"):
                    return jsonify({
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Staff session required.",
                        }
                    }), 401

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
            g.current_user = user
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


import time
from backend.platform.audit_log import SecurityAuditEvent, log_security_event
from backend.platform.login_throttle import get_login_throttle_manager
from backend.platform.mfa_service import get_mfa_service
from backend.platform.rate_limiter import get_auth_rate_limit, get_trusted_client_ip, limiter


class LoginHandler(BaseHandler):
    """POST /api/v1/auth/login — Authenticate and create session."""

    decorators = [
        limiter.limit(
            get_auth_rate_limit,
            deduct_when=lambda response: response.status_code >= 400,
        )
    ]

    def post(self) -> tuple[Response, int]:
        client_ip = get_trusted_client_ip()
        throttle_mgr = get_login_throttle_manager()

        data = request.get_json(silent=True)
        if not data:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return self.render_error(
                "BAD_REQUEST", "username and password are required.", 400
            )

        # 1. Progressive throttling & brute-force mitigation
        is_throttled, retry_after, reason = throttle_mgr.is_throttled(username, client_ip)
        if is_throttled:
            log_security_event(
                event=SecurityAuditEvent.LOGIN_THROTTLED,
                actor_id=username,
                client_ip=client_ip,
                status="THROTTLED",
                details={"retry_after": retry_after, "reason": reason},
            )
            resp, status = self.render_error(
                "UNAUTHORIZED", "Invalid username or password.", 401
            )
            resp.headers["Retry-After"] = str(retry_after)
            return resp, status

        # 2. Authenticate against PostgreSQL first
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

        # 3. Failed authentication handling (generic error prevents account enumeration)
        if user is None or not user.is_active:
            throttle_mgr.record_failure(username, client_ip)
            log_security_event(
                event=SecurityAuditEvent.LOGIN_FAILED,
                actor_id=username,
                client_ip=client_ip,
                status="FAILURE",
            )
            return self.render_error(
                "UNAUTHORIZED", "Invalid username or password.", 401
            )

        # 4. Successful credentials verification
        throttle_mgr.record_success(username, client_ip)

        # 5. Check if staff user has active Multi-Factor Authentication (MFA)
        mfa_service = get_mfa_service()
        try:
            mfa_enabled = mfa_service.is_mfa_enabled(user.user_id)
        except Exception as exc:
            logger.error("Database error checking MFA status for user '%s': %s", user.user_id, exc)
            return self.render_error(
                "SERVICE_UNAVAILABLE",
                "Authentication service temporarily unavailable.",
                503,
            )

        if mfa_enabled:
            session.clear()
            session["mfa_pending_user_id"] = user.user_id
            session["mfa_pending_username"] = user.username
            session["mfa_pending_role"] = user.role.value
            session["mfa_pending_display_name"] = user.display_name
            session["mfa_pending_timestamp"] = time.time()

            log_security_event(
                event=SecurityAuditEvent.MFA_REQUIRED,
                actor_id=user.user_id,
                client_ip=client_ip,
                status="SUCCESS",
            )

            return self.render_json({
                "mfa_required": True,
                "user_id": user.user_id,
                "message": "Multi-factor authentication required.",
            })

        # 6. Standard session creation for users without MFA enabled
        session.clear()
        session.permanent = True
        session["user_id"] = user.user_id
        session["username"] = user.username
        session["role"] = user.role.value
        session["auth_time"] = time.time()
        csrf_token = secrets.token_hex(32)
        session["csrf_token"] = csrf_token

        log_security_event(
            event=SecurityAuditEvent.LOGIN_SUCCESS,
            actor_id=user.user_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"mfa_used": False},
        )

        resp, status = self.render_json({
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role.value,
            "csrf_token": csrf_token,
        })
        _issue_csrf_token(resp)
        return resp, status


class MfaVerifyHandler(BaseHandler):
    """POST /api/v1/auth/mfa/verify — Complete login via TOTP code or emergency recovery code."""

    def post(self) -> tuple[Response, int]:
        client_ip = get_trusted_client_ip()
        mfa_user_id = session.get("mfa_pending_user_id")
        mfa_timestamp = session.get("mfa_pending_timestamp", 0)
        username = session.get("mfa_pending_username", "")

        # Pending MFA state must exist and be within 5-minute timeout window
        if not mfa_user_id or (time.time() - mfa_timestamp) > 300:
            session.clear()
            return self.render_error(
                "UNAUTHORIZED",
                "MFA session has expired or is invalid. Please log in again.",
                401,
            )

        # 1. Enforce login throttling on MFA verification attempts
        from backend.platform.login_throttle import get_login_throttle_manager
        throttle_mgr = get_login_throttle_manager()
        is_locked, retry_after, _ = throttle_mgr.is_throttled(username, client_ip)
        if is_locked:
            resp, status = self.render_error(
                "UNAUTHORIZED",
                "Account is temporarily locked due to repeated failed verification attempts.",
                401,
            )
            resp.headers["Retry-After"] = str(retry_after)
            return resp, status

        data = request.get_json(silent=True) or {}
        code = (
            data.get("totp_code")
            or data.get("code")
            or data.get("recovery_code", "")
        )
        if not code or not isinstance(code, str):
            return self.render_error("BAD_REQUEST", "MFA code or recovery code is required.", 400)

        mfa_service = get_mfa_service()
        try:
            success, method_or_err = mfa_service.verify_login_mfa(
                user_id=mfa_user_id,
                code_or_recovery=code,
                client_ip=client_ip,
            )
        except Exception as exc:
            logger.error("MFA verification database error for user '%s': %s", mfa_user_id, exc)
            return self.render_error(
                "SERVICE_UNAVAILABLE",
                "Authentication service temporarily unavailable.",
                503,
            )

        if not success:
            throttle_mgr.record_failure(username, client_ip)
            failed_attempts = session.get("mfa_failed_attempts", 0) + 1
            session["mfa_failed_attempts"] = failed_attempts

            if failed_attempts >= 3:
                session.clear()
                return self.render_error(
                    "UNAUTHORIZED",
                    "Too many failed verification attempts. Please log in again.",
                    401,
                )

            if method_or_err == "replay_detected":
                return self.render_error(
                    "UNAUTHORIZED",
                    "This authentication code has already been used. Please wait for the next code.",
                    401,
                )
            return self.render_error(
                "UNAUTHORIZED",
                "Invalid authentication code or recovery code.",
                401,
            )

        # Clear throttle on successful verification
        throttle_mgr.record_success(username, client_ip)

        # Complete staff session establishment
        role = session.get("mfa_pending_role")
        display_name = session.get("mfa_pending_display_name", username)

        session.clear()
        session.permanent = True
        session["user_id"] = mfa_user_id
        session["username"] = username
        session["role"] = role
        session["auth_time"] = time.time()
        csrf_token = secrets.token_hex(32)
        session["csrf_token"] = csrf_token

        log_security_event(
            event=SecurityAuditEvent.LOGIN_SUCCESS,
            actor_id=mfa_user_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"mfa_used": True, "method": method_or_err},
        )

        resp, status = self.render_json({
            "user_id": mfa_user_id,
            "username": username,
            "display_name": display_name,
            "role": role,
            "csrf_token": csrf_token,
            "mfa_verified": True,
            "mfa_method": method_or_err,
        })
        _issue_csrf_token(resp)
        return resp, status


class MfaEnrollHandler(BaseHandler):
    """POST /api/v1/auth/mfa/enroll — Initiate MFA setup for authenticated staff."""

    @role_required(*STAFF_ADMIN_ROLES)
    def post(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Staff authentication required.", 401)

        data = request.get_json(silent=True) or {}
        password = data.get("password", "").strip() if isinstance(data, dict) else ""
        auth_time = session.get("auth_time", 0)
        now = time.time()

        # Enforce recent password verification (within 15 minutes) or explicit password re-entry
        if password:
            from backend.platform.security import verify_password
            if not verify_password(password, user.password_hash):
                return self.render_error("UNAUTHORIZED", "Password verification failed.", 401)
            session["auth_time"] = now
        elif not auth_time or (now - auth_time) > 900:
            return self.render_error(
                "UNAUTHORIZED",
                "Recent password verification required to initiate MFA enrollment.",
                401,
            )

        mfa_service = get_mfa_service()
        try:
            enrollment_data = mfa_service.initiate_enrollment(
                user_id=user.user_id,
                username=user.username,
            )
        except Exception as exc:
            logger.error("Failed to initiate MFA enrollment for %s: %s", user.user_id, exc)
            return self.render_error(
                "SERVICE_UNAVAILABLE",
                "Authentication service temporarily unavailable.",
                503,
            )

        return self.render_json({
            "secret": enrollment_data["secret"],
            "provisioning_uri": enrollment_data["provisioning_uri"],
            "recovery_codes": enrollment_data["recovery_codes"],
            "message": "Scan the QR code or enter the secret in your authenticator app, then confirm with a 6-digit code.",
        })


class MfaConfirmEnrollmentHandler(BaseHandler):
    """POST /api/v1/auth/mfa/confirm-enrollment — Confirm TOTP and activate MFA."""

    @role_required(*STAFF_ADMIN_ROLES)
    def post(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Staff authentication required.", 401)

        data = request.get_json(silent=True) or {}
        totp_code = data.get("totp_code", "").strip()
        if not totp_code:
            return self.render_error("BAD_REQUEST", "totp_code is required.", 400)

        mfa_service = get_mfa_service()
        try:
            success = mfa_service.confirm_enrollment(user.user_id, totp_code)
        except Exception as exc:
            logger.error("Failed to confirm MFA enrollment for %s: %s", user.user_id, exc)
            return self.render_error(
                "SERVICE_UNAVAILABLE",
                "Authentication service temporarily unavailable.",
                503,
            )

        if not success:
            return self.render_error(
                "BAD_REQUEST",
                "Verification code is invalid or expired. Check your device clock and try again.",
                400,
            )

        return self.render_json({
            "message": "Multi-factor authentication successfully activated.",
            "mfa_enabled": True,
        })


class MfaStatusHandler(BaseHandler):
    """GET /api/v1/auth/mfa/status — Check staff user's MFA enrollment status."""

    @role_required(*STAFF_ADMIN_ROLES)
    def get(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Staff authentication required.", 401)

        mfa_service = get_mfa_service()
        try:
            status_data = mfa_service.get_status(user.user_id)
        except Exception as exc:
            logger.error("Failed to get MFA status for %s: %s", user.user_id, exc)
            return self.render_error(
                "SERVICE_UNAVAILABLE",
                "Authentication service temporarily unavailable.",
                503,
            )
        return self.render_json(status_data)


class MfaDisableHandler(BaseHandler):
    """POST /api/v1/auth/mfa/disable — Self-service MFA disabling with password re-entry."""

    @role_required(*STAFF_ADMIN_ROLES)
    def post(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Staff authentication required.", 401)

        data = request.get_json(silent=True) or {}
        password = data.get("password", "").strip()
        code = data.get("totp_code") or data.get("recovery_code", "")

        if not password or not code:
            return self.render_error(
                "BAD_REQUEST", "password and totp_code (or recovery_code) are required to disable MFA.", 400
            )

        # Verify password first
        from backend.platform.security import verify_password
        if not verify_password(password, user.password_hash):
            return self.render_error("UNAUTHORIZED", "Password verification failed.", 401)

        # Verify MFA code
        mfa_service = get_mfa_service()
        success, _ = mfa_service.verify_login_mfa(user.user_id, code, get_trusted_client_ip())
        if not success:
            return self.render_error("UNAUTHORIZED", "MFA verification failed.", 401)

        try:
            mfa_service.disable_mfa(user.user_id)
        except Exception as exc:
            logger.error("Failed to disable MFA for user '%s': %s", user.user_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to disable MFA.", 503)

        # Refresh auth_time for this current browser session so it remains authenticated,
        # while other sessions on other browsers/devices are invalidated.
        session["auth_time"] = time.time()
        return self.render_json({"message": "MFA has been disabled.", "mfa_enabled": False})


class LogoutHandler(BaseHandler):
    """POST /api/v1/auth/logout — Destroy session."""

    def post(self) -> tuple[Response, int]:
        user_id = session.get("user_id")
        session.clear()
        if user_id:
            log_security_event(
                event=SecurityAuditEvent.SESSION_REVOKED,
                actor_id=user_id,
                client_ip=get_trusted_client_ip(),
                status="SUCCESS",
            )
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

        mfa_service = get_mfa_service()
        mfa_enabled = mfa_service.is_mfa_enabled(user.user_id)

        resp, status = self.render_json({
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role.value,
            "csrf_token": token,
            "mfa_enabled": mfa_enabled,
        })
        _issue_csrf_token(resp)
        return resp, status

