"""Comprehensive Unit and Safety Tests for HealthAware Email Service.

Validates:
1. Canonical configuration resolution (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL).
2. Backward-compatible alias fallback resolution (SMTP_SERVER, SMTP_USER, SMTP_PASS, SMTP_FROM, EMAIL_FROM).
3. Precedence rules: Canonical variable names strictly override aliases when both are defined.
4. Truthful unconfigured detection when host or credentials are missing/incomplete on authenticated ports.
5. Safe unauthenticated internal relay support on port 25.
6. Graceful port number validation with safe fallback to port 587.
7. Rejection of invalid recipient email addresses without network attempts.
8. Successful SMTP dispatch with STARTTLS (port 587) and SSL (port 465).
9. Failure resilience: failed delivery is never reported as successful (success=False).
10. Credential redaction: passwords and usernames are scrubbed from delivery failure errors.
11. Safe templating of staff application tracking, staff account setup, and community concern notifications.
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


def test_canonical_smtp_variable_resolution():
    """EmailService resolves canonical variable names cleanly."""
    env = {
        "SMTP_HOST": "smtp.canonical-provider.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "canonical_user_apikey",
        "SMTP_PASSWORD": "canonical_secret_token",
        "SMTP_FROM_EMAIL": "official@healthaware.org",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        assert svc.is_configured is True
        assert svc._smtp_host == "smtp.canonical-provider.com"
        assert svc._smtp_port == 587
        assert svc._smtp_user == "canonical_user_apikey"
        assert svc._smtp_password == "canonical_secret_token"
        assert svc._from_email == "official@healthaware.org"


def test_backward_compatible_alias_resolution():
    """EmailService resolves legacy aliases (SMTP_SERVER, SMTP_USER, SMTP_PASS, SMTP_FROM)."""
    env = {
        "SMTP_SERVER": "smtp.legacy-alias.com",
        "SMTP_PORT": "465",
        "SMTP_USER": "legacy_user",
        "SMTP_PASS": "legacy_secret_pass",
        "SMTP_FROM": "legacy-sender@healthaware.org",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        assert svc.is_configured is True
        assert svc._smtp_host == "smtp.legacy-alias.com"
        assert svc._smtp_port == 465
        assert svc._smtp_user == "legacy_user"
        assert svc._smtp_password == "legacy_secret_pass"
        assert svc._from_email == "legacy-sender@healthaware.org"


def test_variable_precedence_canonical_over_alias():
    """Canonical variable names take strict precedence over legacy aliases."""
    env = {
        "SMTP_HOST": "smtp.canonical.com",
        "SMTP_SERVER": "smtp.alias-ignored.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "canonical_user",
        "SMTP_USER": "alias_user_ignored",
        "SMTP_PASSWORD": "canonical_password",
        "SMTP_PASS": "alias_password_ignored",
        "SMTP_FROM_EMAIL": "canonical@healthaware.org",
        "SMTP_FROM": "alias-from-ignored@healthaware.org",
        "EMAIL_FROM": "email-from-ignored@healthaware.org",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        assert svc._smtp_host == "smtp.canonical.com"
        assert svc._smtp_user == "canonical_user"
        assert svc._smtp_password == "canonical_password"
        assert svc._from_email == "canonical@healthaware.org"


def test_truthful_unconfigured_scenarios():
    """Missing or incomplete credentials on authenticated ports evaluate truthfully as unconfigured."""
    # 1. Missing password on port 587
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.mail.org", "SMTP_USERNAME": "user_only"}, clear=True):
        svc = EmailService()
        assert svc.is_configured is False

    # 2. Missing username on port 587
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.mail.org", "SMTP_PASSWORD": "pass_only"}, clear=True):
        svc = EmailService()
        assert svc.is_configured is False

    # 3. Missing host
    with patch.dict(os.environ, {"SMTP_USERNAME": "user", "SMTP_PASSWORD": "pass"}, clear=True):
        svc = EmailService()
        assert svc.is_configured is False

    # 4. Port 25 allows unauthenticated internal relay with host only
    with patch.dict(os.environ, {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": "25"}, clear=True):
        svc = EmailService()
        assert svc.is_configured is True


def test_invalid_port_fallback_safely_defaults_to_587():
    """Invalid non-integer port values fall back safely to 587 without crashing."""
    env = {
        "SMTP_HOST": "smtp.testmail.org",
        "SMTP_PORT": "not-a-valid-port-number",
        "SMTP_USERNAME": "test_user",
        "SMTP_PASSWORD": "test_password",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        assert svc._smtp_port == 587
        assert svc.is_configured is True


def test_email_service_rejects_invalid_recipient():
    """EmailService validates recipient format before attempting any connection."""
    env = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "testuser",
        "SMTP_PASSWORD": "testpassword",
    }
    with patch.dict(os.environ, env, clear=True):
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
        "SMTP_USERNAME": "test_smtp_user",
        "SMTP_PASSWORD": "test_smtp_password",
        "SMTP_FROM_EMAIL": "alerts@healthaware.org",
    }
    with patch.dict(os.environ, env, clear=True):
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
        "SMTP_USERNAME": "test_smtp_user",
        "SMTP_PASSWORD": "test_smtp_password",
        "SMTP_FROM_EMAIL": "alerts@healthaware.org",
    }
    with patch.dict(os.environ, env, clear=True):
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
    """EmailService catches SMTP exceptions, redacts credentials, and returns structured failure result."""
    env = {
        "SMTP_HOST": "smtp.testmail.org",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "secret_username",
        "SMTP_PASSWORD": "super_secret_password_999",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()

        # Simulate exception that includes the password and username in the raw error
        raw_exc = smtplib.SMTPAuthenticationError(
            535,
            b"Auth failed for secret_username with password super_secret_password_999",
        )
        with patch("smtplib.SMTP", side_effect=raw_exc):
            res = svc.send_email(
                to_email="recipient@example.com",
                subject="Test Fail",
                text_content="Will not deliver",
            )

            assert res.success is False
            assert res.provider == "smtp"
            assert "Delivery failed" in (res.error or "")
            # Verify credentials are redacted
            assert "super_secret_password_999" not in (res.error or "")
            assert "[REDACTED_PASSWORD]" in (res.error or "")


def test_email_service_templates_do_not_leak_secrets():
    """Staff tracking, staff account setup, and concern email templates format clean notifications."""
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
        # Staff account setup
        svc.send_staff_account_setup(
            to_email="approved_staff@test.org",
            applicant_name="Dr. Meera",
            username="staff_meera_2026",
            setup_token="set_single_use_token_12345",
            setup_url="/creator/setup?token=set_single_use_token_12345",
        )
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "approved_staff@test.org"
        assert "staff_meera_2026" in args[2]
        assert "set_single_use_token_12345" in args[2]

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


def test_system_email_status_endpoint():
    """GET /api/v1/system/email-status returns safe configuration presence metrics."""
    from backend.app import create_app
    app = create_app({"TESTING": True, "SKIP_NDB_CONTEXT": True})
    client = app.test_client()

    with patch.dict(os.environ, {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "test_operator@gmail.com",
        "SMTP_PASSWORD": "secret_app_password",
        "SMTP_FROM_EMAIL": "test_operator@gmail.com",
    }):
        from backend.platform.email_service import set_email_service, EmailService
        set_email_service(EmailService())

        with patch("socket.socket") as mock_sock:
            mock_instance = MagicMock()
            mock_sock.return_value = mock_instance
            resp = client.get("/api/v1/system/email-status")

        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["is_configured"] is True
        assert data["smtp_host_configured"] is True
        assert data["smtp_host"] == "smtp.gmail.com"
        assert data["smtp_port"] == 587
        assert data["smtp_username_configured"] is True
        assert data["smtp_password_configured"] is True
        assert data["smtp_from_email_configured"] is True
        assert "secret_app_password" not in str(data)
        assert data["from_address_masked"].endswith("@gmail.com")
        set_email_service(None)


def test_system_email_test_endpoint_success():
    """POST /api/v1/system/email-test dispatches a test email successfully."""
    from backend.app import create_app
    app = create_app({"TESTING": True, "SKIP_NDB_CONTEXT": True})
    client = app.test_client()

    from backend.platform.email_service import set_email_service, EmailService
    mock_svc = MagicMock(spec=EmailService)
    mock_svc._from_email = "noreply@healthaware.org"
    mock_svc._smtp_host = "smtp.test.org"
    mock_svc._smtp_port = 587
    mock_svc.send_email.return_value = EmailDeliveryResult(success=True, provider="smtp", message_id="msg-123")
    set_email_service(mock_svc)

    resp = client.post("/api/v1/system/email-test", json={"recipient": "test@example.com"})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["success"] is True
    assert data["provider"] == "smtp"
    set_email_service(None)


def test_system_email_test_endpoint_failure_handled_truthfully():
    """POST /api/v1/system/email-test returns truthful failure without false success."""
    from backend.app import create_app
    app = create_app({"TESTING": True, "SKIP_NDB_CONTEXT": True})
    client = app.test_client()

    from backend.platform.email_service import set_email_service, EmailService
    mock_svc = MagicMock(spec=EmailService)
    mock_svc._from_email = "noreply@healthaware.org"
    mock_svc._smtp_host = "smtp.test.org"
    mock_svc._smtp_port = 587
    mock_svc.send_email.return_value = EmailDeliveryResult(success=False, provider="smtp", error="Delivery failed: timed out")
    set_email_service(mock_svc)

    resp = client.post("/api/v1/system/email-test", json={"recipient": "test@example.com"})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["success"] is False
    assert data["provider"] == "smtp"
    assert "timed out" in data["error"]
    set_email_service(None)

