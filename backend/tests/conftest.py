"""Shared pytest fixtures and safety-checked NDB context for integration tests.

Every test session validates:
1. Execution inside the backend virtual environment (.venv).

Integration tests utilizing the Datastore emulator additionally validate (fail-fast):
2. DATASTORE_EMULATOR_HOST is explicitly configured and points strictly to a loopback address.
3. Active TCP socket connectivity to the local emulator endpoint.

The ``ndb_context`` fixture provides a clean NDB context for each test.
"""

from __future__ import annotations

import os
import socket
import sys
import urllib.parse

import pytest
from google.cloud import ndb


# ---------------------------------------------------------------------------
# Virtual environment check — executed once per session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _verify_virtual_env():
    """Confirms tests run inside the backend virtual environment."""
    if sys.prefix == sys.base_prefix:
        pytest.exit(
            "SAFETY: Tests must run inside the backend virtual environment (.venv). "
            f"Current interpreter: {sys.executable}",
            returncode=1,
        )


# ---------------------------------------------------------------------------
# Emulator safety checks (Cached / Session-wide fail-fast)
# ---------------------------------------------------------------------------

_emulator_verified = False


def _parse_host_port(raw: str) -> tuple[str, int]:
    """Parse host and port from DATASTORE_EMULATOR_HOST."""
    normalised = raw
    if normalised.startswith("http://") or normalised.startswith("https://"):
        parsed = urllib.parse.urlparse(normalised)
        return parsed.hostname, parsed.port or 8080
    parts = normalised.split(":")
    return parts[0], int(parts[1]) if len(parts) > 1 else 8080


def verify_emulator_connection() -> None:
    """Verifies that DATASTORE_EMULATOR_HOST is loopback and responding.
    Fails the test session immediately if offline to prevent multiple socket timeouts.
    """
    global _emulator_verified
    if _emulator_verified:
        return

    emulator_host = os.environ.get("DATASTORE_EMULATOR_HOST", "").strip()
    if not emulator_host:
        pytest.exit(
            "CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST is not set! "
            "Refusing to execute integration tests to prevent any connection to production Datastore.",
            returncode=1,
        )

    host, port = _parse_host_port(emulator_host)
    loopback = frozenset({"127.0.0.1", "localhost", "::1"})
    if host not in loopback:
        pytest.exit(
            f"CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST points to {host!r}, "
            f"which is NOT a loopback address ({loopback}).",
            returncode=1,
        )

    resolved_host = "127.0.0.1" if host == "localhost" else host
    try:
        sock = socket.create_connection((resolved_host, port), timeout=2.0)
        sock.close()
    except OSError as exc:
        pytest.exit(
            f"SAFETY: Cannot connect to emulator at {resolved_host}:{port}. "
            f"Ensure the emulator is running via 'scripts/start-emulator.ps1'. Error: {exc}",
            returncode=1,
        )

    _emulator_verified = True


# ---------------------------------------------------------------------------
# NDB context fixture
# ---------------------------------------------------------------------------

_PROJECT_ID = "health-awareness-local"


@pytest.fixture()
def ndb_context():
    """Provide a clean, isolated NDB context in the 'test-suite' namespace for each test function."""
    verify_emulator_connection()
    client = ndb.Client(project=_PROJECT_ID)
    return client.context(namespace="test-suite")


@pytest.fixture()
def ndb_ctx(ndb_context):
    """Shorthand: yields an entered NDB context for convenience.

    Usage::

        def test_something(ndb_ctx):
            # NDB operations are available immediately
            ...
    """
    with ndb_context as ctx:
        yield ctx
