"""Staff case management controllers for HealthAware complaints and municipal oversight."""

from __future__ import annotations

import functools
import logging
import uuid
from typing import Any, Callable

from flask import jsonify, request, session
from flask.views import MethodView

from backend.controllers.auth import get_current_user
from backend.domain.concern_models import (
    CONCERN_CATEGORY_LABELS,
    STATUS_DISPLAY_LABELS,
    ActorType,
    ConcernCategory,
    ConcernStatus,
)
from backend.domain.domain_objects import UserRole
from backend.platform.security import hash_password
from backend.storage.concern_repository import ConcernRepository
from backend.storage.db import get_db_session
from backend.storage.postgres_models import StaffJurisdictionModel, UserModel

logger = logging.getLogger(__name__)

STAFF_ROLES = frozenset({
    UserRole.ADMIN,
    UserRole.CASE_HANDLER,
    UserRole.JURISDICTION_OFFICER,
})


def require_staff(fn: Callable) -> Callable:
    """Ensures request is authenticated and user has an authorized staff role."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Staff authentication required.",
                }
            }), 401
        if user.role not in STAFF_ROLES:
            return jsonify({
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Staff privileges required. Creator Studio users cannot access case management.",
                }
            }), 403
        return fn(*args, **kwargs)
    return wrapper


def require_admin_staff(fn: Callable) -> Callable:
    """Ensures user is an administrator."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Authentication required."}}), 401
        if user.role != UserRole.ADMIN:
            return jsonify({"error": {"code": "FORBIDDEN", "message": "Administrator role required."}}), 403
        return fn(*args, **kwargs)
    return wrapper


class StaffMeHandler(MethodView):
    """GET /api/v1/staff/me - Returns current staff profile and jurisdiction assignments."""

    @require_staff
    def get(self):
        user = get_current_user()
        with get_db_session() as session:
            jurisdictions = session.query(StaffJurisdictionModel).filter_by(user_id=user.user_id).all()
            jurisdiction_list = [
                {
                    "state": j.state,
                    "district": j.district,
                    "municipality": j.municipality,
                }
                for j in jurisdictions
            ]

        return jsonify({
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role.value,
                "jurisdictions": jurisdiction_list,
            }
        }), 200


class StaffConcernListHandler(MethodView):
    """GET /api/v1/staff/concerns - Scoped concern list with filters."""

    @require_staff
    def get(self):
        user = get_current_user()
        status_filter = request.args.get("status")
        category_filter = request.args.get("category")
        district_filter = request.args.get("district")

        with get_db_session() as session:
            # Query PgUser model for relationship queries
            pg_user = session.query(UserModel).filter_by(user_id=user.user_id).first()
            reports = ConcernRepository.list_reports(
                session=session,
                status=status_filter,
                category=category_filter,
                district=district_filter,
                user=pg_user,
            )

            result = []
            for r in reports:
                status_enum = ConcernStatus(r.status)
                result.append({
                    "report_id": r.report_id,
                    "reference_id": r.reference_id,
                    "category": r.category,
                    "category_label": CONCERN_CATEGORY_LABELS.get(ConcernCategory(r.category), r.category),
                    "state": r.state,
                    "district": r.district,
                    "municipality": r.municipality,
                    "locality": r.locality,
                    "description": r.description[:120] + ("..." if len(r.description) > 120 else ""),
                    "duration": r.duration,
                    "status": r.status,
                    "status_label": STATUS_DISPLAY_LABELS.get(status_enum, r.status),
                    "assigned_handler_id": r.assigned_handler_id,
                    "assigned_handler_name": r.assigned_handler_name,
                    "assigned_jurisdiction": r.assigned_jurisdiction,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                })

        return jsonify({"data": result}), 200


class StaffConcernDetailHandler(MethodView):
    """GET /api/v1/staff/concerns/<report_id> - Full report with internal audit history."""

    @require_staff
    def get(self, report_id: str):
        user = get_current_user()
        with get_db_session() as session:
            report = ConcernRepository.get_by_id(session, report_id)
            if not report:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found."}}), 404

            # Enforce jurisdiction scope check for officers
            if user.role == UserRole.JURISDICTION_OFFICER:
                jurisdictions = session.query(StaffJurisdictionModel).filter_by(user_id=user.user_id).all()
                allowed = False
                for j in jurisdictions:
                    if j.state == report.state and j.district == report.district:
                        if not j.municipality or j.municipality == report.municipality:
                            allowed = True
                            break
                if not allowed:
                    return jsonify({
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "Access denied: Report is outside your assigned municipal jurisdiction.",
                        }
                    }), 403

            timeline = []
            for ev in report.events:
                timeline.append({
                    "event_id": ev.event_id,
                    "from_status": ev.from_status,
                    "to_status": ev.to_status,
                    "to_status_label": STATUS_DISPLAY_LABELS.get(ConcernStatus(ev.to_status), ev.to_status),
                    "actor_type": ev.actor_type,
                    "actor_id": ev.actor_id,
                    "actor_name": ev.actor_name,
                    "public_notes": ev.public_notes,
                    "internal_notes": ev.internal_notes,
                    "created_at": ev.created_at.isoformat() if ev.created_at else None,
                })

            attachments = []
            for att in report.attachments:
                attachments.append({
                    "attachment_id": att.attachment_id,
                    "content_type": att.content_type,
                    "file_size_bytes": att.file_size_bytes,
                    "sha256_checksum": att.sha256_checksum,
                    "created_at": att.created_at.isoformat() if att.created_at else None,
                })

            status_enum = ConcernStatus(report.status)

            return jsonify({
                "data": {
                    "report_id": report.report_id,
                    "reference_id": report.reference_id,
                    "category": report.category,
                    "category_label": CONCERN_CATEGORY_LABELS.get(ConcernCategory(report.category), report.category),
                    "state": report.state,
                    "district": report.district,
                    "municipality": report.municipality,
                    "locality": report.locality,
                    "latitude": report.latitude,
                    "longitude": report.longitude,
                    "description": report.description,
                    "duration": report.duration,
                    "status": report.status,
                    "status_label": STATUS_DISPLAY_LABELS.get(status_enum, report.status),
                    "assigned_handler_id": report.assigned_handler_id,
                    "assigned_handler_name": report.assigned_handler_name,
                    "assigned_jurisdiction": report.assigned_jurisdiction,
                    "citizen_reply_requested": report.citizen_reply_requested,
                    "rejection_reason": report.rejection_reason,
                    "resolution_notes": report.resolution_notes,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "updated_at": report.updated_at.isoformat() if report.updated_at else None,
                    "timeline": timeline,
                    "attachments": attachments,
                }
            }), 200


class StaffStatusTransitionHandler(MethodView):
    """POST /api/v1/staff/concerns/<report_id>/status - Transition complaint lifecycle."""

    @require_staff
    def post(self, report_id: str):
        user = get_current_user()
        payload = request.get_json(silent=True) or {}

        to_status_str = payload.get("status", "").strip()
        public_notes = payload.get("public_notes", "").strip() or None
        internal_notes = payload.get("internal_notes", "").strip() or None
        rejection_reason = payload.get("rejection_reason", "").strip() or None
        resolution_notes = payload.get("resolution_notes", "").strip() or None
        citizen_reply_requested = bool(payload.get("citizen_reply_requested", False))

        if to_status_str not in [s.value for s in ConcernStatus]:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid status. Must be one of: {list(s.value for s in ConcernStatus)}",
                }
            }), 400

        with get_db_session() as session:
            report = ConcernRepository.get_by_id(session, report_id)
            if not report:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found."}}), 404

            # Jurisdiction check for officer
            if user.role == UserRole.JURISDICTION_OFFICER:
                jurisdictions = session.query(StaffJurisdictionModel).filter_by(user_id=user.user_id).all()
                allowed = False
                for j in jurisdictions:
                    if j.state == report.state and j.district == report.district:
                        if not j.municipality or j.municipality == report.municipality:
                            allowed = True
                            break
                if not allowed:
                    return jsonify({"error": {"code": "FORBIDDEN", "message": "Outside your assigned jurisdiction."}}), 403

            ConcernRepository.update_status(
                session=session,
                report=report,
                to_status=to_status_str,
                actor_name=user.display_name,
                actor_id=user.user_id,
                public_notes=public_notes,
                internal_notes=internal_notes,
                rejection_reason=rejection_reason,
                resolution_notes=resolution_notes,
                citizen_reply_requested=citizen_reply_requested,
            )

        return jsonify({"message": f"Concern status successfully updated to '{to_status_str}'."}), 200


class StaffAssignHandler(MethodView):
    """POST /api/v1/staff/concerns/<report_id>/assign - Assign case to handler."""

    @require_staff
    def post(self, report_id: str):
        user = get_current_user()
        if user.role == UserRole.JURISDICTION_OFFICER:
            return jsonify({"error": {"code": "FORBIDDEN", "message": "Officers cannot assign cases."}}), 403

        payload = request.get_json(silent=True) or {}
        handler_id = payload.get("handler_id", "").strip()
        handler_name = payload.get("handler_name", "").strip()
        jurisdiction = payload.get("jurisdiction", "").strip() or None

        if not handler_id or not handler_name:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "handler_id and handler_name are required."}}), 400

        with get_db_session() as session:
            report = ConcernRepository.get_by_id(session, report_id)
            if not report:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found."}}), 404

            ConcernRepository.assign_handler(
                session=session,
                report=report,
                handler_id=handler_id,
                handler_name=handler_name,
                assigned_jurisdiction=jurisdiction,
                actor_name=user.display_name,
                actor_id=user.user_id,
            )

        return jsonify({"message": f"Report assigned to {handler_name}."}), 200


class StaffJurisdictionHandler(MethodView):
    """POST /api/v1/staff/jurisdictions - Assign jurisdiction scope to officer (Admin only)."""

    @require_admin_staff
    def post(self):
        payload = request.get_json(silent=True) or {}
        user_id = payload.get("user_id", "").strip()
        state = payload.get("state", "").strip()
        district = payload.get("district", "").strip()
        municipality = payload.get("municipality", "").strip() or None

        if not user_id or not state or not district:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "user_id, state, and district are required."}}), 400

        with get_db_session() as session:
            target_user = session.query(UserModel).filter_by(user_id=user_id).first()
            if not target_user:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found."}}), 404

            existing = session.query(StaffJurisdictionModel).filter_by(
                user_id=user_id, state=state, district=district, municipality=municipality
            ).first()
            if existing:
                return jsonify({"message": "Jurisdiction already assigned to user."}), 200

            jur = StaffJurisdictionModel(
                id=f"jur_{uuid.uuid4().hex}",
                user_id=user_id,
                state=state,
                district=district,
                municipality=municipality,
            )
            session.add(jur)

        return jsonify({"message": "Jurisdiction successfully assigned to officer."}), 201


class StaffHandlersListHandler(MethodView):
    """GET /api/v1/staff/handlers - List staff handlers and officers."""

    @require_staff
    def get(self):
        with get_db_session() as session:
            users = session.query(UserModel).filter(
                UserModel.role.in_([UserRole.ADMIN.value, UserRole.CASE_HANDLER.value, UserRole.JURISDICTION_OFFICER.value]),
                UserModel.is_active.is_(True),
            ).all()

            handlers = [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "role": u.role,
                }
                for u in users
            ]

        return jsonify({"data": handlers}), 200
