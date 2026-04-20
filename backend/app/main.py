"""
FastAPI application bootstrap.

This module creates the FastAPI application instance, registers middleware,
and includes feature routers. It is the single entry-point referenced by
the uvicorn command:

    uvicorn app.main:app --reload

Currently this is a scaffold — middleware and routers are wired as
placeholders. Business logic will be added in subsequent phases.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


# ── Lifespan ───────────────────────────────────────────────────────
# The lifespan context manager runs startup/shutdown logic that needs
# access to the app instance. This is the modern replacement for the
# deprecated @app.on_event("startup") / @app.on_event("shutdown").
@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan: runs once on startup, yields, then runs on shutdown.

    Future additions:
    - Verify database connectivity (engine.connect())
    - Warm Redis connection pool
    - Seed initial data in development mode
    """
    # ── Startup ────────────────────────────────────────────────
    settings = get_settings()
    if settings.DEBUG:
        print(f"[startup] {settings.APP_NAME} v{settings.APP_VERSION} — DEBUG mode")

    yield  # Application runs here

    # ── Shutdown ───────────────────────────────────────────────
    # Dispose of the database engine connection pool gracefully.
    from app.database import engine
    await engine.dispose()


# ── Application Instance ───────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered intern hiring and evaluation platform",
    lifespan=lifespan,
    # Disable docs in production by checking settings.DEBUG later
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ── CORS Middleware ────────────────────────────────────────────────
# Allow the React frontend (running on a different port in development)
# to communicate with the API. Origins are configurable via CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ───────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """
    Lightweight liveness probe.

    Returns 200 with {"status": "ok"} when the API process is alive.
    Load balancers and Kubernetes use this endpoint to decide whether
    to route traffic to this pod.

    A deeper readiness probe (checking DB + Redis connectivity) will be
    added separately at /health/ready once those integrations land.
    """
    return {"status": "ok"}


# ── Feature Routers ────────────────────────────────────────────────
# Each feature module exposes an `api_router` that groups related
# endpoints. They are included here with a common /api prefix.
# Un-comment each router as the feature is implemented.

# from app.features.auth.routes import router as auth_router
# app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# from app.features.candidates.routes import router as candidates_router
# app.include_router(candidates_router, prefix="/api/candidates", tags=["candidates"])

# from app.features.screening.routes import router as screening_router
# app.include_router(screening_router, prefix="/api/screening", tags=["screening"])

# from app.features.assessments.routes import router as assessments_router
# app.include_router(assessments_router, prefix="/api/assessments", tags=["assessments"])

# from app.features.code_execution.routes import router as code_exec_router
# app.include_router(code_exec_router, prefix="/api/code", tags=["code-execution"])

# from app.features.proctoring.routes import router as proctoring_router
# app.include_router(proctoring_router, prefix="/api/proctoring", tags=["proctoring"])

# from app.features.interviews.routes import router as interviews_router
# app.include_router(interviews_router, prefix="/api/interviews", tags=["interviews"])

# from app.features.selection.routes import router as selection_router
# app.include_router(selection_router, prefix="/api/selection", tags=["selection"])

# from app.features.notifications.routes import router as notifications_router
# app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])

# from app.features.analytics.routes import router as analytics_router
# app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])

# from app.features.audit.routes import router as audit_router
# app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
