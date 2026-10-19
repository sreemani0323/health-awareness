"""Reproducible and idempotent PostgreSQL bootstrap utility for HealthAware.

Initializes a clean or existing PostgreSQL database with:
- All 13 canonical health information sources.
- All 4 published topics.
- All 7 canonical published lessons with complete learning content, quiz cards, choices, and correct answers.
- 4 mosquito prevention chapters in canonical sequence (1, 2, 3, 4).
- Baseline demonstration accounts (admin, contributor, reviewer).

Idempotent: Never overwrites or deletes existing content, user-created drafts, or reviews.
Must be explicitly invoked; does NOT run automatically on Flask startup.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

# Ensure repo root is on sys.path and remove script directory to prevent shadowing stdlib platform
backend_dir = os.path.abspath(os.path.dirname(__file__))
while backend_dir in sys.path:
    sys.path.remove(backend_dir)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

if "platform" in sys.modules and not hasattr(sys.modules["platform"], "python_implementation"):
    del sys.modules["platform"]
import platform
from datetime import date, datetime

from backend.storage.db import (
    create_app_engine,
    get_database_url,
    get_db_session,
    init_db,
)
from backend.storage.postgres_models import (
    HealthSourceModel,
    LessonModel,
    LessonVersionModel,
    TopicModel,
    UserModel,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("bootstrap")

CURRICULUM_FILE = os.path.join(os.path.dirname(__file__), "canonical_curriculum.json")


def parse_date(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val).date()
    except Exception:
        return None


def bootstrap_database(database_url: str | None = None, curriculum_only: bool = False) -> dict[str, int]:
    """Bootstraps the canonical curriculum into the configured PostgreSQL database.
    
    If curriculum_only=True, seeds only sources, topics, lessons, and versions,
    skipping baseline demonstration user accounts.
    """
    target_url = database_url or get_database_url()
    if not target_url:
        raise ValueError("DATABASE_URL is not set. Please provide --database-url or set DATABASE_URL.")

    if not os.path.exists(CURRICULUM_FILE):
        raise FileNotFoundError(f"Canonical curriculum file not found at {CURRICULUM_FILE}")

    with open(CURRICULUM_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    engine = create_app_engine(target_url)
    init_db(engine)

    inserted = {
        "sources": 0,
        "topics": 0,
        "lessons": 0,
        "versions": 0,
        "users": 0,
    }

    with get_db_session(engine) as session:
        # 1. Health Sources
        for s in data.get("sources", []):
            existing = session.query(HealthSourceModel).filter_by(source_id=s["source_id"]).first()
            if not existing:
                src = HealthSourceModel(
                    source_id=s["source_id"],
                    title=s["title"],
                    publisher=s["publisher"],
                    url=s["url"],
                    publication_date=parse_date(s.get("publication_date")),
                    access_date=parse_date(s.get("access_date")),
                    jurisdiction=s.get("jurisdiction"),
                    metadata_notes=s.get("metadata_notes"),
                )
                session.add(src)
                inserted["sources"] += 1

        # 2. Topics
        for t in data.get("topics", []):
            existing = session.query(TopicModel).filter_by(topic_id=t["topic_id"]).first()
            if not existing:
                top = TopicModel(
                    topic_id=t["topic_id"],
                    title=t["title"],
                    url_slug=t["url_slug"],
                    description=t["description"],
                    display_order=t["display_order"],
                    status=t["status"],
                    cover_image_ref=t.get("cover_image_ref"),
                    cover_image_alt=t.get("cover_image_alt"),
                )
                session.add(top)
                inserted["topics"] += 1

        session.flush()

        # 3. Lessons
        for l in data.get("lessons", []):
            existing = session.query(LessonModel).filter_by(lesson_id=l["lesson_id"]).first()
            if not existing:
                les = LessonModel(
                    lesson_id=l["lesson_id"],
                    topic_id=l["topic_id"],
                    display_order=l["display_order"],
                    published_version_id=l.get("published_version_id"),
                    draft_version_id=l.get("draft_version_id"),
                )
                session.add(les)
                inserted["lessons"] += 1

        session.flush()

        # 4. Lesson Versions
        for v in data.get("versions", []):
            existing = session.query(LessonVersionModel).filter_by(version_id=v["version_id"]).first()
            if not existing:
                ver = LessonVersionModel(
                    version_id=v["version_id"],
                    lesson_id=v["lesson_id"],
                    version_number=v["version_number"],
                    title=v["title"],
                    summary=v["summary"],
                    language=v.get("language", "en"),
                    learning_objectives=v["learning_objectives"],
                    estimated_duration_minutes=v.get("estimated_duration_minutes", 5),
                    cards_json=v["cards"],
                    source_ids=v["source_ids"],
                    status=v["status"],
                    author_id=v.get("author_id"),
                    submitted_by=v.get("submitted_by"),
                    review_feedback=v.get("review_feedback"),
                )
                session.add(ver)
                inserted["versions"] += 1

        # 5. Baseline Users (skipped when curriculum_only=True)
        if not curriculum_only:
            for u in data.get("users", []):
                existing = session.query(UserModel).filter_by(user_id=u["user_id"]).first()
                if not existing:
                    usr = UserModel(
                        user_id=u["user_id"],
                        username=u["username"],
                        display_name=u["display_name"],
                        role=u["role"],
                        password_hash=u["password_hash"],
                        is_active=u.get("is_active", True),
                    )
                    session.add(usr)
                    inserted["users"] += 1

        session.commit()

    logger.info("Bootstrap complete: %s (curriculum_only=%s)", inserted, curriculum_only)
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Bootstrap canonical HealthAware curriculum into PostgreSQL")
    parser.add_argument("--database-url", type=str, help="Target PostgreSQL connection URL")
    parser.add_argument("--curriculum-only", action="store_true", help="Seed only canonical curriculum (sources, topics, lessons) without demo users")
    args = parser.parse_args()

    counts = bootstrap_database(args.database_url, curriculum_only=args.curriculum_only)
    print(f"\nBootstrap completed successfully:")
    for k, v in counts.items():
        print(f"  * {k.capitalize()}: {v} inserted")


if __name__ == "__main__":
    main()

