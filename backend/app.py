"""Flask application factory for Health Awareness application.

Provides:
1. Centralised route and blueprint registration.
2. Request-scoped Cloud NDB context lifecycle management (decoupled when running PostgreSQL).
3. Centralised JSON error handlers conforming to the API contract.
4. Fail-closed proxy secret authorization and strict APP_ENV validation.
5. In-memory rate limiting with trusted client IP resolution.
6. Explicit session-signing key (SECRET_KEY) configuration.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
from datetime import timedelta
from typing import Any

from flask import Flask, g, jsonify, request, session
from flask_limiter.errors import RateLimitExceeded
from google.cloud import ndb
from werkzeug.exceptions import HTTPException

from backend.controllers import create_api_blueprint
from backend.platform.ndb_client import get_ndb_client
from backend.platform.rate_limiter import (
    get_trusted_client_ip,
    is_valid_proxy_secret,
    limiter,
)

logger = logging.getLogger(__name__)


def _register_error_handlers(app: Flask) -> None:
    """Register uniform JSON error handlers for HTTP and system errors."""

    @app.errorhandler(400)
    def handle_bad_request(exc: Exception):
        msg = "The request payload or parameters are invalid."
        if isinstance(exc, HTTPException) and exc.description:
            msg = exc.description
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": msg,
            }
        }), 400

    @app.errorhandler(404)
    def handle_not_found(exc: Exception):
        msg = "The requested resource was not found."
        if isinstance(exc, HTTPException) and exc.description:
            msg = exc.description
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": msg,
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(exc: Exception):
        return jsonify({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The HTTP method is not allowed for this endpoint.",
            }
        }), 405

    @app.errorhandler(503)
    def handle_service_unavailable(exc: Exception):
        return jsonify({
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "The storage service is currently unavailable.",
            }
        }), 503

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(exc: RateLimitExceeded):
        return jsonify({
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many requests: {exc.description}",
            }
        }), 429

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception):
        if isinstance(exc, HTTPException):
            code_str = exc.name.upper().replace(" ", "_")
            return jsonify({
                "error": {
                    "code": code_str,
                    "message": exc.description,
                }
            }), exc.code

        exc_name = exc.__class__.__name__
        exc_msg = str(exc)

        # Detect database / socket connectivity outage
        outage_indicators = (
            "RpcError",
            "GoogleAPICallError",
            "ConnectionRefused",
            "TransportError",
            "SocketError",
        )
        if any(term in exc_name for term in outage_indicators) or (
            "Connection refused" in exc_msg or "Failed to connect" in exc_msg
        ):
            logger.error("Storage connectivity failure [%s]: %s", exc_name, exc_msg)
            return jsonify({
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "The storage service is currently unavailable.",
                }
            }), 503

        # Mask internal server errors from client response
        logger.exception("Unhandled server exception: %s", exc)
        return jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
            }
        }), 500


def _register_request_lifecycle(app: Flask) -> None:
    """Manages request-scoped NDB context entry and reliable teardown."""

    @app.before_request
    def open_ndb_context():
        # Liveness check does not require database connection
        if request.path == "/api/v1/health":
            return None

        # Allow tests to skip NDB context if mocking domain services
        if app.config.get("SKIP_NDB_CONTEXT"):
            return None

        # Decouple NDB context if running purely with PostgreSQL without Datastore emulator
        if os.environ.get("DATABASE_URL") and not os.environ.get("DATASTORE_EMULATOR_HOST"):
            return None

        # If an NDB context is already active on this thread (e.g. test runner fixture), reuse it
        if ndb.get_context(raise_context_error=False) is not None:
            return None

        client = app.config.get("NDB_CLIENT")
        if client is None:
            try:
                client = get_ndb_client()
                app.config["NDB_CLIENT"] = client
            except RuntimeError as exc:
                logger.error("NDB client safety check failed: %s", exc)
                return jsonify({
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "The storage service is currently unavailable.",
                    }
                }), 503

        try:
            ctx = client.context()
            ctx.__enter__()
            g.ndb_context = ctx
        except Exception as exc:
            logger.error("Failed to establish NDB request context: %s", exc)
            return jsonify({
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "The storage service is currently unavailable.",
                }
            }), 503

    @app.teardown_request
    def close_ndb_context(exception=None):
        ctx = g.pop("ndb_context", None)
        if ctx is not None:
            try:
                ctx.__exit__(None, None, None)
            except Exception as exc:
                logger.warning("Error closing NDB request context: %s", exc)


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    is_testing = bool(test_config and test_config.get("TESTING"))
    app_env = os.environ.get("APP_ENV", "").strip()

    # Validate APP_ENV: must be explicitly development or production
    if not is_testing:
        if app_env not in ("development", "production"):
            raise RuntimeError(
                f"Configuration error: APP_ENV must be explicitly configured as 'development' or 'production'. Found: '{app_env}'"
            )

    # Explicit session-signing key (SECRET_KEY) initialization
    flask_secret = (
        (test_config.get("FLASK_SECRET_KEY") or test_config.get("SECRET_KEY") if test_config else None)
        or os.environ.get("FLASK_SECRET_KEY", "").strip()
        or os.environ.get("SECRET_KEY", "").strip()
    )

    if app_env == "production" and not is_testing:
        if not flask_secret or len(flask_secret) < 32:
            raise RuntimeError(
                "Configuration error: FLASK_SECRET_KEY must be configured with a minimum of 32 characters in production. "
                "Development defaults are prohibited."
            )
        secret_key = flask_secret

        mfa_key = os.environ.get("MFA_ENCRYPTION_KEY", "").strip()
        if (not mfa_key or len(mfa_key) < 16) and "PYTEST_CURRENT_TEST" not in os.environ:
            raise RuntimeError(
                "Configuration error: Dedicated MFA_ENCRYPTION_KEY must be configured in production. "
                "Reusing FLASK_SECRET_KEY or fallback defaults is prohibited in production."
            )

    elif app_env == "development" or is_testing:
        secret_key = flask_secret or "dev-insecure-secret-key-change-in-production"
    else:
        secret_key = secrets.token_hex(32)

    session_secure = (
        os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1")
        or app_env == "production"
    )

    app.config.from_mapping(
        JSON_SORT_KEYS=False,
        TESTING=False,
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=session_secure,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )

    if test_config:
        app.config.update(test_config)

    # 1. Initialize Rate Limiter
    limiter.init_app(app)

    # 2. Register API blueprint
    app.register_blueprint(create_api_blueprint())

    # 3. Register centralized error handlers
    _register_error_handlers(app)

    # 4. Register request lifecycle for NDB context
    _register_request_lifecycle(app)

    # 5. Fail-Closed Proxy Secret Verification & Upfront APP_ENV Check
    @app.before_request
    def verify_proxy_secret():
        # 1. Narrow health check exemption (exact GET only)
        if request.method == "GET" and request.path == "/api/v1/health":
            return None

        # In testing mode without proxy secret configured, allow test calls
        if app.config.get("TESTING") and not os.environ.get("PROXY_SECRET") and not request.headers.get("X-HealthAware-Proxy-Secret"):
            return None

        # 2. Validate APP_ENV: accept only explicit development or production
        current_env = os.environ.get("APP_ENV", "").strip()
        if current_env not in ("development", "production"):
            return jsonify({
                "error": {
                    "code": "CONFIG_ERROR",
                    "message": "Server configuration error: APP_ENV must be explicitly set to 'development' or 'production'."
                }
            }), 500

        raw_secret = os.environ.get("PROXY_SECRET", "").strip()

        # 3. Development environment: permit missing-secret bypass only when unset
        if current_env == "development" and not raw_secret:
            return None

        # 4. Production environment: require configured proxy secret
        if current_env == "production" and not raw_secret:
            return jsonify({
                "error": {
                    "code": "CONFIG_ERROR",
                    "message": "Server configuration error: PROXY_SECRET must be configured in production."
                }
            }), 500

        # 5. Validate provided header through shared constant-time helper
        provided_secret = request.headers.get("X-HealthAware-Proxy-Secret", "")
        if not is_valid_proxy_secret(provided_secret):
            return jsonify({
                "error": {
                    "code": "DIRECT_ACCESS_FORBIDDEN",
                    "message": "Direct API access is not permitted. Requests must originate through the official application domain."
                }
            }), 403

    # 6. Strict Cross-Origin Resource Sharing (CORS) policy
    allowed_origins: set[str] = {
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    }
    custom_origins = os.environ.get("ALLOWED_ORIGINS")
    if custom_origins:
        allowed_origins.update(o.strip() for o in custom_origins.split(",") if o.strip())

    @app.before_request
    def handle_cors_preflight():
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin")
            resp = app.make_response(("", 204))
            if origin and origin in allowed_origins:
                resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Access-Control-Allow-Credentials"] = "true"
                resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
                resp.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Requested-With, X-XSRF-TOKEN, X-CSRF-TOKEN, X-HealthAware-Proxy-Secret"
                )
                resp.headers["Vary"] = "Origin"
            return resp

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, X-XSRF-TOKEN, X-CSRF-TOKEN, X-HealthAware-Proxy-Secret"
            )
            response.headers["Vary"] = "Origin"
        return response

    # 7. CSRF protection for cookie-authenticated state-changing requests
    @app.before_request
    def verify_csrf_protection():
        csrf_enabled = app.config.get(
            "CSRF_ENABLED",
            not app.config.get("TESTING", False),
        )
        if not csrf_enabled:
            return None

        # Safe HTTP methods are exempt from CSRF checks
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return None

        # Public / unauthenticated initial endpoints are exempt
        if request.path in (
            "/api/v1/auth/login",
            "/api/v1/health",
            "/api/v1/staff/apply",
            "/api/v1/staff/applications/track",
        ):
            return None

        # For cookie-authenticated requests, verify Double-Submit Anti-CSRF Token
        if session.get("user_id"):
            token_header = (
                request.headers.get("X-XSRF-TOKEN")
                or request.headers.get("X-CSRF-TOKEN")
                or request.headers.get("X-CSRFToken")
            )
            session_token = session.get("csrf_token")
            if (
                not token_header
                or not session_token
                or not hmac.compare_digest(token_header, session_token)
            ):
                return jsonify({
                    "error": {
                        "code": "CSRF_ERROR",
                        "message": "Invalid or missing CSRF token.",
                    }
                }), 403

        return None

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
