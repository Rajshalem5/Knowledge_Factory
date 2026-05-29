"""Admin routes: general admin functionality."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import require_role
from app.features.auth.models import User
from app.core.enums import Role, UserStatus
from app.core.security import hash_password
from app.features.admin.schemas import UserCreate, UserUpdate, UserResponse, PasswordReset, UserListResponse

router = APIRouter()


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = 1, 
    limit: int = 50, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN]))
):
    """List all platform users."""
    offset = (page - 1) * limit

    # Get total count
    count_stmt = select(func.count()).select_from(User)
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    # Get users
    stmt = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    users = res.scalars().all()

    user_data = [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            status=u.status,
            created_at=u.created_at.isoformat() if u.created_at else None
        )
        for u in users
    ]

    return {
        "data": user_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    }



@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    payload: UserCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN]))
):
    """Create a new user (ADMIN, HR, or INTERVIEWER)."""
    # Hierarchy check
    if current_user.role == Role.ADMIN:
        if payload.role in [Role.SUPER_ADMIN, Role.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ADMINs can only create HR or Interviewer users"
            )
    
    # SUPER_ADMIN can create anyone except another SUPER_ADMIN (optional policy)
    if current_user.role == Role.SUPER_ADMIN:
        if payload.role == Role.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only one SUPER_ADMIN allowed or must be created via CLI"
            )

    # Check if user already exists
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        status=payload.status
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        status=new_user.status,
        created_at=new_user.created_at.isoformat()
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN]))
):
    """Update user details."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hierarchy check
    if target_user.role == Role.SUPER_ADMIN:
        if current_user.id != target_user.id: # only SUPER_ADMIN can edit themselves
             raise HTTPException(status_code=403, detail="SUPER_ADMIN cannot be modified by others")

    if current_user.role == Role.ADMIN:
        if target_user.role in [Role.SUPER_ADMIN, Role.ADMIN]:
            raise HTTPException(status_code=403, detail="ADMINs can only modify HR/Interviewer users")
        if payload.role and payload.role in [Role.SUPER_ADMIN, Role.ADMIN]:
            raise HTTPException(status_code=403, detail="Privilege escalation: ADMIN cannot promote to ADMIN/SUPER_ADMIN")

    # Perform update
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(target_user, key, value)

    await db.commit()
    await db.refresh(target_user)

    return UserResponse(
        id=target_user.id,
        email=target_user.email,
        name=target_user.name,
        role=target_user.role,
        status=target_user.status,
        created_at=target_user.created_at.isoformat()
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN]))
):
    """Delete a user."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hierarchy check
    if target_user.role == Role.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="SUPER_ADMIN cannot be removed")

    if current_user.role == Role.ADMIN and target_user.role in [Role.SUPER_ADMIN, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="ADMINs can only remove HR users")

    await db.delete(target_user)
    await db.commit()

    return None


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


# ── Audit & Export ────────────────────────────────────────────
@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN])),
):
    """Return paginated audit log entries."""
    from app.features.audit.models import AuditLog
    offset = (page - 1) * limit
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    from sqlalchemy import func as sa_func
    count_stmt = select(sa_func.count(AuditLog.id))
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0
    return {
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "actor_id": str(log.actor_id) if log.actor_id else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "page": page,
        "limit": limit,
        "total": total,
    }


@router.get("/export-db")
async def export_database(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.SUPER_ADMIN, Role.ADMIN])),
):
    """Export full database as JSON. Admin only."""
    from app.features.auth.models import User
    from app.features.candidates.models import Candidate
    from app.features.assessments.models import Assessment, Score
    from app.features.hiring_cycles.models import HiringCycle

    users = (await db.execute(select(User))).scalars().all()
    candidates = (await db.execute(select(Candidate))).scalars().all()
    assessments = (await db.execute(select(Assessment))).scalars().all()
    scores = (await db.execute(select(Score))).scalars().all()
    cycles = (await db.execute(select(HiringCycle))).scalars().all()

    def serialize(obj):
        result = {}
        SENSITIVE_FIELDS = {"password_hash"}
        for col in obj.__table__.columns:
            if col.name in SENSITIVE_FIELDS:
                continue
            val = getattr(obj, col.name, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif hasattr(val, "value"):
                val = val.value
            result[col.name] = val
        return result

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "users": [serialize(u) for u in users],
        "candidates": [serialize(c) for c in candidates],
        "assessments": [serialize(a) for a in assessments],
        "scores": [serialize(s) for s in scores],
        "hiring_cycles": [serialize(h) for h in cycles],
    }


from datetime import datetime, timezone
