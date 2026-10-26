# Digital Health Awareness Web Application

## Overview

The **Digital Health Awareness Web Application** is an accessible, interactive health education platform designed to promote foundational public health knowledge. The application provides interactive lessons and assessments covering:

- **Personal and Food Hygiene:** Best practices for handwashing, sanitation, and food handling.
- **Safe Drinking Water:** Water treatment, safe storage, and contamination prevention.
- **Mosquito Prevention:** Vector control, elimination of stagnant water, and protection against vector-borne diseases.
- **Vaccination Awareness:** Routine immunization schedules, community immunity, and dispelling common misconceptions.

This project draws inspiration from the **Oppia Foundation's** educational approach and layered software architecture, serving as preparation for open-source contributions to Oppia and GSoC 2027.

---

##Technology Stack

- **Frontend:** Angular + TypeScript
- **Backend:** Python
- **Storage Interface:** Google Cloud NDB (`google-cloud-ndb`)
- **Local Database Development:** Local Datastore emulator (e.g., Google Cloud SDK Datastore emulator)
- **Testing:** Angular testing tools (Jasmine/Karma/Jest) and Python unit tests (`unittest`/`pytest`)
- **Development OS:** Windows 11 exclusively (PowerShell & VS Code)

> **Excluded Technologies:** React, Node.js/Express backend, and MongoDB are explicitly excluded from this stack.

---

## Constraints & Objectives

1. **Windows 11 Development Constraint:** All scripts, tooling, commands, and workflows are tailored strictly for PowerShell and native Windows 11 environments without requiring Linux/WSL dependencies.
2. **Zero-Cost Local Development:** The project does not require paid services, cloud billing accounts, or cloud deployment. All components—including the backend, frontend, and datastore emulator—are designed to run locally with zero cloud costs.
3. **Modular Layered Architecture:** The backend adopts an Oppia-inspired layered architecture separating HTTP controllers, domain business logic, storage access (NDB models), and platform abstractions.

---

## Local Development Quickstart

Detailed documentation is available in [docs/local-development.md](docs/local-development.md) and [docs/architecture.md](docs/architecture.md).

### 1. Start the Local Datastore Emulator
```powershell
.\scripts\start-emulator.ps1
```

### 2. Start the Backend REST API Server
```powershell
.\scripts\start-backend.ps1
```

### 3. Verify Database Connectivity Smoke Test
```powershell
.\scripts\test-db-connection.ps1
```

### 4. Run the Backend Test Suite
```powershell
.\scripts\run-tests.ps1
```

### 5. Start the Angular Frontend Dev Server
```powershell
.\scripts\start-frontend.ps1
```
The application will be accessible at: `http://127.0.0.1:4200`

### 6. Run the Frontend Test Suite
```powershell
.\scripts\run-frontend-tests.ps1
```

### 7. Stop the Local Emulator
```powershell
.\scripts\stop-emulator.ps1
```

