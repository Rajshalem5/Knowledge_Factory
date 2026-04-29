# app/routes/candidate.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_roles

from app.models.applicant_status import ApplicantStatus


router = APIRouter()


@router.get("/list")
def list_candidates(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "SUPERADMIN",
            "ADMIN",
            "HR"
        )
    )
):
    data = db.query(
        ApplicantStatus
    ).all()

    return {
        "count": len(data),
        "candidates": data
    }
