from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth import get_current_user
from app.services.parser import extract_text_from_file
from app.models.resume import Resume
from app.models.candidate import Candidate

import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/msword"  # doc
]


@router.post("/upload")
async def upload_resume(
    candidate_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    logger.info("Resume upload request received")

    # 🔹 Validate candidate exists and belongs to current tenant
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.tenant_id == current_user.tenant_id
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 🔹 Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, DOC allowed")

    contents = await file.read()

    # 🔹 Validate file is not empty
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # 🔹 Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    try:
        # 🔥 Extract text
        text = extract_text_from_file(contents, file.filename)

        # 🔥 Store in DB
        resume = Resume(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            candidate_id=candidate_id,
            uploaded_by=current_user.id,
            raw_text=text,
            status="PARSED"
        )

        db.add(resume)
        db.commit()

        return {
            "success": True,
            "data": {
                "resume_id": resume.id,
                "message": "Resume uploaded and processed"
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="Internal server error")