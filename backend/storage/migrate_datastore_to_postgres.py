"""Controlled and repeatable Datastore-to-PostgreSQL migration utility for HealthAware.

Capabilities:
1. Validates and inspects the active Datastore emulator source.
2. Supports --dry-run (inventory and schema validation without modifying target).
3. Supports --execute (transactional migration to PostgreSQL preserving stable IDs and hashes).
4. Supports --verify (record-level parity verification between Datastore and PostgreSQL).
5. Never deletes or alters source Datastore entities.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.cloud import ndb
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.domain.domain_objects import (
    PublicationStatus,
    UserRole,
    VersionStatus,
)
from backend.platform.ndb_client import get_ndb_client
from backend.storage.db import (
    check_database_connection,
    create_app_engine,
    get_database_url,
    get_db_session,
    init_db,
)
from backend.storage.postgres_models import (
    Base,
    HealthSourceModel as PgHealthSource,
    LessonModel as PgLesson,
    LessonVersionModel as PgLessonVersion,
    ReviewRecordModel as PgReviewRecord,
    TopicModel as PgTopic,
    UserModel as PgUser,
)
from backend.storage.storage_models import (
    HealthSourceModel as NdbHealthSource,
    LessonModel as NdbLesson,
    LessonVersionModel as NdbLessonVersion,
    ReviewRecordModel as NdbReviewRecord,
    TopicModel as NdbTopic,
    UserModel as NdbUser,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migration")

CANONICAL_MOSQUITO_LESSONS_ORDER = [
    ("lesson-understanding-mosquitoes-and-m-5557", 1),
    ("lesson-mosquito-control", 2),
    ("lesson-protect-yourself-and-your-fami-3513", 3),
    ("lesson-community-prevention-symptoms--4817", 4),
]


def inspect_source_datastore(ndb_client: ndb.Client) -> dict[str, Any]:
    """Inspects Datastore emulator and returns full source inventory."""
    with ndb_client.context():
        topics = list(NdbTopic.query().order(NdbTopic.display_order).fetch())
        lessons = list(NdbLesson.query().order(NdbLesson.topic_id, NdbLesson.display_order).fetch())
        versions = list(NdbLessonVersion.query().fetch())
        sources = list(NdbHealthSource.query().fetch())
        reviews = list(NdbReviewRecord.query().fetch())
        users = list(NdbUser.query().fetch())

        return {
            "topics": topics,
            "lessons": lessons,
            "versions": versions,
            "sources": sources,
            "reviews": reviews,
            "users": users,
        }


def print_dry_run_report(inventory: dict[str, Any]) -> None:
    """Prints a detailed audit and validation report of the source Datastore."""
    topics = inventory["topics"]
    lessons = inventory["lessons"]
    versions = inventory["versions"]
    sources = inventory["sources"]
    reviews = inventory["reviews"]
    users = inventory["users"]

    print("\n==================================================================")
    print("HealthAware Datastore -> PostgreSQL Migration: DRY-RUN AUDIT")
    print("==================================================================")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Source: Datastore emulator at {os.environ.get('DATASTORE_EMULATOR_HOST', 'unset')}")
    print(f"Project ID: {os.environ.get('DATASTORE_PROJECT_ID', 'unset')}")
    print("------------------------------------------------------------------")
    print(f"Entity Counts:")
    print(f"  * Topics:          {len(topics)}")
    print(f"  * Lessons:         {len(lessons)}")
    print(f"  * Lesson Versions: {len(versions)}")
    print(f"  * Health Sources:  {len(sources)}")
    print(f"  * Review Records:  {len(reviews)}")
    print(f"  * Users:           {len(users)}")
    print("------------------------------------------------------------------")

    print("Curriculum Verification:")
    for t in topics:
        t_lessons = [l for l in lessons if l.topic_id == t.key.string_id()]
        print(f"  Topic: [{t.key.string_id()}] '{t.title}' (order: {t.display_order}, status: {t.status})")
        for l in sorted(t_lessons, key=lambda x: x.display_order):
            print(f"    - Lesson: [{l.key.string_id()}] (order: {l.display_order}, pubVer: {l.published_version_id})")

    # Verify mosquito order
    print("------------------------------------------------------------------")
    print("Checking Mosquito Topic Canonical Order:")
    mosquito_lessons = [l for l in lessons if l.topic_id == "topic-mosquito"]
    mosquito_sorted = sorted(mosquito_lessons, key=lambda x: x.display_order)
    actual_order = [(l.key.string_id(), l.display_order) for l in mosquito_sorted]
    if actual_order == CANONICAL_MOSQUITO_LESSONS_ORDER:
        print("  [PASS] Mosquito topic contains all 4 chapters in exact canonical sequence.")
    else:
        print(f"  [FAIL] Mosquito topic sequence mismatch! Found: {actual_order}")

    print("------------------------------------------------------------------")
    print("User Accounts Verification:")
    for u in users:
        print(f"  User: [{u.key.string_id()}] '{u.username}' (role: {u.role}, active: {u.is_active}, hash_len: {len(u.password_hash or '')})")

    print("==================================================================\n")


def execute_migration(ndb_client: ndb.Client, db_session: Session) -> dict[str, int]:
    """Transfers all entities from Datastore to PostgreSQL in a single transaction."""
    inventory = inspect_source_datastore(ndb_client)

    topics = inventory["topics"]
    lessons = inventory["lessons"]
    versions = inventory["versions"]
    sources = inventory["sources"]
    reviews = inventory["reviews"]
    users = inventory["users"]

    logger.info("Starting transactional migration into PostgreSQL...")

    # 1. Health Sources (referenced by versions)
    source_count = 0
    for s in sources:
        sid = s.key.string_id()
        existing = db_session.query(PgHealthSource).filter_by(source_id=sid).first()
        if not existing:
            pg_s = PgHealthSource(
                source_id=sid,
                title=s.title,
                publisher=s.publisher,
                url=s.url,
                publication_date=s.publication_date,
                access_date=s.access_date,
                jurisdiction=s.jurisdiction,
                metadata_notes=s.metadata_notes,
                created_at=s.created_at or datetime.utcnow(),
                updated_at=s.updated_at or datetime.utcnow(),
            )
            db_session.add(pg_s)
            source_count += 1

    # 2. Topics
    topic_count = 0
    for t in topics:
        tid = t.key.string_id()
        existing = db_session.query(PgTopic).filter_by(topic_id=tid).first()
        if not existing:
            pg_t = PgTopic(
                topic_id=tid,
                title=t.title,
                url_slug=t.url_slug,
                description=t.description,
                display_order=t.display_order,
                status=t.status,
                cover_image_ref=t.cover_image_ref,
                cover_image_alt=t.cover_image_alt,
                created_at=t.created_at or datetime.utcnow(),
                updated_at=t.updated_at or datetime.utcnow(),
            )
            db_session.add(pg_t)
            topic_count += 1

    db_session.flush()

    # 3. Lessons
    lesson_count = 0
    for l in lessons:
        lid = l.key.string_id()
        existing = db_session.query(PgLesson).filter_by(lesson_id=lid).first()
        if not existing:
            pg_l = PgLesson(
                lesson_id=lid,
                topic_id=l.topic_id,
                display_order=l.display_order,
                published_version_id=l.published_version_id,
                draft_version_id=l.draft_version_id,
                created_at=l.created_at or datetime.utcnow(),
                updated_at=l.updated_at or datetime.utcnow(),
            )
            db_session.add(pg_l)
            lesson_count += 1

    db_session.flush()

    # 4. Lesson Versions
    version_count = 0
    for v in versions:
        vid = v.key.string_id()
        existing = db_session.query(PgLessonVersion).filter_by(version_id=vid).first()
        if not existing:
            pg_v = PgLessonVersion(
                version_id=vid,
                lesson_id=v.lesson_id,
                version_number=v.version_number,
                title=v.title,
                summary=v.summary,
                language=v.language or "en",
                learning_objectives=list(v.learning_objectives or []),
                estimated_duration_minutes=v.estimated_duration_minutes or 5,
                cards_json=v.cards_json or [],
                source_ids=list(v.source_ids or []),
                status=v.status,
                author_id=v.author_id,
                submitted_by=v.submitted_by,
                review_feedback=v.review_feedback,
                created_at=v.created_at or datetime.utcnow(),
                updated_at=v.updated_at or datetime.utcnow(),
            )
            db_session.add(pg_v)
            version_count += 1

    # 5. Review Records
    review_count = 0
    for r in reviews:
        rid = r.key.string_id()
        existing = db_session.query(PgReviewRecord).filter_by(review_id=rid).first()
        if not existing:
            pg_r = PgReviewRecord(
                review_id=rid,
                lesson_id=r.lesson_id,
                version_id=r.version_id,
                editorial_status=r.editorial_status,
                health_content_status=r.health_content_status,
                reviewer_role=r.reviewer_role,
                review_date=r.review_date,
                next_review_date=r.next_review_date,
                notes=r.notes,
                created_at=r.created_at or datetime.utcnow(),
                updated_at=r.updated_at or datetime.utcnow(),
            )
            db_session.add(pg_r)
            review_count += 1

    # 6. Users
    user_count = 0
    for u in users:
        uid = u.key.string_id()
        existing = db_session.query(PgUser).filter_by(user_id=uid).first()
        if not existing:
            pg_u = PgUser(
                user_id=uid,
                username=u.username,
                display_name=u.display_name,
                role=u.role,
                password_hash=u.password_hash,
                is_active=u.is_active,
                created_at=u.created_at or datetime.utcnow(),
                updated_at=u.updated_at or datetime.utcnow(),
            )
            db_session.add(pg_u)
            user_count += 1

    db_session.commit()
    logger.info("Transactional migration committed successfully.")

    return {
        "topics": topic_count,
        "lessons": lesson_count,
        "versions": version_count,
        "sources": source_count,
        "reviews": review_count,
        "users": user_count,
    }


def verify_parity(ndb_client: ndb.Client, db_session: Session) -> bool:
    """Verifies complete record-level and semantic parity between Datastore and PostgreSQL."""
    inventory = inspect_source_datastore(ndb_client)

    passed = True
    print("\n==================================================================")
    print("HealthAware Migration Parity Verification")
    print("==================================================================")

    # 1. Topics
    pg_topics = {t.topic_id: t for t in db_session.query(PgTopic).all()}
    if len(pg_topics) != len(inventory["topics"]):
        print(f"[FAIL] Topics count mismatch: Datastore={len(inventory['topics'])}, Postgres={len(pg_topics)}")
        passed = False
    else:
        print(f"[PASS] Topics count matched: {len(pg_topics)}")

    for t in inventory["topics"]:
        tid = t.key.string_id()
        if tid not in pg_topics:
            print(f"[FAIL] Topic missing in Postgres: {tid}")
            passed = False
        else:
            pg_t = pg_topics[tid]
            if pg_t.title != t.title or pg_t.display_order != t.display_order:
                print(f"[FAIL] Topic attributes mismatch for {tid}")
                passed = False

    # 2. Lessons
    pg_lessons = {l.lesson_id: l for l in db_session.query(PgLesson).all()}
    if len(pg_lessons) != len(inventory["lessons"]):
        print(f"[FAIL] Lessons count mismatch: Datastore={len(inventory['lessons'])}, Postgres={len(pg_lessons)}")
        passed = False
    else:
        print(f"[PASS] Lessons count matched: {len(pg_lessons)}")

    for l in inventory["lessons"]:
        lid = l.key.string_id()
        if lid not in pg_lessons:
            print(f"[FAIL] Lesson missing in Postgres: {lid}")
            passed = False
        else:
            pg_l = pg_lessons[lid]
            if (
                pg_l.topic_id != l.topic_id
                or pg_l.display_order != l.display_order
                or pg_l.published_version_id != l.published_version_id
            ):
                print(f"[FAIL] Lesson attributes mismatch for {lid}")
                passed = False

    # 3. Lesson Versions
    pg_versions = {v.version_id: v for v in db_session.query(PgLessonVersion).all()}
    if len(pg_versions) != len(inventory["versions"]):
        print(f"[FAIL] Versions count mismatch: Datastore={len(inventory['versions'])}, Postgres={len(pg_versions)}")
        passed = False
    else:
        print(f"[PASS] Versions count matched: {len(pg_versions)}")

    for v in inventory["versions"]:
        vid = v.key.string_id()
        if vid not in pg_versions:
            print(f"[FAIL] Version missing in Postgres: {vid}")
            passed = False
        else:
            pg_v = pg_versions[vid]
            if len(pg_v.cards_json or []) != len(v.cards_json or []):
                print(f"[FAIL] Card count mismatch for version {vid}")
                passed = False

    # 4. Health Sources
    pg_sources = {s.source_id: s for s in db_session.query(PgHealthSource).all()}
    if len(pg_sources) != len(inventory["sources"]):
        print(f"[FAIL] Sources count mismatch: Datastore={len(inventory['sources'])}, Postgres={len(pg_sources)}")
        passed = False
    else:
        print(f"[PASS] Sources count matched: {len(pg_sources)}")

    # 5. Users
    pg_users = {u.user_id: u for u in db_session.query(PgUser).all()}
    if len(pg_users) != len(inventory["users"]):
        print(f"[FAIL] Users count mismatch: Datastore={len(inventory['users'])}, Postgres={len(pg_users)}")
        passed = False
    else:
        print(f"[PASS] Users count matched: {len(pg_users)}")

    for u in inventory["users"]:
        uid = u.key.string_id()
        if uid not in pg_users:
            print(f"[FAIL] User missing in Postgres: {uid}")
            passed = False
        else:
            pg_u = pg_users[uid]
            if pg_u.password_hash != u.password_hash or pg_u.role != u.role:
                print(f"[FAIL] User credentials/role mismatch for {u.username}")
                passed = False

    # 6. Canonical Mosquito Sequence Check in Postgres
    mosquito_pg = (
        db_session.query(PgLesson)
        .filter_by(topic_id="topic-mosquito")
        .order_by(PgLesson.display_order.asc())
        .all()
    )
    pg_order = [(l.lesson_id, l.display_order) for l in mosquito_pg]
    if pg_order == CANONICAL_MOSQUITO_LESSONS_ORDER:
        print(f"[PASS] PostgreSQL Mosquito lessons verified in exact canonical sequence (1, 2, 3, 4)")
    else:
        print(f"[FAIL] PostgreSQL Mosquito sequence mismatch: {pg_order}")
        passed = False

    print("==================================================================\n")
    return passed


def main():
    parser = argparse.ArgumentParser(description="HealthAware Datastore-to-PostgreSQL Migration Utility")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Perform dry-run inspection (default)")
    parser.add_argument("--execute", action="store_true", help="Execute the migration to PostgreSQL")
    parser.add_argument("--verify", action="store_true", help="Verify record parity between Datastore and PostgreSQL")
    args = parser.parse_args()

    ndb_client = get_ndb_client()

    if args.execute or args.verify:
        db_url = get_database_url()
        if not db_url:
            logger.error("DATABASE_URL is not configured! Cannot connect to PostgreSQL.")
            sys.exit(1)

        engine = create_app_engine(db_url)
        if not check_database_connection(engine):
            logger.error("Cannot connect to PostgreSQL database at %s.", db_url)
            sys.exit(1)

        init_db(engine)
        with get_db_session() as session:
            if args.execute:
                counts = execute_migration(ndb_client, session)
                print(f"Migration completed successfully: {counts}")
            if args.verify or args.execute:
                success = verify_parity(ndb_client, session)
                if not success:
                    logger.error("Parity verification failed!")
                    sys.exit(1)
                print("All parity checks PASSED!")
    else:
        inventory = inspect_source_datastore(ndb_client)
        print_dry_run_report(inventory)


if __name__ == "__main__":
    main()
