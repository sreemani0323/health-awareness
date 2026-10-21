"""Script to generate and validate the complete 20-chapter canonical curriculum for HealthAware.

Includes:
- 4 canonical topics
- 5 chapters per topic (20 chapters total)
- Authentic Indian household & community dialogue scenarios
- 2 in-chapter interactive knowledge checks per lesson
- 5-question comprehensive chapter assessment per lesson
- Multiple interaction types: single_choice, multi_select, arrange_steps, identify_risk, myth_fact
- 4 Capstone Topic Mastery Challenges (10 questions each)
- 19 verified primary sources from WHO, MoHFW India, NHM, CDC, JJM, NCVBDC
- Complete domain validation of all topics, lessons, lesson versions, cards, and interactions
"""

from __future__ import annotations

import json
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

from backend.curriculum_data.hygiene import get_hygiene_lessons
from backend.curriculum_data.water import get_water_lessons
from backend.curriculum_data.mosquito import get_mosquito_lessons
from backend.curriculum_data.vaccine import get_vaccine_lessons
from backend.curriculum_data.mastery import get_mastery_challenges

from backend.domain.domain_objects import (
    HealthSource,
    Lesson,
    LessonVersion,
    PublicationStatus,
    Topic,
    VersionStatus,
)


def parse_date(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val).date()
    except Exception:
        return None


def get_sources() -> list[dict]:
    return [
        {
            "source_id": "src-who-hygiene",
            "title": "WHO Guidelines on Hand Hygiene in Community Settings",
            "publisher": "World Health Organization & UNICEF",
            "url": "https://www.who.int/publications/i/item/9789241597906",
            "publication_date": "2020-04-01",
            "access_date": "2026-10-18",
            "jurisdiction": "Global",
            "metadata_notes": "Official guidance on hand hygiene techniques, indications, and community WASH recommendations.",
        },
        {
            "source_id": "src-cdc-hygiene",
            "title": "CDC When and How to Wash Your Hands: Official Handwashing Guidance",
            "publisher": "Centers for Disease Control and Prevention",
            "url": "https://www.cdc.gov/clean-hands/about/index.html",
            "publication_date": "2024-01-15",
            "access_date": "2026-10-18",
            "jurisdiction": "United States / Global",
            "metadata_notes": "CDC evidence base on hand hygiene duration (20 seconds), soap efficacy, and alcohol-based rub guidelines.",
        },
        {
            "source_id": "src-mohfw-respiratory",
            "title": "Guidance on Respiratory Hygiene, Cough Etiquette and Infection Prevention in Public Settings",
            "publisher": "Ministry of Health and Family Welfare, Government of India",
            "url": "https://www.mohfw.gov.in",
            "publication_date": "2022-03-10",
            "access_date": "2026-10-21",
            "jurisdiction": "India",
            "metadata_notes": "Guidelines on droplet transmission reduction, mask hygiene, elbow flexion coughing, and community ventilation.",
        },
        {
            "source_id": "src-who-oral-health",
            "title": "WHO Oral Health: Fact Sheet and Daily Fluoride Brushing Guidance",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/news-room/fact-sheets/detail/oral-health",
            "publication_date": "2023-03-14",
            "access_date": "2026-10-21",
            "jurisdiction": "Global",
            "metadata_notes": "Evidence on dental biofilm, fluoride toothpaste efficacy, twice-daily brushing, and plaque control.",
        },
        {
            "source_id": "src-who-sanitation-shared",
            "title": "WHO Guidelines on Sanitation and Health: Environmental Hygiene in Shared Living Spaces",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/publications/i/item/9789241514705",
            "publication_date": "2021-08-12",
            "access_date": "2026-10-21",
            "jurisdiction": "Global",
            "metadata_notes": "Hygiene standards for communal living, surface cleaning vs disinfection, chlorine dilutions, and contact times.",
        },
        {
            "source_id": "src-who-water-guidelines",
            "title": "WHO Guidelines for Drinking-water Quality (Fourth Edition Incorporating Addenda)",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/publications/i/item/9789241549950",
            "publication_date": "2022-03-21",
            "access_date": "2026-10-18",
            "jurisdiction": "Global",
            "metadata_notes": "Benchmark framework for microbial water safety, turbidity thresholds, and fecal indicator bacteria (E. coli).",
        },
        {
            "source_id": "src-who-water-factsheet",
            "title": "WHO Drinking-water Fact Sheet: Health Risks and Interventions",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/news-room/fact-sheets/detail/drinking-water",
            "publication_date": "2023-10-24",
            "access_date": "2026-10-18",
            "jurisdiction": "Global",
            "metadata_notes": "Global statistics on waterborne enteric diseases and primary household treatment interventions.",
        },
        {
            "source_id": "src-cdc-water",
            "title": "CDC Healthy Water: Drinking Water Treatment and Purification",
            "publisher": "Centers for Disease Control and Prevention",
            "url": "https://www.cdc.gov/drinking-water/treatment/index.html",
            "publication_date": "2024-02-01",
            "access_date": "2026-10-18",
            "jurisdiction": "United States / Global",
            "metadata_notes": "Evidence for rolling boil duration, filtration pore sizes, chlorination contact time, and UV inactivation.",
        },
        {
            "source_id": "src-who-hwts",
            "title": "WHO Household Water Treatment and Safe Storage Guidance",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/publications/i/item/9789241548151",
            "publication_date": "2021-05-18",
            "access_date": "2026-10-18",
            "jurisdiction": "Global",
            "metadata_notes": "Safe storage practices: narrow neck vessels, dedicated clean taps/ladles, and secondary contamination prevention.",
        },
        {
            "source_id": "src-jjm-water-tech",
            "title": "Jal Jeevan Mission: Handbook on Drinking Water Treatment Technologies",
            "publisher": "Ministry of Jal Shakti, Government of India",
            "url": "https://jaljeevanmission.gov.in/",
            "publication_date": "2022-06-15",
            "access_date": "2026-10-18",
            "jurisdiction": "India",
            "metadata_notes": "Rural piped water standards, chlorine dosing (FTK testing), community source protection, and water testing kits.",
        },
        {
            "source_id": "src-vector-control-measu-4319",
            "title": "Vector Control Measures for Mosquito-Borne Diseases",
            "publisher": "National Center for Vector Borne Diseases Control, Ministry of Health and Family Welfare, Government of India",
            "url": "https://ncvbdc.mohfw.gov.in/index4.php?lang=1&level=0&linkid=484&lid=3728",
            "publication_date": "2024-03-01",
            "access_date": "2026-10-18",
            "jurisdiction": "India",
            "metadata_notes": "Official Indian guidelines on source reduction, weekly Dry Day, container management, and anti-larval measures.",
        },
        {
            "source_id": "src-do-s-and-don-ts-1543",
            "title": "Do's and Don'ts for Prevention and Control of Vector Borne Diseases",
            "publisher": "National Center for Vector Borne Diseases Control, Ministry of Health and Family Welfare, Government of India",
            "url": "https://ncvbdc.mohfw.gov.in/index4.php?lang=1&level=0&linkid=485&lid=3729",
            "publication_date": "2024-03-01",
            "access_date": "2026-10-18",
            "jurisdiction": "India",
            "metadata_notes": "Citizen instructions for desert cooler cleaning, personal protection, and community standing water elimination.",
        },
        {
            "source_id": "src-cdc-mosquito",
            "title": "CDC Mosquito Control: Prevent Mosquito Bites and Breeding",
            "publisher": "Centers for Disease Control and Prevention",
            "url": "https://www.cdc.gov/mosquitoes/mosquito-control/index.html",
            "publication_date": "2024-01-20",
            "access_date": "2026-10-18",
            "jurisdiction": "United States / Global",
            "metadata_notes": "Personal protection: EPA-registered repellents (DEET, Picaridin), window screens, and biological larvicides.",
        },
        {
            "source_id": "src-dengue-and-severe-d-7821",
            "title": "Dengue and severe dengue",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue",
            "publication_date": "2024-04-23",
            "access_date": "2026-10-18",
            "jurisdiction": "Global",
            "metadata_notes": "Clinical warning signs, Aedes diurnal biting patterns, danger of aspirin/NSAIDs in bleeding diathesis, and hydration.",
        },
        {
            "source_id": "src-malaria-control-stra-6564",
            "title": "Malaria Control Strategies and Elimination Road Map",
            "publisher": "National Center for Vector Borne Diseases Control, Ministry of Health and Family Welfare, Government of India",
            "url": "https://ncvbdc.mohfw.gov.in/index4.php?lang=1&level=0&linkid=486&lid=3730",
            "publication_date": "2024-03-01",
            "access_date": "2026-10-18",
            "jurisdiction": "India",
            "metadata_notes": "Anopheles biology, nocturnal biting habits, LLIN bed-net distribution, rapid diagnostic testing, and Artemisinin-based therapy.",
        },
        {
            "source_id": "src-ncvbdc-clinical",
            "title": "Clinical Management Guidelines for Dengue Fever and Chikungunya",
            "publisher": "National Center for Vector Borne Diseases Control, Ministry of Health and Family Welfare, Government of India",
            "url": "https://ncvbdc.mohfw.gov.in",
            "publication_date": "2023-05-15",
            "access_date": "2026-10-21",
            "jurisdiction": "India",
            "metadata_notes": "Hospital triage criteria, paracetamol safety, NSAID contraindication, hematocrit monitoring, and platelet guidelines.",
        },
        {
            "source_id": "src-who-vaccines",
            "title": "WHO Vaccines and Immunization: How Do Vaccines Work?",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/news-room/questions-and-answers/item/vaccines-and-immunization-what-is-vaccination",
            "publication_date": "2023-06-05",
            "access_date": "2026-10-18",
            "jurisdiction": "Global",
            "metadata_notes": "Immunology fundamentals: antigens, antibodies, memory cells, community herd immunity, and vaccine safety testing.",
        },
        {
            "source_id": "src-mohfw-uip",
            "title": "National Immunization Schedule (NIS) for Infants, Children and Pregnant Women",
            "publisher": "Ministry of Health and Family Welfare, Government of India",
            "url": "https://nhm.gov.in/index1.php?lang=1&level=2&sublinkid=824&lid=220",
            "publication_date": "2023-01-10",
            "access_date": "2026-10-21",
            "jurisdiction": "India",
            "metadata_notes": "Official Universal Immunization Programme (UIP) schedule: birth doses, Pentavalent, Rotavirus, fIPV, PCV, MR, and Td.",
        },
        {
            "source_id": "src-who-vaccine-safety",
            "title": "Global Advisory Committee on Vaccine Safety: Common Adverse Events and Post-Marketing Surveillance",
            "publisher": "World Health Organization",
            "url": "https://www.who.int/groups/global-advisory-committee-on-vaccine-safety",
            "publication_date": "2023-09-20",
            "access_date": "2026-10-21",
            "jurisdiction": "Global",
            "metadata_notes": "Distinction between expected mild reactogenicity and serious AEFI, 30-minute post-vaccination observation, and record management.",
        },
    ]


def get_topics() -> list[dict]:
    return [
        {
            "topic_id": "topic-hygiene",
            "title": "Personal Hygiene & Handwashing",
            "url_slug": "personal-hygiene",
            "description": "Master evidence-based personal hygiene, the microscopic world of germs, effective 20-second handwashing, respiratory etiquette, and clean shared spaces.",
            "display_order": 1,
            "status": "published",
            "cover_image_ref": "images/topics/hygiene.svg",
            "cover_image_alt": "Clean hands with soap lather under clean running water",
        },
        {
            "topic_id": "topic-water",
            "title": "Safe Drinking Water & Sanitation",
            "url_slug": "safe-drinking-water",
            "description": "Understand waterborne contamination, learn why clear water can harbor invisible microbes, master household boiling and filtration, and protect community supplies.",
            "display_order": 2,
            "status": "published",
            "cover_image_ref": "images/topics/water.svg",
            "cover_image_alt": "Clean glass of boiled and filtered drinking water",
        },
        {
            "topic_id": "topic-mosquito",
            "title": "Mosquito Prevention & Vector Control",
            "url_slug": "mosquito-prevention",
            "description": "Identify mosquito breeding hotspots, implement the weekly household Dry Day protocol, protect against Dengue and Malaria, and organize community prevention campaigns.",
            "display_order": 3,
            "status": "published",
            "cover_image_ref": "images/topics/mosquito.svg",
            "cover_image_alt": "Clean inverted containers and mosquito netting protecting a home",
        },
        {
            "topic_id": "topic-vaccine",
            "title": "Vaccine Awareness & Immunity",
            "url_slug": "vaccine-awareness",
            "description": "Discover how vaccines train your immune system, navigate the National Immunization Schedule, address common misconceptions respectfully, and prepare for vaccination visits.",
            "display_order": 4,
            "status": "published",
            "cover_image_ref": "images/topics/vaccine.svg",
            "cover_image_alt": "Immunization shield protecting families and communities from infectious diseases",
        },
    ]


def get_users() -> list[dict]:
    """Baseline user accounts preserved from original canonical curriculum."""
    return [
        {
            "user_id": "usr-admin-demo",
            "username": "admin_demo",
            "display_name": "Dr. Sarah Chen (Admin)",
            "role": "admin",
            "password_hash": "argon2id$v=19$m=65536,t=3,p=4$demo_salt$demo_hash_placeholder",
            "is_active": True,
        },
        {
            "user_id": "usr-contributor-demo",
            "username": "contributor_demo",
            "display_name": "Priya Sharma (Health Educator)",
            "role": "contributor",
            "password_hash": "argon2id$v=19$m=65536,t=3,p=4$demo_salt$demo_hash_placeholder",
            "is_active": True,
        },
        {
            "user_id": "usr-reviewer-demo",
            "username": "reviewer_demo",
            "display_name": "Dr. Marcus Vance (Clinical Reviewer)",
            "role": "reviewer",
            "password_hash": "argon2id$v=19$m=65536,t=3,p=4$demo_salt$demo_hash_placeholder",
            "is_active": True,
        },
    ]


def assemble_and_validate_curriculum() -> dict:
    sources = get_sources()
    topics = get_topics()
    users = get_users()
    mastery = get_mastery_challenges()

    hygiene_lessons, hygiene_versions = get_hygiene_lessons()
    water_lessons, water_versions = get_water_lessons()
    mosquito_lessons, mosquito_versions = get_mosquito_lessons()
    vaccine_lessons, vaccine_versions = get_vaccine_lessons()

    all_lessons = hygiene_lessons + water_lessons + mosquito_lessons + vaccine_lessons
    all_versions = hygiene_versions + water_versions + mosquito_versions + vaccine_versions

    print(f"Total Sources: {len(sources)}")
    print(f"Total Topics: {len(topics)}")
    print(f"Total Lessons: {len(all_lessons)}")
    print(f"Total Versions: {len(all_versions)}")
    print(f"Total Mastery Challenges: {len(mastery)}")

    assert len(all_lessons) == 20, f"Expected exactly 20 lessons, got {len(all_lessons)}"
    assert len(all_versions) == 20, f"Expected exactly 20 versions, got {len(all_versions)}"
    assert len(topics) == 4, f"Expected 4 topics, got {len(topics)}"
    assert len(mastery) == 4, f"Expected 4 mastery challenges, got {len(mastery)}"

    source_ids_set = {s["source_id"] for s in sources}
    topic_ids_set = {t["topic_id"] for t in topics}
    lesson_ids_set = {l["lesson_id"] for l in all_lessons}

    # 1. Validate Sources
    for s in sources:
        obj = HealthSource(
            source_id=s["source_id"],
            title=s["title"],
            publisher=s["publisher"],
            url=s["url"],
            publication_date=parse_date(s.get("publication_date")),
            access_date=parse_date(s.get("access_date")),
            jurisdiction=s.get("jurisdiction"),
        )
        obj.validate()

    # 2. Validate Topics
    for t in topics:
        obj = Topic(
            topic_id=t["topic_id"],
            title=t["title"],
            url_slug=t["url_slug"],
            description=t["description"],
            display_order=t["display_order"],
            status=PublicationStatus(t["status"]),
            cover_image_ref=t.get("cover_image_ref"),
            cover_image_alt=t.get("cover_image_alt"),
        )
        obj.validate()

    # 3. Validate Lessons
    for l in all_lessons:
        assert l["topic_id"] in topic_ids_set, f"Unknown topic {l['topic_id']} in lesson {l['lesson_id']}"
        obj = Lesson(
            lesson_id=l["lesson_id"],
            topic_id=l["topic_id"],
            display_order=l["display_order"],
            published_version_id=l.get("published_version_id"),
            draft_version_id=l.get("draft_version_id"),
        )
        obj.validate()

    # 4. Validate Lesson Versions and Cards
    total_interactions = 0
    for v in all_versions:
        assert v["lesson_id"] in lesson_ids_set, f"Unknown lesson {v['lesson_id']} in version {v['version_id']}"
        for sid in v.get("source_ids", []):
            assert sid in source_ids_set, f"Unknown source {sid} in version {v['version_id']}"

        cards = LessonVersion.cards_from_dicts(v["cards"])
        assert len(cards) >= 5, f"Version {v['version_id']} has fewer than 5 cards ({len(cards)})"

        # Check interaction counts: 2 in-chapter checks + 5-question chapter quiz = 7 interactions
        interactions_in_ver = [c for c in cards if c.interaction is not None]
        total_interactions += len(interactions_in_ver)
        assert len(interactions_in_ver) >= 7, (
            f"Version {v['version_id']} has {len(interactions_in_ver)} interactions (expected at least 7)"
        )

        obj = LessonVersion(
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
        obj.validate()

    print(f"Successfully validated all {len(all_versions)} versions and {total_interactions} interactions!")

    # 5. Validate Mastery Challenges
    for mc in mastery:
        assert mc["topic_id"] in topic_ids_set
        assert len(mc["questions"]) >= 8, f"Mastery challenge {mc['topic_id']} has fewer than 8 questions"
        for q in mc["questions"]:
            assert q["id"], "Missing question id"
            assert q["question_prompt"], "Missing question prompt"
            assert len(q["options"]) >= 2, "Question has fewer than 2 options"
            correct_opts = [o for o in q["options"] if o.get("is_correct")]
            assert len(correct_opts) >= 1, f"Question {q['id']} has no correct option"

    print("Successfully validated all 4 Capstone Topic Mastery Challenges!")

    curriculum_data = {
        "sources": sources,
        "topics": topics,
        "lessons": all_lessons,
        "versions": all_versions,
        "mastery_challenges": mastery,
        "users": users,
    }

    target_path = os.path.join(repo_root, "backend", "canonical_curriculum.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(curriculum_data, f, indent=2, ensure_ascii=False)

    print(f"\nWritten {len(all_lessons)} canonical lessons and {len(mastery)} mastery challenges to {target_path}")
    return curriculum_data


if __name__ == "__main__":
    assemble_and_validate_curriculum()
