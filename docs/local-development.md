# Local Development Guide (Windows 11)

## Overview & Zero-Cost Guarantee

This project is built to run entirely on **native Windows 11** using PowerShell and VS Code. **No paid cloud services, Google Cloud accounts, or billing activations are required.** All database interactions are simulated locally via the official Google Cloud Firestore emulator operating in Datastore mode.

---

## 1. Prerequisites

The local environment requires:
- **Operating System:** Windows 11
- **Shell:** PowerShell 5.1 or PowerShell 7+
- **Python:** 3.12.9 (installed via Windows Python Launcher, isolated in `backend\.venv`)
- **Java Runtime:** Java 21 LTS (`java version "21.0.10"` or higher)
- **Google Cloud CLI:** Google Cloud SDK 588.0.0+ with the `cloud-firestore-emulator` (1.22.0+) component installed

---

## 2. Common Workflow

### A. Terminal 1 — Start the Datastore Emulator
Run the startup script in PowerShell:
```powershell
.\scripts\start-emulator.ps1
```

- Binds to `127.0.0.1:8080` in Datastore mode.
- Automatically detects previous export metadata in `local_db\datastore_export` and imports existing data on startup.
- Configures automatic data export upon graceful shutdown.
- To stop the emulator gracefully, press `Ctrl+C` in this terminal window.

### B. Terminal 2 — Start the Backend REST API Server
With the emulator running in Terminal 1, launch the Flask API in a second PowerShell window:
```powershell
.\scripts\start-backend.ps1
```

- Binds to `127.0.0.1:5000` on local loopback.
- Connects automatically to `DATASTORE_EMULATOR_HOST=127.0.0.1:8080`.
- Serves endpoints under `http://127.0.0.1:5000/api/v1`.
- Verify process liveness:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/health"
  ```

### C. Terminal 3 — Run Connectivity Smoke Test
Verify Datastore emulator connectivity:
```powershell
.\scripts\test-db-connection.ps1
```

### D. Running the Backend Test Suite
We provide an automated PowerShell test runner `scripts/run-tests.ps1`:

- **Run all tests (Unit + Controller + Emulator Integration):**
  ```powershell
  .\scripts\run-tests.ps1
  ```
- **Run pure unit tests only (no emulator required):**
  ```powershell
  .\scripts\run-tests.ps1 -UnitOnly
  ```
- **Run emulator-backed integration tests only:**
  ```powershell
  .\scripts\run-tests.ps1 -IntegrationOnly
  ```
- **Run API-specific tests (Controller unit tests + API emulator tests):**
  ```powershell
  .\scripts\run-tests.ps1 -ApiOnly
  ```

Alternatively, invoke `pytest` directly inside the virtual environment:
```powershell
$env:DATASTORE_EMULATOR_HOST = "127.0.0.1:8080"
$env:DATASTORE_PROJECT_ID    = "health-awareness-local"
.\backend\.venv\Scripts\python.exe -m pytest
```

### E. Terminal 4 — Start the Angular Frontend Dev Server
In a third PowerShell window, launch the Angular development server:
```powershell
.\scripts\start-frontend.ps1
```
- Serves the Single-Page Application on `http://127.0.0.1:4200`.
- Connects to the local Flask backend at `http://127.0.0.1:5000/api/v1`.
- Fast live reloading and Vitest integration.

### F. Running the Angular Frontend Test Suite
Run the Angular frontend unit tests non-interactively:
```powershell
.\scripts\run-frontend-tests.ps1
```
Or directly from `frontend/`:
```powershell
cd frontend
npx ng test --watch=false
```

### G. Building for Production
Verify production bundle build and style budget adherence:
```powershell
cd frontend
npm run build
```

### H. Stopping the Emulator Programmatically
If the emulator was started in the background or you need to shut down the listener on port 8080:
```powershell
.\scripts\stop-emulator.ps1
```

---

## 3. Data Persistence & Export/Import

The Datastore-mode emulator runs in memory by default. Data persistence is managed via import and export:

### Automatic Persistence on Startup & Shutdown
- `scripts/start-emulator.ps1` passes `--export-on-exit=local_db\datastore_export`.
- When stopped cleanly (via `Ctrl+C`), data snapshots are saved to `local_db\datastore_export`.
- On the next startup, `scripts/start-emulator.ps1` auto-detects `*.overall_export_metadata` and imports it via `--import-data`.

### Manual On-Demand Data Export
To snapshot current database state while the emulator is actively running:
```powershell
.\scripts\export-emulator-data.ps1 -ExportDir "local_db\datastore_export"
```

### Resetting the Database
To reset the local database to an empty initial state:
1. Stop the emulator: `.\scripts\stop-emulator.ps1`
2. Delete the local export folder:
   ```powershell
   Remove-Item -Recurse -Force "local_db\datastore_export"
   ```
3. Restart the emulator: `.\scripts\start-emulator.ps1`

---

## 4. Troubleshooting Guide

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `Port 8080 is already occupied` | Another process is using port 8080. | Run `.\scripts\stop-emulator.ps1` to stop any orphaned emulator, or check `Get-NetTCPConnection -LocalPort 8080`. |
| `gcloud : The term 'gcloud' is not recognized` | gcloud SDK bin is missing from the active session PATH. | The scripts auto-detect `C:\Users\nalli\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin`. Or run: `$env:Path = "C:\Users\nalli\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin;$env:Path"`. |
| `Unable to connect to Datastore emulator at 127.0.0.1:8080` | Smoke test run before starting emulator. | Start the emulator in a separate terminal via `.\scripts\start-emulator.ps1`. |
| `CRITICAL SAFETY CHECK: DATASTORE_EMULATOR_HOST is not set` | Missing local environment variable. | Ensure `$env:DATASTORE_EMULATOR_HOST = "127.0.0.1:8080"` is defined before connecting. |
| `Smoke test must run inside the backend virtual environment (.venv)` | Global Python invoked instead of venv. | Always invoke `.\backend\.venv\Scripts\python.exe` or use `.\scripts\test-db-connection.ps1`. |
