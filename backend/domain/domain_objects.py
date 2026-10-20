"""Domain objects for the Health Awareness application.

All domain objects are plain Python dataclasses.  They must NOT import Flask,
google.cloud.ndb, or any infrastructure-specific module.

Each domain object carries its own validation via a ``validate()`` method that
raises ``ValueError`` on constraint violations.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import re
from datetime import date, datetime
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}[a-z0-9]$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_URL_RE = re.compile(r"^https?://\S+$")

MAX_TITLE_LEN = 200
MAX_DESCRIPTION_LEN = 1000
MAX_SUMMARY_LEN = 2000
MAX_CARDS = 100
MAX_OPTIONS = 10
MAX_FEEDBACK_LEN = 2000
MAX_OBJECTIVES = 20
MAX_SOURCES_PER_VERSION = 50
SUPPORTED_LANGUAGES = frozenset({"en", "hi", "es", "fr", "pt", "ar", "sw"})


def _validate_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise ValueError(
            f"{label} must be 3-64 lowercase alphanumeric characters, "
            f"hyphens, or underscores, starting and ending with an "
            f"alphanumeric character.  Got: {value!r}"
        )


def _validate_nonempty_str(value: str, label: str, max_len: int) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.  Got: {value!r}")
    if len(value) > max_len:
        raise ValueError(
            f"{label} exceeds maximum length {max_len}.  Got length: {len(value)}"
        )


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PublicationStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class VersionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class UserRole(str, enum.Enum):
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    CASE_HANDLER = "case_handler"
    JURISDICTION_OFFICER = "jurisdiction_officer"
    LEARNER = "learner"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ReviewerRole(str, enum.Enum):
    EDITORIAL = "editorial"
    HEALTH_CONTENT = "health_content"


class CardType(str, enum.Enum):
    EXPLANATION = "explanation"
    INTERACTION = "interaction"
    RECAP = "recap"


class InteractionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"


class IncorrectBehaviour(str, enum.Enum):
    RETRY = "retry"
    CONTINUE = "continue"


# ---------------------------------------------------------------------------
# Domain Objects
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Topic:
    topic_id: str
    title: str
    url_slug: str
    description: str
    display_order: int
    status: PublicationStatus
    cover_image_ref: Optional[str] = None
    cover_image_alt: Optional[str] = None

    def validate(self) -> None:
        _validate_id(self.topic_id, "topic_id")
        _validate_nonempty_str(self.title, "title", MAX_TITLE_LEN)
        if not isinstance(self.url_slug, str) or not _SLUG_RE.match(self.url_slug):
            raise ValueError(
                f"url_slug must be a lowercase dash-separated slug.  Got: {self.url_slug!r}"
            )
        _validate_nonempty_str(self.description, "description", MAX_DESCRIPTION_LEN)
        if not isinstance(self.display_order, int) or self.display_order < 0:
            raise ValueError(
                f"display_order must be a non-negative integer.  Got: {self.display_order!r}"
            )
        if not isinstance(self.status, PublicationStatus):
            raise ValueError(f"status must be a PublicationStatus.  Got: {self.status!r}")
        if self.cover_image_ref is not None:
            _validate_nonempty_str(self.cover_image_ref, "cover_image_ref", 500)
        if self.cover_image_alt is not None:
            _validate_nonempty_str(self.cover_image_alt, "cover_image_alt", 300)


@dataclasses.dataclass
class AnswerOption:
    option_id: str
    label: str
    is_correct: bool
    feedback: str

    def validate(self) -> None:
        _validate_id(self.option_id, "option_id")
        _validate_nonempty_str(self.label, "label", MAX_TITLE_LEN)
        if not isinstance(self.is_correct, bool):
            raise ValueError(f"is_correct must be a boolean.  Got: {self.is_correct!r}")
        _validate_nonempty_str(self.feedback, "feedback", MAX_FEEDBACK_LEN)


@dataclasses.dataclass
class SingleChoiceInteraction:
    interaction_type: InteractionType
    question_prompt: str
    options: list[AnswerOption]
    incorrect_behaviour: IncorrectBehaviour

    def validate(self) -> None:
        if self.interaction_type is not InteractionType.SINGLE_CHOICE:
            raise ValueError(
                f"interaction_type must be SINGLE_CHOICE.  Got: {self.interaction_type!r}"
            )
        _validate_nonempty_str(self.question_prompt, "question_prompt", MAX_SUMMARY_LEN)

        if not isinstance(self.options, list) or len(self.options) < 2:
            raise ValueError("An interaction must have at least 2 answer options.")
        if len(self.options) > MAX_OPTIONS:
            raise ValueError(f"An interaction may have at most {MAX_OPTIONS} options.")

        seen_ids: set[str] = set()
        correct_count = 0
        for opt in self.options:
            opt.validate()
            if opt.option_id in seen_ids:
                raise ValueError(f"Duplicate option_id: {opt.option_id!r}")
            seen_ids.add(opt.option_id)
            if opt.is_correct:
                correct_count += 1

        if correct_count != 1:
            raise ValueError(
                f"Exactly one option must be correct.  Found {correct_count} correct options."
            )

        if not isinstance(self.incorrect_behaviour, IncorrectBehaviour):
            raise ValueError(
                f"incorrect_behaviour must be an IncorrectBehaviour enum.  "
                f"Got: {self.incorrect_behaviour!r}"
            )

    def evaluate(self, selected_option_id: str) -> tuple[bool, str]:
        """Evaluate a learner's answer.  Returns (is_correct, feedback_text)."""
        for opt in self.options:
            if opt.option_id == selected_option_id:
                return opt.is_correct, opt.feedback
        raise ValueError(f"Unknown option_id: {selected_option_id!r}")


@dataclasses.dataclass
class ContentBlock:
    block_type: str  # "text", "heading", "image_ref"
    body: str

    def validate(self) -> None:
        if self.block_type not in ("text", "heading", "image_ref"):
            raise ValueError(f"Unknown content block_type: {self.block_type!r}")
        _validate_nonempty_str(self.body, "body", 5000)


@dataclasses.dataclass
class LessonCard:
    card_id: str
    position: int
    card_type: CardType
    content_blocks: list[ContentBlock]
    source_ids: list[str]
    interaction: Optional[SingleChoiceInteraction] = None

    def validate(self) -> None:
        _validate_id(self.card_id, "card_id")
        if not isinstance(self.position, int) or self.position < 0:
            raise ValueError(f"position must be a non-negative integer.  Got: {self.position!r}")
        if not isinstance(self.card_type, CardType):
            raise ValueError(f"card_type must be a CardType.  Got: {self.card_type!r}")

        if not isinstance(self.content_blocks, list) or len(self.content_blocks) == 0:
            raise ValueError("A card must have at least one content block.")
        for block in self.content_blocks:
            block.validate()

        if not isinstance(self.source_ids, list):
            raise ValueError("source_ids must be a list.")
        for sid in self.source_ids:
            _validate_id(sid, "source_id reference")

        if self.card_type == CardType.INTERACTION:
            if self.interaction is None:
                raise ValueError("An interaction card must include an interaction definition.")
            self.interaction.validate()
        else:
            if self.interaction is not None:
                raise ValueError(
                    f"A {self.card_type.value} card must not include an interaction."
                )


@dataclasses.dataclass
class LessonVersion:
    version_id: str
    lesson_id: str
    version_number: int
    title: str
    summary: str
    language: str
    learning_objectives: list[str]
    estimated_duration_minutes: int
    cards: list[LessonCard]
    source_ids: list[str]
    status: VersionStatus
    author_id: Optional[str] = None
    submitted_by: Optional[str] = None
    review_feedback: Optional[str] = None

    def validate(self) -> None:
        _validate_id(self.version_id, "version_id")
        _validate_id(self.lesson_id, "lesson_id")
        if not isinstance(self.version_number, int) or self.version_number < 1:
            raise ValueError(
                f"version_number must be a positive integer.  Got: {self.version_number!r}"
            )
        _validate_nonempty_str(self.title, "title", MAX_TITLE_LEN)
        _validate_nonempty_str(self.summary, "summary", MAX_SUMMARY_LEN)
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"language must be one of {sorted(SUPPORTED_LANGUAGES)}.  Got: {self.language!r}"
            )
        if not isinstance(self.learning_objectives, list) or len(self.learning_objectives) == 0:
            raise ValueError("At least one learning objective is required.")
        if len(self.learning_objectives) > MAX_OBJECTIVES:
            raise ValueError(f"At most {MAX_OBJECTIVES} learning objectives are allowed.")
        for obj in self.learning_objectives:
            _validate_nonempty_str(obj, "learning_objective", MAX_DESCRIPTION_LEN)

        if not isinstance(self.estimated_duration_minutes, int) or self.estimated_duration_minutes < 1:
            raise ValueError(
                f"estimated_duration_minutes must be a positive integer.  "
                f"Got: {self.estimated_duration_minutes!r}"
            )

        if not isinstance(self.cards, list) or len(self.cards) == 0:
            raise ValueError("A lesson version must have at least one card.")
        if len(self.cards) > MAX_CARDS:
            raise ValueError(f"A lesson version may have at most {MAX_CARDS} cards.")

        card_ids: set[str] = set()
        positions: set[int] = set()
        for card in self.cards:
            card.validate()
            if card.card_id in card_ids:
                raise ValueError(f"Duplicate card_id: {card.card_id!r}")
            card_ids.add(card.card_id)
            if card.position in positions:
                raise ValueError(f"Duplicate card position: {card.position}")
            positions.add(card.position)

        if not isinstance(self.source_ids, list):
            raise ValueError("source_ids must be a list.")
        if len(self.source_ids) > MAX_SOURCES_PER_VERSION:
            raise ValueError(f"At most {MAX_SOURCES_PER_VERSION} source references allowed.")
        for sid in self.source_ids:
            _validate_id(sid, "source_id reference")

        if not isinstance(self.status, VersionStatus):
            raise ValueError(f"status must be a VersionStatus.  Got: {self.status!r}")

    def cards_as_dicts(self) -> list[dict[str, Any]]:
        """Serialise the cards list to JSON-safe dicts for NDB storage."""
        return [dataclasses.asdict(c) for c in self.cards]

    @staticmethod
    def cards_from_dicts(raw: list[dict[str, Any]]) -> list[LessonCard]:
        """Reconstruct LessonCard list from stored dicts."""
        cards: list[LessonCard] = []
        for d in raw:
            interaction = None
            if d.get("interaction"):
                idata = d["interaction"]
                opts = [AnswerOption(**o) for o in idata["options"]]
                interaction = SingleChoiceInteraction(
                    interaction_type=InteractionType(idata["interaction_type"]),
                    question_prompt=idata["question_prompt"],
                    options=opts,
                    incorrect_behaviour=IncorrectBehaviour(idata["incorrect_behaviour"]),
                )
            blocks = [ContentBlock(**b) for b in d["content_blocks"]]
            cards.append(
                LessonCard(
                    card_id=d["card_id"],
                    position=d["position"],
                    card_type=CardType(d["card_type"]),
                    content_blocks=blocks,
                    source_ids=d["source_ids"],
                    interaction=interaction,
                )
            )
        return cards


@dataclasses.dataclass
class Lesson:
    lesson_id: str
    topic_id: str
    display_order: int
    published_version_id: Optional[str] = None
    draft_version_id: Optional[str] = None

    def validate(self) -> None:
        _validate_id(self.lesson_id, "lesson_id")
        _validate_id(self.topic_id, "topic_id")
        if not isinstance(self.display_order, int) or self.display_order < 0:
            raise ValueError(
                f"display_order must be a non-negative integer.  Got: {self.display_order!r}"
            )
        if self.published_version_id is not None:
            _validate_id(self.published_version_id, "published_version_id")
        if self.draft_version_id is not None:
            _validate_id(self.draft_version_id, "draft_version_id")


@dataclasses.dataclass
class HealthSource:
    source_id: str
    title: str
    publisher: str
    url: str
    publication_date: Optional[date] = None
    access_date: Optional[date] = None
    jurisdiction: Optional[str] = None
    metadata_notes: Optional[str] = None

    def validate(self) -> None:
        _validate_id(self.source_id, "source_id")
        _validate_nonempty_str(self.title, "title", MAX_TITLE_LEN)
        _validate_nonempty_str(self.publisher, "publisher", MAX_TITLE_LEN)
        if not isinstance(self.url, str) or not _URL_RE.match(self.url):
            raise ValueError(f"url must be a valid HTTP(S) URL.  Got: {self.url!r}")
        if self.publication_date is not None and not isinstance(self.publication_date, date):
            raise ValueError("publication_date must be a date or None.")
        if self.access_date is not None and not isinstance(self.access_date, date):
            raise ValueError("access_date must be a date or None.")
        if self.jurisdiction is not None:
            _validate_nonempty_str(self.jurisdiction, "jurisdiction", 200)
        if self.metadata_notes is not None:
            _validate_nonempty_str(self.metadata_notes, "metadata_notes", MAX_DESCRIPTION_LEN)


@dataclasses.dataclass
class ReviewRecord:
    review_id: str
    lesson_id: str
    version_id: str
    editorial_status: ReviewStatus
    health_content_status: ReviewStatus
    reviewer_role: ReviewerRole
    review_date: date
    next_review_date: Optional[date] = None
    notes: Optional[str] = None

    def validate(self) -> None:
        _validate_id(self.review_id, "review_id")
        _validate_id(self.lesson_id, "lesson_id")
        _validate_id(self.version_id, "version_id")
        if not isinstance(self.editorial_status, ReviewStatus):
            raise ValueError(f"editorial_status must be a ReviewStatus.  Got: {self.editorial_status!r}")
        if not isinstance(self.health_content_status, ReviewStatus):
            raise ValueError(f"health_content_status must be a ReviewStatus.  Got: {self.health_content_status!r}")
        if not isinstance(self.reviewer_role, ReviewerRole):
            raise ValueError(f"reviewer_role must be a ReviewerRole.  Got: {self.reviewer_role!r}")
        if not isinstance(self.review_date, date):
            raise ValueError("review_date must be a date.")
        if self.next_review_date is not None and not isinstance(self.next_review_date, date):
            raise ValueError("next_review_date must be a date or None.")
        if self.notes is not None:
            _validate_nonempty_str(self.notes, "notes", MAX_DESCRIPTION_LEN)


@dataclasses.dataclass
class User:
    """Application user with role-based access."""
    user_id: str
    username: str
    display_name: str
    role: UserRole
    password_hash: Optional[str] = None
    is_active: bool = True
    neon_auth_user_id: Optional[str] = None
    must_change_password: bool = False

    def validate(self) -> None:
        _validate_id(self.user_id, "user_id")
        if not isinstance(self.username, str) or not self.username.strip():
            raise ValueError(f"username must be a non-empty string.  Got: {self.username!r}")
        if len(self.username) > 100:
            raise ValueError(f"username exceeds maximum length 100.")
        _validate_nonempty_str(self.display_name, "display_name", MAX_TITLE_LEN)
        if not isinstance(self.role, UserRole):
            raise ValueError(f"role must be a UserRole.  Got: {self.role!r}")
        if self.password_hash is not None:
            if not isinstance(self.password_hash, str) or not self.password_hash.strip():
                raise ValueError("password_hash must be a non-empty string or None.")
        if not isinstance(self.is_active, bool):
            raise ValueError(f"is_active must be a boolean.  Got: {self.is_active!r}")
        if not isinstance(self.must_change_password, bool):
            raise ValueError(f"must_change_password must be a boolean.  Got: {self.must_change_password!r}")
