"""NDB client management with strict emulator-safety guarantees.

This module is the ONLY place in the codebase that creates an
``ndb.Client``.  Every call to ``get_ndb_client`` and ``get_ndb_context``
enforces the emulator-safety contract:

1. ``DATASTORE_EMULATOR_HOST`` must be set.
2. The host must resolve to a loopback address (``127.0.0.1`` or ``::1``).

Violation of either rule raises ``RuntimeError`` immediately, preventing
any accidental connection to a remote / production Datastore.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Generator

from google.cloud import ndb

# The project identifier used in emulator mode.
_LOCAL_PROJECT_ID = "health-awareness-local"


def _validate_emulator_host() -> str:
    """Return the validated emulator host string or raise RuntimeError."""
    raw = os.environ.get("DATASTORE_EMULATOR_HOST", "").strip()
    if not raw:
        raise RuntimeError(
            "CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST is not set.  "
            "Refusing to create an NDB client to avoid any connection to "
            "production Datastore."
        )

    # Strip optional http:// prefix for host:port parsing.
    normalised = raw
    if normalised.startswith("http://") or normalised.startswith("https://"):
        parsed = urllib.parse.urlparse(normalised)
        normalised = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname

    host = normalised.split(":")[0]
    _LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
    if host not in _LOOPBACK:
        raise RuntimeError(
            f"CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST resolves to "
            f"{host!r}, which is NOT a loopback address.  Refusing to create "
            f"an NDB client."
        )

    return raw


def get_ndb_client() -> ndb.Client:
    """Create and return a safe NDB client for the local emulator."""
    _validate_emulator_host()
    return ndb.Client(project=_LOCAL_PROJECT_ID)


def get_ndb_context(client: ndb.Client | None = None) -> ndb.Client:
    """Return an NDB context manager for use in a ``with`` block.

    Usage::

        client = get_ndb_client()
        with get_ndb_context(client) as ctx:
            # perform NDB operations
            ...
    """
    if client is None:
        client = get_ndb_client()
    return client.context()
