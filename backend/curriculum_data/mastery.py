"""Capstone Topic Mastery Challenges for HealthAware.

Includes 4 comprehensive 10-question mastery challenges:
1. Personal Hygiene & Infection Control Master (topic-hygiene)
2. Safe Water & Community Sanitation Master (topic-water)
3. Vector Control & Dengue Prevention Master (topic-mosquito)
4. Immunization Science & Community Advocacy Master (topic-vaccine)
"""

from __future__ import annotations


def get_mastery_challenges() -> list[dict]:
    return [
        # Topic 1: Personal Hygiene Mastery Challenge
        {
            "topic_id": "topic-hygiene",
            "title": "Personal Hygiene & Infection Control Capstone",
            "description": "Test your mastery of pathogen transmission, 20-second hand hygiene mechanics, respiratory infection control, oral biofilm management, and shared environmental sanitization across complex real-world scenarios.",
            "passing_score": 8,
            "badge_title": "Hygiene & Infection Control Master",
            "badge_icon": "🧼",
            "questions": [
                {
                    "id": "mc-hyg-1",
                    "question_prompt": "Scenario: After caring for a family member with acute vomiting, your hands are contaminated with bodily fluids. The sink has soap and running water, and there is also a bottle of 70% alcohol hand rub on the table. Which should you choose and why?",
                    "hint": "Think about when alcohol sanitizer is ineffective compared to mechanical soap washing.",
                    "explanation": "When hands are visibly soiled or contaminated with proteinaceous body fluids or norovirus, soap and running water are mandatory because alcohol sanitizers cannot penetrate organic bioburden and are less effective against non-enveloped enteric viruses.",
                    "options": [
                        {"id": "o1-a", "label": "Wash thoroughly with soap and running water for at least 20 seconds.", "is_correct": True, "feedback": "Correct! Soap and water physically remove organic fluids and enteric viruses that resist alcohol."},
                        {"id": "o1-b", "label": "Use only the alcohol hand rub because alcohol evaporates faster.", "is_correct": False, "feedback": "Alcohol is inactivated by heavy organic matter and misses norovirus."},
                        {"id": "o1-c", "label": "Wipe hands on your apron and put on winter gloves.", "is_correct": False, "feedback": "Wiping on clothes spreads contamination to textiles."},
                    ],
                },
                {
                    "id": "mc-hyg-2",
                    "question_prompt": "Scenario: You are in a crowded metro train with no tissues when you feel a sudden cough coming on. How should you shield your cough?",
                    "hint": "Consider which body surface rarely touches grab poles or other people.",
                    "explanation": "Coughing into the inner crook of your flexed elbow seals droplets while keeping your palms free from viral contamination.",
                    "options": [
                        {"id": "o2-a", "label": "Cough into the inner crook of your flexed elbow, sealing your mouth and nose.", "is_correct": True, "feedback": "Correct! The elbow crook prevents palms and fingers from contaminating shared poles and handles."},
                        {"id": "o2-b", "label": "Cough into both bare hands and then hold the handrail firmly.", "is_correct": False, "feedback": "Directly transfers respiratory droplets onto high-touch poles."},
                        {"id": "o2-c", "label": "Cough straight ahead into the open air without covering.", "is_correct": False, "feedback": "Expels droplets 1-2 meters into passengers' breathing zones."},
                    ],
                },
                {
                    "id": "mc-hyg-3",
                    "question_prompt": "Scenario: A restaurant employee washes their hands for only 5 seconds under cold tap water without soap. What is the microbiological outcome?",
                    "hint": "Does water alone dissolve the oily sebum layer that binds microbes to skin?",
                    "explanation": "Water alone cannot dissolve the lipophilic sebum layer that holds microbes to skin crevices. Without soap lather and friction time, over 90% of transient microbes remain viable.",
                    "options": [
                        {"id": "o3-a", "label": "Virtually all surface oils, bacteria, and viruses remain attached to the skin.", "is_correct": True, "feedback": "Exact science! Without surfactants, water flows over oil without lifting pathogens."},
                        {"id": "o3-b", "label": "The hands are 100% sterile because cold water freezes bacteria.", "is_correct": False, "feedback": "Tap water is never cold enough to freeze bacteria."},
                        {"id": "o3-c", "label": "All viruses die instantly from optical light reflection.", "is_correct": False, "feedback": "Light reflection does not kill microbes in tap water."},
                    ],
                },
                {
                    "id": "mc-hyg-4",
                    "question_prompt": "Scenario: A resident is cleaning a shared society kitchen after someone spilled raw chicken juices. They want to apply chlorine bleach. What must they do first?",
                    "hint": "What happens if bleach is poured directly onto raw organic grease and meat juices?",
                    "explanation": "Organic matter like meat grease and blood consumes chlorine, rendering disinfection ineffective. Surfaces must be washed clean with detergent and water first, then disinfected.",
                    "options": [
                        {"id": "o4-a", "label": "Wash the counter clean with soap/detergent and water first to remove organic grease, then apply disinfectant.", "is_correct": True, "feedback": "Correct! Clean first to eliminate the bioburden, then disinfect."},
                        {"id": "o4-b", "label": "Pour concentrated bleach directly on the meat juices and wipe dry immediately.", "is_correct": False, "feedback": "Bleach is deactivated by organic juices and produces fumes."},
                        {"id": "o4-c", "label": "Mix bleach with vinegar and hot oil to form a paste.", "is_correct": False, "feedback": "Mixing bleach with acid produces lethal chlorine gas."},
                    ],
                },
                {
                    "id": "mc-hyg-5",
                    "question_prompt": "Scenario: A college student brushes their teeth by scrubbing horizontally with hard bristles for 30 seconds and then rinses thoroughly with 3 cups of water. What two mistakes are they making?",
                    "hint": "Think about brushing technique/time and the fate of protective fluoride.",
                    "explanation": "Horizontal hard scrubbing abrades enamel and recedes gums (soft circular strokes for 2 minutes are recommended), and immediate water rinsing washes away protective fluoride before it can remineralize enamel.",
                    "options": [
                        {"id": "o5-a", "label": "Brushing too aggressively for too short a time, and washing away protective fluoride by rinsing with water immediately.", "is_correct": True, "feedback": "Spot on! Gentle 2-minute brushing and spit-don't-rinse preserve enamel and fluoride."},
                        {"id": "o5-b", "label": "Brushing with toothpaste instead of raw salt.", "is_correct": False, "feedback": "Raw salt is overly abrasive and lacks protective fluoride."},
                        {"id": "o5-c", "label": "Brushing in the morning instead of at 2:00 PM.", "is_correct": False, "feedback": "Twice daily (morning and before bed) is standard."},
                    ],
                },
                {
                    "id": "mc-hyg-6",
                    "question_prompt": "Scenario: In a shared office building, which surface requires the highest frequency of routine environmental cleaning during an influenza outbreak?",
                    "hint": "Identify the ultimate high-touch fomite handled by dozens of people daily.",
                    "explanation": "Elevator buttons and door handles are classic high-touch fomites handled by multiple unwashed hands within short intervals.",
                    "options": [
                        {"id": "o6-a", "label": "Elevator call buttons and main entrance door handles.", "is_correct": True, "feedback": "Correct! High-touch fomites transfer pathogens rapidly across different departments."},
                        {"id": "o6-b", "label": "The decorative ceiling tiles in the auditorium.", "is_correct": False, "feedback": "Ceiling tiles are rarely touched by human hands."},
                        {"id": "o6-c", "label": "The parking lot asphalt surface.", "is_correct": False, "feedback": "Outdoor asphalt has minimal direct hand-to-mucosa transmission risk."},
                    ],
                },
                {
                    "id": "mc-hyg-7",
                    "question_prompt": "Scenario: How does drying your hands thoroughly with a clean towel complete the protective cycle of handwashing?",
                    "hint": "What is the physical difference between wet skin and dry skin during subsequent touches?",
                    "explanation": "Moisture creates surface capillary tension that allows microorganisms to adhere and transfer up to 1,000 times more readily from skin to surfaces.",
                    "options": [
                        {"id": "o7-a", "label": "Damp hands transfer bacteria up to 1,000 times more readily than dry hands; drying prevents microbial re-adhesion.", "is_correct": True, "feedback": "Scientifically verified! Thorough drying is an essential step of proper hand hygiene."},
                        {"id": "o7-b", "label": "Towel friction generates electricity that vaporizes all viruses.", "is_correct": False, "feedback": "Towels absorb moisture; they do not generate vaporizing electrical currents."},
                        {"id": "o7-c", "label": "Drying is only for personal fashion and has zero hygiene benefit.", "is_correct": False, "feedback": "Drying is a proven microbiological infection control milestone."},
                    ],
                },
                {
                    "id": "mc-hyg-8",
                    "question_prompt": "Scenario: What dangerous chemical mistake must never be made when preparing household chlorine disinfectant solutions?",
                    "hint": "What hazardous reaction occurs when bleach is mixed with acidic or ammonia products?",
                    "explanation": "Mixing bleach with acids (vinegar, toilet acids) releases toxic chlorine gas; mixing with ammonia releases poisonous chloramines, causing severe acute lung damage.",
                    "options": [
                        {"id": "o8-a", "label": "Mixing bleach with vinegar, ammonia, or acidic toilet cleaners, which releases lethal chlorine or chloramine gas.", "is_correct": True, "feedback": "Critical chemical safety knowledge! Never mix bleach with other chemical cleaners."},
                        {"id": "o8-b", "label": "Diluting bleach with cool clean tap water.", "is_correct": False, "feedback": "Diluting with cool water is the correct and safe method."},
                        {"id": "o8-c", "label": "Wearing household rubber gloves during preparation.", "is_correct": False, "feedback": "Wearing gloves is a recommended protective measure."},
                    ],
                },
                {
                    "id": "mc-hyg-9",
                    "question_prompt": "Scenario: How can households prevent fungal skin infections (tinea cruris / ringworm) in humid monsoon weather?",
                    "hint": "What environmental condition is required for fungal spores to germinate on skin?",
                    "explanation": "Dermatophyte fungi require moisture and darkness. Daily washing, thorough drying of skin folds, and wearing loose, breathable cotton garments eliminate fungal breeding micro-climates.",
                    "options": [
                        {"id": "o9-a", "label": "Keep skin folds thoroughly dry after bathing, wear breathable cotton clothes, and avoid sharing towels.", "is_correct": True, "feedback": "Correct! Moisture control is the definitive defense against fungal dermatophytes."},
                        {"id": "o9-b", "label": "Apply thick unwashed synthetic tight pants over wet skin.", "is_correct": False, "feedback": "Trapping moisture accelerates fungal skin infection."},
                        {"id": "o9-c", "label": "Avoid bathing for the entire three months of monsoon.", "is_correct": False, "feedback": "Poor hygiene allows fungi and bacteria to proliferate rapidly."},
                    ],
                },
                {
                    "id": "mc-hyg-10",
                    "question_prompt": "Scenario: What is the proven effect of opening opposite windows (cross-ventilation) in a crowded study room during respiratory illness season?",
                    "hint": "What does continuous air exchange do to suspended indoor aerosol concentrations?",
                    "explanation": "Natural cross-ventilation continuously replaces stagnant indoor air with fresh outdoor air, diluting airborne viral aerosol concentrations by over 80%.",
                    "options": [
                        {"id": "o10-a", "label": "It flushes out stagnant bioaerosols and dilutes infectious airborne particle concentrations by over 80%.", "is_correct": True, "feedback": "Exact public health mechanism! Cross-ventilation is a primary engineering defense against airborne transmission."},
                        {"id": "o10-b", "label": "It makes indoor bacteria heavier so they sink into carpet fibers forever.", "is_correct": False, "feedback": "Air exchange flushes aerosols out rather than making them heavier."},
                        {"id": "o10-c", "label": "It has zero effect on indoor air quality compared to burning incense.", "is_correct": False, "feedback": "Burning incense adds harmful particulate matter; ventilation clears it."},
                    ],
                },
            ],
        },

        # Topic 2: Safe Drinking Water Mastery Challenge
        {
            "topic_id": "topic-water",
            "title": "Safe Water & Community Sanitation Capstone",
            "description": "Demonstrate comprehensive expertise in waterborne disease epidemiology, household purification standards, secondary contamination prevention, and community outbreak management.",
            "passing_score": 8,
            "badge_title": "Water Safety & Sanitation Master",
            "badge_icon": "💧",
            "questions": [
                {
                    "id": "mc-wat-1",
                    "question_prompt": "Scenario: A rural well yields crystal clear, odorless, sweet-tasting water located 8 meters downhill from an unlined pit latrine. Is this water safe to drink without treatment?",
                    "hint": "Can human senses detect microscopic E. coli or Hepatitis A?",
                    "explanation": "Clear, sweet-tasting water can carry millions of invisible pathogenic bacteria and viruses that seep through soil from a nearby pit latrine. Water must be treated before consumption.",
                    "options": [
                        {"id": "w1-a", "label": "No. Invisible fecal pathogens seep through soil into shallow aquifers without altering taste, odor, or clarity.", "is_correct": True, "feedback": "Correct! Taste and optical clarity are never proof of microbiological potability."},
                        {"id": "w1-b", "label": "Yes. If water is sweet and clear, all bacteria are automatically filtered out.", "is_correct": False, "feedback": "Dangerous misconception! Enteric pathogens are microscopic and odorless."},
                        {"id": "w1-c", "label": "Yes, but only if consumed during daytime hours.", "is_correct": False, "feedback": "Bacterial pathogens remain infectious 24 hours a day."},
                    ],
                },
                {
                    "id": "mc-wat-2",
                    "question_prompt": "Scenario: During a monsoon flood, tap water comes out brown and muddy. You have chlorine disinfection tablets. What must you do before adding the tablet?",
                    "hint": "What do mud particles do to chemical chlorine disinfectants?",
                    "explanation": "Turbid, muddy water contains organic particles that chemically consume chlorine and physically shield microbes from disinfection. Water must be settled or filtered through a clean cloth first.",
                    "options": [
                        {"id": "w2-a", "label": "Pre-filter the water through a clean folded cotton cloth or let mud settle, then dose with chlorine.", "is_correct": True, "feedback": "Correct! Removing turbidity ensures chlorine can effectively destroy pathogens."},
                        {"id": "w2-b", "label": "Add ten times the recommended chlorine dose directly to the thick mud and drink immediately.", "is_correct": False, "feedback": "Excessive chlorine dosage can cause chemical toxicity, and turbidity shields microbes."},
                        {"id": "w2-c", "label": "Boil the water with kerosene fuel.", "is_correct": False, "feedback": "Kerosene is a fuel for the burner, not an additive for water."},
                    ],
                },
                {
                    "id": "mc-wat-3",
                    "question_prompt": "Scenario: How long must water be maintained at a continuous rolling boil to reliably inactivate biological pathogens including Cryptosporidium cysts?",
                    "hint": "Think about the WHO and CDC benchmark duration.",
                    "explanation": "A vigorous rolling boil for at least 1 full minute (or 3 minutes at elevations above 2,000 meters / ~6,500 feet) reliably inactivates common waterborne pathogens, including bacteria, viruses, and heat-resistant protozoan cysts. Note that boiling does not remove chemical contaminants or heavy metals.",
                    "options": [
                        {"id": "w3-a", "label": "At least 1 full minute of vigorous rolling boil (3 minutes at elevations above 2,000 m).", "is_correct": True, "feedback": "Exact public health standard! Maintaining a rolling boil for 1 minute (3 minutes at high altitude) provides reliable biological pathogen inactivation."},
                        {"id": "w3-b", "label": "Just until the first tiny bubble appears on the pot bottom (around 60°C).", "is_correct": False, "feedback": "Sub-boiling temperatures leave hardy protozoan cysts viable."},
                        {"id": "w3-c", "label": "At least 4 continuous hours.", "is_correct": False, "feedback": "Hours of boiling wastes fuel and concentrates dissolved solids without added microbiological safety."},
                    ],
                },
                {
                    "id": "mc-wat-4",
                    "question_prompt": "Scenario: A family boils water every morning and pours it into an open wide-mouth brass vessel on the floor. Throughout the day, children dip handleless tumblers into it. What is the risk?",
                    "hint": "What is secondary contamination?",
                    "explanation": "Dipping tumblers with bare fingers touching water introduces skin and fecal bacteria into previously sterile water, causing secondary contamination.",
                    "options": [
                        {"id": "w4-a", "label": "Secondary contamination: unwashed fingers submerge in water and re-inoculate pathogens into the boiled supply.", "is_correct": True, "feedback": "Spot on! Up to 40-50% of boiled water is re-contaminated by hand dipping."},
                        {"id": "w4-b", "label": "The brass metal will turn the water into pure fruit juice.", "is_correct": False, "feedback": "Metals do not convert water to fruit juice."},
                        {"id": "w4-c", "label": "Zero risk, because boiled water is permanently immune to all bacteria for 100 years.", "is_correct": False, "feedback": "Boiled water has zero residual protection against newly introduced bacteria."},
                    ],
                },
                {
                    "id": "mc-wat-5",
                    "question_prompt": "Scenario: A 3-year-old child develops sudden acute watery diarrhea with vomiting. What is the immediate first-line household intervention to prevent life-threatening shock?",
                    "hint": "What is the role of Oral Rehydration Salts (ORS)?",
                    "explanation": "Immediate administration of WHO-formula Oral Rehydration Salts (ORS) solution replenishes fluid and essential electrolytes through intestinal sodium-glucose transport, preventing fatal dehydration.",
                    "options": [
                        {"id": "w5-a", "label": "Administer Oral Rehydration Salts (ORS) solution continuously after every loose stool, along with clean fluids.", "is_correct": True, "feedback": "Life-saving clinical intervention! ORS prevents dehydration and shock."},
                        {"id": "w5-b", "label": "Withhold all water and fluids completely for 24 hours.", "is_correct": False, "feedback": "Fluid restriction causes rapid hypovolemic shock and death in pediatric diarrhea."},
                        {"id": "w5-c", "label": "Give large doses of adult sleeping pills to stop stomach movement.", "is_correct": False, "feedback": "Sedatives are dangerous and do not treat dehydration."},
                    ],
                },
                {
                    "id": "mc-wat-6",
                    "question_prompt": "Scenario: Under what specific water quality condition is a high-wastage Reverse Osmosis (RO) filtration unit genuinely indicated for domestic drinking water?",
                    "hint": "Does RO target biological bacteria or dissolved mineral solutes (TDS)?",
                    "explanation": "RO is indicated when Total Dissolved Solids (TDS) exceed 500 mg/L or when toxic chemical ions like arsenic, fluoride, or heavy metals are present. It is not needed for low-TDS water.",
                    "options": [
                        {"id": "w6-a", "label": "When water contains high Total Dissolved Solids (TDS > 500 mg/L) or toxic dissolved chemicals like arsenic or fluoride.", "is_correct": True, "feedback": "Correct! RO demineralizes water; using it on low-TDS water wastes 3-4 liters per liter purified without added health benefit."},
                        {"id": "w6-b", "label": "Whenever drinking municipal tap water that already has a low TDS of 150 mg/L.", "is_correct": False, "feedback": "Low-TDS water does not require demineralization by RO."},
                        {"id": "w6-c", "label": "Only when water is collected from a mountain snow glacier.", "is_correct": False, "feedback": "Glacial snow water has minimal dissolved minerals."},
                    ],
                },
                {
                    "id": "mc-wat-7",
                    "question_prompt": "Scenario: How does intermittent water supply (turning water pumps on for 2 hours and off for 22 hours) cause pipeline contamination?",
                    "hint": "What pressure forms inside pipes when water flow is shut off?",
                    "explanation": "When water flow stops, falling water creates negative hydraulic suction pressure (vacuum). If pipes have cracked joints passing through sewage drains, wastewater is sucked directly inside.",
                    "options": [
                        {"id": "w7-a", "label": "Negative pressure (vacuum) develops in empty pipes, sucking nearby drain water inward through pipe cracks.", "is_correct": True, "feedback": "Exact public health engineering mechanism! Back-siphonage pollutes municipal lines."},
                        {"id": "w7-b", "label": "Pipes shrink in size and squeeze water molecules into bacteria.", "is_correct": False, "feedback": "Pipes do not convert water molecules into bacteria."},
                        {"id": "w7-c", "label": "Mosquitoes crawl inside the closed metal taps to lay eggs.", "is_correct": False, "feedback": "Back-siphonage of external sewage through leaky joints is the primary cause."},
                    ],
                },
                {
                    "id": "mc-wat-8",
                    "question_prompt": "Scenario: How should traditional unglazed earthen clay water pots (matkas) be cleaned and sanitized?",
                    "hint": "Why should chemical dish soaps be avoided on porous clay?",
                    "explanation": "Porous clay absorbs chemical detergents, which leach into future drinking water. Scrub with clean boiling water and a brush, then sun-dry in direct solar UV light.",
                    "options": [
                        {"id": "w8-a", "label": "Empty completely, scrub with clean hot water and a brush (no soap), and dry thoroughly in direct sunlight.", "is_correct": True, "feedback": "Correct! Boiling water and solar UV rays sanitize clay pores without chemical contamination."},
                        {"id": "w8-b", "label": "Soak the interior in perfumed dishwashing gel and bleach overnight.", "is_correct": False, "feedback": "Porous terracotta absorbs detergent, imparting bad taste and toxic chemicals to drinking water."},
                        {"id": "w8-c", "label": "Never empty the pot; continuously add new water over years.", "is_correct": False, "feedback": "Never topping up without cleaning prevents thick biofilm accumulation."},
                    ],
                },
                {
                    "id": "mc-wat-9",
                    "question_prompt": "Scenario: What is the target level of Free Residual Chlorine (FRC) that must be maintained at the consumer's tap in safe piped distribution networks?",
                    "hint": "Recall the WHO and Indian Public Health Standard range.",
                    "explanation": "A Free Residual Chlorine concentration of 0.2 to 0.5 mg/L at the tap provides an active protective shield against pathogens while remaining completely safe and pleasant to drink.",
                    "options": [
                        {"id": "w9-a", "label": "0.2 to 0.5 mg/L (ppm).", "is_correct": True, "feedback": "Exact benchmark! 0.2 to 0.5 mg/L guards against secondary contamination in distribution pipes."},
                        {"id": "w9-b", "label": "0.0 mg/L with zero residual disinfectant.", "is_correct": False, "feedback": "Zero residual leaves water defenseless against pipe leaks."},
                        {"id": "w9-c", "label": "50 mg/L.", "is_correct": False, "feedback": "50 mg/L is far too high for human drinking water."},
                    ],
                },
                {
                    "id": "mc-wat-10",
                    "question_prompt": "Scenario: Under India's Jal Jeevan Mission, what community role is trained to test local drinking water using Field Test Kits (FTKs)?",
                    "hint": "Who in the village is empowered for localized water surveillance?",
                    "explanation": "Jal Jeevan Mission specifically trains five women from every village (including ASHA and Anganwadi workers) to use Field Test Kits for localized monitoring of chemical and bacteriological water safety.",
                    "options": [
                        {"id": "w10-a", "label": "Five women from every village, including ASHA workers, Anganwadi staff, and community members.", "is_correct": True, "feedback": "Correct! Community-led monitoring empowers trained village women with testing kits."},
                        {"id": "w10-b", "label": "Only visiting international chemical scientists.", "is_correct": False, "feedback": "JJM focuses on decentralized, local grassroots community testing."},
                        {"id": "w10-c", "label": "Private soft drink delivery drivers.", "is_correct": False, "feedback": "Public health surveillance is conducted by trained village women and health workers."},
                    ],
                },
            ],
        },

        # Topic 3: Mosquito Prevention Mastery Challenge
        {
            "topic_id": "topic-mosquito",
            "title": "Vector Control & Dengue Prevention Capstone",
            "description": "Demonstrate mastery over vector biology, container management, clinical triage of Dengue warning signs, emergency medication contraindications, and community mobilization.",
            "passing_score": 8,
            "badge_title": "Vector Control & Dengue Master",
            "badge_icon": "🦟",
            "questions": [
                {
                    "id": "mc-mos-1",
                    "question_prompt": "Scenario: A resident has high fever (103°F), retro-orbital eye pain, and joint aches during peak Dengue season. Which over-the-counter medicine must they avoid?",
                    "hint": "Which class of fever and pain medicines impairs platelets and increases bleeding risk in dengue?",
                    "explanation": "Aspirin, ibuprofen, and other non-steroidal anti-inflammatory drugs (NSAIDs) inhibit platelet function and irritate gastric mucosa, increasing bleeding risk in suspected dengue. Paracetamol is generally used for fever and pain under appropriate guidance, and clinical warning signs require prompt medical evaluation.",
                    "options": [
                        {"id": "m1-a", "label": "Aspirin, Ibuprofen, Naproxen, or Diclofenac (NSAIDs).", "is_correct": True, "feedback": "Correct! NSAIDs inhibit platelet function and increase bleeding risk in suspected dengue."},
                        {"id": "m1-b", "label": "Paracetamol taken at standard weight-appropriate dosages under appropriate guidance.", "is_correct": False, "feedback": "Paracetamol is generally recommended for fever and pain in suspected dengue; NSAIDs must be avoided."},
                        {"id": "m1-c", "label": "Oral rehydration fluids and coconut water.", "is_correct": False, "feedback": "Oral hydration is safe and strongly recommended in Dengue."},
                    ],
                },
                {
                    "id": "mc-mos-2",
                    "question_prompt": "Scenario: Where does the Aedes aegypti mosquito (the primary vector of Dengue and Chikungunya) lay its eggs?",
                    "hint": "Does Aedes prefer clean domestic containers or dirty sewer canals?",
                    "explanation": "Aedes aegypti lays eggs in artificial, clean, stagnant domestic water containers—potted plant trays, cooler basins, discarded tyres, and fresh rainwater collections.",
                    "options": [
                        {"id": "m2-a", "label": "Clean, stagnant water in domestic containers: desert coolers, plant saucers, tyres, and uncovered pots.", "is_correct": True, "feedback": "Exact entomological truth! Aedes breeds in clean domestic containers, not dirty sewer drains."},
                        {"id": "m2-b", "label": "Exclusively in heavily polluted, dirty black sewer water.", "is_correct": False, "feedback": "Dirty sewage breeds Culex mosquitoes, not the Dengue vector."},
                        {"id": "m2-c", "label": "Fast-flowing mountain river rapids.", "is_correct": False, "feedback": "Aedes cannot breed in fast-flowing water."},
                    ],
                },
                {
                    "id": "mc-mos-3",
                    "question_prompt": "Scenario: Why is simply tipping water out of an old desert cooler or tyre without scrubbing the walls insufficient to stop Dengue breeding?",
                    "hint": "How do Aedes eggs survive dry periods?",
                    "explanation": "Aedes eggs are glued to container walls and possess a desiccation-resistant shell that survives dry for 6-12 months. When refilled, they hatch immediately unless mechanically scrubbed off.",
                    "options": [
                        {"id": "m3-a", "label": "Aedes eggs adhere tightly to container walls and survive completely dry for months, hatching when refilled.", "is_correct": True, "feedback": "Scientifically verified! Physical scrubbing is required to dislodge dry viable eggs."},
                        {"id": "m3-b", "label": "Mosquito larvae can dig underground and wait in soil.", "is_correct": False, "feedback": "Mosquito larvae are strictly aquatic and cannot live in soil."},
                        {"id": "m3-c", "label": "The plastic bucket spontaneously turns into mosquito eggs.", "is_correct": False, "feedback": "Insects only hatch from pre-existing biological eggs."},
                    ],
                },
                {
                    "id": "mc-mos-4",
                    "question_prompt": "Scenario: A Dengue patient's high fever suddenly drops back to normal on day 4 of illness. Why must the family remain extra vigilant over the next 48 hours?",
                    "hint": "What is the 'Critical Phase' in Dengue fever?",
                    "explanation": "The 'Critical Phase' occurs when the fever breaks. Increased capillary permeability causes plasma leakage, which can trigger severe Dengue shock, low blood pressure, and organ failure.",
                    "options": [
                        {"id": "m4-a", "label": "Fever defervescence marks the onset of the Critical Phase, when plasma leakage and shock can suddenly develop.", "is_correct": True, "feedback": "Critical clinical insight! The drop in fever is when Dengue shock is most likely to occur."},
                        {"id": "m4-b", "label": "Because when fever drops, the patient's eyes turn into ice cubes.", "is_correct": False, "feedback": "Eyes do not turn to ice; plasma leakage is the true medical emergency."},
                        {"id": "m4-c", "label": "Dropping fever means the patient is 100% cured and can run a marathon immediately.", "is_correct": False, "feedback": "Assuming cure during defervescence leads to delayed recognition of shock."},
                    ],
                },
                {
                    "id": "mc-mos-5",
                    "question_prompt": "Scenario: What visual resting posture distinguishes an adult Anopheles mosquito (the malaria vector) from other mosquito species?",
                    "hint": "What angle does Anopheles hold relative to the resting surface?",
                    "explanation": "Anopheles rests with its proboscis, head, and abdomen in a straight line tilted at a 45-degree angle to the wall, whereas Aedes and Culex rest parallel to the surface.",
                    "options": [
                        {"id": "m5-a", "label": "It rests with its body tilted outward at a distinct 45-degree angle to the wall.", "is_correct": True, "feedback": "Correct! The 45-degree angled stance is characteristic of Anopheles."},
                        {"id": "m5-b", "label": "It rests flat against the wall like a coin.", "is_correct": False, "feedback": "Culex and Aedes rest parallel, not Anopheles."},
                        {"id": "m5-c", "label": "It only hangs upside down by one single toe.", "is_correct": False, "feedback": "Anopheles tilts its abdomen outward at 45 degrees."},
                    ],
                },
                {
                    "id": "mc-mos-6",
                    "question_prompt": "Scenario: Why is burning indoor green mosquito coils discouraged as a primary protective strategy for infants and asthmatics?",
                    "hint": "What does burning coil smoke do to developing lungs?",
                    "explanation": "Mosquito coils emit heavy PM2.5 particulate matter and toxic volatile organic compounds (equivalent to smoking dozens of cigarettes), triggering pediatric asthma and respiratory trauma.",
                    "options": [
                        {"id": "m6-a", "label": "Coil smoke releases high levels of PM2.5 particulate matter and toxic chemicals, irritating delicate infant lungs.", "is_correct": True, "feedback": "Exact public health reason! Physical bed netting and window mesh are far safer non-toxic alternatives."},
                        {"id": "m6-b", "label": "Mosquito coils attract more mosquitoes into the room.", "is_correct": False, "feedback": "Coils repel somewhat, but the severe respiratory damage outweighs the benefit."},
                        {"id": "m6-c", "label": "Coils freeze room air into solid ice.", "is_correct": False, "feedback": "Coils burn and produce hot smoke."},
                    ],
                },
                {
                    "id": "mc-mos-7",
                    "question_prompt": "Scenario: What is the biological vector control mechanism of introducing Gambusia affinis fish into large ornamental ponds and construction water sumps?",
                    "hint": "What do these small fish feed on?",
                    "explanation": "Gambusia affinis (mosquitofish) feed voraciously on aquatic mosquito larvae and pupae, consuming hundreds daily and halting adult emergence naturally without chemicals.",
                    "options": [
                        {"id": "m7-a", "label": "Gambusia fish actively prey on and consume aquatic mosquito larvae and pupae in large water bodies.", "is_correct": True, "feedback": "Correct! Biological control using larvivorous fish suppresses mosquito populations naturally."},
                        {"id": "m7-b", "label": "The fish sing underwater songs that scare adult flying mosquitoes.", "is_correct": False, "feedback": "Fish feed on aquatic larvae, not sound effects."},
                        {"id": "m7-c", "label": "The fish secrete chlorine bleach from their scales.", "is_correct": False, "feedback": "Fish consume larvae as dietary prey."},
                    ],
                },
                {
                    "id": "mc-mos-8",
                    "question_prompt": "Scenario: When applying both sunscreen and DEET insect repellent for morning outdoor activities, what is the correct application sequence?",
                    "hint": "Which product needs direct skin absorption, and which must vaporize on the outer layer?",
                    "explanation": "Apply sunscreen first, allow it to absorb for 15-20 minutes, and apply insect repellent on top so it can vaporize outward and deter biting insects.",
                    "options": [
                        {"id": "m8-a", "label": "Apply sunscreen first, let it absorb, and then apply insect repellent on top of the sunscreen layer.", "is_correct": True, "feedback": "Correct! Repellents must form the outermost vaporizing layer to repel mosquitoes."},
                        {"id": "m8-b", "label": "Apply repellent first and immediately cover it with thick greasy sunscreen.", "is_correct": False, "feedback": "Covering repellent blocks its evaporation and impairs efficacy."},
                        {"id": "m8-c", "label": "Mix both in a cooking pot and boil before applying.", "is_correct": False, "feedback": "Never boil personal care chemicals."},
                    ],
                },
                {
                    "id": "mc-mos-9",
                    "question_prompt": "Scenario: Why is community-wide source reduction necessary instead of just cleaning your own private home?",
                    "hint": "What is the typical flight range of the female Aedes mosquito?",
                    "explanation": "Aedes mosquitoes have a flight radius of 50 to 100 meters. Unmanaged breeding sites in a neighbor's yard, an alley tyre, or a nearby plot fly directly across walls into surrounding homes.",
                    "options": [
                        {"id": "m9-a", "label": "Aedes mosquitoes fly 50 to 100 meters, meaning larvae in nearby unmanaged plots will bite residents across the street.", "is_correct": True, "feedback": "Exact public health reality! Vector control requires a coordinated 100-meter community shield."},
                        {"id": "m9-b", "label": "Mosquitoes only bite people who have completely clean homes.", "is_correct": False, "feedback": "Mosquitoes bite anyone within their flight range."},
                        {"id": "m9-c", "label": "Because individual homes do not have air.", "is_correct": False, "feedback": "Vector flight radius connects entire neighborhoods."},
                    ],
                },
                {
                    "id": "mc-mos-10",
                    "question_prompt": "Scenario: What is the primary limitation of outdoor thermal fogging (insecticide smoke) in urban vector control?",
                    "hint": "Does fogging kill larvae and eggs in water?",
                    "explanation": "Fogging only kills adult mosquitoes flying at that exact moment; it does not penetrate water containers where larvae and eggs remain, allowing new adults to emerge days later.",
                    "options": [
                        {"id": "m10-a", "label": "Fogging only knocks down flying adult mosquitoes; it has zero effect on eggs and larvae in water.", "is_correct": True, "feedback": "Spot on! Fogging is an emergency supplement; source reduction is the only permanent solution."},
                        {"id": "m10-b", "label": "Fogging makes mosquitoes immune to all water forever.", "is_correct": False, "feedback": "Fogging does not confer immunity to water."},
                        {"id": "m10-c", "label": "Fogging permanently changes the weather to winter.", "is_correct": False, "feedback": "Fogging does not alter planetary climate."},
                    ],
                },
            ],
        },

        # Topic 4: Vaccine Awareness Mastery Challenge
        {
            "topic_id": "topic-vaccine",
            "title": "Immunization Science & Community Advocacy Capstone",
            "description": "Master immunology concepts, the National Immunization Schedule, reactogenicity vs true adverse events (AEFI), empathetic communication for hesitancy, and lifelong vaccination records.",
            "passing_score": 8,
            "badge_title": "Immunization Science Master",
            "badge_icon": "🛡️",
            "questions": [
                {
                    "id": "mc-vax-1",
                    "question_prompt": "Scenario: A 10-week-old baby was scheduled for their second Pentavalent and Rotavirus vaccines, but the family missed the appointment by 6 weeks. What is the correct medical catch-up protocol?",
                    "hint": "Does the human immune memory forget previous doses?",
                    "explanation": "Immunological memory persists; you never restart a delayed series from dose 1. Administer the delayed dose immediately and schedule the next dose at the standard interval.",
                    "options": [
                        {"id": "v1-a", "label": "Administer the delayed dose immediately and continue the schedule; never restart the series from dose 1.", "is_correct": True, "feedback": "Correct! Immunological memory is cumulative; missed doses are simply resumed."},
                        {"id": "v1-b", "label": "Restart the entire schedule from the birth doses because previous doses expired.", "is_correct": False, "feedback": "Previous vaccine doses are never wasted and memory cells do not expire."},
                        {"id": "v1-c", "label": "Cancel all future vaccines because the schedule was breached.", "is_correct": False, "feedback": "Catch-up vaccination is universally encouraged at all ages."},
                    ],
                },
                {
                    "id": "mc-vax-2",
                    "question_prompt": "Scenario: What is the scientific consensus regarding the claim that the MMR (Measles-Mumps-Rubella) vaccine causes autism?",
                    "hint": "What happened to the 1998 Andrew Wakefield paper in the Lancet?",
                    "explanation": "The 1998 claim was based on a fraudulent study by Andrew Wakefield involving 12 children that was fully retracted by the Lancet. Hundreds of independent global studies involving millions of children have proven zero link.",
                    "options": [
                        {"id": "v2-a", "label": "Thoroughly disproven: the 1998 study was retracted for proven scientific fraud, and studies of millions of children confirm zero link.", "is_correct": True, "feedback": "Exact scientific consensus! Vaccines do not cause autism."},
                        {"id": "v2-b", "label": "Proven true by every scientific academy in the world.", "is_correct": False, "feedback": "Completely false; the claim was based on proven medical fraud."},
                        {"id": "v2-c", "label": "Autism only occurs if vaccines are given during a full moon.", "is_correct": False, "feedback": "Moon phases have zero clinical relationship with neurodevelopment."},
                    ],
                },
                {
                    "id": "mc-vax-3",
                    "question_prompt": "Scenario: Why is an infant's developing immune system capable of handling multiple combination vaccines (like Pentavalent) safely?",
                    "hint": "How many antigens does a baby encounter daily through breathing, nursing, and touching?",
                    "explanation": "Infants encounter thousands of environmental antigens daily through food and breathing. Modern combination vaccines contain purified proteins representing only a tiny fraction of their immune capacity.",
                    "options": [
                        {"id": "v3-a", "label": "Infants possess immense immune capacity that encounters thousands of antigens daily; combination vaccines use only a minuscule fraction.", "is_correct": True, "feedback": "Exact immunology! Vaccines do not 'overload' the human immune system."},
                        {"id": "v3-b", "label": "Because infants have no white blood cells until age 5.", "is_correct": False, "feedback": "Infants are born with functional white blood cells that respond to antigens."},
                        {"id": "v3-c", "label": "Vaccines do not contain antigens.", "is_correct": False, "feedback": "Antigens are the active components that stimulate targeted antibody production."},
                    ],
                },
                {
                    "id": "mc-vax-4",
                    "question_prompt": "Scenario: Six hours after receiving her 6-week immunization, a baby develops a measured fever of 38°C (100.4°F) and injection-site tenderness. What is the proper response?",
                    "hint": "In an infant under 3 months, should a fever of 38°C be evaluated promptly by a healthcare professional?",
                    "explanation": "In young infants under 3 months of age (such as a 6-week-old), a measured temperature of 38°C (100.4°F) requires prompt assessment by a healthcare professional (doctor, paediatrician, or health worker). Caregivers should never assume fever is purely post-vaccination or wait 48 hours without clinical advice. While awaiting assessment, keep the baby comfortable with light clothing and frequent feeds; do not administer medications without professional guidance. Distinguish this from emergency red flags (breathing difficulty, facial or throat swelling, seizures, or unresponsiveness), which require immediate emergency hospital care.",
                    "options": [
                        {"id": "v4-a", "label": "Promptly contact or visit a healthcare professional for clinical assessment, while keeping the infant comfortable with frequent feeds and light clothing.", "is_correct": True, "feedback": "Correct! In infants under 3 months (such as a 6-week-old), a temperature of 38°C warrants prompt medical evaluation rather than assuming it is only vaccine-related. Red flags like breathing difficulty or seizures require immediate emergency care."},
                        {"id": "v4-b", "label": "Massage the tender injection site with warm mustard oil or herbal pastes to reduce swelling.", "is_correct": False, "feedback": "Applying oils, balms, or pastes and massaging the injection site can irritate delicate infant skin and increase the risk of infection. Never rub or apply unprescribed substances to the site."},
                        {"id": "v4-c", "label": "Bundle the baby in heavy blankets to sweat out the fever and wait 48 hours before contacting a doctor.", "is_correct": False, "feedback": "Over-bundling an infant can cause dangerous overheating. In an infant under 3 months with a 38°C fever, caregivers should not wait 48 hours or assume fever is benign; prompt medical assessment is essential."},
                    ],
                },
                {
                    "id": "mc-vax-5",
                    "question_prompt": "Scenario: Why is it standard public health practice for patients to wait at the clinic for 30 minutes following vaccination?",
                    "hint": "What is the timeline for managing rare acute allergic anaphylaxis?",
                    "explanation": "Severe allergic reactions (anaphylaxis) are extraordinarily rare (1-2 per million), but occur almost immediately. Waiting 30 minutes ensures clinic staff can administer life-saving epinephrine if needed.",
                    "options": [
                        {"id": "v5-a", "label": "To ensure that in the extraordinarily rare event of acute allergic anaphylaxis, clinic staff can administer epinephrine immediately.", "is_correct": True, "feedback": "Exact public health rationale! Immediate clinic treatment completely reverses anaphylaxis."},
                        {"id": "v5-b", "label": "To wait for the vaccine liquid to dry inside the skin.", "is_correct": False, "feedback": "Injected liquids absorb into muscle tissue immediately."},
                        {"id": "v5-c", "label": "Because clinic doors are legally locked for 30 minutes.", "is_correct": False, "feedback": "The wait is strictly for patient clinical safety observation."},
                    ],
                },
                {
                    "id": "mc-vax-6",
                    "question_prompt": "Scenario: What is the primary purpose of India's U-WIN digital immunization registry platform?",
                    "hint": "How does digital tracking help mothers and children across state lines?",
                    "explanation": "U-WIN creates a unified digital immunization record linked to ABHA, enabling tracking of due dates, issuing verifiable certificates, and preventing missed doses anywhere in the country.",
                    "options": [
                        {"id": "v6-a", "label": "Maintaining an authenticated digital registry of every child and pregnant woman to track due vaccines and enable portable records across India.", "is_correct": True, "feedback": "Correct! U-WIN provides portable digital vaccination tracking across all states."},
                        {"id": "v6-b", "label": "Selling personal medical data to commercial advertisers.", "is_correct": False, "feedback": "U-WIN is a secure government public health platform."},
                        {"id": "v6-c", "label": "Playing video games during doctor appointments.", "is_correct": False, "feedback": "U-WIN is an electronic immunization tracking registry."},
                    ],
                },
                {
                    "id": "mc-vax-7",
                    "question_prompt": "Scenario: Why is natural infection with wild pathogens (such as measles or polio) NOT a safer alternative to vaccination?",
                    "hint": "What are the tragic complications of wild diseases?",
                    "explanation": "Wild infections cause severe disability and death: polio causes permanent paralysis, measles causes brain damage and pneumonia, and tetanus causes fatal spasms. Vaccines deliver immunity safely without disease.",
                    "options": [
                        {"id": "v7-a", "label": "Wild infections carry devastating risks of permanent paralysis, encephalitis, pneumonia, and death, whereas vaccines build immunity safely.", "is_correct": True, "feedback": "Vital clinical truth! Vaccines provide the benefit of immune memory without the lethal risks of wild disease."},
                        {"id": "v7-b", "label": "Wild infections do not generate any antibodies whatsoever.", "is_correct": False, "feedback": "Wild infections generate antibodies, but at the cost of severe organ damage and death."},
                        {"id": "v7-c", "label": "Wild pathogens turn people into stone statues.", "is_correct": False, "feedback": "Pathogens cause clinical illness, not petrification."},
                    ],
                },
                {
                    "id": "mc-vax-8",
                    "question_prompt": "Scenario: What cancer-preventing vaccine is recommended for adolescent girls (aged 9-14) under national and global guidelines?",
                    "hint": "What vaccine prevents cervical cancer?",
                    "explanation": "The Human Papillomavirus (HPV) vaccine prevents persistent infection with high-risk oncogenic HPV types, preventing over 90% of cervical cancers.",
                    "options": [
                        {"id": "v8-a", "label": "Human Papillomavirus (HPV) vaccine.", "is_correct": True, "feedback": "Correct! The HPV vaccine is a proven cancer prevention milestone."},
                        {"id": "v8-b", "label": "Oral Polio Drops every week.", "is_correct": False, "feedback": "Polio drops prevent poliomyelitis, not cervical cancer."},
                        {"id": "v8-c", "label": "Rabies vaccine on every birthday.", "is_correct": False, "feedback": "Rabies vaccine is given post-exposure after animal bites."},
                    ],
                },
                {
                    "id": "mc-vax-9",
                    "question_prompt": "Scenario: When a relative expresses anxiety about vaccine safety based on internet forwards, which communication strategy is most effective?",
                    "hint": "Does aggressive argument or empathetic listening build trust?",
                    "explanation": "Listening with empathy, validating their concern for family safety, explaining verified evidence respectfully without condescension, and offering to consult a trusted clinician build trust.",
                    "options": [
                        {"id": "v9-a", "label": "Listen respectfully, validate their protective intention, share verified scientific evidence calmly, and connect them with a trusted doctor.", "is_correct": True, "feedback": "Exact public health communication science! Empathetic dialogue resolves vaccine hesitancy."},
                        {"id": "v9-b", "label": "Insult their intelligence in front of neighbors.", "is_correct": False, "feedback": "Insults entrench distrust and drive people toward misinformation."},
                        {"id": "v9-c", "label": "Agree that all vaccines are dangerous to avoid awkwardness.", "is_correct": False, "feedback": "Reinforcing false rumors leaves children vulnerable to preventable disease."},
                    ],
                },
                {
                    "id": "mc-vax-10",
                    "question_prompt": "Scenario: How frequently should healthy adults receive a Td (Tetanus and adult Diphtheria) booster vaccination?",
                    "hint": "How long does circulating tetanus antitoxin persist before waning?",
                    "explanation": "Tetanus antitoxin antibodies wane over time; a booster dose of Td is recommended once every 10 years throughout adulthood, as well as following contaminated wound injuries.",
                    "options": [
                        {"id": "v10-a", "label": "Once every 10 years throughout adulthood.", "is_correct": True, "feedback": "Correct! Decennial Td boosters maintain lifelong protective antitoxin titers."},
                        {"id": "v10-b", "label": "Every Monday morning.", "is_correct": False, "feedback": "Weekly boosters are completely unnecessary."},
                        {"id": "v10-c", "label": "Only once at age 100.", "is_correct": False, "feedback": "Waiting until age 100 leaves adults unprotected during working years."},
                    ],
                },
            ],
        },
    ]
