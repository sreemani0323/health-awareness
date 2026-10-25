"""Email OTP verification and challenge management service for HealthAware.

Provides CSPRNG 6-digit numeric OTP generation, SHA-256 salted/hashed challenge
persistence, brute-force attempt limits, expiration controls, and transactional email dispatch.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import secrets
import uuid
from typing import Any, Optional

from backend.platform.email_service import get_email_service
from backend.platform.sms_service import get_sms_service, normalize_phone_number
from backend.storage.postgres_models import EmailOtpChallengeModel, SmsOtpChallengeModel

logger = logging.getLogger(__name__)

OTP_DIGITS = 6
OTP_EXPIRATION_MINUTES = 10
MAX_VERIFICATION_ATTEMPTS = 5


def generate_numeric_otp(digits: int = OTP_DIGITS) -> str:
    """Generate a cryptographically secure numeric OTP using CSPRNG."""
    lower_bound = 10 ** (digits - 1)
    upper_bound = 10 ** digits - 1
    # secrets.randbelow(n) returns random int in [0, n)
    return str(lower_bound + secrets.randbelow(upper_bound - lower_bound + 1))


def hash_otp(otp: str) -> str:
    """Hash an OTP string using SHA-256 for secure persistence."""
    cleaned = otp.strip()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def verify_otp_hash(provided_otp: str, stored_hash: str) -> bool:
    """Verify a user-provided OTP against the stored SHA-256 hash in constant time."""
    provided_hash = hash_otp(provided_otp)
    return hmac.compare_digest(provided_hash, stored_hash)


def create_otp_challenge(
    db_sess,
    email: str,
    purpose: str,
    pending_payload: Optional[dict[str, Any]] = None,
) -> tuple[EmailOtpChallengeModel, str]:
    """Create a new OTP challenge, invalidating any previous unverified challenges for the email+purpose.

    Args:
        db_sess: SQLAlchemy database session.
        email: User email address.
        purpose: 'signup' or 'reset_password'.
        pending_payload: Optional dict storing user data (e.g. name, password_hash) until verified.

    Returns:
        tuple of (EmailOtpChallengeModel, raw_6_digit_otp)
    """
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=OTP_EXPIRATION_MINUTES)

    # Invalidate previous unverified challenges for this email and purpose
    db_sess.query(EmailOtpChallengeModel).filter(
        EmailOtpChallengeModel.email == normalized_email,
        EmailOtpChallengeModel.purpose == purpose,
        EmailOtpChallengeModel.is_verified == False,  # noqa: E712
    ).delete(synchronize_session=False)

    otp = generate_numeric_otp(OTP_DIGITS)
    otp_hash = hash_otp(otp)
    challenge_id = f"otp_{uuid.uuid4().hex[:16]}"

    challenge = EmailOtpChallengeModel(
        challenge_id=challenge_id,
        email=normalized_email,
        purpose=purpose,
        otp_hash=otp_hash,
        attempts=0,
        max_attempts=MAX_VERIFICATION_ATTEMPTS,
        is_verified=False,
        expires_at=expires_at,
        pending_payload=pending_payload,
        created_at=now,
    )
    db_sess.add(challenge)
    db_sess.flush()

    return challenge, otp


def verify_otp_challenge(
    db_sess,
    email: str,
    purpose: str,
    provided_otp: str,
) -> tuple[bool, Optional[str], Optional[EmailOtpChallengeModel]]:
    """Verify a user-supplied 6-digit OTP against an active challenge.

    Returns:
        (is_valid: bool, error_message: str | None, challenge: EmailOtpChallengeModel | None)
    """
    normalized_email = email.strip().lower()
    cleaned_otp = (provided_otp or "").strip()

    if not cleaned_otp or len(cleaned_otp) != OTP_DIGITS or not cleaned_otp.isdigit():
        return False, "Please provide a valid 6-digit numeric verification code.", None

    now = datetime.now(timezone.utc)

    challenge = (
        db_sess.query(EmailOtpChallengeModel)
        .filter(
            EmailOtpChallengeModel.email == normalized_email,
            EmailOtpChallengeModel.purpose == purpose,
            EmailOtpChallengeModel.is_verified == False,  # noqa: E712
        )
        .order_by(EmailOtpChallengeModel.created_at.desc())
        .first()
    )

    if not challenge:
        return False, "No active verification code found. Please request a new code.", None

    # Check expiration
    # Handle timezone-aware or naive datetimes from DB
    exp = challenge.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp < now:
        return False, "Verification code has expired. Please request a new code.", None

    # Check maximum brute-force attempts
    if challenge.attempts >= challenge.max_attempts:
        return False, "Too many failed attempts. For security, please request a new verification code.", None

    # Increment attempt count
    challenge.attempts += 1

    # Check OTP hash match in constant time
    if not verify_otp_hash(cleaned_otp, challenge.otp_hash):
        db_sess.flush()
        remaining = challenge.max_attempts - challenge.attempts
        if remaining > 0:
            return False, f"Incorrect verification code. {remaining} attempt(s) remaining.", None
        return False, "Too many failed attempts. For security, please request a new verification code.", None

    # Success: mark challenge verified
    challenge.is_verified = True
    db_sess.flush()

    return True, None, challenge


def send_challenge_email(email: str, otp: str, purpose: str) -> bool:
    """Dispatch the OTP verification code via the configured email service.

    Returns True if dispatched or safely queued; does not crash if unconfigured.
    """
    email_svc = get_email_service()

    if purpose == "signup":
        subject = "Your HealthAware Verification Code"
        text_content = (
            f"Welcome to HealthAware!\n\n"
            f"Your 6-digit email verification code is: {otp}\n\n"
            f"This code will expire in {OTP_EXPIRATION_MINUTES} minutes.\n\n"
            f"If you did not request this registration, please ignore this email.\n\n"
            f"HealthAware Team\nEvidence-Based Community Public Health Education"
        )
        html_content = (
            f"<div style='font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;'>"
            f"<div style='background: #00645c; color: white; padding: 12px 18px; border-radius: 6px; font-weight: bold; font-size: 16px;'>HealthAware Verification</div>"
            f"<p style='color: #334155; font-size: 15px; margin-top: 18px;'>Welcome to HealthAware! Use the verification code below to confirm your email and complete your learner registration:</p>"
            f"<div style='text-align: center; margin: 24px 0;'><span style='font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #00645c; background: #e0f2f1; padding: 10px 24px; border-radius: 6px; display: inline-block;'>{otp}</span></div>"
            f"<p style='color: #64748b; font-size: 13px;'>This code will expire in <strong>{OTP_EXPIRATION_MINUTES} minutes</strong>. If you did not create a HealthAware account, you can safely ignore this email.</p>"
            f"<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;' />"
            f"<p style='color: #94a3b8; font-size: 12px; margin: 0;'>HealthAware • Verified Public Health Education for Everyday Life</p>"
            f"</div>"
        )
    else:  # reset_password
        subject = "HealthAware Password Reset Code"
        text_content = (
            f"You requested a password reset for your HealthAware learner account.\n\n"
            f"Your 6-digit password reset code is: {otp}\n\n"
            f"This code will expire in {OTP_EXPIRATION_MINUTES} minutes.\n\n"
            f"If you did not request a password reset, your account remains secure and you can ignore this email.\n\n"
            f"HealthAware Team"
        )
        html_content = (
            f"<div style='font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;'>"
            f"<div style='background: #00645c; color: white; padding: 12px 18px; border-radius: 6px; font-weight: bold; font-size: 16px;'>HealthAware Security</div>"
            f"<p style='color: #334155; font-size: 15px; margin-top: 18px;'>You requested to reset your password. Use the verification code below to set a new password:</p>"
            f"<div style='text-align: center; margin: 24px 0;'><span style='font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #00645c; background: #e0f2f1; padding: 10px 24px; border-radius: 6px; display: inline-block;'>{otp}</span></div>"
            f"<p style='color: #64748b; font-size: 13px;'>This code will expire in <strong>{OTP_EXPIRATION_MINUTES} minutes</strong>. If you did not request a password reset, please ignore this message.</p>"
            f"<hr style='border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;' />"
            f"<p style='color: #94a3b8; font-size: 12px; margin: 0;'>HealthAware • Verified Public Health Education</p>"
            f"</div>"
        )

    result = email_svc.send_email(
        to_email=email,
        subject=subject,
        text_content=text_content,
        html_content=html_content,
    )

    if not result.success:
        logger.warning(
            "OTP email delivery failed or unconfigured: email=%s, provider=%s, error=%s",
            email,
            result.provider,
            result.error,
        )

    return result.success


def create_sms_otp_challenge(
    db_sess,
    phone_number: str,
    purpose: str,
    pending_payload: Optional[dict[str, Any]] = None,
) -> tuple[SmsOtpChallengeModel, str]:
    """Create a new SMS OTP challenge, invalidating prior unverified challenges for phone_number+purpose.

    Args:
        db_sess: SQLAlchemy database session.
        phone_number: Recipient mobile number (will be normalized to E.164).
        purpose: 'signup', 'role_request', or 'reset_password'.
        pending_payload: Optional dict storing user data until verified.

    Returns:
        tuple of (SmsOtpChallengeModel, raw_6_digit_otp)
    """
    is_valid, norm_phone, err = normalize_phone_number(phone_number)
    if not is_valid:
        raise ValueError(err or "Invalid phone number format.")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=OTP_EXPIRATION_MINUTES)

    # Invalidate previous unverified challenges for this phone and purpose
    db_sess.query(SmsOtpChallengeModel).filter(
        SmsOtpChallengeModel.phone_number == norm_phone,
        SmsOtpChallengeModel.purpose == purpose,
        SmsOtpChallengeModel.is_verified == False,  # noqa: E712
    ).delete(synchronize_session=False)

    otp = generate_numeric_otp(OTP_DIGITS)
    otp_hash = hash_otp(otp)
    challenge_id = f"sms_{uuid.uuid4().hex[:16]}"

    challenge = SmsOtpChallengeModel(
        challenge_id=challenge_id,
        phone_number=norm_phone,
        purpose=purpose,
        otp_hash=otp_hash,
        attempts=0,
        max_attempts=MAX_VERIFICATION_ATTEMPTS,
        is_verified=False,
        expires_at=expires_at,
        pending_payload=pending_payload,
        created_at=now,
    )
    db_sess.add(challenge)
    db_sess.flush()

    return challenge, otp


def verify_sms_otp_challenge(
    db_sess,
    phone_number: str,
    purpose: str,
    provided_otp: str,
) -> tuple[bool, Optional[str], Optional[SmsOtpChallengeModel]]:
    """Verify a user-supplied 6-digit OTP against an active SMS challenge.

    Returns:
        (is_valid: bool, error_message: str | None, challenge: SmsOtpChallengeModel | None)
    """
    is_valid, norm_phone, err = normalize_phone_number(phone_number)
    if not is_valid:
        return False, err or "Invalid phone number.", None

    cleaned_otp = (provided_otp or "").strip()
    if not cleaned_otp or len(cleaned_otp) != OTP_DIGITS or not cleaned_otp.isdigit():
        return False, "Please provide a valid 6-digit numeric verification code.", None

    now = datetime.now(timezone.utc)

    challenge = (
        db_sess.query(SmsOtpChallengeModel)
        .filter(
            SmsOtpChallengeModel.phone_number == norm_phone,
            SmsOtpChallengeModel.purpose == purpose,
            SmsOtpChallengeModel.is_verified == False,  # noqa: E712
        )
        .order_by(SmsOtpChallengeModel.created_at.desc())
        .first()
    )

    if not challenge:
        return False, "No active mobile verification code found. Please request a new code.", None

    exp = challenge.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp < now:
        return False, "Verification code has expired. Please request a new code.", None

    if challenge.attempts >= challenge.max_attempts:
        return False, "Too many failed attempts. For security, please request a new verification code.", None

    challenge.attempts += 1

    if not verify_otp_hash(cleaned_otp, challenge.otp_hash):
        db_sess.flush()
        remaining = challenge.max_attempts - challenge.attempts
        if remaining > 0:
            return False, f"Incorrect verification code. {remaining} attempt(s) remaining.", None
        return False, "Too many failed attempts. For security, please request a new verification code.", None

    challenge.is_verified = True
    db_sess.flush()

    return True, None, challenge


def send_challenge_sms(phone_number: str, otp: str, purpose: str) -> bool:
    """Dispatch the OTP verification code via the configured SMS service.

    Returns True if dispatched; does not crash if unconfigured.
    """
    sms_svc = get_sms_service()

    if purpose in ("signup", "role_request"):
        message = (
            f"HealthAware verification code: {otp}. "
            f"Valid for {OTP_EXPIRATION_MINUTES} minutes. Never share this code."
        )
    else:  # reset_password
        message = (
            f"HealthAware password reset code: {otp}. "
            f"Valid for {OTP_EXPIRATION_MINUTES} minutes. Do not share."
        )

    result = sms_svc.send_sms(to_phone=phone_number, message=message)
    if not result.success:
        logger.warning(
            "OTP SMS delivery failed or unconfigured: provider=%s, error=%s",
            result.provider,
            result.error,
        )

    return result.success

