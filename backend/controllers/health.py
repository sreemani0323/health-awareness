"""Controller for application process-liveness check."""

from __future__ import annotations

from flask import Response

from backend.controllers.base import BaseHandler


class HealthCheckHandler(BaseHandler):
    """Endpoint D: Process liveness check.

    GET /api/v1/health

    Returns minimal status indicating the Flask application process is alive.
    Never exposes internal filesystem paths, credentials, environment variables,
    or database topology.
    """

    def get(self) -> tuple[Response, int]:
        return self.render_json({"status": "healthy"})
