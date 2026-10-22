"""Vaccine Awareness & Immunity Topic (5 Chapters).

Topic ID: topic-vaccine
Chapters:
1. How Vaccines Help the Immune System (lesson-vaccine-basics) [STABLE ID]
2. Why Recommended Vaccination Schedules Matter (lesson-vaccination-schedules)
3. Understanding Common Reactions and When to Seek Medical Advice (lesson-vaccine-reactions-advice)
4. Addressing Vaccination Myths Through Respectful Conversations (lesson-vaccine-myths-conversations)
5. Preparing for a Vaccination Visit and Keeping Records (lesson-vaccination-visit-records)
"""

from __future__ import annotations


def get_vaccine_lessons() -> list[dict]:
    lessons = [
        {
            "lesson_id": "lesson-vaccine-basics",
            "topic_id": "topic-vaccine",
            "display_order": 1,
            "published_version_id": "ver-vaccine-basics-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-vaccination-schedules",
            "topic_id": "topic-vaccine",
            "display_order": 2,
            "published_version_id": "ver-vaccination-schedules-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-vaccine-reactions-advice",
            "topic_id": "topic-vaccine",
            "display_order": 3,
            "published_version_id": "ver-vaccine-reactions-advice-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-vaccine-myths-conversations",
            "topic_id": "topic-vaccine",
            "display_order": 4,
            "published_version_id": "ver-vaccine-myths-conversations-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-vaccination-visit-records",
            "topic_id": "topic-vaccine",
            "display_order": 5,
            "published_version_id": "ver-vaccination-visit-records-1",
            "draft_version_id": None,
        },
    ]

    versions = [
        # Chapter 1: How Vaccines Help the Immune System [STABLE ID: lesson-vaccine-basics]
        {
            "version_id": "ver-vaccine-basics-2",
            "lesson_id": "lesson-vaccine-basics",
            "version_number": 2,
            "title": "How Vaccines Help the Immune System",
            "summary": "Discover how vaccines act as a safe training drill for your immune system, teaching B and T lymphocytes to create lasting immunological memory without causing illness.",
            "language": "en",
            "learning_objectives": [
                "Explain how antigens in vaccines stimulate antibody production without causing active disease.",
                "Describe the role of memory B cells and memory T cells in providing long-term immunity.",
                "Contrast active immunity from vaccination with dangerous wild natural infection.",
                "Define herd immunity and explain how high coverage protects vulnerable community members.",
            ],
            "estimated_duration_minutes": 7,
            "status": "published",
            "source_ids": ["src-who-vaccines"],
            "cards": [
                {
                    "card_id": "vax-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Training Drill for White Blood Cells"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Ananya",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Dr. Joseph, how can injecting a tiny piece of a germ protect my body? Doesn't injecting a virus make me sick?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Dr. Joseph",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Think of a vaccine like a flight simulator or a training drill for fire fighters, Ananya! Vaccines introduce an inactivated germ, a harmless protein fragment, or weakened microbe called an 'antigen'. Your immune system learns to recognize the pathogen's unique shape, manufactures custom antibodies, and stores memory cells. Because the antigen is killed or disarmed, it CANNOT cause the actual disease!",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Immunology Simulator: Vaccines stimulate your immune system to produce antibodies and memory lymphocytes. If the real wild virus or bacterium ever enters your body in the future, your memory cells recognize it instantly and neutralize it before you can get sick.",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": None,
                },
                {
                    "card_id": "vax-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Sequence the Immune Response"},
                        {
                            "block_type": "text",
                            "body": "When a vaccine is administered, the immune system executes a precise biological sequence. Arrange these immunological steps in order from first to last.",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "arrange_steps",
                        "question_prompt": "Arrange the steps of how the immune system responds to a vaccine in correct chronological order:",
                        "options": [
                            {"option_id": "step-antigen-intro", "label": "1. Harmless antigen from the vaccine enters the body", "is_correct": True, "feedback": "Vaccine delivers safe, disarmed molecular markers."},
                            {"option_id": "step-wbc-detect", "label": "2. Antigen-presenting white blood cells detect and display the antigen pattern", "is_correct": True, "feedback": "Dendritic cells and macrophages sound the immune alarm."},
                            {"option_id": "step-b-cell-antibody", "label": "3. B-cells produce specific matching antibodies to bind the antigen", "is_correct": True, "feedback": "Custom antibodies tag and neutralize the target."},
                            {"option_id": "step-memory-store", "label": "4. Memory B and T cells are created and stored long-term in lymph nodes and bone marrow", "is_correct": True, "feedback": "Long-lived memory cells guarantee rapid defense upon future exposure."},
                        ],
                        "correct_order": ["step-antigen-intro", "step-wbc-detect", "step-b-cell-antibody", "step-memory-store"],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "vax-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Vaccination vs 'Natural' Infection"},
                        {
                            "block_type": "text",
                            "body": "Some people believe that getting naturally infected with wild diseases like measles, polio, or tetanus is 'better and more natural' than vaccination.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Lethal Risk of Natural Infection: While wild infection does produce antibodies, it comes with devastating risks: polio causes irreversible paralysis, measles triggers encephalitis and blindness, and tetanus causes fatal muscle spasms. Vaccines provide the exact same immunological memory WITHOUT paying the tragic price of organ damage or death.",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": None,
                },
                {
                    "card_id": "vax-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Myth vs Fact on Natural Immunity"},
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "myth_fact",
                        "question_prompt": "Statement: 'It is safer for a young child to catch wild measles naturally to build lifelong immunity than to receive the measles vaccine.'",
                        "options": [
                            {
                                "option_id": "vax-nat-myth",
                                "label": "Myth",
                                "is_correct": True,
                                "feedback": "Accurate! Wild measles causes severe pneumonia, permanent blindness, brain inflammation (subacute sclerosing panencephalitis), and death in 1 to 3 out of every 1,000 infected children. The measles vaccine safely builds protective immunity without risking disability or death.",
                            },
                            {
                                "option_id": "vax-nat-fact",
                                "label": "Fact",
                                "is_correct": False,
                                "feedback": "Dangerous misconception. Wild measles causes severe pediatric mortality and erases pre-existing immune memory ('immune amnesia'). Vaccination is overwhelmingly safer.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "vax-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is an 'antigen' in the context of vaccination science?",
                        "options": [
                            {
                                "option_id": "q1-antigen-marker",
                                "label": "A molecular surface structure or weakened fragment of a pathogen that triggers the immune system to produce targeted antibodies.",
                                "is_correct": True,
                                "feedback": "Exact immunological definition! Antigens are the molecular signatures that our immune cells recognize as foreign.",
                            },
                            {
                                "option_id": "q1-antigen-fuel",
                                "label": "A synthetic gasoline injected to speed up heart contractions.",
                                "is_correct": False,
                                "feedback": "Antigens are biological molecular proteins or sugars, not fuel.",
                            },
                            {
                                "option_id": "q1-antigen-bone",
                                "label": "A calcium mineral that replaces knee joints.",
                                "is_correct": False,
                                "feedback": "Antigens are immune-stimulating markers.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "vax-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What cell type is responsible for remembering a specific viral or bacterial pattern for decades after vaccination?",
                        "options": [
                            {
                                "option_id": "q2-memory-cells",
                                "label": "Memory B lymphocytes and Memory T lymphocytes.",
                                "is_correct": True,
                                "feedback": "Correct! Memory B and T cells persist in bone marrow and lymphoid tissue, mounting an immediate, overwhelming defense upon reinfection.",
                            },
                            {
                                "option_id": "q2-red-cells",
                                "label": "Mature red blood cells (erythrocytes).",
                                "is_correct": False,
                                "feedback": "Red blood cells carry oxygen and have no memory capacity.",
                            },
                            {
                                "option_id": "q2-hair-cells",
                                "label": "Outer fingernail keratin cells.",
                                "is_correct": False,
                                "feedback": "Fingernails are non-living keratin.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "vax-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is 'Community Immunity' (Herd Immunity)?",
                        "options": [
                            {
                                "option_id": "q3-herd-immunity",
                                "label": "When a high percentage of the population is immune, making pathogen spread difficult and protecting vulnerable people who cannot be vaccinated (newborns, chemotherapy patients).",
                                "is_correct": True,
                                "feedback": "Exact public health definition! Herd immunity acts as an invisible shield around medically vulnerable individuals who cannot produce their own antibodies.",
                            },
                            {
                                "option_id": "q3-cow-milk",
                                "label": "Drinking milk directly from dairy cattle to become immune to snakes.",
                                "is_correct": False,
                                "feedback": "Herd immunity refers to population-level immunological coverage.",
                            },
                            {
                                "option_id": "q3-isolation",
                                "label": "Living alone in a mountain cave for 10 years.",
                                "is_correct": False,
                                "feedback": "Community immunity depends on high collective vaccine uptake.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "vax-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why are booster doses required for certain vaccines (like Tetanus-Diphtheria or Hepatitis B)?",
                        "options": [
                            {
                                "option_id": "q4-booster-memory",
                                "label": "To remind the immune system and elevate declining antibody concentrations back to peak protective levels.",
                                "is_correct": True,
                                "feedback": "Correct! Over time, circulating antibody levels can wan; booster doses trigger rapid clonal expansion of memory cells.",
                            },
                            {
                                "option_id": "q4-booster-waste",
                                "label": "Because the first dose is designed to be completely destroyed by stomach acid.",
                                "is_correct": False,
                                "feedback": "Injected vaccines do not pass through stomach acid.",
                            },
                            {
                                "option_id": "q4-booster-bottle",
                                "label": "Because pharmaceutical companies only manufacture half-full vials.",
                                "is_correct": False,
                                "feedback": "Booster timing is dictated by human immunological memory decay curves.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "vax-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Can a vaccine made with inactivated (killed) bacteria or recombinant protein fragments cause the infectious disease it protects against?",
                        "options": [
                            {
                                "option_id": "q5-cannot-cause",
                                "label": "No. Inactivated or subunit vaccines contain no viable living microbes and are biologically incapable of replicating or causing the disease.",
                                "is_correct": True,
                                "feedback": "Spot on! Inactivated and subunit vaccines have zero replication capacity; mild post-vaccine fever is simply the immune system responding normally.",
                            },
                            {
                                "option_id": "q5-can-resurrect",
                                "label": "Yes. Dead viruses come back to life when injected into blood.",
                                "is_correct": False,
                                "feedback": "Killed and fragmented microbes cannot spontaneously resurrect.",
                            },
                            {
                                "option_id": "q5-turn-different",
                                "label": "Yes, but they turn into a completely different disease like malaria.",
                                "is_correct": False,
                                "feedback": "Pathogens cannot change species.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "vax-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Safe Training Simulator: Vaccines train your immune system with harmless antigens so memory cells neutralize wild infections swiftly.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Protect the Community: High vaccination coverage creates herd immunity, protecting newborns and vulnerable family members.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Check your personal vaccination status for Tetanus-Diphtheria (Td booster recommended every 10 years for adults) today!",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 2: Why Recommended Vaccination Schedules Matter
        {
            "version_id": "ver-vaccination-schedules-1",
            "lesson_id": "lesson-vaccination-schedules",
            "version_number": 1,
            "title": "Why Recommended Vaccination Schedules Matter",
            "summary": "Navigate India's National Immunization Schedule (NIS): critical birth doses, 6-10-14 week milestones, the 'Golden Window' of infant vulnerability, and catch-up rules.",
            "language": "en",
            "learning_objectives": [
                "Identify the core vaccines administered under India's Universal Immunization Programme (UIP).",
                "Explain why birth doses (BCG, OPV-0, Hepatitis B) must be given within the first 24 hours.",
                "Demonstrate the catch-up vaccination principle: never restart a delayed series from dose 1.",
                "Describe the multi-disease protection of combination vaccines (e.g., Pentavalent).",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-mohfw-uip", "src-who-vaccines"],
            "cards": [
                {
                    "card_id": "sched-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Worried Mother at the Health Centre"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Geeta",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Sister Leela, I feel so guilty! My baby was due for her 10-week Pentavalent and Rotavirus vaccines two weeks ago, but we had to travel for family emergency. Do we have to start all over again from the first dose? Has the protection expired?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Sister Leela (Nurse)",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Do not worry, Geeta! In immunology, the rule is: 'Catch up immediately—never restart!' The human immune memory does not forget previous doses. We will simply administer dose 2 today and schedule dose 3 four weeks later. No previous dose is ever wasted!",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Universal Catch-Up Rule: If a child misses a scheduled vaccination appointment, they DO NOT need to restart the entire series from dose 1. Simply visit the nearest Primary Health Centre or Anganwadi and resume from where you left off.",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": None,
                },
                {
                    "card_id": "sched-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Vaccines Administered at Birth"},
                        {
                            "block_type": "text",
                            "body": "Under India's Universal Immunization Programme (UIP), three essential vaccines are administered immediately after birth in institutional deliveries.",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all three essential vaccines given at birth (within 24-48 hours) under the National Immunization Schedule:",
                        "options": [
                            {"option_id": "birth-bcg", "label": "BCG (Bacille Calmette-Guérin for tuberculosis protection)", "is_correct": True, "feedback": "Protects infants from severe forms of pediatric TB (TB meningitis)."},
                            {"option_id": "birth-opv0", "label": "OPV-0 (Oral Polio Vaccine 'zero' birth dose)", "is_correct": True, "feedback": "Provides early gut mucosal immunity against polioviruses."},
                            {"option_id": "birth-hepb", "label": "Hepatitis B birth dose (within 24 hours of birth)", "is_correct": True, "feedback": "Prevents perinatal mother-to-child transmission of chronic Hepatitis B virus."},
                            {"option_id": "birth-mr", "label": "MR (Measles-Rubella vaccine)", "is_correct": False, "feedback": "MR is given at 9 to 12 months, after maternal antibodies wane, not at birth."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "sched-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "The 6, 10, 14 Week Infant Milestones"},
                        {
                            "block_type": "text",
                            "body": "Between 6 and 14 weeks of age, maternal antibodies passed through the placenta naturally begin to decline, leaving infants vulnerable.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Core UIP Primary Infant Series (at 6, 10, and 14 weeks):\n• Pentavalent: Combines 5 vaccines into a single shot (Diphtheria, Pertussis/Whooping Cough, Tetanus, Hepatitis B, and Hib bacteria preventing pneumonia and meningitis).\n• Rotavirus Vaccine: Oral drops preventing severe dehydrating diarrhea in infants.\n• Fractional IPV (fIPV): Inactivated polio vaccine given intradermally for reinforced systemic immunity.\n• Pneumococcal Conjugate Vaccine (PCV): Protects against deadly pneumococcal pneumonia.",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": None,
                },
                {
                    "card_id": "sched-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: The Golden Catch-Up Principle"},
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "If a baby's 14-week vaccination visit is delayed by 3 months due to illness or travel, what must the healthcare provider do?",
                        "options": [
                            {
                                "option_id": "catch-resume-next",
                                "label": "Administer the overdue 14-week dose immediately and resume the schedule without restarting from the beginning.",
                                "is_correct": True,
                                "feedback": "Correct! Immune memory persists; never restart an interrupted series. Continue from the missed dose.",
                            },
                            {
                                "option_id": "catch-restart-zero",
                                "label": "Force the baby to restart all doses from week 6 because all previous antibodies have vanished.",
                                "is_correct": False,
                                "feedback": "Previous doses established memory B-cells and are never wiped out by a schedule delay.",
                            },
                            {
                                "option_id": "catch-cancel-forever",
                                "label": "Refuse all further vaccines because missing a date disqualifies the child.",
                                "is_correct": False,
                                "feedback": "Public health systems actively welcome and encourage catch-up immunization at all ages.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "sched-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is the Hepatitis B birth dose recommended within the first 24 hours of birth?",
                        "options": [
                            {
                                "option_id": "q1-hepb-perinatal",
                                "label": "It prevents perinatal transmission of Hepatitis B from mother to newborn during delivery, preventing lifelong chronic liver cirrhosis.",
                                "is_correct": True,
                                "feedback": "Vital clinical knowledge! Over 90% of newborns infected perinatally develop chronic lifelong infection; birth vaccination stops this.",
                            },
                            {
                                "option_id": "q1-hepb-weight",
                                "label": "It makes the baby's birth weight double within two hours.",
                                "is_correct": False,
                                "feedback": "Hepatitis B vaccine does not double birth weight; its purpose is viral prophylaxis.",
                            },
                            {
                                "option_id": "q1-hepb-sleep",
                                "label": "It ensures the newborn sleeps without dreaming.",
                                "is_correct": False,
                                "feedback": "Vaccines prevent disease; they do not alter dreams.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "sched-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How many diseases are prevented by a single injection of the Pentavalent vaccine?",
                        "options": [
                            {
                                "option_id": "q2-five-diseases",
                                "label": "Five diseases: Diphtheria, Pertussis (Whooping Cough), Tetanus, Hepatitis B, and Haemophilus influenzae type b (Hib).",
                                "is_correct": True,
                                "feedback": "Correct! Combination vaccines reduce the number of separate injections from 5 down to 1, improving infant comfort and compliance.",
                            },
                            {
                                "option_id": "q2-two-diseases",
                                "label": "Only two diseases: Mumps and Rubella.",
                                "is_correct": False,
                                "feedback": "Pentavalent protects against five major pediatric diseases.",
                            },
                            {
                                "option_id": "q2-hundred-diseases",
                                "label": "Over 100 different tropical fungal conditions.",
                                "is_correct": False,
                                "feedback": "Pentavalent is specifically formulated for five targeted bacterial and viral pathogens.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "sched-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "At what age is the first dose of the Measles-Rubella (MR) vaccine administered under the National Immunization Schedule?",
                        "options": [
                            {
                                "option_id": "q3-9-12months",
                                "label": "At 9 to 12 completed months of age.",
                                "is_correct": True,
                                "feedback": "Exact public health milestone! By 9 months, maternal transplacental antibodies have waned sufficiently to allow the live-attenuated MR vaccine to take effect.",
                            },
                            {
                                "option_id": "q3-at-birth",
                                "label": "Immediately on the day of birth.",
                                "is_correct": False,
                                "feedback": "Maternal antibodies present at birth would neutralize the measles vaccine virus.",
                            },
                            {
                                "option_id": "q3-at-15years",
                                "label": "Only upon turning 15 years old.",
                                "is_correct": False,
                                "feedback": "Waiting until age 15 would leave infants vulnerable during their most dangerous years.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "sched-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What vaccine is routinely administered to pregnant women under India's national program to protect both mother and newborn from tetanus?",
                        "options": [
                            {
                                "option_id": "q4-td-pregnant",
                                "label": "Tetanus and adult Diphtheria (Td) vaccine (two doses or one booster during pregnancy).",
                                "is_correct": True,
                                "feedback": "Correct! Td vaccination in pregnancy induces maternal IgG antibodies that cross the placenta, eliminating neonatal tetanus (umbilical cord infection).",
                            },
                            {
                                "option_id": "q4-live-yellow-fever",
                                "label": "High-dose live Yellow Fever vaccine.",
                                "is_correct": False,
                                "feedback": "Live vaccines are generally avoided in pregnancy; Td is an inactivated toxoid.",
                            },
                            {
                                "option_id": "q4-zero-vaccines",
                                "label": "Zero vaccines are permitted during pregnancy.",
                                "is_correct": False,
                                "feedback": "Td is universally recommended and life-saving for both mother and child.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "sched-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the primary consequence of delaying scheduled infant vaccines beyond their recommended age windows?",
                        "options": [
                            {
                                "option_id": "q5-window-vulnerability",
                                "label": "It leaves the infant in an unprotected 'window of vulnerability' during the exact months when severe complications and death from pertussis, pneumonia, or rotavirus are highest.",
                                "is_correct": True,
                                "feedback": "Exact epidemiological rationale! Vaccines are timed to match the earliest moment an infant can mount immunity before natural exposure occurs.",
                            },
                            {
                                "option_id": "q5-police-fine",
                                "label": "The family receives an automatic police summons.",
                                "is_correct": False,
                                "feedback": "Public health immunization is supportive, not punitive.",
                            },
                            {
                                "option_id": "q5-fingerprint-lost",
                                "label": "The infant's biometric fingerprints disappear.",
                                "is_correct": False,
                                "feedback": "Vaccines do not alter fingerprints.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "sched-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Never Restart, Catch Up: If an immunization date is delayed, resume immediately from where you left off; previous doses remain valid.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Protect the First Year: Birth doses and 6-10-14 week combination shots close the critical window of infant vulnerability.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Locate the Mother and Child Protection (MCP) card or immunization record for any children in your family today. Verify that all age-appropriate vaccines are up to date!",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 3: Understanding Common Reactions and When to Seek Medical Advice
        {
            "version_id": "ver-vaccine-reactions-advice-1",
            "lesson_id": "lesson-vaccine-reactions-advice",
            "version_number": 1,
            "title": "Understanding Common Reactions and When to Seek Medical Advice",
            "summary": "Distinguish normal mild reactogenicity (low-grade fever, site soreness) from rare adverse events (AEFI), learn safe comforting measures, and master the 30-minute clinic observation rule.",
            "language": "en",
            "learning_objectives": [
                "Differentiate expected mild immune reactogenicity from Adverse Events Following Immunization (AEFI).",
                "Apply safe comfort measures for injection site tenderness and mild fever.",
                "Identify red-flag clinical symptoms that require immediate emergency evaluation.",
                "Explain the mandatory 30-minute post-vaccination clinic observation period.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
            "cards": [
                {
                    "card_id": "react-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Fretful Afternoon After the 6-Week Shot"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Manju",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Dr. Radhika, our baby had her 6-week vaccination this morning. Now her thigh where the needle went in is slightly swollen and pink, and she has a mild fever of 99.8°F. My neighbor told me to massage the thigh with hot mustard oil and rub ice cubes on it!",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Dr. Radhika",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Please, Manju, NEVER massage, press, or apply mustard oil or ice directly to a vaccination site! Massaging damages irritated muscle tissue and can introduce bacterial infections. Mild low-grade fever and slight redness are common, short-lived reactions as the body responds to the vaccine. However, fever is not required for the vaccine to work—babies without fever develop excellent protection too. Apply a clean, cool, damp cloth gently on the site, dress her in light clothing, and continue frequent breastfeeding. If she is very uncomfortable or fever persists, paracetamol may be given in a child-appropriate dose under a doctor's or health worker's guidance.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Common Reactions vs Red Flags: Mild low-grade fever (<38.5°C / 101.3°F), localized soreness, and slight fussiness are common, self-limiting reactions that typically subside within 24 to 48 hours. Lack of fever is equally normal and does not mean the vaccine was ineffective. Seek prompt medical care for persistent high fever, breathing difficulties, or excessive floppiness.",
                        },
                    ],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": None,
                },
                {
                    "card_id": "react-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Safe Injection Site Comfort"},
                    ],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the recommended, medically safe method to soothe a sore, tender thigh or arm after vaccination?",
                        "options": [
                            {
                                "option_id": "care-cool-cloth",
                                "label": "Place a clean, cool, damp cloth gently over the area and keep clothing loose; never massage the site or apply oils.",
                                "is_correct": True,
                                "feedback": "Correct! According to Indian MoHFW and WHO guidance, a clean, cool damp cloth soothes local discomfort without irritating muscle or risking infection. Never massage or apply oils.",
                            },
                            {
                                "option_id": "care-massage-oil",
                                "label": "Vigorously knead and massage the injection site with hot mustard oil and black pepper.",
                                "is_correct": False,
                                "feedback": "Vigorous massage traumatizes tissue, spreads inflammation, and invites secondary bacterial abscesses.",
                            },
                            {
                                "option_id": "care-tight-bandage",
                                "label": "Wrap an elastic tourniquet tightly around the limb to stop blood flow.",
                                "is_correct": False,
                                "feedback": "Tourniquets cause dangerous ischemia and tissue necrosis.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "react-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "The 30-Minute Clinic Observation Rule"},
                        {
                            "block_type": "text",
                            "body": "Severe allergic reactions (anaphylaxis) following vaccination are extraordinarily rare—occurring in approximately 1 to 2 per million doses. When they do occur, they almost always begin within minutes of injection.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The 30-Minute Observation Rule: Under Indian MoHFW Universal Immunization Programme (UIP) and WHO guidelines, every parent and beneficiary is advised to wait at the clinic or session site for at least 30 minutes following vaccination. In the rare event of an acute allergic reaction (such as facial swelling, hives, or breathing difficulty), healthcare personnel are trained and equipped with adrenaline and emergency supplies to treat it immediately and safely.",
                        },
                    ],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": None,
                },
                {
                    "card_id": "react-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Identifying Red-Flag Symptoms"},
                    ],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all rare red-flag symptoms that require immediate medical attention following a vaccination visit:",
                        "options": [
                            {"option_id": "red-flag-breathing", "label": "Difficulty breathing, persistent wheezing, or swelling of the face, lips, or throat", "is_correct": True, "feedback": "Signs of an acute allergic reaction requiring immediate emergency medical care."},
                            {"option_id": "red-flag-convulsion", "label": "Febrile seizures, convulsions, extreme lethargy / floppiness, or persistent inconsolable crying for several hours", "is_correct": True, "feedback": "Requires urgent medical assessment by a physician or health facility."},
                            {"option_id": "red-flag-high-fever", "label": "Persistent high fever (>39°C / 102.2°F) or large local redness spreading significantly beyond the injection site", "is_correct": True, "feedback": "Warrants prompt clinical evaluation to investigate and treat appropriately."},
                            {"option_id": "normal-mild-fuss", "label": "Mild fussiness, slight low-grade warmth, or wanting to nurse and rest more for an afternoon", "is_correct": False, "feedback": "Mild fussiness and slight warmth are common, temporary reactions that typically resolve within 1–2 days with comfort and rest."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "react-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How should common, mild post-vaccination reactions—such as low-grade fever or injection-site soreness—be understood regarding vaccine effectiveness?",
                        "options": [
                            {
                                "option_id": "q1-common-reaction",
                                "label": "They are common, temporary physiological responses to immune stimulation, but they are neither required for protection nor a measure of protective antibody levels.",
                                "is_correct": True,
                                "feedback": "Correct! While mild fever and soreness commonly occur, individuals who experience no fever or visible reaction still develop robust protective immunity. Reactions do not prove or measure antibody levels.",
                            },
                            {
                                "option_id": "q1-fever-mandatory",
                                "label": "A child must develop a fever above 39°C (102.2°F) for the vaccine to produce any protective antibodies.",
                                "is_correct": False,
                                "feedback": "Incorrect. Fever is neither required nor desirable for a vaccine to work; many children achieve full protective immunity without any fever.",
                            },
                            {
                                "option_id": "q1-fever-poison",
                                "label": "Any mild fever indicates that the syringe or vaccine was contaminated with toxic chemicals.",
                                "is_correct": False,
                                "feedback": "Incorrect. Mild transient warmth or low-grade fever is an expected, sterile biological response to immune stimulation, not chemical contamination.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "react-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why does Indian MoHFW and WHO immunization guidance recommend waiting at the healthcare facility for at least 30 minutes after receiving a vaccine?",
                        "options": [
                            {
                                "option_id": "q2-anaphylaxis-window",
                                "label": "In the rare event of an acute allergic reaction (anaphylaxis), trained healthcare personnel can promptly provide life-saving care with adrenaline.",
                                "is_correct": True,
                                "feedback": "Exact public health protocol! Severe acute reactions usually appear within minutes; immediate clinic evaluation and management effectively resolve them.",
                            },
                            {
                                "option_id": "q2-wait-for-mail",
                                "label": "To wait for a printed receipt to be mailed from the capital city.",
                                "is_correct": False,
                                "feedback": "The 30-minute wait is strictly for patient medical safety and surveillance.",
                            },
                            {
                                "option_id": "q2-wait-for-sunset",
                                "label": "Because leaving before sunset cancels the vaccine.",
                                "is_correct": False,
                                "feedback": "Sunlight has no effect on injected immunity.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "react-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why do clinical guidelines advise against routinely administering paracetamol to an infant BEFORE vaccination as a preventive measure?",
                        "options": [
                            {
                                "option_id": "q3-prophylactic-paracetamol",
                                "label": "Routine antipyretics before shots may slightly reduce initial antibody response; give paracetamol only afterwards if fever or distress occurs under guidance.",
                                "is_correct": True,
                                "feedback": "Correct! Routine preventive antipyretics before vaccination are discouraged; give paracetamol only if fever or discomfort actually develops post-shot under medical guidance.",
                            },
                            {
                                "option_id": "q3-paracetamol-stone",
                                "label": "Paracetamol turns vaccine liquid into solid chalk instantly.",
                                "is_correct": False,
                                "feedback": "Paracetamol does not turn vaccines into chalk.",
                            },
                            {
                                "option_id": "q3-paracetamol-sleep",
                                "label": "Because children are not allowed to sleep on clinic days.",
                                "is_correct": False,
                                "feedback": "Rest is encouraged; the issue is optimizing peak antibody induction.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "react-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the expected, normal reaction at the injection site several weeks after the BCG (tuberculosis) vaccine is given on the upper left arm?",
                        "options": [
                            {
                                "option_id": "q4-bcg-papule-scar",
                                "label": "A small red papule develops at 2-3 weeks, may form a tiny crust/shallow ulcer, and heals naturally into a small permanent round scar.",
                                "is_correct": True,
                                "feedback": "Classic BCG progression! This tiny scar is completely normal and confirms successful intradermal BCG vaccination.",
                            },
                            {
                                "option_id": "q4-bcg-turn-blue",
                                "label": "The whole arm turns bright blue for 5 years.",
                                "is_correct": False,
                                "feedback": "BCG causes a localized, tiny papule and scar, not whole-limb discoloration.",
                            },
                            {
                                "option_id": "q4-bcg-bone",
                                "label": "The arm bone disappears.",
                                "is_correct": False,
                                "feedback": "BCG is an intradermal vaccine with zero effect on skeletal bone structure.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "react-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is an AEFI (Adverse Event Following Immunization) reporting system designed to achieve in public health?",
                        "options": [
                            {
                                "option_id": "q5-aefi-surveillance",
                                "label": "Continuous post-licensure safety surveillance to detect any rare batch issues, maintain rigorous quality control, and ensure ongoing public safety.",
                                "is_correct": True,
                                "feedback": "Exact public health purpose! Robust pharmacovigilance and AEFI monitoring ensure vaccines are continuously scrutinized for safety.",
                            },
                            {
                                "option_id": "q5-aefi-tax",
                                "label": "To charge families a special government tax on injections.",
                                "is_correct": False,
                                "feedback": "AEFI is a medical safety monitoring system, not a taxation agency.",
                            },
                            {
                                "option_id": "q5-aefi-hide",
                                "label": "To conceal medical errors from doctors.",
                                "is_correct": False,
                                "feedback": "AEFI reporting is transparent and standardized to protect patient safety.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "react-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Common Reactions vs Protection: Mild low-grade fever and localized tenderness are common, temporary reactions that usually subside in 1–2 days. They are not required for immunity—individuals without fever gain robust protection as well.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Safe Comfort Care: Soothe injection-site tenderness with a clean, cool, damp cloth and loose clothing. Never massage, rub, or apply oils or ice. Use paracetamol under medical guidance if fever or discomfort requires it.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Wait 30 Minutes: Always remain at the clinic or session site for at least 30 minutes following vaccination for routine safety observation.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: When attending an immunization session, plan an extra 30 minutes to wait comfortably at the clinic so health workers can monitor your child safely before you head home.",
                        },
                    ],
                    "source_ids": ["src-who-vaccine-safety", "src-mohfw-uip"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 4: Addressing Vaccination Myths Through Respectful Conversations
        {
            "version_id": "ver-vaccine-myths-conversations-1",
            "lesson_id": "lesson-vaccine-myths-conversations",
            "version_number": 1,
            "title": "Addressing Vaccination Myths Through Respectful Conversations",
            "summary": "Debunk prominent vaccine myths with verified science (autism, fertility, immune overload) and master empathetic communication tools to address hesitancy respectfully.",
            "language": "en",
            "learning_objectives": [
                "Deconstruct the discredited Wakefield autism myth with decades of global scientific consensus.",
                "Explain why the human immune system easily handles multiple antigens simultaneously.",
                "Apply empathetic, respectful communication techniques when talking with vaccine-hesitant relatives.",
                "Identify authoritative public health information sources (WHO, MoHFW, CDC).",
            ],
            "estimated_duration_minutes": 7,
            "status": "published",
            "source_ids": ["src-who-vaccines", "src-mohfw-uip"],
            "cards": [
                {
                    "card_id": "myth-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Family Tea Conversation with Uncle Shashi"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Uncle Shashi",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Aarti, I saw a forwarded video on WhatsApp claiming that vaccines cause autism and that giving babies five vaccines at once overloads their tiny immune systems. We didn't have so many shots in our village 50 years ago, and we survived!",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Aarti",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Uncle Shashi, I understand why that video worried you—any caring family member would be concerned hearing that! But let me share what rigorous medical science has found. The autism claim originated from a single 1998 paper by Andrew Wakefield involving just 12 children that was fully retracted by the journal Lancet because the data was proven to be fraudulent. Since then, studies involving millions of children worldwide have proven conclusively that vaccines DO NOT cause autism.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Lancet Retraction: The 1998 Wakefield paper was thoroughly investigated, found to involve falsified records and financial conflicts of interest, and was fully retracted. Wakefield's medical license was revoked. Independent global studies encompassing millions of children have found zero link between vaccines and autism.",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": None,
                },
                {
                    "card_id": "myth-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Can Vaccines 'Overload' Immunity?"},
                        {
                            "block_type": "text",
                            "body": "Uncle Shashi asks whether giving multiple antigens at 6 weeks of age 'overwhelms' an infant's developing immune system.",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What does clinical immunology show regarding an infant's capacity to process multiple vaccine antigens?",
                        "options": [
                            {
                                "option_id": "cap-thousands-daily",
                                "label": "Infants encounter and handle thousands of bacteria, viruses, and environmental antigens daily from feeding and breathing; vaccines utilize only a tiny fraction of their immune capacity.",
                                "is_correct": True,
                                "feedback": "Exact immunological fact! Modern vaccines actually contain far FEWER total antigens than vaccines 40 years ago, while offering broader protection against deadly infections.",
                            },
                            {
                                "option_id": "cap-one-per-year",
                                "label": "An infant's body can only handle exactly one single antigen molecule per calendar year.",
                                "is_correct": False,
                                "feedback": "Every single gulp of milk and breath of air exposes an infant to hundreds of foreign environmental antigens safely.",
                            },
                            {
                                "option_id": "cap-fry-brain",
                                "label": "Multiple vaccines short-circuit neural electrical pathways.",
                                "is_correct": False,
                                "feedback": "Vaccines do not short-circuit neural pathways.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "myth-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Empathetic Communication: How to Talk with Loved Ones"},
                        {
                            "block_type": "text",
                            "body": "When loved ones express vaccine hesitation, mockery or angry arguments only make them defensive and entrench their fears.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The 4-Step Empathetic Conversation Model:\n1. Listen Without Judging: Acknowledge their concern ('I understand you want the best for your child').\n2. Validate the Emotion: Recognize that confusing internet rumors are frightening.\n3. Share Verified Evidence Calmly: Explain facts without medical jargon or condescension.\n4. Connect with Healthcare Workers: Offer to accompany them to discuss questions with a trusted doctor or nurse.",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": None,
                },
                {
                    "card_id": "myth-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Myth vs Fact on Fertility"},
                    ],
                    "source_ids": ["src-who-vaccines", "src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "myth_fact",
                        "question_prompt": "Statement: 'Vaccines, such as the polio drops or HPV vaccine, were secretly designed to cause infertility in young people.'",
                        "options": [
                            {
                                "option_id": "fertility-myth",
                                "label": "Myth",
                                "is_correct": True,
                                "feedback": "Accurate! This recurring conspiracy theory has been repeatedly debunked. Vaccines have zero negative effect on male or female fertility. In fact, vaccines like Rubella and HPV actively protect future pregnancies and prevent cervical cancer.",
                            },
                            {
                                "option_id": "fertility-fact",
                                "label": "Fact",
                                "is_correct": False,
                                "feedback": "Completely false and harmful rumor. Extensive long-term demographic and clinical monitoring across billions of individuals proves vaccines do not impair fertility.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "myth-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why was the 1998 Andrew Wakefield study linking the MMR vaccine to autism retracted by the Lancet medical journal?",
                        "options": [
                            {
                                "option_id": "q1-fraud-retraction",
                                "label": "Investigations proved the author falsified patient data, performed unethical procedures on children, and held undisclosed financial conflicts of interest.",
                                "is_correct": True,
                                "feedback": "Correct! Wakefield's paper was proven to be scientific fraud. Hundreds of subsequent global studies involving millions of children verified zero link.",
                            },
                            {
                                "option_id": "q1-print-error",
                                "label": "The printer ran out of ink on page 2.",
                                "is_correct": False,
                                "feedback": "The retraction was for proven fraud, ethical breaches, and falsified medical records.",
                            },
                            {
                                "option_id": "q1-author-forgot",
                                "label": "The author asked for it to be deleted because he changed his mind about medicine.",
                                "is_correct": False,
                                "feedback": "It was forcibly retracted by the editors following official regulatory findings of fraud.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "myth-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the best initial conversational approach when talking with a family member who is fearful of vaccines due to social media claims?",
                        "options": [
                            {
                                "option_id": "q2-listen-first",
                                "label": "Listen respectfully to understand their specific fears, validate their desire to keep family safe, and gently share verified clinical facts.",
                                "is_correct": True,
                                "feedback": "Correct! Empathetic listening builds trust, whereas condescension or ridicule pushes people further into conspiracy theories.",
                            },
                            {
                                "option_id": "q2-ridicule",
                                "label": "Mock them loudly in front of the whole family and call them uneducated.",
                                "is_correct": False,
                                "feedback": "Public humiliation breeds hostility and deepens vaccine hesitancy.",
                            },
                            {
                                "option_id": "q2-block-phone",
                                "label": "Secretly steal their phone and throw it in the trash.",
                                "is_correct": False,
                                "feedback": "Damaging property is destructive and fails to solve the underlying concern.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "myth-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How does modern vaccine composition compare to vaccines administered 40 years ago in terms of total immunological antigen load?",
                        "options": [
                            {
                                "option_id": "q3-fewer-antigens",
                                "label": "Modern biotechnology uses highly purified, specific proteins, meaning today's children receive far fewer total antigens despite being protected against more diseases.",
                                "is_correct": True,
                                "feedback": "Exact immunological reality! The whole-cell smallpox or old DTP vaccines contained thousands of antigens; modern acellular/subunit vaccines contain only a tiny fraction.",
                            },
                            {
                                "option_id": "q3-billions-more",
                                "label": "Modern vaccines contain 100 times more toxic chemicals than earlier vaccines.",
                                "is_correct": False,
                                "feedback": "Modern purification standards have drastically reduced unnecessary cellular debris.",
                            },
                            {
                                "option_id": "q3-exact-same",
                                "label": "Antigens have remained identical down to the microgram since 1796.",
                                "is_correct": False,
                                "feedback": "Immunological biochemistry has advanced substantially.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "myth-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why did previous generations 60 years ago have lower recorded rates of certain childhood chronic conditions compared to today?",
                        "options": [
                            {
                                "option_id": "q4-underdiagnosis-mortality",
                                "label": "Child mortality was catastrophically high (infants died of measles and polio before being diagnosed), and modern diagnostic criteria did not yet exist.",
                                "is_correct": True,
                                "feedback": "Essential historical context! High historical infant mortality and lack of modern screening masked conditions that are accurately recognized today.",
                            },
                            {
                                "option_id": "q4-magic-air",
                                "label": "The air 60 years ago was made of pure vitamin C.",
                                "is_correct": False,
                                "feedback": "Air chemistry was not vitamin C; infectious diseases killed millions of children.",
                            },
                            {
                                "option_id": "q4-superhuman",
                                "label": "Humans had superhuman immune systems that resisted all bacteria naturally.",
                                "is_correct": False,
                                "feedback": "History records devastating epidemics of smallpox, diphtheria, and polio before vaccines were developed.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "myth-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which of the following is considered an authoritative, trustworthy source for verifying vaccine safety information?",
                        "options": [
                            {
                                "option_id": "q5-official-sources",
                                "label": "The World Health Organization (WHO), Ministry of Health and Family Welfare (MoHFW), National Health Mission, and peer-reviewed medical journals.",
                                "is_correct": True,
                                "feedback": "Spot on! Public health agencies and verified peer-reviewed scientific consensus provide evidence-based guidance.",
                            },
                            {
                                "option_id": "q5-anonymous-forward",
                                "label": "An unverified anonymous voice note forwarded 50 times in a messaging app.",
                                "is_correct": False,
                                "feedback": "Unverified social media forwards are the primary vector for fabricated medical misinformation.",
                            },
                            {
                                "option_id": "q5-clickbait-tabloid",
                                "label": "A sensationalist tabloid blog selling untested herbal miracle cures.",
                                "is_correct": False,
                                "feedback": "Commercial blogs selling alternative products have severe financial conflicts of interest.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "myth-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Vaccines Do Not Cause Autism: The 1998 claim was proven to be scientific fraud; decades of global studies confirm vaccines are safe and save lives.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Listen and Connect: Address hesitation with empathy and verified facts from WHO and Ministry of Health sources.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: The next time you see an alarming health claim in a group chat, take two minutes to cross-check it against official MoHFW or WHO websites before sharing!",
                        },
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 5: Preparing for a Vaccination Visit and Keeping Records
        {
            "version_id": "ver-vaccination-visit-records-1",
            "lesson_id": "lesson-vaccination-visit-records",
            "version_number": 1,
            "title": "Preparing for a Vaccination Visit and Keeping Records",
            "summary": "Master practical clinic preparation: comfort positioning, proper clothing for injection sites, Mother and Child Protection (MCP) card / U-WIN records, and adult booster tracking.",
            "language": "en",
            "learning_objectives": [
                "Demonstrate practical preparation steps for an infant or child vaccination appointment.",
                "Apply recommended comfort positioning techniques during injection administration.",
                "Explain the importance of preserving physical and digital records (MCP card, U-WIN registry).",
                "Identify recommended adult booster vaccinations (Td, Influenza, HPV).",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-mohfw-uip", "src-who-vaccine-safety"],
            "cards": [
                {
                    "card_id": "visit-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Preparing for Little Maya's Clinic Visit"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Karthik",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Sister Mary, tomorrow is our daughter's vaccination day. Last time she cried so hard and I panicked because I couldn't find her vaccination booklet or roll up her tight jeans! How can we make tomorrow smoother?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Sister Mary",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Karthik, preparation makes all the difference! First, dress Maya in loose, comfortable clothes with snaps or loose shorts so her thighs can be reached without undressing. Second, bring her Mother and Child Protection (MCP) card. Third, feed her before leaving home so she isn't hungry. And during the shot, hold her upright in a warm embrace on your lap—your calm heartbeat comforts her far more than holding her down stiffly on a cold metal table!",
                        },
                        {
                            "block_type": "callout",
                            "body": "Comfort Holds vs Restraints: Holding a child upright in a comforting hug on a parent's lap significantly reduces procedural pain, distress, and crying compared to holding them flat on an examination table.",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": None,
                },
                {
                    "card_id": "visit-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Pre-Visit Checklist"},
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all recommended preparation steps before heading to a child's vaccination appointment:",
                        "options": [
                            {"option_id": "prep-mcp-card", "label": "Pack the Mother & Child Protection (MCP) card or immunization booklet", "is_correct": True, "feedback": "Ensures the vaccinator records batch numbers and verifies due vaccines."},
                            {"option_id": "prep-loose-clothes", "label": "Dress the child in loose clothing with easy access to upper thighs and arms", "is_correct": True, "feedback": "Allows rapid, calm access without struggling with tight garments."},
                            {"option_id": "prep-feed-comfort", "label": "Ensure the infant is fed and rested, and bring a favorite blanket or soft toy", "is_correct": True, "feedback": "Comfort items and satiety reduce physiological stress."},
                            {"option_id": "prep-scare-child", "label": "Threaten the child that the doctor will punish them with a big needle if they misbehave", "is_correct": False, "feedback": "Using medical care as a threat creates severe medical trauma and fear of healthcare workers."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "visit-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Keeping Digital & Physical Records (U-WIN & MCP)"},
                        {
                            "block_type": "text",
                            "body": "Immunization records are essential life documents required for school admissions, higher education, international travel, and clinical emergency care.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Digital Tracking in India: Through India's U-WIN portal (Universal Immunization Digital Registry), every child and pregnant woman is registered with an ABHA/immunization ID, enabling digital certificates and seamless tracking across all states and districts.",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": None,
                },
                {
                    "card_id": "visit-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Adult Boosters"},
                    ],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which vaccine booster is routinely recommended for all healthy adults once every 10 years?",
                        "options": [
                            {
                                "option_id": "vax-td-adult",
                                "label": "Tetanus and adult Diphtheria (Td) booster.",
                                "is_correct": True,
                                "feedback": "Exact clinical recommendation! Antibody levels against tetanus toxin wane over 10 years; a decennial Td booster ensures life-long protection against deep wound infections.",
                            },
                            {
                                "option_id": "vax-opv-daily",
                                "label": "Oral Polio drops every Friday afternoon.",
                                "is_correct": False,
                                "feedback": "Adults do not take weekly polio drops.",
                            },
                            {
                                "option_id": "vax-bcg-monthly",
                                "label": "Monthly BCG shots on alternating shoulders.",
                                "is_correct": False,
                                "feedback": "BCG is given once in infancy; monthly repeat injections are improper.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "visit-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-mohfw-uip"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the Mother and Child Protection (MCP) card used for in India's public healthcare system?",
                        "options": [
                            {
                                "option_id": "q1-mcp-purpose",
                                "label": "A comprehensive physical health document tracking antenatal visits, maternal health, child growth milestones, and complete immunization history.",
                                "is_correct": True,
                                "feedback": "Exact official role! The MCP card is the primary health and nutrition passport for mothers and children.",
                            },
                            {
                                "option_id": "q1-mcp-credit",
                                "label": "A bank credit card for purchasing groceries.",
                                "is_correct": False,
                                "feedback": "The MCP card is a health record, not a financial credit card.",
                            },
                            {
                                "option_id": "q1-mcp-bus",
                                "label": "A free bus pass for inter-city trains.",
                                "is_correct": False,
                                "feedback": "It is an immunization and maternal-child health tracking card.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "visit-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-vaccine-safety"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is the anterolateral (outer-upper) aspect of the thigh the standard recommended site for intramuscular injections in infants under 12 months?",
                        "options": [
                            {
                                "option_id": "q2-vastus-lateralis",
                                "label": "The vastus lateralis thigh muscle is well-developed with thick mass and has no major nerves or blood vessels that could be accidentally injured.",
                                "is_correct": True,
                                "feedback": "Crucial clinical anatomy! The gluteal (buttock) muscle in infants is underdeveloped and injection there risks injuring the sciatic nerve.",
                            },
                            {
                                "option_id": "q2-thigh-thinnest",
                                "label": "Because the thigh has no skin cells.",
                                "is_correct": False,
                                "feedback": "The thigh has normal skin; the reason is adequate muscle mass without nerve hazards.",
                            },
                            {
                                "option_id": "q2-needle-bend",
                                "label": "Because needles cannot penetrate infant shoulders.",
                                "is_correct": False,
                                "feedback": "Deltoid muscle mass in infants is too small for large intramuscular volumes.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "visit-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What should you do immediately if you lose the physical paper copy of your child's immunization booklet?",
                        "options": [
                            {
                                "option_id": "q3-replace-record",
                                "label": "Contact the administering clinic, hospital, or ASHA to retrieve records from the register or download your digital record from the U-WIN / health portal.",
                                "is_correct": True,
                                "feedback": "Correct! Healthcare centers maintain duplicate physical registers and digital U-WIN records, allowing replacement cards to be issued.",
                            },
                            {
                                "option_id": "q3-give-up",
                                "label": "Give up completely and pretend the child was never born.",
                                "is_correct": False,
                                "feedback": "Registers allow duplicate records to be issued easily.",
                            },
                            {
                                "option_id": "q3-invent-dates",
                                "label": "Guess dates and write them on a piece of cardboard.",
                                "is_correct": False,
                                "feedback": "Official clinic records must be consulted to ensure accurate medical history.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "visit-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-vaccines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which important cancer-preventing vaccine is recommended for adolescent girls (and boys) aged 9 to 14 years before sexual debut?",
                        "options": [
                            {
                                "option_id": "q4-hpv-vaccine",
                                "label": "Human Papillomavirus (HPV) vaccine.",
                                "is_correct": True,
                                "feedback": "Vital public health knowledge! The HPV vaccine prevents over 90% of cervical cancers and HPV-related malignancies.",
                            },
                            {
                                "option_id": "q4-rabies-routine",
                                "label": "Rabies vaccine every month.",
                                "is_correct": False,
                                "feedback": "Rabies vaccine is given post-exposure following animal bites, not as a routine adolescent shot.",
                            },
                            {
                                "option_id": "q4-cholera-daily",
                                "label": "Oral cholera vaccine every morning with breakfast.",
                                "is_correct": False,
                                "feedback": "Oral cholera vaccine is given in two doses during outbreaks, not daily.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "visit-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-vaccine-safety"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What vital safety information should a parent or adult always mention to the vaccinator BEFORE receiving an injection?",
                        "options": [
                            {
                                "option_id": "q5-allergies-previous",
                                "label": "Any known severe allergies (like anaphylaxis to previous vaccine doses or components) and any current acute high fever or illness.",
                                "is_correct": True,
                                "feedback": "Exact clinical safety check! Reporting previous severe reactions allows the healthcare provider to assess contraindications and verify safety.",
                            },
                            {
                                "option_id": "q5-favorite-movie",
                                "label": "The name of their favorite Bollywood actor.",
                                "is_correct": False,
                                "feedback": "Movie preferences have zero relevance to clinical contraindications.",
                            },
                            {
                                "option_id": "q5-shoe-size",
                                "label": "Their grandfather's shoe size.",
                                "is_correct": False,
                                "feedback": "Shoe size is irrelevant to clinical immunization triage.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "visit-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Prepare for Comfort: Dress children in loose clothes, feed them beforehand, and use comforting upright lap holds during injections.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Protect Your Records: Keep physical MCP cards safe and maintain digital records on U-WIN or smartphone cloud backups.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Take a clear photo of your and your family members' immunization cards with your smartphone today and save it in a dedicated 'Health Records' digital folder!",
                        },
                    ],
                    "source_ids": ["src-mohfw-uip", "src-who-vaccine-safety"],
                    "interaction": None,
                },
            ],
        },
    ]

    return lessons, versions
