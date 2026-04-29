"""Candidate management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.features.candidates.schemas import CandidateRead, CandidateListResponse, BulkUploadPreview
from app.features.candidates.service import CandidateService
from app.core.enums import CandidateStatus, Role

router = APIRouter()


@router.get("/", response_model=CandidateListResponse)
async def list_candidates(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: CandidateStatus | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    service = CandidateService(db)
    candidates, total = await service.list_candidates(
        page=page, limit=limit, status=status, search=search,
    )
    return {"data": candidates, "pagination": {"page": page, "limit": limit, "total": total, "total_pages": (total + limit - 1) // limit if limit else 1}}


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: UUID, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN, Role.INTERVIEWER]))):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.get("/me", response_model=CandidateRead)
async def get_my_profile(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Get the authenticated candidate's own profile."""
    service = CandidateService(db)
    return await service.get_my_profile(current_user.id)


@router.patch("/{candidate_id}/status", response_model=CandidateRead)
async def update_candidate_status(candidate_id: UUID, update: dict, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    from app.features.candidates.models import Candidate
    new_status = CandidateStatus(update["status"])
    service = CandidateService(db)
    try:
        candidate = await service.update_status(candidate_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_candidates(db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    """Bulk upload placeholder — accepts CSV file via multipart form."""
    import csv
    import io
    import uuid
    from fastapi import UploadFile, Form

    # Accept an optional CSV file in form data
    from fastapi import Request
    request = Request({})
    body = await request.form()
    file_obj = body.get("file")

    if not isinstance(file_obj, UploadFile):
        return BulkUploadPreview(batch_id="", total_records=0, valid_records=0, invalid_records=0, preview=[], errors=[])

    content = await file_obj.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    records = list(reader)

    batch_id = str(uuid.uuid4())[:8]
    preview = []
    errors = []
    for i, row in enumerate(records[:20]):  # Preview first 20
        try:
            _ = float(row.get("cgpa", 0))
            preview.append({"row": i + 1, "data": row, "valid": True})
        except (ValueError, KeyError):
            errors.append({"row": i + 1, "error": "Invalid CGPA or missing required fields"})
            preview.append({"row": i + 1, "data": row, "valid": False})

    valid_count = sum(1 for p in preview if p["valid"])
    return BulkUploadPreview(
        batch_id=batch_id,
        total_records=len(records),
        valid_records=valid_count,
        invalid_records=len(records) - valid_count,
        preview=preview,
        errors=errors,
    )
