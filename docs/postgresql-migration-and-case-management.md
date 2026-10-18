# HealthAware — PostgreSQL Migration & Staff Case Management Guide

## 1. Overview & Architecture

HealthAware is migrating its persistence layer from Google Cloud NDB (Datastore emulator mode) to **PostgreSQL**, structured for complete local verification and seamless compatibility with Neon serverless PostgreSQL. In addition, the **Report a Concern** workflow and protected **Staff Case Management** system have been reintroduced with strict data privacy, unguessable tracking tokens, role-based jurisdiction scoping, and append-only audit histories.

---

## 2. PostgreSQL Schema & Alembic Migrations

The relational schema is defined using **SQLAlchemy 2.x** in `backend/storage/postgres_models.py` and managed via **Alembic** in `backend/migrations/versions/0001_initial_schema.py`.

### 2.1 Curriculum Tables
- **`topics`**: Topic definitions, slugs, display ordering, and publication statuses (`draft`, `published`, `archived`).
- **`lessons`**: Lesson shells linked via foreign key to `topics.topic_id`, with explicit `display_order` and version pointers (`published_version_id`, `draft_version_id`).
- **`lesson_versions`**: Immutable version history containing `cards_json` (PostgreSQL `JSONB` for rich interactive quiz and card structures), `learning_objectives`, `source_ids`, and editorial states.
- **`health_sources`**: Citations and metadata from public health authorities (CDC, WHO, JJM, NCVBDC, MoHFW).
- **`review_records`**: Formal editorial and medical content review logs.
- **`users`**: Application and staff identities storing display names, roles, account status, and PBKDF2-HMAC-SHA256 password hashes (600,000 iterations).

### 2.2 Report a Concern & Case Management Tables
- **`concern_reports`**: Citizen sanitation reports with unique unpredictable references (`HA-YYYY-XXXXXX`), SHA-256 token hashes, geographic routing (AP / Telangana, district, locality, optional GPS), and assigned handler scopes.
- **`concern_status_events`**: Append-only audit history recording every status transition, public citizen updates, confidential internal notes, timestamps, and acting users.
- **`concern_attachments`**: Protected metadata and opaque storage keys for photo evidence stored outside public assets with EXIF stripping and magic-byte validation.
- **`staff_jurisdictions`**: Explicit authority scopes assigning municipal officers to designated states, districts, and municipalities.

---

## 3. Data Migration Utility & Parity Baseline

The migration utility `backend/storage/migrate_datastore_to_postgres.py` provides:
1. **`--dry-run`**: Audits the active Datastore source without touching the database.
2. **`--execute`**: Transactionally migrates all source records to PostgreSQL with stable identifiers and password hashes.
3. **`--verify`**: Performs full parity checks across entity counts, lesson ordering, card payloads, citations, and credential hashes.

### Verified Baseline Counts
- **Topics**: 4 (`topic-hygiene`, `topic-water`, `topic-mosquito`, `topic-vaccine`)
- **Lessons**: 7 (All canonical published lessons, including all 4 mosquito chapters in exact order: 1, 2, 3, 4)
- **Lesson Versions**: 7 (30 lesson cards, 9 quiz interactions, 27 answer options)
- **Health Sources**: 13 (CDC, WHO, JJM, NCVBDC citations)
- **Users**: 3 (`admin`, `contributor`, `reviewer`)

### Datastore Emulator Snapshot Protection
The source Datastore emulator database has been protected and backed up to:
`local_db/datastore_export/datastore_export_1792319180` (created Oct 18 15:56:20).

---

## 4. Reproducible Clean Initialization (Bootstrap)

A version-controlled canonical curriculum is preserved in `backend/canonical_curriculum.json`.
To initialize any clean PostgreSQL database reproducibly without touching Datastore or user drafts:
```powershell
.\backend\.venv\Scripts\python.exe backend/bootstrap_postgres.py --database-url "postgresql://postgres:postgres@localhost:5432/healthaware"
```

---

## 5. Report a Concern & Staff Case Management

### 5.1 Citizen Flow
- **Intake (`/report`)**: Mobile-first 4-step wizard:
  1. *Category*: Accumulated garbage, stagnant water / mosquitoes, blocked drains / sewage, poor public-toilet sanitation.
  2. *Location*: State (AP or Telangana), District, Municipality (or "Not sure"), Locality/Landmark, optional GPS.
  3. *Details*: Observed duration, description, optional photo evidence (stripped of EXIF metadata).
  4. *Confirmation*: Generates unique Reference ID and High-Entropy Tracking Token. Confirms: **"Your concern has been received by HealthAware."**
- **Private Tracking (`/track`)**:
  - Requires Reference ID + Private Tracking Token.
  - Returns public status events and progress updates.
  - Confidential staff notes and handler IDs are strictly omitted.
  - Supports citizen response submission when additional information is requested.

### 5.2 Staff Case Management (`/staff`)
- **HealthAware Administrator**: System-wide oversight, assignment management, and jurisdiction provisioning.
- **Case Handler / Moderator**: Review concerns, classify issues, request additional information, post internal notes and public citizen updates, resolve or reject complaints.
- **Jurisdiction-Scoped Officer**: Restricted strictly to cases within explicitly assigned state and district boundaries. Cannot view or modify cases outside their scope.

---

## 6. Local PostgreSQL Setup Required for Final Cutover

Per the project safety gate, local PostgreSQL is not currently running on this Windows machine.

### Next Steps to Complete Database Cutover:
1. **Install PostgreSQL on Windows 11**:
   Using Windows Package Manager (PowerShell):
   ```powershell
   winget install PostgreSQL.PostgreSQL --source winget
   ```
   Or download the official installer from: `https://www.postgresql.org/download/windows/`
2. **Start the PostgreSQL Service**:
   ```powershell
   Start-Service postgresql-x64-18
   ```
3. **Create the Database and User**:
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres healthaware
   ```
4. **Configure `.env`**:
   Copy `.env.example` to `.env` and set:
   ```env
   DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/healthaware
   TEST_DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/healthaware_test
   ```
5. **Run Alembic Migrations & Migration Utility**:
   ```powershell
   .\backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
   .\backend\.venv\Scripts\python.exe backend/storage/migrate_datastore_to_postgres.py --execute
   .\backend\.venv\Scripts\python.exe backend/storage/migrate_datastore_to_postgres.py --verify
   ```

---

## 7. Hosted Neon Deployment Readiness

When ready to host on Neon:
1. Provide the Neon pooled connection URL in `DATABASE_URL`:
   `postgresql://[user]:[password]@[endpoint].neon.tech/healthaware?sslmode=require`
2. Alembic migrations and SQLAlchemy pooling (`pool_pre_ping=True`, SSL require) are already pre-configured for Neon.
3. Configure cloud object storage (e.g. S3 or GCS) for attachments before hosting on ephemeral serverless platforms.
