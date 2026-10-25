# ADR 0004: Frontend Backend Startup & Readiness Warmup

## Context & Problem Statement
On cold starts (such as free-tier hosting spin-up or app initialization), the backend may take several seconds to establish database connections and respond to API requests.
Previously, the frontend made requests lazily only when a user navigated to a specific page (e.g. `/topics`). When the user tapped on a link, they encountered latency or transient errors.
The frontend needs to initiate backend readiness and public-data bootstrap as early as practical, without blocking initial rendering or creating duplicate request storms.

## Decision Drivers
- Non-blocking: First-paint and local offline content must never be blocked by backend spin-up.
- Efficient: Shared Observable / Promise replay so multiple views consume the same warmup response rather than issuing duplicate HTTP calls.
- Proxy Compliance: Route all requests through the standard Cloudflare proxy path (`/api/v1`) and preserve proxy secrets.
- Security: Never fetch private or authenticated data during startup bootstrap.

## Decision Outcome
Create `BackendWarmupService` in Angular (`frontend/src/app/services/backend-warmup.service.ts`):
1. Initialized via `APP_INITIALIZER` or early root component lifecycle.
2. Fires a lightweight probe to `GET /api/v1/health/ready` with a bounded timeout (5 seconds) and safe retry.
3. Concurrently warms public curriculum metadata cache via `TopicsService.getTopics()`.
4. Exposes signals `isBackendReady`, `isWarming`, and `warmupError` for application-wide awareness.
