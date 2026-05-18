# FILE_UPLOADS Fix Plan

## Changes

1. `backend/app/core/file_validation.py` — NEW: centralized file validation utility
   - `validate_upload()`: checks size, magic bytes (via `filetype`), UTF-8 decode
   - `secure_filename()`: generates UUID-based filenames
   - 10 MB size limit
   
2. `backend/app/features/candidates/routes.py` — PATCHED: both bulk upload endpoints now call `validate_upload()` before processing

3. `backend/requirements.txt` — ADDED: `filetype==1.2.0`

## Verification goals

- [ ] Uploading a `.csv` with actual CSV content succeeds
- [ ] Uploading a `.csv` that's actually a binary file (e.g. renamed `.png`) is rejected with 400
- [ ] Uploading a file > 10 MB is rejected
- [ ] Uploading a `.pdf` or `.py` disguised as `.csv` is rejected

## Manual verification (for the human)

- When resume/Govt ID upload endpoints are built, require `allow_text=False` — PDF/JPEG/PNG only
- Configure separate subdomain for file serving before production
