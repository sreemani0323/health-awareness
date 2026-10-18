"""Controllers package for the Health Awareness REST API.

Centralises Blueprint definition and URL route registration for API v1.
"""

from __future__ import annotations

from flask import Blueprint

from backend.controllers.admin import (
    AdminOverviewHandler,
    AdminUserListHandler,
    AdminUserRoleHandler,
    AdminUserStatusHandler,
)
from backend.controllers.auth import LoginHandler, LogoutHandler, MeHandler
from backend.controllers.creator import (
    CreatorApproveHandler,
    CreatorLessonDetailHandler,
    CreatorRequestChangesHandler,
    CreatorReviewQueueHandler,
    CreatorSourceListHandler,
    CreatorSubmitHandler,
    CreatorTopicDetailHandler,
    CreatorTopicLessonsHandler,
    CreatorTopicListHandler,
    CreatorVersionDetailHandler,
    CreatorVersionListHandler,
)
from backend.controllers.health import HealthCheckHandler
from backend.controllers.lessons import LessonDetailHandler
from backend.controllers.topics import TopicLessonsHandler, TopicListHandler


def create_api_blueprint() -> Blueprint:
    """Create and configure the v1 REST API blueprint."""
    bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    # --- Public learner endpoints ---

    bp.add_url_rule(
        "/topics",
        view_func=TopicListHandler.as_view("topics_list"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/topics/<topic_id>/lessons",
        view_func=TopicLessonsHandler.as_view("topic_lessons"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/lessons/<lesson_id>",
        view_func=LessonDetailHandler.as_view("lesson_detail"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/health",
        view_func=HealthCheckHandler.as_view("health_check"),
        methods=["GET"],
    )

    # --- Auth endpoints ---

    bp.add_url_rule(
        "/auth/login",
        view_func=LoginHandler.as_view("auth_login"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/auth/logout",
        view_func=LogoutHandler.as_view("auth_logout"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/auth/me",
        view_func=MeHandler.as_view("auth_me"),
        methods=["GET"],
    )

    # --- Creator Studio endpoints ---

    bp.add_url_rule(
        "/creator/topics",
        view_func=CreatorTopicListHandler.as_view("creator_topics_list"),
        methods=["GET", "POST"],
    )
    bp.add_url_rule(
        "/creator/topics/<topic_id>",
        view_func=CreatorTopicDetailHandler.as_view("creator_topic_detail"),
        methods=["GET", "PUT"],
    )
    bp.add_url_rule(
        "/creator/topics/<topic_id>/lessons",
        view_func=CreatorTopicLessonsHandler.as_view("creator_topic_lessons"),
        methods=["GET", "POST"],
    )
    bp.add_url_rule(
        "/creator/lessons/<lesson_id>",
        view_func=CreatorLessonDetailHandler.as_view("creator_lesson_detail"),
        methods=["GET", "PUT", "DELETE"],
    )
    bp.add_url_rule(
        "/creator/lessons/<lesson_id>/versions",
        view_func=CreatorVersionListHandler.as_view("creator_version_list"),
        methods=["GET", "POST"],
    )
    bp.add_url_rule(
        "/creator/versions/<version_id>",
        view_func=CreatorVersionDetailHandler.as_view("creator_version_detail"),
        methods=["GET", "PUT"],
    )
    bp.add_url_rule(
        "/creator/versions/<version_id>/submit",
        view_func=CreatorSubmitHandler.as_view("creator_submit"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/creator/versions/<version_id>/approve",
        view_func=CreatorApproveHandler.as_view("creator_approve"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/creator/versions/<version_id>/request-changes",
        view_func=CreatorRequestChangesHandler.as_view("creator_request_changes"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/creator/reviews",
        view_func=CreatorReviewQueueHandler.as_view("creator_reviews"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/creator/sources",
        view_func=CreatorSourceListHandler.as_view("creator_sources"),
        methods=["GET", "POST"],
    )

    # --- Admin Studio endpoints ---

    bp.add_url_rule(
        "/admin/users",
        view_func=AdminUserListHandler.as_view("admin_users"),
        methods=["GET", "POST"],
    )
    bp.add_url_rule(
        "/admin/users/<user_id>/role",
        view_func=AdminUserRoleHandler.as_view("admin_user_role"),
        methods=["PUT"],
    )
    bp.add_url_rule(
        "/admin/users/<user_id>/status",
        view_func=AdminUserStatusHandler.as_view("admin_user_status"),
        methods=["PUT"],
    )
    bp.add_url_rule(
        "/admin/overview",
        view_func=AdminOverviewHandler.as_view("admin_overview"),
        methods=["GET"],
    )

    # --- Report a Concern (Citizen Intake & Tracking) ---

    from backend.controllers.concerns import (
        ConcernAttachmentHandler,
        ConcernCitizenReplyHandler,
        ConcernSubmitHandler,
        ConcernTrackHandler,
    )

    bp.add_url_rule(
        "/concerns",
        view_func=ConcernSubmitHandler.as_view("concern_submit"),
        methods=["POST"],
    )
    track_view = ConcernTrackHandler.as_view("concern_track")
    bp.add_url_rule(
        "/concerns/track",
        view_func=track_view,
        methods=["POST"],
    )
    bp.add_url_rule(
        "/concerns/<report_id>/track",
        view_func=track_view,
        methods=["GET", "POST"],
    )
    bp.add_url_rule(
        "/concerns/track/reply",
        view_func=ConcernCitizenReplyHandler.as_view("concern_track_reply"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/concerns/<report_id>/attachments/<attachment_id>",
        view_func=ConcernAttachmentHandler.as_view("concern_attachment"),
        methods=["GET"],
    )

    # --- Staff Case Management ---

    from backend.controllers.staff import (
        StaffAssignHandler,
        StaffConcernDetailHandler,
        StaffConcernListHandler,
        StaffHandlersListHandler,
        StaffJurisdictionHandler,
        StaffMeHandler,
        StaffStatusTransitionHandler,
    )

    bp.add_url_rule(
        "/staff/me",
        view_func=StaffMeHandler.as_view("staff_me"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/staff/concerns",
        view_func=StaffConcernListHandler.as_view("staff_concerns_list"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/staff/concerns/<report_id>",
        view_func=StaffConcernDetailHandler.as_view("staff_concern_detail"),
        methods=["GET"],
    )
    bp.add_url_rule(
        "/staff/concerns/<report_id>/status",
        view_func=StaffStatusTransitionHandler.as_view("staff_concern_status"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/staff/concerns/<report_id>/assign",
        view_func=StaffAssignHandler.as_view("staff_concern_assign"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/staff/jurisdictions",
        view_func=StaffJurisdictionHandler.as_view("staff_jurisdiction"),
        methods=["POST"],
    )
    bp.add_url_rule(
        "/staff/handlers",
        view_func=StaffHandlersListHandler.as_view("staff_handlers_list"),
        methods=["GET"],
    )

    return bp
