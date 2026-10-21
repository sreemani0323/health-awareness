"""Mosquito Prevention & Vector Control Topic (5 Chapters).

Topic ID: topic-mosquito
Chapters:
1. Where Mosquitoes Breed (lesson-understanding-mosquitoes-and-m-5557) [STABLE ID]
2. Finding and Eliminating Breeding Sites (lesson-mosquito-control) [STABLE ID]
3. Protecting Yourself at Home and Outdoors (lesson-protect-yourself-and-your-fami-3513) [STABLE ID]
4. Understanding Mosquito-Borne Illnesses and Seeking Appropriate Care (lesson-community-prevention-symptoms--4817) [STABLE ID]
5. Organising a Neighbourhood Prevention Campaign (lesson-neighbourhood-mosquito-campaign)
"""

from __future__ import annotations


def get_mosquito_lessons() -> list[dict]:
    lessons = [
        {
            "lesson_id": "lesson-understanding-mosquitoes-and-m-5557",
            "topic_id": "topic-mosquito",
            "display_order": 1,
            "published_version_id": "ver-mosquito-species-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-mosquito-control",
            "topic_id": "topic-mosquito",
            "display_order": 2,
            "published_version_id": "ver-mosquito-control-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-protect-yourself-and-your-fami-3513",
            "topic_id": "topic-mosquito",
            "display_order": 3,
            "published_version_id": "ver-protect-family-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-community-prevention-symptoms--4817",
            "topic_id": "topic-mosquito",
            "display_order": 4,
            "published_version_id": "ver-symptoms-care-2",
            "draft_version_id": None,
        },
        {
            "lesson_id": "lesson-neighbourhood-mosquito-campaign",
            "topic_id": "topic-mosquito",
            "display_order": 5,
            "published_version_id": "ver-neighbourhood-campaign-1",
            "draft_version_id": None,
        },
    ]

    versions = [
        # Chapter 1: Where Mosquitoes Breed [STABLE ID: lesson-understanding-mosquitoes-and-m-5557]
        {
            "version_id": "ver-mosquito-species-2",
            "lesson_id": "lesson-understanding-mosquitoes-and-m-5557",
            "version_number": 2,
            "title": "Where Mosquitoes Breed",
            "summary": "Differentiate between Aedes (Dengue), Anopheles (Malaria), and Culex mosquitoes, their preferred breeding waters, diurnal biting rhythms, and egg desiccation survival.",
            "language": "en",
            "learning_objectives": [
                "Contrast the breeding habitat preferences of Aedes, Anopheles, and Culex mosquitoes.",
                "Identify the peak biting hours of Aedes aegypti (daytime/dawn/dusk).",
                "Explain how Aedes eggs survive dry periods for months on container walls.",
                "Recognize artificial domestic micro-habitats that harbor mosquito larvae.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-vector-control-measu-4319", "src-dengue-and-severe-d-7821", "src-malaria-control-stra-6564"],
            "cards": [
                {
                    "card_id": "breed-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Terrace Inspection with Maya"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Sameer",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Maya, how could our neighborhood have Dengue cases? We don't live near a muddy swamp or a dirty sewage canal! Our housing society is clean and modern.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Maya",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Sameer, that is the most dangerous misconception about Dengue! Culex mosquitoes breed in dirty sewage, but Aedes aegypti—the mosquito that transmits Dengue and Chikungunya—breeds exclusively in clean, stagnant water! Look at this potted plant saucer and that decorative indoor bamboo glass on your balcony: thousands of larvae are swimming right here!",
                        },
                        {
                            "block_type": "callout",
                            "body": "Aedes Loves Clean Water: Aedes aegypti is a domestic container breeder. It does not breed in dirty drains; it thrives in crystal clean rainwater collected in discarded plastic cups, potted plant trays, air cooler trays, and rooftop buckets.",
                        },
                    ],
                    "source_ids": ["src-dengue-and-severe-d-7821", "src-vector-control-measu-4319"],
                    "interaction": None,
                },
                {
                    "card_id": "breed-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Myth vs Fact on Mosquito Habitats"},
                    ],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "myth_fact",
                        "question_prompt": "Statement: 'If you empty all dirty sewage water from nearby street ditches, your home is 100% safe from Dengue mosquitoes.'",
                        "options": [
                            {
                                "option_id": "breed-myth",
                                "label": "Myth",
                                "is_correct": True,
                                "feedback": "Accurate! The Dengue vector (Aedes) breeds in clean domestic containers (coolers, flower vases, plant saucers, fresh rainwater collections), not dirty drains. Eliminating clean standing water inside and around your house is essential.",
                            },
                            {
                                "option_id": "breed-fact",
                                "label": "Fact",
                                "is_correct": False,
                                "feedback": "Incorrect. Aedes mosquitoes specifically lay eggs in relatively clean water containers inside and immediately outside homes.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "breed-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Know Your Vectors: Aedes vs Anopheles vs Culex"},
                        {
                            "block_type": "text",
                            "body": "Different mosquito species transmit different diseases and bite at different times of the day and night.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Vector Comparison:\n• Aedes aegypti: Tiger mosquito with white stripes; breeds in clean domestic containers; aggressive day-biter (peaks early morning and late afternoon); transmits Dengue, Chikungunya, and Zika.\n• Anopheles: Rests at a 45-degree angle; breeds in clean, slow-moving or pooled water; night-biter (dusk to dawn); transmits Malaria.\n• Culex: Dull brown; breeds in dirty, organic-rich stagnant drains and puddles; night/dusk biter; transmits Lymphatic Filariasis and Japanese Encephalitis.",
                        },
                    ],
                    "source_ids": ["src-malaria-control-stra-6564", "src-vector-control-measu-4319"],
                    "interaction": None,
                },
                {
                    "card_id": "breed-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Peak Biting Rhythm"},
                        {
                            "block_type": "text",
                            "body": "Sameer is planning an outdoor cricket game with neighborhood children. When are Aedes mosquitoes most actively biting?",
                        },
                    ],
                    "source_ids": ["src-dengue-and-severe-d-7821"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "At what time of day are Aedes aegypti (Dengue vectors) most actively searching for a blood meal?",
                        "options": [
                            {
                                "option_id": "time-day-peaks",
                                "label": "During daytime hours, with sharp peaks shortly after sunrise (early morning) and in the late afternoon before sunset.",
                                "is_correct": True,
                                "feedback": "Correct! Aedes is a daytime biter. While Anopheles bites at night, Dengue transmission predominantly occurs during morning and late afternoon hours.",
                            },
                            {
                                "option_id": "time-midnight",
                                "label": "Only between 2:00 AM and 4:00 AM in pitch black darkness.",
                                "is_correct": False,
                                "feedback": "Anopheles may bite at night, but Aedes is active during daylight and dusk.",
                            },
                            {
                                "option_id": "time-noon-sun",
                                "label": "Exclusively at 12:00 PM under direct scorching sunlight.",
                                "is_correct": False,
                                "feedback": "Extreme midday sun often causes mosquitoes to seek cool indoor or shaded resting spots.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "breed-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What remarkable biological characteristic allows Aedes mosquito eggs to survive dry periods without water?",
                        "options": [
                            {
                                "option_id": "q1-desiccation",
                                "label": "Aedes eggs adhere to container walls and survive completely dry conditions for up to 6 to 12 months, hatching when refilled with water.",
                                "is_correct": True,
                                "feedback": "Crucial entomological fact! Simply tipping water out is not enough; container walls must be scrubbed to dislodge dry, glued eggs.",
                            },
                            {
                                "option_id": "q1-wings",
                                "label": "Aedes eggs grow wings and fly to the neighbor's roof.",
                                "is_correct": False,
                                "feedback": "Eggs have no wings; they survive via a protective desiccation-resistant shell.",
                            },
                            {
                                "option_id": "q1-spores",
                                "label": "They turn into fungal mushrooms until it rains.",
                                "is_correct": False,
                                "feedback": "Mosquitoes are insects, not fungi.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "breed-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-dengue-and-severe-d-7821"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Approximately how long does it take for a mosquito to develop from an egg through the larval and pupal stages into a flying adult in warm weather?",
                        "options": [
                            {
                                "option_id": "q2-7-10days",
                                "label": "Approximately 7 to 10 days.",
                                "is_correct": True,
                                "feedback": "Exact biological timeline! Because development takes roughly 7 to 10 days, practicing a 'Weekly Dry Day' (every 7 days) completely breaks the lifecycle.",
                            },
                            {
                                "option_id": "q2-2hours",
                                "label": "Less than 2 hours.",
                                "is_correct": False,
                                "feedback": "Mosquito metamorphosis cannot occur in 2 hours.",
                            },
                            {
                                "option_id": "q2-6months",
                                "label": "6 to 8 months in water.",
                                "is_correct": False,
                                "feedback": "In tropical temperatures, development is rapid, completing within 7 to 10 days.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "breed-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-malaria-control-stra-6564"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which visual clue distinguishes the adult Anopheles mosquito (the vector of Malaria) when resting on a wall?",
                        "options": [
                            {
                                "option_id": "q3-angle-rest",
                                "label": "It rests with its body tilted at a distinct 45-degree angle to the surface, head down and abdomen pointing outward.",
                                "is_correct": True,
                                "feedback": "Correct! Anopheles rests at a characteristic 45-degree angle, unlike Culex and Aedes which rest parallel to the surface.",
                            },
                            {
                                "option_id": "q3-flat-pancake",
                                "label": "It flattens itself completely like a flat coin.",
                                "is_correct": False,
                                "feedback": "Anopheles rests tilted at 45 degrees, not flattened.",
                            },
                            {
                                "option_id": "q3-glow",
                                "label": "It glows bright green in the dark.",
                                "is_correct": False,
                                "feedback": "Mosquitoes do not bioluminesce.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "breed-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-dengue-and-severe-d-7821"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the typical flight range of the female Aedes aegypti mosquito from where it hatched?",
                        "options": [
                            {
                                "option_id": "q4-short-range",
                                "label": "A short radius of only 50 to 100 meters around the breeding site.",
                                "is_correct": True,
                                "feedback": "Vital public health insight! If you are being bitten by Aedes, its breeding site is almost certainly inside your own home, on your balcony, or in your immediate neighbor's yard.",
                            },
                            {
                                "option_id": "q4-long-migr",
                                "label": "Over 500 kilometers across international borders.",
                                "is_correct": False,
                                "feedback": "Aedes is a weak flier that rarely travels more than 100 meters from its emergence point.",
                            },
                            {
                                "option_id": "q4-zero-cm",
                                "label": "It cannot fly at all and only walks on carpets.",
                                "is_correct": False,
                                "feedback": "Aedes adult females fly actively within a 50-100 meter radius.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "breed-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why do only female mosquitoes take blood meals from humans and animals?",
                        "options": [
                            {
                                "option_id": "q5-egg-protein",
                                "label": "Females need the protein and iron in blood to develop and nourish their eggs; males feed exclusively on flower nectar.",
                                "is_correct": True,
                                "feedback": "Exact entomological science! Males lack piercing mouthparts and feed on nectar; only females bite to obtain protein for egg production.",
                            },
                            {
                                "option_id": "q5-anger",
                                "label": "Females bite out of anger while males are peaceful.",
                                "is_correct": False,
                                "feedback": "Biting is a biological reproductive necessity, not an emotional reaction.",
                            },
                            {
                                "option_id": "q5-male-poison",
                                "label": "Human blood is fatal to male mosquitoes.",
                                "is_correct": False,
                                "feedback": "Male mosquito mouthparts are physically incapable of piercing skin.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "breed-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Dengue Breeds in Clean Containers: Aedes mosquitoes breed in clean household containers (potted plant trays, cooler basins, fresh water jars).",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Daytime Biting: Aedes mosquitoes bite aggressively in daylight, peaking in early mornings and late afternoons.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Inspect your balcony and living room right now. Empty any standing water in potted plant saucers, feng shui bamboo bowls, or refrigerator defrost trays!",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319", "src-dengue-and-severe-d-7821"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 2: Finding and Eliminating Breeding Sites [STABLE ID: lesson-mosquito-control]
        {
            "version_id": "ver-mosquito-control-2",
            "lesson_id": "lesson-mosquito-control",
            "version_number": 2,
            "title": "Finding and Eliminating Breeding Sites",
            "summary": "Master the weekly household 'Dry Day' protocol: systematic indoor and outdoor container audits, scrubbing desiccated eggs, desert cooler maintenance, and larvicide use.",
            "language": "en",
            "learning_objectives": [
                "Implement the weekly 'Dry Day' container management protocol.",
                "Demonstrate the Desert Cooler maintenance routine (drain, scrub, dry, larvicide).",
                "Identify hidden breeding micro-habitats (tyres, overhead tanks, elevator shafts, construction sites).",
                "Explain the role of biological control (Gambusia fish) and chemical larvicides (Temephos).",
            ],
            "estimated_duration_minutes": 7,
            "status": "published",
            "source_ids": ["src-vector-control-measu-4319", "src-do-s-and-don-ts-1543"],
            "cards": [
                {
                    "card_id": "ctrl-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Sunday Morning 'Dry Day' Routine"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Kiran",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Ramesh, why are you emptying our desert cooler and scrubbing the sides with a stiff nylon brush? The monsoon just started; we might need the cooler next week!",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Ramesh",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Kiran, today is Sunday—our designated community 'Dry Day'! In our humid weather, a neglected cooler tray becomes a breeding factory for thousands of Dengue mosquitoes. If I just pour the water out, the eggs stay glued to the metal walls. We must scrub the walls, let it dry completely in the sun, or add two drops of temephos larvicide!",
                        },
                        {
                            "block_type": "callout",
                            "body": "The National 'Dry Day' Initiative: India's National Center for Vector Borne Diseases Control (NCVBDC) champions observing one designated day every week (such as Sunday) as 'Dry Day'—emptying, scrubbing, and drying all domestic water containers to interrupt the 7-to-10-day mosquito lifecycle.",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319", "src-do-s-and-don-ts-1543"],
                    "interaction": None,
                },
                {
                    "card_id": "ctrl-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Sequence the Desert Cooler Protocol"},
                        {
                            "block_type": "text",
                            "body": "Evaporative desert coolers are the number-one domestic breeding source for Dengue in northern and central India during summer and monsoon transitions. Arrange the maintenance steps in correct order.",
                        },
                    ],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "arrange_steps",
                        "question_prompt": "Arrange the weekly desert cooler maintenance steps in the correct order:",
                        "options": [
                            {"option_id": "step-drain", "label": "1. Turn off power and completely drain all standing water from the cooler tank", "is_correct": True, "feedback": "Removes existing swimming larvae and pupae."},
                            {"option_id": "step-scrub-tank", "label": "2. Thoroughly scrub the inside tank walls and corners with a brush and detergent", "is_correct": True, "feedback": "Dislodges stubborn eggs glued to the metal/plastic seams."},
                            {"option_id": "step-sun-dry", "label": "3. Leave the tank open to dry completely in the sun for at least 24 hours", "is_correct": True, "feedback": "Total dryness kills desiccated eggs."},
                            {"option_id": "step-refill-larvicide", "label": "4. Refill with fresh water and add government-approved larvicide (e.g. temephos/Bti) if not in continuous use", "is_correct": True, "feedback": "Prevents newly arriving mosquitoes from successfully breeding."},
                        ],
                        "correct_order": ["step-drain", "step-scrub-tank", "step-sun-dry", "step-refill-larvicide"],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "ctrl-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Overhead Tanks and Outdoor Breeding Hotspots"},
                        {
                            "block_type": "text",
                            "body": "Rooftop Sintex water tanks, broken concrete overhead tanks, and elevator machine sumps often breed millions of mosquitoes unobserved above residential buildings.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Prevention Essentials:\n• Cover Overhead Tanks: Ensure tank lids are tightly screwed shut. Cover vent and overflow pipes with fine stainless steel mosquito mesh.\n• Invert Empty Containers: Store unused buckets, paint cans, and drums inverted (upside down) under a shelter.\n• Biological Larvicide: Introduce larvivorous fish (Gambusia affinis or Guppy) into large non-potable ornamental fountains, construction tanks, and garden ponds to feed voraciously on larvae.",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": None,
                },
                {
                    "card_id": "ctrl-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Identify Terrace and Backyard Hazards"},
                    ],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "identify_risk",
                        "question_prompt": "Select all dangerous mosquito breeding sites in a residential terrace and backyard:",
                        "scene_description": "A residential rooftop: discarded automobile tyre filled with rainwater, open coconut shells, a tightly sealed overhead water tank with intact lid, an open bucket catching air conditioner drain drips.",
                        "options": [
                            {
                                "option_id": "risk-tyre",
                                "label": "Discarded vehicle tyre storing rainwater inside its curved rim",
                                "is_correct": True,
                                "feedback": "Tyres provide warm, shaded, dark water—the ideal natural micro-habitat for Aedes mosquitoes.",
                            },
                            {
                                "option_id": "risk-coconut-shells",
                                "label": "Empty broken coconut shells lying in the backyard garden",
                                "is_correct": True,
                                "feedback": "Curved organic shells collect rainwater and harbor dozens of developing larvae.",
                            },
                            {
                                "option_id": "risk-ac-bucket",
                                "label": "Uncovered bucket collecting continuous condensation drips from the AC unit",
                                "is_correct": True,
                                "feedback": "Clean, undisturbed AC condensation water is a frequent urban breeding hotspot.",
                            },
                            {
                                "option_id": "safe-sealed-tank",
                                "label": "Rooftop overhead tank with a tightly secured, sealed inspection lid",
                                "is_correct": False,
                                "feedback": "A tightly sealed tank prevents adult mosquitoes from entering to lay eggs.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "ctrl-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is simply pouring out the water from a cooler or flower vase without scrubbing the sides insufficient to prevent future breeding?",
                        "options": [
                            {
                                "option_id": "q1-glued-eggs",
                                "label": "Aedes eggs are glued to the container walls with sticky protein and survive completely dry for months, hatching the moment the vessel is refilled.",
                                "is_correct": True,
                                "feedback": "Exact public health reason! Physical scrubbing with a brush or cloth is required to dislodge desiccated eggs.",
                            },
                            {
                                "option_id": "q1-larvae-walk",
                                "label": "Larvae can walk across dry carpets to find another water bucket.",
                                "is_correct": False,
                                "feedback": "Larvae are aquatic and cannot walk on land.",
                            },
                            {
                                "option_id": "q1-plastic-eats",
                                "label": "The plastic itself generates new mosquito larvae through spontaneous generation.",
                                "is_correct": False,
                                "feedback": "Spontaneous generation was disproven centuries ago; eggs produce larvae.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "ctrl-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the primary role of larvivorous fish species such as Gambusia affinis or Guppies in community water bodies?",
                        "options": [
                            {
                                "option_id": "q2-eat-larvae",
                                "label": "They provide biological control by actively feeding on mosquito larvae and pupae in large open tanks, ponds, and fountains.",
                                "is_correct": True,
                                "feedback": "Correct! Gambusia consume up to 100 to 300 larvae daily, suppressing mosquito populations naturally without chemical insecticides.",
                            },
                            {
                                "option_id": "q2-poison-water",
                                "label": "They secrete chemical toxins that kill adult flying mosquitoes in the air.",
                                "is_correct": False,
                                "feedback": "Fish feed on aquatic larvae; they do not kill flying adult mosquitoes.",
                            },
                            {
                                "option_id": "q2-filter-salt",
                                "label": "They filter table salt out of domestic drinking water.",
                                "is_correct": False,
                                "feedback": "Gambusia are biological vector control predators, not desalination filters.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "ctrl-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What should be done with air conditioner (AC) drain pipes that drip continuous condensation water onto balconies or alleys?",
                        "options": [
                            {
                                "option_id": "q3-direct-drain",
                                "label": "Direct the pipe into a closed domestic drain or empty the collection bucket daily without letting it stagnate.",
                                "is_correct": True,
                                "feedback": "Correct! AC condensate is pure, clean water—ideal for Aedes breeding if allowed to pool in open containers.",
                            },
                            {
                                "option_id": "q3-leave-open",
                                "label": "Collect it in an open 50-liter bucket on the balcony and never empty it.",
                                "is_correct": False,
                                "feedback": "Leaving open condensation buckets creates a prime breeding hazard.",
                            },
                            {
                                "option_id": "q3-mix-sugar",
                                "label": "Add sugar to the AC bucket to turn it into syrup.",
                                "is_correct": False,
                                "feedback": "Sugar attracts ants and flies and does not prevent mosquito breeding.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "ctrl-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What chemical larvicide is approved by public health authorities for treating stagnant water in large coolers and construction sites?",
                        "options": [
                            {
                                "option_id": "q4-temephos",
                                "label": "Temephos (an organophosphate larvicide) or Bacillus thuringiensis israelensis (Bti).",
                                "is_correct": True,
                                "feedback": "Exact public health formulation! Temephos and Bti specifically target aquatic mosquito larvae with high safety margins when dosed correctly.",
                            },
                            {
                                "option_id": "q4-kerosene-fire",
                                "label": "Raw motor petrol ignited with a lighter.",
                                "is_correct": False,
                                "feedback": "Igniting petrol is extremely dangerous and illegal.",
                            },
                            {
                                "option_id": "q4-cyanide",
                                "label": "Potassium cyanide crystals.",
                                "is_correct": False,
                                "feedback": "Cyanide is an extremely lethal poison prohibited in public health vector control.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "ctrl-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why should unused domestic buckets, washbasins, and garden pots always be stored inverted (upside down)?",
                        "options": [
                            {
                                "option_id": "q5-prevent-pooling",
                                "label": "Inverting containers prevents rainwater or lawn sprinkler drops from collecting inside and creating accidental breeding pools.",
                                "is_correct": True,
                                "feedback": "Exact preventative reasoning! An upside-down vessel cannot collect standing water.",
                            },
                            {
                                "option_id": "q5-make-sturdier",
                                "label": "Plastic melts if stored upright under moonlit skies.",
                                "is_correct": False,
                                "feedback": "Moonlight does not melt plastic; the goal is preventing water accumulation.",
                            },
                            {
                                "option_id": "q5-earth-magnet",
                                "label": "Earth's gravity crushes upright buckets over time.",
                                "is_correct": False,
                                "feedback": "Gravity does not crush empty buckets; storing inverted is strictly for vector control.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "ctrl-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Weekly 'Dry Day': Empty, scrub, and sun-dry desert coolers, potted plant saucers, and storage drums every 7 days.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Seal Rooftop Tanks: Cover all overhead water tank inspection openings and mesh all overflow vents.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Pick your weekly 'Dry Day' (e.g. every Sunday morning) and carry out a 15-minute container inspection of your terrace and yard today!",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319", "src-do-s-and-don-ts-1543"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 3: Protecting Yourself at Home and Outdoors [STABLE ID: lesson-protect-yourself-and-your-fami-3513]
        {
            "version_id": "ver-protect-family-2",
            "lesson_id": "lesson-protect-yourself-and-your-fami-3513",
            "version_number": 2,
            "title": "Protecting Yourself at Home and Outdoors",
            "summary": "Master personal vector protection: EPA-approved skin repellents (DEET, Picaridin), window netting, long-lasting insecticidal nets (LLINs), and baby protection.",
            "language": "en",
            "learning_objectives": [
                "Select evidence-based active ingredients in mosquito repellents (DEET, Picaridin, Oil of Lemon Eucalyptus).",
                "Demonstrate safe repellent application on children and infants.",
                "Describe the proper tucking and maintenance of Long-Lasting Insecticidal Nets (LLINs).",
                "Evaluate the effectiveness of window mesh screens versus indoor coils and vaporizers.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "source_ids": ["src-cdc-mosquito", "src-malaria-control-stra-6564"],
            "cards": [
                {
                    "card_id": "prot-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Protecting Baby Aarav"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Divya",
                            "avatar": "👩🏽",
                            "side": "left",
                            "body": "Dr. Mohan, our 8-month-old baby Aarav gets bitten by mosquitoes during his evening naps. I was about to spray strong chemical aerosol insecticide inside his nursery and light a burning green mosquito coil by his crib.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Dr. Mohan",
                            "avatar": "👨🏽",
                            "side": "right",
                            "body": "Please don't do that, Divya! Burning mosquito coils releases heavy particulate smoke (equivalent to smoking 75 to 100 cigarettes!), severely irritating an infant's developing lungs. The safest, most effective gold-standard protection for an infant is physical barrier netting: a fine mosquito net draped over the crib and intact wire mesh on bedroom windows!",
                        },
                        {
                            "block_type": "callout",
                            "body": "Coil Smoke Warning: Burning indoor mosquito coils generates volatile organic compounds (formaldehyde) and high levels of PM2.5 particulate matter, triggering pediatric asthma and respiratory inflammation.",
                        },
                    ],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": None,
                },
                {
                    "card_id": "prot-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Safe Repellent Usage"},
                    ],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all verified, safe guidelines for applying EPA-registered skin mosquito repellents (like DEET or Picaridin):",
                        "options": [
                            {"option_id": "rep-apply-exposed", "label": "Apply repellent only to exposed skin and clothing; do not apply underneath clothes", "is_correct": True, "feedback": "Underneath clothing, skin absorbs chemicals more readily without added repellent benefit."},
                            {"option_id": "rep-avoid-eyes", "label": "Do not spray directly onto the face; spray onto hands first and gently rub onto face, avoiding eyes and mouth", "is_correct": True, "feedback": "Prevents accidental eye irritation or chemical ingestion."},
                            {"option_id": "rep-no-infant-hands", "label": "Never apply repellent to a young child's hands or palms", "is_correct": True, "feedback": "Children frequently put their fingers and hands into their mouths and rub their eyes."},
                            {"option_id": "rep-drink-repellent", "label": "Swallow a teaspoon of repellent every morning to sweat it out of pores", "is_correct": False, "feedback": "Skin repellents are strictly for external topical use and are toxic if swallowed."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "prot-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Long-Lasting Insecticidal Nets (LLINs)"},
                        {
                            "block_type": "text",
                            "body": "Long-Lasting Insecticidal Nets (LLINs) are treated with microscopic pyrethroid insecticides that both repel and kill mosquitoes on contact.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Proper Net Usage:\n1. Tuck the bottom edge of the net securely underneath the mattress on all sides so mosquitoes cannot crawl underneath.\n2. Ensure the net is hung square without loose sagging folds touching the sleeper's skin.\n3. Repair any small tears promptly with needle and thread.\n4. Wash gently in cold water with mild soap; LLIN insecticidal potency lasts for 20 gentle washes (approximately 3 to 5 years).",
                        },
                    ],
                    "source_ids": ["src-malaria-control-stra-6564"],
                    "interaction": None,
                },
                {
                    "card_id": "prot-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Physical Barriers vs Chemical Vapors"},
                    ],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the most durable, non-toxic, 24-hour intervention for preventing mosquitoes from entering residential bedrooms?",
                        "options": [
                            {
                                "option_id": "mesh-screens",
                                "label": "Installing intact, fine wire or nylon mesh screens on all windows and exterior doors.",
                                "is_correct": True,
                                "feedback": "Correct! Window mesh screens allow continuous natural ventilation while physically blocking mosquitoes without toxic fumes.",
                            },
                            {
                                "option_id": "burn-paper",
                                "label": "Burning newspaper piles in the hallway every evening.",
                                "is_correct": False,
                                "feedback": "Burning paper creates hazardous carbon monoxide and fire risks.",
                            },
                            {
                                "option_id": "loud-speaker",
                                "label": "Playing ultrasonic frequencies through mobile phone speakers.",
                                "is_correct": False,
                                "feedback": "Scientific trials show ultrasonic phone apps have zero repellent effect on biting mosquitoes.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "prot-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which of the following active ingredients has rigorous scientific clinical evidence supporting its safety and efficacy as an EPA-registered skin mosquito repellent?",
                        "options": [
                            {
                                "option_id": "q1-deet-picaridin",
                                "label": "DEET (N,N-Diethyl-meta-toluamide) and Picaridin (KBR 3023).",
                                "is_correct": True,
                                "feedback": "Spot on! DEET and Picaridin are the gold-standard topical repellents with decades of safety and efficacy testing.",
                            },
                            {
                                "option_id": "q1-vitamin-b1",
                                "label": "Oral Vitamin B1 (thiamine) supplements.",
                                "is_correct": False,
                                "feedback": "Numerous controlled clinical trials have disproven the myth that oral Vitamin B1 repels mosquitoes.",
                            },
                            {
                                "option_id": "q1-garlic-neck",
                                "label": "Wearing a necklace made of raw garlic cloves.",
                                "is_correct": False,
                                "feedback": "Garlic necklaces have zero scientific repellent efficacy.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "prot-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What clothing choice offers the best personal protection against mosquito bites during outdoor morning and evening activities?",
                        "options": [
                            {
                                "option_id": "q2-loose-light-long",
                                "label": "Loose-fitting, light-colored long-sleeved shirts and full-length trousers.",
                                "is_correct": True,
                                "feedback": "Exact public health recommendation! Dark colors attract mosquitoes, and tight clothes allow proboscises to pierce through fabric.",
                            },
                            {
                                "option_id": "q2-tight-black",
                                "label": "Tight-fitting, jet black sleeveless vests and shorts.",
                                "is_correct": False,
                                "feedback": "Dark clothing absorbs heat and attracts mosquitoes, while exposed limbs invite bites.",
                            },
                            {
                                "option_id": "q2-wet-swimsuit",
                                "label": "Wet wool sweaters with no pants.",
                                "is_correct": False,
                                "feedback": "Impractical and leaves legs completely unprotected.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "prot-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-malaria-control-stra-6564"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is it important to tuck the bottom edges of a bed net securely underneath the mattress on all sides?",
                        "options": [
                            {
                                "option_id": "q3-tuck-mattress",
                                "label": "Mosquitoes search for tiny gaps and can easily fly or crawl underneath loose hanging net edges during the night.",
                                "is_correct": True,
                                "feedback": "Correct! An untucked net allows mosquitoes to enter near the floor and traps them inside with the sleeper.",
                            },
                            {
                                "option_id": "q3-bed-air",
                                "label": "To stop mattress air from escaping into the room.",
                                "is_correct": False,
                                "feedback": "Mattresses do not leak room air; tucking is strictly to block mosquito ingress.",
                            },
                            {
                                "option_id": "q3-sheet-wrinkle",
                                "label": "To prevent bed sheets from wrinkling.",
                                "is_correct": False,
                                "feedback": "Tucking is a critical vector barrier, not an ironing method.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "prot-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "At what age does the CDC recommend that chemical repellents containing Oil of Lemon Eucalyptus (OLE) or para-menthane-diol (PMD) should NOT be used?",
                        "options": [
                            {
                                "option_id": "q4-under-3-years",
                                "label": "Children under 3 years of age.",
                                "is_correct": True,
                                "feedback": "Exact safety specification! OLE/PMD is not recommended for children under 3. For infants under 2 months, no chemical repellents are recommended (use crib netting).",
                            },
                            {
                                "option_id": "q4-under-18-years",
                                "label": "Teenagers under 18 years.",
                                "is_correct": False,
                                "feedback": "OLE is approved and safe for children aged 3 and older and all adults.",
                            },
                            {
                                "option_id": "q4-over-60-years",
                                "label": "Only adults over 60 years.",
                                "is_correct": False,
                                "feedback": "Senior adults can safely use approved repellents according to label instructions.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "prot-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-cdc-mosquito"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "When applying both sunscreen and insect repellent before going outdoors, in what order should they be applied?",
                        "options": [
                            {
                                "option_id": "q5-sunscreen-first",
                                "label": "Apply sunscreen first, allow it to absorb for 15-20 minutes, and then apply insect repellent on top.",
                                "is_correct": True,
                                "feedback": "Correct! Sunscreen needs skin contact to absorb, and repellent must be on the outer layer to vaporize and repel insects.",
                            },
                            {
                                "option_id": "q5-repellent-first",
                                "label": "Apply repellent first and immediately cover it with thick greasy sunscreen.",
                                "is_correct": False,
                                "feedback": "Coating repellent under sunscreen blocks its evaporation, impairing repellent efficacy.",
                            },
                            {
                                "option_id": "q5-mix-bottle",
                                "label": "Pour both bottles together into a cup and microwave for 30 seconds.",
                                "is_correct": False,
                                "feedback": "Never microwave personal care chemicals; apply separately as directed.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "prot-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Nets Beat Smoke: Use crib netting and window mesh rather than burning mosquito coils that damage infant and adult lungs.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Wear Light & Loose: Light-colored, loose long sleeves protect skin during peak dawn and dusk hours.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Inspect the window mesh screens and bed nets in your home today. Patch any small holes with needle and thread or adhesive tape before sunset!",
                        },
                    ],
                    "source_ids": ["src-cdc-mosquito", "src-malaria-control-stra-6564"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 4: Understanding Mosquito-Borne Illnesses and Seeking Appropriate Care [STABLE ID: lesson-community-prevention-symptoms--4817]
        {
            "version_id": "ver-symptoms-care-2",
            "lesson_id": "lesson-community-prevention-symptoms--4817",
            "version_number": 2,
            "title": "Understanding Mosquito-Borne Illnesses and Seeking Appropriate Care",
            "summary": "Recognize critical Dengue, Malaria, and Chikungunya symptoms, identify emergency Dengue warning signs, understand the life-threatening danger of Aspirin/Ibuprofen, and master hydration.",
            "language": "en",
            "learning_objectives": [
                "Differentiate clinical symptom presentations of Dengue, Malaria, and Chikungunya.",
                "Identify emergency 'warning signs' of severe Dengue requiring immediate hospital admission.",
                "Explain why NSAIDs (Aspirin, Ibuprofen, Diclofenac) are strictly contraindicated in suspected Dengue.",
                "Describe the essential role of oral fluid maintenance and early blood testing.",
            ],
            "estimated_duration_minutes": 7,
            "status": "published",
            "source_ids": ["src-dengue-and-severe-d-7821", "src-ncvbdc-clinical", "src-malaria-control-stra-6564"],
            "cards": [
                {
                    "card_id": "care-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "A Sudden High Fever"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Rohan",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Dr. Lakshmi, I woke up with 103°F fever, severe pain behind my eyes, and my back and bones ache so badly it feels like they're breaking! A friend told me to take Brufen (Ibuprofen) or Disprin (Aspirin) to stop the body aches.",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Dr. Lakshmi",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Stop, Rohan! Never take Aspirin, Ibuprofen, or Diclofenac when you have sudden fever during Dengue season! Dengue damages blood platelets and causes capillary fragility. NSAIDs like Ibuprofen thin your blood and trigger massive, life-threatening internal gastrointestinal bleeding! The only safe medicine for fever and pain in suspected Dengue is Paracetamol, along with continuous oral fluids.",
                        },
                        {
                            "block_type": "callout",
                            "body": "CRITICAL MEDICAL WARNING: In any acute febrile illness where Dengue is possible, DO NOT take Aspirin, Ibuprofen, Naproxen, or Diclofenac. They inhibit platelet aggregation and dramatically elevate the risk of fatal hemorrhage. Use Paracetamol only (following weight-appropriate dosing), and seek professional medical evaluation.",
                        },
                    ],
                    "source_ids": ["src-dengue-and-severe-d-7821", "src-ncvbdc-clinical"],
                    "interaction": None,
                },
                {
                    "card_id": "care-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Safe Fever Medication"},
                    ],
                    "source_ids": ["src-ncvbdc-clinical"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Which medicine is medically safe to reduce fever and body aches in a patient with suspected Dengue fever?",
                        "options": [
                            {
                                "option_id": "med-paracetamol",
                                "label": "Paracetamol (Acetaminophen) at appropriate dosages, accompanied by ample oral fluids.",
                                "is_correct": True,
                                "feedback": "Correct! Paracetamol does not impair platelet function or irritate gastric mucosa, making it the only safe choice in Dengue.",
                            },
                            {
                                "option_id": "med-aspirin",
                                "label": "Aspirin (Disprin) to thin the blood quickly.",
                                "is_correct": False,
                                "feedback": "Lethal hazard! Aspirin irreversibly inhibits platelets and triggers catastrophic internal bleeding in Dengue.",
                            },
                            {
                                "option_id": "med-ibuprofen",
                                "label": "Ibuprofen (Brufen) or Combiflam.",
                                "is_correct": False,
                                "feedback": "Strictly contraindicated! NSAIDs cause gastric ulceration and severe hemorrhagic complications in Dengue.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "care-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Dengue Warning Signs (Critical Phase)"},
                        {
                            "block_type": "text",
                            "body": "In Dengue fever, the most dangerous phase—the 'Critical Phase'—occurs around day 3 to day 7, often just as the high fever begins to drop! This is when plasma leakage from blood vessels into body cavities can cause severe Dengue shock.",
                        },
                        {
                            "block_type": "callout",
                            "body": "WHO & NCVBDC Dengue Warning Signs:\n• Severe, unrelenting abdominal pain or tenderness\n• Persistent vomiting (at least 3 episodes in 24 hours)\n• Bleeding from gums, nose, or blood in vomit/stool\n• Lethargy, extreme restlessness, or confusion\n• Rapid breathing and cold, clammy extremities\n• Sudden drop in platelet count accompanied by a rising hematocrit\n\nIf ANY of these signs appear, rush immediately to a hospital emergency department!",
                        },
                    ],
                    "source_ids": ["src-dengue-and-severe-d-7821", "src-ncvbdc-clinical"],
                    "interaction": None,
                },
                {
                    "card_id": "care-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Emergency Warning Signs"},
                    ],
                    "source_ids": ["src-dengue-and-severe-d-7821"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all clinical warning signs in a Dengue patient that require immediate hospital admission:",
                        "options": [
                            {"option_id": "warn-bleed", "label": "Bleeding from the gums or nose, or black tarry stools", "is_correct": True, "feedback": "Indicates hemorrhagic diathesis requiring inpatient monitoring."},
                            {"option_id": "warn-vomit", "label": "Persistent vomiting that prevents the patient from retaining any oral fluids", "is_correct": True, "feedback": "Leads to rapid dehydration and precludes oral fluid therapy."},
                            {"option_id": "warn-abdo-pain", "label": "Severe, persistent abdominal pain or tenderness", "is_correct": True, "feedback": "Classic indicator of plasma leakage into the peritoneal cavity."},
                            {"option_id": "warn-normal-appetite", "label": "Asking for regular dinner and feeling energetic", "is_correct": False, "feedback": "A cheerful appetite and high energy indicate recovery, not a warning sign."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "care-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-dengue-and-severe-d-7821"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is the 24 to 48 hour period when a Dengue patient's high fever drops to normal considered the most dangerous 'Critical Phase'?",
                        "options": [
                            {
                                "option_id": "q1-plasma-leak",
                                "label": "Capillary permeability increases during this phase, causing plasma leakage, fluid accumulation, and potential circulatory shock.",
                                "is_correct": True,
                                "feedback": "Vital clinical knowledge! Many families mistakenly assume fever defervescence means cure, when it actually marks the onset of potential shock.",
                            },
                            {
                                "option_id": "q1-teeth-fall",
                                "label": "All adult teeth fall out when the fever drops.",
                                "is_correct": False,
                                "feedback": "Dengue does not cause teeth to fall out; plasma leakage is the true hazard.",
                            },
                            {
                                "option_id": "q1-hair-green",
                                "label": "Hair turns bright green when fever breaks.",
                                "is_correct": False,
                                "feedback": "Hair color is unaffected.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "care-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-ncvbdc-clinical"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why are Non-Steroidal Anti-Inflammatory Drugs (NSAIDs) like Ibuprofen, Aspirin, and Diclofenac strictly forbidden in Dengue?",
                        "options": [
                            {
                                "option_id": "q2-nsaid-bleed",
                                "label": "They impair platelet aggregation and cause gastric erosions, triggering life-threatening internal hemorrhage.",
                                "is_correct": True,
                                "feedback": "Correct! Platelets are already compromised by Dengue; adding antiplatelet NSAIDs can cause fatal gastrointestinal hemorrhage.",
                            },
                            {
                                "option_id": "q2-bitter-taste",
                                "label": "They make milk taste too bitter to drink.",
                                "is_correct": False,
                                "feedback": "Taste is irrelevant; the danger is lethal internal hemorrhage.",
                            },
                            {
                                "option_id": "q2-freeze-blood",
                                "label": "They cause blood to freeze solid like an icicle.",
                                "is_correct": False,
                                "feedback": "NSAIDs inhibit clotting; they do not freeze blood.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "care-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-malaria-control-stra-6564"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What classic cyclical fever pattern is typically observed in classic uncomplicated Malaria?",
                        "options": [
                            {
                                "option_id": "q3-chills-fever-sweat",
                                "label": "A recurrent triad of cold stage (shivering/chills), hot stage (high fever), and sweating stage every 48 to 72 hours.",
                                "is_correct": True,
                                "feedback": "Correct! The rupture of red blood cell schizonts releases merozoites, causing classic paroxysms of chills, fever, and drenching sweats.",
                            },
                            {
                                "option_id": "q3-constant-cold",
                                "label": "The patient feels permanently like ice with zero body warmth for 1 year.",
                                "is_correct": False,
                                "feedback": "Malaria causes distinct cyclical febrile spikes, not permanent hypothermia.",
                            },
                            {
                                "option_id": "q3-sleepy-only",
                                "label": "Zero fever, but the patient only sleeps while walking.",
                                "is_correct": False,
                                "feedback": "High fever and chills are hallmark clinical manifestations.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "care-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-dengue-and-severe-d-7821"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the primary supportive treatment for a patient with uncomplicated Dengue fever resting at home?",
                        "options": [
                            {
                                "option_id": "q4-hydration",
                                "label": "Generous oral fluid intake (ORS, coconut water, fresh lime water, soups) and paracetamol for fever.",
                                "is_correct": True,
                                "feedback": "Exact clinical recommendation! Maintaining vigorous oral hydration counters early plasma leakage and prevents progression to shock.",
                            },
                            {
                                "option_id": "q4-antibiotics",
                                "label": "Taking heavy doses of broad-spectrum antibacterial antibiotics without a prescription.",
                                "is_correct": False,
                                "feedback": "Dengue is caused by a virus (DENV); antibacterial antibiotics have zero effect on viruses and cause gut dysbiosis.",
                            },
                            {
                                "option_id": "q4-dehydration",
                                "label": "Completely withholding water to prevent fluid accumulation.",
                                "is_correct": False,
                                "feedback": "Withholding fluids accelerates Dengue hypovolemic shock, leading to multi-organ failure.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "care-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-malaria-control-stra-6564"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How is a suspected case of Malaria definitively diagnosed at a Primary Health Centre (PHC)?",
                        "options": [
                            {
                                "option_id": "q5-blood-smear-rdt",
                                "label": "By microscopic examination of a peripheral blood smear (thick and thin films) or an approved Rapid Diagnostic Test (RDT).",
                                "is_correct": True,
                                "feedback": "Exact laboratory standard! Blood microscopy and RDTs detect Plasmodium parasites or antigen proteins directly.",
                            },
                            {
                                "option_id": "q5-guess",
                                "label": "By guessing based on the patient's favorite color.",
                                "is_correct": False,
                                "feedback": "Parasitological confirmation is required before initiating antimalarial therapy.",
                            },
                            {
                                "option_id": "q5-xray",
                                "label": "By taking an ankle X-ray.",
                                "is_correct": False,
                                "feedback": "Malaria is a blood-borne parasite, not a bone fracture.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "care-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "NO Aspirin / Ibuprofen: In suspected Dengue, use ONLY Paracetamol and copious fluids; NSAIDs trigger fatal internal bleeding.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Watch the Critical Phase: When fever drops, watch for severe abdominal pain, persistent vomiting, or bleeding—rush to the hospital immediately if seen.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Check your home medicine cabinet right now. Clearly mark Paracetamol as your household fever medicine, and ensure no family member takes Ibuprofen or Aspirin for sudden unverified fever!",
                        },
                    ],
                    "source_ids": ["src-dengue-and-severe-d-7821", "src-ncvbdc-clinical"],
                    "interaction": None,
                },
            ],
        },

        # Chapter 5: Organising a Neighbourhood Prevention Campaign
        {
            "version_id": "ver-neighbourhood-campaign-1",
            "lesson_id": "lesson-neighbourhood-mosquito-campaign",
            "version_number": 1,
            "title": "Organising a Neighbourhood Prevention Campaign",
            "summary": "Mobilize your community: collective source reduction drives, street mapping, partnering with ASHA workers and municipal anti-larval teams, and respectfully engaging neighbors.",
            "language": "en",
            "learning_objectives": [
                "Explain why individual household vector control fails without collective community action.",
                "Organize a systematic community 'Source Reduction Drive' across shared streets and vacant plots.",
                "Coordinate with local ASHA workers, ward corporators, and municipal health inspectors.",
                "Apply respectful communication strategies when pointing out breeding hazards on neighbors' properties.",
            ],
            "estimated_duration_minutes": 6,
            "status": "published",
            "status": "published",
            "source_ids": ["src-vector-control-measu-4319", "src-do-s-and-don-ts-1543"],
            "cards": [
                {
                    "card_id": "camp-card-1",
                    "position": 1,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Why One Clean House Isn't Enough"},
                        {
                            "block_type": "dialogue",
                            "speaker": "Tarun",
                            "avatar": "👨🏽",
                            "side": "left",
                            "body": "Sister Sunita, our family emptied every single cup, pot, and cooler in our house. We observed Dry Day religiously! Yet my younger brother still got infected with Dengue. How is that fair?",
                        },
                        {
                            "block_type": "dialogue",
                            "speaker": "Sunita (ASHA)",
                            "avatar": "👩🏽",
                            "side": "right",
                            "body": "Tarun, your personal diligence is wonderful, but remember: an Aedes mosquito has a flight radius of 100 meters! Across the alley, the vacant construction plot has unsealed water curing tanks, and the corner house has three old tyres filled with rainwater. Mosquitoes born there fly straight through your open balcony! Vector control cannot succeed as an isolated act—it requires a coordinated neighbourhood effort.",
                        },
                        {
                            "block_type": "callout",
                            "body": "The 100-Meter Community Shield: Because mosquitoes travel across boundary walls and alleys, a neighbourhood is only as protected as its most neglected water container. Community-wide source reduction breaks transmission across entire wards.",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": None,
                },
                {
                    "card_id": "camp-card-2",
                    "position": 2,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 1: Community Mapping Priorities"},
                    ],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "When planning a neighbourhood source reduction drive after monsoon rains, which area is the highest priority for breeding site elimination?",
                        "options": [
                            {
                                "option_id": "map-priority-vacant-tyres",
                                "label": "Vacant plots with construction curing tanks, discarded tyres behind garages, and clogged street roof gutters.",
                                "is_correct": True,
                                "feedback": "Correct! Unmonitored vacant plots and discarded scrap tyres generate massive vector densities that affect surrounding homes.",
                            },
                            {
                                "option_id": "map-priority-dry-sand",
                                "label": "Completely dry sand dunes in an open desert playground.",
                                "is_correct": False,
                                "feedback": "Dry sand cannot breed mosquitoes; stagnant water is required.",
                            },
                            {
                                "option_id": "map-priority-clean-pavement",
                                "label": "Swept concrete roads with zero puddles.",
                                "is_correct": False,
                                "feedback": "Dry pavements pose zero vector breeding hazard.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "camp-card-3",
                    "position": 3,
                    "card_type": "explanation",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Partnering with Municipal & Health Workers"},
                        {
                            "block_type": "text",
                            "body": "Citizen action is most powerful when connected to official public health resources.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Key Official Partners:\n• ASHA & Anganwadi Workers: Provide door-to-door health education, track fever cases, and supply ORS and paracetamol.\n• Municipal Sanitary Inspectors: Have legal authority to inspect locked premises, issue notices for unmanaged breeding, and deploy vehicle-mounted fogging and larvicide teams.\n• Resident Welfare Associations (RWAs) / Gram Panchayats: Can mandate weekly Dry Days across all building societies and clear community solid waste.",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": None,
                },
                {
                    "card_id": "camp-card-4",
                    "position": 4,
                    "card_type": "interaction",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Practice Check 2: Effective Community Action Items"},
                    ],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "multi_select",
                        "question_prompt": "Select all effective, sustainable activities for a neighbourhood mosquito prevention youth club:",
                        "options": [
                            {"option_id": "act-dry-day-drive", "label": "Organizing a Sunday morning volunteer walk to inspect alleys and help elderly neighbors clean desert coolers", "is_correct": True, "feedback": "Hands-on source reduction directly eliminates thousands of larvae."},
                            {"option_id": "act-report-puddles", "label": "Reporting unsealed construction water tanks and clogged storm drains to municipal health officials", "is_correct": True, "feedback": "Enables official enforcement and large-scale larviciding."},
                            {"option_id": "act-solid-waste", "label": "Collecting and properly disposing of discarded coconut shells, plastic cups, and bottles from vacant lots", "is_correct": True, "feedback": "Eliminates prime outdoor rainwater micro-habitats."},
                            {"option_id": "act-burn-plastic", "label": "Setting fire to piles of plastic tyres and garbage in the street", "is_correct": False, "feedback": "Burning tyres releases toxic cancer-causing dioxins and black smoke; scrap tyres must be recycled or shredded dry."},
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                # Assessment Q1 to Q5
                {
                    "card_id": "camp-card-5",
                    "position": 5,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 1 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "Why is temporary outdoor thermal fogging (smoke spraying) alone NOT a permanent solution for mosquito control?",
                        "options": [
                            {
                                "option_id": "q1-fogging-adults-only",
                                "label": "Fogging only kills currently flying adult mosquitoes; it does not kill larvae or eggs in water, allowing thousands of new mosquitoes to hatch days later.",
                                "is_correct": True,
                                "feedback": "Exact public health limitation! Fogging is an emergency knockdown measure; source reduction (eliminating breeding sites) is the only permanent solution.",
                            },
                            {
                                "option_id": "q1-fogging-food",
                                "label": "Mosquitoes eat the fog smoke and grow ten times larger.",
                                "is_correct": False,
                                "feedback": "Mosquitoes do not eat insecticide fog.",
                            },
                            {
                                "option_id": "q1-fogging-clouds",
                                "label": "Fogging turns into storm clouds that wash away roads.",
                                "is_correct": False,
                                "feedback": "Thermal fogging disperses into air within minutes.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "camp-card-6",
                    "position": 6,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 2 of 5"}],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the most constructive way to approach a neighbor whose balcony has unmanaged flower pots breeding visible mosquito larvae?",
                        "options": [
                            {
                                "option_id": "q2-polite-inform",
                                "label": "Approach them respectfully, show them the swimming larvae, explain how Aedes transmits Dengue to nearby children, and offer to help empty and scrub the trays.",
                                "is_correct": True,
                                "feedback": "Correct! Respectful, collaborative engagement encourages long-term community cooperation and behavioral change.",
                            },
                            {
                                "option_id": "q2-shout-loud",
                                "label": "Scream at them from the street with a megaphone and throw stones at their windows.",
                                "is_correct": False,
                                "feedback": "Hostile confrontation creates resistance and divides the community.",
                            },
                            {
                                "option_id": "q2-ignore-complete",
                                "label": "Ignore it completely because someone else's balcony is none of your business.",
                                "is_correct": False,
                                "feedback": "Mosquitoes fly freely into your home; community vector control requires active neighborly communication.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "camp-card-7",
                    "position": 7,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 3 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What legal responsibility do building contractors and owners have regarding water curing tanks at construction sites under municipal bylaws?",
                        "options": [
                            {
                                "option_id": "q3-contractor-larvicide",
                                "label": "They are legally required to prevent mosquito breeding by covering tanks, introducing larvivorous fish, or dosing with approved larvicide weekly.",
                                "is_correct": True,
                                "feedback": "Correct! Municipal health bylaws penalize construction sites that allow stagnant water to breed disease vectors.",
                            },
                            {
                                "option_id": "q3-contractor-exempt",
                                "label": "Construction sites are completely exempt from all health and disease regulations.",
                                "is_correct": False,
                                "feedback": "Construction sites are prime inspection targets for municipal sanitary teams.",
                            },
                            {
                                "option_id": "q3-contractor-perfume",
                                "label": "They must spray perfume into concrete to attract bees.",
                                "is_correct": False,
                                "feedback": "The mandate is vector suppression via larvicides and covering.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "camp-card-8",
                    "position": 8,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 4 of 5"}],
                    "source_ids": ["src-vector-control-measu-4319"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "How does prompt solid waste collection (clearing plastic cups, wrappers, coconut shells) contribute directly to vector control?",
                        "options": [
                            {
                                "option_id": "q4-eliminate-micro-sites",
                                "label": "It removes thousands of tiny artificial catchment basins that would otherwise capture rainwater and breed Aedes mosquitoes.",
                                "is_correct": True,
                                "feedback": "Exact epidemiological connection! Solid waste management is an integral component of urban vector control.",
                            },
                            {
                                "option_id": "q4-make-pavement-pretty",
                                "label": "It makes pavements shinier so mosquitoes slip and fall.",
                                "is_correct": False,
                                "feedback": "Mosquitoes fly; removing waste removes water-holding receptacles.",
                            },
                            {
                                "option_id": "q4-feed-birds",
                                "label": "It provides food for migrating ducks.",
                                "is_correct": False,
                                "feedback": "Waste removal eliminates aquatic vector breeding habitats.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "camp-card-9",
                    "position": 9,
                    "card_type": "interaction",
                    "content_blocks": [{"block_type": "heading", "body": "Chapter Assessment Question 5 of 5"}],
                    "source_ids": ["src-do-s-and-don-ts-1543"],
                    "interaction": {
                        "interaction_type": "single_choice",
                        "question_prompt": "What is the single most effective long-term outcome of a successful community mosquito prevention campaign?",
                        "options": [
                            {
                                "option_id": "q5-sustained-habits",
                                "label": "Sustained citizen behavior change, where every family routinely observes weekly Dry Days and actively eliminates domestic standing water.",
                                "is_correct": True,
                                "feedback": "Spot on! Community empowerment and weekly habit formation provide lasting protection long after individual clean-up events end.",
                            },
                            {
                                "option_id": "q5-one-day-photo",
                                "label": "Taking a single photograph for social media and never inspecting water containers again.",
                                "is_correct": False,
                                "feedback": "One-off photo ops without continued maintenance fail to stop mosquito breeding.",
                            },
                            {
                                "option_id": "q5-buy-more-spray",
                                "label": "Spending all society funds on chemical aerosol spray cans.",
                                "is_correct": False,
                                "feedback": "Aerosol cans are expensive and short-lived; source reduction is sustainable and effective.",
                            },
                        ],
                        "incorrect_behaviour": "retry",
                    },
                },
                {
                    "card_id": "camp-card-10",
                    "position": 10,
                    "card_type": "recap",
                    "content_blocks": [
                        {"block_type": "heading", "body": "Summary & Practical Action"},
                        {
                            "block_type": "key_takeaway",
                            "body": "Protecting the 100-Meter Shield: Individual efforts multiply when entire streets and apartment complexes coordinate weekly container cleanups.",
                        },
                        {
                            "block_type": "key_takeaway",
                            "body": "Partner with Public Health: Work alongside ASHA workers and municipal sanitary inspectors to report and treat large unmanaged breeding sites.",
                        },
                        {
                            "block_type": "callout",
                            "body": "Real-World Action: Talk to two of your neighbors today about observing a weekly Sunday 'Dry Day' together, and take a quick 5-minute walk down your lane to spot any waterlogged scrap containers!",
                        },
                    ],
                    "source_ids": ["src-vector-control-measu-4319", "src-do-s-and-don-ts-1543"],
                    "interaction": None,
                },
            ],
        },
    ]

    return lessons, versions
