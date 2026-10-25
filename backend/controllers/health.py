"""Controller for application process-liveness and database-readiness checks."""

from __future__ import annotations

import logging
from flask import Response

from backend.controllers.base import BaseHandler
from backend.storage.db import check_database_connection

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHandler):
    """Endpoint D: Process liveness check.

    GET /api/v1/health

    Returns minimal status indicating the Flask application process is alive.
    Never exposes internal filesystem paths, credentials, environment variables,
    or database topology.
    """

    def get(self) -> tuple[Response, int]:
        return self.render_json({"status": "healthy"})


class HealthReadinessHandler(BaseHandler):
    """Process and database readiness check.

    GET /api/v1/health/ready

    Executes a bounded database ping (SELECT 1 with timeout).
    Returns 200 when backend and database are ready to serve requests.
    Returns 503 with masked error details if the database is unavailable,
    connection pool is saturated, or ping times out.
    Never leaks database connection strings, credentials, hosts, or stack traces.
    """

    def get(self) -> tuple[Response, int]:
        try:
            is_ready = check_database_connection(timeout_seconds=2.0)
            if is_ready:
                return self.render_json({
                    "status": "ready",
                    "database": "connected",
                })
        except Exception as exc:
            logger.error("Readiness check encountered error: %s", exc)

        return self.render_error(
            "DATABASE_UNAVAILABLE",
            "The database service is currently unavailable or initializing. Please retry in a moment.",
            503,
        )
