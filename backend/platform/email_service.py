"""Transactional email delivery service with safe HTTPS API and SMTP provider abstractions.

Delivery Channels:
1. Primary / HTTPS API (No-Custom-Domain, Render Free Tier Compatible):
   - Google Gmail API via OAuth 2.0 (gmail.send scope) over port 443 (HTTPS)
   - Configuration variables:
     * GMAIL_CLIENT_ID: OAuth 2.0 Client ID from Google Cloud Console
     * GMAIL_CLIENT_SECRET: OAuth 2.0 Client Secret
     * GMAIL_REFRESH_TOKEN: Long-lived OAuth 2.0 Refresh Token
     * GMAIL_SENDER_EMAIL: Sender Gmail address (defaults to authorized account)

2. Fallback / SMTP Relay (Paid Hosting / Internal Relay):
   - Canonical: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL
   - Aliases: SMTP_SERVER, SMTP_USER, SMTP_PASS, SMTP_FROM, EMAIL_FROM

Safety & Privacy Guarantees:
- When unconfigured or missing credentials, dispatch is truthfully skipped without throwing exceptions.
- Failed deliveries are never reported as successful.
- No client secret, refresh token, access token, password, or secret is ever exposed in logs or exception messages.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
import smtplib
import time
from typing import Optional
import requests

logger = logging.getLogger(__name__)


@dataclass
class EmailDeliveryResult:
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailService:
    """Manages transactional email dispatch for HealthAware."""

    # Gmail API OAuth 2.0 Environment Variables
    ENV_GMAIL_CLIENT_ID = "GMAIL_CLIENT_ID"
    ENV_GMAIL_CLIENT_SECRET = "GMAIL_CLIENT_SECRET"
    ENV_GMAIL_REFRESH_TOKEN = "GMAIL_REFRESH_TOKEN"
    ENV_GMAIL_SENDER_EMAIL = "GMAIL_SENDER_EMAIL"

    # SMTP Canonical Environment Variables
    ENV_SMTP_HOST = "SMTP_HOST"
    ENV_SMTP_PORT = "SMTP_PORT"
    ENV_SMTP_USERNAME = "SMTP_USERNAME"
    ENV_SMTP_PASSWORD = "SMTP_PASSWORD"
    ENV_SMTP_FROM_EMAIL = "SMTP_FROM_EMAIL"

    # SMTP Backward-Compatible Aliases
    ALIAS_SMTP_SERVER = "SMTP_SERVER"
    ALIAS_SMTP_USER = "SMTP_USER"
    ALIAS_SMTP_PASS = "SMTP_PASS"
    ALIAS_SMTP_FROM = "SMTP_FROM"
    ALIAS_EMAIL_FROM = "EMAIL_FROM"

    DEFAULT_FROM_EMAIL = "noreply@healthaware.org"
    GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GMAIL_API_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    def __init__(self):
        # Gmail API OAuth 2.0 Configuration
        self._gmail_client_id = os.environ.get(self.ENV_GMAIL_CLIENT_ID, "").strip()
        self._gmail_client_secret = os.environ.get(self.ENV_GMAIL_CLIENT_SECRET, "").strip()
        self._gmail_refresh_token = os.environ.get(self.ENV_GMAIL_REFRESH_TOKEN, "").strip()

        # Cached access token and expiration timestamp
        self._cached_access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # SMTP Configuration
        self._smtp_host = (
            os.environ.get(self.ENV_SMTP_HOST, "").strip()
            or os.environ.get(self.ALIAS_SMTP_SERVER, "").strip()
        )

        port_raw = os.environ.get(self.ENV_SMTP_PORT, "").strip()
        try:
            self._smtp_port = int(port_raw) if port_raw else 587
        except ValueError:
            logger.warning("Invalid SMTP_PORT '%s', defaulting to 587", port_raw)
            self._smtp_port = 587

        self._smtp_user = (
            os.environ.get(self.ENV_SMTP_USERNAME, "").strip()
            or os.environ.get(self.ALIAS_SMTP_USER, "").strip()
        )

        self._smtp_password = (
            os.environ.get(self.ENV_SMTP_PASSWORD, "").strip()
            or os.environ.get(self.ALIAS_SMTP_PASS, "").strip()
        )

        # Sender resolution (Gmail sender -> SMTP from -> Alias -> Default)
        self._from_email = (
            os.environ.get(self.ENV_GMAIL_SENDER_EMAIL, "").strip()
            or os.environ.get(self.ENV_SMTP_FROM_EMAIL, "").strip()
            or os.environ.get(self.ALIAS_SMTP_FROM, "").strip()
            or os.environ.get(self.ALIAS_EMAIL_FROM, "").strip()
            or self.DEFAULT_FROM_EMAIL
        )

    @property
    def is_gmail_api_configured(self) -> bool:
        """Returns True if the Google Gmail API HTTPS provider is fully configured."""
        return bool(self._gmail_client_id and self._gmail_client_secret and self._gmail_refresh_token)

    @property
    def is_smtp_configured(self) -> bool:
        """Returns True if standard SMTP outbound relay is configured."""
        if not self._smtp_host:
            return False
        if self._smtp_port == 25:
            return True
        return bool(self._smtp_user and self._smtp_password)

    @property
    def is_configured(self) -> bool:
        """Returns True if either Gmail API (HTTPS) or SMTP is truthfully configured."""
        return self.is_gmail_api_configured or self.is_smtp_configured

    def _sanitize_error(self, err_text: str) -> str:
        """Removes any credentials, secrets, or tokens from error text."""
        sanitized = str(err_text)
        if self._smtp_password and len(self._smtp_password) > 3 and self._smtp_password in sanitized:
            sanitized = sanitized.replace(self._smtp_password, "[REDACTED_PASSWORD]")
        if self._smtp_user and len(self._smtp_user) > 3 and self._smtp_user in sanitized:
            sanitized = sanitized.replace(self._smtp_user, "[REDACTED_USER]")
        for secret in [self._gmail_client_secret, self._gmail_refresh_token, self._cached_access_token]:
            if secret and len(secret) > 3 and secret in sanitized:
                sanitized = sanitized.replace(secret, "[REDACTED_SECRET]")
        return sanitized

    def _get_gmail_access_token(self) -> tuple[Optional[str], Optional[str]]:
        """Retrieves or refreshes an OAuth 2.0 access token for the Gmail API.

        Returns:
            (access_token, None) on success
            (None, error_message) on failure
        """
        now = time.time()
        # Reuse cached token if still valid (with 60-second safety margin)
        if self._cached_access_token and (now < self._token_expires_at - 60):
            return self._cached_access_token, None

        payload = {
            "client_id": self._gmail_client_id,
            "client_secret": self._gmail_client_secret,
            "refresh_token": self._gmail_refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            resp = requests.post(
                self.GOOGLE_OAUTH_TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=8.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                expires_in = int(data.get("expires_in", 3600))
                self._cached_access_token = token
                self._token_expires_at = now + expires_in
                return token, None

            # Handle Google OAuth error responses
            err_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_code = err_data.get("error", f"HTTP_{resp.status_code}")
            err_desc = err_data.get("error_description", resp.text[:200])

            if err_code == "invalid_grant":
                logger.error("Gmail OAuth 2.0 refresh token expired or revoked.")
                return None, "GMAIL_OAUTH_REVOKED: Refresh token has been expired or revoked by account owner."

            sanitized_desc = self._sanitize_error(err_desc)
            logger.error("Gmail OAuth 2.0 token refresh failed (%s): %s", err_code, sanitized_desc)
            return None, f"GMAIL_OAUTH_ERROR ({err_code}): {sanitized_desc}"

        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to Google OAuth 2.0 token endpoint.")
            return None, "GMAIL_OAUTH_TIMEOUT: Connection to Google OAuth token endpoint timed out."
        except Exception as exc:
            sanitized = self._sanitize_error(str(exc))
            logger.error("Unexpected error during Gmail OAuth token refresh: %s", sanitized)
            return None, f"GMAIL_OAUTH_EXCEPTION: {sanitized}"

    def _send_via_gmail_api(
        self,
        clean_to: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Dispatches an email over HTTPS using the Gmail REST API (users.messages.send)."""
        access_token, auth_error = self._get_gmail_access_token()
        if not access_token:
            return EmailDeliveryResult(
                success=False,
                provider="gmail_api",
                error=auth_error,
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._from_email
            msg["To"] = clean_to

            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            if html_content:
                msg.attach(MIMEText(html_content, "html", "utf-8"))

            raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            body = {"raw": raw_b64}

            resp = requests.post(
                self.GMAIL_API_SEND_URL,
                headers=headers,
                json=body,
                timeout=10.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                msg_id = data.get("id")
                logger.info("Successfully dispatched email to %s via Gmail API (msg_id=%s)", clean_to, msg_id)
                return EmailDeliveryResult(
                    success=True,
                    provider="gmail_api",
                    message_id=msg_id,
                )

            # Invalidate cached token if unauthorized (401)
            if resp.status_code == 401:
                self._cached_access_token = None
                logger.warning("Gmail API returned 401 Unauthorized; token invalidated.")
                return EmailDeliveryResult(
                    success=False,
                    provider="gmail_api",
                    error="GMAIL_API_UNAUTHORIZED: Access token invalid or expired.",
                )

            # Quota or rate limit exceeded (429 or 403 quota)
            if resp.status_code in (429, 403) and "quota" in resp.text.lower():
                logger.warning("Gmail API daily sending quota exceeded.")
                return EmailDeliveryResult(
                    success=False,
                    provider="gmail_api",
                    error="GMAIL_API_QUOTA_EXCEEDED: Daily sending limit reached.",
                )

            raw_err = resp.text[:300]
            sanitized_err = self._sanitize_error(raw_err)
            logger.error("Gmail API delivery failed (HTTP %s): %s", resp.status_code, sanitized_err)
            return EmailDeliveryResult(
                success=False,
                provider="gmail_api",
                error=f"GMAIL_API_HTTP_{resp.status_code}: {sanitized_err}",
            )

        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to Gmail REST API endpoint.")
            return EmailDeliveryResult(
                success=False,
                provider="gmail_api",
                error="GMAIL_API_TIMEOUT: Request to Gmail API timed out.",
            )
        except Exception as exc:
            sanitized = self._sanitize_error(str(exc))
            logger.error("Failed to dispatch email via Gmail API: %s", sanitized)
            return EmailDeliveryResult(
                success=False,
                provider="gmail_api",
                error=f"GMAIL_API_ERROR: {sanitized}",
            )

    def _send_via_smtp(
        self,
        clean_to: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Dispatches an email via standard SMTP relay."""
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
            sanitized_err = self._sanitize_error(str(exc))
            logger.error("Failed to deliver email to %s via SMTP (%s): %s", clean_to, self._smtp_host, sanitized_err)
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error=f"Delivery failed: {sanitized_err}",
            )

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
    ) -> EmailDeliveryResult:
        """Dispatches an email via the best available configured provider (Gmail API HTTPS -> SMTP)."""
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

        # Precedence: Gmail API over HTTPS (port 443) takes priority over blocked SMTP
        if self.is_gmail_api_configured:
            return self._send_via_gmail_api(clean_to, subject, text_content, html_content)

        return self._send_via_smtp(clean_to, subject, text_content, html_content)

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
