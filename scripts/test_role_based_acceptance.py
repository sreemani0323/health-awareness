"""Comprehensive Role-Based Acceptance Test & Security Boundary Verification.
"""
import sys
import os
import requests

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

API_URL = "http://127.0.0.1:5000/api/v1"
EMULATOR_HOST = "127.0.0.1:8080"
os.environ["DATASTORE_EMULATOR_HOST"] = EMULATOR_HOST
os.environ["DATASTORE_PROJECT_ID"] = "health-awareness-local"

results = {
    "security": [],
    "contributor": [],
    "reviewer": [],
    "admin": [],
    "baseline": [],
    "cleanup": [],
}

def log(category, name, passed, details=""):
    results[category].append({"name": name, "passed": passed, "details": details})
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] [{category.upper()}] {name}: {details}")

def purge_test_entities():
    """Purge any temporary acceptance test entities to ensure complete test isolation."""
    from backend.platform.ndb_client import get_ndb_client
    from backend.storage.storage_models import (
        TopicModel,
        LessonModel,
        LessonVersionModel,
        HealthSourceModel,
        UserModel,
        ReviewRecordModel,
    )
    ndb_client = get_ndb_client()
    with ndb_client.context():
        for t in TopicModel.query().fetch():
            if t.key.id().startswith("topic-acc-"):
                t.key.delete()
        for l in LessonModel.query().fetch():
            if l.key.id().startswith("lesson-acc-"):
                l.key.delete()
        for v in LessonVersionModel.query().fetch():
            if v.key.id().startswith("ver-lesson-acc-"):
                v.key.delete()
                for r in ReviewRecordModel.query(ReviewRecordModel.version_id == v.key.id()).fetch():
                    r.key.delete()
        for s in HealthSourceModel.query().fetch():
            if s.key.id().startswith("src-who-") and len(s.key.id()) == 16:
                s.key.delete()
        for u in UserModel.query().fetch():
            if u.username.startswith("temp_"):
                u.key.delete()

def run_acceptance_tests():
    print("=================================================================")
    print("STARTING HEALTHAWARE CREATOR STUDIO ACCEPTANCE & SECURITY CHECKS")
    print("=================================================================")

    # -------------------------------------------------------------
    # 0. Setup Isolation & Check Baseline Topics
    # -------------------------------------------------------------
    purge_test_entities()
    pub_res = requests.get(f"{API_URL}/topics")
    assert pub_res.status_code == 200, f"Failed to get public topics: {pub_res.status_code}"
    pub_topics = pub_res.json().get("data", [])
    pub_ids = {t["id"] for t in pub_topics}
    baseline_expected = ["topic-hygiene", "topic-water", "topic-mosquito", "topic-vaccine"]
    
    for bid in baseline_expected:
        found = bid in pub_ids
        log("baseline", f"Baseline genuine topic '{bid}' present in public /topics", found, f"Status 200, IDs: {pub_ids}")

    # -------------------------------------------------------------
    # 1. Unauthenticated Security Checks
    # -------------------------------------------------------------
    anon = requests.Session()
    anon_topics = anon.get(f"{API_URL}/creator/topics")
    log("security", "Unauthenticated GET /creator/topics blocked", anon_topics.status_code == 401, f"HTTP {anon_topics.status_code}")
    
    anon_create = anon.post(f"{API_URL}/creator/topics", json={"title": "Hack", "slug": "hack"})
    log("security", "Unauthenticated POST /creator/topics blocked", anon_create.status_code == 401, f"HTTP {anon_create.status_code}")

    anon_admin = anon.get(f"{API_URL}/admin/overview")
    log("security", "Unauthenticated GET /admin/overview blocked", anon_admin.status_code == 401, f"HTTP {anon_admin.status_code}")

    anon_reviews = anon.get(f"{API_URL}/creator/reviews")
    log("security", "Unauthenticated GET /creator/reviews blocked", anon_reviews.status_code == 401, f"HTTP {anon_reviews.status_code}")

    # -------------------------------------------------------------
    # 2. Authenticate Contributor
    # -------------------------------------------------------------
    contrib = requests.Session()
    c_login = contrib.post(f"{API_URL}/auth/login", json={"username": "contributor", "password": "contributor123"})
    assert c_login.status_code == 200, f"Contributor login failed: {c_login.text}"
    c_token = c_login.json()["data"]["csrf_token"]
    contrib.headers.update({"X-CSRF-TOKEN": c_token})
    log("contributor", "Contributor login and CSRF token retrieval", True, f"HTTP 200, user: {c_login.json()['data']['username']}")

    # CSRF Check: mutative request without CSRF token
    no_csrf_res = requests.post(f"{API_URL}/creator/topics", cookies=contrib.cookies, json={"title": "No CSRF", "slug": "no-csrf"})
    log("security", "CSRF enforcement: mutative request without X-CSRF-TOKEN rejected", no_csrf_res.status_code == 403, f"HTTP {no_csrf_res.status_code}")

    # Contributor attempting Admin endpoint
    c_admin_users = contrib.get(f"{API_URL}/admin/users")
    log("security", "Contributor GET /admin/users forbidden", c_admin_users.status_code == 403, f"HTTP {c_admin_users.status_code}")

    c_admin_overview = contrib.get(f"{API_URL}/admin/overview")
    log("security", "Contributor GET /admin/overview forbidden", c_admin_overview.status_code == 403, f"HTTP {c_admin_overview.status_code}")

    # Contributor attempting Review Queue
    c_review_q = contrib.get(f"{API_URL}/creator/reviews")
    log("security", "Contributor GET /creator/reviews forbidden", c_review_q.status_code == 403, f"HTTP {c_review_q.status_code}")

    # -------------------------------------------------------------
    # 3. Contributor Creates Dedicated Test Topic & Chapters
    # -------------------------------------------------------------
    import uuid
    run_suffix = uuid.uuid4().hex[:8]
    test_topic_id = f"topic-acc-{run_suffix}"
    test_slug = f"acc-test-{run_suffix}"
    ch1_id = f"lesson-acc-ch1-{run_suffix}"
    ch2_id = f"lesson-acc-ch2-{run_suffix}"
    src_id = f"src-who-{run_suffix}"

    t_res = contrib.post(f"{API_URL}/creator/topics", json={
        "id": test_topic_id,
        "title": "Household Hygiene & Sanitation Verification",
        "slug": test_slug,
        "description": "Verification curriculum for multi-chapter authoring, review, and publication acceptance.",
        "display_order": 60,
        "status": "draft",
    })
    log("contributor", "Create temporary test topic", t_res.status_code in (200, 201), f"HTTP {t_res.status_code}")

    # Confirm topic is draft and absent from public anonymous endpoints
    pub_check = anon.get(f"{API_URL}/topics")
    pub_topic_ids = [t["id"] for t in pub_check.json().get("data", [])]
    log("security", "Draft topic absent from public /topics", test_topic_id not in pub_topic_ids, f"Draft topic not leaked")

    # Add Chapter 1
    ch1_res = contrib.post(f"{API_URL}/creator/topics/{test_topic_id}/lessons", json={
        "id": ch1_id,
        "title": "Safe Water Storage Methods",
        "summary": "Evidence-based storage practices to prevent recontamination.",
        "display_order": 1,
    })
    log("contributor", "Add Chapter 1 to test topic", ch1_res.status_code in (200, 201), f"HTTP {ch1_res.status_code}")

    # Add Chapter 2
    ch2_res = contrib.post(f"{API_URL}/creator/topics/{test_topic_id}/lessons", json={
        "id": ch2_id,
        "title": "Disinfection & Filtration Protocols",
        "summary": "Chemical and physical barriers against microbiological pathogens.",
        "display_order": 2,
    })
    log("contributor", "Add Chapter 2 to test topic", ch2_res.status_code in (200, 201), f"HTTP {ch2_res.status_code}")

    # Create Source Reference
    src_res = contrib.post(f"{API_URL}/creator/sources", json={
        "id": src_id,
        "title": "WHO Guidelines for Safe Drinking-water Storage and Quality Control",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/water_sanitation_health/publications/gdwq4",
        "publication_date": "2024-01-15",
        "jurisdiction": "International",
        "metadata_notes": "Official acceptance testing health reference citation.",
    })
    log("contributor", "Create medical source reference", src_res.status_code in (200, 201), f"HTTP {src_res.status_code}")

    # Populate Chapter 1 draft version with Explanation, Multiple-choice Quiz, and Source Reference
    ver1_id = f"ver-{ch1_id}-v1"
    ver1_payload = {
        "title": "Safe Water Storage Methods",
        "summary": "Evidence-based storage practices to prevent recontamination.",
        "language": "en",
        "learning_objectives": ["Identify closed container safety.", "Prevent narrow-mouth contamination."],
        "estimated_duration_minutes": 5,
        "source_ids": [src_id],
        "cards": [
            {
                "id": "card-water-storage-exp",
                "position": 1,
                "card_type": "explanation",
                "content_blocks": [
                    {"block_type": "heading", "body": "Preventing Secondary Microbial Contamination"},
                    {"block_type": "text", "body": "Even purified drinking water rapidly acquires bacterial pathogens when stored in wide-mouthed open containers that allow hands or dirty cups to enter."}
                ],
                "source_ids": [src_id],
            },
            {
                "id": "card-water-storage-quiz",
                "position": 2,
                "card_type": "interaction",
                "content_blocks": [
                    {"block_type": "text", "body": "Select the safest container design based on public health guidelines:"}
                ],
                "source_ids": [src_id],
                "interaction": {
                    "interaction_type": "single_choice",
                    "question_prompt": "Which container design provides the greatest protection against secondary water contamination in households?",
                    "incorrect_behaviour": "retry",
                    "options": [
                        {
                            "id": "opt-narrow-spigot",
                            "label": "Narrow-mouth container with a dedicated dispensing tap or spigot",
                            "is_correct": True,
                            "feedback": "Correct! Narrow openings and taps eliminate direct hand and utensil contact with stored water.",
                        },
                        {
                            "id": "opt-wide-pot",
                            "label": "Wide open clay pot accessed with a communal cup or ladle",
                            "is_correct": False,
                            "feedback": "Incorrect. Dipping hands or cups introduces microbial pathogens directly into the water supply.",
                        },
                        {
                            "id": "opt-uncovered-bucket",
                            "label": "Uncovered plastic bucket kept under shade",
                            "is_correct": False,
                            "feedback": "Incorrect. Uncovered containers allow dust, insects, and particulate contamination.",
                        }
                    ]
                }
            }
        ]
    }
    v1_update = contrib.put(f"{API_URL}/creator/versions/{ver1_id}", json=ver1_payload)
    log("contributor", "Save draft content with explanation, quiz, and medical source", v1_update.status_code == 200, f"HTTP {v1_update.status_code}")

    # Confirm content and chapter ordering persist via GET
    topic_lessons_get = contrib.get(f"{API_URL}/creator/topics/{test_topic_id}/lessons")
    lessons_list = topic_lessons_get.json().get("data", [])
    order_persisted = len(lessons_list) == 2 and lessons_list[0]["display_order"] == 1 and lessons_list[1]["display_order"] == 2
    log("contributor", "Chapter ordering persisted across fetch", order_persisted, f"Order: {[l['display_order'] for l in lessons_list]}")

    v1_get = contrib.get(f"{API_URL}/creator/versions/{ver1_id}")
    v1_data = v1_get.json().get("data", {})
    cards_persisted = len(v1_data.get("cards", [])) == 2 and v1_data.get("source_ids") == [src_id]
    log("contributor", "Cards and source reference persisted accurately", cards_persisted, f"Cards: {len(v1_data.get('cards', []))}, Sources: {v1_data.get('source_ids')}")

    # Contributor attempts self-approval
    self_appr = contrib.post(f"{API_URL}/creator/versions/{ver1_id}/approve")
    log("security", "Contributor self-approval blocked with 403 Forbidden", self_appr.status_code == 403, f"HTTP {self_appr.status_code}")

    # Submit Chapter 1 for review
    submit_res = contrib.post(f"{API_URL}/creator/versions/{ver1_id}/submit")
    log("contributor", "Submit Chapter 1 version for peer review", submit_res.status_code == 200, f"HTTP {submit_res.status_code}")

    # Confirm submitted version cannot be edited through draft PUT endpoint
    edit_submitted = contrib.put(f"{API_URL}/creator/versions/{ver1_id}", json=ver1_payload)
    log("security", "Submitted version cannot be edited through draft PUT endpoint", edit_submitted.status_code in (400, 403), f"HTTP {edit_submitted.status_code}")

    # -------------------------------------------------------------
    # 4. Reviewer Operations
    # -------------------------------------------------------------
    reviewer = requests.Session()
    r_login = reviewer.post(f"{API_URL}/auth/login", json={"username": "reviewer", "password": "reviewer123"})
    assert r_login.status_code == 200, f"Reviewer login failed: {r_login.text}"
    r_token = r_login.json()["data"]["csrf_token"]
    reviewer.headers.update({"X-CSRF-TOKEN": r_token})
    log("reviewer", "Reviewer login and CSRF token retrieval", True, f"HTTP 200, user: {r_login.json()['data']['username']}")

    # Reviewer attempts Admin endpoint
    r_admin_users = reviewer.get(f"{API_URL}/admin/users")
    log("security", "Reviewer GET /admin/users forbidden", r_admin_users.status_code == 403, f"HTTP {r_admin_users.status_code}")

    # Reviewer inspects Review Queue
    queue_res = reviewer.get(f"{API_URL}/creator/reviews")
    queue_items = queue_res.json().get("data", [])
    q_item_ids = [item["id"] for item in queue_items]
    log("reviewer", "Reviewer sees submitted version in Review Queue", ver1_id in q_item_ids, f"Queue count: {len(queue_items)}, found: {ver1_id in q_item_ids}")

    # Reviewer inspects specific version details
    inspect_res = reviewer.get(f"{API_URL}/creator/versions/{ver1_id}")
    inspect_data = inspect_res.json().get("data", {})
    sources_in_review = inspect_data.get("source_ids") == [src_id]
    log("reviewer", "Reviewer inspects version content and source reference", sources_in_review, f"Sources: {inspect_data.get('source_ids')}")

    # Reviewer requests changes with constructive feedback
    feedback_notes = "Please refine the explanation card to explicitly mention container cleaning intervals (e.g. weekly hypochlorite wash) before public publication."
    changes_res = reviewer.post(f"{API_URL}/creator/versions/{ver1_id}/request-changes", json={"notes": feedback_notes})
    log("reviewer", "Reviewer requests changes with mandatory constructive notes", changes_res.status_code == 200, f"HTTP {changes_res.status_code}")

    # Contributor checks feedback
    c_check_ver = contrib.get(f"{API_URL}/creator/versions/{ver1_id}").json().get("data", {})
    feedback_visible = c_check_ver.get("review_feedback") == feedback_notes and c_check_ver.get("status") == "draft"
    log("contributor", "Contributor sees review feedback and reverted draft status", feedback_visible, f"Status: {c_check_ver.get('status')}, Feedback: '{c_check_ver.get('review_feedback')}'")

    # Contributor addresses feedback and updates card
    ver1_payload["cards"][0]["content_blocks"].append({
        "block_type": "text",
        "body": "Wash and sanitize storage vessels weekly with a dilute sodium hypochlorite solution to eliminate biofilm accumulation."
    })
    c_resave = contrib.put(f"{API_URL}/creator/versions/{ver1_id}", json=ver1_payload)
    log("contributor", "Contributor addresses feedback and resaves draft", c_resave.status_code == 200, f"HTTP {c_resave.status_code}")

    # Contributor resubmits for review
    c_resubmit = contrib.post(f"{API_URL}/creator/versions/{ver1_id}/submit")
    log("contributor", "Contributor resubmits corrected chapter for review", c_resubmit.status_code == 200, f"HTTP {c_resubmit.status_code}")

    # Reviewer reviews and approves publication
    approve_res = reviewer.post(f"{API_URL}/creator/versions/{ver1_id}/approve")
    log("reviewer", "Reviewer approves and publishes submitted version", approve_res.status_code == 200, f"HTTP {approve_res.status_code}")

    # Verify immutability of published version
    edit_published = contrib.put(f"{API_URL}/creator/versions/{ver1_id}", json=ver1_payload)
    log("security", "Published version is immutable to direct draft PUT edits", edit_published.status_code in (400, 403), f"HTTP {edit_published.status_code}")

    # -------------------------------------------------------------
    # 5. Public API Learner Availability
    # -------------------------------------------------------------
    pub_topics_now = anon.get(f"{API_URL}/topics").json().get("data", [])
    now_ids = [t["id"] for t in pub_topics_now]
    log("contributor", "Published topic now visible in public /topics endpoint", test_topic_id in now_ids, f"Topic {test_topic_id} listed")

    pub_lessons_now = anon.get(f"{API_URL}/topics/{test_topic_id}/lessons").json().get("data", [])
    pub_lesson_ids = [l["id"] for l in pub_lessons_now]
    log("contributor", "Published Chapter 1 visible in public lessons endpoint", ch1_id in pub_lesson_ids, f"Public lessons: {pub_lesson_ids}")
    log("security", "Unpublished Chapter 2 remains absent from public lessons", ch2_id not in pub_lesson_ids, f"Chapter 2 excluded")

    pub_ch1_detail = anon.get(f"{API_URL}/lessons/{ch1_id}")
    log("contributor", "Published Chapter 1 interactive details render for anonymous learners", pub_ch1_detail.status_code == 200, f"HTTP {pub_ch1_detail.status_code}")

    pub_ch2_detail = anon.get(f"{API_URL}/lessons/{ch2_id}")
    log("security", "Unpublished Chapter 2 returns 404 for anonymous learners", pub_ch2_detail.status_code == 404, f"HTTP {pub_ch2_detail.status_code}")

    # -------------------------------------------------------------
    # 6. Administrator Operations
    # -------------------------------------------------------------
    admin = requests.Session()
    a_login = admin.post(f"{API_URL}/auth/login", json={"username": "admin", "password": "admin123"})
    assert a_login.status_code == 200, f"Admin login failed: {a_login.text}"
    a_token = a_login.json()["data"]["csrf_token"]
    admin.headers.update({"X-CSRF-TOKEN": a_token})
    log("admin", "Admin login and CSRF token retrieval", True, f"HTTP 200, user: {a_login.json()['data']['username']}")

    # Overview KPI metrics
    overview_res = admin.get(f"{API_URL}/admin/overview")
    ov = overview_res.json().get("data", {})
    ov_valid = "total_users" in ov and "active_users" in ov and "published_topics" in ov
    log("admin", "Admin overview KPI metrics fetched", overview_res.status_code == 200 and ov_valid, f"Users: {ov.get('total_users')}, Active: {ov.get('active_users')}")

    # User directory listing without exposing passwords
    users_res = admin.get(f"{API_URL}/admin/users")
    u_list = users_res.json().get("data", [])
    has_passwords = any("password" in u or "password_hash" in u for u in u_list)
    log("admin", "User directory list fetched", users_res.status_code == 200 and len(u_list) >= 3, f"Total users: {len(u_list)}")
    log("security", "Passwords and password hashes omitted from user directory", not has_passwords, f"Passwords exposed: {has_passwords}")

    # Create dedicated test user
    import uuid
    temp_uname = f"tester_{uuid.uuid4().hex[:6]}"
    create_u_res = admin.post(f"{API_URL}/admin/users", json={
        "username": temp_uname,
        "display_name": "Temporary Acceptance Tester",
        "role": "contributor",
        "password": "TempTestPassword123!",
    })
    log("admin", "Admin provisions new user account", create_u_res.status_code in (200, 201), f"HTTP {create_u_res.status_code}")
    temp_user_id = create_u_res.json()["data"]["user_id"]

    # Log in as newly created user to verify credentials work and obtain active session
    temp_sess = requests.Session()
    temp_login = temp_sess.post(f"{API_URL}/auth/login", json={"username": temp_uname, "password": "TempTestPassword123!"})
    log("admin", "Newly provisioned user logs in successfully", temp_login.status_code == 200, f"HTTP {temp_login.status_code}")
    temp_csrf = temp_login.json().get("data", {}).get("csrf_token", "")
    temp_sess.headers.update({"X-CSRF-TOKEN": temp_csrf})

    # Test account role update to Reviewer
    role_change_res = admin.put(f"{API_URL}/admin/users/{temp_user_id}/role", json={"role": "reviewer"})
    log("admin", "Admin mutates user role to reviewer", role_change_res.status_code == 200, f"HTTP {role_change_res.status_code}")
    
    # Confirm role change persisted
    u_verify = admin.get(f"{API_URL}/admin/users").json().get("data", [])
    target_u = next((u for u in u_verify if u.get("user_id") == temp_user_id), None)
    log("admin", "Role update persisted in Datastore", target_u is not None and target_u.get("role") == "reviewer", f"Role: {target_u.get('role') if target_u else 'None'}")

    # Admin self-deactivation rejection
    admin_self_deact = admin.put(f"{API_URL}/admin/users/user-admin/status", json={"is_active": False})
    log("security", "Admin self-deactivation blocked", admin_self_deact.status_code in (400, 403), f"HTTP {admin_self_deact.status_code}")

    # Deactivate temporary test user
    deact_res = admin.put(f"{API_URL}/admin/users/{temp_user_id}/status", json={"is_active": False})
    log("admin", "Admin deactivates temporary test account", deact_res.status_code == 200, f"HTTP {deact_res.status_code}")

    # Verify session lockout: deactivated account session immediately revoked on protected call
    lockout_res = temp_sess.get(f"{API_URL}/creator/topics")
    log("security", "Deactivated account session immediately revoked (HTTP 401)", lockout_res.status_code == 401, f"HTTP {lockout_res.status_code}")

    # Verify login rejection for deactivated account
    deact_login = requests.post(f"{API_URL}/auth/login", json={"username": temp_uname, "password": "TempTestPassword123!"})
    log("security", "Deactivated account cannot sign in (HTTP 401)", deact_login.status_code == 401, f"HTTP {deact_login.status_code}")

    purge_test_entities()

    final_pub = requests.get(f"{API_URL}/topics").json().get("data", [])
    final_ids = {t["id"] for t in final_pub}
    all_intact = final_ids == set(baseline_expected)
    log("baseline", "All four genuine health topics remain intact & published", all_intact, f"Active topics: {final_ids}")

    print("=================================================================")
    print("ALL CORE ACCEPTANCE & SECURITY CHECKS EVALUATED")
    print("=================================================================")

if __name__ == "__main__":
    run_acceptance_tests()
