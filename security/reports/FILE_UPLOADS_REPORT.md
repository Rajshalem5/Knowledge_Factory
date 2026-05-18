# FILE_UPLOADS Security Report

## Status: MEDIUM → FIXED

## Findings

### CRITICAL (FIXED): No file type validation by magic bytes

Bulk CSV uploads had no validation beyond trying to parse them — any file (including binaries) would be accepted and decoded as UTF-8.

**Fix applied:**
- Created `backend/app/core/file_validation.py` — uses `filetype` library for magic byte detection on binary files, manual UTF-8 decode check for text files
- Applied to both bulk upload endpoints (`/preview` and `/upload`)
- 10 MB size limit enforced
- Binary files are auto-rejected on CSV upload endpoints (only text/CSV accepted)

### What's at risk (if not addressed)

- An attacker uploads a `.csv` that's actually a 2GB binary → memory exhaustion
- An attacker uploads a `.csv` that's actually an executable → served from same origin

### What's already secure

- CSV content is parsed via `csv.DictReader` — never executed
- Uploads require HR/ADMIN/SUPERADMIN role
- UUID rename available for when file storage is implemented

## Recommendations

1. **[INFO]** When resume/Govt ID upload endpoints are built, reuse `validate_upload()` with `allow_text=False` — it's already ready for PDF/JPEG/PNG
2. **[INFO]** Serve uploaded files from a different origin (subdomain or CDN) — this is the single highest-impact defense
3. **[LOW]** Add ClamAV scanning for production deployment
