# app/schemas/job.py

from pydantic import BaseModel
from typing import List, Optional


class JobCreate(BaseModel):
    job_id: str
    title: str
    job_description: str
    skillset: List[str]
    openings: Optional[int] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    job_id: str
    title: str
    job_description: str
    skillset: List[str]
    status: str
