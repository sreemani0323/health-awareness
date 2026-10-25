"""Controllers for role-request registration, email verification, and approval intake.

Enforces:
- Learners have a streamlined single-step email OTP registration.
- Non-learner applicants (Contributor, Reviewer, Staff) must:
  1. Specify the requested role and application details.
  2. Verify email via Email OTP.
  3. Pre-provision account password during email verification.
- Submissions create an application awaiting authoritative administrator review.
- Client role requests NEVER grant privileges directly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from flask import Response, request

from backend.controllers.base import BaseHandler
from backend.domain.staff_application_models import StaffRoleOption
from backend.domain.staff_application_service import (
    ApplicationConflictError,
    get_staff_application_service,
)
from backend.platform.otp_service import (
    create_otp_challenge,
    send_challenge_email,
    verify_otp_challenge,
)
from backend.platform.rate_limiter import get_trusted_client_ip, limiter
from backend.platform.security import hash_password
from backend.storage.db import get_db_session
from backend.storage.postgres_models import StaffApplicationModel, UserModel

logger = logging.getLogger(__name__)

ALLOWED_REQUEST_ROLES = frozenset({
    "contributor",
    "reviewer",
    "case_handler",
    "jurisdiction_officer",
})


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """Validate password meets security complexity rules."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() or not c.isalnum() for c in password):
        return False, "Password must contain at least one number or special character."
    return True, None


class RoleRequestInitiateHandler(BaseHandler):
    """POST /api/v1/auth/role-request/initiate — Step 1: Validate application & dispatch Email OTP."""

    decorators = [limiter.limit("15 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        name = str(data.get("name") or data.get("applicant_name") or "").strip()
        email = str(data.get("email") or data.get("applicant_email") or "").strip().lower()
        phone = str(data.get("phone") or data.get("applicant_phone") or "").strip() or None
        role = str(data.get("role") or data.get("requested_role") or "").strip().lower()
        sop = str(data.get("statement_of_purpose") or "").strip()
        ev_ack = bool(data.get("evidence_standards_acknowledged"))
        cs_ack = bool(data.get("child_safety_acknowledged"))

        if not name:
            return self.render_error("BAD_REQUEST", "Full name is required.", 400)
        if not email or "@" not in email:
            return self.render_error("BAD_REQUEST", "A valid email address is required.", 400)

        if role not in ALLOWED_REQUEST_ROLES:
            return self.render_error(
                "BAD_REQUEST",
                f"Requested role must be one of: {sorted(list(ALLOWED_REQUEST_ROLES))}",
                400,
            )

        if len(sop) < 30:
            return self.render_error(
                "BAD_REQUEST",
                "Statement of purpose must be at least 30 characters explaining your background.",
                400,
            )

        if not ev_ack:
            return self.render_error("BAD_REQUEST", "You must acknowledge evidence-based health standards.", 400)
        if not cs_ack:
            return self.render_error("BAD_REQUEST", "You must acknowledge learner safety guidelines.", 400)

        # Check for existing active application
        with get_db_session() as sess:
            existing_app = (
                sess.query(StaffApplicationModel)
                .filter(
                    StaffApplicationModel.applicant_email == email,
                    StaffApplicationModel.status.in_(["pending_review", "under_review"]),
                )
                .first()
            )
            if existing_app:
                return self.render_error(
                    "CONFLICT",
                    f"An active application already exists for {email} (Reference: {existing_app.reference_id}).",
                    409,
                )

            # Store payload in challenge
            pending_payload = {
                "name": name,
                "email": email,
                "phone": phone,
                "requested_role": role,
                "organization": str(data.get("organization") or "").strip() or None,
                "professional_title": str(data.get("professional_title") or "").strip() or None,
                "credential_reference": str(data.get("credential_reference") or "").strip() or None,
                "portfolio_url": str(data.get("portfolio_url") or "").strip() or None,
                "statement_of_purpose": sop,
                "evidence_standards_acknowledged": ev_ack,
                "child_safety_acknowledged": cs_ack,
            }

            try:
                challenge, otp = create_otp_challenge(
                    sess,
                    email=email,
                    purpose="role_request_email",
                    pending_payload=pending_payload,
                )
                sess.commit()
            except Exception as exc:
                sess.rollback()
                logger.error("Failed to create email OTP challenge: %s", exc)
                return self.render_error("SERVICE_UNAVAILABLE", "Failed to initiate verification.", 503)

        # Send email OTP
        send_challenge_email(email, otp, "signup")

        return self.render_json({
            "status": "email_challenge_sent",
            "email": email,
            "message": f"Verification code sent to {email}. Please enter the 6-digit code.",
        })


class RoleRequestVerifyEmailHandler(BaseHandler):
    """POST /api/v1/auth/role-request/verify-email — Step 2: Verify Email OTP."""

    decorators = [limiter.limit("20 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()
        otp = str(data.get("otp") or data.get("email_otp") or "").strip()

        if not email or not otp:
            return self.render_error("BAD_REQUEST", "email and otp are required.", 400)

        with get_db_session() as sess:
            is_valid, err_msg, challenge = verify_otp_challenge(
                sess,
                email=email,
                purpose="role_request_email",
                provided_otp=otp,
            )
            if not is_valid:
                sess.commit()
                return self.render_error("UNAUTHORIZED", err_msg or "Invalid verification code.", 401)

            sess.commit()

        return self.render_json({
            "email_verified": True,
            "message": "Email verified successfully.",
        })


class RoleRequestCompleteHandler(BaseHandler):
    """POST /api/v1/auth/role-request/complete — Step 3: Verify Email OTP (if provided), set password, & submit role request."""

    decorators = [limiter.limit("10 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email") or "").strip().lower()
        email_otp = str(data.get("email_otp") or data.get("otp") or data.get("sms_otp") or "").strip()
        password = str(data.get("password") or "").strip()
        phone = str(data.get("phone") or "").strip() or None

        if not email or not password:
            return self.render_error("BAD_REQUEST", "email and password are required.", 400)

        # Validate password strength
        is_strong, pwd_err = validate_password_strength(password)
        if not is_strong:
            return self.render_error("BAD_REQUEST", pwd_err or "Password does not meet requirements.", 400)

        with get_db_session() as sess:
            from backend.storage.postgres_models import EmailOtpChallengeModel
            # 1. If email_otp is provided, verify it directly
            if email_otp:
                is_valid_email, email_err, email_chal = verify_otp_challenge(
                    sess,
                    email=email,
                    purpose="role_request_email",
                    provided_otp=email_otp,
                )
                if not is_valid_email:
                    sess.commit()
                    return self.render_error("UNAUTHORIZED", email_err or "Invalid verification code.", 401)
            else:
                # Confirm prior verification
                email_chal = (
                    sess.query(EmailOtpChallengeModel)
                    .filter(
                        EmailOtpChallengeModel.email == email,
                        EmailOtpChallengeModel.purpose == "role_request_email",
                        EmailOtpChallengeModel.is_verified == True,  # noqa: E712
                    )
                    .order_by(EmailOtpChallengeModel.created_at.desc())
                    .first()
                )
                if not email_chal:
                    return self.render_error("FORBIDDEN", "Email verification required before completing registration.", 403)

            if not email_chal or not email_chal.pending_payload:
                return self.render_error("FORBIDDEN", "Application data not found. Please initiate again.", 403)

            payload = email_chal.pending_payload
            target_phone = phone or payload.get("phone")
            sess.commit()

        # 2. Create staff application record via StaffApplicationService
        service = get_staff_application_service()
        pwd_hash = hash_password(password)

        try:
            app, raw_token = service.submit_application(
                applicant_name=payload["name"],
                applicant_email=payload["email"],
                requested_role=payload["requested_role"],
                statement_of_purpose=payload["statement_of_purpose"],
                evidence_standards_acknowledged=payload["evidence_standards_acknowledged"],
                child_safety_acknowledged=payload["child_safety_acknowledged"],
                applicant_phone=target_phone,
                organization=payload.get("organization"),
                professional_title=payload.get("professional_title"),
                credential_reference=payload.get("credential_reference"),
                portfolio_url=payload.get("portfolio_url"),
                client_ip=get_trusted_client_ip(),
            )

            # Record verified contact status in verification_checklist
            with get_db_session() as sess:
                app_row = sess.query(StaffApplicationModel).filter_by(application_id=app.application_id).first()
                if app_row:
                    checklist = dict(app_row.verification_checklist or {})
                    checklist.update({
                        "email_verified": True,
                        "verified_email": email,
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                        "pre_provisioned_password_hash": pwd_hash,
                    })
                    app_row.verification_checklist = checklist
                    sess.commit()

        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except Exception as exc:
            logger.error("Failed to complete role request application: %s", exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to submit application.", 503)

        return self.render_json({
            "reference_id": app.reference_id,
            "tracking_token": raw_token,
            "status": getattr(app.status, "value", str(app.status)),
            "requested_role": getattr(app.requested_role, "value", str(app.requested_role)),
            "message": (
                "Your role application has been submitted successfully! "
                "Your email address is verified. "
                "Your application is now awaiting administrator review."
            ),
        })
