"""Persistence verification test for Datastore emulator import/export."""

import argparse
import json
import os
import shutil
import sys
import urllib.request
from google.cloud import ndb


class PersistenceVerificationEntity(ndb.Model):
    """Temporary model to verify data preservation across emulator restarts."""
    payload = ndb.StringProperty(required=True)


def export_emulator_data(export_dir: str, project_id: str = "health-awareness-local") -> None:
    """Invokes emulator REST export API."""
    abs_export_dir = os.path.abspath(export_dir)
    os.makedirs(abs_export_dir, exist_ok=True)
    url = f"http://127.0.0.1:8080/emulator/v1/projects/{project_id}:export"
    payload = {
        "database": f"projects/{project_id}/databases/",
        "export_directory": abs_export_dir.replace("\\", "/"),
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = resp.read().decode("utf-8")
        print(f"[EXPORT] Response status {resp.status}: {result}")


def phase_save(export_dir: str, project_id: str = "health-awareness-local") -> None:
    """Step 1: Save entity and trigger export."""
    client = ndb.Client(project=project_id)
    with client.context():
        entity = PersistenceVerificationEntity(id="persist-check-1", payload="VERIFIED_PERSISTENCE_VALUE")
        entity.put()
        print("[PHASE SAVE] Record 'persist-check-1' written to emulator.")

    export_emulator_data(export_dir, project_id)
    print(f"[PHASE SAVE] Data successfully exported to {export_dir}")


def phase_verify(export_dir: str, project_id: str = "health-awareness-local") -> None:
    """Step 2: Read back entity after restart and clean up."""
    client = ndb.Client(project=project_id)
    with client.context():
        entity = PersistenceVerificationEntity.get_by_id("persist-check-1")
        if entity is None:
            raise AssertionError("PERSISTENCE FAILED: Record was not found after emulator restart with import!")
        if entity.payload != "VERIFIED_PERSISTENCE_VALUE":
            raise AssertionError(f"PERSISTENCE FAILED: Unexpected payload '{entity.payload}'")
        print(f"[PHASE VERIFY] [PASS] Record retrieved after restart: '{entity.payload}'")

        # Clean up record
        entity.key.delete()
        print("[PHASE VERIFY] Cleaned up test record.")

    # Clean up test export folder if exists
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir, ignore_errors=True)
        print(f"[PHASE VERIFY] Cleaned up temporary export directory {export_dir}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["save", "verify"], required=True)
    parser.add_argument("--export-dir", default="local_db/test_export")
    args = parser.parse_args()

    project_id = os.environ.get("DATASTORE_PROJECT_ID", "health-awareness-local")
    if args.phase == "save":
        phase_save(args.export_dir, project_id)
    elif args.phase == "verify":
        phase_verify(args.export_dir, project_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
