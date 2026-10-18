"""Targeted Multi-Chapter Publication Verification for HealthAware Creator Studio.

Tests:
1. Clean-slate setup: Purges any prior test run entities for topic-multichapter-verify.
2. Creation of a multi-chapter topic with two chapters (each with valid lesson cards).
3. Independent submission and approval of Chapter 1.
4. Progressive publication verification: Topic is published and public, /topics/<id>/lessons
   returns Chapter 1, but Chapter 2 (in draft) is strictly hidden from learners.
5. Independent submission and approval of Chapter 2.
6. Public API multi-chapter verification: /topics lists the topic, and
   /topics/<id>/lessons returns BOTH chapters in correct display_order [1, 2].
7. Public learner content verification: Full lesson player payloads for both chapters.
8. Draft revision isolation test: A new draft revision (v2) of Chapter 1 is created,
   and public learners continue seeing only v1.
9. Immutability & self-approval checks: Published versions cannot be modified (403),
   and contributors cannot self-approve drafts (403).
10. Targeted cleanup: Deletes only the temporary test entities, verifying that all
    4 genuine health topics remain intact.
"""

import os
import sys
import requests

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

DIRECT_URL = "http://127.0.0.1:5000/api/v1"

TEST_TOPIC_ID = "topic-multichapter-verify"
TEST_LESSON_IDS = ["lesson-cardio-basics", "lesson-strength-flexibility"]
TEST_VERSION_IDS = [
    "ver-lesson-cardio-basics-v1",
    "ver-lesson-cardio-basics-v2",
    "ver-lesson-strength-flexibility-v1",
]

def purge_test_entities():
    """Delete only the dedicated multi-chapter test entities from Datastore."""
    client = get_ndb_client()
    with client.context():
        # Delete topic
        t = TopicModel.get_by_id(TEST_TOPIC_ID)
        if t:
            t.key.delete()
        # Delete lessons
        for lid in TEST_LESSON_IDS:
            l = LessonModel.get_by_id(lid)
            if l:
                l.key.delete()
        # Delete versions
        for vid in TEST_VERSION_IDS:
            v = LessonVersionModel.get_by_id(vid)
            if v:
                v.key.delete()
        # Delete review records
        for vid in TEST_VERSION_IDS:
            reviews = ReviewRecordModel.query(ReviewRecordModel.version_id == vid).fetch()
            for r in reviews:
                r.key.delete()

def verify_baseline_topics():
    """Verify that all genuine public health topics remain intact."""
    client = get_ndb_client()
    with client.context():
        topics = TopicModel.query().fetch()
        topic_ids = {t.key.id() for t in topics}
        required_genuine = {
            "topic-hygiene",
            "topic-water",
            "topic-mosquito",
            "topic-vaccine",
        }
        for gid in required_genuine:
            assert gid in topic_ids, f"CRITICAL: Genuine topic {gid} is missing!"
        assert TEST_TOPIC_ID not in topic_ids, f"Test topic {TEST_TOPIC_ID} should be removed!"
        print("[*] Baseline genuine topics confirmed intact:")
        for t in topics:
            if t.key.id() in required_genuine:
                print(f"    + {t.key.id()}: {t.title} ({t.status})")

def run_test():
    print("=" * 70)
    print("TARGETED MULTI-CHAPTER PUBLICATION VERIFICATION TEST")
    print("=" * 70)

    # Clean prior test state for guaranteed reproducibility
    print("\n[STEP 0] Ensuring clean test environment...")
    purge_test_entities()
    print("  [PASS] Test environment initialized cleanly")

    api_url = DIRECT_URL

    # -------------------------------------------------------------------
    # STEP 1: Contributor Login
    # -------------------------------------------------------------------
    print("\n[STEP 1] Logging in as contributor...")
    contrib_sess = requests.Session()
    login_res = contrib_sess.post(
        f"{api_url}/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    contrib_csrf = login_res.json()["data"]["csrf_token"]
    contrib_sess.headers.update({"X-CSRF-TOKEN": contrib_csrf})
    print("  [PASS] Contributor authenticated successfully")

    # -------------------------------------------------------------------
    # STEP 2: Create Multi-Chapter Topic & Chapters
    # -------------------------------------------------------------------
    print("\n[STEP 2] Creating temporary topic with 2 chapters...")
    topic_payload = {
        "id": TEST_TOPIC_ID,
        "title": "Physical Activity & Heart Health",
        "slug": "physical-activity-heart-health",
        "description": "Evidence-based exercise guidelines, aerobic conditioning, and resistance training.",
        "display_order": 99,
        "status": "draft",
    }
    t_res = contrib_sess.post(f"{api_url}/creator/topics", json=topic_payload)
    assert t_res.status_code in (200, 201), f"Topic creation failed: {t_res.text}"
    print(f"  [PASS] Topic '{topic_payload['title']}' created in DRAFT status")

    # Chapter 1 (display_order: 1)
    ch1_id = TEST_LESSON_IDS[0]
    ch1_res = contrib_sess.post(
        f"{api_url}/creator/topics/{TEST_TOPIC_ID}/lessons",
        json={
            "id": ch1_id,
            "title": "Aerobic Exercise & Heart Function",
            "summary": "Cardiovascular benefits of sustained aerobic training.",
            "display_order": 1,
        },
    )
    assert ch1_res.status_code in (200, 201), f"Chapter 1 creation failed: {ch1_res.text}"
    print(f"  [PASS] Chapter 1 created: {ch1_id} (display_order: 1)")

    # Chapter 2 (display_order: 2)
    ch2_id = TEST_LESSON_IDS[1]
    ch2_res = contrib_sess.post(
        f"{api_url}/creator/topics/{TEST_TOPIC_ID}/lessons",
        json={
            "id": ch2_id,
            "title": "Strength & Flexibility Fundamentals",
            "summary": "Resistance training and musculoskeletal conditioning.",
            "display_order": 2,
        },
    )
    assert ch2_res.status_code in (200, 201), f"Chapter 2 creation failed: {ch2_res.text}"
    print(f"  [PASS] Chapter 2 created: {ch2_id} (display_order: 2)")

    # Populate Chapter 1 with a rich explanation card
    ch1_ver_id = f"ver-{ch1_id}-v1"
    ch1_update = contrib_sess.put(
        f"{api_url}/creator/versions/{ch1_ver_id}",
        json={
            "title": "Aerobic Exercise & Heart Function",
            "summary": "Cardiovascular benefits of sustained aerobic training.",
            "learning_objectives": ["Understand the physiological adaptations to aerobic training."],
            "cards": [
                {
                    "id": "card-cardio-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Aerobic Conditioning & Stroke Volume"},
                        {"block_type": "text", "body": "Regular aerobic exercise increases left ventricular stroke volume and resting bradycardia, optimizing cardiovascular efficiency."},
                    ],
                    "source_ids": [],
                }
            ],
        },
    )
    assert ch1_update.status_code == 200, f"Update Chapter 1 failed: {ch1_update.text}"
    print("  [PASS] Chapter 1 populated with valid explanation card")

    # Populate Chapter 2 with a rich explanation card
    ch2_ver_id = f"ver-{ch2_id}-v1"
    ch2_update = contrib_sess.put(
        f"{api_url}/creator/versions/{ch2_ver_id}",
        json={
            "title": "Strength & Flexibility Fundamentals",
            "summary": "Resistance training and musculoskeletal conditioning.",
            "learning_objectives": ["Understand resistance training effects on musculoskeletal and metabolic health."],
            "cards": [
                {
                    "id": "card-strength-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Resistance Training & Insulin Sensitivity"},
                        {"block_type": "text", "body": "Progressive resistance training enhances glucose transporter type 4 (GLUT4) translocation, improving systemic insulin sensitivity."},
                    ],
                    "source_ids": [],
                }
            ],
        },
    )
    assert ch2_update.status_code == 200, f"Update Chapter 2 failed: {ch2_update.text}"
    print("  [PASS] Chapter 2 populated with valid explanation card")

    # -------------------------------------------------------------------
    # STEP 3: Submit and Approve Chapter 1 Separately
    # -------------------------------------------------------------------
    print("\n[STEP 3] Submitting Chapter 1 for review and approving as Reviewer...")
    sub1_res = contrib_sess.post(f"{api_url}/creator/versions/{ch1_ver_id}/submit")
    assert sub1_res.status_code == 200, f"Submit Chapter 1 failed: {sub1_res.text}"
    print("  [PASS] Chapter 1 submitted for review (status: submitted_for_review)")

    # Reviewer logs in
    reviewer_sess = requests.Session()
    rev_login_res = reviewer_sess.post(
        f"{api_url}/auth/login",
        json={"username": "reviewer", "password": "reviewer123"},
    )
    assert rev_login_res.status_code == 200, f"Reviewer login failed: {rev_login_res.text}"
    rev_csrf = rev_login_res.json()["data"]["csrf_token"]
    reviewer_sess.headers.update({"X-CSRF-TOKEN": rev_csrf})

    app1_res = reviewer_sess.post(f"{api_url}/creator/versions/{ch1_ver_id}/approve")
    assert app1_res.status_code == 200, f"Approve Chapter 1 failed: {app1_res.text}"
    assert app1_res.json()["data"]["status"] == "published"
    print("  [PASS] Chapter 1 APPROVED and published by Reviewer")

    # -------------------------------------------------------------------
    # STEP 4: Verify Progressive Publication State
    # -------------------------------------------------------------------
    print("\n[STEP 4] Verifying progressive publication: Topic live with Chapter 1 only...")
    anon_sess = requests.Session()
    pub_lessons_ch1 = anon_sess.get(f"{api_url}/topics/{TEST_TOPIC_ID}/lessons").json()["data"]
    pub_ids_ch1 = [l["id"] for l in pub_lessons_ch1]
    assert ch1_id in pub_ids_ch1, f"Chapter 1 should be visible publicly: {pub_ids_ch1}"
    assert ch2_id not in pub_ids_ch1, f"Chapter 2 is still DRAFT and must NOT be in public lessons: {pub_ids_ch1}"
    print("  [PASS] Progressive publication confirmed: Topic is published with Chapter 1 only; Chapter 2 is hidden")

    # -------------------------------------------------------------------
    # STEP 5: Submit and Approve Chapter 2 Separately
    # -------------------------------------------------------------------
    print("\n[STEP 5] Submitting Chapter 2 for review and approving as Reviewer...")
    sub2_res = contrib_sess.post(f"{api_url}/creator/versions/{ch2_ver_id}/submit")
    assert sub2_res.status_code == 200, f"Submit Chapter 2 failed: {sub2_res.text}"
    print("  [PASS] Chapter 2 submitted for review (status: submitted_for_review)")

    app2_res = reviewer_sess.post(f"{api_url}/creator/versions/{ch2_ver_id}/approve")
    assert app2_res.status_code == 200, f"Approve Chapter 2 failed: {app2_res.text}"
    assert app2_res.json()["data"]["status"] == "published"
    print("  [PASS] Chapter 2 APPROVED and published by Reviewer")

    # -------------------------------------------------------------------
    # STEP 6: Verify Multi-Chapter Public API & Order
    # -------------------------------------------------------------------
    print("\n[STEP 6] Verifying both chapters in public API in correct display order...")
    # Topic in /topics
    all_pub_topics = anon_sess.get(f"{api_url}/topics").json()["data"]
    matching_topics = [t for t in all_pub_topics if t["id"] == TEST_TOPIC_ID]
    assert len(matching_topics) == 1, "Published topic not found in /topics!"
    print(f"  [PASS] Topic '{matching_topics[0]['title']}' present in public /topics")

    # Lessons in /topics/<id>/lessons
    pub_lessons_both = anon_sess.get(f"{api_url}/topics/{TEST_TOPIC_ID}/lessons").json()["data"]
    assert len(pub_lessons_both) == 2, f"Expected 2 published chapters, got {len(pub_lessons_both)}"
    assert pub_lessons_both[0]["id"] == ch1_id, f"Expected Chapter 1 first, got {pub_lessons_both[0]['id']}"
    assert pub_lessons_both[0]["display_order"] == 1
    assert pub_lessons_both[1]["id"] == ch2_id, f"Expected Chapter 2 second, got {pub_lessons_both[1]['id']}"
    assert pub_lessons_both[1]["display_order"] == 2
    print(f"  [PASS] Both chapters returned in correct display_order: [1: {pub_lessons_both[0]['title']}, 2: {pub_lessons_both[1]['title']}]")

    # -------------------------------------------------------------------
    # STEP 7: Public Learner Content for Both Chapters
    # -------------------------------------------------------------------
    print("\n[STEP 7] Verifying public learner player content for both chapters...")
    p1 = anon_sess.get(f"{api_url}/lessons/{ch1_id}").json()["data"]
    assert p1["title"] == "Aerobic Exercise & Heart Function"
    assert len(p1["cards"]) == 1
    assert "Aerobic Conditioning & Stroke Volume" in p1["cards"][0]["content_blocks"][0]["body"]
    print(f"  [PASS] Chapter 1 player verified: '{p1['title']}' (Card 1: {p1['cards'][0]['content_blocks'][0]['body']})")

    p2 = anon_sess.get(f"{api_url}/lessons/{ch2_id}").json()["data"]
    assert p2["title"] == "Strength & Flexibility Fundamentals"
    assert len(p2["cards"]) == 1
    assert "Resistance Training & Insulin Sensitivity" in p2["cards"][0]["content_blocks"][0]["body"]
    print(f"  [PASS] Chapter 2 player verified: '{p2['title']}' (Card 1: {p2['cards'][0]['content_blocks'][0]['body']})")

    # -------------------------------------------------------------------
    # STEP 8: Draft Revision Isolation Test
    # -------------------------------------------------------------------
    print("\n[STEP 8] Creating a new draft revision (v2) for Chapter 1 and testing learner isolation...")
    v2_id = f"ver-{ch1_id}-v2"
    v2_payload = {
        "id": v2_id,
        "version_number": 2,
        "title": "DRAFT REVISION — Aerobic Exercise Advanced",
        "summary": "This is unapproved work in progress.",
        "learning_objectives": ["Understand advanced aerobic conditioning concepts."],
        "cards": [
            {
                "id": "card-cardio-v2-1",
                "position": 1,
                "card_type": "explanation",
                "content_blocks": [
                    {"block_type": "heading", "body": "UNAPPROVED DRAFT CONTENT"},
                    {"block_type": "text", "body": "This text must NOT be visible to public learners until approved."},
                ],
                "source_ids": [],
            }
        ],
    }
    v2_res = contrib_sess.post(f"{api_url}/creator/lessons/{ch1_id}/versions", json=v2_payload)
    assert v2_res.status_code in (200, 201), f"v2 creation failed: {v2_res.text}"
    print(f"  [PASS] Draft revision v2 created for {ch1_id}")

    # Confirm that public learners STILL receive v1 (published version)
    p1_check = anon_sess.get(f"{api_url}/lessons/{ch1_id}").json()["data"]
    assert p1_check["version_id"] == ch1_ver_id, f"Learner should see v1, got: {p1_check['version_id']}"
    assert p1_check["title"] == "Aerobic Exercise & Heart Function"
    assert "UNAPPROVED DRAFT CONTENT" not in str(p1_check), "SECURITY LEAK: Draft revision content leaked to public learner!"
    print("  [PASS] Learner isolation verified: Public learners still receive published v1; v2 draft is invisible")

    # Anonymous cannot access v2 via any creator endpoint
    anon_v2_res = anon_sess.get(f"{api_url}/creator/versions/{v2_id}")
    assert anon_v2_res.status_code == 401
    print("  [PASS] Anonymous access to draft revision v2 returns 401 Unauthorized")

    # -------------------------------------------------------------------
    # STEP 9: Immutability and Self-Approval Checks
    # -------------------------------------------------------------------
    print("\n[STEP 9] Verifying immutability of published versions and self-approval block...")
    # Direct edit of published v1 rejected
    tamper1 = contrib_sess.put(f"{api_url}/creator/versions/{ch1_ver_id}", json={"title": "Tampered"})
    assert tamper1.status_code == 403, f"Expected 403 for editing published v1, got {tamper1.status_code}"
    print("  [PASS] Published Chapter 1 v1 cannot be edited directly (403 Forbidden)")

    tamper2 = contrib_sess.put(f"{api_url}/creator/versions/{ch2_ver_id}", json={"title": "Tampered"})
    assert tamper2.status_code == 403, f"Expected 403 for editing published v1, got {tamper2.status_code}"
    print("  [PASS] Published Chapter 2 v1 cannot be edited directly (403 Forbidden)")

    # Contributor cannot approve v2
    self_app = contrib_sess.post(f"{api_url}/creator/versions/{v2_id}/approve")
    assert self_app.status_code == 403, f"Expected 403 for contributor self-approval, got {self_app.status_code}"
    print("  [PASS] Contributor self-approval on draft revision v2 blocked with 403 Forbidden")

    # -------------------------------------------------------------------
    # STEP 10: Cleanup of Dedicated Test Entities
    # -------------------------------------------------------------------
    print("\n[STEP 10] Purging temporary test entities and verifying baseline health topics...")
    purge_test_entities()
    verify_baseline_topics()
    print("  [PASS] Cleanup complete: Dedicated test entities removed, all 4 genuine topics intact")

    print("\n" + "=" * 70)
    print("ALL MULTI-CHAPTER PUBLICATION VERIFICATION CHECKS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
