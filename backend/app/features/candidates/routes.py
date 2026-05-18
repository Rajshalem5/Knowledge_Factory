"""Candidate management routes — includes assessment results for HR."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

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
    has_interview_feedback: bool | None = Query(None, description="Filter by whether candidate has interview feedback"),
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
        has_interview_feedback=has_interview_feedback,
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

    # Prevent direct status update to SELECTED/FINAL_REJECTED — must use /selection endpoint
    if raw_status.upper() in ("SELECTED", "FINAL_REJECTED"):
        raise HTTPException(
            status_code=422,
            detail="Use the /api/selection endpoints for selection/rejection decisions",
        )

    # Try parsing as full backend enum first, then as simplified display status
    try:
        new_status = CandidateStatus(raw_status.upper())
    except ValueError:
        mapped = CandidateStatus.from_display_status(raw_status)
        if not mapped:
            raise HTTPException(status_code=422, detail=f"Invalid status: {raw_status}")
        new_status = mapped

    # Validate FSM transition
    allowed_direct = {
        CandidateStatus.ROUND1_PASSED, CandidateStatus.ROUND1_REJECTED,
        CandidateStatus.ROUND2_IN_PROGRESS, CandidateStatus.ROUND2_PASSED,
        CandidateStatus.ROUND2_REJECTED, CandidateStatus.ROUND3_IN_PROGRESS,
        CandidateStatus.ROUND3_PASSED, CandidateStatus.ROUND3_REJECTED,
        CandidateStatus.INTERVIEW_SCHEDULED, CandidateStatus.INTERVIEW_COMPLETED,
    }
    if new_status not in allowed_direct:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot manually set status to {new_status.value}. Use proper pipeline endpoints.",
        )

    service = CandidateService(db)
    try:
        candidate = await service.update_status(candidate_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.get("/{candidate_id}/assessments")
async def get_candidate_assessments(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """Get all assessment submissions and scores for a candidate — HR view."""
    from app.features.assessments.models import Assessment, Submission, Score

    # Get all assessments for this candidate
    stmt = (
        select(Assessment)
        .where(Assessment.candidate_id == candidate_id)
        .order_by(Assessment.created_at.desc())
    )
    res = await db.execute(stmt)
    assessments = res.scalars().all()

    result = []
    for a in assessments:
        # Get submissions for this assessment
        sub_stmt = select(Submission).where(Submission.assessment_id == a.id)
        sub_res = await db.execute(sub_stmt)
        submissions = sub_res.scalars().all()

        # Get scores for this candidate/round
        score_stmt = select(Score).where(
            Score.candidate_id == candidate_id,
            Score.round == a.round,
        )
        score_res = await db.execute(score_stmt)
        scores = score_res.scalars().all()

        result.append({
            "assessment_id": a.id,
            "round": a.round.value if hasattr(a.round, "value") else a.round,
            "status": a.status.value if hasattr(a.status, "value") else a.status,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "ended_at": a.ended_at.isoformat() if a.ended_at else None,
            "time_limit": a.time_limit,
            "submissions": [
                {
                    "id": s.id,
                    "section": s.section.value if hasattr(s.section, "value") else s.section,
                    "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                    "code_snippet": (s.payload_json or {}).get("code", "")[:500] if s.payload_json else "",
                }
                for s in submissions
            ],
            "scores": [
                {
                    "id": sc.id,
                    "correctness": sc.correctness,
                    "quality": sc.quality,
                    "design": sc.design,
                    "weighted_total": float(sc.weighted_total),
                    "verdict": sc.verdict.value if hasattr(sc.verdict, "value") else sc.verdict,
                    "evaluated_at": sc.evaluated_at.isoformat() if sc.evaluated_at else None,
                }
                for sc in scores
            ],
        })

    return {"data": result}


async def _process_bulk_upload_csv(file: UploadFile | None) -> BulkUploadPreview:
    """Parse CSV upload file and return preview + validation results."""
    import csv
    import io
    import uuid

    if not file:
        return BulkUploadPreview(batch_id="", total_records=0, valid_records=0, invalid_records=0, preview=[], errors=[])

    content = await file.read()

    # Validate: size, magic bytes, UTF-8 decode
    from app.core.file_validation import validate_upload, FileValidationError
    try:
        validate_upload(
            file.filename or "upload.csv",
            content,
            allow_text=True,      # CSV is plain text
        )
    except FileValidationError as e:
        return BulkUploadPreview(
            batch_id="", total_records=0, valid_records=0, invalid_records=0,
            preview=[], errors=[{"row": 0, "error": str(e)}],
        )

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


# ── Bulk upload chunking ──────────────────────────────────────
BULK_UPLOAD_CHUNK_SIZE = 100


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_candidates(
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """Bulk upload candidates from CSV — validates, chunks, inserts."""
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle
    import csv
    import io
    import uuid

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()

    # Validate: size, magic bytes, UTF-8 decode
    from app.core.file_validation import validate_upload, FileValidationError
    try:
        validate_upload(
            file.filename or "upload.csv",
            content,
            allow_text=True,
        )
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    records = list(reader)

    if not records:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Get active hiring cycle
    cycle_stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE").limit(1)
    cycle_res = await db.execute(cycle_stmt)
    cycle = cycle_res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(status_code=500, detail="No active hiring cycle")

    # ── Step 1: Pre-validate & build candidate objects ────────────
    all_rows = []
    errors = []
    from app.core.security import hash_password
    for i, row in enumerate(records):
        try:
            email = row.get("email", "").strip()
            if not email:
                raise ValueError("Email is required")
            # Generate temp password hash — candidate must use forgot-password flow
            temp_hash = hash_password(str(uuid.uuid4()))
            candidate = Candidate(
                cycle_id=cycle.id,
                email=email,
                password_hash=temp_hash,
                name=row.get("name", "").strip(),
                college=row.get("college", "").strip(),
                branch=row.get("branch", "").strip(),
                cgpa=float(row.get("cgpa", 0)),
                passed_out_year=int(row.get("passed_out_year", datetime.now().year)),
                language_choice=row.get("language_choice", "python").strip().lower(),
                status=CandidateStatus.APPLIED,
                phone=row.get("phone", "").strip() or None,
            )
            all_rows.append(candidate)
        except (ValueError, KeyError) as e:
            errors.append({"row": i + 2, "error": str(e)})

    if not all_rows:
        return {
            "batch_id": str(uuid.uuid4())[:8],
            "total_records": len(records),
            "saved": 0,
            "errors": errors,
        }

    # ── Step 2: Bulk-check existing emails ────────────────────────
    new_emails = {c.email for c in all_rows}
    existing = set()
    for chunk_start in range(0, len(new_emails), 500):
        email_chunk = list(new_emails)[chunk_start:chunk_start + 500]
        stmt = select(Candidate.email).where(Candidate.email.in_(email_chunk))
        res = await db.execute(stmt)
        existing.update(row[0] for row in res.fetchall())

    dupes_skipped = 0
    valid_rows = []
    for c in all_rows:
        if c.email in existing:
            dupes_skipped += 1
            continue
        valid_rows.append(c)
        existing.add(c.email)  # prevent intra-batch duplicates

    # ── Step 3: Chunked insert ────────────────────────────────────
    saved = 0
    for chunk_start in range(0, len(valid_rows), BULK_UPLOAD_CHUNK_SIZE):
        chunk = valid_rows[chunk_start:chunk_start + BULK_UPLOAD_CHUNK_SIZE]
        try:
            db.add_all(chunk)
            await db.commit()
            saved += len(chunk)
        except Exception as e:
            await db.rollback()
            errors.append({
                "row": f"chunk-{chunk_start // BULK_UPLOAD_CHUNK_SIZE + 1}",
                "error": f"Chunk insert failed: {str(e)}",
            })

    return {
        "batch_id": str(uuid.uuid4())[:8],
        "total_records": len(records),
        "saved": saved,
        "errors": errors,
    }
