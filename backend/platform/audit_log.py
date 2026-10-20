"""Structured security audit logging for HealthAware authentication and authorization events.

Outputs structured, machine-parsable log entries formatted as:
    [SECURITY_AUDIT] {"timestamp": "...", "event": "...", "actor_id": "...", ...}

Complies with OWASP logging guidelines:
- Structured application stdout logging formatted for external log aggregation services.
- Note: Application logs are not cryptographically tamper-evident ledgers.
- Never logs plaintext passwords, TOTP secrets, recovery codes, or session tokens.
- Captures client IP, actor identity, event outcome, and timestamps.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("healthaware.security_audit")


class SecurityAuditEvent:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGIN_THROTTLED = "LOGIN_THROTTLED"
    MFA_REQUIRED = "MFA_REQUIRED"
    MFA_VERIFY_SUCCESS = "MFA_VERIFY_SUCCESS"
    MFA_VERIFY_FAILED = "MFA_VERIFY_FAILED"
    MFA_REPLAY_REJECTED = "MFA_REPLAY_REJECTED"
    MFA_RECOVERY_CODE_USED = "MFA_RECOVERY_CODE_USED"
    MFA_ENROLL_INITIATED = "MFA_ENROLL_INITIATED"
    MFA_ENROLL_CONFIRMED = "MFA_ENROLL_CONFIRMED"
    MFA_DISABLED = "MFA_DISABLED"
    MFA_ADMIN_RESET = "MFA_ADMIN_RESET"
    THROTTLE_ADMIN_RESET = "THROTTLE_ADMIN_RESET"
    SESSION_REVOKED = "SESSION_REVOKED"
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    STAFF_APP_SUBMITTED = "STAFF_APP_SUBMITTED"
    STAFF_APP_CLAIMED = "STAFF_APP_CLAIMED"
    STAFF_APP_CHECKLIST_UPDATED = "STAFF_APP_CHECKLIST_UPDATED"
    STAFF_APP_INFO_REQUESTED = "STAFF_APP_INFO_REQUESTED"
    STAFF_APP_INFO_RESPONDED = "STAFF_APP_INFO_RESPONDED"
    STAFF_APP_APPROVED = "STAFF_APP_APPROVED"
    STAFF_APP_REJECTED = "STAFF_APP_REJECTED"
    STAFF_APP_WITHDRAWN = "STAFF_APP_WITHDRAWN"
    STAFF_ACCOUNT_PROVISIONED = "STAFF_ACCOUNT_PROVISIONED"
    STAFF_SETUP_COMPLETED = "STAFF_SETUP_COMPLETED"
    STAFF_SETUP_TOKEN_REISSUED = "STAFF_SETUP_TOKEN_REISSUED"
    LOGIN_BLOCKED_PENDING_SETUP = "LOGIN_BLOCKED_PENDING_SETUP"


# In-memory buffer of recent audit events for programmatic inspection in tests
_recent_events: list[dict[str, Any]] = []


def log_security_event(
    event: str,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Records a structured security audit event."""
    sanitized_details = dict(details or {})
    # Strip any potential sensitive keys
    for sensitive_key in ("password", "token", "secret", "totp_code", "recovery_code"):
        if sensitive_key in sanitized_details:
            sanitized_details[sensitive_key] = "[REDACTED]"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor_id": actor_id or "anonymous",
        "target_id": target_id or actor_id or "none",
        "client_ip": client_ip or "unknown",
        "status": status,
        "details": sanitized_details,
    }

    # Maintain recent buffer (bounded to 200 items)
    _recent_events.append(record)
    if len(_recent_events) > 200:
        _recent_events.pop(0)

    log_line = f"[SECURITY_AUDIT] {json.dumps(record, separators=(',', ':'))}"
    if status == "SUCCESS":
        logger.info(log_line)
    elif status in ("FAILURE", "THROTTLED", "REJECTED"):
        logger.warning(log_line)
    else:
        logger.error(log_line)

    return record


def get_recent_audit_events() -> list[dict[str, Any]]:
    """Returns a copy of recently recorded audit events (primarily for verification)."""
    return list(_recent_events)


def clear_audit_events() -> None:
    """Clears the in-memory audit event buffer."""
    _recent_events.clear()
