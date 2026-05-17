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


# ── Audit & Export ────────────────────────────────────────────
@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.SUPERADMIN, Role.ADMIN])),
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
    current_user=Depends(require_role([Role.SUPERADMIN, Role.ADMIN])),
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
