"""Safe Drinking Water & Sanitation Topic (5 Chapters).

Topic ID: topic-water
Chapters:
1. When Clear Water Isn't Necessarily Safe (lesson-clear-water-safety)
2. How Water Becomes Contaminated (lesson-water-contamination)
3. Choosing Appropriate Water-Treatment Methods (lesson-water-purification) [STABLE ID]
4. Safe Storage and Handling at Home (lesson-water-storage-handling)
5. Identifying and Responding to Community Water-Safety Concerns (lesson-community-water-safety)
"""

from __future__ import annotations


def get_water_lessons() -> list[dict]:
    lessons = [
        {
            "lesson_id": "lesson-clear-water-safety",
            "topic_id": "topic-water",
            "display_order": 1,
            "published_version_id": "ver-clear-water-safety-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-water-contamination",
            "topic_id": "topic-water",
            "display_order": 2,
            "published_version_id": "ver-water-contamination-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-water-purification",
            "topic_id": "topic-water",
            "display_order": 3,
            "published_version_id": "ver-water-purification-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-water-storage-handling",
            "topic_id": "topic-water",
            "display_order": 4,
            "published_version_id": "ver-water-storage-handling-1",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-community-water-safety",
            "topic_id": "topic-water",
            "display_order": 5,
            "published_version_id": "ver-community-water-safety-1",
            "draft_version_id": None,
        },
    ]

    versions = [
        # Chapter 1: When Clear Water Isn't Necessarily Safe
        {
            "version_id": "ver-clear-water-safety-1",
            "lesson_id": "lesson-clear-water-safety",
            "version_number": 1,
            "title": "When Clear Water Isn't Necessarily Safe",
            "summary": "Discover why sparkling clear water can harbor lethal invisible microbes or chemical toxins, and understand turbidity versus biological contamination.",
            "language": "en",
            "learning_objectives": [
                "Explain why visual transparency and lack of odor do not indicate biological water safety.",
                "Identify common microscopic enteric pathogens present in clear groundwater (E. coli, Giardia, Rotavirus).",
                "Recognize odorless, invisible chemical contaminants such as arsenic and fluoride.",
                "Evaluate the role of laboratory water testing in verifying potability.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-water-guidelines", "src-who-water-factsheet"],
            "cards": [
                {
                    "card_id": "cw-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Drink from the Garden Borewell"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Deepa",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Look how crystal clear this borewell water is, Rajesh! It's so cold, odorless, and sparkling. Why do we need to bother boiling or filtering it?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Rajesh",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Deepa, water clarity only means it has low turbidity (no suspended mud or sand). A single milliliter of sparkling clear water can still carry millions of microscopic cholera bacteria, noroviruses, or odorless dissolved chemicals like arsenic!",
                        },
                        {
                            "block_type": "callout",
                            "body": "Turbidity vs Microorganisms: Turbidity refers to cloudiness caused by suspended particles. While turbid water is certainly risky, crystal clear water can easily harbor microscopic cysts (Cryptosporidium) and enteric viruses that are completely invisible without a microscope.",
                        },
                    ],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": None,
                },
                {
                    "card_id": "cw-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Myth vs Fact on Water Clarity"},
                    ],
                    "source_ids": ["src-who-water-factsheet"],
                    "interaction": {
                        "interaction_type": "myth_fact",
                        "question_prompt": "Statement: 'If underground well water tastes sweet and has no odor, it is guaranteed to be safe from disease-causing bacteria.'",
                        "options": [
                            {
                                "option_id": "water-clarity-myth",
                                "label": "Myth",
                                "is_correct": True,
                                "feedback": "Accurate! Pathogenic bacteria like E. coli, Salmonella, and Vibrio cholerae do not produce a sour taste or bad smell at infectious doses. Taste and smell are never indicators of microbial safety.",
                            },
                            {
                                "option_id": "water-clarity-fact",
                                "label": "Fact",
                                "is_correct": False,
                                "feedback": "Incorrect. Many deadly pathogens and toxic minerals have zero odor or taste. Relying on senses can cause acute waterborne poisoning.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "cw-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Chemical vs Biological Hazards"},
                        {
                            "block_type": "text",
                            "body": "Drinking water hazards fall into two major categories: Biological (living microbes like bacteria, viruses, and amoebic cysts) and Chemical (dissolved minerals like fluoride, arsenic, nitrates, and heavy metals).",
                        },
                        {
                            "block_type": "callout",
                            "body": "Boiling Warning: Boiling kills 100% of biological pathogens (bacteria, viruses, and parasites). However, boiling DOES NOT remove chemical toxins like arsenic or lead; in fact, prolonged boiling concentrates dissolved minerals by evaporating pure steam.",
                        },
                    ],
                    "source_ids": ["src-who-water-guidelines", "src-cdc-water"],
                    "interaction": None,
                },
                {
                    "card_id": "cw-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Identifying Water Risk Factors"},
                    ],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all factors that make an untreated clear borewell vulnerable to microbial contamination:",
                        "scene_description": "A rural borewell located next to an unlined pit latrine, an open sewage ditch 5 meters away, an elevated concrete apron, and monsoon rain pooling around the wellhead.",
                        "options": [
                            {
                                "option_id": "risk-pit-latrine",
                                "label": "An unlined pit latrine located within 10 meters of the wellhead",
                                "is_correct": True,
                                "feedback": "Fecal microbes seep through porous soil into shallow groundwater aquifers.",
                            },
                            {
                                "option_id": "risk-monsoon-pool",
                                "label": "Monsoon surface rainwater pooling directly around the well pipe",
                                "is_correct": True,
                                "feedback": "Pooled runoff carries animal waste down along the casing pipe into the aquifer.",
                            },
                            {
                                "option_id": "risk-open-sewage",
                                "label": "An open household drainage ditch 5 meters from the water source",
                                "is_correct": True,
                                "feedback": "Contaminated wastewater easily infiltrates shallow underground water tables.",
                            },
                            {
                                "option_id": "safe-concrete-apron",
                                "label": "A raised concrete sanitary apron with a sloping drainage channel",
                                "is_correct": False,
                                "feedback": "A sanitary concrete apron is a protective engineering feature that prevents surface infiltration.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "cw-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What does 'turbidity' measure in a sample of drinking water?",
                        "options": [
                            {
                                "option_id": "q1-cloudiness",
                                "label": "The cloudiness or haziness caused by suspended particles like silt, clay, and organic matter.",
                                "is_correct": True,
                                "feedback": "Correct! Turbidity is optical cloudiness. High turbidity shields microbes from disinfectants.",
                            },
                            {
                                "option_id": "q1-salt-content",
                                "label": "The total percentage of table salt dissolved in the liquid.",
                                "is_correct": False,
                                "feedback": "Dissolved salt is measured by Total Dissolved Solids (TDS) or electrical conductivity.",
                            },
                            {
                                "option_id": "q1-temperature",
                                "label": "The thermal temperature of the water at noon.",
                                "is_correct": False,
                                "feedback": "Turbidity is an optical measurement of suspended solids, not temperature.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "cw-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-water-factsheet"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which common organism is used as the global benchmark 'fecal indicator bacterium' to detect sewage contamination in water?",
                        "options": [
                            {
                                "option_id": "q2-ecoli",
                                "label": "Escherichia coli (E. coli)",
                                "is_correct": True,
                                "feedback": "Correct! E. coli normally resides in the intestines of warm-blooded animals; its presence in water confirms recent fecal contamination.",
                            },
                            {
                                "option_id": "q2-yeast",
                                "label": "Baker's yeast (Saccharomyces cerevisiae)",
                                "is_correct": False,
                                "feedback": "Yeast is used in baking and brewing, not as a fecal indicator.",
                            },
                            {
                                "option_id": "q2-lacto",
                                "label": "Lactobacillus acidophilus",
                                "is_correct": False,
                                "feedback": "Lactobacillus is a beneficial yogurt culture, not a sewage contamination indicator.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "cw-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-cdc-water"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "If a water source is contaminated with dissolved chemical arsenic or excessive fluoride, will boiling make it safe to drink?",
                        "options": [
                            {
                                "option_id": "q3-boil-no-chem",
                                "label": "No. Boiling only destroys biological pathogens; it does not remove dissolved chemical toxins like arsenic or fluoride.",
                                "is_correct": True,
                                "feedback": "Vital public health knowledge! Boiling evaporates water, actually increasing the concentration of dissolved toxic chemicals.",
                            },
                            {
                                "option_id": "q3-boil-kills-chem",
                                "label": "Yes. Boiling breaks the chemical bonds of all toxic minerals and turns them into oxygen.",
                                "is_correct": False,
                                "feedback": "Minerals like arsenic and fluoride are elemental ions that cannot be destroyed by kitchen boiling.",
                            },
                            {
                                "option_id": "q3-freeze-chem",
                                "label": "Yes, if boiled for at least 15 minutes in a copper vessel.",
                                "is_correct": False,
                                "feedback": "Copper vessels do not eliminate arsenic or fluoride and can add copper toxicity if water is acidic.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "cw-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why does groundwater in rural wells often show a spike in diarrheal illness during the initial onset of the monsoon season?",
                        "options": [
                            {
                                "option_id": "q4-monsoon-flush",
                                "label": "Heavy rain flushes accumulated surface feces, agricultural runoff, and open waste down into cracked casings and shallow aquifers.",
                                "is_correct": True,
                                "feedback": "Correct! The 'first flush' of the monsoon drives surface contamination deep into vulnerable groundwater tables.",
                            },
                            {
                                "option_id": "q4-cold-water",
                                "label": "Rainwater creates sound waves that awaken dormant bacteria.",
                                "is_correct": False,
                                "feedback": "Sound waves have no pathogenic awakening effect.",
                            },
                            {
                                "option_id": "q4-sky-bacteria",
                                "label": "All clouds are naturally composed of live cholera bacteria.",
                                "is_correct": False,
                                "feedback": "Rainwater begins relatively pure in clouds; contamination happens when it strikes ground surfaces.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "cw-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-jjm-water-tech"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the only reliable way to confirm that a private or community borewell is completely free of harmful pathogens and chemical toxins?",
                        "options": [
                            {
                                "option_id": "q5-lab-testing",
                                "label": "Submitting a water sample to a certified public health laboratory or using an approved Field Test Kit (FTK) for testing.",
                                "is_correct": True,
                                "feedback": "Spot on! Microbiological culture testing (for coliforms) and chemical testing are the only definitive verification methods.",
                            },
                            {
                                "option_id": "q5-drink-glass",
                                "label": "Drinking one glass and waiting two hours to see if anyone vomits.",
                                "is_correct": False,
                                "feedback": "Human self-testing is hazardous; incubation periods for typhoid or hepatitis A take weeks.",
                            },
                            {
                                "option_id": "q5-sunlight-reflection",
                                "label": "Holding the glass up to the morning sun to check for rainbow colors.",
                                "is_correct": False,
                                "feedback": "Sunlight reflection cannot reveal microscopic bacteria or dissolved toxins.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "cw-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Clarity != Purity: Sparkling clear, odorless water can still harbor millions of diarrheal pathogens or dangerous dissolved chemicals.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Boiling Destroys Microbes, Not Chemicals: Boiling kills all bacteria, viruses, and parasites, but chemical contamination requires specialized filtration.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: If using private borewell or tanker water, get your water source tested annually at your nearest district water testing laboratory or through the Jal Jeevan Mission Field Test Kit (FTK).",
                        },
                    ],
                    "source_ids": ["src-who-water-guidelines", "src-who-water-factsheet"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 2: How Water Becomes Contaminated
        {
            "version_id": "ver-water-contamination-1",
            "lesson_id": "lesson-water-contamination",
            "version_number": 1,
            "title": "How Water Becomes Contaminated",
            "summary": "Understand the fecal-oral transmission pathway (the 5 Fs), back-siphonage in broken pipelines, and how surface runoff pollutes community water sources.",
            "language": "en",
            "learning_objectives": [
                "Map the fecal-oral disease transmission pathway using the 5 Fs framework.",
                "Explain how negative pipeline pressure and cross-connections cause sewage ingress into drinking pipes.",
                "Identify safe setback distances between pit latrines and drinking water wells.",
                "Describe how open containers and unwashed hand dipping contaminate stored household water.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-water-guidelines", "src-who-hwts"],
            "cards": [
                {
                    "card_id": "contam-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Mystery Outbreak in the Village"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Farmer Harish",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Maya, half the families on our lane have sudden watery diarrhea and stomach cramps since Tuesday. We get piped water from the main pump station. How did everyone fall sick together?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Maya",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Harish-ji, when the water supply was turned off on Monday afternoon, the underground pipes lost pressure. There's a cracked joint right under the open drain by the tea stall. When pressure dropped, sewage was sucked directly into the drinking water line!",
                        },
                        {
                            "block_type": "callout",
                            "body": "Back-Siphonage & Negative Pressure: When intermittent municipal water supplies are shut off, pipes develop negative suction pressure (vacuum). If pipes have leaks or pass through sewage ditches, dirty wastewater is pulled straight into the drinking water pipeline.",
                        },
                    ],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": None,
                },
                {
                    "card_id": "contam-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: The '5 Fs' Fecal-Oral Pathway"},
                        {
                            "block_type": "text",
                            "body": "In public health epidemiology, the '5 Fs' diagram illustrates the five primary routes through which human feces contaminate food and drinking water.",
                        },
                    ],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all transmission vectors that belong to the classic public health '5 Fs' fecal-oral pathway:",
                        "options": [
                            {"option_id": "f-fingers", "label": "Fingers (unwashed hands touching food or water)", "is_correct": True, "feedback": "Hands carry pathogens directly into drinking vessels and mouths."},
                            {"option_id": "f-flies", "label": "Flies (mechanical vectors landing on feces then food)", "is_correct": True, "feedback": "Houseflies transfer thousands of bacteria on their legs and mouthparts."},
                            {"option_id": "f-fields", "label": "Fields (open defecation washing into soil and crops)", "is_correct": True, "feedback": "Rain washes agricultural and human waste into nearby ponds and rivers."},
                            {"option_id": "f-fluids", "label": "Fluids (contaminated drinking water sources and runoff)", "is_correct": True, "feedback": "Water is the most efficient fluid vehicle for mass enteric outbreaks."},
                            {"option_id": "f-furniture", "label": "Fences and wooden furniture legs", "is_correct": False, "feedback": "Fences are not one of the epidemiological 5 Fs."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "contam-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Safe Setback Distance for Pit Latrines"},
                        {
                            "block_type": "text",
                            "body": "In rural and peri-urban areas without central underground sewage systems, households rely on on-site sanitation like single or twin pit latrines.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The 15 to 30 Meter Rule: WHO and Ministry of Jal Shakti guidelines mandate that pit latrines must be installed at least 15 to 30 meters downhill and away from any groundwater well, and at least 2 meters above the seasonal water table, to prevent subterranean fecal migration.",
                        },
                    ],
                    "source_ids": ["src-jjm-water-tech", "src-who-water-guidelines"],
                    "interaction": None,
                },
                {
                    "card_id": "contam-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Identify Contamination Pathways"},
                    ],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all household practices that cause secondary contamination of clean water:",
                        "scene_description": "A kitchen scene: wide-mouth open pot with drinking water, a communal plastic cup dipped with fingers touching water, an uncovered water jug, a sealed water dispenser with clean tap.",
                        "options": [
                            {
                                "option_id": "risk-dip-cup",
                                "label": "Dipping a handleless cup directly into a wide-mouth pot with fingers entering water",
                                "is_correct": True,
                                "feedback": "Unwashed fingers submerged in water transfer bacteria directly from skin into the drinking supply.",
                            },
                            {
                                "option_id": "risk-uncovered-pot",
                                "label": "Leaving stored water vessels uncovered on the floor",
                                "is_correct": True,
                                "feedback": "Uncovered pots allow dust, houseflies, and domestic pets to introduce pathogens.",
                            },
                            {
                                "option_id": "risk-unwashed-container",
                                "label": "Refilling water into a storage drum without washing the interior biofilm for months",
                                "is_correct": True,
                                "feedback": "Bacterial biofilms cling to container walls and recontaminate freshly boiled water.",
                            },
                            {
                                "option_id": "safe-clean-tap",
                                "label": "Dispensing water through a clean spigot tap on a closed vessel",
                                "is_correct": False,
                                "feedback": "Dispensing via a tap prevents fingers from ever touching the internal water volume.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "contam-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What physical phenomenon causes sewage to be sucked into underground drinking water pipes when water pumps are switched off?",
                        "options": [
                            {
                                "option_id": "q1-neg-pressure",
                                "label": "Negative pressure (back-siphonage or vacuum) drawing external wastewater in through leaks and cracked joints.",
                                "is_correct": True,
                                "feedback": "Correct! When water flow ceases, falling water creates a suction vacuum that draws external contaminated water inward.",
                            },
                            {
                                "option_id": "q1-magnetic",
                                "label": "Magnetic attraction between iron pipes and sewage bacteria.",
                                "is_correct": False,
                                "feedback": "Microbial contamination is driven by hydraulic pressure gradients, not magnetism.",
                            },
                            {
                                "option_id": "q1-heat",
                                "label": "High temperature expanding the water molecules into gas.",
                                "is_correct": False,
                                "feedback": "Negative hydraulic pressure is the verified physical mechanism.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "contam-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-jjm-water-tech"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the minimum safe setback distance recommended between a rural pit latrine and a drinking water well?",
                        "options": [
                            {
                                "option_id": "q2-15-30m",
                                "label": "At least 15 to 30 meters downhill from the water well.",
                                "is_correct": True,
                                "feedback": "Exact public health requirement! 15 to 30 meters provides adequate natural soil filtration in typical soil conditions.",
                            },
                            {
                                "option_id": "q2-1m",
                                "label": "1 to 2 meters directly next to the wellhead.",
                                "is_correct": False,
                                "feedback": "Placing a latrine 1 meter away guarantees catastrophic contamination of the water table.",
                            },
                            {
                                "option_id": "q2-500km",
                                "label": "Over 500 kilometers.",
                                "is_correct": False,
                                "feedback": "Unrealistic distance; 15-30 meters is the verified standard.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "contam-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why are houseflies considered potent mechanical vectors in the spread of cholera, typhoid, and dysentery?",
                        "options": [
                            {
                                "option_id": "q3-fly-legs",
                                "label": "Flies feed on exposed fecal matter and mechanically transfer pathogens on their hairy legs, mouthparts, and vomitus directly onto uncovered food and water.",
                                "is_correct": True,
                                "feedback": "Spot on! Houseflies do not bite; they mechanically transfer millions of pathogens from fecal waste onto uncovered food.",
                            },
                            {
                                "option_id": "q3-fly-sting",
                                "label": "Flies sting human blood vessels and inject intestinal bacteria directly into arteries.",
                                "is_correct": False,
                                "feedback": "Common houseflies do not sting; transmission is through mechanical contamination.",
                            },
                            {
                                "option_id": "q3-fly-sound",
                                "label": "Their wing buzz creates air vibrations that crack water molecules.",
                                "is_correct": False,
                                "feedback": "Mechanical transport on physical legs and mouthparts is the mechanism.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "contam-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is 'secondary contamination' in household water management?",
                        "options": [
                            {
                                "option_id": "q4-recontam",
                                "label": "When safe, purified water becomes contaminated again inside the home during transport, storage, or handling.",
                                "is_correct": True,
                                "feedback": "Exact public health definition! Up to 50% of households that collect clean water drink contaminated water due to unhygienic home storage.",
                            },
                            {
                                "option_id": "q4-two-taps",
                                "label": "When a household uses two different brands of water bottles on the same day.",
                                "is_correct": False,
                                "feedback": "Secondary contamination refers specifically to the re-introduction of pathogens into previously safe water.",
                            },
                            {
                                "option_id": "q4-double-boil",
                                "label": "When water is boiled two times in the same metal pot.",
                                "is_correct": False,
                                "feedback": "Reboiling does not cause microbial contamination.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "contam-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "If an underground pipe leak occurs near an open sewage drain, what immediate action should water authorities and citizens take?",
                        "options": [
                            {
                                "option_id": "q5-boil-repair",
                                "label": "Issue an immediate 'Boil Water Advisory', repair the cracked pipe, and flush the distribution lines with high-dose chlorine.",
                                "is_correct": True,
                                "feedback": "Correct! Immediate community warning to boil water prevents outbreaks while engineers isolate and super-chlorinate the network.",
                            },
                            {
                                "option_id": "q5-ignore",
                                "label": "Wait until the next dry season when the open drain evaporates completely.",
                                "is_correct": False,
                                "feedback": "Delaying action causes explosive epidemic outbreaks of waterborne diseases.",
                            },
                            {
                                "option_id": "q5-perfume",
                                "label": "Pour rose water into the municipal storage tank to improve flavor.",
                                "is_correct": False,
                                "feedback": "Flavoring agents have zero germicidal effect on fecal pathogens.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "contam-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "The 5 Fs Barrier: Break the fecal-oral route by washing hands, covering food from flies, and protecting drinking water from sewage runoff.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Watch for Pipeline Leaks: Low pressure in municipal lines draws nearby drain water inward through cracks; boil water if supply pressure drops unexpectedly.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Everyday Action: Check the route of your household drinking water pipes today. Ensure they do not pass directly through or under open sewer drains.",
                        },
                    ],
                    "source_ids": ["src-who-water-guidelines", "src-who-hwts"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 3: Choosing Appropriate Water-Treatment Methods [STABLE ID: lesson-water-purification]
        {
            "version_id": "ver-water-purification-2",
            "lesson_id": "lesson-water-purification",
            "version_number": 2,
            "title": "Choosing Appropriate Water-Treatment Methods",
            "summary": "Master effective household water purification: rolling boil durations, chlorine tablet disinfection, ceramic filtration, UV disinfection, and when RO is actually necessary.",
            "language": "en",
            "learning_objectives": [
                "Demonstrate the verified rolling boil procedure (1 full minute at sea level; 3 minutes at high altitudes).",
                "Calculate correct chlorine dosing and observe the mandatory 30-minute contact time.",
                "Compare the strengths and limitations of ceramic candle filters, UV purifiers, and Reverse Osmosis (RO).",
                "Explain why turbid water must be settled or cloth-filtered before chemical or UV disinfection.",
            ],
            "estimated_duration_minutes": 7,
            "status": "published",
            "source_ids": ["src-cdc-water", "src-who-hwts", "src-who-water-guidelines"],
            "cards": [
                {
                    "card_id": "purif-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Choosing the Right Purifier at Home"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Neha",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Dr. Varma, a salesman told me I must spend 25,000 rupees on a high-end Reverse Osmosis (RO) machine for our tap water. Our city water tastes normal and has low TDS. Is RO really mandatory for everyone?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Dr. Varma",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Not at all, Neha! Reverse Osmosis is designed specifically to remove dissolved mineral salts and heavy metals when Total Dissolved Solids (TDS) exceed 500 mg/L. RO wastes up to 3 to 4 liters of water for every liter purified! If your goal is killing biological bacteria and viruses, a rolling boil, chlorine tablets, or a UV filter is completely effective and much more sustainable.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Rolling Boil Standard: Bringing water to a vigorous, rolling boil for at least 1 full minute (or 3 minutes at elevations above 2,000 meters / 6,500 feet) inactivates 100% of enteric bacteria, viruses, and hardy protozoan cysts like Cryptosporidium and Giardia.",
                        },
                    ],
                    "source_ids": ["src-cdc-water", "src-who-hwts"],
                    "interaction": None,
                },
                {
                    "card_id": "purif-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Sequence Chemical Water Disinfection"},
                        {
                            "block_type": "text",
                            "body": "During floods or emergency situations when fuel for boiling is unavailable, chlorine tablets (such as Halazone / sodium dichloroisocyanurate) are widely distributed by health departments. Arrange the chemical treatment steps in proper sequence.",
                        },
                    ],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "arrange_steps",
                        "question_prompt": "Arrange the steps for treating water with chlorine tablets in the correct sequence:",
                        "options": [
                            {"option_id": "step-prefilter", "label": "1. If water is turbid, filter through a clean folded cotton cloth or allow sediment to settle", "is_correct": True, "feedback": "Mud and organic particles consume chlorine and protect microbes."},
                            {"option_id": "step-add-tablet", "label": "2. Add the correct strength chlorine tablet according to the vessel volume", "is_correct": True, "feedback": "Proper dosage ensures adequate free residual chlorine."},
                            {"option_id": "step-wait-30min", "label": "3. Stir well and wait for at least 30 minutes of contact time before drinking", "is_correct": True, "feedback": "30 minutes is the mandatory contact time for chlorine to penetrate and destroy viral and bacterial cell walls."},
                            {"option_id": "step-store-sealed", "label": "4. Store the treated water in a covered, clean container with a dedicated tap", "is_correct": True, "feedback": "Keeps chlorine-treated water safe from secondary contamination."},
                        ],
                        "correct_order": ["step-prefilter", "step-add-tablet", "step-wait-30min", "step-store-sealed"],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "purif-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Comparing Household Water Technologies"},
                        {
                            "block_type": "text",
                            "body": "Different water purification methods target different contaminants. Selecting the right technology saves money, protects health, and prevents water wastage.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Method Comparison:\n• Boiling: Kills 100% of biological microbes; zero chemical removal.\n• Chlorine: Highly effective against bacteria and viruses; weak against Cryptosporidium cysts; requires 30 min contact time.\n• Ceramic Gravity Filter: Physically blocks bacteria and protozoa; requires regular gentle cleaning of candles.\n• UV Light: Inactivates microbial DNA; requires clear water (turbidity shields germs); does not alter taste.\n• Reverse Osmosis: Removes dissolved salts/heavy metals; high water wastage; only indicated when TDS is high.",
                        },
                    ],
                    "source_ids": ["src-cdc-water", "src-who-water-guidelines"],
                    "interaction": None,
                },
                {
                    "card_id": "purif-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Boiling Guidelines"},
                    ],
                    "source_ids": ["src-cdc-water"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "According to WHO and CDC standards, how long should water be kept at a vigorous rolling boil to ensure it is microbiologically safe?",
                        "options": [
                            {
                                "option_id": "boil-1min",
                                "label": "At least 1 full minute of vigorous rolling boil (3 minutes at elevations above 2,000 meters).",
                                "is_correct": True,
                                "feedback": "Correct! Reaching 100°C and maintaining a rolling boil for 60 seconds inactivates all human waterborne pathogens, including heat-resistant cysts.",
                            },
                            {
                                "option_id": "boil-warm",
                                "label": "Just until the water feels warm to the touch (around 40°C).",
                                "is_correct": False,
                                "feedback": "Lukewarm water actually provides an ideal incubation environment for bacteria to multiply.",
                            },
                            {
                                "option_id": "boil-2hours",
                                "label": "At least 2 continuous hours with the lid off.",
                                "is_correct": False,
                                "feedback": "Boiling for hours is an unnecessary waste of cooking fuel and concentrates dissolved minerals.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "purif-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-cdc-water"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why must turbid, muddy water be settled or filtered through a clean cloth BEFORE applying chlorine or UV disinfection?",
                        "options": [
                            {
                                "option_id": "q1-particles-shield",
                                "label": "Suspended mud particles shield microorganisms from UV light rays and chemically consume chlorine before it can kill bacteria.",
                                "is_correct": True,
                                "feedback": "Correct! Turbidity interferes directly with chemical and optical disinfection mechanisms.",
                            },
                            {
                                "option_id": "q1-chlorine-heavy",
                                "label": "Chlorine tablets sink to the bottom and become rock hard in mud.",
                                "is_correct": False,
                                "feedback": "Tablets dissolve; the true issue is organic consumption and shadowing.",
                            },
                            {
                                "option_id": "q1-bubbles",
                                "label": "Muddy water turns chlorine into fizzy soda.",
                                "is_correct": False,
                                "feedback": "No such reaction occurs.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "purif-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the mandatory minimum contact time required after adding a chlorine tablet to drinking water before it is safe to consume?",
                        "options": [
                            {
                                "option_id": "q2-30min",
                                "label": "At least 30 minutes.",
                                "is_correct": True,
                                "feedback": "Exact public health requirement! 30 minutes ensures adequate chemical oxidation of microbial proteins and nucleic acids.",
                            },
                            {
                                "option_id": "q2-10sec",
                                "label": "10 seconds after stirring.",
                                "is_correct": False,
                                "feedback": "10 seconds is completely insufficient for chlorine to destroy cell walls.",
                            },
                            {
                                "option_id": "q2-24hours",
                                "label": "At least 24 hours.",
                                "is_correct": False,
                                "feedback": "30 minutes is the established clinical benchmark; waiting 24 hours allows residual chlorine to dissipate.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "purif-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Under what circumstance is a Reverse Osmosis (RO) water purification system genuinely required?",
                        "options": [
                            {
                                "option_id": "q3-high-tds",
                                "label": "When water contains high Total Dissolved Solids (TDS > 500 mg/L) or toxic dissolved chemicals like heavy metals, fluoride, or nitrates.",
                                "is_correct": True,
                                "feedback": "Correct! RO is designed for dissolved solutes and demineralization. Using it on low-TDS water wastes large amounts of water unnecessarily.",
                            },
                            {
                                "option_id": "q3-rainwater",
                                "label": "Whenever drinking fresh rainwater collected in a clean stainless steel pot.",
                                "is_correct": False,
                                "feedback": "Fresh rainwater has naturally low mineral content and does not require demineralization by RO.",
                            },
                            {
                                "option_id": "q3-boil-fail",
                                "label": "Only when the household electricity supply is above 240 volts.",
                                "is_correct": False,
                                "feedback": "Voltage is an electrical specification, not a water quality indicator.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "purif-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How should ceramic candle filters be cleaned and maintained when the flow rate slows down?",
                        "options": [
                            {
                                "option_id": "q4-gentle-scrub",
                                "label": "Gently scrub the outer ceramic surface with clean water and a clean brush without soap or detergent, then rinse.",
                                "is_correct": True,
                                "feedback": "Correct! Scrubbing removes accumulated particulate clogging the ceramic pores. Soap or detergent must never be used as it absorbs into the porous ceramic and spoils water flavor.",
                            },
                            {
                                "option_id": "q4-soap-bleach",
                                "label": "Soak the ceramic candles in laundry detergent and perfumed floor cleaner.",
                                "is_correct": False,
                                "feedback": "Detergents soak into micropores, leaching chemicals into future drinking water.",
                            },
                            {
                                "option_id": "q4-hammer",
                                "label": "Crack the ceramic shell with a hammer to enlarge the holes.",
                                "is_correct": False,
                                "feedback": "Cracking the candle destroys its filtration barrier, allowing pathogens to pass straight through.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "purif-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-cdc-water"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why should boiled drinking water be allowed to cool in the exact same covered pot it was boiled in?",
                        "options": [
                            {
                                "option_id": "q5-cool-same-pot",
                                "label": "The interior of the boiling pot and lid were sterilized during the boil; pouring it into an unsterilized jug introduces new microbes.",
                                "is_correct": True,
                                "feedback": "Correct! Transferring hot or warm water into unsterilized pitchers is a major cause of post-boil recontamination.",
                            },
                            {
                                "option_id": "q5-pot-flavor",
                                "label": "Because cooling water in a different pot causes it to turn into vinegar.",
                                "is_correct": False,
                                "feedback": "Water does not ferment into vinegar.",
                            },
                            {
                                "option_id": "q5-pot-radiation",
                                "label": "Other pots emit gamma radiation when filled with water.",
                                "is_correct": False,
                                "feedback": "Household kitchen utensils do not emit gamma radiation.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "purif-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "The 1-Minute Rolling Boil: Reaching a vigorous rolling boil for 1 full minute destroys 100% of biological waterborne pathogens.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Chlorine Needs 30 Minutes: When using chlorine tablets or drops, always wait at least 30 minutes before drinking.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Review your household water treatment method today. If relying on boiling, ensure you maintain a full 1-minute rolling boil and keep the pot covered while cooling.",
                        },
                    ],
                    "source_ids": ["src-cdc-water", "src-who-hwts"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 4: Safe Storage and Handling at Home
        {
            "version_id": "ver-water-storage-handling-1",
            "lesson_id": "lesson-water-storage-handling",
            "version_number": 1,
            "title": "Safe Storage and Handling at Home",
            "summary": "Prevent secondary contamination: master narrow-neck storage containers, hygienic dispensing taps, ladle protocols, and routine disinfection of home clay pots and storage drums.",
            "language": "en",
            "learning_objectives": [
                "Explain how hand contact and wide-mouth vessels cause secondary water contamination.",
                "Demonstrate the benefits of narrow-neck vessels and spigot taps in home storage.",
                "Describe the proper cleaning protocol for earthen clay pots (matkas) and plastic storage drums.",
                "Establish safe everyday dispensing routines for children and family members.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-who-hwts", "src-who-water-guidelines"],
            "cards": [
                {
                    "card_id": "storage-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Cup Dipped in the Earthen Matka"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Savitri",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Pooja, wait! Don't dip that plastic tumbler straight into the clay matka with your bare fingers touching the water!",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Pooja",
                            "avatar": "👧🏽",
                            "side": "right",
                            "body": "Auntie, I only dipped the rim for a second. We boiled this water this morning, so isn't it completely sterile?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Savitri",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "It was clean when we boiled it. But the moment your fingers entered the water, every bacterium on your skin washed right into the pot. If anyone drinks from it now, they drink whatever was on your hands. That's why we use this long-handled ladle or our tap vessel!",
                        },
                        {
                            "block_type": "callout",
                            "body": "The Dipping Hazard: Studies in community health show that up to 40% of boiled water samples become contaminated with fecal coliforms within 24 hours of storage simply due to hand contact from dipping cups.",
                        },
                    ],
                    "source_ids": ["src-who-hwts"],
                    "interaction": None,
                },
                {
                    "card_id": "storage-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Safe vs Unsafe Storage Vessels"},
                    ],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which container design provides the greatest protection against secondary water contamination in a home?",
                        "options": [
                            {
                                "option_id": "vessel-narrow-tap",
                                "label": "A closed, narrow-neck container fitted with a dispensing tap or spigot near the base.",
                                "is_correct": True,
                                "feedback": "Correct! Narrow openings prevent hands and cups from being dipped inside, and taps allow hygienic touch-free dispensing.",
                            },
                            {
                                "option_id": "vessel-wide-open",
                                "label": "A wide-mouth open brass bucket placed on the kitchen floor without a lid.",
                                "is_correct": False,
                                "feedback": "Wide-mouth open buckets invite dust, insects, and contaminated hand contact.",
                            },
                            {
                                "option_id": "vessel-shallow-tray",
                                "label": "A shallow flat tray kept on the dining table.",
                                "is_correct": False,
                                "feedback": "Shallow trays expose large surface areas to airborne dust and contamination.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "storage-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Cleaning Earthen Pots (Matkas) and Storage Drums"},
                        {
                            "block_type": "text",
                            "body": "Earthen clay pots naturally cool water through evaporative transpiration through their micropores. However, these same pores can harbor bacterial biofilms if not cleaned regularly.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Weekly Maintenance Protocol:\n1. Empty all remaining water completely (never top up old water).\n2. Scrub the interior using boiling hot water and a clean brush without chemical detergents.\n3. Sun-dry the pot in direct sunlight for several hours (UV rays naturally sanitize the clay pores).\n4. Keep the pot elevated on a stand off the floor and covered with a tight lid.",
                        },
                    ],
                    "source_ids": ["src-who-hwts"],
                    "interaction": None,
                },
                {
                    "card_id": "storage-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Safe Ladle Hygiene"},
                    ],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all hygienic practices when using a ladle to dispense water from a storage pot without a tap:",
                        "options": [
                            {"option_id": "ladle-long-handle", "label": "Use a dedicated ladle with a handle longer than the depth of the pot so fingers never enter water", "is_correct": True, "feedback": "Ensures the user's hand remains completely above the pot rim."},
                            {"option_id": "ladle-hang-hook", "label": "Hang the ladle on a clean wall hook after each use rather than laying it on the kitchen counter", "is_correct": True, "feedback": "Prevents the ladle bowl from picking up counter grease or dirt."},
                            {"option_id": "ladle-clean-daily", "label": "Wash the ladle daily with soap and clean running water", "is_correct": True, "feedback": "Keeps the utensil free of salivary or food residues."},
                            {"option_id": "ladle-drink-directly", "label": "Drink directly from the ladle bowl and dip it right back into the pot", "is_correct": False, "feedback": "Drinking from the ladle introduces oral bacteria into the entire family water pot."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "storage-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is 'topping up' freshly boiled water into a half-empty storage drum without emptying and cleaning it first a poor hygiene habit?",
                        "options": [
                            {
                                "option_id": "q1-biofilm-mix",
                                "label": "Old stagnant water and biofilms adhering to the bottom and sides immediately contaminate the incoming fresh water.",
                                "is_correct": True,
                                "feedback": "Correct! Bacterial biofilms persist on container walls and immediately recontaminate fresh water.",
                            },
                            {
                                "option_id": "q1-drum-heavy",
                                "label": "It makes the plastic drum too heavy for municipal meters to read.",
                                "is_correct": False,
                                "feedback": "Municipal meters read pipeline flow, not indoor storage drums.",
                            },
                            {
                                "option_id": "q1-water-bubbles",
                                "label": "Mixing old and new water causes water molecules to explode.",
                                "is_correct": False,
                                "feedback": "Water does not explode when mixed.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "storage-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What role does placing an earthen water pot (matka) on an elevated stand rather than directly on the kitchen floor serve?",
                        "options": [
                            {
                                "option_id": "q2-elevation-protect",
                                "label": "It elevates the pot away from floor dust, pet contact, crawling insects, and muddy splash water during floor mopping.",
                                "is_correct": True,
                                "feedback": "Exact public health rationale! Elevation prevents floor-level contamination from entering the vessel.",
                            },
                            {
                                "option_id": "q2-elevation-cold",
                                "label": "Water only cools down when it is at least 1 meter above sea level.",
                                "is_correct": False,
                                "feedback": "Evaporation cools clay pots regardless of room elevation; the stand is for hygiene.",
                            },
                            {
                                "option_id": "q2-elevation-weight",
                                "label": "Stands make water lighter to drink.",
                                "is_correct": False,
                                "feedback": "Water density does not change on a stand.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "storage-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why should chemical dish soaps and detergents NOT be used inside traditional unglazed clay water pots (matkas)?",
                        "options": [
                            {
                                "option_id": "q3-porous-soap",
                                "label": "Unglazed clay is porous and absorbs soapy chemicals, which later leach out and contaminate drinking water with bad taste and toxic detergents.",
                                "is_correct": True,
                                "feedback": "Correct! Microporous clay absorbs surfactants. Use boiling water, clean brushes, and sunlight to sanitize clay.",
                            },
                            {
                                "option_id": "q3-clay-melt",
                                "label": "Dish soap causes solid terracotta clay to dissolve into red mud immediately.",
                                "is_correct": False,
                                "feedback": "Fired terracotta does not instantly dissolve; chemical absorption is the genuine hazard.",
                            },
                            {
                                "option_id": "q3-color-fade",
                                "label": "Soap attracts ants to terracotta.",
                                "is_correct": False,
                                "feedback": "Chemical leaching into drinking water is the primary public health concern.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "storage-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the primary benefit of sun-drying an emptied water storage vessel in direct sunlight?",
                        "options": [
                            {
                                "option_id": "q4-solar-uv",
                                "label": "Solar Ultraviolet (UV) radiation and complete desiccation destroy residual vegetative bacterial biofilms clinging to interior walls.",
                                "is_correct": True,
                                "feedback": "Scientifically verified! Solar UV radiation and total drying provide natural disinfection without chemicals.",
                            },
                            {
                                "option_id": "q4-solar-charge",
                                "label": "Sunlight charges the plastic molecules with electrical voltage.",
                                "is_correct": False,
                                "feedback": "Sunlight does not charge plastic with voltage.",
                            },
                            {
                                "option_id": "q4-solar-fragrance",
                                "label": "Sunlight adds vanilla fragrance to clay pots.",
                                "is_correct": False,
                                "feedback": "Sunlight does not add vanilla scent.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "storage-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-hwts"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "If a storage container has a dispensing tap (spigot), where should the tap ideally be positioned on the vessel wall?",
                        "options": [
                            {
                                "option_id": "q5-tap-above-bottom",
                                "label": "A few centimeters above the bottom of the container, allowing settled sediment to remain undisturbed at the base.",
                                "is_correct": True,
                                "feedback": "Exact engineering standard! Placing the tap 3 to 5 cm above the container floor ensures settled particulates are not drawn into drinking cups.",
                            },
                            {
                                "option_id": "q5-tap-top-rim",
                                "label": "Directly at the very top rim above the water line.",
                                "is_correct": False,
                                "feedback": "A tap above the water line would not dispense water by gravity.",
                            },
                            {
                                "option_id": "q5-tap-lid",
                                "label": "Inside the removable lid.",
                                "is_correct": False,
                                "feedback": "Taps must be near the base on the side wall to function via gravity.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "storage-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Never Dip Bare Hands: Use a closed vessel with a clean tap or a dedicated long-handled ladle hung on a wall hook.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Empty and Sun-Dry Weekly: Completely empty water drums and clay pots once a week and sun-dry them to eliminate biofilms.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Inspect how drinking water is dispensed in your home today. If family members dip cups into open pots, switch to a container with a tap or dedicated long ladle today!",
                        },
                    ],
                    "source_ids": ["src-who-hwts", "src-who-water-guidelines"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 5: Identifying and Responding to Community Water-Safety Concerns
        {
            "version_id": "ver-community-water-safety-1",
            "lesson_id": "lesson-community-water-safety",
            "version_number": 1,
            "title": "Identifying and Responding to Community Water-Safety Concerns",
            "summary": "Recognize local outbreak warning signs, implement immediate home oral rehydration (ORS) during acute diarrhea, test chlorine residual, and report water hazards to local public health authorities.",
            "language": "en",
            "learning_objectives": [
                "Recognize early community warning signs of a waterborne disease outbreak.",
                "Demonstrate the correct preparation and administration of Oral Rehydration Salts (ORS).",
                "Explain the importance of Free Residual Chlorine (FRC) in piped water supplies.",
                "Outline reporting procedures to Gram Panchayats, municipal water boards, and the Jal Jeevan Mission.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-jjm-water-tech", "src-who-water-factsheet"],
            "cards": [
                {
                    "card_id": "comm-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Sudden Cluster of Illness in Ward 4"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Amit",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Uncle Ramesh! Three children on our street were rushed to the health clinic this morning with sudden severe vomiting and watery diarrhea. The tap water from the municipal standpost has looked yellowish and smelled strange since yesterday.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Sarpanch Ramesh",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Amit, this is an acute public health alert. When multiple households across a street fall ill simultaneously after tap water changes color or odor, we must assume the piped supply has suffered major sewage infiltration. We must immediately issue a community boil alert and notify the Jal Jeevan Mission engineering team!",
                        },
                        {
                            "block_type": "callout",
                            "body": "Outbreak Warning Signs: Sudden clustering of acute watery diarrhea, changes in municipal water turbidity or sulfurous/earthy smells, drops in chlorine taste, or illness following pipe excavation work are red-flag indicators of waterborne disease outbreaks.",
                        },
                    ],
                    "source_ids": ["src-jjm-water-tech", "src-who-water-factsheet"],
                    "interaction": None,
                },
                {
                    "card_id": "comm-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Immediate Home Clinical Response"},
                        {
                            "block_type": "text",
                            "body": "When someone in the household develops acute watery diarrhea, what is the most critical immediate medical action to prevent life-threatening dehydration?",
                        },
                    ],
                    "source_ids": ["src-who-water-factsheet"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the gold-standard first-line intervention for someone with acute watery diarrhea to prevent severe dehydration?",
                        "options": [
                            {
                                "option_id": "ors-first-line",
                                "label": "Start Oral Rehydration Salts (ORS) solution mixed with clean water immediately, sipping continuously after every loose stool.",
                                "is_correct": True,
                                "feedback": "Exact clinical guidance! ORS replenishes lost electrolytes and water through the intestinal sodium-glucose cotransport mechanism, saving lives.",
                            },
                            {
                                "option_id": "ors-stop-fluids",
                                "label": "Stop giving all water and fluids completely to let the stomach 'dry out'.",
                                "is_correct": False,
                                "feedback": "Withholding fluids causes rapid, fatal hypovolemic dehydration in diarrhea patients.",
                            },
                            {
                                "option_id": "ors-heavy-fried",
                                "label": "Feed them heavy, deep-fried spicy snacks to bind the stomach.",
                                "is_correct": False,
                                "feedback": "Heavy fried foods irritate inflamed intestinal mucosa and worsen diarrhea.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "comm-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Free Residual Chlorine (FRC) in Community Water"},
                        {
                            "block_type": "text",
                            "body": "When municipal or community water is treated, chlorine is added at the treatment plant. A small amount of active chlorine must remain in the water throughout the entire pipe network—this is known as Free Residual Chlorine (FRC).",
                        },
                        {
                            "block_type": "callout",
                            "body": "The FRC Standard: WHO and Indian Public Health Standards require a Free Residual Chlorine level of at least 0.2 to 0.5 mg/L (parts per million) at the consumer's tap. This residual acts as an active shield, killing any pathogens that enter through minor pipe leaks along the way.",
                        },
                    ],
                    "source_ids": ["src-jjm-water-tech", "src-who-water-guidelines"],
                    "interaction": None,
                },
                {
                    "card_id": "comm-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Community Risk Actions"},
                    ],
                    "source_ids": ["src-jjm-water-tech"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all essential community actions when a neighborhood water contamination cluster is suspected:",
                        "scene_description": "A neighborhood street meeting: residents boiling water, reporting to Jal Jeevan Mission grievance helpline, keeping quiet to avoid panic, and testing chlorine with Field Test Kit.",
                        "options": [
                            {
                                "option_id": "comm-action-boil-alert",
                                "label": "Inform neighbors immediately to boil all tap drinking water for 1 full minute",
                                "is_correct": True,
                                "feedback": "Halts further transmission across vulnerable families while investigations proceed.",
                            },
                            {
                                "option_id": "comm-action-notify-authority",
                                "label": "Lodge an urgent complaint with the local municipal water board, Gram Panchayat, or Jal Jeevan Mission helpline",
                                "is_correct": True,
                                "feedback": "Triggers engineering inspections of pipeline breaks and emergency super-chlorination.",
                            },
                            {
                                "option_id": "comm-action-ftk-test",
                                "label": "Request the local ASHA or Jal Sahayak to test Free Residual Chlorine using an approved Field Test Kit (FTK)",
                                "is_correct": True,
                                "feedback": "Objective chlorine measurement verifies if disinfection is failing in that section of the network.",
                            },
                            {
                                "option_id": "comm-action-hide-info",
                                "label": "Keep the outbreak quiet and tell nobody to avoid hurting neighborhood property values",
                                "is_correct": False,
                                "feedback": "Concealing contamination risks lives, especially among infants and elderly residents.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "comm-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-who-water-factsheet"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What are the dangerous clinical 'red flag' signs of severe dehydration in a child with watery diarrhea that require immediate emergency hospital care?",
                        "options": [
                            {
                                "option_id": "q1-lethargy-sunken-eyes",
                                "label": "Lethargy or unconsciousness, sunken eyes, inability to drink, and skin pinch that goes back very slowly (>2 seconds).",
                                "is_correct": True,
                                "feedback": "Exact WHO Integrated Management of Childhood Illness (IMCI) criteria for severe dehydration! Immediate IV fluids are required.",
                            },
                            {
                                "option_id": "q1-laughing",
                                "label": "Laughing and asking to play football outdoors.",
                                "is_correct": False,
                                "feedback": "An active, playing child does not show signs of severe dehydration.",
                            },
                            {
                                "option_id": "q1-hair-curly",
                                "label": "Hair becoming curly or changing color.",
                                "is_correct": False,
                                "feedback": "Hair texture changes are not acute signs of dehydration.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "comm-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-who-water-factsheet"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How should a standard packet of WHO-formula Oral Rehydration Salts (ORS) be reconstituted with water?",
                        "options": [
                            {
                                "option_id": "q2-exact-1liter",
                                "label": "Dissolved in exactly 1 liter of clean drinking or boiled water, without adding extra sugar, milk, or fruit juice.",
                                "is_correct": True,
                                "feedback": "Crucial clinical pharmacology! Adding incorrect water volumes alters the exact osmolarity needed for intestinal electrolyte absorption.",
                            },
                            {
                                "option_id": "q2-sip-powder",
                                "label": "Swallowing the dry powder straight from the packet with no water.",
                                "is_correct": False,
                                "feedback": "Swallowing dry ORS powder causes acute hyperosmolar stress.",
                            },
                            {
                                "option_id": "q2-soda-mix",
                                "label": "Mixed with 2 liters of fizzy cola.",
                                "is_correct": False,
                                "feedback": "Cola has high sugar osmolarity which worsens diarrhea.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "comm-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-jjm-water-tech"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the recommended minimum Free Residual Chlorine (FRC) level at the consumer's tap in piped water distribution systems?",
                        "options": [
                            {
                                "option_id": "q3-02-05",
                                "label": "At least 0.2 to 0.5 mg/L (ppm).",
                                "is_correct": True,
                                "feedback": "Exact public health engineering standard! 0.2 to 0.5 mg/L ensures active protection while remaining completely safe and pleasant to drink.",
                            },
                            {
                                "option_id": "q3-zero",
                                "label": "0.0 mg/L with zero residual chlorine.",
                                "is_correct": False,
                                "feedback": "Zero residual chlorine leaves water defenseless against bacterial recontamination inside the pipeline network.",
                            },
                            {
                                "option_id": "q3-500",
                                "label": "At least 500 mg/L.",
                                "is_correct": False,
                                "feedback": "500 mg/L is industrial strength and toxic for human consumption.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "comm-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-jjm-water-tech"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Under India's Jal Jeevan Mission, who in rural communities is specifically trained to test local drinking water sources using Field Test Kits (FTKs)?",
                        "options": [
                            {
                                "option_id": "q4-women-volunteers",
                                "label": "Five women from each village (including ASHA, Anganwadi workers, and village water and sanitation committee members).",
                                "is_correct": True,
                                "feedback": "Correct! Jal Jeevan Mission empowers five women in every village with FTK training to test pH, turbidity, chlorine, hardness, and fecal coliforms.",
                            },
                            {
                                "option_id": "q4-tourists",
                                "label": "Visiting tourists passing through the village.",
                                "is_correct": False,
                                "feedback": "Tourists have no role in institutional community water testing.",
                            },
                            {
                                "option_id": "q4-private-corporation",
                                "label": "Private soft drink advertising executives.",
                                "is_correct": False,
                                "feedback": "JJM establishes community-owned testing via trained village women.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "comm-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-who-water-guidelines"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Following a flood, cyclone, or severe waterlogging event, how should households treat well or tap water until official safety is confirmed?",
                        "options": [
                            {
                                "option_id": "q5-flood-boil-chlorine",
                                "label": "Treat all tap and well water as potentially contaminated: boil for 1 minute or treat with chlorine tablets before drinking.",
                                "is_correct": True,
                                "feedback": "Essential post-disaster protocol! Floodwaters submerge wellheads and overwhelm sewers, contaminating all distribution systems.",
                            },
                            {
                                "option_id": "q5-drink-raw",
                                "label": "Drink floodwater immediately because flood rainwater is 100% distilled.",
                                "is_correct": False,
                                "feedback": "Floodwater is heavily contaminated with animal carcasses, sewage, and chemical runoff.",
                            },
                            {
                                "option_id": "q5-add-sugar",
                                "label": "Add a spoonful of sugar to neutralize flood bacteria.",
                                "is_correct": False,
                                "feedback": "Sugar does not kill bacteria.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "comm-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Act on Outbreak Warnings: Water discolouration or simultaneous neighborhood diarrhea clusters require immediate boil advisories and reporting.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "ORS Saves Lives: Start Oral Rehydration Salts mixed in clean water at the first sign of diarrhea; never withhold fluids.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Everyday Action: Keep at least two packets of WHO-formula Oral Rehydration Salts (ORS) in your family first-aid kit, and locate the customer care or complaint number for your local municipal water board or Gram Panchayat.",
                        },
                    ],
                    "source_ids": ["src-jjm-water-tech", "src-who-water-factsheet"],
                    "interaction": None,
                },
            ],
        },
    ]

    return lessons, versions
