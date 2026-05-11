"""FastAPI app bootstrap — all routers wired."""

import logging
from datetime import date, datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.enums import Role, UserStatus, CycleStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, docs_url="/docs" if settings.DEBUG else None, redoc_url="/redoc" if settings.DEBUG else None)

# CORS — origins from config
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    logger.info("Starting Knowledge Factory API...")
    from app.database import async_session_factory, Base
    from sqlalchemy import create_engine as create_sync_engine

    # Import only the models we actually use
    from app.features.auth.models import User
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle

    if "sqlite" in settings.DATABASE_URL:
        sync_engine = create_sync_engine(settings.DATABASE_URL.replace("+aiosqlite://", "://"))
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()

    logger.info("Database initialized.")
