# HealthAware — Local Demo Runbook

**Audience:** Presenters, reviewers, and engineering team members.  
**Purpose:** Step-by-step instructions for conducting a smooth 5-to-10-minute live demonstration of HealthAware on Windows 11.  
**Prerequisites:** Windows 11 with PowerShell, Google Cloud SDK (Firestore emulator component), Python 3.12 (`backend\.venv`), Node.js, and Java 21 LTS.

---

## 1. Verified Startup Commands

Open three separate Windows PowerShell terminal windows at the project root (`C:\Users\nalli\project-internship\health-awareness`):

### Terminal 1 — Start the Datastore Emulator
```powershell
.\scripts\start-emulator.ps1
```
- **Port:** `127.0.0.1:8080`
- **Persistence:** Automatically detects and loads the latest export snapshot from `local_db\datastore_export\`.
- **Exit Hook:** Configured with `--export-on-exit` to ensure persistence across sessions.

### Terminal 2 — Start the Flask Backend API
```powershell
.\scripts\start-backend.ps1
```
- **Port:** `http://127.0.0.1:5000`
- **Routing:** Automatically directs all database operations to `DATASTORE_EMULATOR_HOST=127.0.0.1:8080`.
- **Verification:** Confirm health status by running:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/health"
  ```
  Expected output: `{"data": {"status": "healthy"}, "meta": {"api_version": "v1"}}`

### Terminal 3 — Start the Angular Frontend Dev Server
```powershell
.\scripts\start-frontend.ps1
```
- **Port:** `http://127.0.0.1:4200`
- **Proxy:** All `/api/*` network requests are automatically reverse-proxied to `http://127.0.0.1:5000`.

---

## 2. Essential Local URLs

| Section | Local URL | Description |
| :--- | :--- | :--- |
| **Learner Home** | `http://127.0.0.1:4200` | Landing page, mission statement, featured topics, quick navigation |
| **Topics Catalog** | `http://127.0.0.1:4200/topics` | Overview of all 4 published health topics |
| **Personal Hygiene** | `http://127.0.0.1:4200/topics/topic-hygiene` | Effective Handwashing Techniques |
| **Safe Water** | `http://127.0.0.1:4200/topics/topic-water` | Household Water Treatment and Safe Storage |
| **Mosquito Prevention** | `http://127.0.0.1:4200/topics/topic-mosquito` | Complete 4-chapter vector control curriculum |
| **Vaccine Awareness** | `http://127.0.0.1:4200/topics/topic-vaccine` | How Vaccines Build Immunity |
| **Family Challenge** | `http://127.0.0.1:4200/challenge` | Interactive collaborative multi-generational quiz game |
| **Creator Studio** | `http://127.0.0.1:4200/creator/login` | Role-based authoring, review queue, and administration |
| **Backend API Health** | `http://127.0.0.1:5000/api/v1/health` | System liveness probe endpoint |

---

## 3. Recommended 5–10 Minute Demonstration Sequence

### Step 1: System Overview & Architecture (1 Minute)
1. Open `http://127.0.0.1:4200` in Google Chrome or Microsoft Edge.
2. Highlight that the entire application operates **100% locally** with **zero cloud cost**:
   - Google Cloud Firestore emulator running in Datastore mode on port 8080.
   - Flask REST API on port 5000 with Google Cloud NDB client.
   - Angular 19 Single Page Application on port 4200.
3. Show the responsive homepage, accessibility features, and mission-aligned evidence-based health topics.

### Step 2: Topics Catalog & Canonical Curriculum (1 Minute)
1. Navigate to **Health Topics** (`http://127.0.0.1:4200/topics`).
2. Point out the 4 canonical health topics:
   - **Personal Hygiene & Handwashing**
   - **Safe Drinking Water & Sanitation**
   - **Mosquito Prevention & Vector Control**
   - **Vaccine Awareness & Immunity**
3. Note that all 7 published lessons across these topics are loaded from the persistent local database snapshot.

### Step 3: Deep Dive — Mosquito Prevention & Vector Control (4 to 5 Minutes)
1. Click **Mosquito Prevention & Vector Control** (`http://127.0.0.1:4200/topics/topic-mosquito`).
2. Demonstrate the structured **4-Chapter Progressive Curriculum**:
   - **Chapter 1:** *Understanding Mosquitoes and Mosquito-Borne Diseases*
   - **Chapter 2:** *Stopping Mosquito Breeding at Home*
   - **Chapter 3:** *Protect Yourself and Your Family from Mosquito Bites*
   - **Chapter 4:** *Community Prevention, Symptoms, and Seeking Care*
3. Click **Start Lesson** on **Chapter 1** (`/lessons/lesson-understanding-mosquitoes-and-m-5557`):
   - **Explanation Cards:** Show bite-sized, accessible educational content with citations to public health guidance.
   - **Knowledge Check (Quiz Card):**
     - First, deliberately select an incorrect option to show immediate, pedagogical explanatory feedback.
     - Then, select the correct option to show positive reinforcement and unlock the **Continue** button.
   - **Recap Card:** Review key takeaways and verified health sources.
   - Click **Complete Lesson** to return to the topic page.
4. Show how the topic page dynamically tracks progress (badge updates to *"Completed"* / *"Review Lesson →"*).
5. Briefly open and showcase **Chapter 2**, **Chapter 3**, or **Chapter 4** to demonstrate consistency across all chapters.

### Step 4: Family Learning Challenge (1 Minute)
1. Navigate to **Family Learning Challenge** (`http://127.0.0.1:4200/challenge`).
2. Explain the goal: A lightweight, gamified quiz format designed for shared family or community learning without barriers.
3. Select answers, inspect scoring, and demonstrate interactive feedback.

### Step 5: Creator Studio Governance & Editorial Workflow (1 to 2 Minutes)
1. Navigate to **Creator Studio** (`http://127.0.0.1:4200/creator/login`).
2. Explain the role-based editorial workflow:
   - **Contributors** author topics and lesson drafts with citations.
   - **Reviewers** audit submissions against WHO/CDC evidence standards.
   - **Admins** manage roles and enforce publishing policies.
   - Contributors cannot self-approve drafts (strict separation of duties).
   - Published versions are immutable; updates require new revisions.
3. *Note:* Local demonstration accounts are available for each role without needing credentials in presentation documentation.

---

## 4. Safe Shutdown Procedure (Zero Data Loss)

To ensure all learner progress and newly authored content are safely preserved, follow this shutdown sequence:

### Step 1: Create an On-Demand Export Snapshot
Before closing services, execute the export script from any PowerShell window:
```powershell
.\scripts\export-emulator-data.ps1
```
This writes a fresh timestamped snapshot into `local_db\datastore_export\`.

### Step 2: Stop Dev Servers
- In **Terminal 3** (Angular Frontend): Press `Ctrl+C` to terminate `ng serve`.
- In **Terminal 2** (Flask Backend): Press `Ctrl+C` to terminate the Flask API server.

### Step 3: Stop the Datastore Emulator
- In **Terminal 1** (Datastore Emulator): Press `Ctrl+C`. The emulator will flush in-memory data to `local_db\datastore_export\` as configured by `--export-on-exit`.
- If the emulator was launched in the background, run:
  ```powershell
  .\scripts\stop-emulator.ps1
  ```

---

## 5. Quick Verification Checklist

Before taking the stage, verify these items:
- [ ] Emulator is running on `127.0.0.1:8080` (`.\scripts\test-db-connection.ps1` passes).
- [ ] Backend is running on `http://127.0.0.1:5000` (`/api/v1/health` returns `200`).
- [ ] Frontend is running on `http://127.0.0.1:4200` (Home page loads cleanly).
- [ ] All 4 topics load under `/topics`.
- [ ] Mosquito Prevention displays 4 chapters in numerical order (1 through 4).
- [ ] Browser developer console shows 0 uncaught errors during navigation.
