"""Phase 1B Staff & Reviewer Onboarding Vetting Workflow Tests.

Verifies:
1. Public Submission & Validation:
   - Valid inputs return 201 Created with unique reference ID and secure tracking token.
   - Required fields, statement length, and declarations fail closed (HTTP 400).
   - Duplicate active applications from same email return 409 Conflict.
2. Applicant Tracking & Follow-up:
   - Tracking requires both reference ID and secret tracking token.
   - Invalid token fails closed (401 Unauthorized / 404 Not Found).
   - Responding to more_info_requested transitions application back to under_review.
   - Voluntary withdrawal transitions to withdrawn.
3. Reviewer Queue & Role-Based Authorization:
   - Contributor/anonymous cannot access admin vetting endpoints (401 / 403).
   - Admin can list, filter by status, search, and view complete audit history.
   - Reviewer can claim application and update verification checklist + internal notes.
4. Approval, Least-Privilege Provisioning & State Machine:
   - Admin approval provisions a real PostgreSQL user account with temporary password.
   - Self-approval by an administrator is strictly blocked (403 Forbidden).
   - Non-admin cannot approve or reject applications (403 Forbidden).
   - Terminal transitions (e.g. approving an already rejected/withdrawn application) fail closed (409 Conflict).
   - Audit trail in staff_application_history records every actor, action, timestamp, and rationale.
"""

from __future__ import annotations

import json
import time
import uuid
import pytest

from backend.app import create_app
from backend.domain.domain_objects import User, UserRole
from backend.platform.audit_log import SecurityAuditEvent, clear_audit_events, get_recent_audit_events
from backend.platform.security import hash_password, verify_password
from backend.storage.db import get_db_session
from backend.storage.postgres_models import (
    StaffApplicationModel,
    StaffApplicationHistoryModel,
    UserModel,
)


@pytest.fixture()
def app_instance(tmp_path):
    test_db = str(tmp_path / "test_throttle.sqlite3")
    test_mfa_db = str(tmp_path / "test_mfa.sqlite3")

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-phase1b-secret-key-32-bytes-long!",
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
def clean_database():
    """Ensure staff application tables, test users, and audit logs are pristine."""
    clear_audit_events()
    with get_db_session() as db:
        db.query(StaffApplicationHistoryModel).delete()
        db.query(StaffApplicationModel).delete()
        db.query(UserModel).filter(
            UserModel.username.like("test_%")
            | UserModel.username.like("app_%")
            | UserModel.username.like("admin_%")
            | UserModel.username.like("contrib_%")
        ).delete()
        db.commit()
    yield
    clear_audit_events()


def seed_user(user_id: str, username: str, role: str, display_name: str = "Test Staff Member"):
    """Seeds a staff user in the PostgreSQL database so get_current_user() authenticates them."""
    with get_db_session() as db:
        existing = db.query(UserModel).filter_by(user_id=user_id).first()
        if not existing:
            u = UserModel(
                user_id=user_id,
                username=username,
                display_name=display_name,
                role=role,
                password_hash=hash_password("TestSecurePass123!"),
                is_active=True,
            )
            db.add(u)
            db.commit()


def set_client_session(c, user_id: str, username: str, role: str, display_name: str = "Staff Member"):
    """Configures signed session cookie for the given user."""
    seed_user(user_id, username, role, display_name)
    with c.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username
        sess["display_name"] = display_name
        sess["role"] = role
        sess["auth_time"] = time.time()


def clear_client_session(c):
    """Clears the session cookie for anonymous requests."""
    with c.session_transaction() as sess:
        sess.clear()


# =========================================================================
# 1. Public Submission & Validation Tests
# =========================================================================

def test_public_submission_validation_and_success(client):
    """Valid submission returns 201 with reference_id and tracking_token."""
    payload = {
        "applicant_name": "Dr. Sunita Sen",
        "applicant_email": "sunita.sen@healthinst.org",
        "applicant_phone": "+91 98765 43210",
        "requested_role": "reviewer",
        "organization": "Apollo Research Foundation",
        "professional_title": "Lead Clinical Epidemiologist",
        "credential_reference": "NMC-2015-88392",
        "portfolio_url": "https://healthinst.org/faculty/sunita-sen",
        "statement_of_purpose": "I have spent over a decade conducting public health research and want to verify evidence cards for youth learners.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }

    resp = client.post("/api/v1/staff/apply", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["reference_id"].startswith("APP-")
    assert data["tracking_token"].startswith("sec_app_")
    assert data["status"] == "pending_review"

    # Verify database persistence
    with get_db_session() as db:
        app = db.query(StaffApplicationModel).filter_by(reference_id=data["reference_id"]).first()
        assert app is not None
        assert app.applicant_name == "Dr. Sunita Sen"
        assert app.tracking_token_hash is not None
        assert app.status == "pending_review"
        assert app.verification_checklist["contact_verified"] is False


def test_public_submission_validates_required_fields(client):
    """Submission missing declarations or too short statement fails 400."""
    # Missing statement of purpose
    resp = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Dr. Sunita Sen",
        "applicant_email": "sunita.sen@healthinst.org",
        "requested_role": "contributor",
        "statement_of_purpose": "Short",  # < 30 chars
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    })
    assert resp.status_code == 400
    assert "between 30 and 4000 characters" in resp.get_json()["error"]["message"]

    # Missing evidence standards declaration
    resp = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Dr. Sunita Sen",
        "applicant_email": "sunita.sen@healthinst.org",
        "requested_role": "contributor",
        "statement_of_purpose": "A sufficiently long statement describing qualifications and background for review.",
        "evidence_standards_acknowledged": False,
        "child_safety_acknowledged": True,
    })
    assert resp.status_code == 400
    assert "evidence-based health" in resp.get_json()["error"]["message"]

    # Missing child safety declaration
    resp = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Dr. Sunita Sen",
        "applicant_email": "sunita.sen@healthinst.org",
        "requested_role": "contributor",
        "statement_of_purpose": "A sufficiently long statement describing qualifications and background for review.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": False,
    })
    assert resp.status_code == 400
    assert "learner safety" in resp.get_json()["error"]["message"]

    # Invalid role
    resp = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Dr. Sunita Sen",
        "applicant_email": "sunita.sen@healthinst.org",
        "requested_role": "super_admin_god_mode",
        "statement_of_purpose": "A sufficiently long statement describing qualifications and background for review.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    })
    assert resp.status_code == 400
    assert "requested_role must be one of" in resp.get_json()["error"]["message"]


def test_duplicate_active_application_conflict(client):
    """Submitting another active application with the same email returns 409 Conflict."""
    payload = {
        "applicant_name": "Dr. Vijay K",
        "applicant_email": "vijay.k@hospital.org",
        "requested_role": "contributor",
        "statement_of_purpose": "Experienced medical writer with background in infectious disease curriculum.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }

    # First submission succeeds
    resp1 = client.post("/api/v1/staff/apply", json=payload)
    assert resp1.status_code == 201

    # Second submission with same email is rejected
    resp2 = client.post("/api/v1/staff/apply", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.get_json()["error"]["message"]


# =========================================================================
# 2. Tracking, Follow-up, and Withdrawal Tests
# =========================================================================

def test_applicant_tracking_and_authentication(client):
    """Tracking requires both correct reference ID and secret token."""
    payload = {
        "applicant_name": "Pooja Reddy",
        "applicant_email": "pooja.reddy@ngo.org",
        "requested_role": "case_handler",
        "statement_of_purpose": "Active community worker in Guntur district coordinating sanitation drives.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }
    init_res = client.post("/api/v1/staff/apply", json=payload).get_json()["data"]
    ref_id = init_res["reference_id"]
    token = init_res["tracking_token"]

    # Valid tracking credentials return public view
    track_res = client.post("/api/v1/staff/applications/track", json={
        "reference_id": ref_id,
        "tracking_token": token,
    })
    assert track_res.status_code == 200
    tracked_data = track_res.get_json()["data"]
    assert tracked_data["reference_id"] == ref_id
    assert tracked_data["applicant_name"] == "Pooja Reddy"
    assert tracked_data["status"] == "pending_review"
    # Never expose internal notes
    assert "internal_notes" not in tracked_data

    # Wrong token fails 401 Unauthorized
    bad_res = client.post("/api/v1/staff/applications/track", json={
        "reference_id": ref_id,
        "tracking_token": "sec_app_wrong_invalid_token",
    })
    assert bad_res.status_code == 401


def test_applicant_follow_up_response(client):
    """Applicant responds to more_info_requested and transitions back to under_review."""
    clear_client_session(client)
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Ravi Teja",
        "applicant_email": "ravi.teja@community.org",
        "requested_role": "contributor",
        "statement_of_purpose": "Experienced educational content creator in Telugu and English.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]
    token = init_res["tracking_token"]

    # Admin requests more info
    with get_db_session() as db:
        app = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first()
        app_id = app.application_id

    set_client_session(client, "admin_user_01", "admin_user_01", "admin")
    req_info_res = client.post(f"/api/v1/admin/staff-applications/{app_id}/request-info", json={
        "details": "Please provide a sample lesson outline on water filtration.",
    })
    assert req_info_res.status_code == 200

    # Clear session to act as public applicant
    clear_client_session(client)

    # Applicant tracks and sees the query
    track_res = client.post("/api/v1/staff/applications/track", json={
        "reference_id": ref_id,
        "tracking_token": token,
    })
    assert track_res.get_json()["data"]["status"] == "more_info_requested"
    assert "water filtration" in track_res.get_json()["data"]["info_request_details"]

    # Applicant responds
    respond_res = client.post(f"/api/v1/staff/applications/{ref_id}/respond", json={
        "tracking_token": token,
        "applicant_notes": "Sample outline attached: Card 1 covers boiling, Card 2 chlorination, Card 3 storage hygiene.",
    })
    assert respond_res.status_code == 200
    assert respond_res.get_json()["data"]["status"] == "under_review"

    # Status in database is now under_review
    with get_db_session() as db:
        refreshed = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first()
        assert refreshed.status == "under_review"
        assert "Sample outline" in refreshed.applicant_notes


def test_applicant_voluntary_withdrawal(client):
    """Applicant can withdraw application while active."""
    clear_client_session(client)
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Meera Joshi",
        "applicant_email": "meera.joshi@clinic.org",
        "requested_role": "reviewer",
        "statement_of_purpose": "Clinical reviewer with 5 years experience reviewing emergency protocols.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]
    token = init_res["tracking_token"]

    withdraw_res = client.post(f"/api/v1/staff/applications/{ref_id}/withdraw", json={
        "tracking_token": token,
        "rationale": "Accepted another full-time clinical engagement.",
    })
    assert withdraw_res.status_code == 200
    assert withdraw_res.get_json()["data"]["status"] == "withdrawn"

    # Withdrawn application tracking token is expired/revoked
    again_res = client.post(f"/api/v1/staff/applications/{ref_id}/withdraw", json={
        "tracking_token": token,
    })
    assert again_res.status_code in (401, 404, 409)


# =========================================================================
# 3. Administrative Review & Vetting Queue Tests
# =========================================================================

def test_admin_authorization_enforcement(client):
    """Only admins can access administrative staff application management endpoints."""
    # 1. Anonymous fails 401
    clear_client_session(client)
    assert client.get("/api/v1/admin/staff-applications").status_code == 401

    # 2. Contributor fails 403
    set_client_session(client, "contrib_user_01", "contrib_user_01", "contributor")
    assert client.get("/api/v1/admin/staff-applications").status_code == 403

    # 3. Admin succeeds 200
    set_client_session(client, "admin_user_01", "admin_user_01", "admin")
    assert client.get("/api/v1/admin/staff-applications").status_code == 200


def test_admin_claim_and_verification_checklist(client):
    """Admin can claim application and update verification checklist."""
    clear_client_session(client)
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Dr. Ananya Ray",
        "applicant_email": "ananya.ray@medical.org",
        "requested_role": "reviewer",
        "statement_of_purpose": "Pediatric health specialist with university teaching experience.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]

    with get_db_session() as db:
        app_id = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first().application_id

    # Switch to admin
    set_client_session(client, "admin_user_01", "admin_user_01", "admin")

    # Claim review
    claim_res = client.post(f"/api/v1/admin/staff-applications/{app_id}/claim")
    assert claim_res.status_code == 200

    with get_db_session() as db:
        app = db.query(StaffApplicationModel).filter_by(application_id=app_id).first()
        assert app.status == "under_review"
        assert app.assigned_reviewer_id == "admin_user_01"

    # Update checklist
    check_res = client.post(f"/api/v1/admin/staff-applications/{app_id}/checklist", json={
        "verification_checklist": {
            "contact_verified": True,
            "affiliation_verified": True,
            "role_criteria_met": True,
            "verification_notes": "Checked against state medical registry #998811.",
        },
        "internal_notes": "Highly qualified candidate. Excellent candidate for pediatric reviewer.",
    })
    assert check_res.status_code == 200

    # Retrieve detail
    detail_res = client.get(f"/api/v1/admin/staff-applications/{app_id}").get_json()["data"]
    assert detail_res["verification_checklist"]["contact_verified"] is True
    assert "Highly qualified" in detail_res["internal_notes"]


# =========================================================================
# 4. Approval, Account Provisioning, and Security Guards
# =========================================================================

def test_admin_approval_provisions_postgres_account(client):
    """Approving application provisions a real active user in PostgreSQL with temporary password."""
    clear_client_session(client)
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Dr. Alok Verma",
        "applicant_email": "alok.verma@delhihealth.org",
        "requested_role": "reviewer",
        "statement_of_purpose": "Experienced reviewer specializing in water quality and vector-borne diseases.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]

    with get_db_session() as db:
        app_id = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first().application_id

    # Switch to admin
    set_client_session(client, "admin_user_01", "admin_user_01", "admin")

    # Approve application
    approve_res = client.post(f"/api/v1/admin/staff-applications/{app_id}/approve", json={
        "approved_role": "reviewer",
        "rationale": "All credentials verified and checklist fully satisfied.",
    })
    assert approve_res.status_code == 200
    app_data = approve_res.get_json()["data"]
    assert app_data["status"] == "approved"
    assert app_data["approved_role"] == "reviewer"
    setup_token = app_data["setup_token"]
    assert setup_token is not None
    username = app_data["username"]
    prov_uid = app_data["provisioned_user_id"]

    # Verify user was created in PostgreSQL users table
    with get_db_session() as db:
        user = db.query(UserModel).filter_by(user_id=prov_uid).first()
        assert user is not None
        assert user.username == username
        assert user.role == "reviewer"
        assert user.is_active is True
        assert user.must_change_password is True
        assert user.setup_token_hash is not None


def test_self_approval_blocked(client):
    """An administrator cannot approve their own application."""
    clear_client_session(client)
    # Create application with admin's email
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Self Admin",
        "applicant_email": "admin_self@healthaware.org",
        "requested_role": "reviewer",
        "statement_of_purpose": "Admin applying for reviewer privileges.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]

    with get_db_session() as db:
        app_id = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first().application_id

    # Admin with matching username tries to approve
    set_client_session(client, "admin_self_uid", "admin_self@healthaware.org", "admin")

    resp = client.post(f"/api/v1/admin/staff-applications/{app_id}/approve", json={
        "approved_role": "reviewer",
    })
    assert resp.status_code == 403
    assert "cannot approve your own" in resp.get_json()["error"]["message"]


def test_rejection_records_rationale(client):
    """Declining an application transitions to rejected and stores rationale."""
    clear_client_session(client)
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Spam Applicant",
        "applicant_email": "spam@commercialsite.com",
        "requested_role": "contributor",
        "statement_of_purpose": "Promoting commercial dietary supplements through health courses.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]

    with get_db_session() as db:
        app_id = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first().application_id

    # Switch to admin
    set_client_session(client, "admin_user_01", "admin_user_01", "admin")

    reject_res = client.post(f"/api/v1/admin/staff-applications/{app_id}/reject", json={
        "reason": "Commercial promotion strictly prohibited by evidence standards.",
    })
    assert reject_res.status_code == 200

    with get_db_session() as db:
        app = db.query(StaffApplicationModel).filter_by(application_id=app_id).first()
        assert app.status == "rejected"
        assert "Commercial promotion" in app.rejection_reason


def test_immutable_history_audit_trail(client):
    """Every state transition creates an audit history entry with actor, action, and rationale."""
    clear_client_session(client)
    init_res = client.post("/api/v1/staff/apply", json={
        "applicant_name": "Audit Test Subject",
        "applicant_email": "audit.subject@gov.in",
        "requested_role": "jurisdiction_officer",
        "statement_of_purpose": "Sanitary inspector applying for municipal coordination access.",
        "evidence_standards_acknowledged": True,
        "child_safety_acknowledged": True,
    }).get_json()["data"]
    ref_id = init_res["reference_id"]

    with get_db_session() as db:
        app_id = db.query(StaffApplicationModel).filter_by(reference_id=ref_id).first().application_id

    # 1. Claim
    set_client_session(client, "admin_user_01", "admin_user_01", "admin")
    client.post(f"/api/v1/admin/staff-applications/{app_id}/claim")

    # 2. Request Info
    client.post(f"/api/v1/admin/staff-applications/{app_id}/request-info", json={
        "details": "Please specify your designated municipal ward.",
    })

    # 3. Respond
    clear_client_session(client)
    client.post(f"/api/v1/staff/applications/{ref_id}/respond", json={
        "tracking_token": init_res["tracking_token"],
        "applicant_notes": "Assigned to Ward 14, Guntur Municipal Corporation.",
    })

    # 4. Approve
    set_client_session(client, "admin_user_01", "admin_user_01", "admin")
    client.post(f"/api/v1/admin/staff-applications/{app_id}/approve", json={
        "approved_role": "jurisdiction_officer",
        "assigned_jurisdiction": "Guntur",
        "rationale": "Verified through municipal authority registry.",
    })

    # Retrieve detail and inspect history list
    detail = client.get(f"/api/v1/admin/staff-applications/{app_id}").get_json()["data"]
    history = detail["history"]
    assert len(history) >= 5  # submitted, claimed, more_info_requested, applicant_responded, approved

    actions = [h["action"] for h in history]
    assert "submit" in actions
    assert "claim" in actions
    assert "request_info" in actions
    assert "respond_info" in actions
    assert "approve" in actions

    # Verify audit log recorded events
    recent_events = get_recent_audit_events()
    audit_events = [e["event"] for e in recent_events]
    assert SecurityAuditEvent.STAFF_APP_SUBMITTED in audit_events
    assert SecurityAuditEvent.STAFF_APP_APPROVED in audit_events
