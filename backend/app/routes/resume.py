from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.services.parser import extract_text_from_file
from app.models.resume import Resume


router = APIRouter()


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("CANDIDATE")
    )
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid file"
        )

    file_bytes = await file.read()

    raw_text = extract_text_from_file(
        file_bytes,
        file.filename
    )

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        uploaded_by=current_user.id,
        raw_text=raw_text,
        status="PARSED"
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume uploaded successfully",
        "resume_id": resume.id
    }
