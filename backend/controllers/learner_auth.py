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
from backend.platform.login_throttle import get_login_throttle_manager
from backend.platform.otp_service import (
    create_otp_challenge,
    send_challenge_email,
    verify_otp_challenge,
)
from backend.platform.rate_limiter import get_trusted_client_ip, limiter
from backend.platform.security import hash_password, verify_password
from backend.storage.db import get_db_session
from backend.storage.postgres_models import EmailOtpChallengeModel, UserModel

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
    """POST /api/v1/learner/auth/register — Start public learner registration with OTP challenge."""

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

        with get_db_session() as db_sess:
            existing = (
                db_sess.query(UserModel)
                .filter(UserModel.username == email)
                .first()
            )
            if existing:
                return self.render_error("CONFLICT", "An account with this email address already exists.", 409)

            # Store pending details in challenge payload until email verification code is verified
            challenge, otp = create_otp_challenge(
                db_sess=db_sess,
                email=email,
                purpose="signup",
                pending_payload={
                    "name": name,
                    "password_hash": pw_hash,
                },
            )
            db_sess.commit()

        # Send OTP email
        send_challenge_email(email, otp, "signup")
        logger.info("Learner signup OTP challenge generated for email=%s", email)

        res_payload: dict[str, Any] = {
            "message": "A 6-digit verification code has been sent to your email. Please verify to complete registration.",
            "email": email,
            "requires_otp": True,
            "expires_in_minutes": 10,
        }
        # In test and local development, surface dev_otp to enable automated E2E tests
        if current_app.config.get("TESTING") or os.environ.get("FLASK_ENV") == "development":
            res_payload["dev_otp"] = otp

        return self.render_json(res_payload, status_code=200)


class LearnerVerifySignupHandler(BaseHandler):
    """POST /api/v1/learner/auth/verify-signup — Verify 6-digit OTP and complete learner registration."""

    decorators = [limiter.limit("30 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        email = str(data.get("email", "")).strip().lower()
        otp = str(data.get("otp", "")).strip()

        if not email or not otp:
            return self.render_error("BAD_REQUEST", "Email and 6-digit verification code are required.", 400)

        with get_db_session() as db_sess:
            is_valid, err_msg, challenge = verify_otp_challenge(db_sess, email, "signup", otp)
            if not is_valid or not challenge:
                return self.render_error("BAD_REQUEST", err_msg or "Invalid verification code.", 400)

            payload = challenge.pending_payload or {}
            name = str(payload.get("name") or "Learner").strip()
            pw_hash = str(payload.get("password_hash") or "")

            if not pw_hash:
                return self.render_error("BAD_REQUEST", "Registration session has expired. Please sign up again.", 400)

            # Check again if user exists to prevent race condition
            existing = db_sess.query(UserModel).filter(UserModel.username == email).first()
            if existing:
                neon_uuid = existing.neon_auth_user_id or uuid.uuid4()
            else:
                neon_uuid = uuid.uuid4()
                user_id = f"usr_{uuid.uuid4().hex[:16]}"
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
        logger.info("Learner verified and created successfully: email=%s", email)

        return self.render_json(
            {
                "token": token,
                "user": {
                    "id": str(neon_uuid),
                    "name": name,
                    "email": email,
                },
                "message": "Learner account verified and created successfully.",
            },
            status_code=201,
        )


class LearnerResendOtpHandler(BaseHandler):
    """POST /api/v1/learner/auth/resend-otp — Resend a 6-digit OTP verification code."""

    decorators = [limiter.limit("5 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        purpose = str(data.get("purpose", "signup")).strip()

        if not email or not EMAIL_REGEX.match(email):
            return self.render_error("BAD_REQUEST", "Please enter a valid email address.", 400)
        if purpose not in ("signup", "reset_password"):
            purpose = "signup"

        otp_for_dev = None
        with get_db_session() as db_sess:
            # Check existing challenge to preserve pending payload if signup
            pending_payload = None
            if purpose == "signup":
                existing = (
                    db_sess.query(EmailOtpChallengeModel)
                    .filter(
                        EmailOtpChallengeModel.email == email,
                        EmailOtpChallengeModel.purpose == purpose,
                        EmailOtpChallengeModel.is_verified == False,  # noqa: E712
                    )
                    .order_by(EmailOtpChallengeModel.created_at.desc())
                    .first()
                )
                if existing:
                    pending_payload = existing.pending_payload

            challenge, otp = create_otp_challenge(db_sess, email, purpose, pending_payload)
            db_sess.commit()
            otp_for_dev = otp

        send_challenge_email(email, otp, purpose)

        res_payload: dict[str, Any] = {
            "message": "A new verification code has been sent to your email.",
            "email": email,
            "expires_in_minutes": 10,
        }
        if current_app.config.get("TESTING") or os.environ.get("FLASK_ENV") == "development":
            res_payload["dev_otp"] = otp_for_dev

        return self.render_json(res_payload)


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
        is_throttled, retry_after, _ = throttle_mgr.is_throttled(email, client_ip)
        if is_throttled:
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
    """POST /api/v1/learner/auth/recover — Request 6-digit OTP code for password reset."""

    decorators = [limiter.limit("5 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()

        if not email or not EMAIL_REGEX.match(email):
            return self.render_error("BAD_REQUEST", "Please enter a valid email address.", 400)

        otp_for_dev = None
        with get_db_session() as db_sess:
            user = db_sess.query(UserModel).filter(UserModel.username == email).first()
            if user and user.is_active:
                challenge, otp = create_otp_challenge(db_sess, email, "reset_password")
                db_sess.commit()
                send_challenge_email(email, otp, "reset_password")
                otp_for_dev = otp

        # Always return generic message to prevent account enumeration
        res_payload: dict[str, Any] = {
            "message": "If an account exists with that email address, a 6-digit verification code has been sent.",
            "requires_otp": True,
            "email": email,
        }
        if (current_app.config.get("TESTING") or os.environ.get("FLASK_ENV") == "development") and otp_for_dev:
            res_payload["dev_otp"] = otp_for_dev

        return self.render_json(res_payload)


class LearnerResetPasswordHandler(BaseHandler):
    """POST /api/v1/learner/auth/reset-password — Reset password using verified 6-digit OTP."""

    decorators = [limiter.limit("10 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        otp = str(data.get("otp", "")).strip()
        new_password = str(data.get("new_password", "") or data.get("password", ""))

        if not email or not otp or not new_password:
            return self.render_error("BAD_REQUEST", "Email, verification code, and new password are required.", 400)

        if len(new_password) < 8:
            return self.render_error("BAD_REQUEST", "New password must be at least 8 characters long.", 400)

        with get_db_session() as db_sess:
            is_valid, err_msg, challenge = verify_otp_challenge(db_sess, email, "reset_password", otp)
            if not is_valid or not challenge:
                return self.render_error("BAD_REQUEST", err_msg or "Invalid verification code.", 400)

            user = db_sess.query(UserModel).filter(UserModel.username == email).first()
            if not user or not user.is_active:
                return self.render_error("NOT_FOUND", "Account not found or inactive.", 404)

            user.password_hash = hash_password(new_password)
            db_sess.commit()

        logger.info("Password successfully reset for learner email=%s", email)
        return self.render_json({
            "message": "Your password has been reset successfully. You can now sign in with your new password.",
        })
