"""Domain dataclasses, enums, and validation for Staff Application and Multi-Stage Vetting."""

from __future__ import annotations

import dataclasses
import enum
import re
from datetime import datetime
from typing import Any, Optional

REFERENCE_ID_REGEX = re.compile(r"^APP-[0-9]{4}-[A-Z0-9]{6}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")

MAX_NAME_LEN = 200
MAX_EMAIL_LEN = 255
MAX_PHONE_LEN = 50
MAX_ORG_LEN = 255
MAX_TITLE_LEN = 255
MAX_STATEMENT_LEN = 4000
MAX_NOTES_LEN = 4000
MAX_REASON_LEN = 2000


class ApplicationStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    MORE_INFO_REQUESTED = "more_info_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


APPLICATION_STATUS_LABELS = {
    ApplicationStatus.PENDING_REVIEW: "Pending Initial Review",
    ApplicationStatus.UNDER_REVIEW: "Under Review by Verification Team",
    ApplicationStatus.MORE_INFO_REQUESTED: "Additional Information Requested",
    ApplicationStatus.APPROVED: "Approved — Account Provisioned",
    ApplicationStatus.REJECTED: "Application Declined",
    ApplicationStatus.WITHDRAWN: "Withdrawn by Applicant",
}


class StaffRoleOption(str, enum.Enum):
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    CASE_HANDLER = "case_handler"
    JURISDICTION_OFFICER = "jurisdiction_officer"


STAFF_ROLE_DESCRIPTIONS = {
    StaffRoleOption.CONTRIBUTOR: "Author and translate community health lessons and explanations",
    StaffRoleOption.REVIEWER: "Review curriculum for medical accuracy, clarity, and citations",
    StaffRoleOption.CASE_HANDLER: "Triage and coordinate public sanitation and health concerns",
    StaffRoleOption.JURISDICTION_OFFICER: "Coordinate localized sanitation response within assigned district",
}


@dataclasses.dataclass
class VerificationChecklist:
    contact_verified: bool = False
    affiliation_verified: bool = False
    role_criteria_met: bool = False
    verification_notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "contact_verified": self.contact_verified,
            "affiliation_verified": self.affiliation_verified,
            "role_criteria_met": self.role_criteria_met,
            "verification_notes": self.verification_notes or "",
        }

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "VerificationChecklist":
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            contact_verified=bool(data.get("contact_verified")),
            affiliation_verified=bool(data.get("affiliation_verified")),
            role_criteria_met=bool(data.get("role_criteria_met")),
            verification_notes=data.get("verification_notes"),
        )


@dataclasses.dataclass
class StaffApplication:
    application_id: str
    reference_id: str
    tracking_token_hash: str
    applicant_name: str
    applicant_email: str
    requested_role: str
    statement_of_purpose: str
    applicant_phone: Optional[str] = None
    organization: Optional[str] = None
    professional_title: Optional[str] = None
    credential_reference: Optional[str] = None
    portfolio_url: Optional[str] = None
    evidence_standards_acknowledged: bool = False
    child_safety_acknowledged: bool = False
    status: ApplicationStatus = ApplicationStatus.PENDING_REVIEW
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    approved_role: Optional[str] = None
    assigned_jurisdiction: Optional[str] = None
    provisioned_user_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    info_request_details: Optional[str] = None
    applicant_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    verification_checklist: VerificationChecklist = dataclasses.field(default_factory=VerificationChecklist)
    tracking_token_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> None:
        if not self.application_id or not isinstance(self.application_id, str):
            raise ValueError("application_id must be a non-empty string.")
        if not self.reference_id or not REFERENCE_ID_REGEX.match(self.reference_id):
            raise ValueError(f"reference_id must match format 'APP-YYYY-XXXXXX', got {self.reference_id!r}")
        if not self.tracking_token_hash:
            raise ValueError("tracking_token_hash is required.")

        clean_name = (self.applicant_name or "").strip()
        if not clean_name or len(clean_name) > MAX_NAME_LEN:
            raise ValueError(f"applicant_name must be between 1 and {MAX_NAME_LEN} characters.")

        clean_email = (self.applicant_email or "").strip().lower()
        if not clean_email or not EMAIL_REGEX.match(clean_email) or len(clean_email) > MAX_EMAIL_LEN:
            raise ValueError("applicant_email must be a valid email address.")

        if self.applicant_phone:
            clean_phone = self.applicant_phone.strip()
            if not PHONE_REGEX.match(clean_phone) or len(clean_phone) > MAX_PHONE_LEN:
                raise ValueError("applicant_phone must be a valid phone number.")

        valid_roles = {r.value for r in StaffRoleOption}
        if self.requested_role not in valid_roles:
            raise ValueError(f"requested_role must be one of {sorted(valid_roles)}, got {self.requested_role!r}")

        clean_sop = (self.statement_of_purpose or "").strip()
        if not clean_sop or len(clean_sop) < 30 or len(clean_sop) > MAX_STATEMENT_LEN:
            raise ValueError(f"statement_of_purpose must be between 30 and {MAX_STATEMENT_LEN} characters.")

        if not self.evidence_standards_acknowledged:
            raise ValueError("You must acknowledge HealthAware's evidence-based health information standards.")
        if not self.child_safety_acknowledged:
            raise ValueError("You must acknowledge HealthAware's learner safety guidelines.")

        if not isinstance(self.status, ApplicationStatus):
            raise ValueError(f"status must be an ApplicationStatus, got {self.status!r}")


@dataclasses.dataclass
class StaffApplicationHistory:
    history_id: str
    application_id: str
    from_status: str
    to_status: str
    actor_id: str
    actor_name: str
    actor_role: str
    action: str
    decision_rationale: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
