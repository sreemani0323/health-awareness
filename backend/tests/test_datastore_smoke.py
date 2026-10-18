"""Database connectivity smoke test for local Datastore emulator.

This test verifies the local infrastructure:
1. Confirms execution inside the designated backend virtual environment.
2. Validates that DATASTORE_EMULATOR_HOST is explicitly configured to a local loopback address.
   Never allows silent fallback to a remote/production Google Cloud project.
3. Tests TCP socket connectivity to the emulator endpoint.
4. Performs an isolated NDB write -> read -> verify -> delete round-trip using a temporary entity.
"""

from __future__ import annotations

import datetime
import os
import socket
import sys
import uuid
import urllib.parse


def verify_virtual_environment() -> None:
    """Verifies that the test is executing inside the project virtual environment."""
    is_venv = sys.prefix != sys.base_prefix
    if not is_venv:
        raise RuntimeError(
            f"Smoke test must run inside the backend virtual environment (.venv). "
            f"Detected interpreter: {sys.executable} with prefix {sys.prefix}"
        )


def verify_local_emulator_host() -> tuple[str, int]:
    """Verifies that DATASTORE_EMULATOR_HOST points strictly to local loopback."""
    emulator_host = os.environ.get("DATASTORE_EMULATOR_HOST", "").strip()
    if not emulator_host:
        raise RuntimeError(
            "CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST is not set! "
            "Refusing to execute test to prevent any possible connection to production Datastore."
        )

    # Normalize url or host:port
    if "://" not in emulator_host:
        target = f"http://{emulator_host}"
    else:
        target = emulator_host

    parsed = urllib.parse.urlparse(target)
    hostname = parsed.hostname or ""
    port = parsed.port or 8080

    allowed_hosts = {"127.0.0.1", "localhost", "::1"}
    if hostname.lower() not in allowed_hosts:
        raise RuntimeError(
            f"CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST '{emulator_host}' "
            f"does not point to a local loopback address ({allowed_hosts}). "
            f"Execution halted to protect remote resources."
        )

    # Verify socket connectivity to the local port
    try:
        with socket.create_connection((hostname, port), timeout=3.0):
            pass
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        raise RuntimeError(
            f"Unable to connect to Datastore emulator at {hostname}:{port}. "
            f"Ensure the emulator is running via 'scripts/start-emulator.ps1'. Error: {exc}"
        ) from exc

    return hostname, port


def run_smoke_test(project_id: str = "health-awareness-local") -> None:
    """Executes the NDB write -> read -> verify -> delete round-trip."""
    from google.cloud import ndb

    # Initialize client explicitly with the local project ID
    client = ndb.Client(project=project_id)

    class _InfrastructureSmokeTestEntity(ndb.Model):
        """Temporary NDB model used exclusively for infrastructure smoke verification."""

        test_uuid = ndb.StringProperty(required=True)
        timestamp = ndb.DateTimeProperty(auto_now_add=True)
        message = ndb.StringProperty(required=True)
        iteration = ndb.IntegerProperty(default=1)

    record_id = f"smoke-{uuid.uuid4()}"
    test_uuid_val = str(uuid.uuid4())
    test_message = "Local Datastore emulator round-trip verification"

    print(f"[SMOKE TEST] Initializing NDB client for project: '{client.project}'")
    print(f"[SMOKE TEST] Connected emulator endpoint: '{client.host}'")

    with client.context():
        # 1. Write temporary record
        entity = _InfrastructureSmokeTestEntity(
            id=record_id,
            test_uuid=test_uuid_val,
            message=test_message,
            iteration=100,
        )
        put_key = entity.put()
        print(f"[SMOKE TEST] [PASS] Record written successfully with key: {put_key}")

        # 2. Read back record
        fetched = _InfrastructureSmokeTestEntity.get_by_id(record_id)
        if fetched is None:
            raise AssertionError(f"Record '{record_id}' was written but could not be read back!")

        # 3. Verify record contents
        if fetched.test_uuid != test_uuid_val:
            raise AssertionError(
                f"Payload mismatch: expected UUID '{test_uuid_val}', got '{fetched.test_uuid}'"
            )
        if fetched.message != test_message:
            raise AssertionError(
                f"Payload mismatch: expected message '{test_message}', got '{fetched.message}'"
            )
        if fetched.iteration != 100:
            raise AssertionError(
                f"Payload mismatch: expected iteration 100, got {fetched.iteration}"
            )
        print(f"[SMOKE TEST] [PASS] Record retrieved and payload verified: {fetched.message}")

        # 4. Delete temporary record
        fetched.key.delete()
        print(f"[SMOKE TEST] [PASS] Record '{record_id}' deleted.")

        # 5. Confirm deletion
        verify_deleted = _InfrastructureSmokeTestEntity.get_by_id(record_id)
        if verify_deleted is not None:
            raise AssertionError(f"Record '{record_id}' was not deleted successfully!")
        print("[SMOKE TEST] [PASS] Deletion confirmed. Local database is clean.")


def main() -> int:
    print("=" * 60)
    print("Health Awareness - Datastore Emulator Connectivity Smoke Test")
    print("=" * 60)

    try:
        verify_virtual_environment()
        print(f"[ENV CHECK] Virtual environment confirmed: {sys.prefix}")

        host, port = verify_local_emulator_host()
        print(f"[SAFETY CHECK] Local loopback verified: {host}:{port}")

        project_id = os.environ.get("DATASTORE_PROJECT_ID", "health-awareness-local")
        run_smoke_test(project_id=project_id)

        print("=" * 60)
        print("ALL INFRASTRUCTURE CHECKS PASSED: Local Datastore emulator is functional!")
        print("=" * 60)
        return 0

    except Exception as exc:
        print(f"\n[SMOKE TEST FAILED] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
