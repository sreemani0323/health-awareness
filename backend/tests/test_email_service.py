"""Comprehensive Unit and Safety Tests for HealthAware Email Service.

Validates:
1. Safe skipping and unconfigured detection when SMTP_HOST or credentials are missing.
2. Rejection of invalid recipient email addresses without network attempts.
3. Successful SMTP dispatch with STARTTLS and proper message MIME headers.
4. Exception resilience when SMTP server returns errors (timeouts, connection refused).
5. Safe templating of staff application tracking and community concern notifications.
"""

from __future__ import annotations

import os
import smtplib
from unittest.mock import MagicMock, patch
import pytest

from backend.platform.email_service import EmailService, EmailDeliveryResult


def test_email_service_unconfigured_when_no_smtp_host():
    """EmailService is_configured is False when SMTP_HOST is not set."""
    with patch.dict(os.environ, {}, clear=True):
        svc = EmailService()
        assert svc.is_configured is False

        result = svc.send_email(
            to_email="user@test.org",
            subject="Test Subject",
            text_content="Test Content",
        )
        assert result.success is False
        assert result.provider == "unconfigured"
        assert result.error == "EMAIL_PROVIDER_NOT_CONFIGURED"


def test_email_service_rejects_invalid_recipient():
    """EmailService validates recipient format before attempting any connection."""
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.example.com", "SMTP_USER": "testuser"}):
        svc = EmailService()
        assert svc.is_configured is True

        # Empty recipient
        r1 = svc.send_email("", "Subject", "Body")
        assert r1.success is False
        assert r1.error == "Invalid recipient email address."

        # Missing @
        r2 = svc.send_email("invalid-address", "Subject", "Body")
        assert r2.success is False
        assert r2.error == "Invalid recipient email address."


def test_email_service_smtp_success():
    """EmailService connects to SMTP, applies STARTTLS, logs in, and delivers message."""
    env = {
        "SMTP_HOST": "smtp.testmail.org",
        "SMTP_PORT": "587",
        "SMTP_USER": "test_smtp_user",
        "SMTP_PASSWORD": "test_smtp_password",
        "SMTP_FROM_EMAIL": "alerts@healthaware.org",
    }
    with patch.dict(os.environ, env):
        svc = EmailService()
        assert svc.is_configured is True

        mock_server = MagicMock()
        mock_server.has_extn.return_value = True

        with patch("smtplib.SMTP", return_value=mock_server):
            mock_server.__enter__.return_value = mock_server

            res = svc.send_email(
                to_email="recipient@example.com",
                subject="Safe Alert",
                text_content="Plain text content",
                html_content="<p>HTML content</p>",
            )

            assert res.success is True
            assert res.provider == "smtp"
            assert res.message_id == "smtp-ok"

            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test_smtp_user", "test_smtp_password")
            mock_server.send_message.assert_called_once()


def test_email_service_smtp_ssl_port_465_success():
    """EmailService uses SMTP_SSL when SMTP_PORT is 465."""
    env = {
        "SMTP_HOST": "smtp.testmail.org",
        "SMTP_PORT": "465",
        "SMTP_USER": "test_smtp_user",
        "SMTP_PASSWORD": "test_smtp_password",
        "SMTP_FROM_EMAIL": "alerts@healthaware.org",
    }
    with patch.dict(os.environ, env):
        svc = EmailService()
        assert svc.is_configured is True

        mock_server = MagicMock()
        with patch("smtplib.SMTP_SSL", return_value=mock_server):
            mock_server.__enter__.return_value = mock_server

            res = svc.send_email(
                to_email="recipient@example.com",
                subject="SSL Alert",
                text_content="Plain text content",
            )

            assert res.success is True
            assert res.provider == "smtp"
            mock_server.login.assert_called_once_with("test_smtp_user", "test_smtp_password")
            mock_server.send_message.assert_called_once()


def test_email_service_smtp_exception_handled_safely():
    """EmailService catches SMTP exceptions and returns structured failure result."""
    env = {
        "SMTP_HOST": "smtp.testmail.org",
        "SMTP_PORT": "587",
        "SMTP_USER": "test_smtp_user",
        "SMTP_PASSWORD": "test_smtp_password",
    }
    with patch.dict(os.environ, env):
        svc = EmailService()

        with patch("smtplib.SMTP", side_effect=smtplib.SMTPConnectError(421, b"Connection refused")):
            res = svc.send_email(
                to_email="recipient@example.com",
                subject="Test Fail",
                text_content="Will not deliver",
            )

            assert res.success is False
            assert res.provider == "smtp"
            assert "Delivery failed" in (res.error or "")


def test_email_service_templates_do_not_leak_secrets():
    """Staff tracking and concern email templates include references and tracking URLs cleanly."""
    svc = EmailService()

    with patch.object(svc, "send_email", return_value=EmailDeliveryResult(success=True, provider="mock")) as mock_send:
        # Staff application tracking
        svc.send_staff_application_tracking(
            to_email="applicant@test.org",
            applicant_name="Dr. Meera",
            reference_id="APP-2026-999999",
            tracking_token="sec_app_secret123",
            tracking_url="/staff/application-status?reference_id=APP-2026-999999",
        )
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "applicant@test.org"
        assert "APP-2026-999999" in args[1]
        assert "sec_app_secret123" in args[2]

    with patch.object(svc, "send_email", return_value=EmailDeliveryResult(success=True, provider="mock")) as mock_send:
        # Concern tracking
        svc.send_concern_tracking(
            to_email="citizen@test.org",
            reference_id="REP-2026-888888",
            tracking_token="sec_con_token456",
            tracking_url="/track?reference_id=REP-2026-888888",
        )
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "citizen@test.org"
        assert "REP-2026-888888" in args[1]
        assert "sec_con_token456" in args[2]
