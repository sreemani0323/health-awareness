"""Domain dataclasses, enums, and validation for Report a Concern and Case Management."""

from __future__ import annotations

import dataclasses
import enum
import re
from datetime import datetime
from typing import Any, Optional

REFERENCE_ID_REGEX = re.compile(r"^HA-[0-9]{4}-[A-Z0-9]{6}$")

ALLOWED_STATES = frozenset({"Andhra Pradesh", "Telangana"})

MAX_DESCRIPTION_LEN = 2000
MAX_LOCALITY_LEN = 500
MAX_DISTRICT_LEN = 100
MAX_MUNICIPALITY_LEN = 100


class ConcernCategory(str, enum.Enum):
    GARBAGE = "garbage"
    STAGNANT_WATER = "stagnant_water"
    DRAINAGE = "drainage"
    SANITATION = "sanitation"


CONCERN_CATEGORY_LABELS = {
    ConcernCategory.GARBAGE: "Accumulated garbage or missed waste collection",
    ConcernCategory.STAGNANT_WATER: "Stagnant water or possible mosquito-breeding site",
    ConcernCategory.DRAINAGE: "Blocked drains or sewage overflow",
    ConcernCategory.SANITATION: "Poor public-toilet sanitation",
}


class ConcernStatus(str, enum.Enum):
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    ACTION_IN_PROGRESS = "action_in_progress"
    NEEDS_MORE_INFO = "needs_more_info"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CLOSED = "closed"


STATUS_DISPLAY_LABELS = {
    ConcernStatus.RECEIVED: "Received by HealthAware",
    ConcernStatus.UNDER_REVIEW: "Under Review by HealthAware Team",
    ConcernStatus.ASSIGNED: "Assigned to Case Handler",
    ConcernStatus.ACTION_IN_PROGRESS: "Action in Progress",
    ConcernStatus.NEEDS_MORE_INFO: "Needs Additional Information",
    ConcernStatus.RESOLVED: "Resolved",
    ConcernStatus.REJECTED: "Rejected / Duplicate",
    ConcernStatus.CLOSED: "Closed",
}


class ConcernDuration(str, enum.Enum):
    LESS_THAN_3_DAYS = "< 3 days"
    THREE_TO_SEVEN_DAYS = "3-7 days"
    ONE_TO_TWO_WEEKS = "1-2 weeks"
    MORE_THAN_A_MONTH = "> 1 month"


class ActorType(str, enum.Enum):
    CITIZEN = "citizen"
    STAFF = "staff"
    SYSTEM = "system"


@dataclasses.dataclass
class ConcernReport:
    report_id: str
    reference_id: str
    token_hash: str
    category: ConcernCategory
    state: str
    district: str
    locality: str
    description: str
    duration: ConcernDuration
    municipality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: ConcernStatus = ConcernStatus.RECEIVED
    assigned_handler_id: Optional[str] = None
    assigned_handler_name: Optional[str] = None
    assigned_jurisdiction: Optional[str] = None
    rejection_reason: Optional[str] = None
    resolution_notes: Optional[str] = None
    citizen_reply_requested: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> None:
        if not REFERENCE_ID_REGEX.match(self.reference_id):
            raise ValueError(f"Invalid reference ID format: {self.reference_id!r}")
        if self.state not in ALLOWED_STATES:
            raise ValueError(f"State must be Andhra Pradesh or Telangana. Got: {self.state!r}")
        if not self.district or len(self.district) > MAX_DISTRICT_LEN:
            raise ValueError(f"District is required and must not exceed {MAX_DISTRICT_LEN} characters.")
        if not self.locality or len(self.locality) > MAX_LOCALITY_LEN:
            raise ValueError(f"Locality is required and must not exceed {MAX_LOCALITY_LEN} characters.")
        if not self.description or len(self.description) > MAX_DESCRIPTION_LEN:
            raise ValueError(f"Description is required and must not exceed {MAX_DESCRIPTION_LEN} characters.")
        if self.latitude is not None and not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude out of valid range: {self.latitude}")
        if self.longitude is not None and not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude out of valid range: {self.longitude}")


@dataclasses.dataclass
class ConcernStatusEvent:
    event_id: str
    report_id: str
    from_status: Optional[ConcernStatus]
    to_status: ConcernStatus
    actor_type: ActorType
    created_at: datetime
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    public_notes: Optional[str] = None
    internal_notes: Optional[str] = None


@dataclasses.dataclass
class ConcernAttachment:
    attachment_id: str
    report_id: str
    storage_key: str
    content_type: str
    file_size_bytes: int
    sha256_checksum: str
    created_at: datetime
    original_filename: Optional[str] = None
    uploaded_by: str = "citizen"
