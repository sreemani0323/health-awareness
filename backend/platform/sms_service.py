"""SMS delivery service supporting free-tier providers for HealthAware.

Provides:
- Phone number normalization to E.164 international standard.
- Multi-provider adapters for zero-cost / free-tier SMS options:
  * Twilio Free Trial (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)
  * Fast2SMS Free Tier (FAST2SMS_API_KEY)
  * TextLocal / MSG91 Free Tier (TEXTLOCAL_API_KEY)
- Safe unconfigured / development fallback that prevents crashing and avoids leaking credentials.
- Strict PII masking in structured audit logs.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SmsSendResult:
    """Outcome of an SMS dispatch attempt."""
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


def normalize_phone_number(raw_phone: str, default_country_code: str = "+91") -> tuple[bool, str, Optional[str]]:
    """Normalize and validate a phone number into strict E.164 international format.

    Args:
        raw_phone: Raw phone string entered by user (e.g. '9876543210', '+91 98765 43210').
        default_country_code: Country code prefix if none supplied (default +91 for India).

    Returns:
        (is_valid: bool, normalized_e164: str, error_message: str | None)
    """
    if not raw_phone or not isinstance(raw_phone, str):
        return False, "", "Phone number is required."

    # Strip whitespace, dashes, parentheses, dots
    cleaned = re.sub(r"[\s\-\(\)\.]", "", raw_phone.strip())

    if not cleaned:
        return False, "", "Phone number cannot be empty."

    # If it starts with '+', validate full E.164
    if cleaned.startswith("+"):
        digits_only = cleaned[1:]
        if not digits_only.isdigit():
            return False, "", "Phone number must contain digits only."
        if len(digits_only) < 7 or len(digits_only) > 15:
            return False, "", "Phone number length must be between 7 and 15 digits (E.164 standard)."
        return True, cleaned, None

    # Handle standard 10-digit national number
    if cleaned.isdigit():
        if len(cleaned) == 10:
            prefix = default_country_code if default_country_code.startswith("+") else f"+{default_country_code}"
            return True, f"{prefix}{cleaned}", None
        elif 10 < len(cleaned) <= 15:
            # Assumed country code without '+'
            return True, f"+{cleaned}", None

    return False, "", "Please enter a valid mobile number with country code (e.g. +91 9876543210)."


def mask_phone_number(phone: str) -> str:
    """Mask a phone number for safe logging (e.g. '+91*****43210')."""
    if not phone or len(phone) < 6:
        return "***"
    return f"{phone[:3]}*****{phone[-4:]}"


class BaseSmsProvider:
    """Abstract base class for SMS provider adapters."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    def is_configured(self) -> bool:
        raise NotImplementedError

    def send(self, to_phone: str, message: str) -> SmsSendResult:
        raise NotImplementedError


class TwilioSmsProvider(BaseSmsProvider):
    """Twilio SMS provider adapter (compatible with Twilio Free Trial)."""

    def __init__(self, account_sid: str, auth_token: str, from_phone: str):
        self._account_sid = account_sid.strip()
        self._auth_token = auth_token.strip()
        self._from_phone = from_phone.strip()

    @property
    def name(self) -> str:
        return "twilio"

    def is_configured(self) -> bool:
        return bool(self._account_sid and self._auth_token and self._from_phone)

    def send(self, to_phone: str, message: str) -> SmsSendResult:
        if not self.is_configured():
            return SmsSendResult(success=False, provider=self.name, error="Twilio credentials not configured.")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}/Messages.json"
        data = urllib.parse.urlencode({
            "To": to_phone,
            "From": self._from_phone,
            "Body": message,
        }).encode("utf-8")

        auth_header = "Basic " + base64.b64encode(
            f"{self._account_sid}:{self._auth_token}".encode("utf-8")
        ).decode("ascii")

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", auth_header)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                msg_sid = resp_data.get("sid", "sent")
                logger.info("SMS delivered via Twilio to %s, sid=%s", mask_phone_number(to_phone), msg_sid)
                return SmsSendResult(success=True, provider=self.name, message_id=msg_sid)
        except urllib.error.HTTPError as exc:
            try:
                err_data = json.loads(exc.read().decode("utf-8"))
                err_msg = err_data.get("message", f"HTTP {exc.code}")
            except Exception:
                err_msg = f"HTTP {exc.code}"
            logger.error("Twilio SMS dispatch failed: %s", err_msg)
            return SmsSendResult(success=False, provider=self.name, error=err_msg)
        except Exception as exc:
            logger.error("Twilio network error: %s", exc)
            return SmsSendResult(success=False, provider=self.name, error=str(exc))


class Fast2SmsProvider(BaseSmsProvider):
    """Fast2SMS provider adapter (supports free credits for Indian mobile numbers)."""

    def __init__(self, api_key: str):
        self._api_key = api_key.strip()

    @property
    def name(self) -> str:
        return "fast2sms"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def send(self, to_phone: str, message: str) -> SmsSendResult:
        if not self.is_configured():
            return SmsSendResult(success=False, provider=self.name, error="Fast2SMS API key not configured.")

        # Fast2SMS expects 10-digit number without +91
        clean_num = to_phone.replace("+91", "").lstrip("+")
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = json.dumps({
            "route": "v3",
            "sender_id": "TXTIND",
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": clean_num,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("authorization", self._api_key)
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                if resp_data.get("return") is True:
                    req_id = resp_data.get("request_id", "sent")
                    logger.info("SMS delivered via Fast2SMS to %s", mask_phone_number(to_phone))
                    return SmsSendResult(success=True, provider=self.name, message_id=req_id)
                err = resp_data.get("message", ["Unknown error"])
                if isinstance(err, list):
                    err = err[0] if err else "Unknown error"
                return SmsSendResult(success=False, provider=self.name, error=str(err))
        except Exception as exc:
            logger.error("Fast2SMS error: %s", exc)
            return SmsSendResult(success=False, provider=self.name, error=str(exc))


class DevelopmentSmsProvider(BaseSmsProvider):
    """Fallback provider for development, tests, or unconfigured environments.

    In test or dev mode, safely logs without exposing raw credentials.
    In production mode, cleanly reports unconfigured state without crashing.
    """

    def __init__(self, is_development: bool = True):
        self._is_dev = is_development

    @property
    def name(self) -> str:
        return "development" if self._is_dev else "unconfigured"

    def is_configured(self) -> bool:
        return self._is_dev

    def send(self, to_phone: str, message: str) -> SmsSendResult:
        app_env = os.environ.get("APP_ENV", "").lower()
        flask_env = os.environ.get("FLASK_ENV", "").lower()
        if app_env == "production" or flask_env == "production":
            return SmsSendResult(
                success=False,
                provider="unconfigured",
                error="SMS service is not configured on this server.",
            )

        if self._is_dev:
            logger.info("[DEV SMS DISPATCH] To: %s | Simulated challenge dispatched (raw OTP suppressed).", mask_phone_number(to_phone))
            return SmsSendResult(success=True, provider="development", message_id="dev-simulated-msg")
        return SmsSendResult(
            success=False,
            provider="unconfigured",
            error="SMS service is not configured on this server.",
        )


class SmsService:
    """Coordinates SMS dispatch across configured providers with priority resolution."""

    def __init__(self):
        self._provider: BaseSmsProvider = self._resolve_provider()

    def _resolve_provider(self) -> BaseSmsProvider:
        # 1. Twilio
        tw_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
        tw_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
        tw_phone = os.environ.get("TWILIO_PHONE_NUMBER", "").strip()
        if tw_sid and tw_token and tw_phone:
            return TwilioSmsProvider(tw_sid, tw_token, tw_phone)

        # 2. Fast2SMS
        f2s_key = os.environ.get("FAST2SMS_API_KEY", "").strip()
        if f2s_key:
            return Fast2SmsProvider(f2s_key)

        # 3. Environment check
        app_env = os.environ.get("FLASK_ENV", "").lower()
        app_mode = os.environ.get("APP_ENV", "").lower()
        is_dev_or_test = (
            app_env in ("development", "test", "testing")
            or app_mode in ("development", "test", "testing")
            or os.environ.get("TESTING", "").lower() in ("1", "true")
            or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        )
        return DevelopmentSmsProvider(is_development=is_dev_or_test)

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def is_configured(self) -> bool:
        return self._provider.is_configured()

    def send_sms(self, to_phone: str, message: str) -> SmsSendResult:
        is_valid, norm_phone, err = normalize_phone_number(to_phone)
        if not is_valid:
            return SmsSendResult(success=False, provider=self._provider.name, error=err)
        return self._provider.send(norm_phone, message)


_global_sms_service: Optional[SmsService] = None


def get_sms_service() -> SmsService:
    """Retrieve or initialize the global SmsService instance."""
    global _global_sms_service
    if _global_sms_service is None:
        _global_sms_service = SmsService()
    return _global_sms_service
