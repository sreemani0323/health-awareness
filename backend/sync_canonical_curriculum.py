"""Idempotent sync utility to publish the canonical curriculum to PostgreSQL and Datastore.

Safely inserts or updates:
- 19 Health Sources
- 4 Canonical Topics
- 20 Canonical Lessons (with exact display_order and published_version_id)
- 20 Published Lesson Versions (with rich cards, dialogues, interactions, and quizzes)

Guarantees:
- Never drops or resets tables.
- Preserves all existing user accounts, credentials, MFA secrets, and sessions.
- Preserves all citizen concern reports, staff applications, and review records.
- Preserves all learner progress records.
- Idempotent: can be safely executed repeatedly in local, test, or production environments.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime

backend_dir = os.path.abspath(os.path.dirname(__file__))
while backend_dir in sys.path:
    sys.path.remove(backend_dir)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

if "platform" in sys.modules and not hasattr(sys.modules["platform"], "python_implementation"):
    del sys.modules["platform"]

from backend.storage.db import create_app_engine, get_database_url, get_db_session, init_db
from backend.storage.postgres_models import (
    HealthSourceModel,
    LessonModel,
    LessonVersionModel,
    TopicModel,
)
from backend.domain.domain_objects import (
    HealthSource,
    Lesson,
    LessonVersion,
    PublicationStatus,
    Topic,
    VersionStatus,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_curriculum")

CURRICULUM_FILE = os.path.join(os.path.dirname(__file__), "canonical_curriculum.json")


def parse_date(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val).date()
    except Exception:
        return None


def sync_database(database_url: str | None = None) -> dict[str, dict[str, int]]:
    target_url = database_url or get_database_url()
    if not target_url:
        raise ValueError("DATABASE_URL is not set. Please provide --database-url or set DATABASE_URL.")

    if not os.path.exists(CURRICULUM_FILE):
        raise FileNotFoundError(f"Canonical curriculum file not found at {CURRICULUM_FILE}")

    with open(CURRICULUM_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    engine = create_app_engine(target_url)
    init_db(engine)

    stats = {
        "sources": {"inserted": 0, "updated": 0},
        "topics": {"inserted": 0, "updated": 0},
        "lessons": {"inserted": 0, "updated": 0},
        "versions": {"inserted": 0, "updated": 0},
    }

    with get_db_session(engine) as session:
        # 1. Health Sources
        for s in data.get("sources", []):
            existing = session.query(HealthSourceModel).filter_by(source_id=s["source_id"]).first()
            if existing:
                existing.title = s["title"]
                existing.publisher = s["publisher"]
                existing.url = s["url"]
                existing.publication_date = parse_date(s.get("publication_date"))
                existing.access_date = parse_date(s.get("access_date"))
                existing.jurisdiction = s.get("jurisdiction")
                existing.metadata_notes = s.get("metadata_notes")
                stats["sources"]["updated"] += 1
            else:
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
                stats["sources"]["inserted"] += 1

        session.flush()

        # 2. Topics
        for t in data.get("topics", []):
            existing = session.query(TopicModel).filter_by(topic_id=t["topic_id"]).first()
            if existing:
                existing.title = t["title"]
                existing.url_slug = t["url_slug"]
                existing.description = t["description"]
                existing.display_order = t["display_order"]
                existing.status = t["status"]
                existing.cover_image_ref = t.get("cover_image_ref")
                existing.cover_image_alt = t.get("cover_image_alt")
                stats["topics"]["updated"] += 1
            else:
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
                stats["topics"]["inserted"] += 1

        session.flush()

        # 3. Lessons
        for l in data.get("lessons", []):
            existing = session.query(LessonModel).filter_by(lesson_id=l["lesson_id"]).first()
            if existing:
                existing.topic_id = l["topic_id"]
                existing.display_order = l["display_order"]
                existing.published_version_id = l.get("published_version_id")
                stats["lessons"]["updated"] += 1
            else:
                les = LessonModel(
                    lesson_id=l["lesson_id"],
                    topic_id=l["topic_id"],
                    display_order=l["display_order"],
                    published_version_id=l.get("published_version_id"),
                    draft_version_id=l.get("draft_version_id"),
                )
                session.add(les)
                stats["lessons"]["inserted"] += 1

        session.flush()

        # 4. Lesson Versions
        for v in data.get("versions", []):
            existing = session.query(LessonVersionModel).filter_by(version_id=v["version_id"]).first()
            if existing:
                existing.title = v["title"]
                existing.summary = v["summary"]
                existing.language = v.get("language", "en")
                existing.learning_objectives = v["learning_objectives"]
                existing.estimated_duration_minutes = v.get("estimated_duration_minutes", 6)
                existing.cards_json = v["cards"]
                existing.source_ids = v["source_ids"]
                existing.status = v["status"]
                stats["versions"]["updated"] += 1
            else:
                ver = LessonVersionModel(
                    version_id=v["version_id"],
                    lesson_id=v["lesson_id"],
                    version_number=v["version_number"],
                    title=v["title"],
                    summary=v["summary"],
                    language=v.get("language", "en"),
                    learning_objectives=v["learning_objectives"],
                    estimated_duration_minutes=v.get("estimated_duration_minutes", 6),
                    cards_json=v["cards"],
                    source_ids=v["source_ids"],
                    status=v["status"],
                    author_id=v.get("author_id"),
                    submitted_by=v.get("submitted_by"),
                    review_feedback=v.get("review_feedback"),
                )
                session.add(ver)
                stats["versions"]["inserted"] += 1

        session.commit()

    logger.info("PostgreSQL curriculum synchronization complete: %s", stats)

    # Also synchronize to Datastore if emulator is running or configured
    if os.environ.get("DATASTORE_EMULATOR_HOST"):
        try:
            from backend.platform.ndb_client import get_ndb_client
            from backend.storage.storage_models import (
                HealthSourceModel as NdbSourceModel,
                LessonModel as NdbLessonModel,
                LessonVersionModel as NdbVersionModel,
                TopicModel as NdbTopicModel,
            )
            client = get_ndb_client()
            with client.context():
                for s in data.get("sources", []):
                    src_dom = HealthSource(
                        source_id=s["source_id"],
                        title=s["title"],
                        publisher=s["publisher"],
                        url=s["url"],
                        publication_date=parse_date(s.get("publication_date")),
                        access_date=parse_date(s.get("access_date")),
                        jurisdiction=s.get("jurisdiction"),
                    )
                    NdbSourceModel.from_domain(src_dom).put()

                for t in data.get("topics", []):
                    top_dom = Topic(
                        topic_id=t["topic_id"],
                        title=t["title"],
                        url_slug=t["url_slug"],
                        description=t["description"],
                        display_order=t["display_order"],
                        status=PublicationStatus(t["status"]),
                        cover_image_ref=t.get("cover_image_ref"),
                        cover_image_alt=t.get("cover_image_alt"),
                    )
                    NdbTopicModel.from_domain(top_dom).put()

                for l in data.get("lessons", []):
                    les_dom = Lesson(
                        lesson_id=l["lesson_id"],
                        topic_id=l["topic_id"],
                        display_order=l["display_order"],
                        published_version_id=l.get("published_version_id"),
                        draft_version_id=l.get("draft_version_id"),
                    )
                    NdbLessonModel.from_domain(les_dom).put()

                for v in data.get("versions", []):
                    cards = LessonVersion.cards_from_dicts(v["cards"])
                    ver_dom = LessonVersion(
                        version_id=v["version_id"],
                        lesson_id=v["lesson_id"],
                        version_number=v["version_number"],
                        title=v["title"],
                        summary=v["summary"],
                        language=v.get("language", "en"),
                        learning_objectives=v["learning_objectives"],
                        estimated_duration_minutes=v.get("estimated_duration_minutes", 6),
                        cards=cards,
                        source_ids=v["source_ids"],
                        status=VersionStatus(v["status"]),
                    )
                    NdbVersionModel.from_domain(ver_dom).put()
            logger.info("Datastore emulator NDB sync complete for all 20 lessons.")
        except Exception as e:
            logger.warning("Could not sync to Datastore emulator (non-critical): %s", e)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Synchronize canonical HealthAware curriculum into PostgreSQL and Datastore")
    parser.add_argument("--database-url", type=str, help="Target PostgreSQL connection URL (defaults to DATABASE_URL in environment)")
    args = parser.parse_args()

    import dotenv
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    stats = sync_database(args.database_url)
    print("\nCurriculum sync successful:")
    for entity, counts in stats.items():
        print(f"  * {entity.capitalize()}: {counts['inserted']} inserted, {counts['updated']} updated")


if __name__ == "__main__":
    main()
