# API Contract Specification

This document defines the RESTful API contract for the **Digital Health Awareness Web Application** (v1).

The API follows an Oppia-inspired layered architecture:
- All responses are served with `Content-Type: application/json`.
- Standardized success envelopes encapsulate resources under a `data` field alongside API metadata (`meta`).
- Standardized error envelopes provide consistent error codes and sanitized public messages.
- Read-only endpoints in Phase 5: no mutation or publication endpoints are exposed.
- Strict publication enforcement: draft, archived, or unreviewed content is never exposed to the public.

---

## 1. Response Formats & Envelopes

### 1.1 Success Envelope
Every successful response returns an envelope containing:
- `data`: The requested resource or array of resources.
- `meta`: Metadata about the response, including `api_version`.

```json
{
  "data": { ... },
  "meta": {
    "api_version": "v1"
  }
}
```

### 1.2 Error Envelope
Every failure response returns an HTTP status code accompanied by a structured JSON payload:
- `error.code`: A machine-readable uppercase snake_case string identifier.
- `error.message`: A human-readable, sanitized explanation of the issue.

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found."
  }
}
```

### 1.3 Standard HTTP Status Codes
| HTTP Status | Error Code | Description |
|---|---|---|
| `200 OK` | — | Request succeeded. |
| `400 Bad Request` | `BAD_REQUEST` | Invalid request parameters or URI syntax. |
| `404 Not Found` | `NOT_FOUND` | Requested topic, lesson, or resource does not exist or is not published. |
| `405 Method Not Allowed`| `METHOD_NOT_ALLOWED` | HTTP method not permitted on this endpoint (e.g. POST, PUT, DELETE). |
| `500 Internal Error` | `INTERNAL_SERVER_ERROR`| Unexpected server fault (stack traces and internal details masked). |
| `503 Service Unavailable`| `SERVICE_UNAVAILABLE`| Storage emulator unreachable or offline. |

---

## 2. API Endpoints

### 2.1 Endpoint A: List Published Topics
Retrieves health awareness topics currently published and available to the general public, ordered by display order.

- **Method / Route:** `GET /api/v1/topics`
- **Authentication:** None (Public)
- **Publication Rule:** Only topics with `status: "published"` are returned. Draft and archived topics are omitted.

#### Success Response (`200 OK`)
```json
{
  "data": [
    {
      "id": "personal-hygiene",
      "title": "Personal and Food Hygiene",
      "slug": "personal-hygiene",
      "description": "Essential practices for daily handwashing, food safety, and sanitation.",
      "display_order": 0,
      "cover_image_ref": "assets/images/topics/hygiene.png",
      "cover_image_alt": "Hands being washed under clean running water"
    },
    {
      "id": "safe-drinking-water",
      "title": "Safe Drinking Water",
      "slug": "safe-drinking-water",
      "description": "Effective household water treatment, chlorination, and safe storage methods.",
      "display_order": 1,
      "cover_image_ref": "assets/images/topics/water.png",
      "cover_image_alt": "Clear drinking water poured into a clean glass"
    }
  ],
  "meta": {
    "api_version": "v1"
  }
}
```

---

### 2.2 Endpoint B: List Published Lessons Within a Topic
Retrieves the publicly accessible lessons belonging to a specific published topic, ordered by display order.

- **Method / Route:** `GET /api/v1/topics/<topic_id>/lessons`
- **Authentication:** None (Public)
- **Publication Rule:**
  - If the topic does not exist or has `status: "draft"` or `status: "archived"`, returns `404 NOT_FOUND`.
  - Only lessons with an active, approved `published_version_id` are included.
  - Draft-only or archived lessons within the topic are omitted.

#### Success Response (`200 OK`)
```json
{
  "data": [
    {
      "id": "hand-washing-technique",
      "topic_id": "personal-hygiene",
      "title": "Effective Handwashing Technique",
      "summary": "Master the 20-second handwashing sequence with soap and running water.",
      "language": "en",
      "estimated_duration_minutes": 5,
      "published_version_id": "hand-washing-technique-v1",
      "display_order": 0
    }
  ],
  "meta": {
    "api_version": "v1"
  }
}
```

#### Error Response — Topic Not Found or Unpublished (`404 Not Found`)
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Topic 'unknown-topic' was not found or is not published."
  }
}
```

---

### 2.3 Endpoint C: Retrieve Published Lesson Detail
Retrieves the complete content structure of a published lesson, including ordered educational cards, interactive quiz items, options, explanatory feedback, and authoritative medical citations.

- **Method / Route:** `GET /api/v1/lessons/<lesson_id>`
- **Authentication:** None (Public)
- **Publication Rule:**
  - If the lesson is missing, has no published version, or its parent topic is unpublished, returns `404 NOT_FOUND`.
  - Only returns the current published version. Previous archived versions or pending drafts are never leaked.
  - Internal curator metadata (e.g., `metadata_notes`) is stripped from health sources.

#### Success Response (`200 OK`)
```json
{
  "data": {
    "id": "hand-washing-technique",
    "topic_id": "personal-hygiene",
    "version_id": "hand-washing-technique-v1",
    "version_number": 1,
    "title": "Effective Handwashing Technique",
    "summary": "Master the 20-second handwashing sequence with soap and running water.",
    "language": "en",
    "learning_objectives": [
      "Explain the five critical moments for hand hygiene",
      "Demonstrate correct 20-second friction technique"
    ],
    "estimated_duration_minutes": 5,
    "cards": [
      {
        "id": "card-intro-01",
        "position": 0,
        "card_type": "explanation",
        "content_blocks": [
          {
            "block_type": "text",
            "body": "Hand hygiene is the single most effective action to stop the spread of infection."
          }
        ],
        "source_ids": ["who-hand-hygiene-2024"],
        "interaction": null
      },
      {
        "id": "card-quiz-01",
        "position": 1,
        "card_type": "interaction",
        "content_blocks": [
          {
            "block_type": "text",
            "body": "Test your knowledge on proper technique:"
          }
        ],
        "source_ids": [],
        "interaction": {
          "interaction_type": "single_choice",
          "question_prompt": "What is the minimum duration recommended for scrubbing hands with soap?",
          "incorrect_behaviour": "retry",
          "options": [
            {
              "id": "opt-20s",
              "label": "At least 20 seconds",
              "is_correct": true,
              "feedback": "Correct! Scrubbing for at least 20 seconds physically dislodges viruses and bacteria."
            },
            {
              "id": "opt-5s",
              "label": "5 seconds",
              "is_correct": false,
              "feedback": "Too fast. 5 seconds is insufficient to break surface tension and remove germs."
            }
          ]
        }
      }
    ],
    "sources": [
      {
        "id": "who-hand-hygiene-2024",
        "title": "WHO Guidelines on Hand Hygiene in Health Care",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/campaigns/world-hand-hygiene-day",
        "publication_date": "2024-05-05",
        "access_date": "2025-06-01",
        "jurisdiction": "Global"
      }
    ]
  },
  "meta": {
    "api_version": "v1"
  }
}
```

#### Error Response — Lesson Not Found or Unpublished (`404 Not Found`)
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Lesson 'draft-lesson' was not found or is not published."
  }
}
```

---

### 2.4 Endpoint D: Application Liveness Check
Confirms that the Flask WSGI application process is running and receptive to HTTP requests.

- **Method / Route:** `GET /api/v1/health`
- **Authentication:** None (Public)
- **Database Dependency:** None. Does not contact Datastore or verify database health.
- **Security Guarantee:** Does not disclose filesystem paths, credentials, environment variables, or infrastructure details.

#### Success Response (`200 OK`)
```json
{
  "data": {
    "status": "healthy"
  },
  "meta": {
    "api_version": "v1"
  }
}
```

### 2.5 Endpoint E: Staff Application Tracking Recovery
Enables applicants to recover access to active applications via their verified email address without disclosing application existence to third parties.

- **Method / Route:** `POST /api/v1/staff/applications/recover`
- **Authentication:** None (Public)
- **Rate Limit:** 10 requests per hour per IP
- **Security Guarantees:**
  - **Account Enumeration Defense:** Returns identical `HTTP 200 OK` status and generic response message whether the email exists, does not exist, or is in an ineligible terminal state.
  - **Zero Public Credential Disclosure:** `reference_id` and raw `tracking_token` are never returned in HTTP responses. They are dispatched solely to the verified applicant inbox via transactional email.
  - **Audit Logging:** Every attempt is recorded in the structured security audit trail with client IP, timestamp, and verification outcome.

#### Request Payload
```json
{
  "email": "applicant@example.org"
}
```

#### Consistent Generic Response (`200 OK`)
```json
{
  "data": {
    "message": "If an active staff application exists for this email address, tracking recovery instructions have been sent."
  },
  "meta": {
    "api_version": "v1"
  }
}
```

---

## 3. Interaction Mechanics & Frontend Consumption

The single-choice interaction design is structured for client-side evaluation by the Angular lesson player:
1. **Interactive Evaluation:** The complete lesson structure—including option IDs, correctness flags, and feedback text—is delivered in the initial lesson payload. No server-side round-trip is required when a learner selects an option.
2. **Behavior Directives:** `incorrect_behaviour: "retry"` indicates the learner must select another answer before proceeding; `"continue"` permits progression to the next card after viewing the explanatory feedback.
3. **Card Sequencing:** The learner navigates cards strictly in ascending order by the `position` index.

---

## 4. Angular Integration via Development Proxy

During local development, the Angular CLI (`ng serve`) runs on `http://127.0.0.1:4200` while the Flask backend runs on `http://127.0.0.1:5000`.

To avoid CORS restrictions and wildcard `Access-Control-Allow-Origin: *` headers, Angular will use a development proxy configuration (`proxy.conf.json`):
```json
{
  "/api": {
    "target": "http://127.0.0.1:5000",
    "secure": false,
    "changeOrigin": true
  }
}
```
All browser requests to `/api/v1/...` are seamlessly routed by the development server without CORS issues.
