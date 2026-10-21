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


def test_gmail_api_configuration_detection():
    """EmailService detects Gmail API OAuth 2.0 configuration accurately."""
    env = {
        "GMAIL_CLIENT_ID": "client-id-1234.apps.googleusercontent.com",
        "GMAIL_CLIENT_SECRET": "secret-xyz-token",
        "GMAIL_REFRESH_TOKEN": "1//04refreshtoken-abc",
        "GMAIL_SENDER_EMAIL": "authorized_sender@gmail.com",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        assert svc.is_gmail_api_configured is True
        assert svc.is_smtp_configured is False
        assert svc.is_configured is True
        assert svc._from_email == "authorized_sender@gmail.com"


def test_gmail_api_token_refresh_and_caching():
    """EmailService refreshes and safely caches OAuth access token."""
    env = {
        "GMAIL_CLIENT_ID": "cid",
        "GMAIL_CLIENT_SECRET": "csec",
        "GMAIL_REFRESH_TOKEN": "reftok",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "ya29.test_token_123", "expires_in": 3600}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            token, err = svc._get_gmail_access_token()
            assert token == "ya29.test_token_123"
            assert err is None
            assert mock_post.call_count == 1

            # Second call within expiry should use cache
            token2, err2 = svc._get_gmail_access_token()
            assert token2 == "ya29.test_token_123"
            assert mock_post.call_count == 1


def test_gmail_api_token_refresh_revoked_grant():
    """EmailService handles revoked/expired refresh tokens gracefully."""
    env = {
        "GMAIL_CLIENT_ID": "cid",
        "GMAIL_CLIENT_SECRET": "csec",
        "GMAIL_REFRESH_TOKEN": "expired_token",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Token has been expired or revoked.",
        }

        with patch("requests.post", return_value=mock_resp):
            token, err = svc._get_gmail_access_token()
            assert token is None
            assert "GMAIL_OAUTH_REVOKED" in err


def test_gmail_api_send_email_success():
    """EmailService successfully delivers email via Gmail REST API over HTTPS."""
    env = {
        "GMAIL_CLIENT_ID": "cid",
        "GMAIL_CLIENT_SECRET": "csec",
        "GMAIL_REFRESH_TOKEN": "reftok",
        "GMAIL_SENDER_EMAIL": "healthaware@gmail.com",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        with patch.object(svc, "_get_gmail_access_token", return_value=("ya29.valid_token", None)):
            mock_send_resp = MagicMock()
            mock_send_resp.status_code = 200
            mock_send_resp.json.return_value = {"id": "gmail_msg_id_9999"}

            with patch("requests.post", return_value=mock_send_resp) as mock_post:
                res = svc.send_email(
                    to_email="recipient@example.com",
                    subject="HealthAware Notification",
                    text_content="This is a test notification.",
                )

                assert res.success is True
                assert res.provider == "gmail_api"
                assert res.message_id == "gmail_msg_id_9999"
                assert mock_post.call_count == 1
                args, kwargs = mock_post.call_args
                assert kwargs["headers"]["Authorization"] == "Bearer ya29.valid_token"
                assert "raw" in kwargs["json"]


def test_gmail_api_quota_exceeded():
    """EmailService handles Gmail API quota exceeded gracefully."""
    env = {
        "GMAIL_CLIENT_ID": "cid",
        "GMAIL_CLIENT_SECRET": "csec",
        "GMAIL_REFRESH_TOKEN": "reftok",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        with patch.object(svc, "_get_gmail_access_token", return_value=("ya29.valid_token", None)):
            mock_send_resp = MagicMock()
            mock_send_resp.status_code = 429
            mock_send_resp.text = "Quota exceeded for quota metric 'Queries' and limit 'Queries per day'"

            with patch("requests.post", return_value=mock_send_resp):
                res = svc.send_email(
                    to_email="recipient@example.com",
                    subject="Notice",
                    text_content="Text",
                )
                assert res.success is False
                assert res.provider == "gmail_api"
                assert "GMAIL_API_QUOTA_EXCEEDED" in res.error


def test_gmail_api_precedence_over_smtp():
    """Gmail API HTTPS delivery takes precedence over SMTP relay."""
    env = {
        "GMAIL_CLIENT_ID": "cid",
        "GMAIL_CLIENT_SECRET": "csec",
        "GMAIL_REFRESH_TOKEN": "reftok",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "smtp_user",
        "SMTP_PASSWORD": "smtp_pass",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        assert svc.is_gmail_api_configured is True
        assert svc.is_smtp_configured is True
        assert svc.is_configured is True

        with patch.object(svc, "_send_via_gmail_api", return_value=EmailDeliveryResult(success=True, provider="gmail_api")) as mock_gmail:
            with patch.object(svc, "_send_via_smtp") as mock_smtp:
                res = svc.send_email(to_email="test@org.com", subject="Subj", text_content="Txt")
                assert res.provider == "gmail_api"
                mock_gmail.assert_called_once()
                mock_smtp.assert_not_called()


def test_gmail_api_credential_sanitization():
    """Client secrets and refresh tokens are scrubbed from error messages."""
    env = {
        "GMAIL_CLIENT_ID": "test_client_id_123",
        "GMAIL_CLIENT_SECRET": "super_secret_client_token_999",
        "GMAIL_REFRESH_TOKEN": "sensitive_refresh_token_777",
    }
    with patch.dict(os.environ, env, clear=True):
        svc = EmailService()
        raw_error = "Failed with super_secret_client_token_999 and sensitive_refresh_token_777 at endpoint"
        sanitized = svc._sanitize_error(raw_error)
        assert "super_secret_client_token_999" not in sanitized
        assert "sensitive_refresh_token_777" not in sanitized
        assert "[REDACTED_SECRET]" in sanitized


# --- System Diagnostic Endpoints Security Tests ---


def test_system_email_status_requires_admin():
    """GET /api/v1/system/email-status requires UserRole.ADMIN."""
    from backend.app import create_app
    app = create_app({"TESTING": True, "SKIP_NDB_CONTEXT": True})
    client = app.test_client()

    # 1. Anonymous request -> 401 Unauthorized
    resp = client.get("/api/v1/system/email-status")
    assert resp.status_code == 401

    # 2. Learner session -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_id"] = "learner-user-1"
        sess["role"] = "learner"
        sess["auth_time"] = 9999999999

    with patch("backend.controllers.auth.get_current_user") as mock_get_user:
        from backend.domain.domain_objects import User, UserRole
        mock_get_user.return_value = User(
            user_id="learner-user-1",
            username="learner1",
            display_name="Learner",
            role=UserRole.LEARNER,
            password_hash="pwd",
        )
        resp = client.get("/api/v1/system/email-status")
        assert resp.status_code == 403

    # 3. Contributor session -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_id"] = "contrib-user-1"
        sess["role"] = "contributor"
        sess["auth_time"] = 9999999999

    with patch("backend.controllers.auth.get_current_user") as mock_get_user:
        mock_get_user.return_value = User(
            user_id="contrib-user-1",
            username="contrib1",
            display_name="Contributor",
            role=UserRole.CONTRIBUTOR,
            password_hash="pwd",
        )
        resp = client.get("/api/v1/system/email-status")
        assert resp.status_code == 403

    # 4. Admin session -> 200 OK
    with client.session_transaction() as sess:
        sess["user_id"] = "admin-user-1"
        sess["role"] = "admin"
        sess["auth_time"] = 9999999999

    with patch("backend.controllers.auth.get_current_user") as mock_get_user:
        from backend.domain.domain_objects import User, UserRole
        mock_get_user.return_value = User(
            user_id="admin-user-1",
            username="admin@healthaware.org",
            display_name="Admin",
            role=UserRole.ADMIN,
            password_hash="pwd",
        )
        resp = client.get("/api/v1/system/email-status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "is_configured" in data
        assert "active_provider" in data
        assert "delivery_channel" in data
        assert "client_secret" not in str(data)


def test_system_email_test_requires_admin_and_authorized_recipient():
    """POST /api/v1/system/email-test enforces admin authorization and recipient restriction."""
    from backend.app import create_app
    app = create_app({"TESTING": True, "SKIP_NDB_CONTEXT": True})
    client = app.test_client()

    # 1. Anonymous request -> 401 Unauthorized
    resp = client.post("/api/v1/system/email-test", json={"recipient": "anyone@victim.com"})
    assert resp.status_code == 401

    # 2. Learner session -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_id"] = "learner-user-1"
        sess["role"] = "learner"
        sess["auth_time"] = 9999999999

    with patch("backend.controllers.auth.get_current_user") as mock_get_user:
        from backend.domain.domain_objects import User, UserRole
        mock_get_user.return_value = User(
            user_id="learner-user-1",
            username="learner1",
            display_name="Learner",
            role=UserRole.LEARNER,
            password_hash="pwd",
        )
        resp = client.post("/api/v1/system/email-test", json={"recipient": "anyone@victim.com"})
        assert resp.status_code == 403

    # 3. Admin session with unauthorized external recipient -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_id"] = "admin-user-1"
        sess["role"] = "admin"
        sess["auth_time"] = 9999999999

    with patch("backend.controllers.auth.get_current_user") as mock_get_user:
        from backend.domain.domain_objects import User, UserRole
        mock_get_user.return_value = User(
            user_id="admin-user-1",
            username="admin@healthaware.org",
            display_name="Admin",
            role=UserRole.ADMIN,
            password_hash="pwd",
        )
        resp = client.post("/api/v1/system/email-test", json={"recipient": "unauthorized_stranger@target.com"})
        assert resp.status_code == 403
        assert "restricted" in resp.get_json()["error"]["message"]

        # 4. Admin session with authorized recipient -> 200 OK
        from backend.platform.email_service import set_email_service, EmailService
        mock_svc = MagicMock(spec=EmailService)
        mock_svc._from_email = "admin@healthaware.org"
        mock_svc.is_gmail_api_configured = True
        mock_svc.send_email.return_value = EmailDeliveryResult(success=True, provider="gmail_api", message_id="gmail-101")
        set_email_service(mock_svc)

        resp = client.post("/api/v1/system/email-test", json={"recipient": "admin@healthaware.org"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["success"] is True
        assert data["provider"] == "gmail_api"
        set_email_service(None)


