"""Analytics routes."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.analytics.schemas import FunnelResponse, DashboardResponse
from app.features.analytics.service import AnalyticsService
from app.core.enums import Role

router = APIRouter()


@router.get("/funnel", response_model=FunnelResponse)
async def get_hiring_funnel(
    branch: str | None = Query(None, description="Optional filter: only candidates from this branch"),
    college: str | None = Query(None, description="Optional filter: only candidates from this college"),
    search: str | None = Query(None, description="Optional search term (name, email, college)"),
    name: str | None = Query(None, description="Optional filter: only candidates matching this name"),
    passed_out_year: int | None = Query(None, description="Optional filter: only candidates from this passed-out year"),
    language_choice: str | None = Query(None, description="Optional filter: only candidates with this language choice"),
    cgpa_min: float | None = Query(None, ge=0.0, le=10.0, description="Optional min CGPA filter"),
    cgpa_max: float | None = Query(None, ge=0.0, le=10.0, description="Optional max CGPA filter"),
    has_resume: bool | None = Query(None, description="Filter by whether candidate has uploaded a resume"),
    has_govt_id: bool | None = Query(None, description="Filter by whether candidate has uploaded govt ID"),
    created_after: date | None = Query(None, description="Filter candidates created after this date (ISO format, e.g. 2026-01-01)"),
    created_before: date | None = Query(None, description="Filter candidates created before this date (ISO format, e.g. 2026-06-30)"),
    passed_out_year_min: int | None = Query(None, ge=1900, le=2100, description="Filter by minimum passed-out year"),
    passed_out_year_max: int | None = Query(None, ge=1900, le=2100, description="Filter by maximum passed-out year"),
    email_verified: bool | None = Query(None, description="Filter by email verification status"),
    phone: str | None = Query(None, description="Filter candidates by phone number"),
    email: str | None = Query(None, description="Filter candidates by exact email address"),
    cycle_id: str | None = Query(None, description="Filter by hiring cycle ID"),
    status: str | None = Query(None, description="Filter by candidate status (raw or display_status)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    service = AnalyticsService(db)
    return await service.get_hiring_funnel(
        branch=branch, college=college, search=search,
        name=name,
        passed_out_year=passed_out_year, language_choice=language_choice,
        cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified, phone=phone, email=email,
        cycle_id=cycle_id,
        status=status,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    service = AnalyticsService(db)
    return await service.get_dashboard()
