"""FastAPI app bootstrap — all routers wired + SPA fallback."""

import logging
from pathlib import Path
from datetime import date, datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.config import settings
from app.core.enums import Role, UserStatus, CycleStatus

# ── Rotating File Logging ─────────────────────────────────────────
import logging.handlers
logs_dir = Path(__file__).resolve().parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)
file_handler = logging.handlers.TimedRotatingFileHandler(
    logs_dir / "knowledge_factory.log",
    when="midnight",
    interval=1,
    backupCount=30,
)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, docs_url="/docs" if settings.DEBUG else None, redoc_url="/redoc" if settings.DEBUG else None)

# CORS — origins from config
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Headers Middleware ──────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    return response


# ── Rate Limiting for Auth Endpoints ────────────────────────────
from collections import defaultdict
from datetime import datetime, timedelta, timezone

_rate_limit_store: dict[str, list[datetime]] = defaultdict(list)
RATE_LIMIT_WINDOW = timedelta(minutes=15)
RATE_LIMIT_MAX = 20  # requests per window


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiter for auth endpoints.
    
    In DEBUG mode uses a higher threshold so dev workflow is not interrupted.
    Follows guidance from addyosmani/agent-skills security-and-hardening:
    rate limiting should never be fully disabled — not even in dev.
    """
    path = request.url.path
    # Only rate-limit auth endpoints
    if not path.startswith("/api/auth/") or path in ("/api/auth/me", "/api/auth/logout", "/api/auth/refresh", "/api/auth/confirm-password", "/api/auth/delete-account"):
        return await call_next(request)

    max_requests = RATE_LIMIT_MAX * 5 if settings.DEBUG else RATE_LIMIT_MAX  # 100 in dev, 20 in prod

    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{path}"
    now = datetime.now(timezone.utc)

    # Clean old entries
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < RATE_LIMIT_WINDOW]

    if len(_rate_limit_store[key]) >= max_requests:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            {"detail": "Too many requests. Please try again later."},
            status_code=429,
        )

    _rate_limit_store[key].append(now)
    return await call_next(request)


# ── Maintenance Mode Middleware ─────────────────────────────────
@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    if settings.MAINTENANCE_MODE:
        path = request.url.path
        if not (path.startswith("/api/auth/login") or path.startswith("/docs") or path == "/health"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "System under maintenance. Please check back later."}, status_code=503)
    return await call_next(request)

# ── Sentry Init ────────────────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

# ── Feature Routers ───────────────────────────────────────────────
from app.features.auth.routes import router as auth_router
from app.features.assessments.routes import router as assessments_router
from app.features.candidates.routes import router as candidates_router
from app.features.proctoring.routes import router as proctoring_router
from app.features.interviews.routes import router as interviews_router
from app.features.selection.routes import router as selection_router
from app.features.analytics.routes import router as analytics_router
from app.features.admin.routes import router as admin_router
from app.features.hiring_cycles.routes import router as hiring_cycles_router
from app.features.screening.routes import router as screening_router
from app.features.code_execution.routes import router as code_execution_router
from app.features.questions.routes import router as questions_router
from app.features.audit.routes import router as audit_router

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(candidates_router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(assessments_router, prefix="/api/assessment", tags=["Assessment"])
app.include_router(code_execution_router, prefix="/api/code", tags=["Code Execution"])
app.include_router(questions_router, prefix="/api/questions", tags=["Questions"])
app.include_router(proctoring_router, prefix="/api/proctoring", tags=["Proctoring"])
app.include_router(interviews_router, prefix="/api", tags=["Interviews"])
app.include_router(selection_router, prefix="/api/selection", tags=["Selection"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(hiring_cycles_router, prefix="/api/hiring-cycles", tags=["Hiring Cycles"])
app.include_router(screening_router, prefix="/api/screening", tags=["Screening"])
app.include_router(audit_router, prefix="/api/audit", tags=["Audit"])


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION, "debug": settings.DEBUG}


# ── SPA Fallback — serve frontend for non-API routes ──────────────
frontend_dist = Path(__file__).resolve().parent.parent.parent / "app" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    # Serve /assets, /favicon.svg, /icons.svg as static files
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    assets_dir = frontend_dist / "assets"

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Skip API routes, health, docs
        if (full_path.startswith("api/") or full_path == "api"
            or full_path.startswith("docs") or full_path.startswith("redoc")
            or full_path == "health" or full_path.startswith("openapi")):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        # Serve actual files like /favicon.svg, /icons.svg
        if full_path in ("favicon.svg", "icons.svg"):
            f = frontend_dist / full_path
            if f.exists():
                return HTMLResponse(content=f.read_bytes(), media_type="image/svg+xml")
        return HTMLResponse(content=(frontend_dist / "index.html").read_text())

    @app.get("/")
    async def root():
        return HTMLResponse(content=(frontend_dist / "index.html").read_text())

    logger.info("Frontend SPA mounted from %s", frontend_dist)


@app.on_event("startup")
async def startup():
    logger.info("Starting Knowledge Factory API...")
    from app.database import async_session_factory, Base
    from sqlalchemy import create_engine as create_sync_engine

    # Import all models to ensure tables/columns exist and relationships resolve
    from app.features.auth.models import User
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle
    from app.features.assessments.models import Assessment, Submission, Score  # noqa: F401
    from app.features.proctoring.models import ProctoringRecord  # noqa: F401
    from app.features.interviews.models import InterviewFeedback  # noqa: F401
    from app.features.audit.models import AuditLog  # noqa: F401
    from app.features.analytics.models import AIGenerationLog  # noqa: F401

    if "sqlite" in settings.DATABASE_URL:
        sync_engine = create_sync_engine(settings.DATABASE_URL.replace("+aiosqlite://", "://"))
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()

    logger.info("Database initialized.")
