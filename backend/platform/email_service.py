"""Transactional email delivery service with safe provider abstractions.

Configuration:
- Canonical Environment Variables:
  * SMTP_HOST: Hostname of SMTP relay (e.g. smtp.sendgrid.net, smtp.resend.com)
  * SMTP_PORT: Port number (e.g. 587 for STARTTLS, 465 for SSL, 25 for unauthenticated relay). Default: 587
  * SMTP_USERNAME: Username or API key user (e.g. apikey, resend)
  * SMTP_PASSWORD: Password or secret API token
  * SMTP_FROM_EMAIL: Outbound sender email address (e.g. no-reply@healthaware.org)

- Backward-Compatible Alias Fallbacks (in order of precedence):
  * Host: SMTP_HOST -> SMTP_SERVER
  * Username: SMTP_USERNAME -> SMTP_USER
  * Password: SMTP_PASSWORD -> SMTP_PASS
  * Sender: SMTP_FROM_EMAIL -> SMTP_FROM -> EMAIL_FROM -> "noreply@healthaware.org"

Safety & Privacy Guarantees:
- When unconfigured or missing credentials, dispatch is truthfully skipped without throwing exceptions.
- Failed deliveries are never reported as successful.
- No password, token, or secret is ever exposed in logs or exception messages.
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

    # Canonical environment variable names
    ENV_SMTP_HOST = "SMTP_HOST"
    ENV_SMTP_PORT = "SMTP_PORT"
    ENV_SMTP_USERNAME = "SMTP_USERNAME"
    ENV_SMTP_PASSWORD = "SMTP_PASSWORD"
    ENV_SMTP_FROM_EMAIL = "SMTP_FROM_EMAIL"

    # Backward-compatible alias environment variable names
    ALIAS_SMTP_SERVER = "SMTP_SERVER"
    ALIAS_SMTP_USER = "SMTP_USER"
    ALIAS_SMTP_PASS = "SMTP_PASS"
    ALIAS_SMTP_FROM = "SMTP_FROM"
    ALIAS_EMAIL_FROM = "EMAIL_FROM"

    DEFAULT_FROM_EMAIL = "noreply@healthaware.org"

    def __init__(self):
        # Host: SMTP_HOST (canonical) -> SMTP_SERVER (alias)
        self._smtp_host = (
            os.environ.get(self.ENV_SMTP_HOST, "").strip()
            or os.environ.get(self.ALIAS_SMTP_SERVER, "").strip()
        )

        # Port: SMTP_PORT (default 587)
        port_raw = os.environ.get(self.ENV_SMTP_PORT, "").strip()
        try:
            self._smtp_port = int(port_raw) if port_raw else 587
        except ValueError:
            logger.warning("Invalid SMTP_PORT '%s', defaulting to 587", port_raw)
            self._smtp_port = 587

        # Username: SMTP_USERNAME (canonical) -> SMTP_USER (alias)
        self._smtp_user = (
            os.environ.get(self.ENV_SMTP_USERNAME, "").strip()
            or os.environ.get(self.ALIAS_SMTP_USER, "").strip()
        )

        # Password: SMTP_PASSWORD (canonical) -> SMTP_PASS (alias)
        self._smtp_password = (
            os.environ.get(self.ENV_SMTP_PASSWORD, "").strip()
            or os.environ.get(self.ALIAS_SMTP_PASS, "").strip()
        )

        # Sender: SMTP_FROM_EMAIL (canonical) -> SMTP_FROM (alias) -> EMAIL_FROM (alias) -> default
        self._from_email = (
            os.environ.get(self.ENV_SMTP_FROM_EMAIL, "").strip()
            or os.environ.get(self.ALIAS_SMTP_FROM, "").strip()
            or os.environ.get(self.ALIAS_EMAIL_FROM, "").strip()
            or self.DEFAULT_FROM_EMAIL
        )

    @property
    def is_configured(self) -> bool:
        """Returns True if a real outbound email delivery provider is truthfully configured.
        
        Requires:
        - Host is non-empty.
        - For standard ports (587 STARTTLS, 465 SSL, etc.), both username and password must be set.
        - For port 25, unauthenticated internal relay is permitted if credentials are omitted.
        """
        if not self._smtp_host:
            return False
        if self._smtp_port == 25:
            return True
        return bool(self._smtp_user and self._smtp_password)

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

            if self._smtp_port == 465:
                server = smtplib.SMTP_SSL(self._smtp_host, self._smtp_port, timeout=10.0)
            else:
                server = smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=10.0)

            with server:
                server.ehlo()
                if self._smtp_port != 465 and server.has_extn("STARTTLS"):
                    server.starttls()
                    server.ehlo()
                if self._smtp_user and self._smtp_password:
                    server.login(self._smtp_user, self._smtp_password)
                server.send_message(msg)

            logger.info("Successfully delivered email to %s via SMTP (%s)", clean_to, self._smtp_host)
            return EmailDeliveryResult(success=True, provider="smtp", message_id="smtp-ok")
        except Exception as exc:
            # Sanitize exception message to ensure credentials, secrets, or internal details are never reflected
            raw_err = str(exc)
            sanitized_err = raw_err
            if self._smtp_password and self._smtp_password in sanitized_err:
                sanitized_err = sanitized_err.replace(self._smtp_password, "[REDACTED_PASSWORD]")
            if self._smtp_user and self._smtp_user in sanitized_err:
                sanitized_err = sanitized_err.replace(self._smtp_user, "[REDACTED_USER]")
            logger.error("Failed to deliver email to %s via SMTP (%s): %s", clean_to, self._smtp_host, sanitized_err)
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error=f"Delivery failed: {sanitized_err}",
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

    def send_staff_account_setup(
        self,
        to_email: str,
        applicant_name: str,
        username: str,
        setup_token: str,
        setup_url: str,
    ) -> EmailDeliveryResult:
        """Sends staff account provisioning credentials and setup link to approved applicant."""
        subject = "HealthAware Staff Account Provisioned — Initial Account Setup"
        text = (
            f"Dear {applicant_name},\n\n"
            f"Congratulations! Your application for a staff role with HealthAware has been approved.\n\n"
            f"Your staff username is: {username}\n\n"
            f"Please complete your initial account password setup using your single-use setup token:\n"
            f"Setup Token: {setup_token}\n\n"
            f"Set up your account online at:\n{setup_url}\n\n"
            f"This setup token is valid for 48 hours and can only be used once.\n\n"
            f"— HealthAware Administration\n"
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

