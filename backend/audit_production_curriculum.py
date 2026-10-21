import json
import urllib.request
import urllib.error
import sys

headers = {"User-Agent": "Mozilla/5.0"}

def query_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== HealthAware Production Curriculum Audit ===")
topics_data = query_json("https://health-awareness.pages.dev/api/v1/topics")
topics = topics_data.get("data", [])
print(f"Total Topics: {len(topics)}")

audit_results = []

for topic in topics:
    topic_id = topic["id"]
    topic_title = topic["title"]
    print(f"\nScanning Topic: {topic_title} ({topic_id})...")
    
    lessons_data = query_json(f"https://health-awareness.pages.dev/api/v1/topics/{topic_id}/lessons")
    lessons = lessons_data.get("data", [])
    print(f"  Published Lessons in topic: {len(lessons)}")
    
    for l_summary in lessons:
        lesson_id = l_summary["id"]
        detail = query_json(f"https://health-awareness.pages.dev/api/v1/lessons/{lesson_id}").get("data", {})
        cards = detail.get("cards", [])
        
        dialogues = []
        in_chapter_checks = []
        quiz_questions = []
        interactions = []
        has_takeaway = False
        
        # In our architecture:
        # Card 1 is Hook/Dialogue
        # Cards 2..N are content & in-chapter checks
        # Cards (last - 5) .. (last - 1) or similar are the 5-question chapter quiz
        # Last Card is Recap / Takeaway
        
        for idx, card in enumerate(cards):
            inter = card.get("interaction")
            blocks = card.get("content_blocks", [])
            
            for b in blocks:
                if b.get("block_type") == "dialogue":
                    dialogues.append({
                        "speaker": b.get("speaker"),
                        "text": b.get("body")
                    })
                if b.get("block_type") == "key_takeaway" or "takeaway" in b.get("body", "").lower():
                    has_takeaway = True
            
            if inter:
                interactions.append({
                    "card_idx": idx + 1,
                    "type": inter.get("interaction_type"),
                    "prompt": inter.get("question_prompt"),
                    "options_count": len(inter.get("options", []))
                })
        
        # Check requirements:
        # 1. Dialogue/scenario hook (dialogues > 0 or scenario text)
        # 2. In-chapter checks: at least 2
        # 3. Chapter quiz: 5 questions
        # Total interactions should typically be >= 7 (2 in-chapter + 5 quiz)
        
        status_flags = []
        if len(dialogues) < 2:
            status_flags.append(f"LOW_DIALOGUE ({len(dialogues)})")
        if len(interactions) < 7:
            status_flags.append(f"INSUFFICIENT_INTERACTIONS ({len(interactions)}/7)")
        if len(detail.get("sources", [])) == 0:
            status_flags.append("NO_SOURCES")
        if not has_takeaway:
            status_flags.append("NO_TAKEAWAY")
            
        audit_results.append({
            "topic_id": topic_id,
            "lesson_id": lesson_id,
            "title": detail.get("title"),
            "total_cards": len(cards),
            "dialogue_count": len(dialogues),
            "interactions_count": len(interactions),
            "interaction_types": [i["type"] for i in interactions],
            "sources_count": len(detail.get("sources", [])),
            "sources": [s.get("id") for s in detail.get("sources", [])],
            "has_takeaway": has_takeaway,
            "issues": status_flags
        })

print("\n" + "="*80)
print("AUDIT MATRIX SUMMARY")
print("="*80)
for r in audit_results:
    issue_str = " | ISSUES: " + ", ".join(r["issues"]) if r["issues"] else " | STATUS: OK"
    print(f"[{r['topic_id']}] {r['lesson_id']}: '{r['title']}'")
    print(f"   Cards: {r['total_cards']} | Dialogues: {r['dialogue_count']} | Interactions: {r['interactions_count']} {r['interaction_types']} | Sources: {r['sources_count']}{issue_str}")

# Check mastery challenges
print("\n" + "="*80)
print("MASTERY CHALLENGES AUDIT")
print("="*80)
for topic in topics:
    topic_id = topic["id"]
    mastery = query_json(f"https://health-awareness.pages.dev/api/v1/topics/{topic_id}/mastery").get("data", {})
    questions = mastery.get("questions", [])
    print(f"[{topic_id}] Mastery: '{mastery.get('title')}' | Questions: {len(questions)} | Badge: '{mastery.get('badge_title')}'")
