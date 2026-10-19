"""Rate limiting configuration and custom client IP resolution for HealthAware.

Uses Flask-Limiter with an in-memory storage backend and a custom key function
that respects Cloudflare edge proxying only after authenticating X-HealthAware-Proxy-Secret.
"""

from __future__ import annotations

import hmac
import os
from flask import request
from flask_limiter import Limiter


def is_valid_proxy_secret(provided_secret: str) -> bool:
    """Validates candidate secrets using constant-time comparison.
    
    Supports single secrets or comma-separated pairs during rotation
    (e.g., PROXY_SECRET="<new_secret>,<old_secret>").
    """
    if not provided_secret:
        return False
    raw_secrets = os.environ.get("PROXY_SECRET", "").strip()
    if not raw_secrets:
        return False
    candidates = [s.strip() for s in raw_secrets.split(",") if s.strip()]
    return any(hmac.compare_digest(provided_secret, candidate) for candidate in candidates)


def get_trusted_client_ip() -> str:
    """Custom Flask-Limiter key function.
    
    Safely determines the client IP address:
    1. Validates APP_ENV: only 'development' and 'production' are accepted.
    2. Validates X-HealthAware-Proxy-Secret using the shared is_valid_proxy_secret() helper.
    3. If valid under an authorized environment, trusts the CF-Connecting-IP header securely injected by Cloudflare.
    4. If APP_ENV is invalid or missing, proxy secret is invalid or missing, or request is direct/unverified,
       NEVER trusts forwarding headers; falls back strictly to the raw socket connection address (request.remote_addr).
    """
    app_env = os.environ.get("APP_ENV", "").strip()
    if app_env in ("development", "production"):
        provided_secret = request.headers.get("X-HealthAware-Proxy-Secret", "")
        if is_valid_proxy_secret(provided_secret):
            cf_ip = request.headers.get("CF-Connecting-IP")
            if cf_ip and cf_ip.strip():
                return cf_ip.strip()
            
    # Direct, unverified, or invalid-environment request: return the raw TCP connection address
    return request.remote_addr or "127.0.0.1"


def get_auth_rate_limit() -> str:
    """Dynamic rate limit string for authentication endpoints.

    Allows configuration via the AUTH_RATE_LIMIT environment variable.
    In testing environments where AUTH_RATE_LIMIT is unset, defaults to '5 per 15 minutes'
    so test suites remain fast and deterministic.
    In production and development, defaults to '30 per 15 minutes' to prevent false lockouts
    for legitimate users behind shared NAT or during interactive sessions.
    """
    configured = os.environ.get("AUTH_RATE_LIMIT", "").strip()
    if configured:
        return configured
    if os.environ.get("TESTING") == "true" or os.environ.get("PYTEST_CURRENT_TEST"):
        return "5 per 15 minutes"
    return "30 per 15 minutes"


limiter = Limiter(
    key_func=get_trusted_client_ip,
    storage_uri="memory://",
    strategy="fixed-window",
    default_limits=[],
)

