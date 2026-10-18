"""Repository for Report a Concern and Case Management persistence in PostgreSQL."""

from __future__ import annotations

import hashlib
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from backend.domain.concern_models import (
    ActorType,
    ConcernAttachment,
    ConcernCategory,
    ConcernDuration,
    ConcernReport,
    ConcernStatus,
    ConcernStatusEvent,
)
from backend.storage.postgres_models import (
    ConcernAttachmentModel,
    ConcernReportModel,
    ConcernStatusEventModel,
    StaffJurisdictionModel,
    UserModel,
)


def generate_reference_id() -> str:
    """Generates an unpredictable reference identifier (e.g., HA-2026-X7K92M)."""
    chars = string.ascii_uppercase + string.digits
    rand_part = "".join(secrets.choice(chars) for _ in range(6))
    year = datetime.now(timezone.utc).year
    return f"HA-{year}-{rand_part}"


def generate_tracking_token() -> str:
    """Generates a high-entropy URL-safe private tracking token."""
    return secrets.token_urlsafe(32)


def hash_tracking_token(token: str) -> str:
    """Computes SHA-256 hash of the tracking token for storage at rest."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


class ConcernRepository:
    """Data access methods for concerns, audit events, and jurisdictions."""

    @staticmethod
    def create_report(
        session: Session,
        category: str,
        state: str,
        district: str,
        locality: str,
        description: str,
        duration: str,
        municipality: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Tuple[ConcernReportModel, str]:
        """Creates a new concern report with unpredictable ref ID and private tracking token.
        
        Returns:
            (ConcernReportModel, raw_tracking_token)
        """
        report_id = f"cr_{uuid.uuid4().hex}"
        reference_id = generate_reference_id()
        raw_token = generate_tracking_token()
        token_hash = hash_tracking_token(raw_token)

        model = ConcernReportModel(
            report_id=report_id,
            reference_id=reference_id,
            token_hash=token_hash,
            category=category,
            state=state,
            district=district,
            municipality=municipality,
            locality=locality,
            latitude=latitude,
            longitude=longitude,
            description=description,
            duration=duration,
            status=ConcernStatus.RECEIVED.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(model)

        # Initial append-only event
        event = ConcernStatusEventModel(
            event_id=f"evt_{uuid.uuid4().hex}",
            report_id=report_id,
            from_status=None,
            to_status=ConcernStatus.RECEIVED.value,
            actor_type=ActorType.CITIZEN.value,
            actor_id=None,
            actor_name="Citizen Submitter",
            public_notes="Your concern has been received by HealthAware and registered in the case management system.",
            internal_notes="Direct citizen submission via /report intake.",
            created_at=datetime.now(timezone.utc),
        )
        session.add(event)
        session.flush()

        return model, raw_token

    @staticmethod
    def add_attachment(
        session: Session,
        report_id: str,
        storage_key: str,
        content_type: str,
        file_size_bytes: int,
        sha256_checksum: str,
        original_filename: Optional[str] = None,
        uploaded_by: str = "citizen",
    ) -> ConcernAttachmentModel:
        """Persists attachment metadata linked to a concern report."""
        att = ConcernAttachmentModel(
            attachment_id=f"att_{uuid.uuid4().hex}",
            report_id=report_id,
            storage_key=storage_key,
            original_filename=original_filename,
            content_type=content_type,
            file_size_bytes=file_size_bytes,
            sha256_checksum=sha256_checksum,
            uploaded_by=uploaded_by,
            created_at=datetime.now(timezone.utc),
        )
        session.add(att)
        session.flush()
        return att

    @staticmethod
    def verify_and_get_for_citizen(
        session: Session, reference_id: str, raw_token: str
    ) -> Optional[ConcernReportModel]:
        """Authenticates citizen tracking lookup using constant-time token hash comparison."""
        token_hash = hash_tracking_token(raw_token)
        ref = reference_id.strip().upper()
        report = (
            session.query(ConcernReportModel)
            .filter(
                (ConcernReportModel.reference_id == ref) |
                (ConcernReportModel.report_id == reference_id.strip())
            )
            .filter(ConcernReportModel.token_hash == token_hash)
            .first()
        )
        return report

    @staticmethod
    def get_by_id(session: Session, report_id: str) -> Optional[ConcernReportModel]:
        """Retrieves a concern report by internal ID."""
        return session.query(ConcernReportModel).filter_by(report_id=report_id).first()

    @staticmethod
    def get_by_reference(session: Session, reference_id: str) -> Optional[ConcernReportModel]:
        """Retrieves a concern report by reference ID."""
        return session.query(ConcernReportModel).filter_by(reference_id=reference_id.strip().upper()).first()

    @staticmethod
    def list_reports(
        session: Session,
        status: Optional[str] = None,
        category: Optional[str] = None,
        district: Optional[str] = None,
        user: Optional[UserModel] = None,
    ) -> List[ConcernReportModel]:
        """Lists reports with strict authorization scoping for jurisdiction officers."""
        query = session.query(ConcernReportModel)

        # Jurisdiction-scoped authority check
        if user and user.role == "jurisdiction_officer":
            jurisdictions = session.query(StaffJurisdictionModel).filter_by(user_id=user.user_id).all()
            if not jurisdictions:
                # Officer has no assigned jurisdictions; returns empty set safely
                return []
            conditions = []
            for j in jurisdictions:
                if j.municipality:
                    conditions.append(
                        and_(
                            ConcernReportModel.state == j.state,
                            ConcernReportModel.district == j.district,
                            ConcernReportModel.municipality == j.municipality,
                        )
                    )
                else:
                    conditions.append(
                        and_(
                            ConcernReportModel.state == j.state,
                            ConcernReportModel.district == j.district,
                        )
                    )
            query = query.filter(or_(*conditions))

        if status:
            query = query.filter(ConcernReportModel.status == status)
        if category:
            query = query.filter(ConcernReportModel.category == category)
        if district:
            query = query.filter(ConcernReportModel.district == district)

        return query.order_by(desc(ConcernReportModel.created_at)).all()

    @staticmethod
    def update_status(
        session: Session,
        report: ConcernReportModel,
        to_status: str,
        actor_name: str,
        actor_id: Optional[str] = None,
        public_notes: Optional[str] = None,
        internal_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        citizen_reply_requested: bool = False,
    ) -> ConcernStatusEventModel:
        """Transitions report status and records an immutable audit event."""
        from_status = report.status
        report.status = to_status
        report.updated_at = datetime.now(timezone.utc)
        report.citizen_reply_requested = citizen_reply_requested

        if rejection_reason:
            report.rejection_reason = rejection_reason
        if resolution_notes:
            report.resolution_notes = resolution_notes

        event = ConcernStatusEventModel(
            event_id=f"evt_{uuid.uuid4().hex}",
            report_id=report.report_id,
            from_status=from_status,
            to_status=to_status,
            actor_type=ActorType.STAFF.value,
            actor_id=actor_id,
            actor_name=actor_name,
            public_notes=public_notes,
            internal_notes=internal_notes,
            created_at=datetime.now(timezone.utc),
        )
        session.add(event)
        session.flush()
        return event

    @staticmethod
    def assign_handler(
        session: Session,
        report: ConcernReportModel,
        handler_id: str,
        handler_name: str,
        assigned_jurisdiction: Optional[str],
        actor_name: str,
        actor_id: Optional[str] = None,
    ) -> ConcernStatusEventModel:
        """Assigns report to an authorized handler."""
        report.assigned_handler_id = handler_id
        report.assigned_handler_name = handler_name
        report.assigned_jurisdiction = assigned_jurisdiction
        report.updated_at = datetime.now(timezone.utc)

        if report.status == ConcernStatus.RECEIVED.value:
            report.status = ConcernStatus.ASSIGNED.value

        event = ConcernStatusEventModel(
            event_id=f"evt_{uuid.uuid4().hex}",
            report_id=report.report_id,
            from_status=report.status,
            to_status=report.status,
            actor_type=ActorType.STAFF.value,
            actor_id=actor_id,
            actor_name=actor_name,
            public_notes=f"Concern assigned to case handler: {handler_name}.",
            internal_notes=f"Assigned by {actor_name} to {handler_name} ({handler_id}).",
            created_at=datetime.now(timezone.utc),
        )
        session.add(event)
        session.flush()
        return event

    @staticmethod
    def citizen_add_response(
        session: Session,
        report: ConcernReportModel,
        response_text: str,
    ) -> ConcernStatusEventModel:
        """Records an additional information response submitted by citizen."""
        report.citizen_reply_requested = False
        report.updated_at = datetime.now(timezone.utc)

        event = ConcernStatusEventModel(
            event_id=f"evt_{uuid.uuid4().hex}",
            report_id=report.report_id,
            from_status=report.status,
            to_status=report.status,
            actor_type=ActorType.CITIZEN.value,
            actor_id=None,
            actor_name="Citizen Submitter",
            public_notes="Citizen provided additional requested details.",
            internal_notes=f"Citizen response: {response_text.strip()}",
            created_at=datetime.now(timezone.utc),
        )
        session.add(event)
        session.flush()
        return event
