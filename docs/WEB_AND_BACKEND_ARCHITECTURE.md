# HealthAware — Web Application & Backend Architecture Guide

**Document Version:** 1.0.0  
**Target Systems:** Desktop & Mobile Web Frontend, Python Flask REST API, Neon PostgreSQL, Cloudflare Pages Edge, Render Cloud Compute, Neon S3 Object Storage  
**Scope:** Architecture, tech stack justifications, API security, authentication flows, database connection models, multi-cloud communications, failure recovery, and deployment secrets.

---

## 1. Executive Summary & Technology Stack

HealthAware is an evidence-based public health micro-learning and citizen reporting platform. The architecture separates client delivery, edge security proxying, business logic, relational persistence, and private multimedia storage into decoupled, zero-cost cloud tiers.

```
+---------------------------------------------------------------------------------------------------+
|                                  PUBLIC INTERNET / WEB CLIENTS                                    |
|             Desktop Browsers (Chrome, Firefox, Safari, Edge) & Mobile Responsive Browsers          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                    +-----------------------------+-----------------------------+
                    | (1) Static SPA Requests                                   | (2) API Requests
                    |     (HTML, JS, CSS, Assets)                               |     (/api/v1/*)
                    v                                                           v
+---------------------------------------+                   +---------------------------------------+
|     CLOUDFLARE PAGES GLOBAL CDN       |                   |   CLOUDFLARE PAGES FUNCTIONS (PROXY)  |
| - Unlimited Static Asset Bandwidth    |                   | - Edge Reverse Proxy ([[path]].ts)    |
| - SPA Rewrite: /* -> /index.html      |                   | - Injects X-HealthAware-Proxy-Secret  |
| - Edge Caching across 330+ Cities     |                   | - Overwrites CF-Connecting-IP         |
| - First-party Cookie Domain Match     |                   | - Intercepts Hibernation (503 Catch)  |
+---------------------------------------+                   +---------------------------------------+
                                                                                |
                                                                                | HTTPS with Proxy Secret
                                                                                v
                                                            +---------------------------------------+
                                                            |          RENDER WEB SERVICE           |
                                                            | - Python 3.12 + Gunicorn (WSGI)       |
                                                            | - Flask Modular REST API              |
                                                            | - Proxy Secret Authorization Check    |
                                                            | - Flask-Limiter (In-Memory IP Limiting|
                                                            | - PBKDF2 Hashing & Anti-CSRF Token    |
                                                            +---------------------------------------+
                                                                  |                           |
                                      Pooled SQL Queries (5432)   |                           | Boto3 Private S3 SDK
                                                                  v                           v
                                    +-------------------------------+   +-------------------------------+
                                    |    NEON SERVERLESS POSTGRES   |   |    NEON S3 OBJECT STORAGE     |
                                    | - PostgreSQL 16/17 + JSONB    |   | - Private S3-Compatible Bucket|
                                    | - Pooled Port: PgBouncer      |   | - Private Citizen Evidence    |
                                    | - Direct Port: DDL Migrations |   | - Authorization-Gated Stream  |
                                    | - Scale-to-Zero Compute       |   | - EXIF & Magic-Byte Sanitized |
                                    +-------------------------------+   +-------------------------------+
```

### Complete Technology Matrix

| Layer | Technology | Version | Purpose in HealthAware |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | **Angular** | 22.2.0 | Reactive Single Page Application (SPA), standalone components, reactive signals. |
| **Language (Client)** | **TypeScript** | 5.9 / 6.0 | End-to-end type safety, strict compile-time interface verification. |
| **Backend Runtime** | **Python** | 3.12.9 | High-performance, clean domain modeling inspired by the Oppia Foundation architecture. |
| **Web Framework** | **Flask** | 3.1.3 | Micro-framework providing modular blueprints, request lifecycle hooks, and error handlers. |
| **Production WSGI** | **Gunicorn** | 23.0.0 | Pre-fork worker model using `gthread` (1 worker, 4 threads, 120s timeout) for production HTTP handling. |
| **Relational Database** | **PostgreSQL** | 16/17/18 | ACID transactions, foreign keys, relational staff applications, and JSONB lesson cards. |
| **Database ORM** | **SQLAlchemy** | 2.1.5 | Declarative schema models, connection pooling, and abstracted SQL queries. |
| **Database Migrations** | **Alembic** | 1.20.0 | Versioned, deterministic, fail-closed database migrations. |
| **Edge CDN & Proxy** | **Cloudflare Pages** | Functions | Global edge CDN, SSL termination, and same-origin reverse proxy for cookies. |
| **Cloud Compute Host** | **Render** | Free Web Service | Isolated Python container execution with automated Git deployment. |
| **Object Storage** | **Neon Object Storage** | S3 API | Secure, access-controlled private bucket for citizen complaint photo attachments. |
| **Rate Limiter** | **Flask-Limiter** | 3.8.0 | In-memory IP rate limiting using trusted proxy headers (`CF-Connecting-IP`). |

---

## 2. Why This Stack Was Chosen (And Why Others Were Rejected)

### Why Angular 22 (Client-Side SPA)?
* **Oppia Foundation Architectural Alignment:** The primary open-source benchmark for HealthAware is the Oppia educational platform, which leverages Angular and TypeScript. Adopting Angular 22 guarantees exact architectural consistency with Oppia's component hierarchies, testing paradigms, and design tokens.
* **Signals & Granular Reactivity:** Angular's reactive Signals (`signal()`, `computed()`) allow deterministic UI updates without the overhead of heavy global state managers (like NgRx or Redux).
* **Built-in HTTP Client & Interceptors:** Angular provides first-class HTTP interception (`apiTimeoutRetryInterceptor`) for transparent exponential backoff, retry ceilings, and security header injection.
* *Why NOT React / Next.js?* React is an unopinionated library that requires assembling routing, state, forms, and HTTP clients from disjointed packages. Next.js server-side rendering (SSR) requires maintaining a persistent Node.js server container in production, doubling compute costs and violating the ₹0/month deployment constraint.
* *Why NOT Vue or Svelte?* Neither aligns with Oppia's open-source codebase standards, reducing preparation value for open-source health education contributions.

### Why Python 3.12 + Flask (Backend)?
* **Clean Layered Separation:** Flask allows an Oppia-inspired architecture separating HTTP Controllers, Domain Business Logic, Storage ORM, and Platform Abstractions without framework bloat.
* **Security & Minimal Footprint:** Flask's minimal surface area makes auditability straightforward. In-memory rate limiting, double-submit CSRF protection, and constant-time secret comparisons integrate cleanly without heavy third-party baggage.
* *Why NOT Node.js / Express?* Express lacks strict architectural standards and encourages mixing database access directly in route handlers. Furthermore, Python is the primary language used by global public health researchers, data scientists, and the Oppia backend team.
* *Why NOT Django?* Django's monolithic admin, built-in session tables, and heavy ORM impose rigid opinions and database locks that interfere with serverless PostgreSQL scale-to-zero lifecycles and modern headless edge-proxy architectures.

### Why PostgreSQL with JSONB (Persistence)?
* **Relational Integrity for Governance:** Citizen complaints, staff roles (Learner, Contributor, Reviewer, Admin), review queues, and audit trails require strict foreign key constraints and ACID transaction isolation.
* **JSONB for Rich Educational Content:** While user records are strictly relational, educational curriculum cards (interactive scenarios, multi-choice options, explanation hints) vary in structure. PostgreSQL's native `JSONB` column type provides document-store flexibility within a structured relational schema.
* *Why NOT MongoDB / NoSQL?* Document databases lack enforceable cross-collection foreign key constraints. In a community health platform where a citizen complaint links to private tokens, status histories, and staff reviewer IDs, orphan records and schema drift pose severe data integrity risks.
* *Why NOT SQLite?* SQLite locks the entire database file during writes, cannot support cloud connection pooling, and cannot scale across multiple worker threads or serverless deployments.

### Why Cloudflare Pages + Render + Neon?
* **Zero Cost with Enterprise Boundaries:** This multi-cloud architecture achieves 100% zero-cost operation without requiring credit cards or trial periods that expire into billing traps.
* **Separation of Edge and Compute:** Static web assets and download binaries are delivered across Cloudflare's 330+ global edge data centers. Compute is only engaged when an authentic `/api/v1/*` request arrives.

---

## 3. What's in the App & Core Functional Modules

HealthAware organizes health awareness into four distinct functional pillars:

```
[ HealthAware Full-Stack Application ]
   │
   ├── 1. Micro-Learning Engine (Public Education)
   │     ├── Hygiene (Handwashing, Food Safety, Sanitation)
   │     ├── Safe Drinking Water (Boiling, SODIS, Storage Protection)
   │     ├── Mosquito Prevention (Vector Elimination, Breeding Control)
   │     └── Vaccination Awareness (Schedules, Herd Immunity, Misconceptions)
   │
   ├── 2. Citizen Concern Portal (Community Incident Reporting)
   │     ├── Anonymous or Verified Incident Submission
   │     ├── Cryptographic Private Tracking Token Issuance
   │     ├── Private Evidence Photo Upload (Camera/File)
   │     └── Jurisdiction-Aware Status Tracking (/track)
   │
   ├── 3. Creator Studio & Review Workflow (Educational Governance)
   │     ├── Role Application Wizard (Contributor & Reviewer)
   │     ├── Pure Email OTP Verification & Account Staging
   │     ├── Topic & Lesson Interactive Editor
   │     └── Review Queue (Draft -> Pending Review -> Published)
   │
   └── 4. Administrative Control Center (/staff/admin)
         ├── User Governance & Role Escalation
         ├── Application Decisioning (Approve / Reject)
         └── System Readiness & Storage Diagnostics
```

### 1. Interactive Micro-Learning Engine
* Lessons are partitioned into sequential **Interaction Cards**.
* Each card pairs factual public health guidance with an immediate **Understanding Check** (multiple-choice question).
* The user cannot blindly advance: selecting an option triggers instant pedagogical feedback explaining *why* the choice is correct or incorrect.
* Learning progress is continuously stored locally and synced to the cloud when authenticated.

### 2. Citizen Concern Portal & Incident Tracking
* Enables community members to report local environmental hazards (e.g., stagnant water pools, contaminated municipal taps, illegal dumping).
* Does not require account registration, protecting citizen privacy and removing barriers to reporting.
* Generates a 24-character cryptographic **Private Tracking Token** and a public **Reference ID** upon submission.
* Citizens query `/track` using this pair to view progress updates and public health authority notes without exposing their identity.

### 3. Creator Studio & Staff Governance
* A collaborative environment where health educators draft curriculum topics and interactive lessons.
* Implements a strict state-machine lifecycle: `DRAFT` $\rightarrow$ `IN_REVIEW` $\rightarrow$ `PUBLISHED` (or `REJECTED`).
* Contributors cannot self-publish: content must be reviewed and approved by an authorized Reviewer or Administrator.

---

## 4. Authentication, Security & Token Architecture

```
                  CITIZEN / APPLICANT REGISTRATION FLOW
                  
   Client Browser                                Cloudflare Proxy                        Flask Backend
         │                                               │                                     │
         │ 1. POST /auth/role-request/initiate           │                                     │
         ├──────────────────────────────────────────────>│ (Injects PROXY_SECRET)              │
         │    {name, email, role, reason}                ├────────────────────────────────────>│
         │                                               │                                     │ 2. Generate 6-digit OTP
         │                                               │                                     │ 3. Store in email_otp_challenges
         │                                               │                                     │ 4. Dispatch Email (Gmail API/SMTP)
         │                                               │<────────────────────────────────────┤
         │<──────────────────────────────────────────────┤  HTTP 200 {status: "challenge_sent"}│
         │                                               │                                     │
         │ 5. Applicant enters 6-digit OTP + Password    │                                     │
         │    POST /auth/role-request/complete           │                                     │
         ├──────────────────────────────────────────────>│ (Injects PROXY_SECRET)              │
         │    {email, otp: "123456", password: "..."}    ├────────────────────────────────────>│
         │                                               │                                     │ 6. Verify OTP & Expiration
         │                                               │                                     │ 7. Hash Password (PBKDF2)
         │                                               │                                     │ 8. Create Inactive Staff Record
         │                                               │                                     │ 9. Await Admin Decision
         │                                               │<────────────────────────────────────┤
         │<──────────────────────────────────────────────┤  HTTP 201 {reference_id: "...", ...}│
```

### Transition to Pure Email OTP Verification (Why SMS Was Removed)
Originally, staff applications tested mobile SMS OTP delivery alongside email verification. SMS verification was intentionally and completely removed across the frontend, backend, and database schema for the following technical and operational reasons:
1. **Telecom Compliance Overhead (DLT Registration):** In jurisdictions like India (Trai DLT regulations), commercial SMS providers (e.g., Fast2SMS) require registered business entities, registered sender headers, and pre-approved SMS message templates. Unregistered developer testing accounts are blocked from arbitrary OTP delivery.
2. **Carrier Delivery Failures & Cost:** SMS delivery is subject to carrier latency, Do-Not-Disturb (DND) filtering, and per-message charges that break the ₹0/month zero-cost constraint.
3. **Streamlined Security:** Transactional email verification via standard SMTP / Google OAuth 2.0 API operates globally at zero cost with high delivery reliability, zero carrier filtering, and sufficient security for educational staff onboarding.

### Password Security & Cryptographic Hashing
* Passwords submitted during staff onboarding or account creation are never stored in plaintext.
* Hashing utilizes **PBKDF2-HMAC-SHA256** with:
  * **600,000 Iterations** (exceeding OWASP recommended minimums for SHA-256).
  * **16-byte cryptographically secure random salt** generated via `secrets.token_bytes(16)`.
  * Output formatted as: `pbkdf2:sha256:600000$<salt_hex>$<hash_hex>`.
* Verification utilizes constant-time string comparison (`hmac.compare_digest`) to defeat timing attacks.

### Double-Submit Anti-CSRF Token Protection
For state-changing operations (POST, PUT, DELETE) executed by cookie-authenticated users:
1. Upon login or session initialization (`/api/v1/auth/me`), the backend generates a 32-byte cryptographic token: `secrets.token_hex(32)`.
2. The token is stored in the server-side signed session (`session["csrf_token"]`) and mirrored in a readable client cookie: `XSRF-TOKEN`.
3. Angular's HTTP client automatically reads `XSRF-TOKEN` and injects it into the request header: `X-XSRF-TOKEN` (or `X-CSRF-TOKEN`).
4. Flask's global `@app.before_request` interceptor compares the header token against the session token using `hmac.compare_digest`.
5. If the tokens do not match or the header is missing, the request is immediately rejected with `403 CSRF_ERROR`.
6. Safe idempotent HTTP methods (`GET`, `HEAD`, `OPTIONS`) are exempt from CSRF checks.

### Private Citizen Tracking Tokens
* When a citizen files a complaint without creating an account, privacy must be preserved:
  * Reference ID: Public, non-sensitive identifier (e.g. `REF-20261025-A1B2`).
  * Tracking Token: 192-bit high-entropy secret generated via `secrets.token_hex(24)`.
* In the database, the token is stored directly or as a SHA-256 hash. Citizens must present *both* the Reference ID and the Tracking Token to view incident notes, preventing enumeration attacks across public records.

---

## 5. Deployment Platforms & Cloud Communications

HealthAware orchestrates three distinct cloud providers:

```
[ Browser / Native App ]
          │
          │ HTTPS (Port 443)
          v
[ Cloudflare Pages Edge ] ── (Static Requests) ──> [ Global Edge Cache (330+ locations) ]
          │
          │ HTTPS (Port 443)
          │ Header: X-HealthAware-Proxy-Secret
          │ Header: CF-Connecting-IP
          v
[ Render Web Service ] ──── (Database Queries) ──> [ Neon Serverless PostgreSQL ]
          │                  TCP Port 5432 / 6543
          │
          │ HTTPS (Port 443)
          │ AWS Signature v4 (Boto3)
          v
[ Neon S3 Object Storage ]
```

### Communication Flow: Step-by-Step
1. **User Request:** The browser sends an API request to `https://health-awareness.pages.dev/api/v1/topics`.
2. **Cloudflare Edge Routing:** Cloudflare matches `/api/*` against `_routes.json` and invokes the edge function: `frontend/functions/api/[[path]].ts`.
3. **Header Sanitization & Injection:**
   * Reads client IP from Cloudflare's trusted network and sets `CF-Connecting-IP` and `X-Forwarded-For`.
   * Sets `Host` to `healthaware-api.onrender.com`.
   * Injects the private `X-HealthAware-Proxy-Secret`.
4. **Upstream Forwarding:** The Cloudflare worker dispatches an HTTPS subrequest to Render.
5. **Render Ingress & Verification:**
   * Render routes traffic to the Gunicorn container listening on `$PORT`.
   * Flask's before-request hook verifies that `X-HealthAware-Proxy-Secret` matches `PROXY_SECRET`. Direct requests from public scrapers lack this header and are terminated with `403 FORBIDDEN`.
6. **Data Retrieval:** Flask queries Neon PostgreSQL over TLS.
7. **Edge Response:** Gunicorn responds to Cloudflare, which preserves session cookies, sets CORS headers, and streams the response back to the client browser.

---

## 6. Secrets, Keys & Connection Strings Explained

### 1. `PROXY_SECRET`
* **What it is:** A high-entropy shared secret known only to Cloudflare Pages Functions and the Render Flask backend.
* **Why it exists:** Render gives every service a public URL (`https://<app>.onrender.com`). Without `PROXY_SECRET`, an attacker could bypass Cloudflare's WAF and DDoS the Render backend directly. By validating `X-HealthAware-Proxy-Secret` on every request, Render ensures it only serves requests routed through the Cloudflare edge proxy.

### 2. `DATABASE_URL` vs. `MIGRATION_DATABASE_URL`
Neon PostgreSQL provides two distinct connection strings:

```
Pooled URL:    postgresql://user:pass@ep-xyz-pooler.ap-southeast-1.aws.neon.tech/neondb
Direct URL:    postgresql://user:pass@ep-xyz.ap-southeast-1.aws.neon.tech/neondb
```

| Parameter | Connection Type | Target Port | Used By | Why It Matters |
| :--- | :--- | :--- | :--- | :--- |
| **`DATABASE_URL`** | **Pooled** (PgBouncer) | `5432` / `6543` | Gunicorn / Flask Web App | Web requests open and close connections rapidly. PgBouncer pools connections so thousands of requests do not overwhelm PostgreSQL's process limit. |
| **`MIGRATION_DATABASE_URL`** | **Direct Unpooled** | `5432` | Alembic Migrations | DDL statements (`CREATE TABLE`, `ALTER TABLE`, schema locks, prepared statements) **fail** under PgBouncer transaction pooling. Alembic strictly requires a direct TCP connection. |

### 3. AWS S3 Object Storage Keys (`Neon S3`)
* **`AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`:** HMAC authentication keys used by the Python `boto3` SDK to sign HTTP requests using AWS Signature Version 4.
* **`S3_ENDPOINT_URL`:** Points to Neon's S3-compatible gateway (`https://br-dawn-mouse-a1l1rlxk.storage.c-1.ap-southeast-1.aws.neon.tech`).
* **`S3_BUCKET_NAME`:** The target private bucket (`healthaware-attachments`).
* **`AWS_REGION`:** S3 signature signing region (`ap-southeast-1`).

### Why Photos Are Stored Privately (Not Public URLs)
* Community hazard reports contain private citizen photos (e.g., photos showing residential streets, houses, or individuals).
* If photos were stored in a public S3 bucket, anyone guessing or scraping the URL could view private citizen evidence without authorization.
* **How HealthAware Handles Photos:**
  1. Citizen uploads photo $\rightarrow$ Flask validates file headers with Pillow, strips all EXIF GPS metadata, resizes if needed, and streams bytes to the private S3 bucket.
  2. The S3 bucket is **100% private**: no public read access is granted.
  3. Photos are viewed strictly through Flask streaming routes (`/api/v1/concerns/<id>/attachment`) which verify either the citizen's Private Tracking Token or an authenticated Staff Reviewer session before streaming bytes.

---

## 7. Failure Handling, Cold Starts & Rate Limiting

### The Render Free-Tier Hibernation Cycle
* **15-Minute Inactivity Rule:** On the free plan, Render spins down web service containers to 0 instances after 15 minutes without traffic to conserve instance hours.
* **The Cold Start Problem:** When a new visitor arrives, Render wakes up the container. This boot cycle takes 30 to 50 seconds.
* **The "Too Many Requests" (429) Trigger:** If multiple requests bombard a sleeping Render instance before it finishes booting, Render's edge router rejects them with:
  ```http
  HTTP/1.1 429 Too Many Requests
  x-render-routing: hibernate-rate-limited
  ```
* **How Cloudflare Solves This:** In `frontend/functions/api/[[path]].ts`, the edge proxy detects `x-render-routing: hibernate-rate-limited`. Instead of passing a cryptic 429 to the client, it returns a clean `503 BACKEND_STARTING` with `Retry-After: 30`.

### Angular Interceptor Resilience
In [`api-timeout-retry.interceptor.ts`](file:///c:/Users/nalli/project-internship/health-awareness/frontend/src/app/interceptors/api-timeout-retry.interceptor.ts):
* Idempotent read requests (`GET`) automatically retry up to 2 times with exponential backoff and jitter (`baseDelay * 2^(retry-1) + jitter`).
* Mutating operations (`POST`, `PUT`, `DELETE`) are **never retried automatically**, preventing duplicate reports or double-submitted applications.
* Technical database strings, hostnames, and stack traces are masked via `sanitizeErrorMessage()` before surfacing user-facing feedback.

---

## 8. Containerization with Docker

The repository includes a production-hardened `Dockerfile` allowing deployment to any standard container platform (Render, Koyeb, Fly.io, or self-hosted Docker):

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies for PostgreSQL compilation (psycopg2) and image processing (Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source
COPY . /app

EXPOSE 8000

# Execute Gunicorn production WSGI server
CMD ["sh", "-c", "gunicorn \"backend.app:create_app()\" --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120"]
```

### Key Docker Optimizations
* `python:3.12-slim`: Reduces image size from 1 GB (full Debian) to under 200 MB, speeding up container spin-up and reducing cold-start latency.
* `libpq-dev` & `gcc`: Required during `pip install` to build native C extensions for `psycopg2` and `Pillow`.
* `.dockerignore`: Prevents `node_modules`, test caches, `.git`, and local virtual environments from inflating the container build context.
