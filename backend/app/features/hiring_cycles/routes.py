"""Hiring cycle CRUD routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.core.enums import Role, CycleStatus
from app.features.hiring_cycles.models import HiringCycle

router = APIRouter()


@router.get("/")
async def list_cycles(db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    stmt = select(HiringCycle).order_by(HiringCycle.created_at.desc())
    res = await db.execute(stmt)
    cycles = res.scalars().all()
    return [
        {
            "id": str(c.id), "name": c.name, "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "status": c.status.value if isinstance(c.status, CycleStatus) else c.status,
            "eligibility_config": c.eligibility_config,
            "assessment_config": c.assessment_config,
            "proctoring_config": c.proctoring_config,
            "created_at": c.created_at.isoformat(),
        }
        for c in cycles
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_cycle(body: dict, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.ADMIN, Role.SUPER_ADMIN]))):
    from datetime import date

    cycle = HiringCycle(
        name=body.get("name", ""),
        start_date=date.fromisoformat(body["start_date"]) if isinstance(body.get("start_date"), str) else body.get("start_date"),
        end_date=date.fromisoformat(body["end_date"]) if isinstance(body.get("end_date"), str) else body.get("end_date"),
        status=CycleStatus.ACTIVE,
        eligibility_config=body.get("eligibility_config", {}),
        assessment_config=body.get("assessment_config", {}),
        proctoring_config=body.get("proctoring_config", {}),
        created_by=current_user.id,
    )
    db.add(cycle)
    await db.flush()
    return {"id": str(cycle.id), "name": cycle.name}


@router.patch("/{cycle_id}")
async def update_cycle(cycle_id: UUID, body: dict, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.ADMIN, Role.SUPER_ADMIN]))):
    stmt = select(HiringCycle).where(HiringCycle.id == str(cycle_id))
    res = await db.execute(stmt)
    cycle = res.scalar_one_or_none()
    if not cycle:
        raise HTTPException(status_code=404, detail="Hiring cycle not found")

    for key in ["name", "status"]:
        if key in body:
            setattr(cycle, key, body[key])
    for json_key in ["eligibility_config", "assessment_config", "proctoring_config"]:
        if json_key in body:
            setattr(cycle, json_key, body[json_key])

    await db.flush()
    return {"id": str(cycle.id), "message": "Cycle updated"}
