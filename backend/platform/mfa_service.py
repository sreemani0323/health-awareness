"""Multi-Factor Authentication (MFA / TOTP) service for HealthAware staff.

Conforms strictly to RFC 6238 (TOTP) and OWASP / NIST SP 800-63B standards:
- Base32 secrets encrypted at rest using AES-256 symmetric encryption (Fernet).
- Time-based verification (30s time-step, 6 digits) with replay protection.
- Replay prevention: Tracks the highest verified time-step to prevent code reuse within the valid window.
- Single-use emergency recovery codes (stored as SHA-256 hashes, burned on consumption).
- PostgreSQL persistence: Stores credentials in staff_mfa_credentials using SQLAlchemy ORM (StaffMfaModel).
- Fail-closed resilience: Database errors never grant password-only access or turn MFA off.
- Session revocation: Tracks session_revoked_at to invalidate active sessions upon MFA reset or disablement.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Generator, Optional, Tuple

import pyotp
from sqlalchemy.orm import Session

from backend.platform.audit_log import SecurityAuditEvent, log_security_event
from backend.platform.security import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_recovery_codes,
    hash_recovery_code,
    verify_recovery_code,
)
from backend.storage.postgres_models import StaffMfaModel

logger = logging.getLogger(__name__)


class MfaStorageError(Exception):
    """Raised when a database or persistence error occurs during MFA operations."""


class MfaService:
    """Manages staff multi-factor authentication and session revocation using PostgreSQL."""

    def __init__(self, session_factory: Optional[Any] = None, engine: Optional[Any] = None):
        self._custom_session_factory = session_factory
        self._custom_engine = engine
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Safely ensures staff_mfa_credentials table and columns exist in the connected database."""
        try:
            from sqlalchemy import text
            if self._custom_engine is not None:
                engine = self._custom_engine
            else:
                from backend.storage.db import get_engine
                engine = get_engine()

            StaffMfaModel.__table__.create(bind=engine, checkfirst=True)

            with engine.begin() as conn:
                if engine.dialect.name == "postgresql":
                    conn.execute(text(
                        "ALTER TABLE staff_mfa_credentials ADD COLUMN IF NOT EXISTS session_revoked_at TIMESTAMP WITH TIME ZONE;"
                    ))
                elif engine.dialect.name == "sqlite":
                    try:
                        conn.execute(text(
                            "ALTER TABLE staff_mfa_credentials ADD COLUMN session_revoked_at TIMESTAMP;"
                        ))
                    except Exception:
                        pass
        except Exception as exc:
            logger.debug("Table check for staff_mfa_credentials: %s", exc)

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        """Provides a database session with automatic commit/rollback."""
        if self._custom_session_factory is not None:
            session: Session = self._custom_session_factory()
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
            with get_db_session(engine=self._custom_engine) as session:
                yield session

    def is_mfa_enabled(self, user_id: str) -> bool:
        """Checks if active MFA is enabled for the specified staff user.

        Fails closed: if a database error occurs, raises MfaStorageError rather than
        silently returning False, preventing password-only bypass during DB outages.
        """
        if not user_id:
            return False
        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                return bool(record and record.totp_enabled)
        except Exception as exc:
            logger.error("Error querying MFA status for user '%s': %s", user_id, exc)
            raise MfaStorageError(f"Database error checking MFA status for user '{user_id}': {exc}") from exc

    def initiate_enrollment(self, user_id: str, username: str) -> dict:
        """Starts MFA enrollment: generates a secret and recovery codes (marked pending)."""
        now = datetime.now(timezone.utc)
        raw_secret = pyotp.random_base32()
        encrypted_secret = encrypt_totp_secret(raw_secret)
        raw_recovery_codes = generate_recovery_codes(8)
        hashed_recovery_codes = [hash_recovery_code(code) for code in raw_recovery_codes]

        totp = pyotp.TOTP(raw_secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name="HealthAware",
        )

        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                if record is None:
                    record = StaffMfaModel(
                        user_id=user_id,
                        totp_secret_encrypted=encrypted_secret,
                        totp_enabled=False,
                        recovery_codes_hash_json=json.dumps(hashed_recovery_codes),
                        last_used_step=0,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(record)
                else:
                    record.totp_secret_encrypted = encrypted_secret
                    record.totp_enabled = False
                    record.recovery_codes_hash_json = json.dumps(hashed_recovery_codes)
                    record.last_used_step = 0
                    record.updated_at = now
                session.commit()
        except Exception as exc:
            logger.error("Failed to persist MFA enrollment for %s: %s", user_id, exc)
            raise MfaStorageError(f"Failed to persist MFA enrollment: {exc}") from exc

        log_security_event(
            event=SecurityAuditEvent.MFA_ENROLL_INITIATED,
            actor_id=user_id,
            status="SUCCESS",
            details={"username": username},
        )

        return {
            "secret": raw_secret,
            "provisioning_uri": provisioning_uri,
            "recovery_codes": raw_recovery_codes,
        }

    def confirm_enrollment(self, user_id: str, totp_code: str) -> bool:
        """Verifies the first TOTP code and activates MFA for the user."""
        if not totp_code:
            return False

        now = datetime.now(timezone.utc)
        current_step = int(time.time() // 30)

        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                if not record:
                    return False

                raw_secret = decrypt_totp_secret(record.totp_secret_encrypted)
                totp = pyotp.TOTP(raw_secret)

                # Verify with window of 1 (±30s)
                if not totp.verify(totp_code.strip(), valid_window=1):
                    log_security_event(
                        event=SecurityAuditEvent.MFA_VERIFY_FAILED,
                        actor_id=user_id,
                        status="FAILURE",
                        details={"reason": "initial_enrollment_code_invalid"},
                    )
                    return False

                # Activate MFA
                record.totp_enabled = True
                record.last_used_step = current_step - 1
                record.updated_at = now
                session.commit()
        except Exception as exc:
            logger.error("Failed to confirm MFA enrollment for %s: %s", user_id, exc)
            raise MfaStorageError(f"Failed to confirm MFA enrollment: {exc}") from exc

        log_security_event(
            event=SecurityAuditEvent.MFA_ENROLL_CONFIRMED,
            actor_id=user_id,
            status="SUCCESS",
        )
        return True

    def verify_login_mfa(
        self,
        user_id: str,
        code_or_recovery: str,
        client_ip: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Validates a TOTP code (with replay check) or an emergency recovery code.

        Returns:
            (success: bool, method_or_error: str)
            method_or_error can be 'totp', 'recovery_code', 'invalid_code', or 'replay_detected'.
        """
        if not user_id or not code_or_recovery:
            return False, "invalid_code"

        candidate = code_or_recovery.strip()
        now = datetime.now(timezone.utc)
        current_step = int(time.time() // 30)

        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                if not record or not record.totp_enabled:
                    return False, "mfa_not_enabled"

                raw_secret = decrypt_totp_secret(record.totp_secret_encrypted)
                last_used_step = record.last_used_step

                # 1. Attempt TOTP verification if candidate is numeric and ~6 digits
                if candidate.isdigit() and len(candidate) == 6:
                    totp = pyotp.TOTP(raw_secret)
                    is_valid = False
                    matched_step = None
                    for step_offset in (0, -1, 1):
                        target_step = current_step + step_offset
                        expected_code = totp.generate_otp(target_step)
                        if pyotp.utils.compare_digest(candidate, expected_code):
                            is_valid = True
                            matched_step = target_step
                            break

                    if is_valid and matched_step is not None:
                        if matched_step <= last_used_step:
                            log_security_event(
                                event=SecurityAuditEvent.MFA_REPLAY_REJECTED,
                                actor_id=user_id,
                                client_ip=client_ip,
                                status="REJECTED",
                                details={"attempted_step": matched_step, "last_used_step": last_used_step},
                            )
                            return False, "replay_detected"

                        record.last_used_step = matched_step
                        record.updated_at = now
                        session.commit()

                        log_security_event(
                            event=SecurityAuditEvent.MFA_VERIFY_SUCCESS,
                            actor_id=user_id,
                            client_ip=client_ip,
                            status="SUCCESS",
                            details={"method": "totp"},
                        )
                        return True, "totp"

                # 2. Attempt Recovery Code verification
                recovery_hashes = json.loads(record.recovery_codes_hash_json or "[]")
                matched_index = -1
                for idx, r_hash in enumerate(recovery_hashes):
                    if verify_recovery_code(candidate, r_hash):
                        matched_index = idx
                        break

                if matched_index >= 0:
                    recovery_hashes.pop(matched_index)
                    record.recovery_codes_hash_json = json.dumps(recovery_hashes)
                    record.updated_at = now
                    session.commit()

                    log_security_event(
                        event=SecurityAuditEvent.MFA_RECOVERY_CODE_USED,
                        actor_id=user_id,
                        client_ip=client_ip,
                        status="SUCCESS",
                        details={"codes_remaining": len(recovery_hashes)},
                    )
                    return True, "recovery_code"

        except Exception as exc:
            logger.error("MFA verification error for user %s: %s", user_id, exc)
            raise MfaStorageError(f"MFA verification storage error: {exc}") from exc

        log_security_event(
            event=SecurityAuditEvent.MFA_VERIFY_FAILED,
            actor_id=user_id,
            client_ip=client_ip,
            status="FAILURE",
            details={"reason": "invalid_code_or_recovery"},
        )
        return False, "invalid_code"

    def get_status(self, user_id: str) -> dict:
        """Returns MFA status and remaining recovery codes count."""
        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                if not record:
                    return {"mfa_enabled": False, "recovery_codes_remaining": 0}

                recovery_hashes = json.loads(record.recovery_codes_hash_json or "[]")
                return {
                    "mfa_enabled": bool(record.totp_enabled),
                    "recovery_codes_remaining": len(recovery_hashes),
                }
        except Exception as exc:
            logger.error("Error fetching MFA status for %s: %s", user_id, exc)
            raise MfaStorageError(f"Error fetching MFA status: {exc}") from exc

    def disable_mfa(self, user_id: str) -> bool:
        """Disables MFA for a user and sets session_revoked_at to invalidate other active sessions."""
        now = datetime.now(timezone.utc)
        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                if record:
                    record.totp_enabled = False
                    record.session_revoked_at = now
                    record.updated_at = now
                    session.commit()
            log_security_event(
                event=SecurityAuditEvent.MFA_DISABLED,
                actor_id=user_id,
                status="SUCCESS",
            )
            return True
        except Exception as exc:
            logger.error("Failed to disable MFA for user '%s': %s", user_id, exc)
            raise MfaStorageError(f"Failed to disable MFA: {exc}") from exc

    def admin_reset_mfa(self, target_user_id: str, admin_user_id: str) -> bool:
        """Administrator-assisted recovery: resets MFA and revokes all active sessions for the user."""
        now = datetime.now(timezone.utc)
        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=target_user_id).first()
                if record:
                    record.totp_enabled = False
                    record.totp_secret_encrypted = ""
                    record.recovery_codes_hash_json = "[]"
                    record.last_used_step = 0
                    record.session_revoked_at = now
                    record.updated_at = now
                else:
                    record = StaffMfaModel(
                        user_id=target_user_id,
                        totp_secret_encrypted="",
                        totp_enabled=False,
                        recovery_codes_hash_json="[]",
                        last_used_step=0,
                        session_revoked_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(record)
                session.commit()
            log_security_event(
                event=SecurityAuditEvent.MFA_ADMIN_RESET,
                actor_id=admin_user_id,
                target_id=target_user_id,
                status="SUCCESS",
            )
            return True
        except Exception as exc:
            logger.error("Admin reset MFA failed for user '%s': %s", target_user_id, exc)
            raise MfaStorageError(f"Admin reset MFA failed: {exc}") from exc

    def get_session_revoked_at(self, user_id: str) -> Optional[datetime]:
        """Returns the timestamp of the most recent session revocation event, if any."""
        if not user_id:
            return None
        try:
            with self._get_session() as session:
                record = session.query(StaffMfaModel).filter_by(user_id=user_id).first()
                if record and record.session_revoked_at:
                    return record.session_revoked_at
                return None
        except Exception as exc:
            logger.error("Failed to query session revocation timestamp for %s: %s", user_id, exc)
            raise MfaStorageError(f"Failed to query session revocation: {exc}") from exc

    def clear_all(self) -> None:
        """Clears all MFA records (for test isolation)."""
        try:
            with self._get_session() as session:
                session.query(StaffMfaModel).delete()
                session.commit()
        except Exception as exc:
            logger.debug("Failed to clear MFA credentials in test cleanup: %s", exc)


# Process-wide singleton
_default_mfa_service: Optional[MfaService] = None


def get_mfa_service() -> MfaService:
    global _default_mfa_service
    if _default_mfa_service is None:
        _default_mfa_service = MfaService()
    return _default_mfa_service


def set_mfa_service(service: Optional[MfaService]) -> None:
    """Allows test fixtures to inject custom MfaService instances."""
    global _default_mfa_service
    _default_mfa_service = service
