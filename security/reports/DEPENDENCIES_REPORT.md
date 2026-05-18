# DEPENDENCIES Security Report

## Status: LOW → FIXED

## Findings

### FIXED: Some dependencies used `>=` pinning

All 18 packages in `requirements.txt` now use exact `==` version pinning for reproducible builds.

### PASS: Lock files

- Frontend: `package-lock.json` committed
- Backend: exact version pinning in `requirements.txt` ensures reproducibility
