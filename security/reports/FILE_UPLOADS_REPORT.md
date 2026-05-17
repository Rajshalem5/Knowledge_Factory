# FILE_UPLOADS Security Report

## Status: MEDIUM

## Findings

### MEDIUM: No file type validation by magic bytes

The bulk CSV upload (`backend/app/features/candidates/routes.py`) accepts `UploadFile` but:
- Does not validate file type by magic bytes (only relies on browser's `Content-Type`)
- No extension whitelist enforcement
- Files read as decoded text (safe for CSV parsing, but no validation)

### Resume/Govt ID uploads
Candidates can upload resumes and government IDs, stored as URLs (`resume_url`, `govt_id_url`). The upload handling needs to be checked for:
- File type validation (magic bytes vs extension)
- Server-side rename to UUID
- Storage on separate domain

## Recommendations

1. **[MEDIUM]** Add magic byte validation for all file uploads (use `python-magic` or `file` command)
2. **[MEDIUM]** Store uploaded files with UUID-based names on a separate domain/bucket
3. **[LOW]** Add server-side file size limits
