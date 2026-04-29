# app/routes/submissions.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_roles

from app.schemas.submission import SubmissionCreate
from app.services.submission_service import create_submission


router = APIRouter()


@router.post("/submit")
def submit_answer(
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("CANDIDATE")
    )
):
    return create_submission(
        db,
        data,
        current_user
    )
