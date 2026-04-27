"""FastAPI app bootstrap — all routers wired."""

import uuid
from datetime import date, datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.core.enums import Role, UserStatus, CycleStatus, TenantStatus
from app.features.auth.models import Tenant, User
from app.features.hiring_cycles.models import HiringCycle

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
from app.features.audit.routes import router as audit_router

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(candidates_router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(assessments_router, prefix="/api/assessment", tags=["Assessment"])
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
    return {"status": "ok"}


async def seed_default_tenant_and_cycle(db):
    """Create default tenant and active cycle if none exist."""
    from sqlalchemy import select as sa_select

    res = await db.execute(sa_select(Tenant).limit(1))
    if res.scalar_one_or_none():
        return

    tenant = Tenant(name="Default Org", slug="default-org", status=TenantStatus.ACTIVE)
    db.add(tenant)
    await db.flush()

    # Create a superadmin user
    from app.core.security import hash_password
    admin = User(
        tenant_id=tenant.id,
        email="admin@knowledgefactory.io",
        password_hash=hash_password("Admin@12345"),
        name="Platform Admin",
        role=Role.SUPERADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)

    # Default hiring cycle
    cycle = HiringCycle(
        tenant_id=tenant.id,
        name="Summer 2026 Internship",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 12, 31),
        status=CycleStatus.ACTIVE,
        eligibility_config={"min_cgpa": 7.0, "allowed_branches": ["CSE", "ECE", "EEE", "IT"]},
        assessment_config={"difficulty_mix": "medium", "languages": ["python", "javascript"]},
        proctoring_config={"max_warnings": 3, "retention_days": 20},
        created_by=admin.id,
    )
    db.add(cycle)
    await db.flush()


@app.on_event("startup")
async def startup():
    logger.info("Starting Knowledge Factory API...")
    from app.database import async_session_factory, Base
    from sqlalchemy import create_engine as create_sync_engine

    # Import ALL models so SQLAlchemy discovers them
    from app.features.auth.models import Tenant, User
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle
    from app.features.assessments.models import Assessment, Submission, Score
    from app.features.proctoring.models import ProctoringRecord
    from app.features.interviews.models import InterviewFeedback
    from app.features.audit.models import AuditLog
    from app.features.analytics.models import AIGenerationLog

    if "sqlite" in settings.DATABASE_URL:
        sync_engine = create_sync_engine(settings.DATABASE_URL.replace("+aiosqlite://", "://"))
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()

    async with async_session_factory() as session:
        await seed_default_tenant_and_cycle(session)
        await session.commit()

    logger.info("Database initialized. Default tenant + cycle seeded.")
