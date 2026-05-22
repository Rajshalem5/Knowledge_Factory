"""Candidate management routes."""

from datetime import date, datetime
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.features.auth.models import User
from app.features.candidates.schemas import CandidateRead, CandidateListResponse, CandidateStatusUpdate, BulkUploadPreview
from app.features.candidates.service import CandidateService
from app.core.enums import CandidateStatus, Role

logger = logging.getLogger(__name__)

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
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
):
    """List all candidates with extensive filtering and pagination."""
    logger.info(f"list_candidates called by {current_user.email} | page={page}, limit={limit}, search={search}")
    service = CandidateService(db)
    try:
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
        logger.info(f"Returning {len(candidates)} candidates out of {total} total")
        return {
            "data": candidates,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit else 1
            }
        }
    except Exception as e:
        logger.error(f"Error in list_candidates: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/me/resume")
async def upload_my_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Allow candidate to upload/update their own resume."""
    from app.features.candidates.models import Candidate
    import uuid
    import os

    # Resolve candidate
    stmt = select(Candidate).where(Candidate.id == current_user.id)
    res = await db.execute(stmt)
    candidate = res.scalar_one_or_none()

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # In a real app, save to S3. For local, we just update the URL.
    filename = f"resume_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
    candidate.resume_url = f"uploads/resumes/{filename}"
    
    await db.commit()
    return {"message": "Resume uploaded successfully", "resume_url": candidate.resume_url}


@router.get("/me", response_model=CandidateRead)
async def get_my_profile(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Get the authenticated candidate's own profile."""
    service = CandidateService(db)
    return await service.get_my_profile(current_user.id)


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN, Role.INTERVIEWER]))):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.patch("/{candidate_id}/status", response_model=CandidateRead)
async def update_candidate_status(candidate_id: str, update: CandidateStatusUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Update candidate status. Accepts both canonical enum values (SELECTED, ROUND1_PASSED) and display statuses (selected, round1)."""
    new_status = update.status
    logger.info(
        "[update_candidate_status] candidate_id=%s, incoming_status=%s, by=%s",
        candidate_id, new_status.value, current_user.email,
    )

    service = CandidateService(db)
    try:
        candidate = await service.update_status(candidate_id, new_status)
    except ValueError as e:
        logger.warning(
            "[update_candidate_status] Invalid transition: candidate_id=%s, error=%s",
            candidate_id, str(e),
        )
        raise HTTPException(status_code=422, detail=str(e))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


async def _safe_decode(content: bytes) -> str:
    """Attempt to decode bytes using multiple encodings."""
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to decode file content with supported encodings (utf-8, latin-1, etc.)")


async def _process_bulk_upload_file(file: UploadFile | None) -> BulkUploadPreview:
    """Parse upload file (CSV/XLSX/PDF) and return preview + validation results."""
    import csv
    import io
    import uuid
    import os
    from app.services.parser import extract_text_from_file
    from app.services.extractor import extract_candidate_info

    if not file:
        return BulkUploadPreview(batch_id="", total_records=0, valid_records=0, invalid_records=0, preview=[], errors=[])

    filename = file.filename or "unknown.csv"
    ext = os.path.splitext(filename)[1].lower()
    content = await file.read()
    batch_id = str(uuid.uuid4())[:8]
    
    logger.info(
        "[_process_bulk_upload_file] Incoming file | name=%s | ext=%s | type=%s | size=%d bytes", 
        filename, ext, file.content_type, len(content)
    )

    # Structured Data Path (CSV)
    if ext == ".csv":
        try:
            text = await _safe_decode(content)
            reader = csv.DictReader(io.StringIO(text))
            records = list(reader)
        except Exception as e:
            logger.error("[_process_bulk_upload_file] CSV decode error: %s", str(e))
            return BulkUploadPreview(
                batch_id=batch_id, total_records=0, valid_records=0, invalid_records=0, 
                preview=[], errors=[{"row": 0, "error": f"Failed to read CSV: {str(e)}"}]
            )

        preview = []
        errors = []
        for i, row in enumerate(records[:20]):  # Preview first 20
            try:
                # Basic validation
                email = row.get("email", "").strip()
                if not email or "@" not in email:
                    raise ValueError("Missing or invalid email")
                preview.append({"row": i + 1, "data": row, "valid": True})
            except (ValueError, KeyError) as e:
                errors.append({"row": i + 1, "error": str(e) or "Invalid data format"})
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

    # Document Path (PDF/DOCX) - Use AI Extraction
    elif ext in [".pdf", ".doc", ".docx"]:
        try:
            logger.info("[_process_bulk_upload_file] Extracting text from document...")
            raw_text = await extract_text_from_file(content, filename)
            
            logger.info("[_process_bulk_upload_file] Extracting entities via LLM...")
            extracted = await extract_candidate_info(raw_text)
            
            # Map extracted data to unified row format
            preview_data = {
                "name": extracted.get("name") or filename.replace(ext, "").title(),
                "email": extracted.get("email") or "",
                "phone": extracted.get("phone") or "",
                "degree": extracted.get("degree") or "Unknown",
                "branch": extracted.get("branch") or "Unknown",
                "college": extracted.get("college") or "Unknown",
                "cgpa": extracted.get("cgpa") or 0.0,
                "percentage": extracted.get("percentage"),
                "passed_out_year": extracted.get("graduation_year") or datetime.now().year,
                "academic_status": extracted.get("academic_status"),
                "skills": extracted.get("skills", []) if isinstance(extracted.get("skills"), list) else [],
                "experience_summary": extracted.get("experience_summary"),
                "type": "AI Extracted Resume",
                "is_ai_parsed": True
            }
            
            # Convert skills back to string if it was a list
            if isinstance(preview_data["skills"], list):
                preview_data["skills"] = ", ".join(preview_data["skills"])

            valid = bool(preview_data["email"] and "@" in preview_data["email"])
            
            return BulkUploadPreview(
                batch_id=batch_id,
                total_records=1,
                valid_records=1 if valid else 0,
                invalid_records=0 if valid else 1,
                preview=[{"row": 1, "data": preview_data, "valid": valid}],
                errors=[] if valid else [{"row": 1, "error": "Resume uploaded. AI could not reliably extract an email. Please enter manually."}],
            )
        except Exception as e:
            logger.warning(f"[_process_bulk_upload_file] Text extraction failed, falling back to manual entry: {e}")
            # Even if parsing fails, we want to allow them to create a placeholder
            placeholder_data = {
                "name": filename.replace(ext, "").title(),
                "email": "",
                "type": "Manual Entry (Parsing Failed)",
                "is_ai_parsed": True # keep it true so frontend shows the edit form
            }
            return BulkUploadPreview(
                batch_id=batch_id,
                total_records=1,
                valid_records=0,
                invalid_records=1,
                preview=[{"row": 1, "data": placeholder_data, "valid": False}],
                errors=[{"row": 1, "error": f"Extraction failed: {str(e)}. Document stored, please fill details manually."}]
            )

    # Unsupported Path
    else:
        logger.warning("[_process_bulk_upload_file] Unsupported file type: %s", ext)
        return BulkUploadPreview(
            batch_id=batch_id, total_records=0, valid_records=0, invalid_records=0,
            preview=[], errors=[{"row": 0, "error": f"Unsupported file type: {ext}. Please use CSV, PDF, or DOCX."}]
        )


@router.post("/bulk-upload/preview", response_model=BulkUploadPreview)
async def preview_bulk_upload(
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
):
    """Preview bulk upload — support multiple formats without crashing."""
    return await _process_bulk_upload_file(file)


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_candidates(
    file: UploadFile | None = File(None),
    data: str | None = Form(None), # Optional JSON from frontend
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
):
    """Bulk upload candidates — handles multiple formats safely."""
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle
    import csv
    import io
    import uuid
    import os
    import json

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = file.filename or "unknown.csv"
    ext = os.path.splitext(filename)[1].lower()
    content = await file.read()

    # Get active hiring cycle
    cycle_stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE").limit(1)
    cycle_res = await db.execute(cycle_stmt)
    cycle = cycle_res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(status_code=500, detail="No active hiring cycle found")

    saved = 0
    errors = []
    total_records = 0

    # CSV Processing
    if ext == ".csv":
        try:
            text = await _safe_decode(content)
            reader = csv.DictReader(io.StringIO(text))
            records = list(reader)
            total_records = len(records)
            
            for i, row in enumerate(records):
                try:
                    candidate = Candidate(
                        cycle_id=cycle.id,
                        email=row.get("email", "").strip(),
                        name=row.get("name", "").strip() or "Unnamed Candidate",
                        college=row.get("college", "").strip() or "Unknown",
                        branch=row.get("branch", "").strip() or "Unknown",
                        cgpa=float(row.get("cgpa", 0)),
                        passed_out_year=int(row.get("passed_out_year", datetime.now().year)),
                        language_choice=row.get("language_choice", "python").strip().lower(),
                        status=CandidateStatus.APPLIED,
                        phone=row.get("phone", "").strip() or None,
                    )
                    db.add(candidate)
                    saved += 1
                except Exception as e:
                    errors.append({"row": i + 2, "error": str(e)})
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

    # Document Processing (PDF/DOCX)
    elif ext in [".pdf", ".doc", ".docx"]:
        total_records = 1
        try:
            from app.services.parser import extract_text_from_file
            from app.services.extractor import extract_candidate_info

            logger.info("[bulk_upload_candidates] Processing document: %s", filename)
            
            extracted = {}
            if data:
                try:
                    extracted = json.loads(data)
                    logger.info("[bulk_upload_candidates] Using provided data for candidate creation")
                except Exception:
                    logger.warning("[bulk_upload_candidates] Failed to parse provided data JSON, falling back to AI")

            if not extracted:
                raw_text = await extract_text_from_file(content, filename)
                extracted = await extract_candidate_info(raw_text)

            candidate = Candidate(
                cycle_id=cycle.id,
                email=extracted.get("email") or f"upload_{uuid.uuid4().hex[:6]}@example.com",
                name=extracted.get("name") or filename.replace(ext, "").title(),
                degree=extracted.get("degree") or "Unknown",
                branch=extracted.get("branch") or "Unknown",
                college=extracted.get("college") or "Unknown",
                cgpa=float(extracted.get("cgpa") or 0.0),
                passed_out_year=int(extracted.get("passed_out_year") or datetime.now().year),
                skills=extracted.get("skills") if isinstance(extracted.get("skills"), str) else ", ".join(extracted.get("skills", [])),
                language_choice="python",
                status=CandidateStatus.APPLIED,
                phone=extracted.get("phone"),
                resume_url=f"uploads/resumes/{filename}",
                custom_fields={
                    "percentage": extracted.get("percentage"),
                    "academic_status": extracted.get("academic_status"),
                    "experience_summary": extracted.get("experience_summary"),
                }
            )
            db.add(candidate)
            saved += 1
            
            # Save file to disk
            upload_dir = "uploads/resumes"
            os.makedirs(upload_dir, exist_ok=True)
            with open(os.path.join(upload_dir, filename), "wb") as f:
                f.write(content)

            logger.info("[bulk_upload_candidates] Successfully created candidate from document: %s", filename)
        except Exception as e:
            logger.error("[bulk_upload_candidates] Document processing error: %s", e)
            errors.append({"row": 1, "error": str(e)})

    # Unsupported / Placeholder for XLSX
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Automated processing for {ext} files is not yet implemented. Please use CSV."
        )

    if saved > 0:
        await db.commit()

    return {
        "batch_id": str(uuid.uuid4())[:8],
        "total_records": total_records,
        "saved": saved,
        "errors": errors,
    }
