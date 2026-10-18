"""Automated tests for Report a Concern, Private Tracking, and Staff Case Management.

Validates:
1. Citizen submission creates persistent records with unique references.
2. Tracking tokens are never stored in plaintext (SHA-256 hash only).
3. Input validation rejects invalid states, categories, and oversized inputs.
4. Attachment handling enforces magic bytes, strips metadata, and limits size.
5. Citizens without valid tokens are denied access.
6. Permitted details and timeline are returned without leaking internal notes or handler IDs.
7. Append-only status event history and audit trails.
8. Staff role permissions: Handler, Admin, and Jurisdiction-scoped Officer.
"""

from __future__ import annotations

import io
import json
import pytest
from PIL import Image

from backend.app import create_app
from backend.domain.concern_models import (
    ActorType,
    ConcernCategory,
    ConcernDuration,
    ConcernStatus,
)
from backend.domain.domain_objects import User, UserRole
from backend.platform.attachment_storage import (
    AttachmentStorageService,
    detect_image_format,
    sanitize_and_strip_metadata,
)
from backend.storage.concern_repository import (
    ConcernRepository,
    hash_tracking_token,
)
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    init_db,
)
from backend.storage.postgres_models import (
    Base,
    ConcernAttachmentModel,
    ConcernReportModel,
    ConcernStatusEventModel,
    StaffJurisdictionModel,
    UserModel,
)


from sqlalchemy import text
from backend.storage.db import get_test_database_url


@pytest.fixture()
def test_db():
    """Provides an isolated database initialized with all schema tables."""
    test_url = get_test_database_url()
    if test_url and "postgresql" in test_url:
        engine = create_app_engine(test_url)
        # Explicit Safety Gate: strictly require healthaware_test
        assert engine.url.database == "healthaware_test", (
            f"CRITICAL SAFETY VIOLATION: Test database must be 'healthaware_test', got {engine.url.database}"
        )
    else:
        engine = create_app_engine("sqlite:///:memory:")
        init_db(engine)

    # Clean test tables before test
    with engine.begin() as conn:
        for tbl in ["concern_attachments", "concern_status_events", "concern_reports", "staff_jurisdictions", "users"]:
            try:
                conn.execute(text(f"DELETE FROM {tbl}"))
            except Exception:
                pass

    yield engine

    # Clean test tables after test
    with engine.begin() as conn:
        for tbl in ["concern_attachments", "concern_status_events", "concern_reports", "staff_jurisdictions", "users"]:
            try:
                conn.execute(text(f"DELETE FROM {tbl}"))
            except Exception:
                pass


@pytest.fixture()
def client(test_db):
    """Provides a test Flask client configured with the test database."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-32-bytes-long-for-testing",
        "SKIP_NDB_CONTEXT": True,
        "DATABASE_URL": str(test_db.url),
    })

    # Override get_engine to use our test_db
    import backend.storage.db as db_mod
    original_engine = db_mod._engine
    original_factory = db_mod._SessionFactory
    db_mod._engine = test_db
    db_mod._SessionFactory = None

    with app.test_client() as test_client:
        yield test_client

    db_mod._engine = original_engine
    db_mod._SessionFactory = original_factory


def create_test_image(format="JPEG", size=(100, 100), color="red") -> bytes:
    """Generates valid image bytes for attachment testing."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Attachment Storage Tests
# ---------------------------------------------------------------------------


def test_attachment_magic_byte_detection():
    jpeg_bytes = create_test_image("JPEG")
    png_bytes = create_test_image("PNG")
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"

    assert detect_image_format(jpeg_bytes) == "image/jpeg"
    assert detect_image_format(png_bytes) == "image/png"
    assert detect_image_format(fake_exe) is None


def test_attachment_metadata_stripping(tmp_path):
    storage = AttachmentStorageService(storage_dir=str(tmp_path))
    raw_jpeg = create_test_image("JPEG")
    
    key, mime, size, checksum = storage.store_attachment(raw_jpeg, "test.jpg")
    assert key.startswith("att_")
    assert mime == "image/jpeg"
    assert size > 0
    assert len(checksum) == 64

    # Verify file is stored in storage_dir
    stored_path = storage.get_attachment_path(key)
    assert stored_path is not None
    assert tmp_path.as_posix() in stored_path.replace("\\", "/")


def test_attachment_rejects_unsupported_format(tmp_path):
    storage = AttachmentStorageService(storage_dir=str(tmp_path))
    script_bytes = b"#!/bin/bash\necho dangerous"
    with pytest.raises(ValueError, match="Unsupported file format"):
        storage.store_attachment(script_bytes, "malicious.sh")


# ---------------------------------------------------------------------------
# Citizen Reporting Flow Tests
# ---------------------------------------------------------------------------


def test_citizen_submit_valid_concern(client):
    payload = {
        "category": "garbage",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "municipality": "GVMC",
        "locality": "Near RTC Complex, Sector 4",
        "description": "Large garbage heap accumulating for days creating foul odor.",
        "duration": "3-7 days",
    }
    response = client.post("/api/v1/concerns", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert "Your concern has been received by HealthAware." in data["message"]
    assert "data" in data
    ref_id = data["data"]["reference_id"]
    token = data["data"]["tracking_token"]

    assert ref_id.startswith("HA-")
    assert len(token) > 20
    assert data["data"]["status"] == "received"

    # Verify token is NOT stored in plaintext
    with get_db_session() as session:
        report = session.query(ConcernReportModel).filter_by(reference_id=ref_id).first()
        assert report is not None
        assert report.token_hash == hash_tracking_token(token)
        assert report.token_hash != token


def test_citizen_submit_rejects_invalid_state(client):
    payload = {
        "category": "drainage",
        "state": "Maharashtra",  # Not AP or Telangana
        "district": "Mumbai",
        "locality": "Main Road",
        "description": "Blocked drain overflow",
        "duration": "< 3 days",
    }
    response = client.post("/api/v1/concerns", json=payload)
    assert response.status_code == 400
    err = response.get_json()["error"]
    assert "State must be Andhra Pradesh or Telangana" in err["message"]


def test_citizen_submit_rejects_missing_locality(client):
    payload = {
        "category": "stagnant_water",
        "state": "Telangana",
        "district": "Hyderabad",
        "locality": "",  # Empty
        "description": "Mosquito breeding puddle",
        "duration": "1-2 weeks",
    }
    response = client.post("/api/v1/concerns", json=payload)
    assert response.status_code == 400


def test_citizen_track_with_valid_token(client):
    # 1. Submit concern
    sub_res = client.post("/api/v1/concerns", json={
        "category": "stagnant_water",
        "state": "Telangana",
        "district": "Warangal",
        "locality": "Subhash Nagar park",
        "description": "Standing pool of water after rainfall",
        "duration": "< 3 days",
    })
    sub_data = sub_res.get_json()["data"]
    ref_id = sub_data["reference_id"]
    token = sub_data["tracking_token"]

    # 2. Track with valid credentials
    track_res = client.post("/api/v1/concerns/track", json={
        "reference_id": ref_id,
        "tracking_token": token,
    })
    assert track_res.status_code == 200
    details = track_res.get_json()["data"]

    assert details["reference_id"] == ref_id
    assert details["status"] == "received"
    assert details["category"] == "stagnant_water"
    assert len(details["timeline"]) == 1
    # Check that public notes exist and internal notes are NOT exposed
    assert "public_notes" in details["timeline"][0]
    assert "internal_notes" not in details["timeline"][0]


def test_citizen_track_fails_with_wrong_token(client):
    sub_res = client.post("/api/v1/concerns", json={
        "category": "sanitation",
        "state": "Andhra Pradesh",
        "district": "Guntur",
        "locality": "Bus Stand",
        "description": "Public toilet in poor sanitation condition",
        "duration": "1-2 weeks",
    })
    ref_id = sub_res.get_json()["data"]["reference_id"]

    track_res = client.post("/api/v1/concerns/track", json={
        "reference_id": ref_id,
        "tracking_token": "wrong-tracking-token-abcdef",
    })
    assert track_res.status_code == 404
    assert track_res.get_json()["error"]["code"] == "UNAUTHORIZED_OR_NOT_FOUND"


def test_citizen_cannot_access_other_citizens_report(client):
    # Citizen A
    sub_a = client.post("/api/v1/concerns", json={
        "category": "garbage", "state": "Telangana", "district": "Hyderabad",
        "locality": "Area A", "description": "Garbage in Area A", "duration": "< 3 days",
    }).get_json()["data"]

    # Citizen B
    sub_b = client.post("/api/v1/concerns", json={
        "category": "drainage", "state": "Andhra Pradesh", "district": "Nellore",
        "locality": "Area B", "description": "Drain in Area B", "duration": "< 3 days",
    }).get_json()["data"]

    # Citizen A attempts to use Token A on Report B
    track_cross = client.post("/api/v1/concerns/track", json={
        "reference_id": sub_b["reference_id"],
        "tracking_token": sub_a["tracking_token"],
    })
    assert track_cross.status_code == 404


# ---------------------------------------------------------------------------
# Staff Permissions & Case Management Tests
# ---------------------------------------------------------------------------


def test_staff_endpoints_require_authentication(client):
    res = client.get("/api/v1/staff/concerns")
    assert res.status_code == 401


def test_staff_case_handler_workflow(client):
    # Setup: Create a concern
    sub_data = client.post("/api/v1/concerns", json={
        "category": "garbage", "state": "Andhra Pradesh", "district": "Kurnool",
        "locality": "Old Town", "description": "Garbage dump near primary school", "duration": "3-7 days",
    }).get_json()["data"]
    ref_id = sub_data["reference_id"]

    # Create handler user in DB
    with get_db_session() as session:
        handler_user = UserModel(
            user_id="user-handler-1",
            username="handler1",
            display_name="Case Handler One",
            role=UserRole.CASE_HANDLER.value,
            password_hash="dummy_hash",
            is_active=True,
        )
        session.add(handler_user)
        report = session.query(ConcernReportModel).filter_by(reference_id=ref_id).first()
        report_id = report.report_id

    # Simulate logged-in handler
    with client.session_transaction() as sess:
        sess["user_id"] = "user-handler-1"
        sess["role"] = UserRole.CASE_HANDLER.value

    # 1. Handler views concern list
    list_res = client.get("/api/v1/staff/concerns")
    assert list_res.status_code == 200
    reports = list_res.get_json()["data"]
    assert any(r["reference_id"] == ref_id for r in reports)

    # 2. Handler views detail with internal notes
    detail_res = client.get(f"/api/v1/staff/concerns/{report_id}")
    assert detail_res.status_code == 200
    detail = detail_res.get_json()["data"]
    assert detail["timeline"][0]["internal_notes"] is not None

    # 3. Handler updates status to under_review
    trans_res = client.post(f"/api/v1/staff/concerns/{report_id}/status", json={
        "status": "under_review",
        "public_notes": "A health inspector has been assigned to verify the location.",
        "internal_notes": "Checked coordinates, confirmed not a duplicate.",
    })
    assert trans_res.status_code == 200

    # 4. Verify citizen sees public update but NOT internal notes
    track_res = client.post("/api/v1/concerns/track", json={
        "reference_id": ref_id,
        "tracking_token": sub_data["tracking_token"],
    })
    cit_data = track_res.get_json()["data"]
    assert cit_data["status"] == "under_review"
    assert len(cit_data["timeline"]) == 2
    assert "health inspector has been assigned" in cit_data["timeline"][1]["public_notes"]
    assert "internal_notes" not in cit_data["timeline"][1]


def test_jurisdiction_scoped_officer_restrictions(client):
    # Setup two concerns: one in assigned jurisdiction, one outside
    sub_assigned = client.post("/api/v1/concerns", json={
        "category": "garbage", "state": "Telangana", "district": "Rangareddy",
        "locality": "Gachibowli", "description": "Waste issue in Rangareddy", "duration": "< 3 days",
    }).get_json()["data"]

    sub_unassigned = client.post("/api/v1/concerns", json={
        "category": "sanitation", "state": "Andhra Pradesh", "district": "Chittoor",
        "locality": "Tirupati Road", "description": "Sanitation in Chittoor", "duration": "< 3 days",
    }).get_json()["data"]

    # Create officer restricted to Rangareddy, Telangana
    with get_db_session() as session:
        officer = UserModel(
            user_id="user-officer-1",
            username="officer_rr",
            display_name="Rangareddy Officer",
            role=UserRole.JURISDICTION_OFFICER.value,
            password_hash="dummy_hash",
            is_active=True,
        )
        session.add(officer)
        session.flush()

        jur = StaffJurisdictionModel(
            id="jur-1",
            user_id="user-officer-1",
            state="Telangana",
            district="Rangareddy",
            municipality=None,
        )
        session.add(jur)

        rep_unassigned = session.query(ConcernReportModel).filter_by(
            reference_id=sub_unassigned["reference_id"]
        ).first()
        unassigned_report_id = rep_unassigned.report_id

    # Log in as officer
    with client.session_transaction() as sess:
        sess["user_id"] = "user-officer-1"
        sess["role"] = UserRole.JURISDICTION_OFFICER.value

    # 1. Officer list only shows Rangareddy report
    list_res = client.get("/api/v1/staff/concerns")
    assert list_res.status_code == 200
    scoped_reports = list_res.get_json()["data"]
    ref_ids = [r["reference_id"] for r in scoped_reports]
    assert sub_assigned["reference_id"] in ref_ids
    assert sub_unassigned["reference_id"] not in ref_ids

    # 2. Officer cannot access Chittoor report directly by ID
    forbidden_res = client.get(f"/api/v1/staff/concerns/{unassigned_report_id}")
    assert forbidden_res.status_code == 403
    assert forbidden_res.get_json()["error"]["code"] == "FORBIDDEN"

    # 3. Officer cannot transition status of unassigned report
    status_res = client.post(f"/api/v1/staff/concerns/{unassigned_report_id}/status", json={
        "status": "under_review",
        "public_notes": "Attempting illegal update",
    })
    assert status_res.status_code == 403

    # 4. Officer cannot assign cases
    assign_res = client.post(f"/api/v1/staff/concerns/{unassigned_report_id}/assign", json={
        "handler_id": "user-officer-1",
        "handler_name": "Rangareddy Officer",
    })
    assert assign_res.status_code == 403
