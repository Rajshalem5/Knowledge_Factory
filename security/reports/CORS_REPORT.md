# CORS Security Report

## Status: PASS

## Findings

CORS is configured in `backend/app/main.py`:
```python
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- Origins are an **explicit allowlist** from config (`http://localhost:5173`, etc.)
- **No wildcard (`*`)** origin
- `credentials: true` is paired with specific origins (correct)
