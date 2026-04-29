from sqlalchemy.orm import Session
from app.models.job import Job


def create_job(db: Session, data, current_user):
    job = Job(
        job_id=data.job_id,
        title=data.title,
        job_description=data.job_description,
        skillset=data.skillset,
        openings=data.openings,
        experience_level=data.experience_level,
        location=data.location,
        status="DRAFT",
        created_by=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_all_jobs(db: Session):
    return db.query(Job).all()