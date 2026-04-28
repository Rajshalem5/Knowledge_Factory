"""Analytics routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.analytics.schemas import FunnelResponse, DashboardResponse
from app.features.analytics.service import AnalyticsService
from app.core.enums import Role

router = APIRouter()


@router.get("/funnel", response_model=FunnelResponse)
async def get_hiring_funnel(db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    service = AnalyticsService(db)
    return await service.get_hiring_funnel(current_user.tenant_id)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    service = AnalyticsService(db)
    return await service.get_dashboard(current_user.tenant_id)
