"""
Proctoring routes.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CANDIDATE_ONLY
from app.features.proctoring.schemas import ProctoringEventCreate
from app.features.proctoring.service import ProctoringService

router = APIRouter()


@router.post("/event", status_code=status.HTTP_201_CREATED)
async def record_proctoring_event(
    event_data: ProctoringEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(CANDIDATE_ONLY)
):
    """
    Record a real-time proctoring event from the client.
    """
    service = ProctoringService(db)
    return await service.record_event(event_data)
