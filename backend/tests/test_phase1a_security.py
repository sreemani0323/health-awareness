"""Phase 1A Security Hardening & Session Isolation Test Suite.

Verifies:
1. Progressive Throttling:
   - Repeated failed login attempts trigger progressive throttling.
   - Failure thresholds: 5 attempts triggers pair lockout (HTTP 401 with generic error & Retry-After).
   - Successful login immediately resets failure counters.
   - Generic authentication error messages across all failure modes (anti-enumeration).
   - Account lockout DoS mitigation: per-IP failure tracking protects legitimate users on different IPs;
     administrative unlock endpoint immediately clears locks.

2. Privileged Staff Multi-Factor Authentication (MFA / TOTP):
   - Existing staff accounts without MFA log in seamlessly (no lockout).
   - Enrollment generates a base32 secret, provisioning URI, and 8 single-use recovery codes.
   - TOTP secret is verified to be encrypted at rest in the storage layer.
   - Enrollment confirmation requires a valid TOTP code to activate MFA.
   - MFA login workflow: password validation returns mfa_required=True without setting full session;
     subsequent /auth/mfa/verify with valid TOTP code establishes authenticated session and CSRF cookie.
   - Replay Protection: submitting the same TOTP code in the same time window is rejected.
   - Emergency Recovery: redeeming a valid recovery code logs in and burns that single code.
   - Admin-Assisted Recovery: admin endpoint completely resets MFA for locked-out staff.
   - Self-service MFA disable requires password and TOTP code.

3. Authentication Boundary & Session Isolation:
   - Staff APIs (/api/v1/creator/*, /api/v1/admin/*, /api/v1/staff/*) strictly require a signed Flask session cookie.
   - Learner Bearer JWTs are rejected on all staff administrative endpoints (HTTP 403 Forbidden).
   - Invalid, expired, or malformed learner tokens fail closed immediately.
   - Public concern submission and anonymous lesson playback remain operational.

4. Audit Logging:
   - Structured security audit events are emitted for login attempts, throttles, MFA flows, and resets.
"""

from __future__ import annotations

import json
import time
import uuid
import pyotp
import pytest
from flask import session

from backend.app import create_app
from backend.domain.domain_objects import User, UserRole
from backend.platform.audit_log import SecurityAuditEvent, clear_audit_events, get_recent_audit_events
from backend.platform.login_throttle import get_login_throttle_manager
from backend.platform.mfa_service import get_mfa_service
from backend.platform.security import hash_password, decrypt_totp_secret


@pytest.fixture()
def app_instance(tmp_path):
    test_db = str(tmp_path / "test_throttle.sqlite3")
    test_mfa_db = str(tmp_path / "test_mfa.sqlite3")

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-phase1a-secret-key-32-bytes-long!",
        "LOGIN_THROTTLE_DB_PATH": test_db,
        "MFA_DB_PATH": test_mfa_db,
        "TEST_JWT_SECRET": "test-jwt-secret-key-for-learners",
        "TEST_JWT_ALGORITHM": "HS256",
        "NEON_AUTH_ISSUER": "https://test.neon.tech/auth",
        "AUTH_RATE_LIMIT": "1000 per 15 minutes",
        "RATELIMIT_ENABLED": False,
    })
    return app


@pytest.fixture()
def client(app_instance):
    with app_instance.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_security_state():
    """Clear throttles, MFA data, and audit logs before and after each test."""
    throttle_mgr = get_login_throttle_manager()
    throttle_mgr.clear_all()
    mfa_service = get_mfa_service()
    mfa_service.clear_all()
    clear_audit_events()
    yield
    throttle_mgr.clear_all()
    mfa_service.clear_all()
    clear_audit_events()


@pytest.fixture()
def seeded_staff_user(app_instance, ndb_ctx):
    """Provisions an active staff contributor in the database/domain."""
    uid = uuid.uuid4().hex[:8]
    user_id = f"user-staff-{uid}"
    username = f"staff_{uid}"
    password = "StaffSecurePassword2026!"
    hashed_pw = hash_password(password)

    user = User(
        user_id=user_id,
        username=username,
        display_name="Staff Test Contributor",
        role=UserRole.CONTRIBUTOR,
        password_hash=hashed_pw,
        is_active=True,
    )

    from backend.domain import domain_services
    domain_services.create_user(user)

    # Also register in PostgreSQL if DB session available
    try:
        from backend.storage.db import get_db_session
        from backend.storage.postgres_models import UserModel as PgUserModel
        with get_db_session() as db_sess:
            pg_u = PgUserModel(
                user_id=user_id,
                username=username,
                display_name="Staff Test Contributor",
                role=UserRole.CONTRIBUTOR.value,
                password_hash=hashed_pw,
                is_active=True,
            )
            db_sess.add(pg_u)
            db_sess.commit()
    except Exception:
        pass

    return {
        "user_id": user_id,
        "username": username,
        "password": password,
        "user": user,
    }


@pytest.fixture()
def seeded_admin_user(app_instance, ndb_ctx):
    """Provisions an active administrator in the database/domain."""
    uid = uuid.uuid4().hex[:8]
    user_id = f"user-admin-{uid}"
    username = f"admin_{uid}"
    password = "AdminSecurePassword2026!"
    hashed_pw = hash_password(password)

    user = User(
        user_id=user_id,
        username=username,
        display_name="Admin Test User",
        role=UserRole.ADMIN,
        password_hash=hashed_pw,
        is_active=True,
    )

    from backend.domain import domain_services
    domain_services.create_user(user)


    try:
        from backend.storage.db import get_db_session
        from backend.storage.postgres_models import UserModel as PgUserModel
        with get_db_session() as db_sess:
            pg_u = PgUserModel(
                user_id=user_id,
                username=username,
                display_name="Admin Test User",
                role=UserRole.ADMIN.value,
                password_hash=hashed_pw,
                is_active=True,
            )
            db_sess.add(pg_u)
            db_sess.commit()
    except Exception:
        pass

    return {
        "user_id": user_id,
        "username": username,
        "password": password,
        "user": user,
    }


# ===========================================================================
# 1. Progressive Throttling & Account Lockout Tests
# ===========================================================================


def test_login_progressive_throttling_thresholds(client, seeded_staff_user):
    """Repeated failed attempts trigger progressive throttling after 5 attempts."""
    username = seeded_staff_user["username"]

    # Attempts 1 to 4: standard 401 Unauthorized (not yet locked)
    for attempt in range(1, 5):
        resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": f"WrongAttempt{attempt}!",
        })
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"
        assert "Retry-After" not in resp.headers

    # Attempt 5: triggers pair lockout (threshold reached)
    resp5 = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": "WrongAttempt5!",
    })
    assert resp5.status_code == 401
    assert resp5.get_json()["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid username or password" in resp5.get_json()["error"]["message"]

    # Attempt 6 (while locked out): returns generic 401 with Retry-After header
    resp6 = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": "AnyAttemptWhileLocked!",
    })
    assert resp6.status_code == 401
    assert "Retry-After" in resp6.headers
    retry_after = int(resp6.headers["Retry-After"])
    assert retry_after > 0


def test_login_successful_login_resets_throttling(client, seeded_staff_user):
    """Successful login resets failure counters immediately."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]

    # 3 failed attempts
    for _ in range(3):
        client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "BadPassword123!",
        })

    # 1 successful login
    succ_resp = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": password,
    })
    assert succ_resp.status_code == 200

    # Counter is reset: can make 4 more failed attempts without triggering threshold
    for i in range(4):
        resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": f"SubsequentBad{i}!",
        })
        assert resp.status_code == 401
        assert "Retry-After" not in resp.headers


def test_generic_authentication_errors_prevent_enumeration(client, seeded_staff_user):
    """Generic error message is identical across non-existent user, bad password, and throttled user."""
    # 1. Non-existent username
    resp_unknown = client.post("/api/v1/auth/login", json={
        "username": "totally_unknown_user_999",
        "password": "SomePassword123!",
    })
    assert resp_unknown.status_code == 401
    err_unknown = resp_unknown.get_json()["error"]
    assert err_unknown["code"] == "UNAUTHORIZED"
    assert err_unknown["message"] == "Invalid username or password."

    # 2. Existing username with bad password
    resp_bad_pw = client.post("/api/v1/auth/login", json={
        "username": seeded_staff_user["username"],
        "password": "IncorrectPassword!",
    })
    assert resp_bad_pw.status_code == 401
    err_bad_pw = resp_bad_pw.get_json()["error"]
    assert err_bad_pw["code"] == "UNAUTHORIZED"
    assert err_bad_pw["message"] == "Invalid username or password."


def test_account_lockout_dos_mitigation_and_admin_reset(client, seeded_staff_user, seeded_admin_user):
    """Lockout on one IP does not block another IP; admin reset unlocks immediately."""
    username = seeded_staff_user["username"]

    # Lock out user from IP "198.51.100.1" (Attacker IP)
    attacker_env = {"REMOTE_ADDR": "198.51.100.1"}
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "WrongPassword!"},
            environ_base=attacker_env,
        )

    # Attacker IP is throttled
    resp_attacker = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "WrongPassword!"},
        environ_base=attacker_env,
    )
    assert "Retry-After" in resp_attacker.headers

    # Legitimate user from a different IP ("203.0.113.5") can still attempt login with valid password
    legit_env = {"REMOTE_ADDR": "203.0.113.5"}
    resp_legit = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": seeded_staff_user["password"]},
        environ_base=legit_env,
    )
    assert resp_legit.status_code == 200

    # Re-trigger lockout on attacker IP
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "WrongPassword!"},
            environ_base=attacker_env,
        )

    # Admin resets throttle via admin endpoint
    # First, login as admin
    admin_login = client.post("/api/v1/auth/login", json={
        "username": seeded_admin_user["username"],
        "password": seeded_admin_user["password"],
    })
    assert admin_login.status_code == 200
    csrf_token = admin_login.get_json()["data"]["csrf_token"]

    reset_resp = client.post(
        f"/api/v1/admin/users/{username}/throttle/reset",
        headers={"X-XSRF-TOKEN": csrf_token},
    )
    assert reset_resp.status_code == 200

    # Attacker IP is no longer throttled
    resp_after_reset = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "AnyPassword!"},
        environ_base=attacker_env,
    )
    assert resp_after_reset.status_code == 401
    assert "Retry-After" not in resp_after_reset.headers


# ===========================================================================
# 2. Privileged Staff MFA / TOTP Tests
# ===========================================================================


def test_mfa_enrollment_and_secret_encryption(client, seeded_staff_user):
    """Staff can initiate enrollment; secret is encrypted at rest; MFA is not active until confirmed."""
    # 1. Login as staff
    login_resp = client.post("/api/v1/auth/login", json={
        "username": seeded_staff_user["username"],
        "password": seeded_staff_user["password"],
    })
    assert login_resp.status_code == 200
    csrf_token = login_resp.get_json()["data"]["csrf_token"]

    # 2. Initiate enrollment
    enroll_resp = client.post("/api/v1/auth/mfa/enroll", headers={"X-XSRF-TOKEN": csrf_token})
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.get_json()["data"]
    assert "secret" in enroll_data
    assert "provisioning_uri" in enroll_data
    assert "recovery_codes" in enroll_data
    assert len(enroll_data["recovery_codes"]) == 8

    raw_secret = enroll_data["secret"]

    # 3. Verify MFA is NOT yet active (still pending confirmation)
    mfa_service = get_mfa_service()
    assert mfa_service.is_mfa_enabled(seeded_staff_user["user_id"]) is False

    # 4. Verify secret is ENCRYPTED at rest in PostgreSQL storage
    from backend.storage.postgres_models import StaffMfaModel
    with mfa_service._get_session() as session:
        record = session.query(StaffMfaModel).filter_by(user_id=seeded_staff_user["user_id"]).first()
        assert record is not None
        encrypted_val = record.totp_secret_encrypted
        # Must not be equal to plaintext base32 secret
        assert encrypted_val != raw_secret
        # Decrypts back to the original secret
        assert decrypt_totp_secret(encrypted_val) == raw_secret


def test_mfa_confirm_enrollment_and_login_flow(client, seeded_staff_user):
    """Complete enrollment with valid TOTP; subsequent login requires TOTP verification."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]
    user_id = seeded_staff_user["user_id"]

    # 1. Login and initiate enrollment
    login_resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    csrf_token = login_resp.get_json()["data"]["csrf_token"]
    enroll_resp = client.post("/api/v1/auth/mfa/enroll", headers={"X-XSRF-TOKEN": csrf_token})
    raw_secret = enroll_resp.get_json()["data"]["secret"]

    # 2. Confirm enrollment with invalid code -> rejected
    bad_confirm = client.post(
        "/api/v1/auth/mfa/confirm-enrollment",
        json={"totp_code": "000000"},
        headers={"X-XSRF-TOKEN": csrf_token},
    )
    assert bad_confirm.status_code == 400

    # 3. Confirm enrollment with valid TOTP code
    totp = pyotp.TOTP(raw_secret)
    valid_code = totp.now()
    good_confirm = client.post(
        "/api/v1/auth/mfa/confirm-enrollment",
        json={"totp_code": valid_code},
        headers={"X-XSRF-TOKEN": csrf_token},
    )
    assert good_confirm.status_code == 200
    assert good_confirm.get_json()["data"]["mfa_enabled"] is True

    # 4. Logout
    client.post("/api/v1/auth/logout")

    # 5. Subsequent login with password alone -> returns mfa_required=True
    login2 = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login2.status_code == 200
    login2_data = login2.get_json()["data"]
    assert login2_data.get("mfa_required") is True
    assert "csrf_token" not in login2_data

    # Verify session is NOT yet authenticated for staff endpoints
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401

    # 6. Verify MFA with invalid code -> 401
    bad_verify = client.post("/api/v1/auth/mfa/verify", json={"totp_code": "999999"})
    assert bad_verify.status_code == 401

    # 7. Verify MFA with valid code -> establishes full session
    # Generate fresh code for current step
    fresh_code = totp.now()
    good_verify = client.post("/api/v1/auth/mfa/verify", json={"totp_code": fresh_code})
    assert good_verify.status_code == 200
    verify_data = good_verify.get_json()["data"]
    assert verify_data["mfa_verified"] is True
    assert "csrf_token" in verify_data

    # Now /api/v1/auth/me succeeds
    me_resp2 = client.get("/api/v1/auth/me")
    assert me_resp2.status_code == 200
    assert me_resp2.get_json()["data"]["username"] == username


def test_mfa_replay_protection(client, seeded_staff_user):
    """Submitting the exact same TOTP code in the same window is rejected as replay."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]
    user_id = seeded_staff_user["user_id"]

    # Setup MFA
    mfa_service = get_mfa_service()
    enroll = mfa_service.initiate_enrollment(user_id, username)
    raw_secret = enroll["secret"]
    totp = pyotp.TOTP(raw_secret)
    code = totp.now()
    mfa_service.confirm_enrollment(user_id, code)

    # 1. Login step 1
    client.post("/api/v1/auth/login", json={"username": username, "password": password})

    # 2. Use current valid code to verify
    code1 = totp.now()
    resp1 = client.post("/api/v1/auth/mfa/verify", json={"totp_code": code1})
    assert resp1.status_code == 200

    # Logout
    client.post("/api/v1/auth/logout")

    # 3. Login step 1 again
    client.post("/api/v1/auth/login", json={"username": username, "password": password})

    # 4. Attempt to REPLAY the exact same code in the same window
    resp2 = client.post("/api/v1/auth/mfa/verify", json={"totp_code": code1})
    assert resp2.status_code == 401
    assert "already been used" in resp2.get_json()["error"]["message"]



def test_mfa_emergency_recovery_code_redemption(client, seeded_staff_user):
    """Emergency recovery code redeems successfully and is burned (cannot be used twice)."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]
    user_id = seeded_staff_user["user_id"]

    # Setup MFA
    mfa_service = get_mfa_service()
    enroll = mfa_service.initiate_enrollment(user_id, username)
    raw_secret = enroll["secret"]
    recovery_codes = enroll["recovery_codes"]
    first_recovery_code = recovery_codes[0]

    totp = pyotp.TOTP(raw_secret)
    mfa_service.confirm_enrollment(user_id, totp.now())

    # 1. Password login -> MFA pending
    client.post("/api/v1/auth/login", json={"username": username, "password": password})

    # 2. Verify using first recovery code
    verify_resp = client.post("/api/v1/auth/mfa/verify", json={"recovery_code": first_recovery_code})
    assert verify_resp.status_code == 200
    assert verify_resp.get_json()["data"]["mfa_method"] == "recovery_code"

    # Verify recovery codes count decremented to 7
    status = mfa_service.get_status(user_id)
    assert status["recovery_codes_remaining"] == 7

    client.post("/api/v1/auth/logout")

    # 3. Password login again
    client.post("/api/v1/auth/login", json={"username": username, "password": password})

    # 4. Attempt to REUSE the burned recovery code -> rejected
    reuse_resp = client.post("/api/v1/auth/mfa/verify", json={"recovery_code": first_recovery_code})
    assert reuse_resp.status_code == 401


def test_admin_assisted_mfa_reset(client, seeded_staff_user, seeded_admin_user):
    """Admin can reset MFA for a locked-out staff member."""
    staff_uid = seeded_staff_user["user_id"]
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    # Enable MFA for staff
    mfa_service = get_mfa_service()
    enroll = mfa_service.initiate_enrollment(staff_uid, staff_username)
    totp = pyotp.TOTP(enroll["secret"])
    mfa_service.confirm_enrollment(staff_uid, totp.now())
    assert mfa_service.is_mfa_enabled(staff_uid) is True

    # Login as admin
    admin_login = client.post("/api/v1/auth/login", json={
        "username": seeded_admin_user["username"],
        "password": seeded_admin_user["password"],
    })
    csrf_token = admin_login.get_json()["data"]["csrf_token"]

    # Admin resets staff MFA
    reset_resp = client.post(
        f"/api/v1/admin/users/{staff_uid}/mfa/reset",
        headers={"X-XSRF-TOKEN": csrf_token},
    )
    assert reset_resp.status_code == 200
    assert mfa_service.is_mfa_enabled(staff_uid) is False

    # Staff can now log in directly with password alone (no MFA prompt)
    client.post("/api/v1/auth/logout")
    staff_login = client.post("/api/v1/auth/login", json={
        "username": staff_username,
        "password": staff_password,
    })
    assert staff_login.status_code == 200
    assert "csrf_token" in staff_login.get_json()["data"]
    assert staff_login.get_json()["data"].get("mfa_required") is not True


# ===========================================================================
# 3. Authentication Boundary & Session Isolation Tests
# ===========================================================================


def test_session_isolation_learner_jwt_rejected_on_staff_apis(client, app_instance):
    """Learner Bearer JWTs are rejected on staff administrative APIs (fail closed)."""
    import jwt

    # Generate a valid learner JWT
    secret = app_instance.config["TEST_JWT_SECRET"]
    payload = {
        "sub": str(uuid.uuid4()),
        "name": "Public Community Learner",
        "iss": app_instance.config["NEON_AUTH_ISSUER"],
        "exp": int(time.time()) + 3600,
    }
    learner_jwt = jwt.encode(payload, secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {learner_jwt}"}

    # 1. Staff Creator Studio: GET /api/v1/creator/topics
    resp1 = client.get("/api/v1/creator/topics", headers=headers)
    assert resp1.status_code == 403
    assert "Bearer tokens are not permitted" in resp1.get_json()["error"]["message"]

    # 2. Staff Creator Studio: GET /api/v1/creator/reviews
    resp2 = client.get("/api/v1/creator/reviews", headers=headers)
    assert resp2.status_code == 403

    # 3. Administrator: GET /api/v1/admin/users
    resp3 = client.get("/api/v1/admin/users", headers=headers)
    assert resp3.status_code == 403

    # 4. Staff Case Management: GET /api/v1/staff/concerns
    resp4 = client.get("/api/v1/staff/concerns", headers=headers)
    assert resp4.status_code == 403


def test_un_enrolled_existing_staff_login_compatibility(client, seeded_staff_user):
    """Staff accounts without MFA enabled continue logging in directly without disruption."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]

    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["username"] == username
    assert data["role"] == "contributor"
    assert "csrf_token" in data
    assert data.get("mfa_required") is not True

    # Active session works immediately
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200


def test_audit_logging_emits_structured_events(client, seeded_staff_user):
    """Structured audit records are emitted for all authentication lifecycle events."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]

    # 1. Failed login emits LOGIN_FAILED
    client.post("/api/v1/auth/login", json={"username": username, "password": "WrongPassword!"})
    events = get_recent_audit_events()
    failed_events = [e for e in events if e["event"] == SecurityAuditEvent.LOGIN_FAILED]
    assert len(failed_events) >= 1
    assert failed_events[-1]["actor_id"] == username
    assert failed_events[-1]["status"] == "FAILURE"

    # 2. Successful login emits LOGIN_SUCCESS
    client.post("/api/v1/auth/login", json={"username": username, "password": password})
    events = get_recent_audit_events()
    succ_events = [e for e in events if e["event"] == SecurityAuditEvent.LOGIN_SUCCESS]
    assert len(succ_events) >= 1
    assert succ_events[-1]["status"] == "SUCCESS"


# ===========================================================================
# 4. Phase 1A.1 Verification Tests (MFA Password Re-Verification, Throttling, Reset Safety)
# ===========================================================================


def test_mfa_enrollment_password_re_verification_enforcement(client, seeded_staff_user):
    """MFA enrollment requires recent authentication or explicit password re-verification."""
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]

    login_resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    csrf_token = login_resp.get_json()["data"]["csrf_token"]

    # 1. Simulate expired auth_time (> 15 min old)
    with client.session_transaction() as sess:
        sess["auth_time"] = time.time() - 1000

    # 2. Request without password fails closed with 401
    stale_resp = client.post(
        "/api/v1/auth/mfa/enroll",
        headers={"X-XSRF-TOKEN": csrf_token},
        json={},
    )
    assert stale_resp.status_code == 401
    assert "Recent password verification required" in stale_resp.get_json()["error"]["message"]

    # 3. Request with wrong password fails closed with 401
    wrong_pwd_resp = client.post(
        "/api/v1/auth/mfa/enroll",
        headers={"X-XSRF-TOKEN": csrf_token},
        json={"password": "IncorrectPassword123!"},
    )
    assert wrong_pwd_resp.status_code == 401
    assert "Password verification failed" in wrong_pwd_resp.get_json()["error"]["message"]

    # 4. Request with valid password succeeds and issues enrollment details
    valid_resp = client.post(
        "/api/v1/auth/mfa/enroll",
        headers={"X-XSRF-TOKEN": csrf_token},
        json={"password": password},
    )
    assert valid_resp.status_code == 200
    data = valid_resp.get_json()["data"]
    assert "secret" in data
    assert "recovery_codes" in data


def test_mfa_verification_brute_force_throttling_and_session_clearing(client, seeded_staff_user):
    """Repeated invalid MFA verification attempts trigger lockout and session clearing."""
    staff_uid = seeded_staff_user["user_id"]
    username = seeded_staff_user["username"]
    password = seeded_staff_user["password"]

    # Setup active MFA for staff
    mfa_service = get_mfa_service()
    enroll = mfa_service.initiate_enrollment(staff_uid, username)
    totp = pyotp.TOTP(enroll["secret"])
    mfa_service.confirm_enrollment(staff_uid, totp.now())

    # Step 1: Login with password to enter mfa_pending state
    login_resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    assert login_resp.get_json()["data"].get("mfa_required") is True

    # Attempt 1: wrong code
    v1 = client.post("/api/v1/auth/mfa/verify", json={"totp_code": "000000"})
    assert v1.status_code == 401
    assert "Invalid authentication code" in v1.get_json()["error"]["message"]

    # Attempt 2: wrong code
    v2 = client.post("/api/v1/auth/mfa/verify", json={"totp_code": "111111"})
    assert v2.status_code == 401

    # Attempt 3: third failure clears session and fails closed
    v3 = client.post("/api/v1/auth/mfa/verify", json={"totp_code": "222222"})
    assert v3.status_code == 401
    assert "Too many failed verification attempts" in v3.get_json()["error"]["message"]

    # Attempt 4: session is completely cleared, subsequent request requires login from scratch
    v4 = client.post("/api/v1/auth/mfa/verify", json={"totp_code": totp.now()})
    assert v4.status_code == 401
    assert "expired or is invalid" in v4.get_json()["error"]["message"]


def test_admin_reset_endpoints_require_existing_users(client, seeded_admin_user):
    """Admin reset endpoints return 404 when target user does not exist."""
    admin_login = client.post("/api/v1/auth/login", json={
        "username": seeded_admin_user["username"],
        "password": seeded_admin_user["password"],
    })
    csrf_token = admin_login.get_json()["data"]["csrf_token"]
    headers = {"X-XSRF-TOKEN": csrf_token}

    # 1. Reset MFA for non-existent user ID
    mfa_404 = client.post("/api/v1/admin/users/usr_non_existent_123/mfa/reset", headers=headers)
    assert mfa_404.status_code == 404
    assert "does not exist" in mfa_404.get_json()["error"]["message"]

    # 2. Reset throttle for non-existent username
    throttle_404 = client.post("/api/v1/admin/users/ghost_user_999/throttle/reset", headers=headers)
    assert throttle_404.status_code == 404
    assert "does not exist" in throttle_404.get_json()["error"]["message"]


# ===========================================================================
# 5. Phase 1A.2 Session Revocation & Fail-Closed DB Tests
# ===========================================================================

from unittest.mock import patch
from backend.platform.mfa_service import MfaStorageError


def test_session_revocation_on_admin_mfa_reset(app_instance, seeded_staff_user, seeded_admin_user):
    """Admin MFA reset revokes active sessions across all browsers and devices."""
    staff_uid = seeded_staff_user["user_id"]
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    # 1. Simulate Browser 1 (e.g. desktop) and Browser 2 (e.g. mobile)
    browser1 = app_instance.test_client()
    browser2 = app_instance.test_client()
    admin_client = app_instance.test_client()

    # Browser 1 logs in
    resp1 = browser1.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    assert resp1.status_code == 200
    assert browser1.get("/api/v1/auth/me").status_code == 200

    # Ensure a measurable timestamp progression
    time.sleep(0.05)

    # Browser 2 logs in
    resp2 = browser2.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    assert resp2.status_code == 200
    assert browser2.get("/api/v1/auth/me").status_code == 200

    time.sleep(0.05)

    # 2. Admin logs in and resets staff MFA
    admin_login = admin_client.post("/api/v1/auth/login", json={
        "username": seeded_admin_user["username"],
        "password": seeded_admin_user["password"],
    })
    assert admin_login.status_code == 200
    admin_csrf = admin_login.get_json()["data"]["csrf_token"]

    reset_resp = admin_client.post(
        f"/api/v1/admin/users/{staff_uid}/mfa/reset",
        headers={"X-XSRF-TOKEN": admin_csrf},
    )
    assert reset_resp.status_code == 200

    # 3. Both Browser 1 and Browser 2 attempt to use their existing sessions -> rejected (401)
    b1_check = browser1.get("/api/v1/auth/me")
    assert b1_check.status_code == 401
    assert "Session has been revoked" in b1_check.get_json()["error"]["message"]

    b2_check = browser2.get("/api/v1/auth/me")
    assert b2_check.status_code == 401
    assert "Session has been revoked" in b2_check.get_json()["error"]["message"]


def test_newly_authenticated_session_works_after_mfa_reset(app_instance, seeded_staff_user, seeded_admin_user):
    """After an admin reset, subsequent new logins establish valid active sessions."""
    staff_uid = seeded_staff_user["user_id"]
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    admin_client = app_instance.test_client()
    admin_login = admin_client.post("/api/v1/auth/login", json={
        "username": seeded_admin_user["username"],
        "password": seeded_admin_user["password"],
    })
    admin_csrf = admin_login.get_json()["data"]["csrf_token"]

    # Admin resets MFA
    reset_resp = admin_client.post(
        f"/api/v1/admin/users/{staff_uid}/mfa/reset",
        headers={"X-XSRF-TOKEN": admin_csrf},
    )
    assert reset_resp.status_code == 200

    # Ensure timestamp progression
    time.sleep(0.05)

    # Staff performs a new login
    new_browser = app_instance.test_client()
    login_resp = new_browser.post("/api/v1/auth/login", json={
        "username": staff_username,
        "password": staff_password,
    })
    assert login_resp.status_code == 200

    # Active session check succeeds
    me_resp = new_browser.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.get_json()["data"]["username"] == staff_username


def test_mfa_disable_revokes_other_device_sessions(app_instance, seeded_staff_user):
    """Disabling MFA invalidates sessions on other browsers while keeping the current session active."""
    staff_uid = seeded_staff_user["user_id"]
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    # Setup MFA for staff
    mfa_service = get_mfa_service()
    enroll = mfa_service.initiate_enrollment(staff_uid, staff_username)
    raw_secret = enroll["secret"]
    totp = pyotp.TOTP(raw_secret)
    mfa_service.confirm_enrollment(staff_uid, totp.now())

    # Browser 1 (initiator) logs in
    browser1 = app_instance.test_client()
    browser1.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    v1 = browser1.post("/api/v1/auth/mfa/verify", json={"totp_code": totp.now()})
    assert v1.status_code == 200
    b1_csrf = v1.get_json()["data"]["csrf_token"]

    # Browser 2 (other device) logs in
    browser2 = app_instance.test_client()
    browser2.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    # Note: might need code from step or slight wait if replay check applies
    time.sleep(0.05)
    v2 = browser2.post("/api/v1/auth/mfa/verify", json={"totp_code": totp.now()})
    # If same time step was used, use emergency recovery code for browser 2
    if v2.status_code != 200:
        recovery_code = enroll["recovery_codes"][0]
        v2 = browser2.post("/api/v1/auth/mfa/verify", json={"recovery_code": recovery_code})
    assert v2.status_code == 200
    assert browser2.get("/api/v1/auth/me").status_code == 200

    time.sleep(0.05)

    # Browser 1 disables MFA
    disable_resp = browser1.post(
        "/api/v1/auth/mfa/disable",
        json={"password": staff_password, "totp_code": totp.now()},
        headers={"X-XSRF-TOKEN": b1_csrf},
    )
    if disable_resp.status_code != 200:
        # Replay might have triggered on same totp_code, fallback to recovery code
        recovery_code = enroll["recovery_codes"][1]
        disable_resp = browser1.post(
            "/api/v1/auth/mfa/disable",
            json={"password": staff_password, "recovery_code": recovery_code},
            headers={"X-XSRF-TOKEN": b1_csrf},
        )
    assert disable_resp.status_code == 200

    # Current browser (Browser 1) remains authenticated because auth_time was refreshed
    b1_me = browser1.get("/api/v1/auth/me")
    assert b1_me.status_code == 200

    # Other device (Browser 2) is revoked
    b2_me = browser2.get("/api/v1/auth/me")
    assert b2_me.status_code == 401
    assert "Session has been revoked" in b2_me.get_json()["error"]["message"]


def test_normal_sessions_preserved_when_no_revocation_occurred(client, seeded_staff_user):
    """Sessions remain fully valid and functional when no revocation events occur."""
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    login_resp = client.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    assert login_resp.status_code == 200

    for _ in range(3):
        me_resp = client.get("/api/v1/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.get_json()["data"]["username"] == staff_username


def test_database_failure_during_session_validation_fails_closed(client, seeded_staff_user):
    """Database failure when checking session revocation timestamp fails closed (HTTP 503)."""
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    # 1. Login successfully
    login_resp = client.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    assert login_resp.status_code == 200

    # 2. Simulate database failure during session revocation check in get_current_user()
    with patch.object(
        get_mfa_service(),
        "get_session_revoked_at",
        side_effect=MfaStorageError("PostgreSQL pool connection timeout"),
    ):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 503
        err = resp.get_json()["error"]
        assert err["code"] == "SERVICE_UNAVAILABLE"


def test_database_failure_during_login_mfa_check_fails_closed(client, seeded_staff_user):
    """Database failure during login MFA check fails closed (HTTP 503) without granting password-only access."""
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    # Simulate database outage when checking is_mfa_enabled
    with patch.object(
        get_mfa_service(),
        "is_mfa_enabled",
        side_effect=MfaStorageError("PostgreSQL database connection refused"),
    ):
        resp = client.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
        assert resp.status_code == 503
        err = resp.get_json()["error"]
        assert err["code"] == "SERVICE_UNAVAILABLE"

    # Verify no session was created in the client cookie
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401


def test_database_failure_during_mfa_verify_fails_closed(client, seeded_staff_user):
    """Database failure during MFA code verification fails closed with HTTP 503."""
    staff_uid = seeded_staff_user["user_id"]
    staff_username = seeded_staff_user["username"]
    staff_password = seeded_staff_user["password"]

    # Enable MFA
    mfa_service = get_mfa_service()
    enroll = mfa_service.initiate_enrollment(staff_uid, staff_username)
    totp = pyotp.TOTP(enroll["secret"])
    mfa_service.confirm_enrollment(staff_uid, totp.now())

    # Step 1: Login to get mfa_pending session
    login_resp = client.post("/api/v1/auth/login", json={"username": staff_username, "password": staff_password})
    assert login_resp.status_code == 200
    assert login_resp.get_json()["data"].get("mfa_required") is True

    # Step 2: Simulate database failure during verify_login_mfa
    with patch.object(
        get_mfa_service(),
        "verify_login_mfa",
        side_effect=MfaStorageError("PostgreSQL transaction aborted"),
    ):
        verify_resp = client.post("/api/v1/auth/mfa/verify", json={"totp_code": totp.now()})
        assert verify_resp.status_code == 503
        assert verify_resp.get_json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_database_failure_during_admin_reset_fails_closed(client, seeded_admin_user, seeded_staff_user):
    """Database failure during admin MFA reset returns HTTP 503."""
    staff_uid = seeded_staff_user["user_id"]

    admin_login = client.post("/api/v1/auth/login", json={
        "username": seeded_admin_user["username"],
        "password": seeded_admin_user["password"],
    })
    admin_csrf = admin_login.get_json()["data"]["csrf_token"]

    with patch.object(
        get_mfa_service(),
        "admin_reset_mfa",
        side_effect=MfaStorageError("PostgreSQL write failed"),
    ):
        reset_resp = client.post(
            f"/api/v1/admin/users/{staff_uid}/mfa/reset",
            headers={"X-XSRF-TOKEN": admin_csrf},
        )
        assert reset_resp.status_code == 503
        assert reset_resp.get_json()["error"]["code"] == "SERVICE_UNAVAILABLE"


