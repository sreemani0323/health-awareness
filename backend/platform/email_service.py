"""Transactional email delivery service with safe provider abstractions.

Supports:
- SMTP with STARTTLS (configurable via SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL)
- Safe fallback / audit mode when no external transactional email provider is configured.
- Rejection of email dispatch to unverified or blank addresses.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailDeliveryResult:
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailService:
    """Manages transactional email dispatch for HealthAware."""

    def __init__(self):
        self._smtp_host = os.environ.get("SMTP_HOST", "").strip()
        self._smtp_port = int(os.environ.get("SMTP_PORT", "587")) if os.environ.get("SMTP_PORT") else 587
        self._smtp_user = os.environ.get("SMTP_USER", "").strip()
        self._smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
        self._from_email = (
            os.environ.get("SMTP_FROM_EMAIL", "").strip()
            or os.environ.get("EMAIL_FROM", "").strip()
            or "noreply@healthaware.org"
        )

    @property
    def is_configured(self) -> bool:
        """Returns True if a real outbound email delivery provider is configured."""
        return bool(self._smtp_host and (self._smtp_user or self._smtp_port == 25))

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Dispatches an email or records delivery intent safely if unconfigured."""
        clean_to = to_email.strip().lower() if to_email else ""
        if not clean_to or "@" not in clean_to:
            return EmailDeliveryResult(
                success=False,
                provider="none",
                error="Invalid recipient email address.",
            )

        if not self.is_configured:
            logger.info(
                "Transactional email dispatch skipped (no provider configured). Recipient: %s, Subject: '%s'",
                clean_to,
                subject,
            )
            return EmailDeliveryResult(
                success=False,
                provider="unconfigured",
                error="EMAIL_PROVIDER_NOT_CONFIGURED",
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._from_email
            msg["To"] = clean_to

            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            if html_content:
                msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=10.0) as server:
                server.ehlo()
                if server.has_extn("STARTTLS"):
                    server.starttls()
                    server.ehlo()
                if self._smtp_user and self._smtp_password:
                    server.login(self._smtp_user, self._smtp_password)
                server.send_message(msg)

            logger.info("Successfully delivered email to %s via SMTP (%s)", clean_to, self._smtp_host)
            return EmailDeliveryResult(success=True, provider="smtp", message_id="smtp-ok")
        except Exception as exc:
            logger.error("Failed to deliver email to %s: %s", clean_to, exc)
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error=f"Delivery failed: {str(exc)}",
            )

    def send_staff_application_tracking(
        self,
        to_email: str,
        applicant_name: str,
        reference_id: str,
        tracking_token: str,
        tracking_url: str,
    ) -> EmailDeliveryResult:
        """Sends staff application tracking token and instructions to applicant."""
        subject = f"HealthAware Staff Application Received — Reference {reference_id}"
        text = (
            f"Dear {applicant_name},\n\n"
            f"Thank you for applying for a staff or reviewer role with HealthAware.\n\n"
            f"Your application has been received and queued for administrative vetting.\n"
            f"Reference ID: {reference_id}\n"
            f"Tracking Token: {tracking_token}\n\n"
            f"Track your application status online at:\n{tracking_url}\n\n"
            f"Please keep this token secure. It will not be sent again.\n\n"
            f"— The HealthAware Team\n"
        )
        return self.send_email(to_email, subject, text)

    def send_concern_tracking(
        self,
        to_email: str,
        reference_id: str,
        tracking_token: str,
        tracking_url: str,
    ) -> EmailDeliveryResult:
        """Sends citizen concern tracking credentials to a registered user."""
        subject = f"HealthAware Community Concern Report — Reference {reference_id}"
        text = (
            f"Hello,\n\n"
            f"Your community sanitation report has been registered with HealthAware.\n\n"
            f"Reference ID: {reference_id}\n"
            f"Tracking Token: {tracking_token}\n\n"
            f"You can monitor coordinator triage and municipal updates at:\n{tracking_url}\n\n"
            f"— HealthAware Community Care Team\n"
        )
        return self.send_email(to_email, subject, text)


# Process-wide singleton
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def set_email_service(service: Optional[EmailService]) -> None:
    """Allows tests to inject mock email service."""
    global _email_service
    _email_service = service
