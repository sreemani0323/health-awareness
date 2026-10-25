# ADR 0002: Multi-Image Evidence Attachments for Concern Reporting

## Context & Problem Statement
Citizens reporting sanitation, drainage, or sewage concerns often need to attach multiple photos (e.g., wide view of street, close-up of blockage, water source proximity) to give municipal coordinators sufficient context. The initial implementation supported only a single photo under form field `photo`.
The product requirement is to allow up to five photos per report, with client-side previews, individual deletion prior to submission, and strict backend sanitization (magic-byte validation, EXIF metadata stripping, 5 MB size limit per file).

## Decision Drivers
- Backward Compatibility: Existing single-attachment records and legacy clients sending `photo` must continue to work without breaking changes.
- Database Schema Integrity: Do not perform disruptive table drops or migrations. Leverage existing relational models where possible.
- Security & Privacy: Never trust filename extensions. Validate magic bytes. Strip GPS coordinates and camera EXIF metadata before saving to disk/S3. Store outside public web roots.

## Decision Outcome
1. **Relational Model**: The existing `concern_attachments` table already features a one-to-many foreign key relationship with `concern_reports` (`report_id`). No destructive database migration is required.
2. **Backend Controller**: Update `ConcernSubmitHandler` (`backend/controllers/concerns.py`) to accept `request.files.getlist("photos")` in addition to fallback `request.files.get("photo")`. Enforce `len(files) <= 5`.
3. **Metadata Stripping**: Process each image sequentially through `AttachmentStorageService.store_attachment`, which verifies magic bytes and uses Pillow to strip EXIF data before persisting.
4. **Atomic Transaction**: Commit all attachment records and the parent report within a single database transaction. If any attachment fails sanitization or size limit, fail closed and rollback.
5. **Frontend UI**: Enable `<input type="file" multiple accept="image/*">`, maintain an array of up to 5 files with thumbnail previews and individual removal buttons, and summarize all attached photos on the Review step.
