# HealthAware — Zero-Cost Deployment Readiness Assessment

**Document Version:** 2.4.0  
**Target Architecture:** ₹0 / Month Public Demonstration & Portfolio Deployment  
**Scope:** Production architecture design, provider quota boundaries, repository inspection, origin security, safe migration procedures, and implementation roadmap.  
**Constraint:** Documentation and planning only. No cloud resources, credentials, or application code modifications are created in this phase.

---

## 1. Executive Summary & Recommended Architecture

HealthAware is a full-stack, evidence-based community health education and citizen reporting application. It combines an Angular 22 frontend, a Python 3.12 Flask backend, a relational PostgreSQL 18 schema with JSONB rich-content modeling, and a protected citizen complaint evidence workflow.

To achieve a true **₹0 / month operating cost** for a public demonstration and portfolio release without sacrificing security, authentication stability, or data protection, the recommended architecture consists of:

1. **Frontend Hosting:** **Cloudflare Pages (Free Tier)**
   - Project Root: `frontend`
   - Build Output Directory: `dist/health-awareness-frontend/browser`
   - Build Runtime: **Node.js 24.15.0 LTS** (matching Angular 22's official `^22.22.3 || ^24.15.0 || ^26.0.0` compatibility matrix and npm 11).
   - Delivers the compiled Angular Single Page Application (SPA) across Cloudflare’s global edge network with unlimited static asset bandwidth.
   - SPA routing enforced via `frontend/public/_redirects` (`/*  /index.html  200`).
   - Function invocation scoping enforced via `frontend/public/_routes.json` (`"include": ["/api/*"]`) so static assets and HTML never consume the Function execution quota.
2. **Same-Origin API Proxy:** **Cloudflare Pages Functions (Free Tier)**
   - Located at `frontend/functions/api/[[path]].ts` (matching the `frontend` Pages project root).
   - Routes `/api/*` requests through an edge function to a fixed backend origin.
   - Solves cross-origin cookie blocking (Safari ITP, Chrome Privacy Sandbox, Firefox ETP) by ensuring all session and tracking cookies remain first-party host-only cookies.
   - Overwrites client-supplied IP forwarding headers with trusted `CF-Connecting-IP`.
   - Injects a server-side shared proxy secret (`X-HealthAware-Proxy-Secret`) to verify that API requests originate strictly through the Cloudflare edge.
3. **API & Business Logic:** **Render Web Services (Free Tier / Hobby)**
   - Hosts the Python 3.12 / Flask REST API using Gunicorn (`--workers 1 --threads 4`) as the production WSGI server.
   - Explicitly validates `APP_ENV` upfront, accepting only `development` or `production`, and failing closed with HTTP 500 on missing or invalid configurations.
   - Enforces fail-closed proxy secret validation (using constant-time comparison across candidate secrets), role-based access control, image sanitization (magic bytes, EXIF stripping), and best-effort in-memory rate limits keyed by trusted client IP.
   - Explicitly maps `FLASK_SECRET_KEY` to Flask's `SECRET_KEY` configuration before session usage, requiring a high-entropy secret in production with no development defaults.
   - Outbound bandwidth budget calibrated strictly within Render's **5 GB / month** free allowance. No payment method attached (service suspends safely if quota is exhausted). Rollback supported to the two most recent previous deployments on the Free plan.
4. **Relational Database:** **Neon Serverless PostgreSQL (Free Tier)**
   - Provides fully managed PostgreSQL 16/17/18 with native JSONB support.
   - Free plan includes up to **100 projects**, each with 1 GB storage, 100 Compute Unit (CU) hours per month, 5 GB monthly egress, serverless scale-to-zero, and up to 10 branches per project.
   - Schema migrations fail closed: Alembic explicitly validates `APP_ENV`, strictly requiring `MIGRATION_DATABASE_URL` (direct unpooled connection on port 5432) in production with no silent fallback to pooled runtime URLs, and rejecting missing or invalid environment flags with a configuration error.
5. **Private Attachment Storage:** **Neon Object Storage / S3-Compatible Private Bucket**
   - Stores citizen evidence photos in an access-restricted private bucket outside the public web root.
   - Accessible from Flask via standard `boto3` client methods. Photo bytes are authorized and streamed strictly through existing citizen tracking token and staff jurisdiction checks.

### Architecture & Request Flow Diagram

```
                                  +--------------------------------------------+
                                  |            Citizen / Staff Browser         |
                                  +--------------------------------------------+
                                        |                                |
                       (1) Static Asset |               (2) API Requests |
                           Requests     |                   & Cookies    |
                           (e.g. /)     |                   (/api/v1/*)  |
                                        v                                v
                     +--------------------------------------------------------------+
                     |                 Cloudflare Pages Edge Network                |
                     |               (https://healthaware.pages.dev)                |
                     +--------------------------------------------------------------+
                           |                                        |
              [Static Cache Match]                          [_routes.json Match]
              Static HTML, JS, CSS, Assets                  Only /api/* -> frontend/functions/
              (Zero Function Invocations)                   api/[[path]].ts
                           |                                        |
                           v                                        v (3) Forward Subrequest
              +-------------------------+                   +--------------------------------+
              | Cloudflare Global Edge  |                   | Cloudflare Pages Function      |
              | (Fast Static Delivery)  |                   | - Fixed Render origin          |
              +-------------------------+                   | - Preserves host-only cookies  |
                                                            | - Overwrites client IP headers |
                                                            | - Injects X-Proxy-Secret       |
                                                            | - Zero request body logging    |
                                                            +--------------------------------+
                                                                            |
                                                                            v (HTTPS subrequest)
                                                            +--------------------------------+
                                                            | Render Free Web Service        |
                                                            | Python 3.12 + Flask + Gunicorn |
                                                            | - APP_ENV in (dev, prod)       |
                                                            | - Explicit Flask SECRET_KEY    |
                                                            | - Fail-Closed Proxy Secret     |
                                                            | - is_valid_proxy_secret()      |
                                                            | - Custom get_trusted_client_ip |
                                                            | - In-Memory Rate Limiter       |
                                                            +--------------------------------+
                                                                 |                     |
                                            (4) SQL Queries /    |                     | (5) Private Media
                                                Connection Pool  |                     |     Streaming
                                                                 v                     v
                                                +----------------------+  +-------------------------+
                                                | Neon PostgreSQL      |  | Neon Object Storage     |
                                                | Serverless DB        |  | (S3-Compatible Private) |
                                                | (healthaware DB)     |  | (Private Photo Bucket)  |
                                                +----------------------+  +-------------------------+
```

---

## 2. Zero-Cost Boundary & Provider Quotas Assessment

The table below delineates verified free tier boundaries across each chosen provider, distinguishing official provider limits from HealthAware usage expectations, suspension behaviors, and safe exhaustion modes.

| Provider & Service | Intended Free Plan | Documented Resource Allowance | Expected HealthAware Usage | Cold-Start & Inactivity Behavior | Failure / Throttle Threshold | Payment Method Required? | Conditions Leaving ₹0 Tier |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Cloudflare Pages** (Frontend) | Pages Free | • Unlimited bandwidth<br>• 500 builds / month<br>• 1 concurrent build<br>• 20,000 files / site | • ~1 MB bundle<br>• ~15–30 builds / month<br>• Node 24.15.0 runtime | Instant edge delivery. No cold starts for static assets. | Build queue delay if > 500 builds/mo. | **No** | Explicit upgrade to Pro ($20/mo). Free plan never auto-bills. |
| **Cloudflare Pages Functions** (Proxy) | Workers Free | • 100,000 requests / day<br>• 10 ms CPU time / request<br>• 128 MB RAM<br>• 100 MB request body limit | • ~500–2,000 req / day (demo traffic)<br>• < 1 ms CPU time (proxying)<br>• < 5 MB multipart uploads | Zero cold start for edge isolates. Network I/O waiting time on Render (`await fetch`) does **not** consume CPU time. | HTTP 1102 if CPU time exceeds 10 ms. HTTP 1015 if daily invocations exceed 100,000. | **No** | Explicit upgrade to Workers Paid ($5/mo). |
| **Render** (API Backend) | Web Service Free (Hobby) | • 750 instance hours / month<br>• 512 MB RAM<br>• 0.1 CPU core<br>• **5 GB outbound bandwidth / month**<br>• Inbound bandwidth free & unmetered<br>• Rollback to **two most recent previous deploys**<br>• Ephemeral storage | • 1 web service = 720–744 hrs / month (fits 1 service 24/7)<br>• ~120–180 MB RAM<br>• **~550 MB – 1 GB outbound bandwidth / month** | **Spins down after 15 min of inactivity.** Initial spin-up latency is **50–60 seconds**. | **Service suspended until 1st of next month** if instance hours exceed 750 or outbound bandwidth exceeds 5 GB. | **No** | Attaching a payment method enables paid overages at **$0.15/GB** for public internet traffic or explicit upgrade to Starter ($7/mo). **Do not attach payment method.** |
| **Neon** (Database) | Neon Free | • **Up to 100 projects**<br>• Per project: 1 GB storage<br>• 100 CU-hours / month<br>• 5 GB data egress / month<br>• Up to 10 branches per project | • 1 project used<br>• ~15 MB storage (curriculum + demo reports)<br>• ~5–15 CU-hours / month<br>• < 500 MB egress / month | **Auto-suspends after 5 min of inactivity.** Resumes in **~500 ms** upon incoming connection. | Compute suspended until next calendar month if 100 CU-hours or 5 GB egress reached. Database becomes read-only if 1 GB storage cap is reached. | **No** | Explicit upgrade to Launch ($19/mo). |
| **Neon Object Storage / S3** (Private Media) | Free Project Storage | • Storage allocated within project quota<br>• Egress network transfer subject to project bandwidth allowance | • < 50 MB total for demo photos (< 100 test photos at 500 KB avg) | Handled over standard HTTPS S3 API. No cold start. | Storage cap enforced by project quota. Access blocked if project storage limit reached. | **No** (within Neon free project) | Exceeding project storage allocation. |

### 2.1 Render Free-Tier Bandwidth Budget Analysis
Render's official Free Web Service allowance includes **5 GB of outbound bandwidth per month** to the public internet (inbound bandwidth is free and unmetered). 

**Strict ₹0 Requirement & Safe Suspension Behavior:**
* **Do NOT attach a payment method or credit card.**  
  If a payment method were on file, Render would bill public internet bandwidth overages at **$0.15 per GB**.
* **Zero Billing Risk via Service Suspension:**  
  When no payment method is linked, Render does not charge overages; instead, Render **automatically suspends the web service** once the 5 GB included outbound bandwidth is reached. The service remains suspended until the first day of the next calendar month.
* **No Guaranteed Availability Post-Quota:**  
  Service availability is **not guaranteed** after the 5 GB quota is reached. Availability will cease immediately upon quota exhaustion.

**Bandwidth Consumption Modeling:**
1. **JSON REST API Traffic:**
   - Topics, lessons, quiz evaluations, complaint creation, status checks, and authentication payloads average ~5 KB per response.
   - At an expected demonstration load of 2,000 API requests/day (60,000 requests/month):
     $$\text{API Bandwidth} = 60{,}000 \times 5\text{ KB} \approx 300\text{ MB / month}$$
2. **Private Evidence Photo Transfers:**
   - Uploaded complaint attachments are sanitized and compressed to an average of ~500 KB per photo.
   - For demo evaluations, assuming 100–200 photo viewings per month by case handlers and citizens:
     $$\text{Photo Bandwidth} = 200 \times 500\text{ KB} \approx 100\text{ MB / month}$$
   - Even under heavy evaluation traffic of 1,000 photo viewings per month:
     $$\text{Peak Photo Bandwidth} = 1{,}000 \times 500\text{ KB} \approx 500\text{ MB / month}$$
3. **Service-Initiated Outbound Traffic:**
   - Outbound HTTP requests from Flask (e.g. S3 object retrieval from Neon Object Storage): S3 fetch traffic to Flask is inbound to Render (unmetered); the subsequent streaming to Cloudflare Pages is outbound (accounted for in the photo transfer budget above).
4. **Total Expected Outbound Bandwidth:**
   - Normal monthly usage: **~400 MB to 600 MB / month** (~10% of the 5 GB quota).
   - High-activity evaluation: **~1.0 GB / month** (~20% of the 5 GB quota).
   - **Safety Margin:** Under typical portfolio review traffic, 5 GB provides sufficient headroom. However, automated scrapers or abusive traffic could exhaust the quota, which will trigger service suspension until month-end rather than generating unexpected charges.

---

## 3. Node.js Runtime Verification for Frontend Build

### 3.1 Version Specification
* **Proposed Build Runtime:** **Node.js 24.15.0 (Active LTS)**
* **Environment Variable:** `NODE_VERSION: 24.15.0` configured in Cloudflare Pages dashboard.

### 3.2 Angular 22 Compatibility Verification
According to Angular's official Version Compatibility table:
1. **Angular 22 Baseline:**
   - Angular 22 officially supports Node.js versions matching the SemVer range:  
     `^22.22.3 || ^24.15.0 || ^26.0.0`
   - **Important:** Support for Node.js 20 was dropped in Angular 22. **Node 20 is NOT supported by Angular 22.**
2. **Selected Runtime:**
   - **Node.js 24.15.0** is the selected deployment runtime. It is the active LTS release within the supported compatibility range and bundles npm 11 natively.
3. **Package Manager & Lockfile:**
   - `frontend/package.json` specifies `"packageManager": "npm@11.12.1"`.
   - `frontend/package-lock.json` uses `lockfileVersion: 3`.
   - Node 24.15.0 installs dependencies deterministically via `npm ci` without lockfile version conflicts or peer dependency breakage.
4. **Local Independence:**
   - Specifying `NODE_VERSION: 24.15.0` applies exclusively to Cloudflare Pages' build container; the local project dependencies and development environment remain unmodified.

---

## 4. Cloudflare Pages Project Layout & Route Configuration

To ensure consistent project layout and prevent edge function invocation overages, the repository layout places the Functions directory directly inside the Pages project root.

### 4.1 Repository Layout
```
health-awareness/
├── backend/                              # Flask API service (deployed to Render)
├── frontend/                             # Cloudflare Pages Project Root
│   ├── functions/                        # Cloudflare Pages Functions
│   │   └── api/
│   │       └── [[path]].ts               # Edge proxy for /api/*
│   ├── public/                           # Static assets copied directly to build output
│   │   ├── _redirects                    # Client-side SPA routing rules
│   │   ├── _routes.json                  # Function invocation routing rules
│   │   ├── favicon.ico
│   │   └── assets/
│   ├── src/                              # Angular TypeScript source code
│   ├── package.json
│   └── angular.json
└── docs/
    └── deployment-readiness.md
```

### 4.2 Function Scoping via `_routes.json`
By default, Cloudflare Pages runs a deployed Function on *every* incoming request if a `functions/` directory exists. To prevent static frontend assets (HTML, JavaScript bundles, CSS, images, fonts) from consuming the free daily 100,000 Function request quota, a `_routes.json` file is placed in `frontend/public/_routes.json` (copied to `dist/health-awareness-frontend/browser/_routes.json` upon build).

**`frontend/public/_routes.json`:**
```json
{
  "version": 1,
  "include": [
    "/api/*"
  ],
  "exclude": []
}
```

* **Effect:** Cloudflare’s edge routing engine intercepts *only* paths matching `/api/*` for execution by `frontend/functions/api/[[path]].ts`.
* **Static Assets:** Requests for `/`, `/main.js`, `/styles.css`, `/assets/*`, etc., are served directly by Cloudflare's static asset cache at zero Function invocation cost.

### 4.3 Client-Side SPA Routing via `_redirects`
Because Angular utilizes HTML5 pushState routing (`@angular/router`), deep links (e.g. `/topics/topic-mosquito`, `/report`, `/track`, `/staff`) must resolve to `index.html` when refreshed in the browser.

**`frontend/public/_redirects`:**
```
/*  /index.html  200
```

* **Interaction with `_routes.json`:**  
  When a user refreshes `/report`:
  1. Cloudflare checks `_routes.json`: `/report` does not match `/api/*`, so the Function is **not** invoked.
  2. Cloudflare checks for a static file named `/report`. None exists.
  3. Cloudflare evaluates `_redirects`: `/*` matches `/report`, serving `/index.html` with HTTP 200.
  4. Angular initializes in the browser and navigates to the Report a Concern route.

---

## 5. Public Backend Origin Protection & API Security

Relying on Cloudflare Pages proxy limits does **not** protect against direct network requests targeting Render's public hostname (`https://<app>.onrender.com`). A defensible security boundary must be established at the application layer.

### 5.1 Fail-Closed Proxy Secret Verification & Application Environment

To guarantee that incoming API requests originate strictly through the Cloudflare Pages Function edge proxy:
1. **Secret Generation:**  
   A high-entropy, 64-character random string (`PROXY_SECRET`) is generated.
2. **Cloudflare Edge Injection:**  
   The Cloudflare Pages Function reads `env.PROXY_SECRET` from its secure environment and attaches an internal header to outgoing subrequests:  
   `X-HealthAware-Proxy-Secret: <PROXY_SECRET>`
3. **Explicit Application Environment Flag (`APP_ENV`):**  
   Modern Flask deprecated `FLASK_ENV` in 2.2 and completely removed it in 2.3. HealthAware uses an explicit custom environment variable: `APP_ENV`.  
   - Only two values are supported: `development` and `production`.
   - Any missing, empty, or unsupported value (such as staging, test, or typos) causes the backend to reject requests immediately with a configuration error (`HTTP 500 CONFIG_ERROR`).
4. **Shared Secret Validation Helper (`is_valid_proxy_secret`):**  
   To prevent logic drift between request authorization and client IP resolution, a single shared helper is defined in `backend/app.py`:
   ```python
   import hmac
   import os

   def is_valid_proxy_secret(provided_secret: str) -> bool:
       """Validates candidate secrets using constant-time comparison.
       
       Supports single secrets or comma-separated pairs during rotation
       (e.g., PROXY_SECRET="<new_secret>,<old_secret>").
       """
       if not provided_secret:
           return False
       raw_secrets = os.environ.get("PROXY_SECRET", "").strip()
       if not raw_secrets:
           return False
       candidates = [s.strip() for s in raw_secrets.split(",") if s.strip()]
       return any(hmac.compare_digest(provided_secret, candidate) for candidate in candidates)
   ```
5. **Backend Middleware Enforcement (`before_request`):**
   - **Narrow Health Check Exemption:** Only the exact `GET /api/v1/health` request (`request.method == "GET" and request.path == "/api/v1/health"`) is exempt from proxy authorization so Render's internal orchestrator can probe liveness. Non-GET methods on `/api/v1/health` require the proxy secret.
   - **Environment Validation Precedence:** `APP_ENV` is strictly validated *before* proxy secret authorization is evaluated.
   - **Fail-Closed Guarantees:**  
     - Missing or unsupported `APP_ENV` values return `HTTP 500 CONFIG_ERROR`.
     - In `APP_ENV=development`: A missing proxy secret permits local bypass. If a secret is provided, it is validated via `is_valid_proxy_secret()`.
     - In `APP_ENV=production`: A configured proxy secret is **strictly required**. If `PROXY_SECRET` is unset or empty, the server halts request handling with `HTTP 500 CONFIG_ERROR`. When configured, the request's `X-HealthAware-Proxy-Secret` header must match via `is_valid_proxy_secret()`; otherwise, it returns `HTTP 403 DIRECT_ACCESS_FORBIDDEN`.
   - **Verification Logic:**
     ```python
     from flask import jsonify, request

     def verify_proxy_secret():
         # 1. Narrow health check exemption (exact GET only)
         if request.method == "GET" and request.path == "/api/v1/health":
             return None

         # 2. Validate APP_ENV: accept only explicit development or production
         app_env = os.environ.get("APP_ENV", "").strip()
         if app_env not in ("development", "production"):
             return jsonify({
                 "error": {
                     "code": "CONFIG_ERROR",
                     "message": "Server configuration error: APP_ENV must be explicitly set to 'development' or 'production'."
                 }
             }), 500

         raw_secret = os.environ.get("PROXY_SECRET", "").strip()

         # 3. Development environment: permit missing-secret bypass only when unset
         if app_env == "development" and not raw_secret:
             return None

         # 4. Production environment: require configured proxy secret
         if app_env == "production" and not raw_secret:
             return jsonify({
                 "error": {
                     "code": "CONFIG_ERROR",
                     "message": "Server configuration error: PROXY_SECRET must be configured in production."
                 }
             }), 500

         # 5. Validate provided header through shared constant-time helper
         provided_secret = request.headers.get("X-HealthAware-Proxy-Secret", "")
         if not is_valid_proxy_secret(provided_secret):
             return jsonify({
                 "error": {
                     "code": "DIRECT_ACCESS_FORBIDDEN",
                     "message": "Direct API access is not permitted. Requests must originate through the official application domain."
                 }
             }), 403
     ```
6. **Staged Proxy-Secret Rotation:**  
   Because `is_valid_proxy_secret()` inspects comma-separated values, secrets can be rotated safely through a staged overlap mechanism:
   - **Step 1:** Update Render's environment variable with both secrets: `PROXY_SECRET="<new_secret>,<old_secret>"`. Note that updating environment variables on Render triggers a service restart during which brief service disruption may occur; true zero downtime is not guaranteed on Render's Free tier. Once restarted, Render accepts either secret.
   - **Step 2:** Update Cloudflare Pages Function environment with `PROXY_SECRET="<new_secret>"`. Edge invocations immediately forward `<new_secret>`, which Render validates against the dual-secret configuration.
   - **Step 3:** Remove `<old_secret>` from Render's environment, leaving `PROXY_SECRET="<new_secret>"`. This triggers a final clean restart with only the active secret.
7. **Secret Secrecy:**  
   The secret exists only in Cloudflare Pages Function environment variables and Render environment variables. It is **never** sent to browser JavaScript, bundled in Angular code, or logged to console output.

### 5.2 Trusted Client IP Forwarding Pipeline
External clients can forge headers like `X-Forwarded-For` or `CF-Connecting-IP` when attempting direct calls to Render.

**Trusted IP Pipeline:**
1. Cloudflare's edge network terminates the client TLS connection and securely establishes the genuine client IP in `request.headers.get("CF-Connecting-IP")`.
2. In `frontend/functions/api/[[path]].ts`, the Function explicitly overwrites client IP headers:
   ```typescript
   const clientIp = request.headers.get("CF-Connecting-IP") || "";
   proxyHeaders.set("CF-Connecting-IP", clientIp);
   proxyHeaders.set("X-Forwarded-For", clientIp);
   ```

### 5.3 Server-Side Rate Limiting & Custom Key Function

#### 5.3.1 Custom Rate-Limit Key Function Requirement
> [!IMPORTANT]
> **Do Not Rely on Flask-Limiter's Default `get_remote_address`**  
> Flask-Limiter's default key function, `flask_limiter.util.get_remote_address`, simply inspects `request.remote_addr`. In a proxied architecture behind Cloudflare Pages Functions, `request.remote_addr` corresponds to Cloudflare's outbound edge proxy servers, not the individual client. Consequently, default rate limiting would incorrectly group all website visitors into a shared rate limit bucket.  
> 
> Furthermore, an application must **never** blindly read `CF-Connecting-IP` without first verifying environment validity and proxy authenticity, as an attacker calling Render directly could spoof arbitrary IPs.

**Custom Rate-Limit Key Function Implementation (`backend/app.py`):**
```python
import os
from flask import request

def get_trusted_client_ip() -> str:
    """Custom Flask-Limiter key function.
    
    Safely determines the client IP address:
    1. Validates APP_ENV: only 'development' and 'production' are accepted.
    2. Validates X-HealthAware-Proxy-Secret using the shared is_valid_proxy_secret() helper.
    3. If valid under an authorized environment, trusts the CF-Connecting-IP header securely injected by Cloudflare.
    4. If APP_ENV is invalid or missing, proxy secret is invalid or missing, or request is direct/unverified,
       NEVER trusts forwarding headers; falls back strictly to the raw socket connection address (request.remote_addr).
    """
    app_env = os.environ.get("APP_ENV", "").strip()
    if app_env in ("development", "production"):
        provided_secret = request.headers.get("X-HealthAware-Proxy-Secret", "")
        if is_valid_proxy_secret(provided_secret):
            cf_ip = request.headers.get("CF-Connecting-IP")
            if cf_ip and cf_ip.strip():
                return cf_ip.strip()
            
    # Direct, unverified, or invalid-environment request: return the raw TCP connection address
    return request.remote_addr or "127.0.0.1"
```

When an unauthenticated direct request hits Render:
- `get_trusted_client_ip()` uses `request.remote_addr` (ignoring spoofed headers).
- `verify_proxy_secret()` rejects the request with HTTP 403 Forbidden.

#### 5.3.2 Cloudflare Edge WAF vs. Default Pages Domain Reality
* **Zone-Level Constraint:** On Cloudflare, WAF Rate Limiting rules are **zone-level** configurations applied strictly to customer-controlled apex DNS zones (e.g. `example.com`). The default deployment domain `healthaware.pages.dev` is a shared Cloudflare Pages subdomain, **not** a customer-managed DNS zone. Therefore, Cloudflare WAF rate limiting rules **cannot** be bound to the default `*.pages.dev` hostname.
* **Cloudflare Free Plan Restrictions (For Custom Zones):** If a customer-controlled domain is later linked, Cloudflare’s Free plan permits only **1 rate limiting rule**, and the counting window is strictly restricted to a **10-second period** (e.g. 10 requests / 10 seconds), not an arbitrary 60-second window.
* **Design Decision for Initial Demo:** Edge WAF rate limiting is treated strictly as an **optional future enhancement** if a custom domain is attached. For this ₹0 demonstration on `pages.dev`, rate limiting is handled entirely on the backend.

#### 5.3.3 Backend Rate Limiting via Flask-Limiter
* **Concurrency Model:** Render Free Web Service provides 0.1 vCPU and 512 MB RAM. To optimize memory and prevent worker contention, Gunicorn runs with **1 worker process and 4 threads** (`--workers 1 --threads 4`).
* **In-Memory Storage (`memory://`):**
  - Thread-safe in-memory rate limiting is **100% consistent across all threads** within the single worker process.
  - **Important Limitation & Realistic Characterization:** This in-memory limiter is **best-effort**. Because Render Free spins down after 15 minutes of inactivity and restarts on new deployments, hit counters **reset upon process restart or service wake-up**.
  - It is **not** durable, persistent, or distributed abuse protection.
  - However, it effectively throttles rapid double-submissions, client retry loops, and casual automated hammering during an active session.
* **Why Distributed Storage is Avoided:**
  - We explicitly do **not** introduce paid services (e.g. Upstash Redis, Redis Cloud) or a new database to achieve distributed rate limiting for this portfolio demonstration.
  - We explicitly avoid using Neon PostgreSQL for rate-limit counter storage, because writing hit counters on every API request would generate continuous DML queries, preventing Neon serverless compute from sleeping after 5 minutes and rapidly exhausting the 100 CU-hour free tier.
* **Application Limits Enforced in Flask:**
  - Public concern submissions (`POST /api/v1/concerns`): **5 submissions per IP per 10 minutes** (best-effort within active worker lifespan).
  - Citizen tracking queries (`GET /api/v1/concerns/<report_id>/track`): **10 queries per IP per 15 minutes** (with exponential backoff on invalid tracking tokens).
  - Staff login (`POST /api/v1/auth/login`): **5 attempts per IP per 15 minutes**.

### 5.4 Architecture Boundary: CORS vs. Authentication
> [!WARNING]
> **CORS is NOT a Security or Authentication Boundary**  
> Cross-Origin Resource Sharing (CORS) is purely a browser-enforced mechanism instructing conforming web browsers whether to expose response data to JavaScript origins. Curl, Postman, custom Python scripts, and automated bots completely ignore CORS headers.  
> 
> True security boundaries in HealthAware are enforced strictly on the server:
> - **Proxy Origin Verification:** Enforced via `X-HealthAware-Proxy-Secret` with constant-time comparison.
> - **User & Staff Authentication:** Enforced via encrypted, `HttpOnly`, `SameSite=Lax` session cookies.
> - **Mutation Protection:** Enforced via `X-CSRF-Token` validation on all state-changing methods (`POST`, `PUT`, `DELETE`).
> - **Case Access & Attachments:** Enforced via jurisdictional hierarchy and private tracking tokens.

### 5.5 Explicit Flask Session-Signing Key Configuration (`SECRET_KEY`)
Flask's session subsystem and CSRF token generation rely strictly on `app.config["SECRET_KEY"]`. Flask does **not** automatically read custom environment variables like `FLASK_SECRET_KEY` into `SECRET_KEY` unless explicitly mapped in code or loaded via an explicit prefix loader (`app.config.from_prefixed_env()`).

**Requirements & Guarantees:**
1. **Explicit Code Mapping:** `backend/app.py` in `create_app()` will explicitly inspect `FLASK_SECRET_KEY` (or `SECRET_KEY`) and assign it to `app.config["SECRET_KEY"]` before session middlewares or blueprints are initialized.
2. **Fail Closed in Production:** In production (`APP_ENV=production`), the secret key must be non-empty and possess sufficient entropy (minimum 32 characters, recommended 64 hex characters). If missing, empty, or short, the application must immediately raise a `RuntimeError` during startup and refuse to serve traffic.
3. **No Development Default in Production:** Development fallback keys (e.g. `dev-insecure-secret-key`) are strictly forbidden in production and permitted solely when `APP_ENV=development` is explicitly configured.

**Planned Implementation (`backend/app.py`):**
```python
# Session signing key initialization inside create_app()
app_env = os.environ.get("APP_ENV", "").strip()
flask_secret = os.environ.get("FLASK_SECRET_KEY", "").strip() or os.environ.get("SECRET_KEY", "").strip()

if app_env == "production":
    if not flask_secret or len(flask_secret) < 32:
        raise RuntimeError(
            "Configuration error: FLASK_SECRET_KEY must be configured with a minimum of 32 characters in production. "
            "Development defaults are prohibited."
        )
    app.config["SECRET_KEY"] = flask_secret
elif app_env == "development":
    app.config["SECRET_KEY"] = flask_secret or "dev-insecure-secret-key-change-in-production"
else:
    raise RuntimeError(f"Configuration error: Unsupported APP_ENV '{app_env}'. Must be 'development' or 'production'.")
```

---

## 6. Portfolio Demonstration & Service Limitations Policy

This initial deployment is strictly a **portfolio and educational demonstration project**. It is not an operational municipal emergency or municipal health complaint dispatch system.

### 6.1 Demo Banner and User Disclaimer
The deployed frontend must prominently inform visitors of the system’s demonstration nature:
1. **Persistent Demonstration Banner:**  
   A visible header across all application pages stating:  
   `"HealthAware Demonstration Project — Educational & Portfolio Prototype. Do not submit real emergency complaints or sensitive personal information."`
2. **Citizen Reporting Form Notice (`/report`):**  
   An explicit notice above the submission button stating:  
   `"Notice: This is a demonstration application for technical evaluation. Submissions are NOT transmitted to municipal health departments, law enforcement, or emergency healthcare providers."`

### 6.2 Demonstration Data Retention & Hygiene Policy
To prevent accumulation of test data and preserve the ₹0 boundary:
* **Target Retention Window:**  
  Demonstration complaints and uploaded attachments are intended to be ephemeral, with an operational target threshold of 14 days.
* **Current Status — Not Yet Implemented as an Enforceable Guarantee:**  
  Automatic deletion or a guaranteed 14-day maximum is **not currently an enforceable SLA**. While a script named `backend/cleanup_test_data.py` exists in the repository, inspection confirms it is a legacy utility targeting the local Datastore emulator for topics and lessons; a dedicated complaint-purging script for PostgreSQL has **not yet been implemented or verified**.
* **Demonstration Phase Procedure:**  
  During the demonstration phase, retention remains **best-effort manual operator cleanup**. Operators will manually inspect and prune demo records in PostgreSQL and S3 to prevent storage exhaustion.
* **Enforceable Guarantee Requirement:**  
  An automated scheduled pruning policy will only be documented as an enforceable retention guarantee once a verified PostgreSQL/S3 cleanup command and a scheduled background runner are implemented and tested.
* **Personal Data Protection:**  
  Identifiable personal health information (PII) or real citizen photographs must not be accepted or stored in public demonstration environments.

---

## 7. Safe Free-Tier Database Migration & Bootstrapping Strategy

### 7.1 The Danger of In-Build Migrations on Render Free
On Render's Free Web Service tier, the documented `preDeployCommand` is **unavailable** (restricted to paid plans). 

Running Alembic migrations in Render's `buildCommand` (e.g. `pip install ... && alembic upgrade head`) is **dangerous and unsuitable** for the following reasons:
1. **Premature Database Mutation:** If the migration succeeds during the build step, but the subsequent application build, dependency installation, or Gunicorn startup fails, the remote database has already been altered while the *old* application version continues running. Backwards-incompatible schema changes will crash the live service.
2. **Repeated Unreviewed Execution:** Any routine rebuild, environment variable change, or redeploy will re-run migration utilities against the live database without explicit developer review.
3. **Locking & Concurrency:** Automated rebuild attempts can trigger concurrent DDL lock contention.

### 7.2 Recommended Safe Free-Tier Migration Procedure
All database schema migrations must be applied **out-of-band** by an authorized operator prior to releasing a compatible application version:

```
[Developer Terminal]                    [Neon PostgreSQL]                 [Render Web Service]
        |                                       |                                  |
        | 1. neonctl branches create snapshot   |                                  |
        |-------------------------------------->|                                  |
        |    (Instant 0-cost rollback point)    |                                  |
        |                                       |                                  |
        | 2. Set APP_ENV=production &           |                                  |
        |    MIGRATION_DATABASE_URL             |                                  |
        |    alembic upgrade head               |                                  |
        |    (Direct unpooled port 5432)        |                                  |
        |-------------------------------------->|                                  |
        |    (Verify schema version)            |                                  |
        |                                       |                                  |
        | 3. Tag & Push Tested Code             |                                  |
        |------------------------------------------------------------------------->|
        |                                                                          | 4. Build & Deploy
        |                                                                          |    (pip install only)
        |                                       |<---------------------------------| 5. Runtime Queries
        |                                       |                                  |    (DATABASE_URL pooled)
```

**Step-by-Step Procedure:**
1. **Create Instant Rollback Branch:**  
   Prior to applying any DDL migration, create a Neon branch snapshot:
   ```bash
   neonctl branches create --name pre-migration-$(Get-Date -Format "yyyyMMddHHmmss")
   ```
2. **Fail-Closed Migration Connection Variable (`MIGRATION_DATABASE_URL`) & Environment Validation:**  
   Alembic configuration (`backend/migrations/env.py`) is configured to fail closed:
   - **Strict `APP_ENV` Validation:** Alembic explicitly inspects and validates `APP_ENV`, accepting only `development` or `production`. If `APP_ENV` is missing, empty, or unsupported (e.g. staging, test, or typos), Alembic stops immediately with a clear configuration error. It never routes an invalid environment value through the development fallback.
   - **Production Requirement:** When `APP_ENV=production`, `MIGRATION_DATABASE_URL` (direct unpooled connection on port 5432) is **strictly required**. If `MIGRATION_DATABASE_URL` is missing or empty, Alembic stops immediately with a configuration error. It does **not** fall back to the pooled runtime `DATABASE_URL`.
   - **Development Fallback:** When `APP_ENV=development`, Alembic prioritizes `MIGRATION_DATABASE_URL` but permits the documented local fallback to `DATABASE_URL` for local workflow convenience.
   - **`backend/migrations/env.py` Connection Resolution:**
     ```python
     import os

     app_env = os.environ.get("APP_ENV", "").strip()

     if app_env == "production":
         migration_url = os.environ.get("MIGRATION_DATABASE_URL", "").strip()
         if not migration_url:
             raise ValueError(
                 "Configuration error: MIGRATION_DATABASE_URL is required for production schema migrations. "
                 "Alembic must use a direct, unpooled connection (port 5432) and will not fall back to DATABASE_URL in production."
             )
         target_url = migration_url
     elif app_env == "development":
         # Local development: prioritize MIGRATION_DATABASE_URL, permit documented fallback to DATABASE_URL
         target_url = os.environ.get("MIGRATION_DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()
         if not target_url:
             raise ValueError("Configuration error: Neither MIGRATION_DATABASE_URL nor DATABASE_URL is configured for development.")
     else:
         raise ValueError(
             f"Configuration error: Unsupported or missing APP_ENV '{app_env}'. "
             "Alembic environment must be explicitly configured as 'development' or 'production'."
         )
     ```
3. **Execute Alembic Out-of-Band:**  
   From an authorized operator terminal, execute the migration with `APP_ENV=production` and `MIGRATION_DATABASE_URL`:
   ```powershell
   $env:APP_ENV="production"
   $env:MIGRATION_DATABASE_URL="postgresql://[user]:[password]@[endpoint].neon.tech/healthaware?sslmode=require"
   python -m alembic -c backend/alembic.ini upgrade head
   ```
4. **Verify Revision:**  
   Verify the migration revision in Neon:
   ```powershell
   python -m alembic -c backend/alembic.ini current
   ```
5. **Deploy Application Code:**  
   Only after the database schema migration is verified should the application build be triggered on Render. Render’s `buildCommand` will strictly install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

### 7.3 Separating Curriculum Initialization from Admin Provisioning
`backend/bootstrap_postgres.py` currently seeds both the canonical curriculum (sources, topics, lessons, cards) and three local demo accounts with known passwords (`admin123`, `contrib123`, `review123`).

**Production Rules:**
1. **Curriculum Bootstrapping (`--curriculum-only`):**  
   A dedicated flag (`--curriculum-only`) will be added to `backend/bootstrap_postgres.py`. In production, this will populate the 13 health sources, 4 published topics, 7 lessons, and cards without creating any users.
2. **No Fixed Demo Passwords in Production:**  
   Public deployments must **never** be provisioned with default passwords or known credentials.
3. **First Production Administrator Provisioning:**  
   The initial administrator will be created via a dedicated script (`backend/provision_admin.py` updated for PostgreSQL) executed out-of-band by the operator:
   ```bash
   python backend/provision_admin.py --username sysadmin --name "System Administrator"
   ```
   The password must be entered interactively via secure prompt (minimum 16 characters with mixed entropy) or supplied via a one-time environment variable `INITIAL_ADMIN_PASSWORD` that is cleared immediately after account creation.

---

## 8. Repository Data Exposure Safeguards & Pre-Flight Check

### 8.1 Audit of Existing Git Configuration and Ignored Files
Inspection of `c:\Users\nalli\project-internship\health-awareness\.gitignore` confirms that key local artifacts are ignored:
- `local_db/` (ignores `local_db/postgres_backups/` and `local_db/datastore_export/`)
- `local_storage/` (ignores `local_storage/attachments/` uploaded evidence photos)
- `.env` and `*.env` (ignores environment credential files)
- `.venv/`, `node_modules/`, `dist/`, `.angular/`

### 8.2 Identified Gaps to Address Before Git Connection
Before initializing Git or connecting to a remote repository (such as GitHub), `.gitignore` must be enhanced with explicit backup and secret patterns:
```gitignore
# Database SQL Backups & Dumps
*.sql
*.dump
*.tar
*.bak

# Environment & Private Keys
.env
*.env
*.env.*
backend/.env
frontend/.env
*.pem
*.key

# Runtime Storage
local_storage/attachments/*
attachments/*
```

### 8.3 Pre-Flight Repository Verification Checklist
Before running any `git push` or connecting to a public repository:
- [ ] 1. **Check Git Status:** Verify `.git` is clean and no untracked private files appear.
- [ ] 2. **Check Ignored Files:** Run `git status --ignored` to confirm that `.env`, `local_db/`, and `local_storage/` are actively recognized as ignored.
- [ ] 3. **Avoid Blind Staging:** Never use `git add .` or `git add -A`. Add specific directories:
  ```bash
  git add frontend/ backend/ docs/ scripts/ .gitignore README.md
  ```
- [ ] 4. **Inspect Staged Files:** Run `git diff --cached --name-only` to review every file queued for commit.
- [ ] 5. **Secret Scan:** Run a regex scan across staged files to ensure no API keys, connection strings, or password hashes are present:
  ```bash
  git diff --cached | Select-String -Pattern "(password_hash|DATABASE_URL|SECRET_KEY|aws_secret|bearer)"
  ```
- [ ] 6. **Preserve Local Data:** Do not delete existing local PostgreSQL SQL dumps or Datastore emulator backups during repository preparation.

---

## 9. Cloudflare Pages Same-Origin Proxy Specification

A Cloudflare Pages Function at `frontend/functions/api/[[path]].ts` will intercept all `/api/*` traffic, sanitize client IP headers, attach the internal proxy secret, and forward requests to the fixed Render origin.

### 9.1 Proposed Implementation (`frontend/functions/api/[[path]].ts`)

```typescript
interface Env {
  RENDER_BACKEND_URL: string;
  PROXY_SECRET: string;
}

export const onRequest: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  // 1. Verify Configuration
  if (!env.RENDER_BACKEND_URL || !env.PROXY_SECRET) {
    return new Response(
      JSON.stringify({
        error: {
          code: "CONFIG_ERROR",
          message: "Upstream backend or proxy credentials are not configured.",
        },
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  const backendOrigin = new URL(env.RENDER_BACKEND_URL);
  const clientUrl = new URL(request.url);

  // 2. Build Target URL strictly against fixed backend origin (blocks open proxy attacks)
  const targetUrl = new URL(clientUrl.pathname + clientUrl.search, backendOrigin);

  // 3. Clone and Sanitize Headers
  const proxyHeaders = new Headers(request.headers);
  proxyHeaders.set("Host", backendOrigin.host);
  proxyHeaders.set("X-Forwarded-Host", clientUrl.host);
  proxyHeaders.set("X-Forwarded-Proto", "https");

  // 4. Overwrite Spoofable Client IP Headers with Trusted Cloudflare IP
  const trustedClientIp = request.headers.get("CF-Connecting-IP") || "";
  proxyHeaders.set("CF-Connecting-IP", trustedClientIp);
  proxyHeaders.set("X-Forwarded-For", trustedClientIp);

  // 5. Inject Server-Side Shared Proxy Secret (never exposed to client browser)
  proxyHeaders.set("X-HealthAware-Proxy-Secret", env.PROXY_SECRET);

  const method = request.method.toUpperCase();
  const isBodyAllowed = !["GET", "HEAD"].includes(method);

  try {
    // 6. Forward Subrequest to Render
    const upstreamResponse = await fetch(targetUrl.toString(), {
      method,
      headers: proxyHeaders,
      body: isBodyAllowed ? request.body : null,
      redirect: "manual",
    });

    // 7. Reconstruct Response Preserving Set-Cookie & Status
    const responseHeaders = new Headers(upstreamResponse.headers);

    // Host-only cookie preservation
    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    // 8. Structured Cold-Start / Timeout Error Handling
    return new Response(
      JSON.stringify({
        error: {
          code: "BACKEND_UNAVAILABLE",
          message: "The backend service is starting up or temporarily unreachable. Please retry in a moment.",
        },
      }),
      {
        status: 503,
        headers: {
          "Content-Type": "application/json",
          "Retry-After": "10",
        },
      }
    );
  }
};
```

---

## 10. Required File Modifications (Future Implementation Phase)

The table below lists the minimal set of files that will require modification or creation during the future deployment implementation. **No application code changes have been made during this planning phase.**

| Target File | Change Type | Purpose & Scope |
| :--- | :---: | :--- |
| `frontend/public/_redirects` | **New** | Adds `/*  /index.html  200` to support Angular HTML5 pushState client-side routing on Cloudflare Pages. |
| `frontend/public/_routes.json` | **New** | Restricts Cloudflare Pages Function execution strictly to `/api/*`, protecting the 100k requests/day free quota. |
| `frontend/functions/api/[[path]].ts` | **New** | Cloudflare Pages Function proxying `/api/*` to the fixed Render backend origin with host-only cookie forwarding, IP sanitization, and `X-HealthAware-Proxy-Secret` injection. |
| `backend/requirements.txt` | **Edit** | Adds `gunicorn==23.0.0` (production WSGI server), `boto3==1.36.21` (S3 object storage client), and `Flask-Limiter==3.8.0` (rate limiting). |
| `backend/app.py` | **Edit** | Decouples Google Cloud NDB request lifecycle when running with PostgreSQL; validates `APP_ENV` upfront (`development` or `production` only); explicitly maps `FLASK_SECRET_KEY` to `app.config['SECRET_KEY']` requiring a nonempty secret in production with no dev default; adds `is_valid_proxy_secret()` constant-time helper; adds fail-closed `verify_proxy_secret` hook (exempting exact `GET /api/v1/health`); configures rate limiting with `get_trusted_client_ip()` custom key function enforcing the same strict environment policy. |
| `backend/migrations/env.py` | **Edit** | Configures Alembic environment to fail closed by strictly validating `APP_ENV` (`development` or `production` only), stopping with a configuration error on missing or unsupported values; requires `MIGRATION_DATABASE_URL` (direct unpooled endpoint on port 5432) for production migrations with zero fallback to `DATABASE_URL`; permits fallback to `DATABASE_URL` solely in local development. |
| `backend/platform/attachment_storage.py` | **Edit** | Adds S3/Boto3 read/write methods for Neon Object Storage with seamless fallback to local disk storage for local test execution. |
| `backend/bootstrap_postgres.py` | **Edit** | Adds `--curriculum-only` flag to populate health sources, topics, and lessons without seeding baseline test users. |
| `backend/provision_admin.py` | **Edit** | Adapts admin provisioning CLI tool to write directly to PostgreSQL via SQLAlchemy. |
| `.gitignore` | **Edit** | Adds explicit exclusions for `*.sql`, `*.dump`, `backend/.env`, and attachments. |

---

## 11. Build, Startup, and Migration Commands (Verified)

### Frontend (Cloudflare Pages)
* **Framework Preset:** None / Angular
* **Build Command:** `npm run build`
* **Build Output Directory:** `dist/health-awareness-frontend/browser`
* **Root Directory:** `frontend`
* **Environment Variables:**
  - `NODE_VERSION`: `24.15.0`

### Backend (Render Free Web Service)
* **Runtime:** Python 3
* **Root Directory:** `.` (Repository root)
* **Build Command:**
  ```bash
  pip install -r backend/requirements.txt
  ```
* **Start Command:**
  ```bash
  gunicorn "backend.app:create_app()" --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
  ```
* **Health Check Path:** `/api/v1/health`

### Out-of-Band Migration & Provisioning (Operator Workstation)
* **Pre-Migration Snapshot:**
  ```bash
  neonctl branches create --name pre-deploy-snapshot
  ```
* **Verify Migration Connection Variable & Run Alembic (Fail-Closed):**
  ```powershell
  $env:APP_ENV="production"
  $env:MIGRATION_DATABASE_URL="postgresql://[user]:[password]@[endpoint].neon.tech/healthaware?sslmode=require"
  python -m alembic -c backend/alembic.ini upgrade head
  ```
* **Seed Canonical Curriculum:**
  ```powershell
  $env:APP_ENV="production"
  $env:DATABASE_URL="postgresql://[user]:[password]@[endpoint].neon.tech/healthaware?sslmode=require"
  python backend/bootstrap_postgres.py --curriculum-only
  ```
* **Provision First Administrator:**
  ```powershell
  python backend/provision_admin.py --username sysadmin --name "System Administrator"
  ```

---

## 12. Deployment Environment Variables Inventory

All sensitive credentials and connection strings must be configured exclusively in provider secret managers. **No real credentials belong in code or Git.**

### Cloudflare Pages Dashboard
* `RENDER_BACKEND_URL`: URL of the deployed Render service (e.g. `https://healthaware-api.onrender.com`).
* `PROXY_SECRET`: Cryptographically secure 64-character random string for edge-to-backend authentication.
* `NODE_VERSION`: `24.15.0`

### Render Dashboard (Backend Web Service)
* `APP_ENV`: `production` (explicit custom environment flag; must be `development` or `production`. Replaces `FLASK_ENV`, which was deprecated in Flask 2.2 and removed in Flask 2.3).
* `FLASK_SECRET_KEY`: Cryptographically secure 64-character random string for session signature. Explicitly mapped to `app.config['SECRET_KEY']` in `backend/app.py`. Required and non-empty in production (minimum 32 characters; no development defaults permitted).
* `PROXY_SECRET`: Identical 64-character random string matching Cloudflare Pages Function. Required in production.
* `DATABASE_URL`: Neon pooled PostgreSQL connection string with `?sslmode=require` (for runtime queries).
* `MIGRATION_DATABASE_URL`: Neon direct (unpooled) PostgreSQL connection string for Alembic DDL. Required for out-of-band production schema migrations.
* `ALLOWED_ORIGINS`: `https://healthaware.pages.dev` (and custom domain if configured).
* `SESSION_COOKIE_SECURE`: `true`
* `ATTACHMENT_STORAGE_BACKEND`: `s3`
* `S3_ENDPOINT_URL`: Neon S3-compatible storage endpoint URL.
* `S3_BUCKET_NAME`: Private bucket name.
* `AWS_ACCESS_KEY_ID`: S3 access key.
* `AWS_SECRET_ACCESS_KEY`: S3 secret key.
* `AWS_REGION`: `us-east-2` (matching Neon region).
* `PYTHON_VERSION`: `3.12.9`
* `SMTP_HOST`: Canonical hostname of transactional SMTP relay (e.g. `smtp.sendgrid.net`, `smtp.resend.com`). Alias fallback: `SMTP_SERVER`.
* `SMTP_PORT`: Canonical port number (`587` for STARTTLS, `465` for SSL, `25` for unauthenticated relay; default: `587`).
* `SMTP_USERNAME`: Canonical SMTP username / API key user (e.g. `apikey`, `resend`). Alias fallback: `SMTP_USER`.
* `SMTP_PASSWORD`: Canonical SMTP password / API secret key. Alias fallback: `SMTP_PASS`.
* `SMTP_FROM_EMAIL`: Canonical outbound sender email (e.g. `no-reply@healthaware.org`). Alias fallbacks: `SMTP_FROM`, `EMAIL_FROM`. Defaults to `noreply@healthaware.org`.

---

## 13. Rollback & Disaster Recovery Strategy

1. **Database Rollback:**
   - **Neon Instant Branch Restore:** Neon allows creating a branch snapshot prior to running any migration. If a migration or deployment introduces data corruption, restoring the previous branch takes under 2 seconds.
   - **Alembic Downward Migration:** `alembic -c backend/alembic.ini downgrade -1` can roll back schema revisions.
   - **Datastore Emulator Protection:** The original Datastore export snapshot (`local_db/datastore_export/datastore_export_1792319180`) remains completely preserved locally. The Datastore codebase in `backend/storage/storage_models.py` is intact and can be re-activated if ever required.
2. **Frontend Rollback:**
   - Cloudflare Pages preserves all historical deployment builds. Rolling back to a previous build takes one click in the Cloudflare dashboard and updates instantly worldwide.
3. **Backend Rollback:**
   - Render Free Web Service documentation states that rollback is supported to the **two most recent previous deployments**. A rollback can be triggered immediately from the Render dashboard without rebuilding from source.

---

## 14. Manual Deployment Checklist & Smoke-Test Plan

When approved to implement deployment in a future phase, execute the following verified sequence:

### Phase A: Database Setup (Neon)
- [ ] 1. Create a free Neon project in `us-east-2` (or nearest region).
- [ ] 2. Copy the pooled connection string to `DATABASE_URL` and direct connection to `MIGRATION_DATABASE_URL`.
- [ ] 3. Enable Neon Object Storage / create a private bucket; record S3 credentials.
- [ ] 4. Set `$env:APP_ENV="production"` and `$env:MIGRATION_DATABASE_URL="postgresql://..."`. Confirm Alembic stops with an error if `APP_ENV` is missing/invalid or if `MIGRATION_DATABASE_URL` is omitted, and run out-of-band Alembic migration from operator terminal: `alembic -c backend/alembic.ini upgrade head`.
- [ ] 5. Seed canonical curriculum: `python backend/bootstrap_postgres.py --curriculum-only`.
- [ ] 6. Provision initial administrator: `python backend/provision_admin.py --username sysadmin`.

### Phase B: Backend Web Service (Render)
- [ ] 1. Connect GitHub repository to Render as a Web Service.
- [ ] 2. Configure environment variables (`APP_ENV=production`, `FLASK_SECRET_KEY` [>=32 chars], `DATABASE_URL`, `MIGRATION_DATABASE_URL`, S3 keys, Proxy Secret). Do NOT attach a credit card.
- [ ] 3. Set Build Command (`pip install -r backend/requirements.txt`) and Start Command (`gunicorn ...`).
- [ ] 4. Confirm `GET /api/v1/health` responds with HTTP 200 without requiring `PROXY_SECRET`.
- [ ] 5. Confirm non-GET methods on `/api/v1/health` or calls to `/api/v1/topics` on Render hostname return HTTP 403 Forbidden.
- [ ] 6. Confirm that starting the application with a missing or invalid `APP_ENV` (or missing `FLASK_SECRET_KEY` in production) fails immediately during initialization.

### Phase C: Frontend & Proxy (Cloudflare Pages)
- [ ] 1. Connect GitHub repository to Cloudflare Pages.
- [ ] 2. Configure root directory `frontend` and output directory `dist/health-awareness-frontend/browser`.
- [ ] 3. Set `RENDER_BACKEND_URL`, `PROXY_SECRET`, and `NODE_VERSION=24.15.0` environment variables.
- [ ] 4. Trigger build and verify edge deployment. Confirm `_routes.json` limits function executions to `/api/*`.

### Phase D: Post-Deployment Smoke Test
- [ ] 1. Navigate to deployed Pages URL (`https://healthaware.pages.dev/`).
- [ ] 2. Verify homepage, 4 topics, 7 lessons, and 4 mosquito chapters in order.
- [ ] 3. Verify persistent demonstration banner is visible.
- [ ] 4. Complete Chapter 1 quiz card; verify explanation feedback.
- [ ] 5. Submit a test complaint on `/report`; verify Reference ID and token are issued.
- [ ] 6. Query status on `/track`; confirm timeline displays 'Received'.
- [ ] 7. Log in to `/staff` as sysadmin; update report status to 'under_review' with public note.
- [ ] 8. Re-query on `/track`; confirm public note is visible and internal note is hidden.
- [ ] 9. Delete test complaint to leave database clean.

---

## 15. Official Documentation References

* **Angular Version Compatibility Guide:** `https://angular.dev/reference/versions`
* **Cloudflare Pages Framework Guides (Angular):** `https://developers.cloudflare.com/pages/framework-guides/deploy-an-angular-site/`
* **Cloudflare Pages Functions Routing & `_routes.json`:** `https://developers.cloudflare.com/pages/functions/routing/#create-a-_routesjson-file`
* **Cloudflare Pages Platform Limits:** `https://developers.cloudflare.com/pages/platform/limits/`
* **Cloudflare Workers Execution Limits:** `https://developers.cloudflare.com/workers/platform/limits/`
* **Cloudflare WAF Rate Limiting Rules & Plans:** `https://developers.cloudflare.com/waf/rate-limiting-rules/`
* **Flask Environment & Configuration (Deprecation & Removal of FLASK_ENV):** `https://flask.palletsprojects.com/en/stable/config/#environment-and-debug-features`
* **Flask Session Secret Configuration:** `https://flask.palletsprojects.com/en/stable/config/#SECRET_KEY`
* **Flask-Limiter Key Functions:** `https://flask-limiter.readthedocs.io/en/stable/configuration.html#ratelimit-key`
* **Render Free Services & Quotas:** `https://render.com/docs/free#free-web-services`
* **Render Bandwidth & Overage Specifications:** `https://render.com/docs/free#bandwidth` and `https://render.com/docs/pricing#bandwidth`
* **Render Deploys & Rollbacks:** `https://render.com/docs/deploys#rollbacks`
* **Neon Serverless Pricing & Plans:** `https://neon.com/pricing`
* **Neon Object Storage Architecture:** `https://neon.com/blog/building-a-private-searchable-photo-library-on-the-neon-backend`
* **Node.js Release Lifecycle:** `https://nodejs.org/en/about/previous-releases`
* **Boto3 S3 Client Documentation:** `https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html`

---

*Assessment v2.4.0 finalized. The HealthAware deployment readiness plan incorporates fail-closed Alembic environment validation (explicitly accepting only development or production, with zero fallback on invalid values), fail-closed production migrations requiring direct MIGRATION_DATABASE_URL, staged proxy-secret rotation acknowledging Render restart behavior on the Free plan, upfront Flask APP_ENV validation, explicit Flask SECRET_KEY mapping without production defaults, unified constant-time proxy secret validation, Render Free 2-deploy rollback limits, and verified retention boundaries.*
