"""System diagnostic and operational verification endpoints.

Provides administrative health inspection and controlled operational verification
of transactional email delivery. All endpoints strictly require an active,
authenticated administrator session (UserRole.ADMIN) and CSRF protection.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from flask import Response, request

from backend.controllers.auth import get_current_user, role_required
from backend.controllers.base import BaseHandler
from backend.domain.domain_objects import UserRole
from backend.platform.email_service import get_email_service
from backend.platform.rate_limiter import limiter

logger = logging.getLogger(__name__)


def _mask_email(email: str) -> str:
    """Mask email address safely (e.g. user@gmail.com -> us***@gmail.com)."""
    if not email or "@" not in email:
        return "not_configured"
    user_part, domain_part = email.split("@", 1)
    if len(user_part) <= 2:
        return f"*@{domain_part}"
    return f"{user_part[:2]}***@{domain_part}"


class SystemEmailStatusHandler(BaseHandler):
    """GET /api/v1/system/email-status — Secure administrative inspection of email service.

    Requires UserRole.ADMIN. Anonymous users receive 401; ordinary learners receive 403.
    Never discloses client secrets, refresh tokens, passwords, or raw configuration values.
    """

    decorators = [limiter.limit("30 per minute")]

    @role_required(UserRole.ADMIN)
    def get(self) -> tuple[Response, int]:
        svc = get_email_service()

        active_provider = (
            "gmail_api"
            if svc.is_gmail_api_configured
            else ("smtp" if svc.is_smtp_configured else "unconfigured")
        )

        delivery_channel = (
            "https_api"
            if active_provider == "gmail_api"
            else ("smtp" if active_provider == "smtp" else "none")
        )

        return self.render_json({
            "is_configured": svc.is_configured,
            "active_provider": active_provider,
            "delivery_channel": delivery_channel,
            "gmail_api_configured": svc.is_gmail_api_configured,
            "smtp_configured": svc.is_smtp_configured,
            "sender_address_masked": _mask_email(svc._from_email),
        })


class SystemEmailTestHandler(BaseHandler):
    """POST /api/v1/system/email-test — Secure administrator transactional test dispatch.

    Requires UserRole.ADMIN, CSRF protection, and rate limiting (5 per hour).
    Restricts test recipients strictly to authorized operator/administrator addresses.
    Never discloses raw SMTP errors or OAuth access/refresh tokens.
    """

    decorators = [limiter.limit("5 per hour")]

    @role_required(UserRole.ADMIN)
    def post(self) -> tuple[Response, int]:
        svc = get_email_service()
        data = request.get_json(silent=True) or {}

        from flask import g
        current_user = getattr(g, "current_user", None) or get_current_user()
        admin_email = current_user.username if (current_user and "@" in getattr(current_user, "username", "")) else ""
        configured_sender = svc._from_email if (svc._from_email and "@" in svc._from_email) else ""
        explicit_admin_test_email = os.environ.get("ADMIN_TEST_EMAIL", "").strip().lower()

        authorized_recipients = {
            r.lower()
            for r in [admin_email, configured_sender, explicit_admin_test_email]
            if r and "@" in r
        }

        requested_recipient = (
            data.get("recipient")
            or data.get("to_email")
            or configured_sender
            or admin_email
            or ""
        ).strip().lower()

        if not requested_recipient or "@" not in requested_recipient:
            return self.render_error("BAD_REQUEST", "Valid recipient email address is required.", 400)

        # Enforce authorized recipient restriction
        if authorized_recipients and requested_recipient not in authorized_recipients:
            return self.render_error(
                "FORBIDDEN",
                "Test email dispatch is restricted to authorized administrator addresses.",
                403,
            )

        subject = "HealthAware Production Transactional Email Verification"
        channel_desc = "Gmail REST API (HTTPS port 443)" if svc.is_gmail_api_configured else "SMTP Relay"
        content = (
            "HealthAware Production Transactional Email Verification\n\n"
            "This diagnostic verification email was dispatched through the deployed application's\n"
            "active EmailService instance by an authorized administrator.\n\n"
            f"Delivery Channel: {channel_desc}\n"
            f"Recipient: {requested_recipient}\n\n"
            "— HealthAware Production Infrastructure"
        )

        res = svc.send_email(
            to_email=requested_recipient,
            subject=subject,
            text_content=content,
        )

        if res.success:
            message = f"Transactional test email successfully dispatched via {res.provider}."
        else:
            message = "Transactional test email failed to dispatch. Provider reported delivery error."

        return self.render_json({
            "success": res.success,
            "provider": res.provider,
            "message": message,
            "recipient_masked": _mask_email(requested_recipient),
        }, status_code=200)
