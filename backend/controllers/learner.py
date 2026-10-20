"""Learner controller for HealthAware.

Provides authenticated cross-device learning progress synchronization
strictly isolated by the authenticated user's server identity.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from flask import Response, jsonify, request

from backend.controllers.auth import get_current_user, role_required
from backend.controllers.base import BaseHandler
from backend.domain.domain_objects import UserRole
from backend.storage.db import get_db_session
from backend.storage.postgres_models import LearnerProgressModel

logger = logging.getLogger(__name__)

MAX_PAYLOAD_BYTES = 65536  # 64 KB limit
MAX_LESSON_IDS = 500
MAX_ACTIVITY_IDS = 500
MAX_MILESTONES = 100


def _validate_progress_payload(data: dict[str, Any]) -> tuple[bool, str]:
    """Validate incoming learner progress data structure and bounds."""
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object."

    completed_lessons = data.get("completed_lesson_ids", [])
    if not isinstance(completed_lessons, list) or len(completed_lessons) > MAX_LESSON_IDS:
        return False, f"completed_lesson_ids must be a list with <= {MAX_LESSON_IDS} items."
    for item in completed_lessons:
        if not isinstance(item, str) or len(item) > 64:
            return False, "Each completed_lesson_id must be a string up to 64 chars."

    completed_activities = data.get("completed_activity_ids", [])
    if not isinstance(completed_activities, list) or len(completed_activities) > MAX_ACTIVITY_IDS:
        return False, f"completed_activity_ids must be a list with <= {MAX_ACTIVITY_IDS} items."
    for item in completed_activities:
        if not isinstance(item, str) or len(item) > 64:
            return False, "Each completed_activity_id must be a string up to 64 chars."

    milestones = data.get("achieved_milestones", [])
    if not isinstance(milestones, list) or len(milestones) > MAX_MILESTONES:
        return False, f"achieved_milestones must be a list with <= {MAX_MILESTONES} items."
    for m in milestones:
        if not isinstance(m, dict) or "id" not in m:
            return False, "Each milestone item must be an object with an 'id' property."

    last_lesson = data.get("last_lesson")
    if last_lesson is not None and not isinstance(last_lesson, dict):
        return False, "last_lesson must be an object or null."

    return True, ""


def _merge_progress(server_record: LearnerProgressModel | None, client_data: dict[str, Any]) -> dict[str, Any]:
    """Execute deterministic merge policy between server and client progress."""
    server_lessons = list(server_record.completed_lesson_ids or []) if server_record else []
    server_activities = list(server_record.completed_activity_ids or []) if server_record else []
    server_milestones = list(server_record.achieved_milestones or []) if server_record else []
    server_last_lesson = server_record.last_lesson if server_record else None

    client_lessons = client_data.get("completed_lesson_ids") or []
    client_activities = client_data.get("completed_activity_ids") or []
    client_milestones = client_data.get("achieved_milestones") or []
    client_last_lesson = client_data.get("last_lesson")

    # 1. Lessons: Set Union
    merged_lessons = sorted(list(set(server_lessons) | set(client_lessons)))

    # 2. Activities: Set Union
    merged_activities = sorted(list(set(server_activities) | set(client_activities)))

    # 3. Milestones: Dedup by id, keep earliest achievedAt
    milestone_map: dict[str, dict[str, Any]] = {}
    for m in server_milestones + client_milestones:
        if not isinstance(m, dict) or "id" not in m:
            continue
        m_id = str(m["id"])
        if m_id not in milestone_map:
            milestone_map[m_id] = m
        else:
            cur_time = str(milestone_map[m_id].get("achievedAt") or "")
            new_time = str(m.get("achievedAt") or "")
            if new_time and (not cur_time or new_time < cur_time):
                milestone_map[m_id] = m
    merged_milestones = list(milestone_map.values())

    # 4. Last lesson: Compare timestamps, then completion ratio
    merged_last_lesson = server_last_lesson
    if client_last_lesson and not server_last_lesson:
        merged_last_lesson = client_last_lesson
    elif client_last_lesson and server_last_lesson:
        c_time = str(client_last_lesson.get("updatedAt") or "")
        s_time = str(server_last_lesson.get("updatedAt") or "")
        if c_time and s_time:
            if c_time >= s_time:
                merged_last_lesson = client_last_lesson
            else:
                merged_last_lesson = server_last_lesson
        else:
            c_ratio = (int(client_last_lesson.get("cardIndex", 0)) + 1) / max(
                int(client_last_lesson.get("totalCards", 1)), 1
            )
            s_ratio = (int(server_last_lesson.get("cardIndex", 0)) + 1) / max(
                int(server_last_lesson.get("totalCards", 1)), 1
            )
            merged_last_lesson = client_last_lesson if c_ratio >= s_ratio else server_last_lesson

    return {
        "version": 1,
        "completed_lesson_ids": merged_lessons,
        "completed_activity_ids": merged_activities,
        "achieved_milestones": merged_milestones,
        "last_lesson": merged_last_lesson,
    }


class LearnerProgressHandler(BaseHandler):
    """GET and PUT /api/v1/learner/progress — Sync cross-device learner progress."""

    decorators = [role_required(UserRole.LEARNER)]

    def get(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        with get_db_session() as db_sess:
            record = (
                db_sess.query(LearnerProgressModel)
                .filter_by(user_id=user.user_id)
                .first()
            )
            if record is None:
                return self.render_json({
                    "version": 1,
                    "last_lesson": None,
                    "completed_lesson_ids": [],
                    "completed_activity_ids": [],
                    "achieved_milestones": [],
                    "updated_at": None,
                })

            return self.render_json({
                "version": record.version,
                "last_lesson": record.last_lesson,
                "completed_lesson_ids": record.completed_lesson_ids or [],
                "completed_activity_ids": record.completed_activity_ids or [],
                "achieved_milestones": record.achieved_milestones or [],
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            })

    def put(self) -> tuple[Response, int]:
        user = get_current_user()
        if user is None:
            return self.render_error("UNAUTHORIZED", "Authentication required.", 401)

        raw_data = request.get_data()
        if len(raw_data) > MAX_PAYLOAD_BYTES:
            return self.render_error("PAYLOAD_TOO_LARGE", f"Payload exceeds {MAX_PAYLOAD_BYTES} bytes limit.", 413)

        data = request.get_json(silent=True)
        if data is None:
            return self.render_error("BAD_REQUEST", "JSON body required.", 400)

        valid, error_msg = _validate_progress_payload(data)
        if not valid:
            return self.render_error("BAD_REQUEST", error_msg, 400)

        with get_db_session() as db_sess:
            record = (
                db_sess.query(LearnerProgressModel)
                .filter_by(user_id=user.user_id)
                .first()
            )

            merged = _merge_progress(record, data)

            now = datetime.datetime.now(datetime.timezone.utc)
            if record is None:
                record = LearnerProgressModel(
                    progress_id=f"prog_{uuid.uuid4().hex[:16]}",
                    user_id=user.user_id,
                    version=merged["version"],
                    last_lesson=merged["last_lesson"],
                    completed_lesson_ids=merged["completed_lesson_ids"],
                    completed_activity_ids=merged["completed_activity_ids"],
                    achieved_milestones=merged["achieved_milestones"],
                    updated_at=now,
                )
                db_sess.add(record)
            else:
                record.last_lesson = merged["last_lesson"]
                record.completed_lesson_ids = merged["completed_lesson_ids"]
                record.completed_activity_ids = merged["completed_activity_ids"]
                record.achieved_milestones = merged["achieved_milestones"]
                record.updated_at = now

            db_sess.commit()

            merged["updated_at"] = record.updated_at.isoformat() if record.updated_at else None
            return self.render_json(merged)
