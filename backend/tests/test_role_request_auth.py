"""Tests for role-request registration, email OTP verification, and admin approval lifecycle."""

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
    generate_numeric_otp,
    hash_otp,
    verify_otp_challenge,
)
from backend.platform.security import hash_password
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    get_test_database_url,
    init_db,
)
import backend.storage.db as db_mod
from backend.storage.postgres_models import (
    EmailOtpChallengeModel,
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
        sess.execute(text("DELETE FROM email_otp_challenges;"))
        sess.execute(text("DELETE FROM staff_application_history;"))
        sess.execute(text("DELETE FROM staff_applications WHERE applicant_email LIKE '%@example.com';"))
        sess.execute(text("DELETE FROM users WHERE username LIKE 'staff_%' OR username LIKE '%@example.com';"))
        sess.commit()
    yield
    with db_mod.get_db_session() as sess:
        sess.execute(text("DELETE FROM email_otp_challenges;"))
        sess.execute(text("DELETE FROM staff_application_history;"))
        sess.execute(text("DELETE FROM staff_applications WHERE applicant_email LIKE '%@example.com';"))
        sess.execute(text("DELETE FROM users WHERE username LIKE 'staff_%' OR username LIKE '%@example.com';"))
        sess.commit()


@pytest.fixture
def client(app: Flask):
    return app.test_client()


def test_email_otp_crypto_and_verification():
    """Verify Email OTP challenge lifecycle and attempt throttling."""
    email = "crypto_test@example.com"
    with db_mod.get_db_session() as sess:
        chal, raw_otp = create_otp_challenge(sess, email, "role_request_email")
        sess.commit()

        assert len(raw_otp) == 6
        assert chal.email == email
        assert chal.is_verified is False

    # Bad code attempt
    with db_mod.get_db_session() as sess:
        ok, err, _ = verify_otp_challenge(sess, email, "role_request_email", "000000")
        assert ok is False
        assert "attempt(s) remaining" in err

    # Correct code
    with db_mod.get_db_session() as sess:
        ok, err, verified_chal = verify_otp_challenge(sess, email, "role_request_email", raw_otp)
        assert ok is True
        assert verified_chal.is_verified is True


def test_complete_non_learner_role_request_flow(client):
    """End-to-end test of non-learner registration with pure email verification:

    1. Initiate: submit details -> Email OTP dispatched
    2. Verify Email: valid OTP confirms email
    3. Complete: submit chosen password -> creates pending application
    4. Privilege check: applicant CANNOT log in or access privileged APIs while pending
    5. Admin review: Administrator approves application -> user active with approved role
    6. Post-approval access: user can now log in with their chosen password and access role!
    """
    test_email = f"reviewer_{uuid.uuid4().hex[:8]}@example.com"
    chosen_password = "DrReviewerPassword2026!"

    # --- Step 1: Initiate role request ---
    initiate_payload = {
        "name": "Dr. Anita Desai",
        "email": test_email,
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

    # --- Step 3: Complete role request with password ---
    resp3 = client.post("/api/v1/auth/role-request/complete", json={
        "email": test_email,
        "password": chosen_password,
    })
    assert resp3.status_code == 200, resp3.get_json()
    res_data = resp3.get_json()["data"]
    assert res_data["status"] == "pending_review"
    assert res_data["requested_role"] == "reviewer"
    ref_id = res_data["reference_id"]
    assert ref_id.startswith("APP-")

    # --- Step 4: PRIVILEGE CHECK: Applicant CANNOT log in before admin approval ---
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

    # --- Step 5: Administrator reviews and approves application ---
    service = get_staff_application_service()
    admin_user = User(
        user_id="test-admin-uuid-001",
        username="admin_tester",
        display_name="Admin Reviewer",
        role=UserRole.ADMIN,
        is_active=True,
    )
    approval_result = service.approve_application(
        identifier=ref_id,
        admin_user=admin_user,
        approved_role="reviewer",
        rationale="Credentials verified with Medical Council of India registry.",
    )
    assert approval_result["status"] == "approved"

    # --- Step 6: Post-Approval Access Verification ---
    # The newly approved user can now successfully log in with their pre-provisioned password!
    login_approved = client.post("/api/v1/auth/login", json={
        "username": test_email,
        "password": chosen_password,
    })
    assert login_approved.status_code == 200, login_approved.get_json()
    auth_data = login_approved.get_json()["data"]
    assert auth_data["role"] == "reviewer"
    assert "user_id" in auth_data or "username" in auth_data


def test_rejected_applicant_cannot_log_in(client):
    """Verify that a rejected role-request application never creates an active privileged account."""
    test_email = f"rejected_{uuid.uuid4().hex[:8]}@example.com"
    chosen_password = "DrRejectedPass2026!"

    # 1. Initiate
    resp1 = client.post("/api/v1/auth/role-request/initiate", json={
        "name": "Applicant Rejection Test",
        "email": test_email,
        "role": "contributor",
        "statement_of_purpose": "Testing admin rejection pathway to confirm access is cleanly denied.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    })
    assert resp1.status_code == 200

    # 2. Complete directly with email_otp
    with db_mod.get_db_session() as sess:
        email_chal = sess.query(EmailOtpChallengeModel).filter_by(email=test_email).first()
        raw_email_otp = "888888"
        email_chal.otp_hash = hash_otp(raw_email_otp)
        sess.commit()

    resp2 = client.post("/api/v1/auth/role-request/complete", json={
        "email": test_email,
        "email_otp": "888888",
        "password": chosen_password,
    })
    assert resp2.status_code == 200
    ref_id = resp2.get_json()["data"]["reference_id"]

    # 3. Admin rejects application
    service = get_staff_application_service()
    admin_user = User(
        user_id="test-admin-uuid-002",
        username="admin_rejecter",
        display_name="Admin Rejecter",
        role=UserRole.ADMIN,
        is_active=True,
    )
    rejection_result = service.reject_application(
        identifier=ref_id,
        admin_user=admin_user,
        reason="Insufficient clinical qualifications.",
    )
    assert rejection_result["status"] == "rejected"

    # 4. Login attempt MUST fail with 403 Forbidden explaining rejection
    login_attempt = client.post("/api/v1/auth/login", json={
        "username": test_email,
        "password": chosen_password,
    })
    assert login_attempt.status_code == 403
    err_msg = login_attempt.get_json()["error"]["message"].lower()
    assert "declined" in err_msg or "rejected" in err_msg
