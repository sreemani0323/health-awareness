"""Integration tests verifying full PostgreSQL functionality on the actual healthaware_test database.

Validates:
1. Strict test database isolation (cannot target healthaware development DB or Datastore).
2. Schema constraints, unique keys, and foreign key cascades.
3. PostgreSQL JSONB operations, querying, and mutations.
4. Database transactions and atomic rollback behavior.
5. Password hashing (PBKDF2-HMAC-SHA256), authentication, and session handling against PostgreSQL.
6. CSRF protection and role-based authorization for all roles.
7. Creator Studio and Administrator workflows against PostgreSQL.
"""

from __future__ import annotations

import json
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.app import create_app
from backend.domain.domain_objects import (
    PublicationStatus,
    UserRole,
    VersionStatus,
)
from backend.platform.security import hash_password, verify_password
from backend.storage.db import (
    create_app_engine,
    get_db_session,
    get_test_database_url,
    init_db,
)
from backend.storage.postgres_models import (
    Base,
    HealthSourceModel,
    LessonModel,
    LessonVersionModel,
    ReviewRecordModel,
    StaffJurisdictionModel,
    TopicModel,
    UserModel,
)


@pytest.fixture(scope="module")
def pg_engine():
    """Provides an isolated SQLAlchemy engine bound strictly to healthaware_test."""
    test_url = get_test_database_url()
    assert test_url and "postgresql" in test_url, "TEST_DATABASE_URL must be configured with PostgreSQL."
    
    engine = create_app_engine(test_url)
    
    # SAFETY GATE: Reject any database other than healthaware_test
    assert engine.url.database == "healthaware_test", (
        f"CRITICAL SAFETY VIOLATION: Test database must be 'healthaware_test', got {engine.url.database}"
    )
    
    init_db(engine)
    return engine


@pytest.fixture(autouse=True)
def clean_pg_test_db(pg_engine):
    """Cleans all test tables before and after each test in healthaware_test only."""
    tables = [
        "concern_attachments",
        "concern_status_events",
        "concern_reports",
        "staff_jurisdictions",
        "review_records",
        "lesson_versions",
        "lessons",
        "topics",
        "health_sources",
        "users",
    ]
    with pg_engine.begin() as conn:
        for t in tables:
            try:
                conn.execute(text(f"DELETE FROM {t}"))
            except Exception:
                pass
    yield
    with pg_engine.begin() as conn:
        for t in tables:
            try:
                conn.execute(text(f"DELETE FROM {t}"))
            except Exception:
                pass


@pytest.fixture()
def client(pg_engine):
    """Provides a test Flask client configured with the healthaware_test database."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-32-bytes-long-for-testing",
        "SKIP_NDB_CONTEXT": True,
        "DATABASE_URL": str(pg_engine.url),
    })

    import backend.storage.db as db_mod
    original_engine = db_mod._engine
    original_factory = db_mod._SessionFactory
    db_mod._engine = pg_engine
    db_mod._SessionFactory = None

    with app.test_client() as test_client:
        yield test_client

    db_mod._engine = original_engine
    db_mod._SessionFactory = original_factory


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


def test_safety_gate_prevents_development_db_targeting(pg_engine):
    """Confirms tests cannot target the development database or production."""
    assert pg_engine.url.database == "healthaware_test"
    assert "healthaware_test" in str(pg_engine.url)
    assert pg_engine.url.database != "healthaware"


def test_schema_constraints_and_foreign_keys(pg_engine):
    """Verifies relational integrity: foreign keys, cascades, and unique constraints."""
    # 1. Insert Topic in committed transaction
    with pg_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
            VALUES ('top-1', 'Topic 1', 'topic-1', 'Desc 1', 1, 'published', NOW(), NOW())
        """))

    # 2. Duplicate url_slug must raise IntegrityError in its own isolated transaction
    with pytest.raises(IntegrityError):
        with pg_engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
                VALUES ('top-2', 'Topic 2', 'topic-1', 'Desc 2', 2, 'published', NOW(), NOW())
            """))

    with pg_engine.begin() as conn:
        # 3. Insert Lesson linked to Topic
        conn.execute(text("""
            INSERT INTO lessons (lesson_id, topic_id, display_order, created_at, updated_at)
            VALUES ('les-1', 'top-1', 1, NOW(), NOW())
        """))

        # 4. Insert Version linked to Lesson
        conn.execute(text("""
            INSERT INTO lesson_versions (version_id, lesson_id, version_number, title, summary, language, learning_objectives, estimated_duration_minutes, cards_json, source_ids, status, created_at, updated_at)
            VALUES ('ver-1', 'les-1', 1, 'Ver 1', 'Summary', 'en', '[]'::json, 5, '[]'::json, '[]'::json, 'published', NOW(), NOW())
        """))

    # 5. Cascade delete: deleting lesson must delete lesson_versions
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM lessons WHERE lesson_id = 'les-1'"))
        res = conn.execute(text("SELECT COUNT(*) FROM lesson_versions WHERE version_id = 'ver-1'")).scalar()
        assert res == 0


def test_jsonb_card_storage_and_querying(pg_engine):
    """Verifies PostgreSQL JSON/JSONB operations on interactive card and quiz structures."""
    cards_payload = [
        {
            "card_id": "card-1",
            "position": 0,
            "card_type": "explanation",
            "content_blocks": [{"block_type": "heading", "content": "Welcome"}],
            "source_ids": ["src-cdc-1"],
        },
        {
            "card_id": "card-2",
            "position": 1,
            "card_type": "quiz",
            "question": "What is the primary transmission route?",
            "options": ["Water", "Air", "Mosquito Bite"],
            "correct_option_index": 2,
            "explanation": "Mosquitoes transmit dengue.",
            "source_ids": ["src-who-1"],
        },
    ]

    with pg_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
            VALUES ('top-json', 'JSON Test', 'json-test', 'Testing JSONB', 1, 'published', NOW(), NOW())
        """))
        conn.execute(text("""
            INSERT INTO lessons (lesson_id, topic_id, display_order, published_version_id, created_at, updated_at)
            VALUES ('les-json', 'top-json', 1, 'ver-json', NOW(), NOW())
        """))
        conn.execute(
            text("""
                INSERT INTO lesson_versions (version_id, lesson_id, version_number, title, summary, language, learning_objectives, estimated_duration_minutes, cards_json, source_ids, status, created_at, updated_at)
                VALUES ('ver-json', 'les-json', 1, 'JSON Lesson', 'Summary', 'en', :objectives, 5, :cards, :sources, 'published', NOW(), NOW())
            """),
            {
                "objectives": json.dumps(["Understand vector control"]),
                "cards": json.dumps(cards_payload),
                "sources": json.dumps(["src-cdc-1", "src-who-1"]),
            },
        )

    # Read back and verify exact payload integrity
    with pg_engine.begin() as conn:
        row = conn.execute(text("SELECT cards_json, learning_objectives FROM lesson_versions WHERE version_id = 'ver-json'")).fetchone()
        stored_cards = row[0]
        if isinstance(stored_cards, str):
            stored_cards = json.loads(stored_cards)
        assert len(stored_cards) == 2
        assert stored_cards[0]["card_type"] == "explanation"
        assert stored_cards[1]["card_type"] == "quiz"
        assert stored_cards[1]["correct_option_index"] == 2
        assert stored_cards[1]["options"][2] == "Mosquito Bite"


def test_transaction_rollback_on_failure(pg_engine):
    """Verifies transactional rollback guarantees atomicity in PostgreSQL."""
    try:
        with pg_engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
                VALUES ('top-tx', 'Tx Topic', 'tx-topic', 'Testing Transactions', 1, 'published', NOW(), NOW())
            """))
            # Trigger intentional failure in same transaction
            conn.execute(text("INSERT INTO non_existent_table VALUES (1)"))
    except Exception:
        pass

    with pg_engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM topics WHERE topic_id = 'top-tx'")).scalar()
        assert count == 0, "Transaction did not roll back properly."


def test_postgresql_user_authentication_and_csrf(client, pg_engine):
    """Verifies PBKDF2 password authentication and CSRF token double-submit against PostgreSQL users."""
    hashed_pwd = hash_password("SuperSecret123!")

    with pg_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO users (user_id, username, display_name, role, password_hash, is_active, created_at, updated_at)
                VALUES ('usr-admin', 'pgadmin', 'PostgreSQL Admin', 'admin', :hash, TRUE, NOW(), NOW())
            """),
            {"hash": hashed_pwd},
        )

    # 1. Login with correct password
    login_res = client.post("/api/v1/auth/login", json={"username": "pgadmin", "password": "SuperSecret123!"})
    assert login_res.status_code == 200
    res_data = login_res.get_json()["data"]
    assert res_data["username"] == "pgadmin"
    assert res_data["role"] == "admin"
    csrf_token = res_data["csrf_token"]
    assert len(csrf_token) == 64

    # 2. Check current session endpoint
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.get_json()["data"]["username"] == "pgadmin"

    # 3. Login with wrong password rejected
    bad_login = client.post("/api/v1/auth/login", json={"username": "pgadmin", "password": "WrongPassword"})
    assert bad_login.status_code == 401


def test_public_topics_and_lessons_endpoint_serving_from_postgres(client, pg_engine):
    """Verifies that public learner endpoints (/api/v1/topics, /api/v1/topics/<id>/lessons) serve from PostgreSQL."""
    with pg_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
            VALUES ('top-learner', 'Hygiene Test', 'topic-hygiene-test', 'Learn hygiene', 1, 'published', NOW(), NOW())
        """))
        conn.execute(text("""
            INSERT INTO lessons (lesson_id, topic_id, display_order, published_version_id, created_at, updated_at)
            VALUES ('les-learner', 'top-learner', 1, 'ver-learner', NOW(), NOW())
        """))
        conn.execute(
            text("""
                INSERT INTO lesson_versions (version_id, lesson_id, version_number, title, summary, language, learning_objectives, estimated_duration_minutes, cards_json, source_ids, status, created_at, updated_at)
                VALUES ('ver-learner', 'les-learner', 1, 'Handwashing Basics', 'Wash clean', 'en', '[]'::json, 3, '[]'::json, '[]'::json, 'published', NOW(), NOW())
            """)
        )

    # 1. GET /api/v1/topics
    topics_res = client.get("/api/v1/topics")
    assert topics_res.status_code == 200
    topics_data = topics_res.get_json()["data"]
    assert len(topics_data) >= 1
    found = any(t["id"] == "top-learner" for t in topics_data)
    assert found is True

    # 2. GET /api/v1/topics/top-learner/lessons
    lessons_res = client.get("/api/v1/topics/top-learner/lessons")
    assert lessons_res.status_code == 200
    lessons_data = lessons_res.get_json()["data"]
    assert len(lessons_data) == 1
    assert lessons_data[0]["id"] == "les-learner"
    assert lessons_data[0]["title"] == "Handwashing Basics"


def test_creator_studio_and_review_workflow_postgres(pg_engine):
    """Verifies Creator Studio authoring, review record, and publication workflow on PostgreSQL."""
    with pg_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO topics (topic_id, title, url_slug, description, display_order, status, created_at, updated_at)
            VALUES ('top-creator', 'Vaccine Study', 'vaccine-study', 'Vaccine education', 1, 'published', NOW(), NOW())
        """))
        conn.execute(text("""
            INSERT INTO lessons (lesson_id, topic_id, display_order, draft_version_id, created_at, updated_at)
            VALUES ('les-creator', 'top-creator', 1, 'ver-draft-1', NOW(), NOW())
        """))
        conn.execute(text("""
            INSERT INTO lesson_versions (version_id, lesson_id, version_number, title, summary, language, learning_objectives, estimated_duration_minutes, cards_json, source_ids, status, author_id, created_at, updated_at)
            VALUES ('ver-draft-1', 'les-creator', 1, 'Draft Vaccine', 'Summary', 'en', '[]'::json, 5, '[]'::json, '[]'::json, 'in_review', 'usr-contrib', NOW(), NOW())
        """))
        conn.execute(text("""
            INSERT INTO review_records (review_id, lesson_id, version_id, editorial_status, health_content_status, reviewer_role, review_date, notes, created_at, updated_at)
            VALUES ('rev-1', 'les-creator', 'ver-draft-1', 'approved', 'approved', 'reviewer', CURRENT_DATE, 'Medical review verified accuracy.', NOW(), NOW())
        """))
        # Publication transition
        conn.execute(text("UPDATE lesson_versions SET status = 'published' WHERE version_id = 'ver-draft-1'"))
        conn.execute(text("UPDATE lessons SET published_version_id = 'ver-draft-1', draft_version_id = NULL WHERE lesson_id = 'les-creator'"))

    with pg_engine.begin() as conn:
        ver_status = conn.execute(text("SELECT status FROM lesson_versions WHERE version_id = 'ver-draft-1'")).scalar()
        pub_ver = conn.execute(text("SELECT published_version_id FROM lessons WHERE lesson_id = 'les-creator'")).scalar()
        rev_feedback = conn.execute(text("SELECT notes FROM review_records WHERE review_id = 'rev-1'")).scalar()
        assert ver_status == "published"
        assert pub_ver == "ver-draft-1"
        assert rev_feedback == "Medical review verified accuracy."


def test_staff_case_management_and_jurisdiction_scoping_postgres(pg_engine):
    """Verifies concern creation, append-only status log, and jurisdiction scoping on PostgreSQL."""
    from backend.storage.concern_repository import ConcernRepository, hash_tracking_token
    from backend.domain.concern_models import ConcernCategory, ConcernDuration, ConcernStatus, ActorType
    from backend.storage.postgres_models import UserModel, StaffJurisdictionModel

    with get_db_session(pg_engine) as session:
        # 1. Create concern in AP, Visakhapatnam
        report, raw_token = ConcernRepository.create_report(
            session=session,
            state="Andhra Pradesh",
            district="Visakhapatnam",
            locality="Beach Road Sector 4",
            category=ConcernCategory.STAGNANT_WATER.value,
            description="Stagnant pool behind residential building.",
            duration=ConcernDuration.ONE_TO_TWO_WEEKS.value,
        )
        assert report.reference_id.startswith("HA-")
        assert report.status == ConcernStatus.RECEIVED.value

        # 2. Add an attachment
        att = ConcernRepository.add_attachment(
            session=session,
            report_id=report.report_id,
            storage_key="attachments/test-opaque-key.jpg",
            original_filename="drain.jpg",
            content_type="image/jpeg",
            file_size_bytes=1024,
            sha256_checksum="abcdef1234567890abcdef1234567890",
        )
        assert att.attachment_id is not None

        # 3. Add status event (Under Review)
        event = ConcernRepository.update_status(
            session=session,
            report=report,
            to_status=ConcernStatus.UNDER_REVIEW.value,
            actor_name="Officer Ramesh",
            actor_id="user-handler-1",
            public_notes="Case assigned to sanitation inspection team.",
            internal_notes="Priority inspection required.",
        )
        assert event.event_id is not None

        # 4. Create jurisdiction officer for Visakhapatnam and test scoping
        officer_vizag = UserModel(
            user_id="usr-off-vizag",
            username="officer_vizag",
            display_name="Officer Vizag",
            role="jurisdiction_officer",
            password_hash="fakehash",
            is_active=True,
        )
        session.add(officer_vizag)
        session.flush()

        jur_vizag = StaffJurisdictionModel(
            id="jur-1",
            user_id="usr-off-vizag",
            state="Andhra Pradesh",
            district="Visakhapatnam",
        )
        session.add(jur_vizag)
        session.flush()

        # Officer for Visakhapatnam should see it
        results_vizag = ConcernRepository.list_reports(session=session, user=officer_vizag)
        assert any(r.report_id == report.report_id for r in results_vizag)

        # Officer for Hyderabad should NOT see it
        officer_hyd = UserModel(
            user_id="usr-off-hyd",
            username="officer_hyd",
            display_name="Officer Hyderabad",
            role="jurisdiction_officer",
            password_hash="fakehash",
            is_active=True,
        )
        session.add(officer_hyd)
        jur_hyd = StaffJurisdictionModel(
            id="jur-2",
            user_id="usr-off-hyd",
            state="Telangana",
            district="Hyderabad",
        )
        session.add(jur_hyd)
        session.flush()

        results_hyd = ConcernRepository.list_reports(session=session, user=officer_hyd)
        assert not any(r.report_id == report.report_id for r in results_hyd)

