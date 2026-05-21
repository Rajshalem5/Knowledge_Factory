"""SuperAdmin routes — platform overview, user management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.features.auth.models import User
from app.core.enums import Role

router = APIRouter()


@router.get("/organizations")
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN])),
):
    """Platform overview — aggregated stats."""
    r = await db.execute(text("SELECT COUNT(*) FROM candidates"))
    total_candidates = r.scalar() or 0

    r = await db.execute(text("SELECT COUNT(*) FROM hiring_cycles"))
    total_cycles = r.scalar() or 0

    r = await db.execute(text("SELECT COUNT(*) FROM hiring_cycles WHERE status = 'ACTIVE'"))
    active_cycles = r.scalar() or 0

    return [
        {
            "id": "1",
            "name": "Knowledge Factory",
            "candidateCount": total_candidates,
            "activeHiringCycles": active_cycles,
            "plan": "enterprise",
        }
    ]


@router.get("/users")
async def list_all_users(
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([Role.SUPER_ADMIN])),
):
    """List all platform users."""
    offset = (page - 1) * limit
    result = await db.execute(
        text("""
            SELECT id, email, name, role, status, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {"limit": limit, "offset": offset},
    )
    rows = result.fetchall()

    count_r = await db.execute(text("SELECT COUNT(*) FROM users"))
    total = count_r.scalar() or 0

    return {
        "data": [
            {
                "id": str(r.id),
                "email": r.email,
                "name": r.name,
                "role": r.role,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([Role.SUPER_ADMIN])),
):
    """Update a user's role. Normalizes input to canonical form."""
    raw_role = body.get("role", "")
    new_role = Role.normalize(raw_role)

    valid_roles = [Role.SUPER_ADMIN.value, Role.ADMIN.value, Role.HR.value, "CANDIDATE", Role.INTERVIEWER.value]
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role: {raw_role}")

    await db.execute(
        text("UPDATE users SET role = :role WHERE id = :id"),
        {"role": new_role, "id": user_id},
    )
    await db.commit()
    return {"id": user_id, "role": new_role}
