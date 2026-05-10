"""Candidate management routes."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
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
    status: str | None = None,
    search: str | None = None,
    name: str | None = None,
    branch: str | None = None,
    college: str | None = None,
    cgpa_min: float | None = Query(None, ge=0.0, le=10.0),
    cgpa_max: float | None = Query(None, ge=0.0, le=10.0),
    passed_out_year: int | None = None,
    language_choice: str | None = None,
    has_resume: bool | None = Query(None, description="Filter by whether candidate has uploaded a resume"),
    has_govt_id: bool | None = Query(None, description="Filter by whether candidate has uploaded govt ID"),
    created_after: date | None = Query(None, description="Filter candidates created after this date (ISO format)"),
    created_before: date | None = Query(None, description="Filter candidates created before this date (ISO format)"),
    passed_out_year_min: int | None = Query(None, ge=1900, le=2100, description="Filter by minimum passed-out year"),
    passed_out_year_max: int | None = Query(None, ge=1900, le=2100, description="Filter by maximum passed-out year"),
    email_verified: bool | None = Query(None, description="Filter by email verification status"),
    phone: str | None = Query(None, description="Filter by phone number"),
    email: str | None = Query(None, description="Filter by exact email address"),
    cycle_id: str | None = Query(None, description="Filter candidates by hiring cycle ID"),
    has_phone: bool | None = Query(None, description="Filter by whether candidate has provided a phone number"),
    has_assessment: bool | None = Query(None, description="Filter by whether candidate has any assessment records"),
    updated_after: date | None = Query(None, description="Filter candidates updated after this date (ISO format)"),
    updated_before: date | None = Query(None, description="Filter candidates updated before this date (ISO format)"),
    assessment_status: str | None = Query(None, description="Filter candidates whose assessment has this status (e.g. IN_PROGRESS, COMPLETED)"),
    min_score: float | None = Query(None, ge=0.0, le=100.0, description="Filter candidates whose assessment score is >= this value"),
    max_score: float | None = Query(None, ge=0.0, le=100.0, description="Filter candidates whose assessment score is <= this value"),
    sort_by: str | None = Query(None, description="Sort column (name, email, college, branch, cgpa, passed_out_year, created_at, status)"),
    sort_order: str | None = Query("desc", description="Sort direction: asc or desc"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    service = CandidateService(db)
    candidates, total = await service.list_candidates(
        page=page, limit=limit, status=status, search=search,
        name=name,
        branch=branch, college=college, cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        passed_out_year=passed_out_year, language_choice=language_choice,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified,
        phone=phone,
        email=email,
        cycle_id=cycle_id,
        has_phone=has_phone,
        has_assessment=has_assessment,
        updated_after=updated_after,
        updated_before=updated_before,
        assessment_status=assessment_status,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by, sort_order=sort_order,
    )
    return {"data": candidates, "pagination": {"page": page, "limit": limit, "total": total, "total_pages": (total + limit - 1) // limit if limit else 1}}


@router.get("/me", response_model=CandidateRead)
async def get_my_profile(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Get the authenticated candidate's own profile."""
    service = CandidateService(db)
    return await service.get_my_profile(current_user.id)


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN, Role.INTERVIEWER]))):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.patch("/{candidate_id}/status", response_model=CandidateRead)
async def update_candidate_status(candidate_id: str, update: dict, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    from app.features.candidates.models import Candidate
    raw_status = update["status"]
    # Try parsing as full backend enum first, then as simplified display status
    try:
        new_status = CandidateStatus(raw_status.upper())
    except ValueError:
        mapped = CandidateStatus.from_display_status(raw_status)
        if not mapped:
            raise HTTPException(status_code=422, detail=f"Invalid status: {raw_status}")
        new_status = mapped
    service = CandidateService(db)
    try:
        candidate = await service.update_status(candidate_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


async def _process_bulk_upload_csv(file: UploadFile | None) -> BulkUploadPreview:
    """Parse CSV upload file and return preview + validation results."""
    import csv
    import io
    import uuid

    if not file:
        return BulkUploadPreview(batch_id="", total_records=0, valid_records=0, invalid_records=0, preview=[], errors=[])

    content = await file.read()
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


@router.post("/bulk-upload/preview", response_model=BulkUploadPreview)
async def preview_bulk_upload(
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """Preview bulk upload — validate CSV and return preview without saving."""
    return await _process_bulk_upload_csv(file)


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_candidates(
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """Bulk upload candidates from CSV (preview + save)."""
    preview = await _process_bulk_upload_csv(file)
    # TODO: Save valid records to the database
    return preview
