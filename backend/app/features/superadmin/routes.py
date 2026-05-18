"""SuperAdmin routes — user management and role transfer."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.superadmin.service import SuperAdminService
from app.core.enums import Role

router = APIRouter()


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.SUPERADMIN])),
):
    """List all platform users with pagination. SUPERADMIN only."""
    service = SuperAdminService(db)
    return await service.list_all_users(page=page, limit=limit)


@router.post("/users/{user_id}/transfer")
async def transfer_superadmin(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.SUPERADMIN])),
):
    """Transfer superadmin role to an ADMIN user. Current superadmin is demoted to ADMIN."""
    service = SuperAdminService(db)
    try:
        return await service.transfer_superadmin(user_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
