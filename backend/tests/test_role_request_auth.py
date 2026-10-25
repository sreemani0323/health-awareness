"""Tests for role-request registration, email/SMS OTP verification, and admin approval lifecycle."""

from __future__ import annotations

import uuid
import pytest
from flask import Flask
from sqlalchemy import text

from backend.app import create_app
from backend.domain.domain_objects import User, UserRole
from backend.domain.staff_application_models import StaffRoleOption
from backend.domain.staff_application_service import get_staff_application_service
from backend.platform.otp_service import (
    create_otp_challenge,
    create_sms_otp_challenge,
    generate_numeric_otp,
    hash_otp,
    verify_otp_challenge,
    verify_sms_otp_challenge,
)
from backend.platform.security import hash_password
from backend.platform.sms_service import normalize_phone_number
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    get_test_database_url,
    init_db,
)
import backend.storage.db as db_mod
from backend.storage.postgres_models import (
    EmailOtpChallengeModel,
    SmsOtpChallengeModel,
    StaffApplicationModel,
    UserModel,
)


@pytest.fixture(scope="module")
def app():
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

    flask_app = create_app(
        test_config={
            "TESTING": True,
            "DATABASE_URL": test_url,
            "SECRET_KEY": "test-secret-key-32-chars-at-least!",
            "LEARNER_JWT_SECRET": "test-learner-jwt-secret-32-chars-long!",
            "RATELIMIT_ENABLED": False,
        }
    )

    yield flask_app

    db_mod._engine = orig_engine
    db_mod._SessionFactory = orig_factory


@pytest.fixture(autouse=True)
def clean_test_tables(app):
    """Clean test tables before and after each test."""
    with db_mod.get_db_session() as sess:
        sess.execute(text("DELETE FROM sms_otp_challenges;"))
        sess.execute(text("DELETE FROM email_otp_challenges;"))
        sess.execute(text("DELETE FROM staff_application_history;"))
        sess.execute(text("DELETE FROM staff_applications WHERE applicant_email LIKE '%@example.com';"))
        sess.execute(text("DELETE FROM users WHERE username LIKE 'staff_%' OR username LIKE '%@example.com';"))
        sess.commit()
    yield
    with db_mod.get_db_session() as sess:
        sess.execute(text("DELETE FROM sms_otp_challenges;"))
        sess.execute(text("DELETE FROM email_otp_challenges;"))
        sess.execute(text("DELETE FROM staff_application_history;"))
        sess.execute(text("DELETE FROM staff_applications WHERE applicant_email LIKE '%@example.com';"))
        sess.execute(text("DELETE FROM users WHERE username LIKE 'staff_%' OR username LIKE '%@example.com';"))
        sess.commit()


@pytest.fixture
def client(app: Flask):
    return app.test_client()


def test_phone_number_normalization():
    """Verify E.164 phone normalization across formats."""
    # Standard 10-digit Indian number defaults to +91
    ok, norm, err = normalize_phone_number("9876543210")
    assert ok is True
    assert norm == "+919876543210"

    # Number with spaces and dashes
    ok, norm, err = normalize_phone_number("+91 98765-43210")
    assert ok is True
    assert norm == "+919876543210"

    # US number with +1
    ok, norm, err = normalize_phone_number("+1 202 555 0123")
    assert ok is True
    assert norm == "+12025550123"

    # Invalid string
    ok, norm, err = normalize_phone_number("invalid-phone")
    assert ok is False


def test_sms_otp_crypto_and_verification():
    """Verify SMS OTP challenge lifecycle and attempt throttling."""
    phone = "+919876543210"
    with db_mod.get_db_session() as sess:
        chal, raw_otp = create_sms_otp_challenge(sess, phone, "role_request_sms")
        sess.commit()

        assert len(raw_otp) == 6
        assert chal.phone_number == phone
        assert chal.is_verified is False

    # Bad code attempt
    with db_mod.get_db_session() as sess:
        ok, err, _ = verify_sms_otp_challenge(sess, phone, "role_request_sms", "000000")
        assert ok is False
        assert "attempt(s) remaining" in err

    # Correct code
    with db_mod.get_db_session() as sess:
        ok, err, verified_chal = verify_sms_otp_challenge(sess, phone, "role_request_sms", raw_otp)
        assert ok is True
        assert verified_chal.is_verified is True


def test_complete_non_learner_role_request_flow(client):
    """End-to-end test of non-learner registration:

    1. Initiate: submit details -> Email OTP dispatched
    2. Verify Email: valid OTP confirms email
    3. Send SMS: request SMS OTP to normalized phone
    4. Complete: submit SMS OTP + chosen password -> creates pending application
    5. Privilege check: applicant CANNOT log in or access privileged APIs while pending
    6. Admin review: Administrator approves application -> user active with approved role
    7. Post-approval access: user can now log in with their chosen password and access role!
    """
    test_email = f"reviewer_{uuid.uuid4().hex[:8]}@example.com"
    test_phone = "+919876543210"
    chosen_password = "DrReviewerPassword2026!"

    # --- Step 1: Initiate role request ---
    initiate_payload = {
        "name": "Dr. Anita Desai",
        "email": test_email,
        "phone": test_phone,
        "role": "reviewer",
        "statement_of_purpose": "I am a registered public health epidemiologist with 10 years of clinical experience in maternal health.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
        "professional_title": "Senior Epidemiologist",
    }

    resp1 = client.post("/api/v1/auth/role-request/initiate", json=initiate_payload)
    assert resp1.status_code == 200, resp1.get_json()
    assert resp1.get_json()["data"]["status"] == "email_challenge_sent"

    # Extract email OTP from DB (simulating delivery to applicant's email inbox)
    with db_mod.get_db_session() as sess:
        email_chal = (
            sess.query(EmailOtpChallengeModel)
            .filter_by(email=test_email, purpose="role_request_email")
            .first()
        )
        assert email_chal is not None
        raw_email_otp = "123456"
        email_chal.otp_hash = hash_otp(raw_email_otp)
        sess.commit()

    # --- Step 2: Verify Email OTP ---
    resp2 = client.post("/api/v1/auth/role-request/verify-email", json={
        "email": test_email,
        "otp": "123456",
    })
    assert resp2.status_code == 200, resp2.get_json()
    assert resp2.get_json()["data"]["email_verified"] is True

    # --- Step 3: Request SMS OTP ---
    resp3 = client.post("/api/v1/auth/role-request/send-sms-otp", json={
        "email": test_email,
        "phone": test_phone,
    })
    assert resp3.status_code == 200, resp3.get_json()
    assert resp3.get_json()["data"]["sms_challenge_sent"] is True

    # Set known SMS OTP in DB for test
    with db_mod.get_db_session() as sess:
        sms_chal = (
            sess.query(SmsOtpChallengeModel)
            .filter_by(phone_number=test_phone, purpose="role_request_sms")
            .first()
        )
        assert sms_chal is not None
        raw_sms_otp = "654321"
        sms_chal.otp_hash = hash_otp(raw_sms_otp)
        sess.commit()

    # --- Step 4: Complete role request with password ---
    resp4 = client.post("/api/v1/auth/role-request/complete", json={
        "email": test_email,
        "phone": test_phone,
        "sms_otp": "654321",
        "password": chosen_password,
    })
    assert resp4.status_code == 200, resp4.get_json()
    res_data = resp4.get_json()["data"]
    assert res_data["status"] == "pending_review"
    assert res_data["requested_role"] == "reviewer"
    ref_id = res_data["reference_id"]
    assert ref_id.startswith("APP-")

    # --- Step 5: PRIVILEGE CHECK: Applicant CANNOT log in before admin approval ---
    # Attempt login with email:
    login_resp = client.post("/api/v1/auth/login", json={
        "username": test_email,
        "password": chosen_password,
    })
    # Must be 403 Forbidden with pending explanation, NOT active session
    assert login_resp.status_code == 403
    assert "under review" in login_resp.get_json()["error"]["message"]

    # Attempt to access privileged reviewer route without approved session:
    rev_resp = client.get("/api/v1/creator/reviews")
    assert rev_resp.status_code == 401

    # --- Step 6: Administrator reviews and approves application ---
    admin_user = User(
        user_id="user-admin-test-01",
        username="admin_super",
        display_name="Super Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    svc = get_staff_application_service()
    approval_result = svc.approve_application(
        identifier=ref_id,
        admin_user=admin_user,
        approved_role="reviewer",
        rationale="Credentials verified with Medical Council of India registry.",
    )
    assert approval_result["status"] == "approved"
    assert approval_result["approved_role"] == "reviewer"

    # --- Step 7: POST-APPROVAL ACCESS: User can now log in and access Review Queue ---
    approved_login_resp = client.post("/api/v1/auth/login", json={
        "username": test_email,
        "password": chosen_password,
    })
    assert approved_login_resp.status_code == 200
    user_payload = approved_login_resp.get_json()["data"]
    assert user_payload["role"] == "reviewer"

    # Reviewer session is authenticated and authorized
    auth_me_resp = client.get("/api/v1/auth/me")
    assert auth_me_resp.status_code == 200
    assert auth_me_resp.get_json()["data"]["role"] == "reviewer"


def test_staff_forgot_and_reset_password_flow(client):
    """Verify staff password recovery:

    1. POST /api/v1/auth/recover returns generic message (prevents user enumeration)
    2. OTP challenge created and dispatched via email
    3. POST /api/v1/auth/reset-password verifies code and updates password hash
    4. Old password rejected; new password logs in successfully
    """
    staff_username = f"staff_{uuid.uuid4().hex[:6]}"
    staff_email = f"{staff_username}@example.com"
    old_pw = "OldPassword123!"
    new_pw = "BrandNewPassword2026!"

    with db_mod.get_db_session() as sess:
        u = UserModel(
            user_id=f"u-{uuid.uuid4().hex[:8]}",
            username=staff_username,
            display_name="Staff Contributor",
            role="contributor",
            password_hash=hash_password(old_pw),
            is_active=True,
        )
        sess.add(u)
        sess.flush()

        # Link application for email resolution
        app = StaffApplicationModel(
            application_id=f"app-{uuid.uuid4().hex[:8]}",
            reference_id=f"HA-STF-{uuid.uuid4().hex[:6].upper()}",
            tracking_token_hash="dummy",
            applicant_name="Staff Contributor",
            applicant_email=staff_email,
            requested_role="contributor",
            statement_of_purpose="Background in public health communications.",
            status="approved",
            provisioned_user_id=u.user_id,
        )
        sess.add(app)
        sess.commit()

    # Step 1: Request recovery
    rec_resp = client.post("/api/v1/auth/recover", json={"identifier": staff_username})
    assert rec_resp.status_code == 200
    assert "verification code has been dispatched" in rec_resp.get_json()["data"]["message"]

    # Set known OTP in DB
    with db_mod.get_db_session() as sess:
        chal = sess.query(EmailOtpChallengeModel).filter_by(email=staff_email, purpose="staff_reset_password").first()
        assert chal is not None
        chal.otp_hash = hash_otp("998877")
        sess.commit()

    # Step 2: Reset password
    reset_resp = client.post("/api/v1/auth/reset-password", json={
        "identifier": staff_username,
        "otp": "998877",
        "new_password": new_pw,
    })
    assert reset_resp.status_code == 200
    assert reset_resp.get_json()["data"]["success"] is True

    # Step 3: Verify old password fails
    old_login = client.post("/api/v1/auth/login", json={"username": staff_username, "password": old_pw})
    assert old_login.status_code == 401

    # Step 4: Verify new password succeeds
    new_login = client.post("/api/v1/auth/login", json={"username": staff_username, "password": new_pw})
    assert new_login.status_code == 200
    assert new_login.get_json()["data"]["username"] == staff_username
