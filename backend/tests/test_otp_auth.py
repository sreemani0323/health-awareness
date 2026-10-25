"""Tests for email OTP registration verification and password reset flows."""

from __future__ import annotations

import json
import uuid
import pytest
from flask import Flask

from backend.app import create_app
from backend.domain.domain_objects import UserRole
from backend.platform.otp_service import generate_numeric_otp, hash_otp, verify_otp_hash
from backend.platform.security import hash_password, verify_password
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    get_test_database_url,
    init_db,
)
from backend.storage.postgres_models import EmailOtpChallengeModel, UserModel


from sqlalchemy import text
import backend.storage.db as db_mod


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
def clean_otp_db(app):
    """Clean test tables before each test."""
    with db_mod.get_db_session() as sess:
        sess.execute(text("DELETE FROM email_otp_challenges;"))
        sess.execute(text("DELETE FROM users WHERE username LIKE '%@example.com';"))
        sess.commit()
    yield
    with db_mod.get_db_session() as sess:
        sess.execute(text("DELETE FROM email_otp_challenges;"))
        sess.execute(text("DELETE FROM users WHERE username LIKE '%@example.com';"))
        sess.commit()


@pytest.fixture
def client(app: Flask):
    return app.test_client()


def test_otp_crypto_primitives():
    """Verify CSPRNG 6-digit numeric OTP generation and constant-time hashing."""
    otp = generate_numeric_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()

    otp_hash = hash_otp(otp)
    assert len(otp_hash) == 64  # SHA-256 hex digest
    assert verify_otp_hash(otp, otp_hash) is True
    assert verify_otp_hash("000000", otp_hash) is False


def test_first_time_signup_otp_challenge_and_verification(client):
    """Test 2-step registration: request OTP -> verify 6-digit OTP -> account created with JWT."""
    test_email = f"learner_{uuid.uuid4().hex[:8]}@example.com"
    signup_payload = {
        "name": "Priya Sharma",
        "email": test_email,
        "password": "SecurePassword123!",
    }

    # Step 1: Submit registration details
    resp1 = client.post("/api/v1/learner/auth/register", json=signup_payload)
    assert resp1.status_code == 200
    data1 = resp1.get_json()["data"]
    assert data1["requires_otp"] is True
    assert "dev_otp" in data1
    otp = data1["dev_otp"]
    assert len(otp) == 6

    # Verify user does NOT exist in DB yet
    with get_db_session() as db_sess:
        user = db_sess.query(UserModel).filter(UserModel.username == test_email).first()
        assert user is None

        # Verify challenge exists in DB
        challenge = (
            db_sess.query(EmailOtpChallengeModel)
            .filter(EmailOtpChallengeModel.email == test_email, EmailOtpChallengeModel.purpose == "signup")
            .first()
        )
        assert challenge is not None
        assert challenge.is_verified is False
        assert challenge.otp_hash == hash_otp(otp)

    # Step 2: Attempt verification with incorrect OTP
    bad_resp = client.post(
        "/api/v1/learner/auth/verify-signup",
        json={"email": test_email, "otp": "999999"},
    )
    assert bad_resp.status_code == 400
    assert "Incorrect verification code" in bad_resp.get_json()["error"]["message"]

    # Step 3: Verify with correct OTP
    good_resp = client.post(
        "/api/v1/learner/auth/verify-signup",
        json={"email": test_email, "otp": otp},
    )
    assert good_resp.status_code == 201
    good_data = good_resp.get_json()["data"]
    assert "token" in good_data
    assert good_data["user"]["email"] == test_email
    assert good_data["user"]["name"] == "Priya Sharma"

    # Verify user now exists in DB with role learner
    with get_db_session() as db_sess:
        user = db_sess.query(UserModel).filter(UserModel.username == test_email).first()
        assert user is not None
        assert user.role == UserRole.LEARNER.value
        assert verify_password("SecurePassword123!", user.password_hash) is True

    # Step 4: Login with newly created credentials
    login_resp = client.post(
        "/api/v1/learner/auth/login",
        json={"email": test_email, "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    assert "token" in login_resp.get_json()["data"]


def test_signup_rejects_duplicate_email(client):
    """Submitting registration for an existing account returns 409 Conflict."""
    test_email = f"existing_{uuid.uuid4().hex[:8]}@example.com"
    with get_db_session() as db_sess:
        user = UserModel(
            user_id=f"usr_{uuid.uuid4().hex[:16]}",
            username=test_email,
            display_name="Existing User",
            role=UserRole.LEARNER.value,
            password_hash=hash_password("ExistingPassword123!"),
            is_active=True,
        )
        db_sess.add(user)
        db_sess.commit()

    resp = client.post(
        "/api/v1/learner/auth/register",
        json={"name": "Duplicate User", "email": test_email, "password": "NewPassword123!"},
    )
    assert resp.status_code == 409
    assert "already exists" in resp.get_json()["error"]["message"]


def test_forgot_password_and_reset_flow(client):
    """Test forgot-password OTP challenge and subsequent password reset."""
    test_email = f"reset_{uuid.uuid4().hex[:8]}@example.com"
    with get_db_session() as db_sess:
        user = UserModel(
            user_id=f"usr_{uuid.uuid4().hex[:16]}",
            username=test_email,
            display_name="Reset Learner",
            role=UserRole.LEARNER.value,
            password_hash=hash_password("OldPassword123!"),
            is_active=True,
        )
        db_sess.add(user)
        db_sess.commit()

    # Step 1: Request recovery OTP
    rec_resp = client.post("/api/v1/learner/auth/recover", json={"email": test_email})
    assert rec_resp.status_code == 200
    rec_data = rec_resp.get_json()["data"]
    assert rec_data["requires_otp"] is True
    assert "dev_otp" in rec_data
    reset_otp = rec_data["dev_otp"]

    # Step 2: Attempt reset with wrong OTP
    bad_reset = client.post(
        "/api/v1/learner/auth/reset-password",
        json={
            "email": test_email,
            "otp": "000000",
            "new_password": "NewSecurePassword456!",
        },
    )
    assert bad_reset.status_code == 400
    assert "Incorrect verification code" in bad_reset.get_json()["error"]["message"]

    # Old password still works
    old_login = client.post(
        "/api/v1/learner/auth/login",
        json={"email": test_email, "password": "OldPassword123!"},
    )
    assert old_login.status_code == 200

    # Step 3: Complete reset with valid OTP
    good_reset = client.post(
        "/api/v1/learner/auth/reset-password",
        json={
            "email": test_email,
            "otp": reset_otp,
            "new_password": "NewSecurePassword456!",
        },
    )
    assert good_reset.status_code == 200
    assert "successfully" in good_reset.get_json()["data"]["message"]

    # Step 4: Login with old password fails
    failed_login = client.post(
        "/api/v1/learner/auth/login",
        json={"email": test_email, "password": "OldPassword123!"},
    )
    assert failed_login.status_code == 401

    # Step 5: Login with new password succeeds
    success_login = client.post(
        "/api/v1/learner/auth/login",
        json={"email": test_email, "password": "NewSecurePassword456!"},
    )
    assert success_login.status_code == 200
    assert "token" in success_login.get_json()["data"]


def test_forgot_password_generic_response_for_nonexistent_email(client):
    """Requesting recovery for unknown email returns generic success message without leaking existence."""
    resp = client.post(
        "/api/v1/learner/auth/recover",
        json={"email": "nonexistent_email_123456@example.com"},
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "If an account exists" in data["message"]
    # No dev_otp should be generated for nonexistent account
    assert "dev_otp" not in data
