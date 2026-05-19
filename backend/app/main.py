"""FastAPI app bootstrap — all routers wired with security middleware."""

import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.enums import Role, UserStatus, CycleStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


# ── Lifespan Events ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handling."""
    logger.info("Starting Knowledge Factory API...")
    from app.database import async_session_factory, Base
    from sqlalchemy import create_engine as create_sync_engine

    # Import ALL models so SQLAlchemy discovers them
    from app.features.auth.models import User
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle
    from app.features.assessments.models import Assessment, Submission, Score
    from app.features.proctoring.models import ProctoringRecord
    from app.features.interviews.models import InterviewFeedback
    from app.features.audit.models import AuditLog
    from app.features.analytics.models import AIGenerationLog
    from app.features.notifications.models import EmailLog

    if "sqlite" in settings.DATABASE_URL:
        sync_engine = create_sync_engine(settings.DATABASE_URL.replace("+aiosqlite://", "://"))
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()

    logger.info("Database initialized.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── CORS — strict, no wildcard fallback ─────────────────────────
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not cors_origins:
    logger.warning("CORS_ORIGINS is empty — API will not be accessible from any origin.")
    cors_origins = []  # empty = all origins denied by CORS spec
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# ── Security Headers Middleware ─────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# ── Global Exception Handler (prevent info leakage) ──────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Feature Routers ───────────────────────────────────────────────
from app.features.auth.routes import router as auth_router
from app.features.candidates.routes import router as candidates_router
from app.features.assessments.routes import router as assessments_router
from app.features.proctoring.routes import router as proctoring_router
from app.features.interviews.routes import router as interviews_router
from app.features.selection.routes import router as selection_router
from app.features.analytics.routes import router as analytics_router
from app.features.admin.routes import router as admin_router
from app.features.hiring_cycles.routes import router as hiring_cycles_router
from app.features.screening.routes import router as screening_router
from app.features.audit.routes import router as audit_router
from app.features.code_execution.routes import router as code_execution_router
from app.features.questions.routes import router as questions_router

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
app.include_router(audit_router, prefix="/api/admin", tags=["Audit"])


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION, "debug": settings.DEBUG}
