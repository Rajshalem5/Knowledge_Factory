# app/routes/jobs.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_roles

from app.schemas.job import JobCreate
from app.services.job_service import (
    create_job,
    get_all_jobs
)


router = APIRouter()


@router.post("/create")
def create_new_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "SUPERADMIN",
            "ADMIN",
            "HR"
        )
    )
):
    return create_job(
        db,
        data,
        current_user
    )


@router.get("/list")
def list_jobs(
    db: Session = Depends(get_db)
):
    return get_all_jobs(db)
