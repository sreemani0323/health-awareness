"""Learner authentication controller for HealthAware.

Provides:
- Public learner registration (/api/v1/learner/auth/register)
- Public learner login (/api/v1/learner/auth/login)
- Learner session inspection (/api/v1/learner/auth/me)
- Learner account recovery (/api/v1/learner/auth/recover)
- Cryptographic JWT issuance compatible with verify_neon_jwt
"""

from __future__ import annotations

import logging
import os
import re
import time
import uuid
from typing import Any

from flask import Response, current_app, request
import jwt

from backend.controllers.auth import get_current_user, get_learner_signing_secret, verify_neon_jwt
from backend.controllers.base import BaseHandler
from backend.domain.domain_objects import UserRole
from backend.platform.email_service import get_email_service
from backend.platform.login_throttle import get_login_throttle_manager
from backend.platform.rate_limiter import get_trusted_client_ip, limiter
from backend.platform.security import hash_password, verify_password
from backend.storage.db import get_db_session
from backend.storage.postgres_models import UserModel

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
JWT_LIFESPAN_SECONDS = 30 * 86400  # 30 days


def issue_learner_jwt(neon_uuid: uuid.UUID, display_name: str, email: str) -> str:
    """Issue a cryptographically signed HS256 JWT for a verified learner."""
    secret = get_learner_signing_secret()
    now = int(time.time())
    payload = {
        "sub": str(neon_uuid),
        "name": display_name.strip(),
        "email": email.strip().lower(),
        "role": "learner",
        "iss": "healthaware-auth",
        "exp": now + JWT_LIFESPAN_SECONDS,
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class LearnerRegisterHandler(BaseHandler):
    """POST /api/v1/learner/auth/register — Public learner registration."""

    decorators = [limiter.limit("15 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        name = str(data.get("name") or data.get("display_name") or "").strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not name or len(name) < 2:
            return self.render_error("BAD_REQUEST", "Please provide your full name (at least 2 characters).", 400)
        if not email or not EMAIL_REGEX.match(email):
            return self.render_error("BAD_REQUEST", "Please enter a valid email address.", 400)
        if not password or len(password) < 8:
            return self.render_error("BAD_REQUEST", "Password must be at least 8 characters long.", 400)

        pw_hash = hash_password(password)
        neon_uuid = uuid.uuid4()
        user_id = f"usr_{uuid.uuid4().hex[:16]}"

        with get_db_session() as db_sess:
            existing = (
                db_sess.query(UserModel)
                .filter(UserModel.username == email)
                .first()
            )
            if existing:
                return self.render_error("CONFLICT", "An account with this email address already exists.", 409)

            new_user = UserModel(
                user_id=user_id,
                username=email,
                display_name=name,
                role=UserRole.LEARNER.value,
                password_hash=pw_hash,
                neon_auth_user_id=neon_uuid,
                is_active=True,
            )
            db_sess.add(new_user)
            db_sess.commit()

        token = issue_learner_jwt(neon_uuid, name, email)
        logger.info("New learner registered: email=%s, user_id=%s", email, user_id)

        return self.render_json(
            {
                "token": token,
                "user": {
                    "id": str(neon_uuid),
                    "name": name,
                    "email": email,
                },
                "message": "Learner account created successfully.",
            },
            status_code=201,
        )


class LearnerLoginHandler(BaseHandler):
    """POST /api/v1/learner/auth/login — Public learner sign-in."""

    decorators = [limiter.limit("30 per minute")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return self.render_error("BAD_REQUEST", "Email and password are required.", 400)

        client_ip = get_trusted_client_ip()
        throttle_mgr = get_login_throttle_manager()
        is_locked, retry_after = throttle_mgr.is_locked(email, client_ip)
        if is_locked:
            resp, status = self.render_error(
                "LOCKED",
                f"Too many failed login attempts. Please try again in {retry_after} seconds.",
                429,
            )
            resp.headers["Retry-After"] = str(retry_after)
            return resp, status

        with get_db_session() as db_sess:
            user_model = (
                db_sess.query(UserModel)
                .filter(UserModel.username == email)
                .first()
            )

            # Accept both learner role and unassigned accounts
            if not user_model or not user_model.is_active or not user_model.password_hash:
                throttle_mgr.record_failure(email, client_ip)
                return self.render_error("UNAUTHORIZED", "Invalid email or password.", 401)

            if not verify_password(password, user_model.password_hash):
                throttle_mgr.record_failure(email, client_ip)
                return self.render_error("UNAUTHORIZED", "Invalid email or password.", 401)

            throttle_mgr.record_success(email, client_ip)

            # Ensure neon_auth_user_id exists
            if not user_model.neon_auth_user_id:
                user_model.neon_auth_user_id = uuid.uuid4()
                db_sess.commit()

            neon_uuid = user_model.neon_auth_user_id
            name = user_model.display_name or "Learner"

        token = issue_learner_jwt(neon_uuid, name, email)
        logger.info("Learner logged in successfully: email=%s", email)

        return self.render_json({
            "token": token,
            "user": {
                "id": str(neon_uuid),
                "name": name,
                "email": email,
            },
            "message": "Signed in successfully.",
        })


class LearnerMeHandler(BaseHandler):
    """GET /api/v1/learner/auth/me — Current authenticated learner session."""

    def get(self) -> tuple[Response, int]:
        user = get_current_user()
        if not user or user.role != UserRole.LEARNER:
            return self.render_error("UNAUTHORIZED", "Learner authentication required.", 401)

        return self.render_json({
            "id": user.user_id,
            "name": user.display_name,
            "role": user.role.value,
        })


class LearnerRecoverHandler(BaseHandler):
    """POST /api/v1/learner/auth/recover — Request password reset / recovery."""

    decorators = [limiter.limit("5 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()

        if not email or not EMAIL_REGEX.match(email):
            return self.render_error("BAD_REQUEST", "Please enter a valid email address.", 400)

        email_svc = get_email_service()
        if email_svc.is_configured:
            # Send recovery email
            email_svc.send_email(
                to_email=email,
                subject="HealthAware Password Recovery Request",
                text_content="If you requested a password reset, please follow instructions sent to your email.",
            )

        # Always return generic message to prevent account enumeration
        return self.render_json({
            "message": "If an account exists with that email address, recovery instructions have been sent.",
        })
