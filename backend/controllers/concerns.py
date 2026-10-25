"""Citizen intake and private tracking controllers for Report a Concern."""

from __future__ import annotations

import logging
from typing import Any

from flask import Response, jsonify, request
from flask.views import MethodView

from backend.domain.concern_models import (
    ALLOWED_STATES,
    CONCERN_CATEGORY_LABELS,
    STATUS_DISPLAY_LABELS,
    ConcernCategory,
    ConcernDuration,
    ConcernStatus,
)
from backend.controllers.auth import get_current_user
from backend.domain.domain_objects import UserRole
from backend.platform.attachment_storage import AttachmentStorageService
from backend.platform.rate_limiter import limiter
from backend.storage.concern_repository import ConcernRepository
from backend.storage.db import get_db_session
from backend.storage.postgres_models import (
    ConcernAttachmentModel,
    StaffJurisdictionModel,
)

logger = logging.getLogger(__name__)


class ConcernSubmitHandler(MethodView):
    """Citizen intake endpoint: POST /api/v1/concerns."""

    decorators = [limiter.limit("5 per 10 minutes")]

    def post(self):

        # Support both multipart form data (with optional file) and json
        data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})

        category_str = data.get("category", "").strip()
        state = data.get("state", "").strip()
        district = data.get("district", "").strip()
        municipality = data.get("municipality", "").strip() or None
        locality = data.get("locality", "").strip()
        description = data.get("description", "").strip()
        duration_str = data.get("duration", "").strip()

        # Validation
        if category_str not in [c.value for c in ConcernCategory]:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid category. Must be one of: {list(c.value for c in ConcernCategory)}",
                }
            }), 400

        if state not in ALLOWED_STATES:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "State must be Andhra Pradesh or Telangana.",
                }
            }), 400

        if not district or len(district) > 100:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "District is required and must not exceed 100 characters.",
                }
            }), 400

        if not locality or len(locality) > 500:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Locality/landmark is required and must not exceed 500 characters.",
                }
            }), 400

        if not description or len(description) > 2000:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Description is required and must not exceed 2000 characters.",
                }
            }), 400

        if duration_str not in [d.value for d in ConcernDuration]:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid duration. Must be one of: {list(d.value for d in ConcernDuration)}",
                }
            }), 400

        lat_val = None
        lon_val = None
        if data.get("latitude"):
            try:
                lat_val = float(data["latitude"])
                if not (-90.0 <= lat_val <= 90.0):
                    raise ValueError()
            except Exception:
                return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid latitude."}}), 400

        if data.get("longitude"):
            try:
                lon_val = float(data["longitude"])
                if not (-180.0 <= lon_val <= 180.0):
                    raise ValueError()
            except Exception:
                return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid longitude."}}), 400

        # Check for optional photo uploads (supports both "photos" list and legacy "photo" single file)
        photo_files = []
        if request.files:
            photo_files = request.files.getlist("photos")
            if not photo_files and "photo" in request.files:
                single_photo = request.files.get("photo")
                if single_photo:
                    photo_files = [single_photo]

        if len(photo_files) > 5:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "A maximum of 5 photo attachments is permitted per concern.",
                }
            }), 400

        attachments_meta = []
        if photo_files:
            storage = AttachmentStorageService()
            for pf in photo_files:
                if pf and pf.filename:
                    try:
                        file_bytes = pf.read()
                        storage_key, mime_type, file_size, checksum = storage.store_attachment(
                            file_bytes, pf.filename
                        )
                        attachments_meta.append({
                            "storage_key": storage_key,
                            "mime_type": mime_type,
                            "file_size": file_size,
                            "checksum": checksum,
                            "filename": pf.filename,
                        })
                    except ValueError as ve:
                        return jsonify({"error": {"code": "INVALID_ATTACHMENT", "message": str(ve)}}), 400

        with get_db_session() as session:
            report, raw_token = ConcernRepository.create_report(
                session=session,
                category=category_str,
                state=state,
                district=district,
                locality=locality,
                description=description,
                duration=duration_str,
                municipality=municipality,
                latitude=lat_val,
                longitude=lon_val,
            )

            for meta in attachments_meta:
                ConcernRepository.add_attachment(
                    session=session,
                    report_id=report.report_id,
                    storage_key=meta["storage_key"],
                    content_type=meta["mime_type"],
                    file_size_bytes=meta["file_size"],
                    sha256_checksum=meta["checksum"],
                    original_filename=meta["filename"],
                )

            ref_id = report.reference_id

        user = get_current_user()
        email_sent = False
        user_email = user.username if (user and "@" in getattr(user, "username", "")) else None
        if user_email:
            from backend.platform.email_service import get_email_service
            email_svc = get_email_service()
            res = email_svc.send_concern_tracking(
                to_email=user_email,
                reference_id=ref_id,
                tracking_token=raw_token,
                tracking_url=f"/track?reference_id={ref_id}",
            )
            email_sent = res.success

        delivery_notice = (
            "A copy of your tracking credentials was sent to your verified account email."
            if email_sent
            else "Anonymous submission. Save your Reference ID and Tracking Token now; they cannot be recovered after leaving this screen."
        )

        # Return reference ID and tracking token once
        return jsonify({
            "message": "Your concern has been received by HealthAware.",
            "notice": "This reference confirms intake by HealthAware. It does not represent an official municipal government filing.",
            "delivery_notice": delivery_notice,
            "email_sent": email_sent,
            "data": {
                "reference_id": ref_id,
                "tracking_token": raw_token,
                "status": "received",
                "status_label": STATUS_DISPLAY_LABELS[ConcernStatus.RECEIVED],
                "created_at": report.created_at.isoformat() if report.created_at else None,
            }
        }), 201


class ConcernTrackHandler(MethodView):
    """Citizen private tracking endpoint: POST /api/v1/concerns/track or GET/POST /api/v1/concerns/<report_id>/track."""

    decorators = [limiter.limit("10 per 15 minutes")]

    def _handle_tracking(self, reference_id: str, tracking_token: str):
        if not reference_id or not tracking_token:
            return jsonify({
                "error": {
                    "code": "MISSING_CREDENTIALS",
                    "message": "Both reference ID and private tracking token are required to view report status.",
                }
            }), 400

        with get_db_session() as session:
            report = ConcernRepository.verify_and_get_for_citizen(session, reference_id, tracking_token)
            if not report:
                return jsonify({
                    "error": {
                        "code": "UNAUTHORIZED_OR_NOT_FOUND",
                        "message": "Invalid reference ID or tracking token. Please verify your details.",
                    }
                }), 404

            # Prepare safe citizen response: NO internal notes, NO staff IDs
            timeline = []
            for ev in report.events:
                timeline.append({
                    "status": ev.to_status,
                    "status_label": STATUS_DISPLAY_LABELS.get(ConcernStatus(ev.to_status), ev.to_status),
                    "timestamp": ev.created_at.isoformat() if ev.created_at else None,
                    "public_notes": ev.public_notes,
                })

            attachments = []
            for att in report.attachments:
                attachments.append({
                    "attachment_id": att.attachment_id,
                    "content_type": att.content_type,
                    "file_size_bytes": att.file_size_bytes,
                    "uploaded_at": att.created_at.isoformat() if att.created_at else None,
                })

            status_enum = ConcernStatus(report.status)

            return jsonify({
                "data": {
                    "reference_id": report.reference_id,
                    "status": report.status,
                    "status_label": STATUS_DISPLAY_LABELS.get(status_enum, report.status),
                    "category": report.category,
                    "category_label": CONCERN_CATEGORY_LABELS.get(ConcernCategory(report.category), report.category),
                    "state": report.state,
                    "district": report.district,
                    "municipality": report.municipality or "Not specified",
                    "locality": report.locality,
                    "description": report.description,
                    "duration": report.duration,
                    "citizen_reply_requested": report.citizen_reply_requested,
                    "resolution_notes": report.resolution_notes if report.status == ConcernStatus.RESOLVED.value else None,
                    "rejection_reason": report.rejection_reason if report.status == ConcernStatus.REJECTED.value else None,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "timeline": timeline,
                    "attachments": attachments,
                }
            }), 200

    def get(self, report_id: str | None = None):
        reference_id = (report_id or request.args.get("reference_id") or "").strip().upper()
        tracking_token = (request.headers.get("X-Tracking-Token") or request.args.get("tracking_token") or "").strip()
        return self._handle_tracking(reference_id, tracking_token)

    def post(self, report_id: str | None = None):
        payload = request.get_json(silent=True) or {}
        reference_id = (report_id or payload.get("reference_id") or "").strip().upper()
        tracking_token = (payload.get("tracking_token") or request.headers.get("X-Tracking-Token") or "").strip()
        return self._handle_tracking(reference_id, tracking_token)


class ConcernCitizenReplyHandler(MethodView):
    """Citizen additional information endpoint: POST /api/v1/concerns/track/reply."""

    def post(self):
        payload = request.get_json(silent=True) or {}
        reference_id = payload.get("reference_id", "").strip().upper()
        tracking_token = payload.get("tracking_token", "").strip()
        reply_text = payload.get("reply_text", "").strip()

        if not reference_id or not tracking_token or not reply_text:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Reference ID, tracking token, and reply text are required.",
                }
            }), 400

        if len(reply_text) > 2000:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Reply text must not exceed 2000 characters.",
                }
            }), 400

        with get_db_session() as session:
            report = ConcernRepository.verify_and_get_for_citizen(session, reference_id, tracking_token)
            if not report:
                return jsonify({
                    "error": {
                        "code": "UNAUTHORIZED_OR_NOT_FOUND",
                        "message": "Invalid reference ID or tracking token.",
                    }
                }), 404

            ConcernRepository.citizen_add_response(session, report, reply_text)

        return jsonify({
            "message": "Your response has been added to your HealthAware report.",
        }), 200


class ConcernAttachmentHandler(MethodView):
    """Secure attachment retrieval: GET /api/v1/concerns/<report_id>/attachments/<attachment_id>."""

    def get(self, report_id: str, attachment_id: str):
        token = request.headers.get("X-Tracking-Token", "").strip()
        user = get_current_user()

        with get_db_session() as session:
            report = ConcernRepository.get_by_id(session, report_id)
            if not report:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found."}}), 404

            # Authorization check: valid tracking token OR authorized staff (with jurisdiction scoping)
            authorized = False
            if token and ConcernRepository.verify_and_get_for_citizen(session, report.reference_id, token):
                authorized = True
            elif user is not None:
                if user.role in (UserRole.ADMIN, UserRole.CASE_HANDLER):
                    authorized = True
                elif user.role == UserRole.JURISDICTION_OFFICER:
                    jurisdictions = session.query(StaffJurisdictionModel).filter_by(user_id=user.user_id).all()
                    for j in jurisdictions:
                        if j.state == report.state and j.district == report.district:
                            if not j.municipality or j.municipality == report.municipality:
                                authorized = True
                                break

            if not authorized:
                return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Access denied to attachment."}}), 403

            att = session.query(ConcernAttachmentModel).filter_by(
                attachment_id=attachment_id, report_id=report_id
            ).first()
            if not att:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Attachment not found."}}), 404

            storage = AttachmentStorageService()
            file_bytes = storage.read_attachment_bytes(att.storage_key)
            if not file_bytes:
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Attachment file missing."}}), 404

            response = Response(file_bytes, mimetype=att.content_type)
            response.headers["Cache-Control"] = "private, no-store, max-age=0"
            return response
