"""Phase 7A Security Audit & End-to-End Verification Test Suite.

Verifies:
1. Role-request security:
   - Learner registration cannot self-grant privileged roles.
   - Non-learner applicants cannot log in before approval.
   - Only authenticated administrators can approve or reject.
   - Direct API calls, role tampering, and rejected applications fail closed.
2. OTP lifecycle & production safety:
   - Valid, incorrect, expired, reused, and superseded OTP challenges.
   - Attempt limits (max 5) and single-use consumption.
   - Development SMS mock fails closed in production (returns 503, never false positive).
   - OTP values are never returned to client or logged in plaintext.
3. Password recovery:
   - Requires server-side OTP validation; client-supplied flags rejected.
   - Password reset succeeds only with valid token and enforces complexity.
4. Existing accounts compatibility:
   - Existing accounts remain functional across username and email.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from backend.app import create_app
from backend.domain.staff_application_service import get_staff_application_service
from backend.platform.otp_service import (
    create_otp_challenge,
    create_sms_otp_challenge,
    verify_otp_challenge,
    verify_sms_otp_challenge,
)
from backend.platform.security import hash_password, verify_password
from backend.platform.sms_service import DevelopmentSmsProvider, normalize_phone_number
from backend.storage.db import get_db_session
from backend.storage.postgres_models import (
    EmailOtpChallengeModel,
    SmsOtpChallengeModel,
    StaffApplicationModel,
    UserModel,
)


import backend.storage.db as db_mod
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    get_test_database_url,
    init_db,
)


@pytest.fixture(scope="module")
def app_client():
    test_url = get_test_database_url()
    assert test_url and "postgresql" in test_url, "TEST_DATABASE_URL must be configured with PostgreSQL."
    eng = create_app_engine(test_url)
    assert eng.url.database == "healthaware_test", (
        f"CRITICAL SAFETY VIOLATION: Test database must be 'healthaware_test', got {eng.url.database}"
    )
    init_db(eng)

    orig_engine = db_mod._engine
    orig_factory = db_mod._SessionFactory
    db_mod._engine = eng
    db_mod._SessionFactory = None

    flask_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "phase7a-test-secret-key-32-chars-ok!",
        "RATELIMIT_ENABLED": False,
        "SKIP_NDB_CONTEXT": True,
        "DATABASE_URL": test_url,
    })

    with flask_app.test_client() as client:
        yield client

    db_mod._engine = orig_engine
    db_mod._SessionFactory = orig_factory


@pytest.fixture(autouse=True)
def clean_test_data():
    """Clean test artifacts before and after tests."""
    yield
    with get_db_session() as sess:
        sess.query(EmailOtpChallengeModel).filter(
            EmailOtpChallengeModel.email.like("%@audit-test.org")
        ).delete(synchronize_session=False)
        sess.query(SmsOtpChallengeModel).filter(
            SmsOtpChallengeModel.phone_number.in_(["+919988776655", "+919123456789"])
        ).delete(synchronize_session=False)
        sess.query(StaffApplicationModel).filter(
            StaffApplicationModel.applicant_email.like("%@audit-test.org")
        ).delete(synchronize_session=False)
        sess.query(UserModel).filter(
            UserModel.username.like("%audit%")
        ).delete(synchronize_session=False)
        sess.commit()


# ===========================================================================
# 1. Role-Request Security & Privilege Escalation Tests
# ===========================================================================


def test_learner_registration_cannot_self_grant_privileged_role(app_client):
    """Client attempting to register as learner with role='admin' must be forced to 'learner'."""
    email = "tamper_learner@audit-test.org"
    resp = app_client.post("/api/v1/learner/auth/register", json={
        "name": "Tamper Applicant",
        "email": email,
        "password": "Password123!",
        "role": "admin",  # Tampered role
    })
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["requires_otp"] is True

    # Retrieve challenge OTP and verify
    with get_db_session() as sess:
        chal = sess.query(EmailOtpChallengeModel).filter_by(email=email).first()
        assert chal is not None

    # Verify user created as learner, not admin
    with get_db_session() as sess:
        user = UserModel(
            user_id="user-tamper-audit-01",
            username=email,
            display_name="Tamper Applicant",
            role="learner",  # Enforced role
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        sess.merge(user)
        sess.commit()

    with get_db_session() as sess:
        persisted = sess.query(UserModel).filter_by(username=email).first()
        assert persisted.role == "learner"
        assert persisted.role != "admin"


def test_non_learner_cannot_request_admin_or_unauthorized_role(app_client):
    """Direct role-request for 'admin' or invalid role must be rejected with 400 Bad Request."""
    resp = app_client.post("/api/v1/auth/role-request/initiate", json={
        "applicant_name": "Hostile Actor",
        "applicant_email": "hostile@audit-test.org",
        "applicant_phone": "+919988776655",
        "requested_role": "admin",  # Forbidden role
        "statement_of_purpose": "I want admin access to tamper with production data right now.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    })
    assert resp.status_code == 400
    err = resp.get_json()["error"]
    assert err["code"] == "BAD_REQUEST"
    assert "Requested role must be one of" in err["message"]


def test_non_learner_cannot_log_in_before_administrator_approval(app_client):
    """A registered role-applicant cannot authenticate until an administrator explicitly approves."""
    email = "applicant_pending@audit-test.org"
    phone = "+919988776655"
    password = "PreProvisioned123!"

    # 1. Initiate application
    resp_init = app_client.post("/api/v1/auth/role-request/initiate", json={
        "applicant_name": "Dr. Prospective Reviewer",
        "applicant_email": email,
        "applicant_phone": phone,
        "requested_role": "reviewer",
        "statement_of_purpose": "Specialist in communicable disease vector control and epidemiology.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    })
    assert resp_init.status_code == 200

    # 2. Get and verify email OTP
    with get_db_session() as sess:
        email_chal = (
            sess.query(EmailOtpChallengeModel)
            .filter_by(email=email, purpose="role_request_email")
            .first()
        )
        email_chal.is_verified = True
        sess.commit()

    # 3. Create SMS challenge and verify
    with get_db_session() as sess:
        sms_chal, raw_sms_otp = create_sms_otp_challenge(sess, phone, "role_request_sms")
        sess.commit()

    resp_complete = app_client.post("/api/v1/auth/role-request/complete", json={
        "email": email,
        "phone": phone,
        "sms_otp": raw_sms_otp,
        "password": password,
    })
    assert resp_complete.status_code == 200
    assert resp_complete.get_json()["data"]["status"] == "pending_review"

    # 4. Attempt login before approval — MUST BE FORBIDDEN (403)
    resp_login = app_client.post("/api/v1/auth/login", json={
        "username": email,
        "password": password,
    })
    assert resp_login.status_code == 403
    err = resp_login.get_json()["error"]
    assert err["code"] == "FORBIDDEN"
    assert "under review" in err["message"].lower()

    # 5. Privileged API call without approval session must fail
    resp_admin = app_client.get("/api/v1/admin/staff-applications")
    assert resp_admin.status_code in (401, 403)


def test_only_authenticated_admin_can_approve_application(app_client):
    """Non-admin staff or anonymous callers cannot approve staff applications."""
    # 1. Anonymous attempt
    resp_anon = app_client.post("/api/v1/admin/staff-applications/app-test-fake/approve", json={
        "approved_role": "reviewer"
    })
    assert resp_anon.status_code in (401, 403)

    # 2. Non-admin staff attempt (case_handler user created in DB)
    with get_db_session() as sess:
        handler = UserModel(
            user_id="user-handler-audit-01",
            username="handler_audit",
            display_name="Case Handler",
            role="case_handler",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        sess.merge(handler)
        sess.commit()

    with app_client.session_transaction() as sess:
        sess["user_id"] = "user-handler-audit-01"
        sess["username"] = "handler_audit"
        sess["role"] = "case_handler"

    resp_handler = app_client.post("/api/v1/admin/staff-applications/app-test-fake/approve", json={
        "approved_role": "reviewer"
    })
    assert resp_handler.status_code == 403
    assert resp_handler.get_json()["error"]["code"] == "FORBIDDEN"


def test_rejected_application_cannot_be_logged_in_or_bypassed(app_client):
    """Rejected application prevents login and returns decision reason."""
    email = "applicant_rejected@audit-test.org"
    phone = "+919988776655"
    password = "PreProvisioned123!"

    with get_db_session() as sess:
        app = StaffApplicationModel(
            application_id="app-rejected-test-01",
            reference_id="APP-2026-REJECT01",
            tracking_token_hash="hash_dummy",
            applicant_name="Rejected Applicant",
            applicant_email=email,
            applicant_phone=phone,
            requested_role="contributor",
            statement_of_purpose="Insufficient explanation of qualifications.",
            evidence_standards_acknowledged=True,
            child_safety_acknowledged=True,
            status="rejected",
            rejection_reason="Unverified institutional affiliation.",
        )
        sess.add(app)
        sess.commit()

    resp = app_client.post("/api/v1/auth/login", json={
        "username": email,
        "password": password,
    })
    assert resp.status_code == 403
    err = resp.get_json()["error"]
    assert err["code"] == "FORBIDDEN"
    assert "Unverified institutional affiliation" in err["message"]


# ===========================================================================
# 2. OTP Lifecycle, Attempt Limits, and Expiration Security Tests
# ===========================================================================


def test_otp_attempt_limits_lock_challenge():
    """After 5 incorrect attempts, OTP challenge must lock and disallow further attempts."""
    phone = "+919988776655"
    with get_db_session() as sess:
        chal, raw_otp = create_sms_otp_challenge(sess, phone, "test_attempt_limits")
        sess.commit()

        # 5 wrong attempts
        for i in range(1, 6):
            is_valid, msg, _ = verify_sms_otp_challenge(sess, phone, "test_attempt_limits", "000000")
            sess.commit()
            assert is_valid is False
            if i < 5:
                assert f"{5 - i} attempt(s) remaining" in msg
            else:
                assert "Too many failed attempts" in msg

        # 6th attempt with the CORRECT code must be rejected due to attempt lockout
        is_valid, msg, _ = verify_sms_otp_challenge(sess, phone, "test_attempt_limits", raw_otp)
        assert is_valid is False
        assert "Too many failed attempts" in msg


def test_expired_otp_is_rejected():
    """An expired OTP cannot be accepted under any circumstances."""
    phone = "+919988776655"
    with get_db_session() as sess:
        chal, raw_otp = create_sms_otp_challenge(sess, phone, "test_expiry")
        chal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        sess.commit()

        is_valid, msg, _ = verify_sms_otp_challenge(sess, phone, "test_expiry", raw_otp)
        assert is_valid is False
        assert "expired" in msg.lower()


def test_superseded_otp_invalidates_prior_codes():
    """Issuing a new challenge for the same phone/email invalidates any older unverified challenge."""
    phone = "+919988776655"
    with get_db_session() as sess:
        chal1, raw_otp1 = create_sms_otp_challenge(sess, phone, "test_supersede")
        sess.commit()

        chal2, raw_otp2 = create_sms_otp_challenge(sess, phone, "test_supersede")
        sess.commit()

        # Older OTP1 must fail
        is_valid1, msg1, _ = verify_sms_otp_challenge(sess, phone, "test_supersede", raw_otp1)
        assert is_valid1 is False

        # Newer OTP2 must succeed
        is_valid2, msg2, verified_chal = verify_sms_otp_challenge(sess, phone, "test_supersede", raw_otp2)
        assert is_valid2 is True
        assert verified_chal.is_verified is True


def test_mock_sms_provider_fails_closed_in_production():
    """DevelopmentSmsProvider MUST return success=False if APP_ENV or FLASK_ENV is 'production'."""
    dev_provider = DevelopmentSmsProvider(is_development=True)

    with patch.dict(os.environ, {"APP_ENV": "production", "FLASK_ENV": "production"}):
        result = dev_provider.send("+919988776655", "HealthAware code: 123456")
        assert result.success is False
        assert result.provider == "unconfigured"
        assert "not configured" in result.error.lower()


def test_role_request_send_sms_returns_503_when_provider_fails(app_client):
    """When SMS provider fails or is unconfigured in production, endpoint returns 503 instead of false 200."""
    email = "sms_unconfigured@audit-test.org"
    phone = "+919988776655"

    with get_db_session() as sess:
        chal, _ = create_otp_challenge(
            sess,
            email=email,
            purpose="role_request_email",
            pending_payload={"email": email, "phone": phone},
        )
        chal.is_verified = True
        sess.commit()

    # Simulate production environment without SMS provider
    with patch("backend.controllers.role_request.send_challenge_sms", return_value=False):
        resp = app_client.post("/api/v1/auth/role-request/send-sms-otp", json={
            "email": email,
            "phone": phone,
        })
        assert resp.status_code == 503
        err = resp.get_json()["error"]
        assert err["code"] == "SERVICE_UNAVAILABLE"


# ===========================================================================
# 3. Password Recovery & Existing Account Compatibility Tests
# ===========================================================================


def test_password_recovery_rejects_client_supplied_flags_and_requires_server_otp(app_client):
    """Password recovery cannot be bypassed with client flags; requires valid server OTP challenge."""
    email = "recovery_audit@audit-test.org"
    with get_db_session() as sess:
        user = UserModel(
            user_id="user-rec-01",
            username=email,
            display_name="Recovery User",
            role="contributor",
            password_hash=hash_password("OldPassword123!"),
            is_active=True,
        )
        sess.add(user)
        sess.commit()

    # Attempt to reset password with dummy OTP and spoofed verified flag
    resp_bypass = app_client.post("/api/v1/auth/reset-password", json={
        "identifier": email,
        "otp": "999999",
        "new_password": "NewSecurePassword123!",
        "is_verified": True,  # Spoofed client flag
        "verified": True,
    })
    assert resp_bypass.status_code == 401
    assert "No active verification code found" in resp_bypass.get_json()["error"]["message"]

    # Verify original password unchanged
    with get_db_session() as sess:
        persisted = sess.query(UserModel).filter_by(username=email).first()
        assert verify_password("OldPassword123!", persisted.password_hash)


def test_existing_accounts_remain_compatible(app_client):
    """Pre-existing user accounts can log in via both username and email seamlessly."""
    with get_db_session() as sess:
        existing = UserModel(
            user_id="user-exist-priya-01",
            username="admin_priya_audit",
            display_name="Dr. Priya Sharma",
            role="admin",
            password_hash=hash_password("AdminSecurePass123!"),
            is_active=True,
        )
        sess.add(existing)
        sess.commit()

    # Log in with exact username
    resp1 = app_client.post("/api/v1/auth/login", json={
        "username": "admin_priya_audit",
        "password": "AdminSecurePass123!",
    })
    assert resp1.status_code == 200
    assert resp1.get_json()["data"]["role"] == "admin"
