"""Controllers for public staff application intake, tracking, and administrator vetting workflows."""

from __future__ import annotations

import logging
from typing import Any

from flask import Response, request

from backend.controllers.auth import get_current_user, role_required
from backend.controllers.base import BaseHandler
from backend.domain.domain_objects import UserRole
from backend.domain.staff_application_service import (
    ApplicationConflictError,
    ApplicationNotFoundError,
    ApplicationSecurityError,
    get_staff_application_service,
)
from backend.platform.rate_limiter import get_trusted_client_ip, limiter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public Applicant Endpoints
# ---------------------------------------------------------------------------


class StaffApplicationSubmitHandler(BaseHandler):
    """POST /api/v1/staff/apply — Submit a public staff application."""

    decorators = [limiter.limit("20 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        required_fields = (
            "applicant_name",
            "applicant_email",
            "requested_role",
            "statement_of_purpose",
            "evidence_standards_acknowledged",
            "child_safety_acknowledged",
        )
        for field in required_fields:
            if field not in data:
                return self.render_error("BAD_REQUEST", f"Missing required field: {field}", 400)

        service = get_staff_application_service()
        try:
            app, raw_token = service.submit_application(
                applicant_name=str(data.get("applicant_name", "")),
                applicant_email=str(data.get("applicant_email", "")),
                requested_role=str(data.get("requested_role", "")),
                statement_of_purpose=str(data.get("statement_of_purpose", "")),
                evidence_standards_acknowledged=bool(data.get("evidence_standards_acknowledged")),
                child_safety_acknowledged=bool(data.get("child_safety_acknowledged")),
                applicant_phone=str(data.get("applicant_phone", "")) if data.get("applicant_phone") else None,
                organization=str(data.get("organization", "")) if data.get("organization") else None,
                professional_title=str(data.get("professional_title", "")) if data.get("professional_title") else None,
                credential_reference=str(data.get("credential_reference", "")) if data.get("credential_reference") else None,
                portfolio_url=str(data.get("portfolio_url", "")) if data.get("portfolio_url") else None,
                client_ip=get_trusted_client_ip(),
            )
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except Exception as exc:
            logger.error("Failed to submit staff application: %s", exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Application intake service temporarily unavailable.", 503)

        email_sent = False
        try:
            from backend.platform.email_service import get_email_service
            email_svc = get_email_service()
            res = email_svc.send_staff_application_tracking(
                to_email=app.applicant_email,
                applicant_name=app.applicant_name,
                reference_id=app.reference_id,
                tracking_token=raw_token,
                tracking_url=f"/staff/application-status?reference_id={app.reference_id}",
            )
            email_sent = res.success
        except Exception:
            pass

        return self.render_json(
            {
                "reference_id": app.reference_id,
                "tracking_token": raw_token,
                "status": app.status.value,
                "email_sent": email_sent,
                "message": (
                    "Staff application submitted successfully. "
                    "Save your Reference ID and Tracking Token to check review progress."
                ),
            },
            status_code=201,
        )


class StaffApplicationRecoverHandler(BaseHandler):
    """POST /api/v1/staff/applications/recover — Secure tracking token recovery."""

    decorators = [limiter.limit("10 per hour")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        email = (data.get("applicant_email") or data.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return self.render_error("BAD_REQUEST", "Valid applicant email address is required.", 400)

        service = get_staff_application_service()
        try:
            app, raw_token, email_sent = service.recover_application_tracking(
                applicant_email=email,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json({
                "reference_id": app.reference_id,
                "tracking_token": raw_token,
                "email_sent": email_sent,
                "message": (
                    "A new tracking token has been generated. "
                    + ("A recovery copy was emailed to your address." if email_sent else "Please copy and store it securely now.")
                ),
            })
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except Exception as exc:
            logger.error("Error recovering staff tracking token for '%s': %s", email, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Tracking recovery service temporarily unavailable.", 503)


class StaffApplicationTrackHandler(BaseHandler):
    """POST /api/v1/staff/applications/track — Secure applicant status inspection."""

    decorators = [limiter.limit("60 per minute")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        reference_id = (
            data.get("reference_id")
            or request.args.get("reference_id")
            or ""
        ).strip()
        tracking_token = (
            data.get("tracking_token")
            or request.headers.get("X-Application-Token")
            or request.args.get("token")
            or ""
        ).strip()

        if not reference_id or not tracking_token:
            return self.render_error(
                "BAD_REQUEST",
                "reference_id and tracking_token are required.",
                400,
            )

        service = get_staff_application_service()
        try:
            app_data = service.get_application_for_applicant(reference_id, tracking_token)
            return self.render_json(app_data)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationSecurityError as exc:
            return self.render_error("UNAUTHORIZED", str(exc), 401)
        except Exception as exc:
            logger.error("Error retrieving application status for %s: %s", reference_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Status service temporarily unavailable.", 503)


class StaffApplicationRespondHandler(BaseHandler):
    """POST /api/v1/staff/applications/<reference_id>/respond — Submit follow-up information."""

    def post(self, reference_id: str) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        tracking_token = (
            data.get("tracking_token")
            or request.headers.get("X-Application-Token")
            or ""
        ).strip()
        applicant_notes = str(data.get("applicant_notes") or data.get("notes") or "").strip()

        if not tracking_token or not applicant_notes:
            return self.render_error(
                "BAD_REQUEST",
                "tracking_token and applicant_notes are required.",
                400,
            )

        service = get_staff_application_service()
        try:
            result = service.respond_to_info_request(
                reference_id=reference_id,
                raw_token=tracking_token,
                applicant_notes=applicant_notes,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationSecurityError as exc:
            return self.render_error("UNAUTHORIZED", str(exc), 401)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
        except Exception as exc:
            logger.error("Error submitting response for application %s: %s", reference_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Service temporarily unavailable.", 503)


class StaffApplicationWithdrawHandler(BaseHandler):
    """POST /api/v1/staff/applications/<reference_id>/withdraw — Withdraw an active application."""

    def post(self, reference_id: str) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        tracking_token = (
            data.get("tracking_token")
            or request.headers.get("X-Application-Token")
            or ""
        ).strip()
        rationale = str(data.get("rationale") or "").strip() or None

        if not tracking_token:
            return self.render_error("BAD_REQUEST", "tracking_token is required.", 400)

        service = get_staff_application_service()
        try:
            result = service.withdraw_application(
                reference_id=reference_id,
                raw_token=tracking_token,
                rationale=rationale,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationSecurityError as exc:
            return self.render_error("UNAUTHORIZED", str(exc), 401)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except Exception as exc:
            logger.error("Error withdrawing application %s: %s", reference_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Service temporarily unavailable.", 503)


# ---------------------------------------------------------------------------
# Administrator & Reviewer Queue Endpoints
# ---------------------------------------------------------------------------


class AdminStaffApplicationListHandler(BaseHandler):
    """GET /api/v1/admin/staff-applications — List staff applications queue with filtering."""

    @role_required(UserRole.ADMIN)
    def get(self) -> tuple[Response, int]:
        status_filter = request.args.get("status")
        search_query = request.args.get("q")

        service = get_staff_application_service()
        try:
            apps = service.list_applications_for_admin(status_filter, search_query)
            return self.render_json({"applications": apps, "total": len(apps)})
        except Exception as exc:
            logger.error("Error listing staff applications: %s", exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to retrieve applications.", 503)


class AdminStaffApplicationDetailHandler(BaseHandler):
    """GET /api/v1/admin/staff-applications/<application_id> — Administrative detail inspection."""

    @role_required(UserRole.ADMIN)
    def get(self, application_id: str) -> tuple[Response, int]:
        service = get_staff_application_service()
        try:
            detail = service.get_application_for_admin(application_id)
            return self.render_json(detail)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except Exception as exc:
            logger.error("Error loading application detail %s: %s", application_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to load application detail.", 503)


class AdminStaffApplicationClaimHandler(BaseHandler):
    """POST /api/v1/admin/staff-applications/<application_id>/claim — Claim review."""

    @role_required(UserRole.ADMIN)
    def post(self, application_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        service = get_staff_application_service()
        try:
            result = service.claim_application(
                identifier=application_id,
                admin_user=current_user,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationSecurityError as exc:
            return self.render_error("FORBIDDEN", str(exc), 403)
        except Exception as exc:
            logger.error("Error claiming application %s: %s", application_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to claim application.", 503)


class AdminStaffApplicationChecklistHandler(BaseHandler):
    """POST /api/v1/admin/staff-applications/<application_id>/checklist — Save verification checklist."""

    @role_required(UserRole.ADMIN)
    def post(self, application_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        data = request.get_json(silent=True) or {}
        checklist_data = data.get("verification_checklist", data)
        internal_notes = data.get("internal_notes")

        service = get_staff_application_service()
        try:
            result = service.update_verification_checklist(
                identifier=application_id,
                admin_user=current_user,
                checklist_data=checklist_data,
                internal_notes=internal_notes,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except Exception as exc:
            logger.error("Error updating checklist %s: %s", application_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to update checklist.", 503)


class AdminStaffApplicationRequestInfoHandler(BaseHandler):
    """POST /api/v1/admin/staff-applications/<application_id>/request-info — Request more information."""

    @role_required(UserRole.ADMIN)
    def post(self, application_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        data = request.get_json(silent=True) or {}
        details = str(data.get("details") or data.get("info_request_details") or "").strip()
        if not details:
            return self.render_error("BAD_REQUEST", "details field is required.", 400)

        service = get_staff_application_service()
        try:
            result = service.request_more_information(
                identifier=application_id,
                admin_user=current_user,
                info_details=details,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
        except Exception as exc:
            logger.error("Error requesting info on application %s: %s", application_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to request info.", 503)


class AdminStaffApplicationApproveHandler(BaseHandler):
    """POST /api/v1/admin/staff-applications/<application_id>/approve — Approve & provision staff account."""

    @role_required(UserRole.ADMIN)
    def post(self, application_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        data = request.get_json(silent=True) or {}
        approved_role = str(data.get("approved_role") or data.get("role") or "").strip().lower()
        if not approved_role:
            return self.render_error("BAD_REQUEST", "approved_role field is required.", 400)

        assigned_jurisdiction = data.get("assigned_jurisdiction")
        rationale = data.get("rationale")

        service = get_staff_application_service()
        try:
            result = service.approve_application(
                identifier=application_id,
                admin_user=current_user,
                approved_role=approved_role,
                assigned_jurisdiction=assigned_jurisdiction,
                rationale=rationale,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationSecurityError as exc:
            return self.render_error("FORBIDDEN", str(exc), 403)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
        except Exception as exc:
            logger.error("Error approving application %s: %s", application_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to approve application.", 503)


class AdminStaffApplicationRejectHandler(BaseHandler):
    """POST /api/v1/admin/staff-applications/<application_id>/reject — Reject application."""

    @role_required(UserRole.ADMIN)
    def post(self, application_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        data = request.get_json(silent=True) or {}
        reason = str(data.get("reason") or data.get("rejection_reason") or "").strip()
        if not reason:
            return self.render_error("BAD_REQUEST", "reason field is required.", 400)

        service = get_staff_application_service()
        try:
            result = service.reject_application(
                identifier=application_id,
                admin_user=current_user,
                reason=reason,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
        except Exception as exc:
            logger.error("Error rejecting application %s: %s", application_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to reject application.", 503)


class StaffAccountCompleteSetupHandler(BaseHandler):
    """POST /api/v1/staff/account/complete-setup — Initial mandatory password setup via single-use token."""

    decorators = [limiter.limit("10 per minute")]

    def post(self) -> tuple[Response, int]:
        data = request.get_json(silent=True) or {}
        setup_token = str(data.get("setup_token") or "").strip()
        new_password = str(data.get("new_password") or "").strip()

        if not setup_token or not new_password:
            return self.render_error("BAD_REQUEST", "setup_token and new_password are required.", 400)

        service = get_staff_application_service()
        try:
            result = service.complete_account_setup(
                setup_token=setup_token,
                new_password=new_password,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationSecurityError as exc:
            return self.render_error("UNAUTHORIZED", str(exc), 401)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except ValueError as exc:
            return self.render_error("BAD_REQUEST", str(exc), 400)
        except Exception as exc:
            logger.error("Error completing account setup: %s", exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Account setup service temporarily unavailable.", 503)


class AdminStaffAccountReissueSetupTokenHandler(BaseHandler):
    """POST /api/v1/admin/staff-users/<user_id>/reissue-setup-token — Reissue single-use setup token."""

    @role_required(UserRole.ADMIN)
    def post(self, user_id: str) -> tuple[Response, int]:
        current_user = get_current_user()
        if not current_user:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        service = get_staff_application_service()
        try:
            result = service.reissue_setup_token(
                user_id=user_id,
                admin_user=current_user,
                client_ip=get_trusted_client_ip(),
            )
            return self.render_json(result)
        except ApplicationNotFoundError as exc:
            return self.render_error("NOT_FOUND", str(exc), 404)
        except ApplicationConflictError as exc:
            return self.render_error("CONFLICT", str(exc), 409)
        except ApplicationSecurityError as exc:
            return self.render_error("FORBIDDEN", str(exc), 403)
        except Exception as exc:
            logger.error("Error reissuing setup token for user %s: %s", user_id, exc)
            return self.render_error("SERVICE_UNAVAILABLE", "Failed to reissue setup token.", 503)
