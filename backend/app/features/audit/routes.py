"""Audit log routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.audit.models import AuditLog
from app.core.enums import Role

router = APIRouter()


@router.get("/logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.ADMIN, Role.SUPERADMIN])),
):
    """Retrieve audit logs for the current tenant."""
    q = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)

    res = await db.execute(q)
    logs = res.scalars().all()

    count_q = select(func.count()).select_from(q.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    return {
        "data": [
            {
                "id": str(l.id),
                "actor_id": str(l.actor_id) if l.actor_id else None,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": str(l.entity_id) if l.entity_id else None,
                "before_state": l.before_json,
                "after_state": l.after_json,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "pagination": {"page": page, "limit": limit, "total": total, "total_pages": (total + limit - 1) // limit if limit else 1},
    }
