# ADR 0003: Email OTP Verification Challenge Architecture

## Context & Problem Statement
HealthAware requires a secure, role-differentiated authentication workflow.
Previously, learner registration accepted an email and password directly without pre-verification, and password recovery sent an uncoordinated recovery link.
To prevent unauthorized account creation, spam registrations, and account takeover, new registrations and password recovery must issue an email verification challenge (OTP) that the user must verify *before* creating or resetting a password.

## Security & Architectural Requirements
1. Role Isolation: Choosing a role in the UI must never grant privileged permissions. Public registration is limited to `learner` or `contributor_applicant`. Privileged roles (`reviewer`, `staff`, `admin`) require server-authorized provisioning or application approval.
2. Cryptographic Security: Generate 6-digit numeric OTPs using Python's `secrets` module (CSPRNG).
3. Hashed Storage: Store SHA-256 hashes of OTP tokens rather than plaintext codes in the database.
4. Expiration & Rate Limiting: OTPs expire in 10 minutes. Limit verification attempts to 5 per challenge. Limit challenge creation rate per IP/email.
5. Invalidation: Previous active challenges for the same email and purpose must be invalidated upon generating a new challenge.
6. Email Provider Gate: Inspect existing email delivery options (Gmail API OAuth2 over HTTPS port 443, SMTP relay) without introducing paid third-party services. If no provider credentials are configured, complete data models, interfaces, UI, and test suites safely, and await administrative decision before deploying production delivery.

## Decision Outcome
Introduce `EmailOtpChallengeModel` and `OtpService` (`backend/platform/otp_service.py`):
- `POST /api/v1/auth/signup/challenge`: Issues an OTP challenge for eligible public roles.
- `POST /api/v1/auth/signup/verify`: Verifies the OTP hash, validates password strength, and creates the account.
- `POST /api/v1/auth/recovery/challenge`: Initiates password reset challenge without leaking account existence.
- `POST /api/v1/auth/recovery/reset`: Verifies the reset OTP hash and updates the account password.
