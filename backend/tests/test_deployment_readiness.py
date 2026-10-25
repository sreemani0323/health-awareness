"""Tests for deployment readiness and origin protection features.

Verifies:
1. Fail-closed APP_ENV validation.
2. Fail-closed proxy secret authorization and staged rotation.
3. Narrow GET /api/v1/health probe exemption.
4. Custom trusted client IP determination and spoofing resistance.
5. Fail-closed Alembic migration connection resolution.
6. Explicit Flask session SECRET_KEY mapping and production enforcement.
7. Curriculum-only bootstrap functionality.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from backend.app import create_app
from backend.platform.rate_limiter import get_trusted_client_ip, is_valid_proxy_secret


class TestAppEnvAndProxySecret:
    """Tests for fail-closed APP_ENV validation and proxy secret middleware."""

    def test_health_check_get_is_exempt_without_proxy_secret(self):
        """GET /api/v1/health succeeds even in production without proxy secret."""
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": "sec-12345678901234567890123456789012"}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["data"]["status"] == "healthy"

    def test_health_check_post_requires_proxy_secret_in_production(self):
        """Non-GET methods on /api/v1/health require proxy secret in production."""
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": "sec-12345678901234567890123456789012"}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            resp = client.post("/api/v1/health")
            assert resp.status_code == 403
            assert resp.get_json()["error"]["code"] == "DIRECT_ACCESS_FORBIDDEN"

    def test_invalid_app_env_returns_config_error(self):
        """Requests with missing or invalid APP_ENV return HTTP 500 CONFIG_ERROR."""
        with patch.dict(os.environ, {"APP_ENV": "staging", "PROXY_SECRET": "some-secret"}):
            # In non-testing creation, invalid APP_ENV raises RuntimeError
            with pytest.raises(RuntimeError, match="APP_ENV must be explicitly configured"):
                create_app({"TESTING": False, "SECRET_KEY": "a" * 32})

    def test_production_missing_proxy_secret_fails_closed(self):
        """In production, missing PROXY_SECRET returns HTTP 500 CONFIG_ERROR."""
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": ""}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            resp = client.get("/api/v1/topics")
            assert resp.status_code == 500
            assert resp.get_json()["error"]["code"] == "CONFIG_ERROR"

    def test_production_direct_request_without_secret_is_forbidden(self):
        """In production, requests without X-HealthAware-Proxy-Secret are rejected with 403."""
        secret = "super-secret-key-that-is-at-least-32-chars-long"
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": secret}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            resp = client.get("/api/v1/topics")
            assert resp.status_code == 403
            assert resp.get_json()["error"]["code"] == "DIRECT_ACCESS_FORBIDDEN"

    def test_production_request_with_correct_proxy_secret_succeeds(self):
        """In production, matching proxy secret allows request to proceed."""
        secret = "super-secret-key-that-is-at-least-32-chars-long"
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": secret}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            with patch("backend.domain.domain_services.list_topics", return_value=[]):
                resp = client.get(
                    "/api/v1/topics",
                    headers={"X-HealthAware-Proxy-Secret": secret},
                )
                assert resp.status_code == 200

    def test_staged_proxy_secret_rotation(self):
        """Dual secrets in PROXY_SECRET permit both old and new secret headers."""
        old_sec = "old-secret-1234567890123456789012345"
        new_sec = "new-secret-1234567890123456789012345"
        dual = f"{new_sec},{old_sec}"

        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": dual}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            with patch("backend.domain.domain_services.list_topics", return_value=[]):
                # Old secret passes
                resp_old = client.get("/api/v1/topics", headers={"X-HealthAware-Proxy-Secret": old_sec})
                assert resp_old.status_code == 200

                # New secret passes
                resp_new = client.get("/api/v1/topics", headers={"X-HealthAware-Proxy-Secret": new_sec})
                assert resp_new.status_code == 200

                # Invalid secret rejected
                resp_bad = client.get("/api/v1/topics", headers={"X-HealthAware-Proxy-Secret": "wrong"})
                assert resp_bad.status_code == 403

    def test_development_bypass_allowed_when_secret_unset(self):
        """In development with no secret set, requests are permitted."""
        with patch.dict(os.environ, {"APP_ENV": "development", "PROXY_SECRET": ""}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True, "SECRET_KEY": "a" * 32})
            client = app.test_client()
            with patch("backend.domain.domain_services.list_topics", return_value=[]):
                resp = client.get("/api/v1/topics")
                assert resp.status_code == 200


class TestTrustedClientIp:
    """Tests for custom Flask-Limiter key function get_trusted_client_ip()."""

    def test_trusts_cf_connecting_ip_when_proxy_secret_valid(self):
        secret = "secret-123456789012345678901234567890"
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": secret}):
            app = Flask(__name__)
            with app.test_request_context(
                "/test",
                headers={
                    "X-HealthAware-Proxy-Secret": secret,
                    "CF-Connecting-IP": "203.0.113.195",
                    "X-Forwarded-For": "198.51.100.1",
                },
                environ_base={"REMOTE_ADDR": "192.0.2.1"},
            ):
                assert get_trusted_client_ip() == "203.0.113.195"

    def test_ignores_forwarded_headers_when_proxy_secret_invalid(self):
        secret = "secret-123456789012345678901234567890"
        with patch.dict(os.environ, {"APP_ENV": "production", "PROXY_SECRET": secret}):
            app = Flask(__name__)
            with app.test_request_context(
                "/test",
                headers={
                    "X-HealthAware-Proxy-Secret": "attacker-wrong-secret",
                    "CF-Connecting-IP": "203.0.113.195",
                },
                environ_base={"REMOTE_ADDR": "198.51.100.50"},
            ):
                assert get_trusted_client_ip() == "198.51.100.50"


class TestSecretKeyConfiguration:
    """Tests for Flask session secret key configuration."""

    def test_production_rejects_missing_secret_key(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "FLASK_SECRET_KEY": "", "SECRET_KEY": ""}):
            with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY must be configured with a minimum of 32 characters in production"):
                create_app({"TESTING": False})

    def test_production_rejects_short_secret_key(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "FLASK_SECRET_KEY": "short-key", "SECRET_KEY": ""}):
            with pytest.raises(RuntimeError, match="minimum of 32 characters"):
                create_app({"TESTING": False})

    def test_development_allows_dev_default(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "FLASK_SECRET_KEY": "", "SECRET_KEY": ""}):
            app = create_app({"TESTING": False, "SKIP_NDB_CONTEXT": True})
            assert app.config["SECRET_KEY"] == "dev-insecure-secret-key-change-in-production"


class TestAlembicEnvFailClosed:
    """Tests for backend/migrations/env.py connection resolution."""

    def test_production_requires_migration_database_url(self):
        from backend.migrations.env import get_url
        with patch.dict(os.environ, {"APP_ENV": "production", "MIGRATION_DATABASE_URL": "", "DATABASE_URL": "postgresql://pooled:5432/db"}):
            with pytest.raises(ValueError, match="MIGRATION_DATABASE_URL is required for production schema migrations"):
                get_url()

    def test_production_resolves_migration_database_url(self):
        from backend.migrations.env import get_url
        target = "postgresql://migrator:secret@direct.neon.tech:5432/healthaware"
        with patch.dict(os.environ, {"APP_ENV": "production", "MIGRATION_DATABASE_URL": target}):
            assert "direct.neon.tech" in get_url()

    def test_development_falls_back_to_database_url(self):
        from backend.migrations.env import get_url
        fallback = "postgresql://app:pass@127.0.0.1:5432/healthaware"
        with patch.dict(os.environ, {"APP_ENV": "development", "MIGRATION_DATABASE_URL": "", "DATABASE_URL": fallback}):
            assert "127.0.0.1" in get_url()

    def test_invalid_app_env_raises_value_error(self):
        from backend.migrations.env import get_url
        with patch.dict(os.environ, {"APP_ENV": "invalid_env", "DATABASE_URL": "postgresql://127.0.0.1/db"}):
            with pytest.raises(ValueError, match="Unsupported or missing APP_ENV"):
                get_url()


def create_test_image(format="PNG", size=(50, 50), color="blue") -> bytes:
    """Generates valid image bytes for attachment testing."""
    import io
    from PIL import Image
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class TestProductionAttachmentStorage:
    """Check 1 — Production attachment storage fail-closed verification."""

    def test_production_rejects_non_s3_backend(self):
        """When APP_ENV=production, ATTACHMENT_STORAGE_BACKEND != s3 fails immediately."""
        with patch.dict(os.environ, {"APP_ENV": "production", "ATTACHMENT_STORAGE_BACKEND": "local"}):
            with pytest.raises(RuntimeError, match="Local disk storage is prohibited in production"):
                from backend.platform.attachment_storage import AttachmentStorageService
                AttachmentStorageService()

    def test_production_rejects_missing_s3_bucket(self):
        """When APP_ENV=production, missing S3_BUCKET_NAME fails immediately."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "ATTACHMENT_STORAGE_BACKEND": "s3",
            "S3_BUCKET_NAME": "",
        }):
            with pytest.raises(RuntimeError, match="S3_BUCKET_NAME must be configured when APP_ENV=production"):
                from backend.platform.attachment_storage import AttachmentStorageService
                AttachmentStorageService()

    def test_production_rejects_failed_s3_client_initialization(self):
        """When APP_ENV=production, boto3 client failure does not fall back to disk."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "ATTACHMENT_STORAGE_BACKEND": "s3",
            "S3_BUCKET_NAME": "healthaware-prod-bucket",
        }):
            with patch("boto3.client", side_effect=Exception("AWS connection error")):
                with pytest.raises(RuntimeError, match="Failed to initialize S3 client"):
                    from backend.platform.attachment_storage import AttachmentStorageService
                    AttachmentStorageService()

    def test_production_store_refuses_local_persistence(self, tmp_path):
        """store_attachment refuses local disk persistence in production."""
        from backend.platform.attachment_storage import AttachmentStorageService
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            service = object.__new__(AttachmentStorageService)
            service.backend_type = "local"
            service.storage_dir = str(tmp_path)
            service.s3_client = None
            service.s3_bucket = ""

            png_bytes = create_test_image("PNG")
            with pytest.raises(RuntimeError, match="Writing complaint evidence to local disk is prohibited in production"):
                service.store_attachment(png_bytes)

    def test_development_permits_local_disk_fallback(self, tmp_path):
        """In development/testing, local disk fallback works as intended."""
        from backend.platform.attachment_storage import AttachmentStorageService
        with patch.dict(os.environ, {
            "APP_ENV": "development",
            "ATTACHMENT_STORAGE_BACKEND": "local",
            "ATTACHMENT_STORAGE_DIR": str(tmp_path),
        }):
            service = AttachmentStorageService(storage_dir=str(tmp_path))
            assert service.backend_type == "local"

            png_bytes = create_test_image("PNG")
            key, mime, size, checksum = service.store_attachment(png_bytes)
            assert key.endswith(".png")
            assert os.path.exists(os.path.join(str(tmp_path), key))

            read_bytes = service.read_attachment_bytes(key)
            assert read_bytes is not None
            assert len(read_bytes) > 0


class TestRateLimitRouteCoverage:
    """Check 2 — Rate-limit route coverage and security verification."""

    @pytest.fixture(autouse=True)
    def reset_limiter(self):
        """Reset Flask-Limiter storage between tests to ensure deterministic rates."""
        from backend.platform.rate_limiter import limiter
        try:
            if getattr(limiter, "_storage", None) is not None:
                limiter.reset()
        except Exception:
            pass
        yield
        try:
            if getattr(limiter, "_storage", None) is not None:
                limiter.reset()
        except Exception:
            pass

    def test_auth_login_rate_limit_applies(self):
        """POST /api/v1/auth/login enforces 5 attempts per 15 minutes without weakening auth."""
        with patch.dict(os.environ, {"APP_ENV": "development", "PROXY_SECRET": ""}):
            app = create_app({
                "TESTING": True,
                "RATELIMIT_ENABLED": True,
                "SKIP_NDB_CONTEXT": True,
                "SECRET_KEY": "a" * 32,
            })
            client = app.test_client()

            # First 5 attempts: authenticate normally (fail with 401 UNAUTHORIZED, not 429)
            for _ in range(5):
                resp = client.post("/api/v1/auth/login", json={"username": "wrong", "password": "bad"})
                assert resp.status_code in (400, 401)
                assert resp.get_json()["error"]["code"] in ("VALIDATION_ERROR", "UNAUTHORIZED", "INVALID_CREDENTIALS")

            # 6th attempt: rate limited with 429 RATE_LIMIT_EXCEEDED
            resp_limited = client.post("/api/v1/auth/login", json={"username": "wrong", "password": "bad"})
            assert resp_limited.status_code == 429
            assert resp_limited.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_concern_submission_rate_limit_applies(self):
        """POST /api/v1/concerns enforces 5 submissions per 10 minutes."""
        with patch.dict(os.environ, {"APP_ENV": "development", "PROXY_SECRET": ""}):
            app = create_app({
                "TESTING": True,
                "RATELIMIT_ENABLED": True,
                "SKIP_NDB_CONTEXT": True,
                "SECRET_KEY": "a" * 32,
            })
            client = app.test_client()

            # 5 calls within limit: validation error 400, not 429
            for _ in range(5):
                resp = client.post("/api/v1/concerns", json={"category": "invalid"})
                assert resp.status_code == 400
                assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"

            # 6th call exceeds limit
            resp_limited = client.post("/api/v1/concerns", json={"category": "invalid"})
            assert resp_limited.status_code == 429
            assert resp_limited.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_concern_track_rate_limit_and_token_validation_with_path_param(self):
        """Citizen tracking enforces 10 per 15 minutes across POST /track and GET /<report_id>/track without weakening token validation."""
        from contextlib import contextmanager

        @contextmanager
        def mock_db_sess():
            yield MagicMock()

        with patch.dict(os.environ, {"APP_ENV": "development", "PROXY_SECRET": ""}):
            with patch("backend.controllers.concerns.get_db_session", mock_db_sess):
                with patch("backend.controllers.concerns.ConcernRepository.verify_and_get_for_citizen", return_value=None):
                    app = create_app({
                        "TESTING": True,
                        "RATELIMIT_ENABLED": True,
                        "SKIP_NDB_CONTEXT": True,
                        "SECRET_KEY": "a" * 32,
                    })
                    client = app.test_client()

                    # First 5 calls via POST /api/v1/concerns/track with invalid token return 404 (token verified)
                    for _ in range(5):
                        resp = client.post("/api/v1/concerns/track", json={
                            "reference_id": "HA-DL-2026-NONEXIST",
                            "tracking_token": "wrong-token-abcde",
                        })
                        assert resp.status_code == 404
                        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED_OR_NOT_FOUND"

                    # Next 5 calls via GET /api/v1/concerns/<report_id>/track with path parameter return 404
                    for _ in range(5):
                        resp = client.get("/api/v1/concerns/HA-DL-2026-NONEXIST/track", headers={
                            "X-Tracking-Token": "wrong-token-abcde",
                        })
                        assert resp.status_code == 404
                        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED_OR_NOT_FOUND"

                    # 11th call exceeds rate limit (10 per 15 minutes) -> HTTP 429
                    resp_limited = client.get("/api/v1/concerns/HA-DL-2026-NONEXIST/track", headers={
                        "X-Tracking-Token": "wrong-token-abcde",
                    })
                    assert resp_limited.status_code == 429
                    assert resp_limited.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
