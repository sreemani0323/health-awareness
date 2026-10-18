"""Purge test pollution and re-seed genuine HealthAware topics and lessons."""
import os
import sys

os.environ["DATASTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
os.environ["DATASTORE_PROJECT_ID"] = "health-awareness-local"

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from google.cloud import ndb

from backend.platform.ndb_client import get_ndb_client
from backend.storage.storage_models import (
    TopicModel,
    LessonModel,
    LessonVersionModel,
    HealthSourceModel,
    ReviewRecordModel,
)
from backend.seed_data import seed_database

GENUINE_TOPIC_IDS = {
    "topic-hygiene",
    "topic-water",
    "topic-mosquito",
    "topic-vaccine",
}

GENUINE_LESSON_IDS = {
    "lesson-handwashing",
    "lesson-water-purification",
    "lesson-mosquito-control",
    "lesson-vaccine-basics",
}

GENUINE_SOURCE_IDS = {
    "src-who-hygiene",
    "src-cdc-hygiene",
    "src-who-water-guidelines",
    "src-who-water-factsheet",
    "src-who-hwts",
    "src-jjm-water-tech",
    "src-cdc-water",
    "src-cdc-mosquito",
    "src-who-vaccines",
}

GENUINE_VERSION_IDS = {
    "ver-handwashing-1",
    "ver-water-1",
    "ver-mosquito-1",
    "ver-vaccine-1",
}

def clean_database():
    client = get_ndb_client()
    with client.context():
        print("[*] Purging unwanted entities from emulator...")

        # 1. Topics (delete topic-water so it reseeds with updated description)
        topics = TopicModel.query().fetch()
        for t in topics:
            if t.key.id() == "topic-water" or t.key.id() not in GENUINE_TOPIC_IDS:
                print(f"  - Deleting topic for fresh re-seed: {t.key.id()} ({t.title})")
                t.key.delete()

        # 2. Lessons (delete water lesson so it reseeds with fresh pointers)
        lessons = LessonModel.query().fetch()
        for l in lessons:
            if l.key.id() == "lesson-water-purification" or l.key.id() not in GENUINE_LESSON_IDS:
                print(f"  - Deleting lesson for fresh re-seed: {l.key.id()}")
                l.key.delete()

        # 3. Versions (delete ver-handwashing-1 and ver-water-1 so they reseed freshly)
        versions = LessonVersionModel.query().fetch()
        for v in versions:
            if v.key.id() in {"ver-handwashing-1", "ver-water-1"} or v.key.id() not in GENUINE_VERSION_IDS:
                print(f"  - Deleting version for fresh re-seed: {v.key.id()}")
                v.key.delete()

        # 4. Sources (delete hygiene & water sources so they reseed with full metadata)
        sources = HealthSourceModel.query().fetch()
        for s in sources:
            if s.key.id() in {
                "src-who-hygiene",
                "src-cdc-hygiene",
                "src-cdc-water",
                "src-who-water-guidelines",
                "src-who-water-factsheet",
                "src-who-hwts",
                "src-jjm-water-tech",
            } or s.key.id() not in GENUINE_SOURCE_IDS:
                print(f"  - Deleting source for fresh re-seed: {s.key.id()}")
                s.key.delete()

        # 5. Reviews
        reviews = ReviewRecordModel.query().fetch()
        for r in reviews:
            r.key.delete()

    print("[*] Re-seeding official database content...")
    seed_database()

    # Verify final counts
    with client.context():
        final_topics = TopicModel.query().fetch()
        print(f"[SUCCESS] Cleaned! Total topics remaining: {len(final_topics)}")
        for t in final_topics:
            print(f"  -> {t.key.id()}: {t.title} ({t.status})")

if __name__ == "__main__":
    clean_database()
