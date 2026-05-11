"""SuperAdmin routes — platform overview, user management.
Uses raw SQL against Supabase tables.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, AuthUser, require_roles

router = APIRouter()


@router.get("/organizations")
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(require_roles("SUPERADMIN")),
):
    """Platform overview — aggregated stats (no multi-tenancy)."""
    # Total candidates
    r = await db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'CANDIDATE'"))
    total_candidates = r.scalar() or 0

    # Total jobs
    r = await db.execute(text("SELECT COUNT(*) FROM jobs"))
    total_jobs = r.scalar() or 0

    # Active jobs
    r = await db.execute(text("SELECT COUNT(*) FROM jobs WHERE status = 'OPEN'"))
    active_jobs = r.scalar() or 0

    # Return as a list to match the frontend's expected Organization[] type
    return [
        {
            "id": "1",
            "name": "Knowledge Factory",
            "candidateCount": total_candidates,
            "activeHiringCycles": active_jobs,
            "plan": "enterprise",
        }
    ]


@router.get("/users")
async def list_all_users(
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(require_roles("SUPERADMIN")),
):
    """List all platform users."""
    offset = (page - 1) * limit
    result = await db.execute(
        text("""
            SELECT id, email, full_name, role, status, created_at
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
                "name": r.full_name,
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
    current_user: AuthUser = Depends(require_roles("SUPERADMIN")),
):
    """Update a user's role."""
    new_role = body.get("role", "").upper()
    if new_role not in ("SUPERADMIN", "ADMIN", "HR", "CANDIDATE", "INTERVIEWER"):
        raise HTTPException(status_code=400, detail=f"Invalid role: {new_role}")

    await db.execute(
        text("UPDATE users SET role = :role, updated_at = now() WHERE id = :id"),
        {"role": new_role, "id": user_id},
    )
    await db.commit()
    return {"id": user_id, "role": new_role}
