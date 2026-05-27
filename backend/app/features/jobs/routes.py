"""Job management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user, AuthUser, HR_AND_ABOVE, require_role
from app.core.enums import Role

router = APIRouter()


class JobCreate(BaseModel):
    title: str
    job_description: str
    skillset: list[str]
    location: str = "Remote"
    experience_level: str = "Entry Level"
    openings: int = 1
    status: str = "OPEN"


class JobUpdate(BaseModel):
    title: str | None = None
    job_description: str | None = None
    skillset: list[str] | None = None
    location: str | None = None
    experience_level: str | None = None
    openings: int | None = None
    status: str | None = None


@router.post("/")
async def create_job(
    data: JobCreate,
    db: AsyncSession = Depends(get_db),
    hr_user: AuthUser = Depends(HR_AND_ABOVE),
):
    """Create a new job posting."""
    result = await db.execute(
        text("""
            INSERT INTO jobs (title, job_description, skillset, location, experience_level, openings, status, created_by, created_at, updated_at)
            VALUES (:title, :job_description, :skillset, :location, :experience_level, :openings, :status, :created_by, NOW(), NOW())
            RETURNING id, title, job_description, skillset, location, experience_level, openings, status, created_at
        """),
        {
            "title": data.title,
            "job_description": data.job_description,
            "skillset": data.skillset,
            "location": data.location,
            "experience_level": data.experience_level,
            "openings": data.openings,
            "status": data.status,
            "created_by": hr_user.id,
        },
    )
    await db.commit()
    row = result.fetchone()
    
    return {
        "id": str(row.id),
        "title": row.title,
        "job_description": row.job_description,
        "skillset": row.skillset,
        "location": row.location,
        "experience_level": row.experience_level,
        "openings": row.openings,
        "status": row.status,
        "created_at": str(row.created_at),
    }


@router.get("/")
async def list_jobs(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
):
    """List all job postings."""
    query = "SELECT id, title, job_description, skillset, location, experience_level, openings, status, created_at FROM jobs"
    params = {}
    
    if status:
        query += " WHERE status = :status"
        params["status"] = status
    
    query += " ORDER BY created_at DESC"
    
    result = await db.execute(text(query), params)
    rows = result.fetchall()
    
    return {
        "data": [
            {
                "id": str(row.id),
                "title": row.title,
                "job_description": row.job_description,
                "skillset": row.skillset,
                "location": row.location,
                "experience_level": row.experience_level,
                "openings": row.openings,
                "status": row.status,
                "created_at": str(row.created_at),
            }
            for row in rows
        ]
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUser = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
):
    """Get a single job by ID."""
    result = await db.execute(
        text("SELECT id, title, job_description, skillset, location, experience_level, openings, status, created_at FROM jobs WHERE id = :id"),
        {"id": job_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": str(row.id),
        "title": row.title,
        "job_description": row.job_description,
        "skillset": row.skillset,
        "location": row.location,
        "experience_level": row.experience_level,
        "openings": row.openings,
        "status": row.status,
        "created_at": str(row.created_at),
    }


@router.patch("/{job_id}")
async def update_job(
    job_id: str,
    data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    hr_user: AuthUser = Depends(HR_AND_ABOVE),
):
    """Update a job posting."""
    updates = []
    params = {"id": job_id}
    
    for field, value in data.dict(exclude_unset=True).items():
        updates.append(f"{field} = :{field}")
        params[field] = value
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = NOW()")
    
    await db.execute(
        text(f"UPDATE jobs SET {', '.join(updates)} WHERE id = :id"),
        params,
    )
    await db.commit()
    
    return {"message": "Job updated successfully"}


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    hr_user: AuthUser = Depends(HR_AND_ABOVE),
):
    """Delete a job posting."""
    await db.execute(text("DELETE FROM jobs WHERE id = :id"), {"id": job_id})
    await db.commit()
    
    return {"message": "Job deleted successfully"}