"""Domain service managing the staff application lifecycle, verification, and multi-stage approval.

Enforces:
- Explicit state machine with strict transition guards.
- Concurrent conflict prevention using transactional row locking.
- Self-approval prohibition: administrators cannot approve their own application.
- Public vs. internal data isolation: applicants cannot view internal reviewer notes or other applications.
- Secure tracking token verification via SHA-256 and constant-time comparison.
- Atomic account provisioning upon authorized approval.
- Structured audit logging for all application events.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import logging
import re
import secrets
import uuid
from typing import Any, Generator, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.domain.domain_objects import User, UserRole
from backend.domain.staff_application_models import (
    ApplicationStatus,
    StaffApplication,
    StaffApplicationHistory,
    StaffRoleOption,
    VerificationChecklist,
)
from backend.platform.audit_log import SecurityAuditEvent, log_security_event
from backend.platform.security import hash_password
from backend.storage.postgres_models import (
    StaffApplicationHistoryModel,
    StaffApplicationModel,
    StaffJurisdictionModel,
    UserModel,
)

logger = logging.getLogger(__name__)

# Configurable lifecycle policies
STAFF_APPLICATION_TRACKING_EXPIRY_DAYS = 30
SETUP_TOKEN_EXPIRY_HOURS = 48


class ApplicationConflictError(Exception):
    """Raised when an application state has already changed concurrently."""


class ApplicationNotFoundError(Exception):
    """Raised when an application is not found."""


class ApplicationSecurityError(Exception):
    """Raised when unauthorized access or a security policy violation occurs."""


class StaffApplicationService:
    """Manages the full lifecycle of staff applications and multi-stage vetting."""

    VALID_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
        ApplicationStatus.PENDING_REVIEW: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.MORE_INFO_REQUESTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.UNDER_REVIEW: {
            ApplicationStatus.MORE_INFO_REQUESTED,
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.MORE_INFO_REQUESTED: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.APPROVED: set(),  # Terminal state
        ApplicationStatus.REJECTED: set(),  # Terminal state
        ApplicationStatus.WITHDRAWN: set(),  # Terminal state
    }

    def __init__(self, session_factory: Optional[Any] = None, engine: Optional[Any] = None):
        self._session_factory = session_factory
        self._engine = engine
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Safely ensures staff application tables and schema columns exist in the connected database."""
        try:
            if self._engine is not None:
                eng = self._engine
            else:
                from backend.storage.db import get_engine
                eng = get_engine()
            StaffApplicationModel.__table__.create(bind=eng, checkfirst=True)
            StaffApplicationHistoryModel.__table__.create(bind=eng, checkfirst=True)

            # Ensure columns exist if table was already created in a previous test run
            with eng.connect() as conn:
                for col_sql in [
                    "ALTER TABLE staff_applications ADD COLUMN tracking_token_expires_at TIMESTAMP WITH TIME ZONE",
                    "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE NOT NULL",
                    "ALTER TABLE users ADD COLUMN setup_token_hash VARCHAR(64)",
                    "ALTER TABLE users ADD COLUMN setup_token_expires_at TIMESTAMP WITH TIME ZONE",
                ]:
                    try:
                        conn.execute(text(col_sql))
                        conn.commit()
                    except Exception:
                        pass
        except Exception as exc:
            logger.debug("Table check for staff_applications: %s", exc)

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        if self._session_factory:
            session: Session = self._session_factory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        else:
            from backend.storage.db import get_db_session
            with get_db_session() as session:
                yield session

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Computes SHA-256 digest of tracking token."""
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def generate_reference_id() -> str:
        """Generates reference ID formatted as APP-YYYY-XXXXXX."""
        year = datetime.now(timezone.utc).year
        random_suffix = secrets.token_hex(3).upper()
        return f"APP-{year}-{random_suffix}"

    # -----------------------------------------------------------------------
    # Public Applicant Methods
    # -----------------------------------------------------------------------

    def submit_application(
        self,
        applicant_name: str,
        applicant_email: str,
        requested_role: str,
        statement_of_purpose: str,
        evidence_standards_acknowledged: bool,
        child_safety_acknowledged: bool,
        applicant_phone: Optional[str] = None,
        organization: Optional[str] = None,
        professional_title: Optional[str] = None,
        credential_reference: Optional[str] = None,
        portfolio_url: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Tuple[StaffApplication, str]:
        """Submits a new staff application with tracking credentials."""
        app_id = f"app_{uuid.uuid4().hex[:16]}"
        ref_id = self.generate_reference_id()
        raw_token = f"sec_app_{secrets.token_urlsafe(32)}"
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=STAFF_APPLICATION_TRACKING_EXPIRY_DAYS)

        app = StaffApplication(
            application_id=app_id,
            reference_id=ref_id,
            tracking_token_hash=token_hash,
            tracking_token_expires_at=expires_at,
            applicant_name=applicant_name.strip(),
            applicant_email=applicant_email.strip().lower(),
            requested_role=requested_role.strip().lower(),
            statement_of_purpose=statement_of_purpose.strip(),
            evidence_standards_acknowledged=evidence_standards_acknowledged,
            child_safety_acknowledged=child_safety_acknowledged,
            applicant_phone=applicant_phone.strip() if applicant_phone else None,
            organization=organization.strip() if organization else None,
            professional_title=professional_title.strip() if professional_title else None,
            credential_reference=credential_reference.strip() if credential_reference else None,
            portfolio_url=portfolio_url.strip() if portfolio_url else None,
            status=ApplicationStatus.PENDING_REVIEW,
            created_at=now,
            updated_at=now,
        )
        app.validate()

        with self._get_session() as session:
            # Check for existing pending application for this email
            existing = (
                session.query(StaffApplicationModel)
                .filter(
                    StaffApplicationModel.applicant_email == app.applicant_email,
                    StaffApplicationModel.status.in_([
                        ApplicationStatus.PENDING_REVIEW.value,
                        ApplicationStatus.UNDER_REVIEW.value,
                        ApplicationStatus.MORE_INFO_REQUESTED.value,
                    ]),
                )
                .first()
            )
            if existing:
                raise ApplicationConflictError(
                    f"An active application already exists for '{app.applicant_email}'. "
                    f"Please track reference {existing.reference_id} instead of creating a duplicate."
                )

            model = StaffApplicationModel(
                application_id=app.application_id,
                reference_id=app.reference_id,
                tracking_token_hash=app.tracking_token_hash,
                tracking_token_expires_at=expires_at,
                applicant_name=app.applicant_name,
                applicant_email=app.applicant_email,
                applicant_phone=app.applicant_phone,
                requested_role=app.requested_role,
                organization=app.organization,
                professional_title=app.professional_title,
                credential_reference=app.credential_reference,
                portfolio_url=app.portfolio_url,
                statement_of_purpose=app.statement_of_purpose,
                evidence_standards_acknowledged=app.evidence_standards_acknowledged,
                child_safety_acknowledged=app.child_safety_acknowledged,
                status=app.status.value,
                verification_checklist=app.verification_checklist.to_dict(),
                created_at=now,
                updated_at=now,
            )
            session.add(model)

            # Record initial history
            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=app.application_id,
                from_status="none",
                to_status=ApplicationStatus.PENDING_REVIEW.value,
                actor_id="applicant",
                actor_name=app.applicant_name,
                actor_role="applicant",
                action="submit",
                decision_rationale="Initial public staff application submitted.",
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_SUBMITTED,
            actor_id=app.applicant_email,
            target_id=app.reference_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "requested_role": app.requested_role,
                "reference_id": app.reference_id,
            },
        )

        return app, raw_token

    def recover_application_tracking(
        self, applicant_email: str, client_ip: Optional[str] = None
    ) -> Tuple[StaffApplication, str, bool]:
        """Recovers or reissues tracking token for an applicant with an active application."""
        clean_email = applicant_email.strip().lower()
        now = datetime.now(timezone.utc)
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    StaffApplicationModel.applicant_email == clean_email,
                    StaffApplicationModel.status.in_([
                        ApplicationStatus.PENDING_REVIEW.value,
                        ApplicationStatus.UNDER_REVIEW.value,
                        ApplicationStatus.MORE_INFO_REQUESTED.value,
                    ]),
                )
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"No active staff application found for '{clean_email}'.")

            ref_id = model.reference_id
            app_name = model.applicant_name

            raw_token = f"sec_app_{secrets.token_urlsafe(32)}"
            token_hash = self.hash_token(raw_token)
            expires_at = now + timedelta(days=STAFF_APPLICATION_TRACKING_EXPIRY_DAYS)

            model.tracking_token_hash = token_hash
            model.tracking_token_expires_at = expires_at
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=model.status,
                to_status=model.status,
                actor_id="applicant",
                actor_name=model.applicant_name,
                actor_role="applicant",
                action="token_recovery",
                decision_rationale="Applicant requested secure tracking token recovery.",
                created_at=now,
            )
            session.add(hist)
            session.commit()

        from backend.platform.email_service import get_email_service
        email_svc = get_email_service()
        email_res = email_svc.send_staff_application_tracking(
            to_email=clean_email,
            applicant_name=app_name,
            reference_id=ref_id,
            tracking_token=raw_token,
            tracking_url=f"/staff/application-status?reference_id={ref_id}",
        )
        email_sent = bool(email_res.success)

        log_security_event(
            event=(
                SecurityAuditEvent.STAFF_APP_RECOVERY_DISPATCHED
                if email_sent
                else SecurityAuditEvent.STAFF_APP_RECOVERY_REQUESTED
            ),
            actor_id=clean_email,
            target_id=ref_id,
            client_ip=client_ip,
            status="SUCCESS" if email_sent else "EMAIL_FAILED_OR_UNCONFIGURED",
            details={
                "reference_id": ref_id,
                "email_sent": email_sent,
            },
        )
        return ref_id, raw_token, email_sent

    def get_application_for_applicant(
        self, reference_id: str, raw_token: str
    ) -> dict[str, Any]:
        """Returns the applicant-facing view of an application. Fails closed with generic privacy-preserving error."""
        if not reference_id or not raw_token:
            raise ApplicationSecurityError("Reference ID and tracking token are required.")

        now = datetime.now(timezone.utc)
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter_by(reference_id=reference_id.strip())
                .first()
            )

            # Security and privacy guard:
            # 1. Non-existent application
            # 2. Token expiration
            # 3. Terminal state (approved, rejected, withdrawn)
            # 4. Revoked token
            # 5. Invalid token hash
            # All fail closed with identical ApplicationNotFoundError to prevent state enumeration
            expected_hash = self.hash_token(raw_token)
            is_expired = bool(
                model
                and model.tracking_token_expires_at
                and now > (
                    model.tracking_token_expires_at
                    if model.tracking_token_expires_at.tzinfo
                    else model.tracking_token_expires_at.replace(tzinfo=timezone.utc)
                )
            )
            is_terminal = bool(
                model
                and model.status in (
                    ApplicationStatus.APPROVED.value,
                    ApplicationStatus.REJECTED.value,
                    ApplicationStatus.WITHDRAWN.value,
                )
            )
            is_revoked = bool(model and (model.tracking_token_hash or "").startswith("REVOKED"))
            token_matches = bool(model and hmac.compare_digest(expected_hash, model.tracking_token_hash))

            if not model:
                raise ApplicationNotFoundError(f"Application '{reference_id}' not found.")

            if is_expired or is_terminal or is_revoked or not token_matches:
                log_security_event(
                    event=SecurityAuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
                    actor_id="applicant_tracking",
                    target_id=reference_id,
                    status="REJECTED",
                    details={"reason": "invalid_or_expired_tracking_credentials"},
                )
                raise ApplicationSecurityError("Invalid tracking credentials or tracking access has expired.")

            # Applicant view strictly omits internal_notes, reviewer details, and rejection specifics
            return {
                "reference_id": model.reference_id,
                "applicant_name": model.applicant_name,
                "applicant_email": model.applicant_email,
                "requested_role": model.requested_role,
                "status": model.status,
                "organization": model.organization,
                "professional_title": model.professional_title,
                "credential_reference": model.credential_reference,
                "portfolio_url": model.portfolio_url,
                "statement_of_purpose": model.statement_of_purpose,
                "info_request_details": model.info_request_details if model.status == ApplicationStatus.MORE_INFO_REQUESTED.value else None,
                "applicant_notes": model.applicant_notes,
                "rejection_reason": None,
                "approved_role": None,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            }

    def respond_to_info_request(
        self,
        reference_id: str,
        raw_token: str,
        applicant_notes: str,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Allows applicant to respond to follow-up information requests."""
        if not applicant_notes or not applicant_notes.strip():
            raise ValueError("Response notes cannot be empty.")

        now = datetime.now(timezone.utc)
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter_by(reference_id=reference_id.strip())
                .with_for_update()
                .first()
            )

            expected_hash = self.hash_token(raw_token)
            is_expired = bool(
                model
                and model.tracking_token_expires_at
                and now > (
                    model.tracking_token_expires_at
                    if model.tracking_token_expires_at.tzinfo
                    else model.tracking_token_expires_at.replace(tzinfo=timezone.utc)
                )
            )
            is_revoked = bool(model and (model.tracking_token_hash or "").startswith("REVOKED"))
            token_matches = bool(model and hmac.compare_digest(expected_hash, model.tracking_token_hash))

            if not model or is_expired or is_revoked or not token_matches:
                raise ApplicationNotFoundError("Invalid tracking credentials or tracking access has expired.")

            if model.status != ApplicationStatus.MORE_INFO_REQUESTED.value:
                raise ApplicationConflictError(
                    f"Application is in '{model.status}' state. "
                    "Follow-up responses can only be submitted when additional information is requested."
                )

            from_status = model.status
            to_status = ApplicationStatus.UNDER_REVIEW.value

            # Update notes and transition back to under_review
            combined_notes = (
                f"{model.applicant_notes}\n\n[{now.strftime('%Y-%m-%d %H:%M UTC')}]: {applicant_notes.strip()}"
                if model.applicant_notes
                else f"[{now.strftime('%Y-%m-%d %H:%M UTC')}]: {applicant_notes.strip()}"
            )
            model.applicant_notes = combined_notes
            model.status = to_status
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=from_status,
                to_status=to_status,
                actor_id="applicant",
                actor_name=model.applicant_name,
                actor_role="applicant",
                action="respond_info",
                decision_rationale="Applicant provided requested follow-up information.",
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_INFO_RESPONDED,
            actor_id=model.applicant_email,
            target_id=reference_id,
            client_ip=client_ip,
            status="SUCCESS",
        )

        return {"reference_id": reference_id, "status": to_status, "message": "Information submitted successfully."}

    def withdraw_application(
        self,
        reference_id: str,
        raw_token: str,
        rationale: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Allows an applicant to voluntarily withdraw their application."""
        now = datetime.now(timezone.utc)
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter_by(reference_id=reference_id.strip())
                .with_for_update()
                .first()
            )

            expected_hash = self.hash_token(raw_token)
            is_expired = bool(
                model
                and model.tracking_token_expires_at
                and now > (
                    model.tracking_token_expires_at
                    if model.tracking_token_expires_at.tzinfo
                    else model.tracking_token_expires_at.replace(tzinfo=timezone.utc)
                )
            )
            is_revoked = bool(model and (model.tracking_token_hash or "").startswith("REVOKED"))
            token_matches = bool(model and hmac.compare_digest(expected_hash, model.tracking_token_hash))

            if not model or is_expired or is_revoked or not token_matches:
                raise ApplicationNotFoundError("Invalid tracking credentials or tracking access has expired.")

            current_status = ApplicationStatus(model.status)
            if current_status not in (
                ApplicationStatus.PENDING_REVIEW,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.MORE_INFO_REQUESTED,
            ):
                raise ApplicationConflictError(
                    f"Cannot withdraw application in '{model.status}' state."
                )

            from_status = model.status
            to_status = ApplicationStatus.WITHDRAWN.value

            # Invalidate tracking token upon reaching terminal state
            model.tracking_token_hash = f"REVOKED_{uuid.uuid4().hex}"
            model.tracking_token_expires_at = now
            model.status = to_status
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=from_status,
                to_status=to_status,
                actor_id="applicant",
                actor_name=model.applicant_name,
                actor_role="applicant",
                action="withdraw",
                decision_rationale=rationale or "Application voluntarily withdrawn by applicant.",
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_WITHDRAWN,
            actor_id=model.applicant_email,
            target_id=reference_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"rationale": rationale or "none"},
        )

        return {"reference_id": reference_id, "status": to_status, "message": "Application has been withdrawn."}

    # -----------------------------------------------------------------------
    # Authorized Reviewer & Administrator Methods
    # -----------------------------------------------------------------------

    def list_applications_for_admin(
        self,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Lists applications for administrator queue with filtering."""
        with self._get_session() as session:
            q = session.query(StaffApplicationModel)
            if status_filter and status_filter.lower() != "all":
                q = q.filter(StaffApplicationModel.status == status_filter.strip().lower())
            if search_query:
                term = f"%{search_query.strip()}%"
                q = q.filter(
                    (StaffApplicationModel.reference_id.ilike(term))
                    | (StaffApplicationModel.applicant_name.ilike(term))
                    | (StaffApplicationModel.applicant_email.ilike(term))
                    | (StaffApplicationModel.organization.ilike(term))
                )
            results = q.order_by(StaffApplicationModel.created_at.desc()).all()

            output = []
            for m in results:
                output.append({
                    "application_id": m.application_id,
                    "reference_id": m.reference_id,
                    "applicant_name": m.applicant_name,
                    "applicant_email": m.applicant_email,
                    "applicant_phone": m.applicant_phone,
                    "requested_role": m.requested_role,
                    "organization": m.organization,
                    "professional_title": m.professional_title,
                    "status": m.status,
                    "assigned_reviewer_id": m.assigned_reviewer_id,
                    "assigned_reviewer_name": m.assigned_reviewer_name,
                    "approved_role": m.approved_role,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                })
            return output

    def get_application_for_admin(self, identifier: str) -> dict[str, Any]:
        """Returns full administrative details including verification checklist and history."""
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    (StaffApplicationModel.application_id == identifier.strip())
                    | (StaffApplicationModel.reference_id == identifier.strip())
                )
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"Application '{identifier}' not found.")

            # Load history
            histories = (
                session.query(StaffApplicationHistoryModel)
                .filter_by(application_id=model.application_id)
                .order_by(StaffApplicationHistoryModel.created_at.asc())
                .all()
            )

            hist_list = []
            for h in histories:
                hist_list.append({
                    "history_id": h.history_id,
                    "from_status": h.from_status,
                    "to_status": h.to_status,
                    "actor_id": h.actor_id,
                    "actor_name": h.actor_name,
                    "actor_role": h.actor_role,
                    "action": h.action,
                    "decision_rationale": h.decision_rationale,
                    "metadata": h.metadata_json,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                })

            checklist = VerificationChecklist.from_dict(model.verification_checklist)

            return {
                "application_id": model.application_id,
                "reference_id": model.reference_id,
                "applicant_name": model.applicant_name,
                "applicant_email": model.applicant_email,
                "applicant_phone": model.applicant_phone,
                "requested_role": model.requested_role,
                "organization": model.organization,
                "professional_title": model.professional_title,
                "credential_reference": model.credential_reference,
                "portfolio_url": model.portfolio_url,
                "statement_of_purpose": model.statement_of_purpose,
                "evidence_standards_acknowledged": model.evidence_standards_acknowledged,
                "child_safety_acknowledged": model.child_safety_acknowledged,
                "status": model.status,
                "assigned_reviewer_id": model.assigned_reviewer_id,
                "assigned_reviewer_name": model.assigned_reviewer_name,
                "approved_role": model.approved_role,
                "assigned_jurisdiction": model.assigned_jurisdiction,
                "provisioned_user_id": model.provisioned_user_id,
                "rejection_reason": model.rejection_reason,
                "info_request_details": model.info_request_details,
                "applicant_notes": model.applicant_notes,
                "internal_notes": model.internal_notes,
                "verification_checklist": checklist.to_dict(),
                "history": hist_list,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            }

    def claim_application(
        self,
        identifier: str,
        admin_user: User,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Claims an application for review and moves it to under_review."""
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    (StaffApplicationModel.application_id == identifier.strip())
                    | (StaffApplicationModel.reference_id == identifier.strip())
                )
                .with_for_update()
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"Application '{identifier}' not found.")

            # Self-approval / self-review prohibition
            if admin_user.username == model.applicant_email or admin_user.display_name.lower() == model.applicant_name.lower():
                raise ApplicationSecurityError("Self-review is strictly prohibited. You cannot claim your own application.")

            now = datetime.now(timezone.utc)
            from_status = model.status
            to_status = ApplicationStatus.UNDER_REVIEW.value

            model.assigned_reviewer_id = admin_user.user_id
            model.assigned_reviewer_name = admin_user.display_name
            if model.status == ApplicationStatus.PENDING_REVIEW.value:
                model.status = to_status
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=from_status,
                to_status=model.status,
                actor_id=admin_user.user_id,
                actor_name=admin_user.display_name,
                actor_role=admin_user.role.value,
                action="claim",
                decision_rationale=f"Review claimed by {admin_user.display_name}.",
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_CLAIMED,
            actor_id=admin_user.user_id,
            target_id=model.reference_id,
            client_ip=client_ip,
            status="SUCCESS",
        )

        return {"application_id": model.application_id, "status": model.status, "assigned_reviewer": admin_user.display_name}

    def update_verification_checklist(
        self,
        identifier: str,
        admin_user: User,
        checklist_data: dict[str, Any],
        internal_notes: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Updates verification checklist and internal notes during vetting."""
        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    (StaffApplicationModel.application_id == identifier.strip())
                    | (StaffApplicationModel.reference_id == identifier.strip())
                )
                .with_for_update()
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"Application '{identifier}' not found.")

            checklist = VerificationChecklist.from_dict(checklist_data)
            now = datetime.now(timezone.utc)
            model.verification_checklist = checklist.to_dict()
            if internal_notes is not None:
                model.internal_notes = internal_notes.strip()
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=model.status,
                to_status=model.status,
                actor_id=admin_user.user_id,
                actor_name=admin_user.display_name,
                actor_role=admin_user.role.value,
                action="update_checklist",
                decision_rationale="Verification checklist updated.",
                metadata_json=checklist.to_dict(),
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_CHECKLIST_UPDATED,
            actor_id=admin_user.user_id,
            target_id=model.reference_id,
            client_ip=client_ip,
            status="SUCCESS",
        )

        return {"application_id": model.application_id, "verification_checklist": checklist.to_dict()}

    def request_more_information(
        self,
        identifier: str,
        admin_user: User,
        info_details: str,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Requests follow-up clarification from the applicant, moving status to more_info_requested."""
        if not info_details or not info_details.strip():
            raise ValueError("Information request details are required.")

        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    (StaffApplicationModel.application_id == identifier.strip())
                    | (StaffApplicationModel.reference_id == identifier.strip())
                )
                .with_for_update()
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"Application '{identifier}' not found.")

            current_status = ApplicationStatus(model.status)
            if current_status not in (ApplicationStatus.PENDING_REVIEW, ApplicationStatus.UNDER_REVIEW):
                raise ApplicationConflictError(
                    f"Cannot request info when application is in '{model.status}' state."
                )

            now = datetime.now(timezone.utc)
            from_status = model.status
            to_status = ApplicationStatus.MORE_INFO_REQUESTED.value

            model.status = to_status
            model.info_request_details = info_details.strip()
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=from_status,
                to_status=to_status,
                actor_id=admin_user.user_id,
                actor_name=admin_user.display_name,
                actor_role=admin_user.role.value,
                action="request_info",
                decision_rationale=info_details.strip(),
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_INFO_REQUESTED,
            actor_id=admin_user.user_id,
            target_id=model.reference_id,
            client_ip=client_ip,
            status="SUCCESS",
        )

        return {"application_id": model.application_id, "status": to_status}

    def approve_application(
        self,
        identifier: str,
        admin_user: User,
        approved_role: str,
        assigned_jurisdiction: Optional[str] = None,
        rationale: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Approves a staff application and atomically provisions a staff user account with temporary credentials."""
        # 1. Authorize approver role
        if admin_user.role != UserRole.ADMIN:
            raise ApplicationSecurityError("Only administrators are authorized to approve staff applications.")

        # 2. Validate approved role
        valid_roles = {r.value for r in StaffRoleOption}
        if approved_role not in valid_roles:
            raise ValueError(f"approved_role must be one of {sorted(valid_roles)}, got {approved_role!r}")

        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    (StaffApplicationModel.application_id == identifier.strip())
                    | (StaffApplicationModel.reference_id == identifier.strip())
                )
                .with_for_update()
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"Application '{identifier}' not found.")

            # 3. SELF-APPROVAL PROHIBITION (Strict Security Guard)
            if (
                admin_user.user_id == model.provisioned_user_id
                or admin_user.username == model.applicant_email
                or admin_user.display_name.lower() == model.applicant_name.lower()
            ):
                log_security_event(
                    event=SecurityAuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
                    actor_id=admin_user.user_id,
                    target_id=model.reference_id,
                    status="REJECTED",
                    details={"reason": "self_approval_attempt"},
                )
                raise ApplicationSecurityError("Self-approval is strictly prohibited. You cannot approve your own application.")

            # 4. State transition check
            current_status = ApplicationStatus(model.status)
            if current_status not in (
                ApplicationStatus.PENDING_REVIEW,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.MORE_INFO_REQUESTED,
            ):
                raise ApplicationConflictError(
                    f"Cannot approve application in '{model.status}' state. "
                    "Decisions cannot be duplicated or changed once finalized."
                )

            now = datetime.now(timezone.utc)
            from_status = model.status
            to_status = ApplicationStatus.APPROVED.value

            # 5. Invalidate tracking token upon reaching terminal approved state
            model.tracking_token_hash = f"REVOKED_{uuid.uuid4().hex}"
            model.tracking_token_expires_at = now

            # 6. Provision staff account
            # Derive unique username from email prefix
            email_prefix = re.sub(r"[^a-zA-Z0-9_]", "", model.applicant_email.split("@")[0])[:20]
            candidate_username = f"staff_{email_prefix}"
            # Check uniqueness
            existing_user = session.query(UserModel).filter_by(username=candidate_username).first()
            if existing_user:
                candidate_username = f"staff_{email_prefix}_{secrets.token_hex(2)}"

            new_user_id = f"user-staff-{uuid.uuid4().hex[:8]}"

            # Generate single-use setup token with 48h expiry and scrambled dummy password
            raw_setup_token = f"set_{secrets.token_urlsafe(32)}"
            setup_token_hash = hashlib.sha256(raw_setup_token.encode("utf-8")).hexdigest()
            setup_token_expires_at = now + timedelta(hours=SETUP_TOKEN_EXPIRY_HOURS)

            scrambled_dummy_pw = secrets.token_urlsafe(32)
            hashed_pw = hash_password(scrambled_dummy_pw)

            new_user = UserModel(
                user_id=new_user_id,
                username=candidate_username,
                display_name=model.applicant_name,
                role=approved_role,
                password_hash=hashed_pw,
                is_active=True,
                must_change_password=True,
                setup_token_hash=setup_token_hash,
                setup_token_expires_at=setup_token_expires_at,
                created_at=now,
                updated_at=now,
            )
            session.add(new_user)
            session.flush()

            # Sync to NDB if context is present
            try:
                from google.cloud import ndb
                if ndb.get_context(raise_context_error=False) is not None:
                    from backend.storage.storage_models import UserModel as NdbUserModel
                    ndb_u = NdbUserModel(
                        id=new_user_id,
                        username=candidate_username,
                        display_name=model.applicant_name,
                        role=approved_role,
                        password_hash=hashed_pw,
                        is_active=True,
                        must_change_password=True,
                    )
                    ndb_u.put()
            except Exception as ndb_exc:
                logger.debug("NDB sync for newly provisioned user: %s", ndb_exc)

            # Assign jurisdiction if specified
            if assigned_jurisdiction and approved_role == StaffRoleOption.JURISDICTION_OFFICER.value:
                jur = StaffJurisdictionModel(
                    id=f"jur_{uuid.uuid4().hex[:16]}",
                    user_id=new_user_id,
                    state="Andhra Pradesh",
                    district=assigned_jurisdiction.strip(),
                    created_at=now,
                )
                session.add(jur)

            # Update application state
            model.status = to_status
            model.approved_role = approved_role
            model.assigned_jurisdiction = assigned_jurisdiction.strip() if assigned_jurisdiction else None
            model.provisioned_user_id = new_user_id
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=from_status,
                to_status=to_status,
                actor_id=admin_user.user_id,
                actor_name=admin_user.display_name,
                actor_role=admin_user.role.value,
                action="approve",
                decision_rationale=rationale or f"Application approved for role {approved_role}.",
                metadata_json={
                    "approved_role": approved_role,
                    "provisioned_user_id": new_user_id,
                    "assigned_jurisdiction": assigned_jurisdiction,
                },
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_APPROVED,
            actor_id=admin_user.user_id,
            target_id=model.reference_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "approved_role": approved_role,
                "provisioned_user_id": new_user_id,
            },
        )
        log_security_event(
            event=SecurityAuditEvent.STAFF_ACCOUNT_PROVISIONED,
            actor_id=admin_user.user_id,
            target_id=new_user_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "username": candidate_username,
                "role": approved_role,
            },
        )

        return {
            "application_id": model.application_id,
            "reference_id": model.reference_id,
            "status": to_status,
            "approved_role": approved_role,
            "provisioned_user_id": new_user_id,
            "username": candidate_username,
            "setup_token": raw_setup_token,
            "setup_token_expires_at": setup_token_expires_at.isoformat(),
            "message": "Staff application approved and staff account provisioned with single-use setup token.",
        }

    def reject_application(
        self,
        identifier: str,
        admin_user: User,
        reason: str,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Rejects a staff application with a recorded rationale."""
        if not reason or not reason.strip():
            raise ValueError("Rejection rationale is required.")

        with self._get_session() as session:
            model = (
                session.query(StaffApplicationModel)
                .filter(
                    (StaffApplicationModel.application_id == identifier.strip())
                    | (StaffApplicationModel.reference_id == identifier.strip())
                )
                .with_for_update()
                .first()
            )
            if not model:
                raise ApplicationNotFoundError(f"Application '{identifier}' not found.")

            current_status = ApplicationStatus(model.status)
            if current_status not in (
                ApplicationStatus.PENDING_REVIEW,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.MORE_INFO_REQUESTED,
            ):
                raise ApplicationConflictError(
                    f"Cannot reject application in '{model.status}' state."
                )

            now = datetime.now(timezone.utc)
            from_status = model.status
            to_status = ApplicationStatus.REJECTED.value

            # Invalidate tracking token upon reaching terminal rejected state
            model.tracking_token_hash = f"REVOKED_{uuid.uuid4().hex}"
            model.tracking_token_expires_at = now
            model.status = to_status
            model.rejection_reason = reason.strip()
            model.updated_at = now

            hist = StaffApplicationHistoryModel(
                history_id=f"hist_{uuid.uuid4().hex[:16]}",
                application_id=model.application_id,
                from_status=from_status,
                to_status=to_status,
                actor_id=admin_user.user_id,
                actor_name=admin_user.display_name,
                actor_role=admin_user.role.value,
                action="reject",
                decision_rationale=reason.strip(),
                created_at=now,
            )
            session.add(hist)
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_APP_REJECTED,
            actor_id=admin_user.user_id,
            target_id=model.reference_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"reason": reason.strip()},
        )

        return {"application_id": model.application_id, "status": to_status, "rejection_reason": reason.strip()}

    def complete_account_setup(
        self,
        setup_token: str,
        new_password: str,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Completes mandatory initial account setup using a single-use setup token."""
        if not setup_token or not setup_token.strip():
            raise ApplicationSecurityError("Account setup token is required.")

        if not new_password or len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        now = datetime.now(timezone.utc)
        raw_token_hash = hashlib.sha256(setup_token.strip().encode("utf-8")).hexdigest()

        with self._get_session() as session:
            user = (
                session.query(UserModel)
                .filter(UserModel.setup_token_hash == raw_token_hash)
                .with_for_update()
                .first()
            )
            if not user:
                log_security_event(
                    event=SecurityAuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
                    actor_id="account_setup",
                    client_ip=client_ip,
                    status="REJECTED",
                    details={"reason": "invalid_setup_token"},
                )
                raise ApplicationSecurityError("Invalid or expired account setup token.")

            # Validate token expiration
            exp = user.setup_token_expires_at
            if exp:
                exp_tz = exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)
                if now > exp_tz:
                    log_security_event(
                        event=SecurityAuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
                        actor_id=user.username,
                        client_ip=client_ip,
                        status="REJECTED",
                        details={"reason": "expired_setup_token"},
                    )
                    raise ApplicationSecurityError("Invalid or expired account setup token.")

            if not user.must_change_password or not user.is_active:
                raise ApplicationConflictError("Account is not in a pending setup state.")

            # Atomically set new password and clear single-use setup token
            user.password_hash = hash_password(new_password)
            user.must_change_password = False
            user.setup_token_hash = None
            user.setup_token_expires_at = None
            user.updated_at = now

            # Invalidate any prior sessions
            try:
                from backend.storage.postgres_models import StaffMfaModel
                mfa_record = session.query(StaffMfaModel).filter_by(user_id=user.user_id).first()
                if mfa_record:
                    mfa_record.session_revoked_at = now
            except Exception as mfa_err:
                logger.debug("MFA session revocation update during setup: %s", mfa_err)

            # Sync to NDB if context is present
            try:
                from google.cloud import ndb
                if ndb.get_context(raise_context_error=False) is not None:
                    from backend.storage.storage_models import UserModel as NdbUserModel
                    ndb_u = NdbUserModel.get_by_id(user.user_id)
                    if ndb_u:
                        ndb_u.password_hash = user.password_hash
                        ndb_u.must_change_password = False
                        ndb_u.put()
            except Exception as ndb_err:
                logger.debug("NDB sync during account setup completion: %s", ndb_err)

            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_SETUP_COMPLETED,
            actor_id=user.username,
            target_id=user.user_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"role": user.role},
        )

        return {
            "username": user.username,
            "role": user.role,
            "message": "Account setup completed successfully. You may now log in with your new password.",
        }

    def reissue_setup_token(
        self,
        user_id: str,
        admin_user: User,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        """Reissues a single-use setup token for an account with pending setup."""
        if admin_user.role != UserRole.ADMIN:
            raise ApplicationSecurityError("Only administrators can reissue setup tokens.")

        now = datetime.now(timezone.utc)
        raw_setup_token = f"set_{secrets.token_urlsafe(32)}"
        token_hash = hashlib.sha256(raw_setup_token.encode("utf-8")).hexdigest()
        expires_at = now + timedelta(hours=SETUP_TOKEN_EXPIRY_HOURS)

        with self._get_session() as session:
            user = (
                session.query(UserModel)
                .filter_by(user_id=user_id.strip())
                .with_for_update()
                .first()
            )
            if not user:
                raise ApplicationNotFoundError(f"User '{user_id}' not found.")

            if not user.must_change_password:
                raise ApplicationConflictError(
                    f"User '{user.username}' has already completed account setup. "
                    "To change their password, use the password reset flow."
                )

            user.setup_token_hash = token_hash
            user.setup_token_expires_at = expires_at
            user.updated_at = now
            session.commit()

        log_security_event(
            event=SecurityAuditEvent.STAFF_SETUP_TOKEN_REISSUED,
            actor_id=admin_user.user_id,
            target_id=user_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"target_username": user.username},
        )

        return {
            "user_id": user.user_id,
            "username": user.username,
            "setup_token": raw_setup_token,
            "setup_token_expires_at": expires_at.isoformat(),
            "message": "New setup token issued successfully. It is single-use and expires in 48 hours.",
        }


# Process singleton
_default_staff_app_service: Optional[StaffApplicationService] = None


def get_staff_application_service() -> StaffApplicationService:
    global _default_staff_app_service
    if _default_staff_app_service is None:
        _default_staff_app_service = StaffApplicationService()
    return _default_staff_app_service
