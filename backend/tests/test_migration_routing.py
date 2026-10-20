"""Regression tests for Alembic migration connection routing safety.

Guarantees:
1. Development-mode migrations strictly use local/test DATABASE_URL targets.
2. A remote MIGRATION_DATABASE_URL in .env cannot silently override development targets.
3. Production migrations strictly require MIGRATION_DATABASE_URL and reject pooler hosts.
4. Missing, empty, or ambiguous configuration fails closed before opening any connection.
5. Exceptions never expose credentials or connection strings.
"""

import os
import unittest
from unittest.mock import patch

from backend.migrations.env import get_url


class TestMigrationRoutingSafety(unittest.TestCase):
    """Test suite verifying fail-closed connection routing for database migrations."""

    def test_01_development_ignores_remote_migration_url_and_uses_database_url(self):
        """In development mode, explicitly selected DATABASE_URL is used; MIGRATION_DATABASE_URL is ignored."""
        env_overrides = {
            "APP_ENV": "development",
            "DATABASE_URL": "postgresql://local_dev_user:local_pass@127.0.0.1:5432/healthaware_local",
            "MIGRATION_DATABASE_URL": "postgresql://prod_user:secret_prod_pass@ep-remote.ap-southeast-1.aws.neon.tech/neondb",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            resolved = get_url()
            self.assertIn("127.0.0.1:5432/healthaware_local", resolved)
            self.assertNotIn("neon.tech", resolved)
            self.assertNotIn("secret_prod_pass", resolved)

    def test_02_development_uses_test_database_url_when_database_url_empty(self):
        """In development mode, TEST_DATABASE_URL is accepted as local fallback when DATABASE_URL is empty."""
        env_overrides = {
            "APP_ENV": "development",
            "DATABASE_URL": "",
            "TEST_DATABASE_URL": "postgresql://test_user:test_pass@127.0.0.1:5432/healthaware_test",
            "MIGRATION_DATABASE_URL": "postgresql://prod_user:secret_prod_pass@ep-remote.ap-southeast-1.aws.neon.tech/neondb",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            resolved = get_url()
            self.assertIn("127.0.0.1:5432/healthaware_test", resolved)
            self.assertNotIn("neon.tech", resolved)

    def test_03_development_fails_closed_when_local_urls_missing_even_if_migration_url_present(self):
        """In development mode, presence of MIGRATION_DATABASE_URL alone fails closed; never connects to remote."""
        env_overrides = {
            "APP_ENV": "development",
            "DATABASE_URL": "",
            "TEST_DATABASE_URL": "",
            "MIGRATION_DATABASE_URL": "postgresql://prod_user:secret_prod_pass@ep-remote.ap-southeast-1.aws.neon.tech/neondb",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            with self.assertRaises(ValueError) as ctx:
                get_url()
            err = str(ctx.exception)
            self.assertIn("DATABASE_URL is required for development migrations", err)
            self.assertIn("MIGRATION_DATABASE_URL cannot be used in development mode", err)
            # Ensure no credentials leaked in error message
            self.assertNotIn("secret_prod_pass", err)
            self.assertNotIn("prod_user", err)

    def test_04_production_fails_closed_when_migration_database_url_missing(self):
        """In production mode, missing MIGRATION_DATABASE_URL raises ValueError and never uses DATABASE_URL."""
        env_overrides = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://app_pooler:pass@ep-pooler.ap-southeast-1.aws.neon.tech/neondb",
            "MIGRATION_DATABASE_URL": "",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            with self.assertRaises(ValueError) as ctx:
                get_url()
            err = str(ctx.exception)
            self.assertIn("MIGRATION_DATABASE_URL is required for production schema migrations", err)

    def test_05_production_rejects_pooled_migration_url(self):
        """In production mode, a pooled connection host (-pooler.) is rejected to protect DDL lock semantics."""
        env_overrides = {
            "APP_ENV": "production",
            "MIGRATION_DATABASE_URL": "postgresql://owner:pass@ep-raspy-moon-a1st7amb-pooler.ap-southeast-1.aws.neon.tech/neondb",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            with self.assertRaises(ValueError) as ctx:
                get_url()
            err = str(ctx.exception)
            self.assertIn("MIGRATION_DATABASE_URL points to a pooled connection host", err)

    def test_06_production_selects_unpooled_migration_url(self):
        """In production mode, unpooled MIGRATION_DATABASE_URL is selected."""
        env_overrides = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://pooler_user:pass@ep-pooler.neon.tech/neondb",
            "MIGRATION_DATABASE_URL": "postgresql://owner:pass@ep-raspy-moon-a1st7amb.ap-southeast-1.aws.neon.tech/neondb",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            resolved = get_url()
            self.assertIn("ep-raspy-moon-a1st7amb.ap-southeast-1.aws.neon.tech/neondb", resolved)
            self.assertNotIn("-pooler", resolved)

    def test_07_missing_app_env_fails_closed(self):
        """Missing or empty APP_ENV fails closed before inspecting any database URLs."""
        env_overrides = {
            "APP_ENV": "",
            "DATABASE_URL": "postgresql://localhost/db",
            "MIGRATION_DATABASE_URL": "postgresql://remote/db",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            with self.assertRaises(ValueError) as ctx:
                get_url()
            self.assertIn("Unsupported or missing APP_ENV", str(ctx.exception))

    def test_08_unsupported_app_env_fails_closed(self):
        """Ambiguous APP_ENV (e.g. 'staging', 'test') fails closed immediately."""
        for invalid_env in ["staging", "test", "local", "prod"]:
            with patch.dict(os.environ, {"APP_ENV": invalid_env}, clear=True):
                with self.assertRaises(ValueError) as ctx:
                    get_url()
                self.assertIn("Unsupported or missing APP_ENV", str(ctx.exception))

    def test_09_no_credentials_exposed_in_exceptions(self):
        """Exception messages never reveal database passwords, usernames, or connection strings."""
        sensitive_pass = "super_secret_p@ss_xyz99!"
        env_overrides = {
            "APP_ENV": "development",
            "DATABASE_URL": "",
            "MIGRATION_DATABASE_URL": f"postgresql://admin:{sensitive_pass}@ep-xyz.neon.tech/neondb",
        }
        with patch.dict(os.environ, env_overrides, clear=True):
            try:
                get_url()
            except ValueError as exc:
                err_msg = str(exc)
                self.assertNotIn(sensitive_pass, err_msg)
                self.assertNotIn("ep-xyz", err_msg)


if __name__ == "__main__":
    unittest.main()
