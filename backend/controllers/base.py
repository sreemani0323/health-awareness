"""Base controller handler inspired by Oppia Foundation architecture.

All REST controllers subclass BaseHandler, which extends Flask MethodView.
It standardises JSON response formatting, success envelopes, and error formatting.
"""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify
from flask.views import MethodView


class BaseHandler(MethodView):
    """Base class for all application REST API controllers."""

    DEFAULT_API_VERSION = "v1"

    def render_json(
        self,
        data: Any,
        meta: dict[str, Any] | None = None,
        status_code: int = 200,
    ) -> tuple[Response, int]:
        """Wrap payload in a standardized success envelope.

        Format:
        {
            "data": <data>,
            "meta": { "api_version": "v1", ... }
        }
        """
        response_meta = {"api_version": self.DEFAULT_API_VERSION}
        if meta:
            response_meta.update(meta)

        envelope = {
            "data": data,
            "meta": response_meta,
        }
        return jsonify(envelope), status_code

    def render_error(
        self,
        code: str,
        message: str,
        status_code: int = 400,
    ) -> tuple[Response, int]:
        """Return standardized error structure."""
        envelope = {
            "error": {
                "code": code,
                "message": message,
            }
        }
        return jsonify(envelope), status_code
