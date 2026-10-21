import json

with open("backend/canonical_curriculum.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lessons = data["lessons"]
versions = {v["version_id"]: v for v in data["versions"]}

print(f"Total Lessons: {len(lessons)}")
print(f"Total Versions: {len(versions)}")

report = []

for l in sorted(lessons, key=lambda x: (x["topic_id"], x["display_order"])):
    lid = l["lesson_id"]
    vid = l["published_version_id"]
    v = versions.get(vid)
    if not v:
        report.append({"lesson_id": lid, "error": "MISSING_VERSION"})
        continue
        
    cards = v.get("cards", [])
    
    # 1. Dialogue audit
    dialogues = []
    card1 = cards[0] if cards else {}
    for b in card1.get("content_blocks", []):
        if b.get("block_type") == "dialogue":
            dialogues.append(f"{b.get('speaker')}: \"{b.get('body')}\"")
            
    # 2. In-chapter checks vs Quiz
    # Interactions: first N-5 are in-chapter, last 5 are chapter quiz
    all_interactions = []
    for c_idx, c in enumerate(cards):
        inter = c.get("interaction")
        if inter:
            all_interactions.append({
                "card_pos": c.get("position", c_idx + 1),
                "type": inter.get("interaction_type"),
                "prompt": inter.get("question_prompt"),
                "options": inter.get("options", []),
                "incorrect_behaviour": inter.get("incorrect_behaviour")
            })
            
    in_chapter = all_interactions[:-5] if len(all_interactions) >= 5 else []
    quiz = all_interactions[-5:] if len(all_interactions) >= 5 else all_interactions
    
    # 3. Takeaway audit
    last_card = cards[-1] if cards else {}
    takeaways = []
    for b in last_card.get("content_blocks", []):
        if b.get("block_type") == "key_takeaway" or "takeaway" in b.get("body", "").lower():
            takeaways.append(b.get("body"))
            
    # Check for clinical safety red flags
    # E.g., aspirin for dengue, drinking untreated flood water, etc.
    text_corpus = json.dumps(v).lower()
    safety_flags = []
    if "aspirin" in text_corpus and "contraindicated" not in text_corpus and "avoid" not in text_corpus and "do not" not in text_corpus:
        safety_flags.append("POTENTIAL_ASPIRIN_WARNING_MISSING")
    if "ibuprofen" in text_corpus and "contraindicated" not in text_corpus and "avoid" not in text_corpus and "do not" not in text_corpus:
        safety_flags.append("POTENTIAL_NSAID_WARNING_MISSING")
        
    report.append({
        "topic_id": l["topic_id"],
        "display_order": l["display_order"],
        "lesson_id": lid,
        "title": v.get("title"),
        "dialogue_snippets": dialogues[:3],
        "dialogue_count": len(dialogues),
        "in_chapter_count": len(in_chapter),
        "in_chapter_types": [ic["type"] for ic in in_chapter],
        "quiz_count": len(quiz),
        "quiz_all_have_feedback": all(all(o.get("feedback") for o in q["options"]) for q in quiz),
        "total_cards": len(cards),
        "takeaways_count": len(takeaways),
        "sources_count": len(v.get("source_ids", [])),
        "safety_flags": safety_flags
    })

print("\n" + "="*90)
print(f"{'TOPIC':<16} | {'CH':<2} | {'TITLE':<38} | {'DLG':<3} | {'IN-CH':<16} | {'QUIZ':<4} | {'FB':<3} | {'SRC':<3}")
print("="*90)
for r in report:
    inch_str = f"{r['in_chapter_count']} {r['in_chapter_types']}"
    fb_str = "YES" if r["quiz_all_have_feedback"] else "NO"
    print(f"{r['topic_id']:<16} | {r['display_order']:<2} | {r['title'][:38]:<38} | {r['dialogue_count']:<3} | {inch_str:<16} | {r['quiz_count']:<4} | {fb_str:<3} | {r['sources_count']:<3}")

print("\nDetailed Dialogues Sample:")
for r in report:
    print(f"\n--- [{r['topic_id']} Ch {r['display_order']}] {r['title']} ---")
    for d in r["dialogue_snippets"]:
        print(f"  {d}")
