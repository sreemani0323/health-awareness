"""Seed realistic, evidence-based public health data into local Datastore emulator.

Creates 4 rich topics, lessons, cards (explanation, single-choice quiz, recap),
and official health sources (WHO, CDC).
"""

from __future__ import annotations

import os
import sys
from datetime import date

# Ensure repo root is on sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from google.cloud import ndb

from backend.domain.domain_objects import (
    AnswerOption,
    CardType,
    ContentBlock,
    HealthSource,
    IncorrectBehaviour,
    InteractionType,
    Lesson,
    LessonCard,
    LessonVersion,
    PublicationStatus,
    SingleChoiceInteraction,
    Topic,
    User,
    UserRole,
    VersionStatus,
)
from backend.domain.domain_services import (
    create_health_source,
    create_lesson,
    create_lesson_version,
    create_topic,
    create_user,
    get_topic,
    publish_lesson_version,
)
from backend.platform.ndb_client import get_ndb_client


def seed_database():
    client = get_ndb_client()

    with client.context():
        print("[*] Seeding database...")

        # 1. Sources
        sources = [
            HealthSource(
                source_id="src-who-hygiene",
                title="WHO Guidelines on Hand Hygiene in Community Settings",
                publisher="World Health Organization & UNICEF",
                url="https://www.who.int/publications/i/item/9789240116559",
                publication_date=date(2025, 10, 15),
                access_date=date(2026, 10, 12),
                jurisdiction="Global",
            ),
            HealthSource(
                source_id="src-cdc-hygiene",
                title="CDC When and How to Wash Your Hands: Official Handwashing Guidance",
                publisher="Centers for Disease Control and Prevention",
                url="https://www.cdc.gov/clean-hands/about/index.html",
                publication_date=date(2024, 5, 14),
                access_date=date(2026, 10, 12),
                jurisdiction="Global / United States",
            ),
            HealthSource(
                source_id="src-who-water-guidelines",
                title="WHO Guidelines for Drinking-water Quality (Fourth Edition Incorporating Addenda)",
                publisher="World Health Organization",
                url="https://www.who.int/publications/i/item/9789240121225",
                publication_date=date(2022, 3, 21),
                access_date=date(2026, 10, 12),
                jurisdiction="Global",
            ),
            HealthSource(
                source_id="src-who-water-factsheet",
                title="WHO Drinking-water Fact Sheet: Health Risks and Interventions",
                publisher="World Health Organization",
                url="https://www.who.int/news-room/fact-sheets/detail/drinking-water",
                publication_date=date(2023, 9, 13),
                access_date=date(2026, 10, 12),
                jurisdiction="Global",
            ),
            HealthSource(
                source_id="src-who-hwts",
                title="WHO Household Water Treatment and Safe Storage Guidance",
                publisher="World Health Organization",
                url="https://iris.who.int/handle/10665/206916",
                publication_date=date(2010, 1, 1),
                access_date=date(2026, 10, 12),
                jurisdiction="Global",
            ),
            HealthSource(
                source_id="src-jjm-water-tech",
                title="Jal Jeevan Mission: Handbook on Drinking Water Treatment Technologies",
                publisher="Ministry of Jal Shakti, Government of India",
                url="https://jaljeevanmission.gov.in/sites/default/files/handbook-on-drinking-water-treatment-technologies-2023.pdf",
                publication_date=date(2023, 1, 1),
                access_date=date(2026, 10, 12),
                jurisdiction="India / National",
            ),
            HealthSource(
                source_id="src-cdc-water",
                title="CDC Healthy Water: Drinking Water Treatment and Purification",
                publisher="Centers for Disease Control and Prevention",
                url="https://www.cdc.gov/healthywater/drinking",
                publication_date=date(2023, 10, 1),
                access_date=date(2026, 10, 12),
                jurisdiction="Global",
            ),
            HealthSource(
                source_id="src-cdc-mosquito",
                title="CDC Mosquito Control: Prevent Mosquito Bites and Breeding",
                publisher="Centers for Disease Control and Prevention",
                url="https://www.cdc.gov/mosquitoes/prevention",
                publication_date=date(2024, 2, 15),
                access_date=date(2025, 3, 1),
                jurisdiction="Global",
            ),
            HealthSource(
                source_id="src-who-vaccines",
                title="WHO Vaccines and Immunization: How Do Vaccines Work?",
                publisher="World Health Organization",
                url="https://www.who.int/news-room/questions-and-answers/item/vaccines-and-immunization-what-is-vaccination",
                publication_date=date(2023, 11, 20),
                access_date=date(2025, 3, 1),
                jurisdiction="Global",
            ),
        ]

        for s in sources:
            try:
                create_health_source(s)
                print(f"  + Added source: {s.title}")
            except Exception as e:
                print(f"  ~ Source already exists or skipped: {e}")

        # 2. Topics & Lessons
        topics_data = [
            {
                "topic": Topic(
                    topic_id="topic-hygiene",
                    title="Personal Hygiene & Handwashing",
                    url_slug="hygiene",
                    description="Essential techniques for infection prevention through proper handwashing and personal hygiene.",
                    display_order=1,
                    status=PublicationStatus.PUBLISHED,
                ),
                "lesson": Lesson(
                    lesson_id="lesson-handwashing",
                    topic_id="topic-hygiene",
                    display_order=1,
                ),
                "version": LessonVersion(
                    version_id="ver-handwashing-1",
                    lesson_id="lesson-handwashing",
                    version_number=1,
                    title="Effective Handwashing Techniques",
                    summary="Learn the science-backed 20-second handwashing method to remove pathogens.",
                    language="en",
                    learning_objectives=[
                        "Master the 5-step handwashing technique with soap and running water, scrubbing for at least 20 seconds",
                        "Identify the 5 critical everyday moments for hand hygiene in household and community settings",
                        "Understand how soap, friction, and rinsing remove germs, and when alcohol-based rub is an acceptable alternative",
                    ],
                    estimated_duration_minutes=5,
                    source_ids=["src-who-hygiene", "src-cdc-hygiene"],
                    status=VersionStatus.DRAFT,
                    cards=[
                        LessonCard(
                            card_id="hw-card-1",
                            position=1,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Why Handwashing Saves Lives",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Handwashing with soap and clean running water is one of the most effective and affordable ways to prevent diarrheal illnesses and acute respiratory infections. Germs spread quickly when unwashed hands touch the face, food, or surfaces that others share.",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="How soap works: Soap does not instantly kill all germs on contact. Instead, soap molecules combine with the physical friction of scrubbing and rinsing to loosen, lift, and wash away dirt, grease, and infectious microbes from your skin. For certain viruses with an outer lipid layer (such as influenza and coronaviruses), soap also disrupts that protective fatty envelope to help inactivate them. For other bacteria and non-enveloped germs, the mechanical action of lathering and rinsing safely removes them from hands.",
                                ),
                            ],
                            source_ids=["src-who-hygiene", "src-cdc-hygiene"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="hw-card-2",
                            position=2,
                            card_type=CardType.INTERACTION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Knowledge Check: Scrub Duration",
                                ),
                            ],
                            source_ids=["src-cdc-hygiene", "src-who-hygiene"],
                            interaction=SingleChoiceInteraction(
                                interaction_type=InteractionType.SINGLE_CHOICE,
                                question_prompt="According to WHO and CDC guidelines, how long should you scrub your hands with soap?",
                                incorrect_behaviour=IncorrectBehaviour.RETRY,
                                options=[
                                    AnswerOption(
                                        option_id="opt-hw-1",
                                        label="5 to 10 seconds",
                                        is_correct=False,
                                        feedback="Too brief! Quick scrubbing does not provide enough friction time for soap lather to lift and loosen microbes, dirt, and grease from skin folds, finger webs, and under fingernails.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-hw-2",
                                        label="At least 20 seconds",
                                        is_correct=True,
                                        feedback="Spot on! The CDC and WHO recommend scrubbing with soap for at least 20 seconds (the time it takes to hum 'Happy Birthday' twice). This provides enough physical friction to lift germs from palms, backs of hands, between fingers, and under nails before rinsing.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-hw-3",
                                        label="1 minute with scalding hot water",
                                        is_correct=False,
                                        feedback="Scalding water does not remove more germs and can damage your skin barrier, causing dryness and irritation. Clean running water (warm or cold) with 20 seconds of soap scrubbing is effective and safe.",
                                    ),
                                ],
                            ),
                        ),
                        LessonCard(
                            card_id="hw-card-3",
                            position=3,
                            card_type=CardType.RECAP,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Key Takeaways: 5 Steps & Everyday Moments",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="The 5 Steps of Handwashing (CDC): 1. Wet hands with clean running water (warm or cold). 2. Lather thoroughly with soap. 3. Scrub for at least 20 seconds, including backs of hands, between fingers, and under nails. 4. Rinse completely under running water. 5. Dry with a clean towel or air dry.",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="5 Key Everyday Community Moments (WHO): Wash before preparing food, before eating or feeding others, after using the toilet or handling feces (including changing diapers), after coughing or sneezing, and whenever hands are visibly soiled. Note: These community moments apply to everyday life and are distinct from the clinical '5 Moments' framework used in hospital healthcare settings.",
                                ),
                            ],
                            source_ids=["src-who-hygiene", "src-cdc-hygiene"],
                            interaction=None,
                        ),
                    ],
                ),
            },
            {
                "topic": Topic(
                    topic_id="topic-water",
                    title="Safe Drinking Water & Sanitation",
                    url_slug="water",
                    description="Practical household water treatment, safe storage principles, and sanitation barriers to protect health.",
                    display_order=2,
                    status=PublicationStatus.PUBLISHED,
                ),
                "lesson": Lesson(
                    lesson_id="lesson-water-purification",
                    topic_id="topic-water",
                    display_order=1,
                ),
                "version": LessonVersion(
                    version_id="ver-water-1",
                    lesson_id="lesson-water-purification",
                    version_number=1,
                    title="Household Water Treatment and Safe Storage",
                    summary="Learn practical methods to treat drinking water, prevent recontamination during storage, and protect community water sources through sanitation.",
                    language="en",
                    learning_objectives=[
                        "Understand why drinking water can become contaminated across collection, transport, treatment, and storage",
                        "Distinguish between microbial hazards and chemical hazards and recognize why treatment methods must match the risk",
                        "Evaluate common household treatment options (boiling, filtration, disinfection) and understand their specific limitations",
                        "Apply practical safe-water collection, covered storage, and hygienic handling principles to prevent recontamination",
                        "Explain how community sanitation facilities and personal hygiene barriers protect shared drinking-water sources",
                    ],
                    estimated_duration_minutes=7,
                    source_ids=[
                        "src-who-water-guidelines",
                        "src-who-water-factsheet",
                        "src-who-hwts",
                        "src-jjm-water-tech",
                        "src-cdc-water",
                    ],
                    status=VersionStatus.DRAFT,
                    cards=[
                        LessonCard(
                            card_id="water-card-1",
                            position=1,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Understanding Drinking Water Safety and Contamination",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Safe drinking water is essential for health, yet contamination can occur at any stage: at the source, during transport, during handling, or within household storage.\n\nWater that looks clear, smells fresh, and tastes normal is not guaranteed to be safe. Microscopic disease-causing pathogens—including bacteria (such as Vibrio cholerae and pathogenic E. coli), viruses, and protozoan parasites—cannot be seen with the naked eye. Contaminated drinking water contributes significantly to acute waterborne illnesses, especially diarrheal disease in children and vulnerable community members.\n\nCrucially, microbial hazards and chemical hazards are different. Microbial pathogens are living organisms that cause immediate infections, while chemical contaminants (such as naturally occurring arsenic, excess fluoride, or industrial runoff) cause chronic toxic effects over time and require fundamentally different treatment solutions.",
                                ),
                            ],
                            source_ids=["src-who-water-guidelines", "src-who-water-factsheet"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="water-card-2",
                            position=2,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Household Water Treatment: Choosing the Right Method",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Household water treatment (HWT) can improve water quality, but households must match the treatment method to the specific contamination risk.\n\n• Boiling: Bringing water to a rolling boil for 1 full minute is highly effective for inactivating disease-causing bacteria, viruses, and protozoa according to WHO guidelines. However, boiling does NOT destroy or remove dissolved chemical contaminants like arsenic, fluoride, or heavy metals. In fact, prolonged boiling evaporates water and actually concentrates dissolved chemical toxins.\n\n• Filtration: Physical filters vary widely by technology. Verified ceramic and membrane filters can physically trap bacteria and parasites, whereas simple cloth straining only removes suspended dirt and insects—not bacteria, viruses, or dissolved chemicals.\n\n• Disinfection: Disinfection products (such as approved chlorine tablets or liquid solutions) destroy most bacteria and viruses in clear water, but are less effective in cloudy water and do not remove dissolved chemicals or certain resistant protozoa.\n\nAlways follow local public-health advice and product instructions. When chemical contamination is suspected, households should seek water-quality testing and guidance from the responsible water-supply authority or qualified testing service rather than assuming home treatment makes all water safe.",
                                ),
                            ],
                            source_ids=["src-who-water-guidelines", "src-who-hwts", "src-jjm-water-tech"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="water-card-3",
                            position=3,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Safe Collection, Storage, and Handling",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Even thoroughly treated drinking water can quickly become contaminated again if it is handled or stored without care. Practical household practices help maintain water safety from the tap to the cup.\n\n• Dedicated Storage Container: Store treated drinking water in a clean, dedicated container made of food-grade material.\n\n• Keep Covered: Always keep the storage vessel tightly covered to shield water from dust, flies, airborne particles, and domestic animals.\n\n• Narrow Neck or Dispensing Tap: Containers with a narrow neck or a built-in tap are strongly recommended. These designs prevent hands, unwashed cups, ladles, or foreign objects from entering the stored water.\n\n• Hygienic Dispensing: If a container has a wide opening, use a dedicated, clean ladle with a long handle rather than dipping cups or hands into the water.\n\n• Routine Cleaning: Regularly clean storage containers with clean water and appropriate disinfectant. Keep the container elevated off the ground in a clean, shaded area.",
                                ),
                            ],
                            source_ids=["src-who-hwts", "src-who-water-guidelines"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="water-card-4",
                            position=4,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Sanitation and Protecting Community Water Sources",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Safe sanitation is the first and most critical protective barrier for drinking-water safety. Unsafe disposal of human excreta, overflowing open drains, and leaking sewage allow disease-causing pathogens to wash into surface streams or leach deep into groundwater aquifers.\n\n• Use and Maintain Toilets: Defecation in the open exposes community soil and runoff to heavy pathogen loads. Using and properly maintaining sanitary latrines contains human waste safely.\n\n• Protect Water Points: Ensure that toilets, soak pits, and animal pens are constructed downhill and at a safe distance from wells, hand pumps, and delivery pipes.\n\n• Hand Hygiene: Always wash hands thoroughly with soap and water after using the toilet and before preparing food, collecting water, or serving drinks.\n\n• Community Action: Avoid washing clothes, bathing cattle, or dumping garbage near drinking-water wells, ponds, or standposts. Report damaged water pipes, broken handpumps, or sewage leaks promptly to local authorities.",
                                ),
                            ],
                            source_ids=["src-who-water-factsheet", "src-jjm-water-tech"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="water-card-5",
                            position=5,
                            card_type=CardType.INTERACTION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Knowledge Check: Water Treatment Limits",
                                ),
                            ],
                            source_ids=["src-who-water-guidelines", "src-jjm-water-tech"],
                            interaction=SingleChoiceInteraction(
                                interaction_type=InteractionType.SINGLE_CHOICE,
                                question_prompt="Why can boiling alone NOT be relied upon to make water safe if it contains dissolved chemical contaminants like arsenic or fluoride?",
                                incorrect_behaviour=IncorrectBehaviour.RETRY,
                                options=[
                                    AnswerOption(
                                        option_id="opt-wt-q1-1",
                                        label="Boiling inactivates microbial pathogens, but does not remove dissolved chemicals and actually concentrates them as water evaporates",
                                        is_correct=True,
                                        feedback="Correct! Boiling heat destroys living microorganisms (bacteria, viruses, parasites), but dissolved minerals like arsenic and fluoride do not evaporate with steam. Prolonged boiling reduces water volume and increases the concentration of chemical toxins. Chemical contamination requires verified specialized treatment or an alternative safe water source.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-wt-q1-2",
                                        label="Boiling only removes dissolved chemical toxins if the water is boiled for more than 45 minutes continuously",
                                        is_correct=False,
                                        feedback="Incorrect. Boiling longer does not eliminate dissolved chemicals—it evaporates more water, which actually concentrates the chemical contaminants further and wastes fuel.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-wt-q1-3",
                                        label="Boiling works for chemicals only if a pinch of salt or lemon juice is added to the pot",
                                        is_correct=False,
                                        feedback="Incorrect. Household kitchen additives do not neutralize dissolved mineral contaminants like arsenic or fluoride. When chemical contamination is suspected, seek guidance and testing from local water-supply authorities.",
                                    ),
                                ],
                            ),
                        ),
                        LessonCard(
                            card_id="water-card-6",
                            position=6,
                            card_type=CardType.INTERACTION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Knowledge Check: Safe Storage and Handling",
                                ),
                            ],
                            source_ids=["src-who-hwts", "src-who-water-guidelines"],
                            interaction=SingleChoiceInteraction(
                                interaction_type=InteractionType.SINGLE_CHOICE,
                                question_prompt="Which household storage practice best protects treated drinking water from becoming recontaminated?",
                                incorrect_behaviour=IncorrectBehaviour.RETRY,
                                options=[
                                    AnswerOption(
                                        option_id="opt-wt-q2-1",
                                        label="Storing water in an open bucket so natural sunlight can reach and disinfect the water surface all day",
                                        is_correct=False,
                                        feedback="Incorrect. Leaving drinking water uncovered in an open bucket allows dust, insects, hands, and airborne germs to rapidly recontaminate treated water.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-wt-q2-2",
                                        label="Keeping water in a clean, covered container with a narrow neck or dispensing tap to prevent hands and dirty cups from touching it",
                                        is_correct=True,
                                        feedback="Correct! Keeping water covered in a narrow-neck or tap-dispensing container prevents direct contact. Dipping unwashed fingers, ladles, or dirty cups into open storage is a leading cause of recontamination in homes.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-wt-q2-3",
                                        label="Allowing family members to dip shared drinking cups into the container as long as cups are rinsed with cold water first",
                                        is_correct=False,
                                        feedback="Incorrect. Dipping cups or fingers into the storage container introduces bacteria and germs from hands and lips directly into the entire stored water supply.",
                                    ),
                                ],
                            ),
                        ),
                        LessonCard(
                            card_id="water-card-7",
                            position=7,
                            card_type=CardType.INTERACTION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Knowledge Check: Community Sanitation Barriers",
                                ),
                            ],
                            source_ids=["src-who-water-factsheet", "src-jjm-water-tech"],
                            interaction=SingleChoiceInteraction(
                                interaction_type=InteractionType.SINGLE_CHOICE,
                                question_prompt="How does safe community sanitation directly protect drinking-water supplies from contamination?",
                                incorrect_behaviour=IncorrectBehaviour.RETRY,
                                options=[
                                    AnswerOption(
                                        option_id="opt-wt-q3-1",
                                        label="By safely containing human waste and sewage away from groundwater aquifers and surface water sources",
                                        is_correct=True,
                                        feedback="Correct! Safely containing human waste in proper latrines and keeping sewage away from water sources acts as the primary barrier, stopping fecal pathogens before they can enter groundwater or runoff into drinking supplies.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-wt-q3-2",
                                        label="By naturally neutralizing dissolved mineral chemicals before rain enters the soil",
                                        is_correct=False,
                                        feedback="Incorrect. Sanitation manages human waste and wastewater to prevent microbiological disease transmission; it does not remove naturally occurring minerals from soil or rain.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-wt-q3-3",
                                        label="Sanitation only keeps surroundings looking clean and has no direct connection to drinking water safety",
                                        is_correct=False,
                                        feedback="Incorrect. Inadequate sanitation and open waste disposal are major causes of microbial contamination in drinking water sources worldwide.",
                                    ),
                                ],
                            ),
                        ),
                        LessonCard(
                            card_id="water-card-8",
                            position=8,
                            card_type=CardType.RECAP,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Core Takeaways: Safe Drinking Water & Sanitation",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="By following evidence-based drinking-water and sanitation practices, households and communities can effectively prevent waterborne illness:\n\n1. Water Appearance Can Be Deceiving: Clear, odorless water can still carry invisible microorganisms or harmful dissolved chemicals. Do not rely on visual inspection alone.\n\n2. Match Treatment to the Contaminant: A 1-minute rolling boil inactivates microbial pathogens, but does NOT remove dissolved chemical hazards like arsenic or fluoride. Where chemical risks exist, seek official testing and advice from water-supply authorities.\n\n3. Safeguard Treated Water: Store drinking water in clean, covered containers with a narrow neck or tap. Never dip hands, unwashed cups, or utensils into stored drinking water.\n\n4. Strengthen Sanitation Barriers: Using sanitary latrines, containing sewage away from water points, washing hands with soap, and reporting water-system damage protect entire communities from waterborne disease outbreaks.",
                                ),
                            ],
                            source_ids=[
                                "src-who-water-guidelines",
                                "src-who-water-factsheet",
                                "src-who-hwts",
                                "src-jjm-water-tech",
                            ],
                            interaction=None,
                        ),
                    ],
                ),
            },
            {
                "topic": Topic(
                    topic_id="topic-mosquito",
                    title="Mosquito Prevention & Vector Control",
                    url_slug="mosquito",
                    description="Eliminate stagnant water breeding habitats, apply personal barriers, and reduce vector-borne disease risks.",
                    display_order=3,
                    status=PublicationStatus.PUBLISHED,
                ),
                "lesson": Lesson(
                    lesson_id="lesson-mosquito-control",
                    topic_id="topic-mosquito",
                    display_order=1,
                ),
                "version": LessonVersion(
                    version_id="ver-mosquito-1",
                    lesson_id="lesson-mosquito-control",
                    version_number=1,
                    title="Stopping Mosquito Breeding at Home",
                    summary="Simple weekly routines to disrupt mosquito breeding cycles in household environments.",
                    language="en",
                    learning_objectives=[
                        "Recognize common household standing water traps",
                        "Understand mosquito larval development cycles",
                        "Adopt the weekly 'Tip and Toss' routine",
                    ],
                    estimated_duration_minutes=4,
                    source_ids=["src-cdc-mosquito"],
                    status=VersionStatus.DRAFT,
                    cards=[
                        LessonCard(
                            card_id="mos-card-1",
                            position=1,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="The Mosquito Life Cycle",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Mosquitoes responsible for transmitting Dengue, Malaria, and Zika lay eggs on the surface of standing water. It takes only 7 to 10 days for an egg to develop into a biting adult.",
                                ),
                            ],
                            source_ids=["src-cdc-mosquito"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="mos-card-2",
                            position=2,
                            card_type=CardType.INTERACTION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Knowledge Check: Breeding Prevention",
                                ),
                            ],
                            source_ids=["src-cdc-mosquito"],
                            interaction=SingleChoiceInteraction(
                                interaction_type=InteractionType.SINGLE_CHOICE,
                                question_prompt="How often should you empty and scrub outdoor containers holding standing water?",
                                incorrect_behaviour=IncorrectBehaviour.RETRY,
                                options=[
                                    AnswerOption(
                                        option_id="opt-m-1",
                                        label="Once a month",
                                        is_correct=False,
                                        feedback="Too late! Larvae will have already emerged as adult mosquitoes within 7-10 days.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-m-2",
                                        label="At least once a week",
                                        is_correct=True,
                                        feedback="Excellent! Emptying containers weekly interrupts the larval life cycle before mosquitoes can emerge.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-m-3",
                                        label="Only during heavy rain season",
                                        is_correct=False,
                                        feedback="Mosquitoes can breed year-round in artificial containers, plant saucers, and air conditioner runoff.",
                                    ),
                                ],
                            ),
                        ),
                        LessonCard(
                            card_id="mos-card-3",
                            position=3,
                            card_type=CardType.RECAP,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Tip, Toss, and Cover",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Check flower pots, pet bowls, old tires, and coolers weekly. Turn empty containers upside down, cover rain barrels with mesh screens, and use repellents or bed nets in endemic areas.",
                                ),
                            ],
                            source_ids=["src-cdc-mosquito"],
                            interaction=None,
                        ),
                    ],
                ),
            },
            {
                "topic": Topic(
                    topic_id="topic-vaccine",
                    title="Vaccine Awareness & Immunity",
                    url_slug="vaccine",
                    description="Learn how vaccines prime the human immune system, preserve community immunity, and save millions of lives.",
                    display_order=4,
                    status=PublicationStatus.PUBLISHED,
                ),
                "lesson": Lesson(
                    lesson_id="lesson-vaccine-basics",
                    topic_id="topic-vaccine",
                    display_order=1,
                ),
                "version": LessonVersion(
                    version_id="ver-vaccine-1",
                    lesson_id="lesson-vaccine-basics",
                    version_number=1,
                    title="How Vaccines Build Immunity",
                    summary="Discover the biological mechanisms of immunization and why community immunity matters.",
                    language="en",
                    learning_objectives=[
                        "Understand memory B and T cell activation",
                        "Explain herd/community immunity in simple terms",
                        "Distinguish between vaccination and active infection risks",
                    ],
                    estimated_duration_minutes=5,
                    source_ids=["src-who-vaccines"],
                    status=VersionStatus.DRAFT,
                    cards=[
                        LessonCard(
                            card_id="vac-card-1",
                            position=1,
                            card_type=CardType.EXPLANATION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Training Your Immune Defenses",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Vaccines introduce a weakened or harmless fragment of an antigen to teach your immune cells how to fight it. When your body encounters the real pathogen later, antibodies recognize and eliminate it rapidly.",
                                ),
                            ],
                            source_ids=["src-who-vaccines"],
                            interaction=None,
                        ),
                        LessonCard(
                            card_id="vac-card-2",
                            position=2,
                            card_type=CardType.INTERACTION,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Knowledge Check: Community Immunity",
                                ),
                            ],
                            source_ids=["src-who-vaccines"],
                            interaction=SingleChoiceInteraction(
                                interaction_type=InteractionType.SINGLE_CHOICE,
                                question_prompt="What is 'Community Immunity' (also known as Herd Immunity)?",
                                incorrect_behaviour=IncorrectBehaviour.RETRY,
                                options=[
                                    AnswerOption(
                                        option_id="opt-v-1",
                                        label="When healthy individuals avoid going outside to prevent infection",
                                        is_correct=False,
                                        feedback="That is physical isolation, not community immunity.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-v-2",
                                        label="When a high percentage of a population is immune, protecting vulnerable individuals who cannot be vaccinated",
                                        is_correct=True,
                                        feedback="Correct! High vaccination rates shield newborns, immunocompromised patients, and elders who cannot receive certain vaccines.",
                                    ),
                                    AnswerOption(
                                        option_id="opt-v-3",
                                        label="Immunity acquired exclusively through contracting severe illnesses",
                                        is_correct=False,
                                        feedback="Natural infection carries high risks of permanent disability and death; vaccines provide immunity safely.",
                                    ),
                                ],
                            ),
                        ),
                        LessonCard(
                            card_id="vac-card-3",
                            position=3,
                            card_type=CardType.RECAP,
                            content_blocks=[
                                ContentBlock(
                                    block_type="heading",
                                    body="Staying Protected",
                                ),
                                ContentBlock(
                                    block_type="text",
                                    body="Vaccines prevent over 3.5 to 5 million deaths each year globally from diseases like measles, tetanus, and influenza. Keep your routine immunizations up to date according to your local health authority.",
                                ),
                            ],
                            source_ids=["src-who-vaccines"],
                            interaction=None,
                        ),
                    ],
                ),
            },
        ]

        for item in topics_data:
            t = item["topic"]
            l = item["lesson"]
            v = item["version"]

            try:
                create_topic(t)
                print(f"  + Added Topic: {t.title}")
            except Exception as e:
                print(f"  ~ Topic {t.topic_id} already exists or skipped: {e}")

            try:
                create_lesson(l)
                print(f"    + Added Lesson: {l.lesson_id}")
            except Exception as e:
                print(f"    ~ Lesson {l.lesson_id} already exists or skipped: {e}")

            try:
                if not v.author_id:
                    v.author_id = "user-contributor"
                create_lesson_version(v)
                print(f"      + Added Version: {v.version_id}")
                publish_lesson_version(v.version_id)
                print(f"      [OK] Published Version: {v.version_id}")
            except Exception as e:
                print(f"      ~ Version {v.version_id} already exists or skipped: {e}")

        print("[SUCCESS] Database successfully seeded!")

        # --- Seed Creator Studio users ---
        # Demo accounts are restricted strictly to explicitly enabled local development/testing.
        # They must NEVER be silently provisioned into a production environment.
        env_mode = os.environ.get("FLASK_ENV", "").lower()
        app_env = os.environ.get("APP_ENV", "").lower()
        is_prod = (
            env_mode == "production"
            or app_env == "production"
            or bool(os.environ.get("GAE_APPLICATION"))
            or bool(os.environ.get("GAE_ENV"))
            or bool(os.environ.get("RENDER"))
        )
        # Never enable demo accounts in production
        enable_demo = False if is_prod else (os.environ.get("ENABLE_DEMO_ACCOUNTS", "false").lower() in ("true", "1"))

        if enable_demo:
            from backend.platform.security import hash_password

            default_users = [
                User(
                    user_id="user-contributor",
                    username="contributor",
                    display_name="Health Contributor",
                    role=UserRole.CONTRIBUTOR,
                    password_hash=hash_password("contributor123"),
                ),
                User(
                    user_id="user-reviewer",
                    username="reviewer",
                    display_name="Health Reviewer",
                    role=UserRole.REVIEWER,
                    password_hash=hash_password("reviewer123"),
                ),
                User(
                    user_id="user-admin",
                    username="admin",
                    display_name="Administrator",
                    role=UserRole.ADMIN,
                    password_hash=hash_password("admin123"),
                ),
            ]

            print("\n[*] Seeding Creator Studio demo users (local development only)...")
            for u in default_users:
                try:
                    create_user(u)
                    print(f"    + Added User: {u.username} ({u.role.value})")
                except Exception as e:
                    print(f"    ~ User {u.username} already exists or skipped: {e}")

            print("[SUCCESS] Creator Studio demo users seeded!")
        else:
            print("\n[*] Demo accounts are disabled in this environment. Skipping user seeding.")


if __name__ == "__main__":
    seed_database()

