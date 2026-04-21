"""
Candidate management routes.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.features.candidates.schemas import (
    CandidateRead, 
    CandidateListResponse, 
    CandidateStatusUpdate,
    BulkUploadPreview
)
from app.features.candidates.service import CandidateService
from app.core.enums import CandidateStatus, Role

router = APIRouter()


@router.get("/", response_model=CandidateListResponse)
async def list_candidates(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[CandidateStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))
):
    """
    List candidates for the current tenant.
    """
    service = CandidateService(db)
    candidates, total = await service.list_candidates(
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
        status=status
    )
    
    return {
        "data": candidates,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    }


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN, Role.INTERVIEWER]))
):
    """
    Get detailed profile of a candidate.
    """
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id, current_user.tenant_id)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return candidate


@router.patch("/{candidate_id}/status", response_model=CandidateRead)
async def update_candidate_status(
    candidate_id: UUID,
    update_data: CandidateStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))
):
    """
    Manually override candidate status.
    """
    service = CandidateService(db)
    candidate = await service.update_status(candidate_id, current_user.tenant_id, update_data)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return candidate


@router.post("/bulk-upload", response_model=BulkUploadPreview)
async def bulk_upload_candidates(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))
):
    """
    Upload a CSV/Excel file and get a preview of records to be created.
    (Placeholder: File upload logic to be added)
    """
    service = CandidateService(db)
    # logic would extract file content here
    return await service.bulk_upload_preview(b"")
