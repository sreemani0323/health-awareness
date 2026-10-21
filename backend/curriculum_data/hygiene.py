"""Personal Hygiene Topic (5 Chapters).

Topic ID: topic-hygiene
Chapters:
1. The Invisible World of Germs (lesson-invisible-germs)
2. The Handwashing Challenge (lesson-handwashing) [REFERENCE CHAPTER]
3. Coughs, Sneezes, and Preventing the Spread of Infection (lesson-respiratory-hygiene)
4. Everyday Personal and Oral Hygiene (lesson-personal-oral-hygiene)
5. Keeping Shared Spaces Clean (lesson-shared-spaces-clean)
"""

from __future__ import annotations


def get_hygiene_lessons() -> list[dict]:
    lessons = [
        {
            "lesson_id": "lesson-invisible-germs",
            "topic_id": "topic-hygiene",
            "display_order": 1,
            "published_version_id": "ver-invisible-germs-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-handwashing",
            "topic_id": "topic-hygiene",
            "display_order": 2,
            "published_version_id": "ver-handwashing-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-respiratory-hygiene",
            "topic_id": "topic-hygiene",
            "display_order": 3,
            "published_version_id": "ver-respiratory-hygiene-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-personal-oral-hygiene",
            "topic_id": "topic-hygiene",
            "display_order": 4,
            "published_version_id": "ver-personal-oral-hygiene-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-shared-spaces-clean",
            "topic_id": "topic-hygiene",
            "display_order": 5,
            "published_version_id": "ver-shared-spaces-clean-1",
            "draft_version_id": None,
        },
    ]

    versions = [
        # Chapter 1: The Invisible World of Germs
        {
            "version_id": "ver-invisible-germs-1",
            "lesson_id": "lesson-invisible-germs",
            "version_number": 1,
            "title": "The Invisible World of Germs",
            "summary": "Understand how microscopic pathogens spread invisibly across everyday items, skin, and shared surfaces, and why visual cleanliness does not equal biological safety.",
            "language": "en",
            "learning_objectives": [
                "Differentiate between visible dirt and microscopic pathogens.",
                "Identify high-touch surface contamination hotspots in daily life.",
                "Explain the primary transmission routes of bacteria and viruses to mucosal membranes.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-hygiene", "src-cdc-hygiene"],
            "cards": [
                {
                    "card_id": "germs-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Quick Snack at the Study Table"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Priya",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "I'm starving after that three-hour exam! Let me just grab this samosa with one hand while I scroll through the lecture slides on my phone.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Kabir",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Wait, Priya! When was the last time you washed your hands or wiped down that phone screen? You took the metro, held the handrails, and worked on campus all morning.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Priya",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "My hands look completely clean, Kabir! There's no mud or grease on them. Why does it matter?",
                        },
                        {
                            "block_type": "callout",
                            "body": "Public Health Reality: Microscopic bacteria and viruses are 100 to 1,000 times smaller than the width of a human hair. A surface or hand that looks spotless can harbor tens of thousands of viable infectious pathogens.",
                        },
                    ],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": None,
                },
                {
                    "card_id": "germs-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Activity: Identify High-Touch Surface Hazards"},
                        {
                            "block_type": "text",
                            "body": "Priya's study desk has several items. In public health microbiology, which items are classified as high-touch fomites (objects capable of carrying and transmitting infectious organisms)?",
                        },
                    ],
                    "source_ids": ["src-cdc-hygiene"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all high-touch items on the study desk that act as primary microbial transfer points:",
                        "scene_description": "A study desk with a smartphone, a shared laptop keyboard, an open water bottle rim, a notebook paper page, and a plastic desk lamp base.",
                        "options": [
                            {
                                "option_id": "risk-phone",
                                "label": "Smartphone touchscreen",
                                "is_correct": True,
                                "feedback": "Correct! Touchscreens collect oils and pathogens from fingers throughout the day and are held directly against the face.",
                            },
                            {
                                "option_id": "risk-keyboard",
                                "label": "Shared laptop keyboard & mouse",
                                "is_correct": True,
                                "feedback": "Correct! Keyboards collect dead skin cells, food particles, and respiratory droplets from multiple touches.",
                            },
                            {
                                "option_id": "risk-bottle-rim",
                                "label": "Water bottle mouth rim",
                                "is_correct": True,
                                "feedback": "Correct! Touching or sipping from an unwashed bottle rim transfers oral and skin bacteria directly into water.",
                            },
                            {
                                "option_id": "risk-paper",
                                "label": "Dry notebook paper page",
                                "is_correct": False,
                                "feedback": "Dry porous paper generally carries a much lower transmission risk than smooth, non-porous glass or plastic surfaces.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "germs-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "How Microbes Invade the Body"},
                        {
                            "block_type": "text",
                            "body": "Intact skin is one of the body's strongest defensive barriers. Microorganisms generally cannot penetrate healthy, unbroken skin. The danger occurs when contaminated fingertips touch the 'T-zone' of the face: the eyes, nose, and mouth.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Did you know? Observational public health studies reveal that the average person touches their face 16 to 23 times per hour. Each touch can inoculate respiratory or gastrointestinal viruses directly into mucous membranes.",
                        },
                    ],
                    "source_ids": ["src-who-hygiene", "src-cdc-hygiene"],
                    "interaction": None,
                },
                {
                    "card_id": "germs-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Myth vs Fact: Cleanliness vs Disinfection"},
                    ],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "myth_fact",
                        "question_prompt": "Statement: 'If a dining table looks glossy and smells like lemon air freshener, it is free of illness-causing bacteria.'",
                        "options": [
                            {
                                "option_id": "opt-myth",
                                "label": "Myth",
                                "is_correct": True,
                                "feedback": "Accurate! Aesthetic shine and fragrances do not kill germs. True disinfection requires physical removal of dirt followed by an active antimicrobial agent with adequate contact time.",
                            },
                            {
                                "option_id": "opt-fact",
                                "label": "Fact",
                                "is_correct": False,
                                "feedback": "Incorrect. Fragrances and visual shine mask odours and grease but do not inactivate pathogens without proper chemical disinfection.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Quiz questions 1 to 5
                {
                    "card_id": "germs-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the primary way that respiratory viruses on contaminated surfaces enter the human body?",
                        "options": [
                            {
                                "option_id": "q1-a",
                                "label": "They are absorbed directly through unbroken skin on the palms.",
                                "is_correct": False,
                                "feedback": "Unbroken skin is a formidable barrier and does not absorb intact respiratory viruses.",
                            },
                            {
                                "option_id": "q1-b",
                                "label": "Contaminated hands transfer pathogens to the eyes, nose, or mouth mucous membranes.",
                                "is_correct": True,
                                "feedback": "Correct! Mucous membranes in the eyes, nose, and mouth allow viral attachment and cell entry.",
                            },
                            {
                                "option_id": "q1-c",
                                "label": "They multiply on fingernails and penetrate directly into the bloodstream.",
                                "is_correct": False,
                                "feedback": "Nails do not provide direct bloodstream access unless there is an open laceration or infected nailbed.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "germs-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Assessment Question 2 of 5"}],
                    "source_ids": ["src-cdc-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is wiping a phone or desk with a dry cloth or clothing sleeve ineffective against bacteria?",
                        "options": [
                            {
                                "option_id": "q2-a",
                                "label": "It spreads surface oils and pathogens across a wider area without removing or inactivating them.",
                                "is_correct": True,
                                "feedback": "Correct! Dry wiping lacks surfactants or sanitizing agents, merely redistributing microbes across the surface.",
                            },
                            {
                                "option_id": "q2-b",
                                "label": "Dry cloth friction generates heat that accelerates bacterial multiplication instantly.",
                                "is_correct": False,
                                "feedback": "Cloth friction does not generate sufficient heat to promote microbial growth.",
                            },
                            {
                                "option_id": "q2-c",
                                "label": "Clothing fibers chemically react with viruses to make them resistant to future soap.",
                                "is_correct": False,
                                "feedback": "Fabric fibers have no chemical mutagenic effect on viruses.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "germs-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Under typical room temperature and humidity, how long can influenza and noroviruses survive on hard, non-porous plastic surfaces?",
                        "options": [
                            {
                                "option_id": "q3-a",
                                "label": "Only 2 to 3 seconds before naturally dying in air.",
                                "is_correct": False,
                                "feedback": "Viruses survive significantly longer than a few seconds on inert surfaces.",
                            },
                            {
                                "option_id": "q3-b",
                                "label": "From several hours up to multiple days depending on the specific pathogen.",
                                "is_correct": True,
                                "feedback": "Correct! Influenza can persist for 24-48 hours on hard plastics, while norovirus can survive for days to weeks.",
                            },
                            {
                                "option_id": "q3-c",
                                "label": "Indefinitely for decades without any loss of virulence.",
                                "is_correct": False,
                                "feedback": "Environmental factors like desiccation, UV light, and temperature gradually degrade viral infectivity.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "germs-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Assessment Question 4 of 5"}],
                    "source_ids": ["src-cdc-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the primary scientific difference between 'cleaning' and 'disinfecting' in infection control?",
                        "options": [
                            {
                                "option_id": "q4-a",
                                "label": "Cleaning physically removes dirt and germs; disinfecting uses chemicals to kill or inactivate remaining pathogens.",
                                "is_correct": True,
                                "feedback": "Exact definition! Cleaning with soap and water removes organic loads, while disinfectants destroy residual organisms.",
                            },
                            {
                                "option_id": "q4-b",
                                "label": "Cleaning is done in hospitals, whereas disinfecting is only done in food preparation.",
                                "is_correct": False,
                                "feedback": "Both cleaning and disinfection are practiced across domestic, community, and clinical settings.",
                            },
                            {
                                "option_id": "q4-c",
                                "label": "Disinfecting removes visible grease, while cleaning only removes pleasant fragrances.",
                                "is_correct": False,
                                "feedback": "Cleaning is what removes visible grease and organic soil.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "germs-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which everyday habit provides the greatest reduction in pathogen transfer from high-touch surfaces to the body?",
                        "options": [
                            {
                                "option_id": "q5-a",
                                "label": "Washing hands with soap and water before eating or touching the face.",
                                "is_correct": True,
                                "feedback": "Spot on! Hand hygiene breaks the chain of infection before pathogens can enter mucosal membranes.",
                            },
                            {
                                "option_id": "q5-b",
                                "label": "Wearing cloth gloves continuously throughout the day without washing them.",
                                "is_correct": False,
                                "feedback": "Gloves become contaminated just like hands and transfer pathogens if used to touch the face.",
                            },
                            {
                                "option_id": "q5-c",
                                "label": "Spraying room air freshener every hour in study spaces.",
                                "is_correct": False,
                                "feedback": "Air fresheners do not neutralize pathogens on hands or surfaces.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "germs-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary: Key Takeaways & Everyday Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Invisible Microbes: Clear and shiny surfaces can carry infectious loads. High-touch items like smartphones, handles, and keyboards require regular cleaning.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Protect Your T-Zone: Avoid touching your eyes, nose, and mouth with unwashed hands.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Everyday Action: Wipe your smartphone and study desk with a 70% alcohol wipe or damp soapy microfiber cloth today, and always wash hands before snacking.",
                        },
                    ],
                    "source_ids": ["src-who-hygiene", "src-cdc-hygiene"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 2: The Handwashing Challenge [REFERENCE CHAPTER]
        {
            "version_id": "ver-handwashing-2",
            "lesson_id": "lesson-handwashing",
            "version_number": 2,
            "title": "The Handwashing Challenge",
            "summary": "Master the verified 20-second handwashing technique with soap and water through the real-world story of Meera and Arun, learning molecular mechanics and critical community moments.",
            "language": "en",
            "learning_objectives": [
                "Explain the molecular mechanism of soap in lifting microbes from skin folds.",
                "Demonstrate the correct 5-step sequence of handwashing recommended by WHO and CDC.",
                "Identify the five essential everyday community moments for hand hygiene.",
                "Evaluate why brief rinsing with water alone fails to eliminate infection risk.",
            ],
            "estimated_duration_minutes": 7,
            "status": "published",
            "source_ids": ["src-who-hygiene", "src-cdc-hygiene"],
            "cards": [
                {
                    "card_id": "hw-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Conversation at the Kitchen Sink"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Meera",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Lunch is ready! Why are you still at the sink?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Arun",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "I rinsed my hands already. Isn't that enough?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Meera",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Let's find out what actually makes handwashing effective. A quick three-second rinse only wets the skin—it leaves grease, bacteria, and viruses right where they are.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Science of Skin Sebum: Your skin naturally produces natural oils (sebum). Pathogens cling tightly to this fatty layer. Water alone cannot dissolve oil, meaning plain water flows straight off without removing the microbes.",
                        },
                    ],
                    "source_ids": ["src-who-hygiene", "src-cdc-hygiene"],
                    "interaction": None,
                },
                {
                    "card_id": "hw-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Learner Decision: How Does Soap Work?"},
                        {
                            "block_type": "text",
                            "body": "Arun looks at the soap bar on the counter. If you were Arun, what is the scientific reason for lathering with soap rather than using water alone?",
                        },
                    ],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What actually happens at the microscopic level when soap interacts with germs and skin oil?",
                        "options": [
                            {
                                "option_id": "opt-hw-soap-1",
                                "label": "Soap molecules have two ends: one binds to water, the other binds to oil and germ membranes, lifting them into the lather to be rinsed away.",
                                "is_correct": True,
                                "feedback": "Correct! Soap's amphipathic molecules pry apart lipid-enveloped viruses and surround bacteria in tiny droplets (micelles) that running water washes down the drain.",
                            },
                            {
                                "option_id": "opt-hw-soap-2",
                                "label": "Soap acts as a chemical poison that instantly burns all germs on contact within one second.",
                                "is_correct": False,
                                "feedback": "Incorrect. Standard hand soap is not a chemical poison; its power lies in mechanical surfactant action and physical friction.",
                            },
                            {
                                "option_id": "opt-hw-soap-3",
                                "label": "Soap merely adds a pleasant scent to mask dirty hands without removing pathogens.",
                                "is_correct": False,
                                "feedback": "Incorrect. Fragrance is incidental; soap's surfactant chemistry is what safely lifts microbes from skin folds.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Visualizing the 5 Steps of Handwashing"},
                        {
                            "block_type": "text",
                            "body": "The World Health Organization (WHO) and CDC established a validated 5-step sequence for hand hygiene in community settings. Achieving clean hands is not about scalding hot water—it is about friction, coverage, and lather duration.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The 20-Second Benchmark: Scrubbing for at least 20 seconds is necessary to cover palms, backs of hands, thumbs, finger webs, and under fingernails. A good timing tool is humming 'Happy Birthday' or your favorite nursery rhyme twice.",
                        },
                    ],
                    "source_ids": ["src-cdc-hygiene", "src-who-hygiene"],
                    "interaction": None,
                },
                {
                    "card_id": "hw-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Sequence the Steps"},
                        {
                            "block_type": "text",
                            "body": "Help Arun follow the proper public health procedure. Arrange these 5 handwashing steps into the correct chronological order from first to last.",
                        },
                    ],
                    "source_ids": ["src-cdc-hygiene"],
                    "interaction": {
                        "interaction_type": "arrange_steps",
                        "question_prompt": "Arrange the 5 steps of effective handwashing in the correct sequence:",
                        "options": [
                            {"option_id": "step-wet", "label": "1. Wet hands with clean running water (warm or cold)", "is_correct": True, "feedback": "Wet first to allow soap lather to spread."},
                            {"option_id": "step-soap", "label": "2. Apply soap and lather thoroughly across all hand surfaces", "is_correct": True, "feedback": "Lather fully to engage surfactants."},
                            {"option_id": "step-scrub", "label": "3. Scrub palms, backs, thumbs, finger webs, and nails for at least 20 seconds", "is_correct": True, "feedback": "Friction lifts pathogens from skin folds."},
                            {"option_id": "step-rinse", "label": "4. Rinse hands thoroughly under clean running water", "is_correct": True, "feedback": "Rinsing carries suspended micelles and germs away."},
                            {"option_id": "step-dry", "label": "5. Dry hands completely with a clean towel or air dry", "is_correct": True, "feedback": "Dry skin prevents pathogen re-adhesion."},
                        ],
                        "correct_order": ["step-wet", "step-soap", "step-scrub", "step-rinse", "step-dry"],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Everyday Community Moments"},
                        {
                            "block_type": "text",
                            "body": "In community life, when is handwashing mandatory to prevent illness transmission across family members?",
                        },
                    ],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all essential community moments when you must wash your hands with soap and water:",
                        "options": [
                            {
                                "option_id": "mom-before-eat",
                                "label": "Before eating food or feeding a child",
                                "is_correct": True,
                                "feedback": "Prevents direct ingestion of pathogens into the gastrointestinal tract.",
                            },
                            {
                                "option_id": "mom-after-toilet",
                                "label": "After using the toilet or cleaning a child who used the toilet",
                                "is_correct": True,
                                "feedback": "Critical to block the fecal-oral route of diarrhea and cholera transmission.",
                            },
                            {
                                "option_id": "mom-after-cough",
                                "label": "After blowing your nose, coughing, or sneezing into hands",
                                "is_correct": True,
                                "feedback": "Removes respiratory droplet secretions before touching shared objects.",
                            },
                            {
                                "option_id": "mom-before-food",
                                "label": "Before and during the preparation of meals",
                                "is_correct": True,
                                "feedback": "Prevents cross-contamination of raw and cooked foodstuffs.",
                            },
                            {
                                "option_id": "mom-after-phone",
                                "label": "Every single time you send a text message on your personal phone",
                                "is_correct": False,
                                "feedback": "While keeping phones clean is good practice, routine texting without soiling does not require immediate water-and-soap washing.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Chapter Assessment Q1 to Q5
                {
                    "card_id": "hw-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-cdc-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the minimum scrubbing time recommended by the CDC and WHO when washing hands with soap?",
                        "options": [
                            {
                                "option_id": "q1-5s",
                                "label": "5 to 10 seconds",
                                "is_correct": False,
                                "feedback": "Too short! Brief scrubbing fails to create sufficient friction to dislodge microbes from crevices.",
                            },
                            {
                                "option_id": "q1-20s",
                                "label": "At least 20 seconds",
                                "is_correct": True,
                                "feedback": "Correct! 20 seconds of mechanical friction allows soap lather to lift stubborn microbes from all skin areas.",
                            },
                            {
                                "option_id": "q1-60s",
                                "label": "At least 2 minutes of vigorous scraping",
                                "is_correct": False,
                                "feedback": "Excessive scraping can irritate skin, creating microscopic cracks that harbor microbes.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "When is an alcohol-based hand rub NOT an acceptable substitute for soap and running water?",
                        "options": [
                            {
                                "option_id": "q2-visibly-dirty",
                                "label": "When hands are visibly dirty, covered in grease, or contaminated with body fluids or feces.",
                                "is_correct": True,
                                "feedback": "Correct! Alcohol sanitizers cannot penetrate heavy soil or grease and are less effective against norovirus or bacterial spores.",
                            },
                            {
                                "option_id": "q2-indoors",
                                "label": "Whenever you are inside a residential building rather than outdoors.",
                                "is_correct": False,
                                "feedback": "Location is irrelevant; visible cleanliness and soiling determine when soap and water are mandatory.",
                            },
                            {
                                "option_id": "q2-cold-weather",
                                "label": "When the outdoor temperature falls below 20 degrees Celsius.",
                                "is_correct": False,
                                "feedback": "Ambient temperature does not impair alcohol hand rub efficacy.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which areas of the hands are most frequently missed when people rush through handwashing?",
                        "options": [
                            {
                                "option_id": "q3-palms",
                                "label": "The centers of the palms",
                                "is_correct": False,
                                "feedback": "Palms receive the majority of friction during simple rubbing.",
                            },
                            {
                                "option_id": "q3-thumbs-nails",
                                "label": "The thumbs, web spaces between fingers, backs of hands, and under the fingernails",
                                "is_correct": True,
                                "feedback": "Correct! Observational studies show thumbs, interdigital webs, and subungual areas are most commonly neglected.",
                            },
                            {
                                "option_id": "q3-wrists",
                                "label": "Only the forearm skin above the wrists",
                                "is_correct": False,
                                "feedback": "While wrists can be included, the high-contact fingertips, thumbs, and webs are the key neglected zones.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-cdc-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What does public health evidence say about using very hot water for handwashing?",
                        "options": [
                            {
                                "option_id": "q4-hot-better",
                                "label": "Scalding hot water kills all viruses instantly without needing soap.",
                                "is_correct": False,
                                "feedback": "Water hot enough to kill germs on contact would cause severe thermal burns to human skin.",
                            },
                            {
                                "option_id": "q4-temp-unimportant",
                                "label": "Water temperature does not affect germ removal; warm or cold clean running water works equally well, while very hot water damages skin.",
                                "is_correct": True,
                                "feedback": "Exact evidence! Friction, soap lather, and clean running water remove germs. Hot water increases skin irritation without added microbial benefit.",
                            },
                            {
                                "option_id": "q4-cold-preserves",
                                "label": "Cold water freezes bacteria onto the skin so they can never be rinsed off.",
                                "is_correct": False,
                                "feedback": "Tap water is never cold enough to freeze bacteria; running water rinses them away equally well.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-10",
                    "position": 10,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is drying hands thoroughly with a clean towel or air dryer a necessary step of hand hygiene?",
                        "options": [
                            {
                                "option_id": "q5-damp-transfer",
                                "label": "Wet and damp hands transfer bacteria up to 1,000 times more readily to door handles and food than dry hands.",
                                "is_correct": True,
                                "feedback": "Scientifically verified! Moisture facilitates bacterial transmission. Drying completes the protective barrier.",
                            },
                            {
                                "option_id": "q5-towel-antiviral",
                                "label": "Clean cotton towels produce antimicrobial static electricity that sterilizes skin.",
                                "is_correct": False,
                                "feedback": "Towels do not produce antimicrobial electricity; their role is mechanical moisture absorption.",
                            },
                            {
                                "option_id": "q5-drying-not-needed",
                                "label": "Drying is actually discouraged because water drops protect skin from sunlight.",
                                "is_correct": False,
                                "feedback": "Leaving hands wet facilitates microbial re-adhesion from subsequent touches.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "hw-card-11",
                    "position": 11,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Arun's Takeaway & Chapter Recap"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Arun",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Now I understand! It's not just splashing water for three seconds. The soap lather and 20 seconds of friction are what actually loosen the germs so they wash down the sink.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "The 20-Second Clean Rule: Wet, soap, scrub for 20 seconds (including thumbs and between fingers), rinse, and dry completely.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Soap Beats Plain Water: Surfactants dissolve the lipid envelopes of viruses and carry away trapped bacteria in lather.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Commit to the full 20-second soap scrub before your very next meal today!",
                        },
                    ],
                    "source_ids": ["src-who-hygiene", "src-cdc-hygiene"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 3: Coughs, Sneezes, and Preventing the Spread of Infection
        {
            "version_id": "ver-respiratory-hygiene-1",
            "lesson_id": "lesson-respiratory-hygiene",
            "version_number": 1,
            "title": "Coughs, Sneezes, and Preventing the Spread of Infection",
            "summary": "Learn respiratory droplet dynamics, the elbow-bend cough technique, safe mask handling, and how indoor ventilation halts airborne transmission.",
            "language": "en",
            "learning_objectives": [
                "Demonstrate the correct respiratory cough etiquette using a tissue or flexed elbow.",
                "Explain how droplet distance and aerosol dispersion drive respiratory infection spread.",
                "Identify safe mask donning, wearing, and disposal protocols.",
                "Evaluate the role of natural cross-ventilation in shared indoor environments.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-mohfw-respiratory", "src-who-hygiene"],
            "cards": [
                {
                    "card_id": "resp-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Sneeze on the Morning Metro"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Vikram",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Achoo! Whew... I managed to catch that sneeze right in my bare palms. At least I didn't spray the person standing next to me!",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Anita",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Vikram, thank you for trying, but look at your hand right now. You're holding onto the stainless steel overhead grab pole with that exact same hand!",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Vikram",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Oh no. Everyone who grabs this pole after me will pick up whatever virus I have.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Droplet Dispersion: A single unshielded sneeze expels up to 40,000 microscopic droplet particles at speeds exceeding 100 km/h, traveling 1 to 2 meters. Catching them in bare hands turns your palms into viral transfer pads.",
                        },
                    ],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": None,
                },
                {
                    "card_id": "resp-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: The Elbow Shield"},
                        {
                            "block_type": "text",
                            "body": "When you feel an involuntary cough or sneeze coming and do not have a clean tissue in hand, what is the safest technique?",
                        },
                    ],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the recommended public health technique when sneezing without a disposable tissue?",
                        "options": [
                            {
                                "option_id": "resp-opt-elbow",
                                "label": "Cough or sneeze into the inner crook of your flexed elbow, sealing your nose and mouth.",
                                "is_correct": True,
                                "feedback": "Correct! The inside of your elbow rarely touches shared surfaces, door handles, or other people's hands.",
                            },
                            {
                                "option_id": "resp-opt-hands",
                                "label": "Cover your mouth tightly with both bare hands and wipe them on your trousers.",
                                "is_correct": False,
                                "feedback": "Wiping hands on fabric does not disinfect them; pathogens transfer directly to anything you touch next.",
                            },
                            {
                                "option_id": "resp-opt-turn",
                                "label": "Turn your head sideways and sneeze into the open room aisle without covering.",
                                "is_correct": False,
                                "feedback": "Sneezing into open air propels infectious droplets across the room into others' breathing zones.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "resp-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Ventilation: Diluting Indoor Airborne Microbes"},
                        {
                            "block_type": "text",
                            "body": "When someone with a respiratory infection speaks, coughs, or breathes in an enclosed room, tiny aerosolized particles remain suspended in stagnant air for minutes to hours.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Power of Cross-Ventilation: Opening opposite windows and doors creates a cross-breeze that rapidly replaces stale indoor air with fresh outdoor air, diluting airborne viral concentrations by over 80%.",
                        },
                    ],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": None,
                },
                {
                    "card_id": "resp-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Identify Mask & Hygiene Hazards"},
                    ],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all unsafe actions when managing respiratory symptoms in public:",
                        "scene_description": "Commuters on a public bus: one pulling mask under chin, one touching the front of mask repeatedly, one opening a window, and one stuffing a wet tissue into a pocket.",
                        "options": [
                            {
                                "option_id": "risk-mask-chin",
                                "label": "Pulling a face mask down under the chin to talk or sneeze",
                                "is_correct": True,
                                "feedback": "Contaminates the inner mask with neck skin bacteria and exposes surrounding passengers to droplets.",
                            },
                            {
                                "option_id": "risk-touch-front",
                                "label": "Constantly adjusting the mask by grabbing its front fabric",
                                "is_correct": True,
                                "feedback": "The front of a mask filters and concentrates airborne particles; touching it contaminates your fingers.",
                            },
                            {
                                "option_id": "risk-pocket-tissue",
                                "label": "Stuffing a used, wet tissue back into a pocket for reuse later",
                                "is_correct": True,
                                "feedback": "Used tissues should be discarded immediately into a closed bin, not saved in pockets.",
                            },
                            {
                                "option_id": "safe-open-window",
                                "label": "Cracking open the bus window to allow fresh air flow",
                                "is_correct": False,
                                "feedback": "This is a safe and beneficial action that improves ventilation.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "resp-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the proper method for discarding a used disposable paper tissue after blowing your nose?",
                        "options": [
                            {
                                "option_id": "q1-t-bin",
                                "label": "Throw it immediately into a closed waste bin and wash hands with soap or alcohol rub.",
                                "is_correct": True,
                                "feedback": "Correct! Immediate disposal in a closed bin prevents environmental contamination and flies.",
                            },
                            {
                                "option_id": "q1-t-table",
                                "label": "Leave it on the desk or armrest until the end of the day.",
                                "is_correct": False,
                                "feedback": "Leaving soiled tissues on surfaces creates fomite risks for anyone touching the table.",
                            },
                            {
                                "option_id": "q1-t-pocket",
                                "label": "Fold it up and store it in your trousers pocket to use several more times.",
                                "is_correct": False,
                                "feedback": "Reusing damp tissues reinoculates bacteria and contaminates clothing and hands.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "resp-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why should you handle a medical or cloth face mask only by its ear loops or head ties?",
                        "options": [
                            {
                                "option_id": "q2-m-loops",
                                "label": "The outer front surface collects and concentrates respiratory droplets; touching it contaminates hands.",
                                "is_correct": True,
                                "feedback": "Spot on! The front filter layer traps microbes; handling by loops prevents fingertip contamination.",
                            },
                            {
                                "option_id": "q2-m-fray",
                                "label": "Touching the fabric causes the cotton threads to instantly dissolve.",
                                "is_correct": False,
                                "feedback": "Mask fabric does not dissolve from touch; the reason is strictly microbiological safety.",
                            },
                            {
                                "option_id": "q2-m-loose",
                                "label": "Touching the front breaks the elastic stretch of the ear straps.",
                                "is_correct": False,
                                "feedback": "The straps are located at the sides, not the front.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "resp-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How does cross-ventilation in shared rooms lower the risk of respiratory infection transmission?",
                        "options": [
                            {
                                "option_id": "q3-v-dilute",
                                "label": "It continuously flushes stagnant indoor air and dilutes viral aerosol concentrations with fresh air.",
                                "is_correct": True,
                                "feedback": "Correct! Air exchange removes viral bioaerosols that would otherwise linger and accumulate.",
                            },
                            {
                                "option_id": "q3-v-pressure",
                                "label": "It increases atmospheric pressure to crush virus envelopes.",
                                "is_correct": False,
                                "feedback": "Drafts and windows do not alter atmospheric pressure significantly.",
                            },
                            {
                                "option_id": "q3-v-warmth",
                                "label": "It warms the room so that human immune cells travel faster.",
                                "is_correct": False,
                                "feedback": "Ventilation is about air exchange and particle dilution, not heating.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "resp-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "If a family member or co-worker develops an acute fever and persistent cough, what is the most responsible community action?",
                        "options": [
                            {
                                "option_id": "q4-stay-home",
                                "label": "Encourage them to rest at home, avoid crowded public spaces, wear a mask around others, and seek medical advice if needed.",
                                "is_correct": True,
                                "feedback": "Correct! Voluntary isolation while symptomatic prevents propagating an outbreak at school or work.",
                            },
                            {
                                "option_id": "q4-work-harder",
                                "label": "Tell them to exercise vigorously in an enclosed gym to sweat the infection out.",
                                "is_correct": False,
                                "feedback": "Heavy exertion in an enclosed gym increases droplet shedding and stresses recovering organs.",
                            },
                            {
                                "option_id": "q4-share-cup",
                                "label": "Share hot tea from the same mug to share natural antibodies.",
                                "is_correct": False,
                                "feedback": "Sharing cups transmits pathogens directly through saliva.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "resp-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-mohfw-respiratory"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How far can large respiratory droplets travel through the air from an uncovered, forceful cough?",
                        "options": [
                            {
                                "option_id": "q5-dist-1-2m",
                                "label": "Up to 1 to 2 meters (approximately 3 to 6 feet).",
                                "is_correct": True,
                                "feedback": "Exact public health range! Heavy droplets travel 1 to 2 meters before gravity pulls them onto surfaces.",
                            },
                            {
                                "option_id": "q5-dist-10cm",
                                "label": "Less than 10 centimeters.",
                                "is_correct": False,
                                "feedback": "Droplets are expelled with considerable velocity and travel well past 10 centimeters.",
                            },
                            {
                                "option_id": "q5-dist-50m",
                                "label": "Over 50 meters in a straight line.",
                                "is_correct": False,
                                "feedback": "Droplets succumb to aerodynamic drag and gravity within a few meters.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "resp-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Cough into Your Elbow: Never use bare hands; the inner elbow crook protects surfaces and others.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Mask Hygiene: Touch only the straps, keep masks dry, and discard used tissues into closed bins immediately.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Everyday Action: Practice the 'elbow-shield' cough today and check that windows are slightly opened in your shared living and working rooms.",
                        },
                    ],
                    "source_ids": ["src-mohfw-respiratory", "src-who-hygiene"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 4: Everyday Personal and Oral Hygiene
        {
            "version_id": "ver-personal-oral-hygiene-1",
            "lesson_id": "lesson-personal-oral-hygiene",
            "version_number": 1,
            "title": "Everyday Personal and Oral Hygiene",
            "summary": "Protect oral health with 2-minute fluoride brushing, combat microbial plaque biofilms, manage skin fold hygiene in humid climates, and maintain safe grooming habits.",
            "language": "en",
            "learning_objectives": [
                "Explain the nature of dental plaque biofilm and acid demineralization of enamel.",
                "Demonstrate the 2-minute fluoride toothbrushing technique and spit-don't-rinse method.",
                "Identify fungal and bacterial skin infection risks in skin folds during hot, humid weather.",
                "Outline safe fingernail and daily bathing hygiene practices.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-oral-health", "src-who-hygiene"],
            "cards": [
                {
                    "card_id": "oral-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Dental Checkup with Dr. Ananya"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Rahul",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Dr. Ananya, I brush every single morning with a hard-bristled brush. I scrub back and forth with all my strength! Why are my gums bleeding?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Dr. Ananya",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Rahul, scrubbing aggressively with hard bristles doesn't clean teeth better—it actually abrades your enamel and wears away your gums! Plaque is a soft bacterial film; gentle, circular strokes for 2 full minutes are what work.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Plaque Biofilm Science: Dental plaque is a sticky, invisible biofilm composed of millions of bacteria. When you consume dietary carbohydrates, these bacteria produce organic acids within minutes that attack tooth enamel.",
                        },
                    ],
                    "source_ids": ["src-who-oral-health"],
                    "interaction": None,
                },
                {
                    "card_id": "oral-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Sequence the Toothbrushing Routine"},
                        {
                            "block_type": "text",
                            "body": "Help Rahul replace his aggressive scrubbing with the WHO-recommended dental hygiene technique.",
                        },
                    ],
                    "source_ids": ["src-who-oral-health"],
                    "interaction": {
                        "interaction_type": "arrange_steps",
                        "question_prompt": "Arrange the steps of effective dental hygiene in the correct sequence:",
                        "options": [
                            {"option_id": "step-angle", "label": "1. Position a soft-bristled brush at a 45-degree angle toward the gumline", "is_correct": True, "feedback": "Cleans the gingival sulcus where plaque collects."},
                            {"option_id": "step-circle", "label": "2. Gently brush outer, inner, and chewing surfaces using short circular motions for 2 minutes", "is_correct": True, "feedback": "Frees plaque without traumatizing enamel or gums."},
                            {"option_id": "step-tongue", "label": "3. Clean the tongue gently from back to front to remove odor-causing bacteria", "is_correct": True, "feedback": "The tongue harbors significant bacterial deposits."},
                            {"option_id": "step-spit", "label": "4. Spit out excess toothpaste without immediately washing mouth out with cups of water", "is_correct": True, "feedback": "Leaving a fluoride film on teeth strengthens enamel against acids."},
                        ],
                        "correct_order": ["step-angle", "step-circle", "step-tongue", "step-spit"],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "oral-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Skin Fold Hygiene in Warm, Humid Climates"},
                        {
                            "block_type": "text",
                            "body": "In tropical and monsoon climates, sweat and sebum accumulate in skin folds: the groin, armpits, under breasts, and between toes. Fungi (like Candida and dermatophytes causing ringworm/athlete's foot) thrive in warm, dark, damp environments.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Prevention Essentials: Bathe daily with soap, dry skin folds completely before putting on clothes, wear breathable cotton undergarments, and keep fingernails trimmed short to prevent scratching skin barriers.",
                        },
                    ],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": None,
                },
                {
                    "card_id": "oral-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Myth vs Fact on Enamel Care"},
                    ],
                    "source_ids": ["src-who-oral-health"],
                    "interaction": {
                        "interaction_type": "myth_fact",
                        "question_prompt": "Statement: 'Rinsing vigorously with a glass of water immediately after brushing with fluoride toothpaste is the best way to protect your teeth.'",
                        "options": [
                            {
                                "option_id": "oral-myth",
                                "label": "Myth",
                                "is_correct": True,
                                "feedback": "Accurate! Rinsing immediately with water washes away the concentrated fluoride layer before it can remineralize tooth enamel. Spit out excess paste, don't rinse!",
                            },
                            {
                                "option_id": "oral-fact",
                                "label": "Fact",
                                "is_correct": False,
                                "feedback": "Incorrect. Public health dental guidance strongly recommends spitting out excess paste without immediately rinsing with water.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "oral-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-oral-health"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How long does the World Health Organization recommend brushing your teeth during each session?",
                        "options": [
                            {
                                "option_id": "q1-20s",
                                "label": "20 to 30 seconds.",
                                "is_correct": False,
                                "feedback": "30 seconds leaves over 60% of plaque deposits untouched on back molars.",
                            },
                            {
                                "option_id": "q1-2min",
                                "label": "At least 2 full minutes, twice a day.",
                                "is_correct": True,
                                "feedback": "Correct! 2 minutes allows thorough coverage of all 4 quadrants of the mouth.",
                            },
                            {
                                "option_id": "q1-10min",
                                "label": "10 minutes of intense brushing.",
                                "is_correct": False,
                                "feedback": "Excessive brushing leads to tooth abrasion and gingival irritation.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "oral-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-oral-health"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is brushing your teeth before going to sleep at night considered the most critical brushing of the day?",
                        "options": [
                            {
                                "option_id": "q2-saliva-drop",
                                "label": "Saliva production drops sharply during sleep, reducing its natural antibacterial wash and acid-buffering power.",
                                "is_correct": True,
                                "feedback": "Correct! Reduced salivary flow during sleep leaves uncleaned teeth defenseless against bacterial acid production.",
                            },
                            {
                                "option_id": "q2-night-cold",
                                "label": "Cold night air causes teeth to crack if food remains on them.",
                                "is_correct": False,
                                "feedback": "Night air temperature does not crack teeth.",
                            },
                            {
                                "option_id": "q2-tooth-growth",
                                "label": "Adult teeth only grow new roots while sleeping.",
                                "is_correct": False,
                                "feedback": "Permanent adult teeth do not continuously grow new roots.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "oral-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-oral-health"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How frequently should a standard manual toothbrush be replaced according to dental health standards?",
                        "options": [
                            {
                                "option_id": "q3-3months",
                                "label": "Every 3 months, or sooner if the bristles become frayed or splayed.",
                                "is_correct": True,
                                "feedback": "Correct! Frayed bristles lose their ability to reach interproximal spaces and can abrade gums.",
                            },
                            {
                                "option_id": "q3-2years",
                                "label": "Once every two years as long as the handle isn't cracked.",
                                "is_correct": False,
                                "feedback": "After 3 months, bristles lose stiffness and accumulate bacterial biofilms.",
                            },
                            {
                                "option_id": "q3-weekly",
                                "label": "Every Monday morning regardless of use.",
                                "is_correct": False,
                                "feedback": "Weekly replacement is unnecessary and wasteful.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "oral-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the most effective daily habit for preventing fungal skin infections (tinea / ringworm) in humid weather?",
                        "options": [
                            {
                                "option_id": "q4-dry-folds",
                                "label": "Thoroughly drying skin folds with a clean towel after bathing and wearing loose, breathable cotton clothes.",
                                "is_correct": True,
                                "feedback": "Exact public health recommendation! Fungi require moisture to proliferate; eliminating moisture stops fungal germination.",
                            },
                            {
                                "option_id": "q4-heavy-oil",
                                "label": "Applying thick mustard or coconut oil into sweaty skin folds before exercising.",
                                "is_correct": False,
                                "feedback": "Thick oils trap sweat and moisture against the skin, worsening fungal colonization.",
                            },
                            {
                                "option_id": "q4-no-bathing",
                                "label": "Avoiding bathing altogether during monsoon season to keep skin dry.",
                                "is_correct": False,
                                "feedback": "Daily bathing removes accumulated sweat, dead keratinocytes, and fungal spores.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "oral-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-hygiene"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is keeping fingernails trimmed short and clean an important personal hygiene practice?",
                        "options": [
                            {
                                "option_id": "q5-subungual",
                                "label": "The space underneath fingernails (subungual space) harbors the highest concentration of bacteria and pinworm/parasite eggs on the hands.",
                                "is_correct": True,
                                "feedback": "Correct! Long nails act as reservoirs for fecal-oral pathogens and parasitic eggs.",
                            },
                            {
                                "option_id": "q5-blood-vessels",
                                "label": "Long fingernails pull blood vessels out from the fingertips.",
                                "is_correct": False,
                                "feedback": "Nails do not pull blood vessels out; the hazard is strictly microbial accumulation.",
                            },
                            {
                                "option_id": "q5-calcium-loss",
                                "label": "Trimming nails prevents the body from losing calcium through hair follicles.",
                                "is_correct": False,
                                "feedback": "Fingernails are made of keratin and trimming them has no effect on systemic calcium.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "oral-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Spit, Don't Rinse: Brush for 2 full minutes twice daily with soft bristles and spit out excess paste to keep fluoride on your enamel.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Dry Skin Folds: Prevent fungal infections by drying groin, armpits, and toes thoroughly after every bath.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Brush your teeth tonight for a full two minutes right before bed, and leave the fluoride on your teeth without rinsing!",
                        },
                    ],
                    "source_ids": ["src-who-oral-health", "src-who-hygiene"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 5: Keeping Shared Spaces Clean
        {
            "version_id": "ver-shared-spaces-clean-1",
            "lesson_id": "lesson-shared-spaces-clean",
            "version_number": 1,
            "title": "Keeping Shared Spaces Clean",
            "summary": "Master environmental hygiene in communal buildings: cleaning vs disinfecting, proper chemical dilution, contact times, and maintaining shared kitchens and restrooms safely.",
            "language": "en",
            "learning_objectives": [
                "Differentiate cleaning with detergent from chemical disinfection.",
                "Calculate and prepare safe 0.1% sodium hypochlorite (chlorine) solutions.",
                "Identify high-touch communal contamination hazards in shared buildings.",
                "Explain the critical role of disinfectant contact time and cross-ventilation.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-sanitation-shared", "src-cdc-hygiene"],
            "cards": [
                {
                    "card_id": "shared-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Sunday Society Cleanliness Drive"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Suresh",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Kavita, I bought concentrated bleach! I was planning to pour it raw onto the greasy kitchen counter and wipe it dry immediately with an old rag.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Kavita",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Stop, Suresh! Raw bleach produces dangerous fumes, and organic grease actually neutralizes chlorine so it can't kill germs. We need to clean off the grease with soapy water first, then apply diluted bleach and let it sit wet for several minutes!",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Two-Step Golden Rule: Clean first with detergent and water to remove organic dirt, grease, and bioburden. Disinfect second with an approved antimicrobial solution allowed to remain visibly wet for its full contact time.",
                        },
                    ],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": None,
                },
                {
                    "card_id": "shared-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Identify High-Touch Communal Hazards"},
                    ],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all high-touch communal surfaces that require daily targeted disinfection in an apartment building:",
                        "scene_description": "An apartment lobby and shared staircase: elevator call buttons, metal staircase handrails, hallway ceiling lights, community water dispenser tap handle, and exterior floor doormat.",
                        "options": [
                            {
                                "option_id": "risk-elevator",
                                "label": "Elevator call and floor buttons",
                                "is_correct": True,
                                "feedback": "Pressed by dozens of residents daily; high risk for respiratory droplet and enteric transfer.",
                            },
                            {
                                "option_id": "risk-handrails",
                                "label": "Stairwell metal and wooden handrails",
                                "is_correct": True,
                                "feedback": "Gripped by numerous hands; needs regular surfactant or chlorine wipe-downs.",
                            },
                            {
                                "option_id": "risk-dispenser-tap",
                                "label": "Community drinking water dispenser lever / tap",
                                "is_correct": True,
                                "feedback": "Frequent hand contact point directly adjacent to clean drinking water.",
                            },
                            {
                                "option_id": "safe-ceiling-light",
                                "label": "Ceiling mounted hallway light fixtures",
                                "is_correct": False,
                                "feedback": "Ceiling fixtures are rarely touched and pose minimal infectious fomite risk.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "shared-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Chemical Safety: Preparing Diluted Chlorine Solution"},
                        {
                            "block_type": "text",
                            "body": "The WHO recommends a 0.1% (1,000 ppm) sodium hypochlorite solution for general environmental disinfection. For standard household bleach (5% concentration), dilute 20 ml of bleach in 1 liter of cool water (or roughly 1 part bleach to 49 parts water).",
                        },
                        {
                            "block_type": "callout",
                            "body": "Safety Warning: Never mix chlorine bleach with ammonia, vinegar, or acidic toilet cleaners! Mixing them generates toxic chloramine and chlorine gases that cause severe chemical lung injury.",
                        },
                    ],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": None,
                },
                {
                    "card_id": "shared-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: What is Contact Time?"},
                        {
                            "block_type": "text",
                            "body": "Suresh wipes the elevator button with disinfectant and immediately buffs it dry with a dry cloth 2 seconds later. Why is this ineffective?",
                        },
                    ],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What does 'contact time' or 'dwell time' mean on a disinfectant label?",
                        "options": [
                            {
                                "option_id": "dwell-correct",
                                "label": "The duration the surface must stay visibly wet with the disinfectant solution to chemically destroy targeted microbes.",
                                "is_correct": True,
                                "feedback": "Exact definition! Disinfectants require 1 to 5 minutes of wet contact time to deactivate stubborn viruses and bacteria.",
                            },
                            {
                                "option_id": "dwell-dry",
                                "label": "The amount of time the bottle can sit unopened on a store shelf before expiring.",
                                "is_correct": False,
                                "feedback": "That is shelf life, not contact time.",
                            },
                            {
                                "option_id": "dwell-spray",
                                "label": "The time it takes to squeeze the spray nozzle trigger.",
                                "is_correct": False,
                                "feedback": "Contact time refers specifically to the wetting period on the targeted surface.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "shared-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why must visible grease and dirt be washed off with soap and water before applying a chemical disinfectant?",
                        "options": [
                            {
                                "option_id": "q1-organic-load",
                                "label": "Organic soil, grease, and dirt shield microorganisms and chemically deactivate chlorine and quaternary disinfectants.",
                                "is_correct": True,
                                "feedback": "Correct! Biofilms and organic matter consume the active antimicrobial agents, rendering disinfection ineffective.",
                            },
                            {
                                "option_id": "q1-color-change",
                                "label": "Because bleach turns green when applied to dry food crumbs.",
                                "is_correct": False,
                                "feedback": "Bleach does not turn green on food crumbs.",
                            },
                            {
                                "option_id": "q1-smell-bad",
                                "label": "Disinfectants make organic grease permanently stick to tables like cement.",
                                "is_correct": False,
                                "feedback": "The critical issue is loss of germicidal potency.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "shared-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What dangerous hazard occurs if someone mixes household chlorine bleach with an acidic cleaner (like vinegar or hydrochloric toilet acid)?",
                        "options": [
                            {
                                "option_id": "q2-toxic-gas",
                                "label": "It releases toxic chlorine gas, causing severe respiratory distress, coughing, and chemical lung injury.",
                                "is_correct": True,
                                "feedback": "Critical chemical safety knowledge! Acid reacts with hypochlorite to release poisonous chlorine gas.",
                            },
                            {
                                "option_id": "q2-no-reaction",
                                "label": "Nothing happens; the two liquids simply cancel each other out into pure harmless water.",
                                "is_correct": False,
                                "feedback": "Extremely dangerous misconception. Mixing them produces lethal gas.",
                            },
                            {
                                "option_id": "q2-freeze",
                                "label": "The mixture instantly freezes into solid nitrogen ice blocks.",
                                "is_correct": False,
                                "feedback": "The reaction produces hazardous volatile gas, not ice.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "shared-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why are damp cleaning sponges and reused mop heads considered major cross-contamination hazards in shared facilities?",
                        "options": [
                            {
                                "option_id": "q3-sponge-biofilm",
                                "label": "Damp porous sponges harbor dense bacterial biofilms that get smeared across every subsequent surface cleaned.",
                                "is_correct": True,
                                "feedback": "Exact microbiology! Sponges must be sanitized in boiling water or bleach and dried thoroughly between uses.",
                            },
                            {
                                "option_id": "q3-sponge-heavy",
                                "label": "Sponges become too heavy for cleaning workers to lift safely.",
                                "is_correct": False,
                                "feedback": "Weight is trivial; microbial colonization is the true hazard.",
                            },
                            {
                                "option_id": "q3-sponge-melt",
                                "label": "Wet sponges dissolve tiles by leaking synthetic foam.",
                                "is_correct": False,
                                "feedback": "Sponges do not dissolve tiles.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "shared-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How frequently should freshly diluted 0.1% sodium hypochlorite bleach solutions be prepared?",
                        "options": [
                            {
                                "option_id": "q4-fresh-daily",
                                "label": "Freshly every 24 hours, because dilute chlorine breaks down rapidly when exposed to air and light.",
                                "is_correct": True,
                                "feedback": "Correct! Dilute bleach degrades rapidly and loses germicidal effectiveness within 24 hours.",
                            },
                            {
                                "option_id": "q4-yearly",
                                "label": "Once every 12 months in a large open bucket.",
                                "is_correct": False,
                                "feedback": "After a day or two, dilute bleach in an open bucket reverts to inactive salt water.",
                            },
                            {
                                "option_id": "q4-five-years",
                                "label": "Diluted bleach remains active indefinitely for 5 years.",
                                "is_correct": False,
                                "feedback": "Only concentrated bleach in sealed opaque containers maintains shelf life.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "shared-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-sanitation-shared"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What personal protective measure should always be taken when applying chemical disinfectants in poorly ventilated spaces?",
                        "options": [
                            {
                                "option_id": "q5-vent-gloves",
                                "label": "Open windows to establish airflow and wear protective household gloves to prevent skin irritation.",
                                "is_correct": True,
                                "feedback": "Correct! Adequate airflow protects lungs from fumes, and gloves protect the skin barrier.",
                            },
                            {
                                "option_id": "q5-seal-room",
                                "label": "Seal all doors and windows tightly and blow into the bucket.",
                                "is_correct": False,
                                "feedback": "Sealing the room traps noxious fumes, leading to acute chemical inhalation risks.",
                            },
                            {
                                "option_id": "q5-drink-water",
                                "label": "Drink a glass of milk before cleaning to coat the stomach.",
                                "is_correct": False,
                                "feedback": "Drinking milk does not protect respiratory mucous membranes from inhaled disinfectant fumes.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "shared-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Clean Before Disinfecting: Always wipe off grease and soil with soapy water before applying disinfectant.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Respect Contact Time: Keep surfaces visibly wet with disinfectant for the full duration specified (usually 1-5 minutes).",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Inspect the high-touch door handles and water dispenser tap in your home or workplace today, and disinfect them safely with adequate contact time.",
                        },
                    ],
                    "source_ids": ["src-who-sanitation-shared", "src-cdc-hygiene"],
                    "interaction": None,
                },
            ],
        },
    ]

    return lessons, versions
