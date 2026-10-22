"""Regression tests for medical wording review and clinical accuracy.

Verifies:
1. Dengue guidance (lesson-community-prevention-symptoms--4817 and mc-mos-1):
   - Advice to avoid aspirin and NSAIDs in suspected dengue is preserved.
   - Sensational language ("massive, life-threatening internal gastrointestinal bleeding")
     and absolute claims ("the only safe medicine") are eliminated.
   - Bleeding risk is stated accurately (platelet inhibition, gastric irritation).
   - Paracetamol is recommended for fever/pain under appropriate guidance.
   - Explicit instructions to seek qualified medical care for symptoms and warning signs.

2. Water treatment (lesson-water-purification, lesson-clear-water-safety, and mc-wat-3):
   - Boiling duration retains elevation qualification (1 min rolling boil, 3 min above 2,000m).
   - Unsupported absolute claims ("100%") are removed.
   - Clear distinction between biological pathogen inactivation and chemical contamination.
   - Chlorine product instructions emphasize following manufacturer label directions and concentration.

3. Post-vaccination advice (lesson-vaccine-reactions-advice and mc-vax-4):
   - Distinguishes common, mild, short-lived reactions from serious or red-flag symptoms.
   - Does not imply that fever or redness is required for a vaccine to work or proves antibody levels.
   - Injection-site care aligns with Indian MoHFW UIP guidance (clean cool damp cloth; never massage,
     press, or apply mustard oil or ice).
   - 30-minute observation rule aligns with MoHFW UIP and WHO guidance.
"""

from __future__ import annotations

import json
import os
import re
import pytest

from backend.curriculum_data.mosquito import get_mosquito_lessons
from backend.curriculum_data.water import get_water_lessons
from backend.curriculum_data.vaccine import get_vaccine_lessons
from backend.curriculum_data.mastery import get_mastery_challenges


@pytest.fixture(scope="module")
def canonical_curriculum():
    curriculum_path = os.path.join(
        os.path.dirname(__file__), "..", "canonical_curriculum.json"
    )
    assert os.path.exists(curriculum_path), f"Missing {curriculum_path}"
    with open(curriculum_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestDengueGuidanceWording:
    """Tests for clinical wording in lesson-community-prevention-symptoms--4817."""

    def test_dengue_lesson_exists_and_published(self, canonical_curriculum):
        lesson_id = "lesson-community-prevention-symptoms--4817"
        versions = [v for v in canonical_curriculum["versions"] if v["lesson_id"] == lesson_id]
        assert len(versions) == 1, f"Expected 1 published version for {lesson_id}"
        ver = versions[0]
        assert ver["status"] == "published"
        assert len(ver["cards"]) == 10

    def test_dengue_avoids_sensational_language(self, canonical_curriculum):
        """Sensational bleeding claims and absolute statements must be absent."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-community-prevention-symptoms--4817"
        )
        content_text = json.dumps(ver["cards"])

        # Prohibited sensational / absolute phrases
        prohibited_phrases = [
            "massive, life-threatening internal gastrointestinal bleeding",
            "the only safe medicine",
            "triggers fatal bleeding",
            "trigger massive",
        ]
        for phrase in prohibited_phrases:
            assert phrase.lower() not in content_text.lower(), (
                f"Prohibited sensational phrase found in dengue lesson: '{phrase}'"
            )

    def test_dengue_accurately_states_nsaid_contraindication_and_bleeding_risk(self, canonical_curriculum):
        """Must state avoiding aspirin/NSAIDs, platelet impairment, and paracetamol under guidance."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-community-prevention-symptoms--4817"
        )
        content_text = json.dumps(ver["cards"])

        assert "aspirin" in content_text.lower()
        assert "nsaid" in content_text.lower() or "ibuprofen" in content_text.lower()
        assert "platelet" in content_text.lower()
        assert "bleeding" in content_text.lower()
        assert "paracetamol" in content_text.lower()
        assert "medical" in content_text.lower()

    def test_dengue_directs_to_qualified_medical_care_for_warning_signs(self, canonical_curriculum):
        """Must instruct learners to seek medical care for persistent vomiting, abdominal pain, or bleeding."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-community-prevention-symptoms--4817"
        )
        card4 = next(c for c in ver["cards"] if c["card_id"] == "care-card-4")
        assert "warning signs" in json.dumps(card4).lower()
        assert "hospital" in json.dumps(card4).lower() or "medical" in json.dumps(card4).lower()

    def test_dengue_mastery_capstone_question_wording(self):
        """Capstone question mc-mos-1 avoids absolute/sensational claims."""
        challenges = get_mastery_challenges()
        mosquito_ch = next(ch for ch in challenges if ch["topic_id"] == "topic-mosquito")
        q1 = next(q for q in mosquito_ch["questions"] if q["id"] == "mc-mos-1")

        q_text = json.dumps(q1).lower()
        assert "the only safe" not in q_text
        assert "massive, life-threatening" not in q_text
        assert "nsaid" in q_text
        assert "platelet" in q_text


class TestWaterTreatmentWording:
    """Tests for clinical and scientific wording in water purification lessons."""

    def test_boiling_duration_retains_elevation_qualification(self, canonical_curriculum):
        """Boiling guidance must state 1 minute rolling boil, 3 minutes above 2,000m."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-water-purification"
        )
        content_text = json.dumps(ver["cards"])

        assert "1 minute" in content_text or "1 full minute" in content_text
        assert "2,000" in content_text or "2000" in content_text
        assert "3 minute" in content_text

    def test_water_purification_avoids_unsupported_absolute_claims(self, canonical_curriculum):
        """Absolute efficacy claims like 'inactivates 100%' or '100% sterile' must be absent."""
        for lesson_id in ["lesson-water-purification", "lesson-clear-water-safety"]:
            ver = next(
                v for v in canonical_curriculum["versions"]
                if v["lesson_id"] == lesson_id
            )
            content_text = json.dumps(ver["cards"])
            assert "100%" not in content_text, f"Unqualified '100%' claim found in {lesson_id}"

    def test_distinguishes_biological_from_chemical_contamination(self, canonical_curriculum):
        """Must distinguish microbial inactivation from chemical/heavy metal contaminants."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-water-purification"
        )
        content_text = json.dumps(ver["cards"]).lower()
        assert "chemical" in content_text
        assert "heavy metal" in content_text or "arsenic" in content_text

    def test_chlorine_product_directions_respect_concentration_and_labels(self, canonical_curriculum):
        """Chlorine instructions must reference product label directions and typical contact time."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-water-purification"
        )
        content_text = json.dumps(ver["cards"]).lower()
        assert "label" in content_text
        assert "contact time" in content_text or "30 minute" in content_text


class TestPostVaccinationAdviceWording:
    """Tests for post-vaccination advice in lesson-vaccine-reactions-advice."""

    def test_vaccine_lesson_exists_and_published(self, canonical_curriculum):
        lesson_id = "lesson-vaccine-reactions-advice"
        versions = [v for v in canonical_curriculum["versions"] if v["lesson_id"] == lesson_id]
        assert len(versions) == 1
        ver = versions[0]
        assert ver["status"] == "published"
        assert len(ver["cards"]) == 10

    def test_distinguishes_common_reactions_from_serious_symptoms(self, canonical_curriculum):
        """Common short-lived reactions must be distinguished from serious red flags."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-vaccine-reactions-advice"
        )
        content_text = json.dumps(ver["cards"])

        # Check common reactions
        assert "mild" in content_text.lower()
        assert "tenderness" in content_text.lower() or "soreness" in content_text.lower()

        # Check serious red flags
        assert "difficulty breathing" in content_text.lower()
        assert "convulsion" in content_text.lower() or "seizure" in content_text.lower()

        # Check distinction between emergency help and prompt healthcare professional advice
        assert "immediate emergency help" in content_text.lower() or "immediate emergency medical care" in content_text.lower()
        assert "prompt healthcare advice" in content_text.lower() or "prompt advice from a healthcare professional" in content_text.lower()

        # Check absence of unsupported causal claim
        assert "damages irritated muscle tissue and can introduce bacterial infections" not in content_text.lower()

    def test_does_not_imply_fever_is_required_for_vaccine_to_work(self, canonical_curriculum):
        """Must not claim or imply that fever is necessary for protection or proves antibodies."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-vaccine-reactions-advice"
        )
        content_text = json.dumps(ver["cards"])

        # Prohibited implications
        assert "positive biological indicator" not in content_text.lower()
        assert "fever will prove" not in content_text.lower()

        # Card 1 and Card 5 must explicitly state fever is not required for immunity
        card1 = next(c for c in ver["cards"] if c["card_id"] == "react-card-1")
        card1_text = json.dumps(card1).lower()
        assert "not required" in card1_text or "without fever" in card1_text

        card5 = next(c for c in ver["cards"] if c["card_id"] == "react-card-5")
        q1_prompt = card5["interaction"]["question_prompt"]
        assert "positive biological indicator" not in q1_prompt.lower()
        assert "neither required for protection" in json.dumps(card5).lower()

    def test_injection_site_care_conforms_to_mohfw_guidance(self, canonical_curriculum):
        """Site care must advise cool damp cloth and strictly prohibit mustard oil or direct ice."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-vaccine-reactions-advice"
        )
        card1 = next(c for c in ver["cards"] if c["card_id"] == "react-card-1")
        card2 = next(c for c in ver["cards"] if c["card_id"] == "react-card-2")
        text = json.dumps([card1, card2]).lower()

        assert "cool, damp cloth" in text or "cool damp cloth" in text
        assert "mustard oil" in text
        assert "never massage" in text

    def test_observation_time_aligns_with_mohfw_30_minute_rule(self, canonical_curriculum):
        """Must specify 30 minutes observation at clinic for acute allergic reaction care."""
        ver = next(
            v for v in canonical_curriculum["versions"]
            if v["lesson_id"] == "lesson-vaccine-reactions-advice"
        )
        card3 = next(c for c in ver["cards"] if c["card_id"] == "react-card-3")
        card3_text = json.dumps(card3).lower()

        assert "30-minute" in card3_text or "30 minutes" in card3_text
        assert "anaphylaxis" in card3_text or "allergic reaction" in card3_text
        assert "adrenaline" in card3_text or "epinephrine" in card3_text

    def test_vaccine_mastery_capstone_question_wording(self):
        """Capstone question mc-vax-4 adheres to young infant (<3 month) fever safety guidelines."""
        challenges = get_mastery_challenges()
        vaccine_ch = next(ch for ch in challenges if ch["topic_id"] == "topic-vaccine")
        q4 = next(q for q in vaccine_ch["questions"] if q["id"] == "mc-vax-4")

        q_text = json.dumps(q4).lower()
        # Explicitly specifies a 6-week-old baby
        assert "a 6-week-old baby" in q4["question_prompt"].lower()

        # Does not imply fever is required for immunity
        assert "indicating active antibody production" not in q_text

        # Rejects implausible or sensational distractors
        assert "open-heart surgery" not in q_text
        assert "red chili" not in q_text

        # Correct option requires prompt clinical assessment, not routine home care alone
        correct_opts = [o for o in q4["options"] if o["is_correct"]]
        assert len(correct_opts) == 1
        correct_opt = correct_opts[0]
        correct_text = correct_opt["label"].lower()
        assert "healthcare professional" in correct_text or "clinical assessment" in correct_text
        assert "48 hours" not in correct_text

        # Distractor advising waiting 48 hours / sweating out fever is marked incorrect
        wait_distractor = next(
            o for o in q4["options"] if "48 hours" in o["label"] or "sweat out" in o["label"]
        )
        assert wait_distractor["is_correct"] is False

        # Explanation distinguishes prompt clinical evaluation from emergency red flags
        explanation = q4["explanation"].lower()
        assert "prompt assessment" in explanation or "healthcare professional" in explanation
        assert "breathing difficulty" in explanation or "seizures" in explanation or "unresponsiveness" in explanation


class TestAuthoritativeSourceLinkages:
    """Verifies that primary sources from MoHFW, WHO, CDC, JJM, NCVBDC are properly linked."""

    def test_sources_present_in_curriculum(self, canonical_curriculum):
        sources = {s["source_id"]: s for s in canonical_curriculum["sources"]}
        assert "src-who-vaccine-safety" in sources
        assert "src-mohfw-uip" in sources
        assert "src-dengue-and-severe-d-7821" in sources
        assert "src-ncvbdc-clinical" in sources
        assert "src-who-water-guidelines" in sources
        assert "src-jjm-water-tech" in sources

        # Verify source metadata
        assert sources["src-mohfw-uip"]["jurisdiction"] == "India"
        assert "nhm.gov.in" in sources["src-mohfw-uip"]["url"]

        assert sources["src-ncvbdc-clinical"]["jurisdiction"] == "India"
        assert "ncvbdc.mohfw.gov.in" in sources["src-ncvbdc-clinical"]["url"]

        assert sources["src-who-vaccine-safety"]["publisher"] == "World Health Organization"
        assert "who.int" in sources["src-who-vaccine-safety"]["url"]
