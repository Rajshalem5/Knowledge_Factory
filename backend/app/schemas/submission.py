# app/schemas/submission.py

from pydantic import BaseModel
from typing import Optional, Dict, Any


class SubmissionCreate(BaseModel):
    qid: str
    language: str
    code: Optional[str] = None
    mcq_answers: Optional[Dict[str, Any]] = None
    time_spent: int


class SubmissionResponse(BaseModel):
    id: str
    submission_id: str
    qid: str
    candidate_id: str
    created_at: str
