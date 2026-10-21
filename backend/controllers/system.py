"""System diagnostic and operational verification endpoints.

Allows safe inspection of transactional email provider readiness and
controlled end-to-end verification without leaking credentials or secrets.
"""

from __future__ import annotations

import logging
import os
import socket
from typing import Any

from flask import Response, request

from backend.controllers.base import BaseHandler
from backend.platform.email_service import get_email_service

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
    """GET /api/v1/system/email-status — Safe operational inspection of SMTP configuration.

    Never discloses passwords, auth tokens, or sensitive API keys.
    Reports presence of required environment variables and tests outbound socket connectivity.
    """

    def get(self) -> tuple[Response, int]:
        svc = get_email_service()

        has_host = bool(svc._smtp_host)
        has_port = bool(os.environ.get("SMTP_PORT", "").strip())
        has_username = bool(svc._smtp_user)
        has_password = bool(svc._smtp_password)
        has_from = bool(
            os.environ.get("SMTP_FROM_EMAIL", "").strip()
            or os.environ.get("SMTP_FROM", "").strip()
            or os.environ.get("EMAIL_FROM", "").strip()
        )

        host_repr = svc._smtp_host
        if host_repr and not any(
            h in host_repr.lower() for h in ("gmail.com", "sendgrid.net", "resend.com", "mailgun.org", "postmarkapp.com")
        ):
            host_repr = "[CONFIGURED_CUSTOM_HOST]"

        ports_to_test = [587, 465]
        if svc._smtp_port not in ports_to_test:
            ports_to_test.append(svc._smtp_port)

        connectivity: dict[str, Any] = {}
        if has_host:
            for p in ports_to_test:
                port_result = {"reachable": False, "error": None}
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2.5)
                    sock.connect((svc._smtp_host, p))
                    sock.close()
                    port_result["reachable"] = True
                except socket.timeout:
                    port_result["error"] = "TIMEOUT_FIREWALL_BLOCKED (outbound port dropped by Render Free tier firewall)"
                except ConnectionRefusedError:
                    port_result["error"] = "CONNECTION_REFUSED"
                except Exception as exc:
                    port_result["error"] = f"SOCKET_ERROR: {str(exc)}"
                connectivity[f"port_{p}"] = port_result

        return self.render_json({
            "is_configured": svc.is_configured,
            "smtp_host_configured": has_host,
            "smtp_host": host_repr or None,
            "smtp_port": svc._smtp_port,
            "smtp_username_configured": has_username,
            "smtp_password_configured": has_password,
            "smtp_from_email_configured": has_from,
            "from_address_masked": _mask_email(svc._from_email),
            "connectivity": connectivity,
        })


class SystemEmailTestHandler(BaseHandler):
    """POST /api/v1/system/email-test — Standalone test email dispatch.

    Dispatches a single diagnostic message through the actual EmailService
    instance to verify end-to-end SMTP delivery to a verified recipient.
    """

    def post(self) -> tuple[Response, int]:
        svc = get_email_service()
        data = request.get_json(silent=True) or {}

        recipient = (
            data.get("recipient")
            or data.get("to_email")
            or svc._from_email
            or ""
        ).strip().lower()

        if not recipient or "@" not in recipient:
            return self.render_error("BAD_REQUEST", "Valid recipient email address is required.", 400)

        subject = data.get("subject") or "HealthAware Production SMTP Test"
        content = (
            "HealthAware Production Transactional Email Verification\n\n"
            "This standalone test email was dispatched through the deployed application's\n"
            "actual EmailService instance to verify SMTP relay connectivity and inbox delivery.\n\n"
            f"Configured Host: {svc._smtp_host or 'none'}\n"
            f"Configured Port: {svc._smtp_port}\n"
            f"Recipient: {recipient}\n\n"
            "— HealthAware Production Infrastructure"
        )

        res = svc.send_email(
            to_email=recipient,
            subject=subject,
            text_content=content,
        )

        return self.render_json({
            "success": res.success,
            "provider": res.provider,
            "message_id": res.message_id,
            "error": res.error,
            "recipient_masked": _mask_email(recipient),
        }, status_code=200)
