"""Admin routes: general admin functionality (tenant management removed with multi-tenancy)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.auth.models import User
from app.core.enums import Role

router = APIRouter()


@router.get("/users")
async def list_users(page: int = 1, limit: int = 50, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.SUPERADMIN, Role.ADMIN]))):
    """List all platform users."""
    offset = (page - 1) * limit
    stmt = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "status": u.status.value if hasattr(u.status, "value") else str(u.status),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/organizations", include_in_schema=False)
async def list_organizations():
    """Deprecated: tenant management removed. Return empty list for backward compat."""
    return []


@router.post("/organizations", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_organization():
    """Deprecated: tenant management removed."""
    from app.core.exceptions import NotFoundError
    raise NotFoundError("Organization management has been removed")


@router.patch("/organizations/{org_id}", include_in_schema=False)
async def update_organization(org_id: str):
    """Deprecated: tenant management removed. No-op for backward compat."""
    return {"id": org_id, "message": "Organization management has been removed"}
