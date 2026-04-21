from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_roles

from app.models.candidate import Candidate
from app.models.resume import Resume

router = APIRouter()


@router.get("/list")
def get_candidates(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("ADMIN", "HR"))
):
    candidates = db.query(Candidate).filter(
        Candidate.tenant_id == current_user.tenant_id
    ).all()

    result = []

    for c in candidates:
        resume = db.query(Resume).filter(
            Resume.candidate_id == c.id,
            Resume.tenant_id == current_user.tenant_id
        ).first()

        result.append({
            "candidate_id": c.id,
            "name": c.name,
            "email": c.email,
            "status": c.status,

            "has_resume": bool(resume),
            "resume_status": resume.status if resume else None
        })

    return {
        "success": True,
        "data": {
            "count": len(result),
            "candidates": result
        }
    }