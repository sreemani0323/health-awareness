"""End-to-end API Publication Acceptance Test for HealthAware Creator Studio.

Tests all publication lifecycle steps:
1. Contributor login
2. Source creation
3. Topic creation (2 chapters)
4. Draft saving (explanation card, multiple-choice quiz card, recap card)
5. Draft privacy enforcement (anonymous user blocked from drafts and unlisted topic)
6. Self-approval enforcement (contributor cannot approve own submission -> 403)
7. Submission for review
8. Reviewer login, queue inspection, and approval
9. Immutability enforcement (published version cannot be edited directly -> 403)
10. Public API availability for learners (topic, chapters, lesson, quiz, source)
11. Unpublished draft lesson remains 404 for learners
"""

import os
import sys
import requests

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

os.environ["DATASTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
os.environ["DATASTORE_PROJECT_ID"] = "health-awareness-local"

DIRECT_URL = "http://127.0.0.1:5000/api/v1"

def run_test():
    print("=" * 60)
    print("CREATOR STUDIO — END-TO-END PUBLICATION ACCEPTANCE TEST")
    print("=" * 60)

    api_url = DIRECT_URL

    # ---------------------------------------------------------
    # STEP 1: Contributor Login
    # ---------------------------------------------------------
    print("\n[STEP 1] Logging in as contributor...")
    contrib_sess = requests.Session()
    login_res = contrib_sess.post(
        f"{api_url}/auth/login",
        json={"username": "contributor", "password": "contributor123"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    contrib_data = login_res.json()["data"]
    csrf_token = contrib_data["csrf_token"]
    contrib_sess.headers.update({"X-CSRF-TOKEN": csrf_token})
    print(f"  [PASS] Authenticated as {contrib_data['username']} ({contrib_data['role']})")

    # ---------------------------------------------------------
    # STEP 2: Create Medical Source
    # ---------------------------------------------------------
    print("\n[STEP 2] Creating evidence-based HealthSource...")
    source_payload = {
        "id": "src-who-diet-2024",
        "title": "WHO Healthy Diet Fact Sheet and Dietary Guidelines",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
        "publication_date": "2024-05-15",
        "jurisdiction": "International",
        "metadata_notes": "Official WHO nutritional recommendations for noncommunicable disease prevention.",
    }
    src_res = contrib_sess.post(f"{api_url}/creator/sources", json=source_payload)
    if src_res.status_code in (200, 201):
        print(f"  [PASS] Created source: {src_res.json()['data']['title']}")
    elif src_res.status_code == 400 and "already exists" in src_res.text:
        print("  [PASS] Source 'src-who-diet-2024' already exists, continuing.")
    else:
        raise AssertionError(f"Source creation failed: {src_res.text}")

    # ---------------------------------------------------------
    # STEP 3: Create Dedicated Test Topic
    # ---------------------------------------------------------
    print("\n[STEP 3] Creating dedicated draft topic...")
    topic_payload = {
        "id": "topic-acceptance-test-nutrition",
        "title": "Nutrition & Healthy Eating Habits",
        "slug": "nutrition-healthy-eating-habits",
        "description": "Evidence-based principles of balanced nutrition, hydration, and micronutrient intake for everyday health.",
        "display_order": 99,
        "status": "draft",
    }
    topic_res = contrib_sess.post(f"{api_url}/creator/topics", json=topic_payload)
    if topic_res.status_code in (200, 201):
        created_topic = topic_res.json()["data"]
        print(f"  [PASS] Created Topic: {created_topic['title']} (status: {created_topic['status']})")
    elif topic_res.status_code == 400 and "already exists" in topic_res.text:
        print("  [PASS] Topic 'topic-acceptance-test-nutrition' already exists.")
    else:
        raise AssertionError(f"Topic creation failed: {topic_res.text}")

    # ---------------------------------------------------------
    # STEP 4: Create Two Chapters (Lessons)
    # ---------------------------------------------------------
    print("\n[STEP 4] Creating Chapter 1 & Chapter 2...")
    ch1_res = contrib_sess.post(
        f"{api_url}/creator/topics/topic-acceptance-test-nutrition/lessons",
        json={
            "id": "lesson-acceptance-plate",
            "title": "Balanced Plate Essentials",
            "summary": "Understanding macronutrients and portion control for healthy daily living.",
        },
    )
    if ch1_res.status_code in (200, 201):
        ch1_data = ch1_res.json()["data"]
        print(f"  [PASS] Created Chapter 1: {ch1_data['title']} (ID: {ch1_data['id']})")
    elif ch1_res.status_code == 400 and "already exists" in ch1_res.text:
        ch1_get = contrib_sess.get(f"{api_url}/creator/lessons/lesson-acceptance-plate")
        ch1_data = ch1_get.json()["data"]
        print(f"  [PASS] Chapter 1 exists (ID: {ch1_data['id']})")
    else:
        raise AssertionError(f"Chapter 1 creation failed: {ch1_res.text}")

    ch2_res = contrib_sess.post(
        f"{api_url}/creator/topics/topic-acceptance-test-nutrition/lessons",
        json={
            "id": "lesson-acceptance-hydration",
            "title": "Hydration & Micronutrient Fundamentals",
            "summary": "The critical role of daily water intake and vital vitamins and minerals.",
        },
    )
    if ch2_res.status_code in (200, 201):
        ch2_data = ch2_res.json()["data"]
        print(f"  [PASS] Created Chapter 2: {ch2_data['title']} (ID: {ch2_data['id']})")
    elif ch2_res.status_code == 400 and "already exists" in ch2_res.text:
        ch2_get = contrib_sess.get(f"{api_url}/creator/lessons/lesson-acceptance-hydration")
        ch2_data = ch2_get.json()["data"]
        print(f"  [PASS] Chapter 2 exists (ID: {ch2_data['id']})")
    else:
        raise AssertionError(f"Chapter 2 creation failed: {ch2_res.text}")

    # ---------------------------------------------------------
    # STEP 5: Populate Chapter 1 with 3 Cards & Medical Source
    # ---------------------------------------------------------
    print("\n[STEP 5] Populating Chapter 1 draft version with Explanation, Quiz & Recap cards...")
    ver_id = ch1_data.get("draft_version_id") or ch1_data.get("published_version_id") or "ver-lesson-acceptance-plate-v1"
    
    version_update_payload = {
        "title": "Balanced Plate Essentials",
        "summary": "Evidence-based macronutrient balance and portion guidelines from WHO.",
        "language": "en",
        "learning_objectives": [
            "Identify the essential components of a balanced plate.",
            "Determine the recommended proportion of vegetables and fruits.",
        ],
        "estimated_duration_minutes": 5,
        "source_ids": ["src-who-diet-2024"],
        "cards": [
            {
                "id": "card-plate-1",
                "position": 1,
                "card_type": "explanation",
                "content_blocks": [
                    {
                        "block_type": "heading",
                        "body": "The Balanced Plate Model",
                    },
                    {
                        "block_type": "text",
                        "body": "A healthy, balanced plate comprises approximately half non-starchy vegetables and whole fruits, one quarter whole grains, and one quarter lean protein sources, complemented by clean water.",
                    },
                ],
                "source_ids": ["src-who-diet-2024"],
            },
            {
                "id": "card-plate-2",
                "position": 2,
                "card_type": "interaction",
                "content_blocks": [
                    {
                        "block_type": "heading",
                        "body": "Knowledge Check: Dietary Proportions",
                    },
                ],
                "source_ids": ["src-who-diet-2024"],
                "interaction": {
                    "interaction_type": "single_choice",
                    "question_prompt": "According to WHO dietary recommendations, what proportion of an everyday healthy plate should ideally consist of vegetables and fruits?",
                    "options": [
                        {
                            "id": "opt-plate-1",
                            "label": "About one quarter (25%)",
                            "is_correct": False,
                            "feedback": "A quarter is insufficient; vegetables and fruits provide essential dietary fiber and vitamins.",
                        },
                        {
                            "id": "opt-plate-2",
                            "label": "Approximately half (50%)",
                            "is_correct": True,
                            "feedback": "Correct! Whole fruits and vegetables should constitute roughly half of a balanced plate.",
                        },
                        {
                            "id": "opt-plate-3",
                            "label": "Less than 10%",
                            "is_correct": False,
                            "feedback": "This is much too low according to international dietary guidelines.",
                        },
                    ],
                    "incorrect_behaviour": "retry",
                },
            },
            {
                "id": "card-plate-3",
                "position": 3,
                "card_type": "recap",
                "content_blocks": [
                    {
                        "block_type": "heading",
                        "body": "Summary & Long-Term Health Impact",
                    },
                    {
                        "block_type": "text",
                        "body": "Adopting the balanced plate model consistently reduces risks of cardiovascular illness, hypertension, and type 2 diabetes. Remember to stay hydrated throughout the day.",
                    },
                ],
                "source_ids": ["src-who-diet-2024"],
            },
        ],
    }

    # If version is already published from previous step, let's verify immutability
    ver_status_check = contrib_sess.get(f"{api_url}/creator/versions/{ver_id}").json()["data"]
    if ver_status_check["status"] == "draft":
        ver_update_res = contrib_sess.put(
            f"{api_url}/creator/versions/{ver_id}",
            json=version_update_payload,
        )
        assert ver_update_res.status_code == 200, f"Version update failed: {ver_update_res.text}"
        updated_ver = ver_update_res.json()["data"]
        assert len(updated_ver["cards"]) == 3, f"Expected 3 cards, got {len(updated_ver['cards'])}"
        print(f"  [PASS] Chapter 1 Draft updated with 3 cards (Explanation, Single Choice Quiz, Recap)")
        print(f"  [PASS] Attached Medical Source: {updated_ver['source_ids']}")

        # ---------------------------------------------------------
        # STEP 6: Verify Draft Privacy (Anonymous / Public Endpoints)
        # ---------------------------------------------------------
        print("\n[STEP 6] Verifying draft isolation from anonymous users and public endpoints...")
        anon_sess = requests.Session()

        # 6a. Topic list does not leak draft topic
        public_topics_res = anon_sess.get(f"{api_url}/topics")
        assert public_topics_res.status_code == 200
        pub_topic_ids = [t["id"] for t in public_topics_res.json()["data"]]
        assert "topic-acceptance-test-nutrition" not in pub_topic_ids, (
            "SECURITY LEAK: Draft topic found in public /topics endpoint!"
        )
        print("  [PASS] Draft topic is INVISIBLE in public GET /topics")

        # 6b. Topic lessons endpoint returns 404 for draft topic
        pub_lessons_res = anon_sess.get(f"{api_url}/topics/topic-acceptance-test-nutrition/lessons")
        assert pub_lessons_res.status_code == 404, (
            f"Expected 404 for draft topic lessons, got {pub_lessons_res.status_code}"
        )
        print("  [PASS] Anonymous GET /topics/topic-acceptance-test-nutrition/lessons returns 404")

        # 6c. Lesson player endpoint returns 404 for unpublished lesson
        pub_lesson_play_res = anon_sess.get(f"{api_url}/lessons/lesson-acceptance-plate")
        assert pub_lesson_play_res.status_code == 404, (
            f"Expected 404 for unpublished lesson player, got {pub_lesson_play_res.status_code}"
        )
        print("  [PASS] Anonymous GET /lessons/lesson-acceptance-plate returns 404")

        # 6d. Creator version endpoint returns 401 for anonymous
        anon_creator_res = anon_sess.get(f"{api_url}/creator/versions/{ver_id}")
        assert anon_creator_res.status_code == 401, (
            f"Expected 401 for anonymous creator access, got {anon_creator_res.status_code}"
        )
        print(f"  [PASS] Anonymous GET /creator/versions/{ver_id} returns 401 Unauthorized")

        # ---------------------------------------------------------
        # STEP 7: Verify Self-Approval Prohibition
        # ---------------------------------------------------------
        print("\n[STEP 7] Verifying self-approval prohibition...")
        self_approve_res = contrib_sess.post(f"{api_url}/creator/versions/{ver_id}/approve")
        assert self_approve_res.status_code == 403, (
            f"SECURITY BREACH: Contributor was able to invoke approve endpoint! Got {self_approve_res.status_code}"
        )
        print(f"  [PASS] Contributor self-approval blocked with HTTP 403 Forbidden ({self_approve_res.json()['error']['message']})")

        # ---------------------------------------------------------
        # STEP 8: Contributor Submits Version for Review
        # ---------------------------------------------------------
        print("\n[STEP 8] Submitting version for review as contributor...")
        submit_res = contrib_sess.post(f"{api_url}/creator/versions/{ver_id}/submit")
        assert submit_res.status_code == 200, f"Submit failed: {submit_res.text}"
        submitted_ver = submit_res.json()["data"]
        assert submitted_ver["status"] == "submitted_for_review"
        print(f"  [PASS] Version submitted for review (status: {submitted_ver['status']})")

        # Contributor still cannot approve even after submitting
        self_approve_post_submit = contrib_sess.post(f"{api_url}/creator/versions/{ver_id}/approve")
        assert self_approve_post_submit.status_code == 403
        print("  [PASS] Post-submit self-approval still rejected with HTTP 403 Forbidden")

        # ---------------------------------------------------------
        # STEP 9: Reviewer Logs In, Inspects Queue & Approves
        # ---------------------------------------------------------
        print("\n[STEP 9] Logging in as Reviewer and inspecting submission...")
        reviewer_sess = requests.Session()
        rev_login_res = reviewer_sess.post(
            f"{api_url}/auth/login",
            json={"username": "reviewer", "password": "reviewer123"},
        )
        assert rev_login_res.status_code == 200, f"Reviewer login failed: {rev_login_res.text}"
        rev_data = rev_login_res.json()["data"]
        reviewer_sess.headers.update({"X-CSRF-TOKEN": rev_data["csrf_token"]})
        print(f"  [PASS] Authenticated as {rev_data['username']} ({rev_data['role']})")

        # Reviewer inspects Review Queue
        queue_res = reviewer_sess.get(f"{api_url}/creator/reviews")
        assert queue_res.status_code == 200, f"Queue lookup failed: {queue_res.text}"
        queue_items = queue_res.json()["data"]
        queue_ver_ids = [q["id"] for q in queue_items]
        assert ver_id in queue_ver_ids, f"Submitted version {ver_id} not found in review queue: {queue_ver_ids}"
        print(f"  [PASS] Version {ver_id} found in Review Queue ({len(queue_items)} total submissions)")

        # Reviewer inspects version details and sources
        ver_detail_res = reviewer_sess.get(f"{api_url}/creator/versions/{ver_id}")
        assert ver_detail_res.status_code == 200, f"Version inspection failed: {ver_detail_res.text}"
        inspected_ver = ver_detail_res.json()["data"]
        assert inspected_ver["id"] == ver_id
        assert len(inspected_ver["cards"]) == 3
        assert len(inspected_ver.get("sources", [])) == 1
        assert inspected_ver["sources"][0]["title"] == "WHO Healthy Diet Fact Sheet and Dietary Guidelines"
        print(f"  [PASS] Inspected submission details: verified 3 cards and attached WHO source reference")

        # Reviewer approves and publishes version
        print("\n[STEP 10] Reviewer approves and publishes submitted version...")
        approve_res = reviewer_sess.post(f"{api_url}/creator/versions/{ver_id}/approve")
        assert approve_res.status_code == 200, f"Approve failed: {approve_res.text}"
        approved_ver = approve_res.json()["data"]
        assert approved_ver["status"] == "published"
        print(f"  [PASS] Version {ver_id} approved and PUBLISHED successfully!")

    else:
        print(f"  [INFO] Version {ver_id} is already in '{ver_status_check['status']}' state.")

    # ---------------------------------------------------------
    # STEP 11: Verify Published Version Immutability
    # ---------------------------------------------------------
    print("\n[STEP 11] Verifying published version immutability...")
    tamper_res = contrib_sess.put(
        f"{api_url}/creator/versions/{ver_id}",
        json={"title": "Hacked Title"},
    )
    assert tamper_res.status_code == 403, (
        f"SECURITY BREACH: Published version was mutated! Got {tamper_res.status_code}"
    )
    print(f"  [PASS] Direct edit of published version rejected with HTTP 403 ({tamper_res.json()['error']['message']})")

    # ---------------------------------------------------------
    # STEP 12: Confirm Public Learner API Availability
    # ---------------------------------------------------------
    print("\n[STEP 12] Confirming public availability on learner API endpoints...")
    anon_sess = requests.Session()
    # 12a. Topic is now listed in GET /topics
    pub_topics = anon_sess.get(f"{api_url}/topics").json()["data"]
    matching_topics = [t for t in pub_topics if t["id"] == "topic-acceptance-test-nutrition"]
    assert len(matching_topics) == 1, "Published topic not found in public GET /topics!"
    pub_topic = matching_topics[0]
    assert pub_topic["title"] == "Nutrition & Healthy Eating Habits"
    print(f"  [PASS] Public GET /topics returns published topic: '{pub_topic['title']}'")

    # 12b. GET /topics/<topic_id>/lessons returns published chapter
    pub_lessons_res = anon_sess.get(f"{api_url}/topics/topic-acceptance-test-nutrition/lessons")
    assert pub_lessons_res.status_code == 200
    pub_lessons = pub_lessons_res.json()["data"]
    pub_lesson_ids = [l["id"] for l in pub_lessons]
    assert "lesson-acceptance-plate" in pub_lesson_ids, "Published chapter not in lessons list!"
    print(f"  [PASS] Public GET /topics/.../lessons returns published chapter: '{pub_lessons[0]['title']}'")

    # 12c. GET /lessons/<lesson_id> returns complete lesson player payload
    player_res = anon_sess.get(f"{api_url}/lessons/lesson-acceptance-plate")
    assert player_res.status_code == 200, f"Learner player failed: {player_res.text}"
    player_data = player_res.json()["data"]
    assert player_data["id"] == "lesson-acceptance-plate"
    assert player_data["title"] == "Balanced Plate Essentials"
    assert len(player_data["cards"]) == 3
    # Check interaction structure
    quiz_card = player_data["cards"][1]
    assert quiz_card["card_type"] == "interaction"
    assert "According to WHO dietary recommendations" in quiz_card["interaction"]["question_prompt"]
    assert len(quiz_card["interaction"]["options"]) == 3
    # Check source
    assert len(player_data.get("sources", [])) == 1
    assert "World Health Organization" in player_data["sources"][0]["publisher"]
    print("  [PASS] Public GET /lessons/lesson-acceptance-plate renders complete lesson with 3 cards, quiz & sources")

    # 12d. Unpublished Chapter 2 remains invisible on public lesson player
    unpub_ch2_res = anon_sess.get(f"{api_url}/lessons/lesson-acceptance-hydration")
    assert unpub_ch2_res.status_code == 404, f"Unpublished chapter 2 should return 404, got {unpub_ch2_res.status_code}"
    print("  [PASS] Unpublished Chapter 2 correctly returns 404 on public /lessons endpoint")

    # 13. Teardown: purge temporary test entities
    print("\n[STEP 13] Cleaning up temporary acceptance test entities...")
    from backend.platform.ndb_client import get_ndb_client
    from backend.storage.storage_models import (
        TopicModel,
        LessonModel,
        LessonVersionModel,
        HealthSourceModel,
    )
    ndb_client = get_ndb_client()
    with ndb_client.context():
        t = TopicModel.get_by_id("topic-acceptance-test-nutrition")
        if t:
            t.key.delete()
        for lid in ["lesson-acceptance-plate", "lesson-acceptance-hydration"]:
            l = LessonModel.get_by_id(lid)
            if l:
                l.key.delete()
        for vid in ["ver-lesson-acceptance-plate-v1", "ver-lesson-acceptance-hydration-v1"]:
            v = LessonVersionModel.get_by_id(vid)
            if v:
                v.key.delete()
        s = HealthSourceModel.get_by_id("src-who-diet-2024")
        if s:
            s.key.delete()
    print("  [PASS] Temporary test entities cleaned up successfully.")

    print("\n" + "=" * 60)
    print("ALL PUBLICATION ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
