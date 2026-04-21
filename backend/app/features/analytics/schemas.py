"""
Analytics and Selection schemas.
"""

from uuid import UUID
from typing import Any
from pydantic import BaseModel


class FunnelStage(BaseModel):
    status: str
    count: int


class FunnelResponse(BaseModel):
    stages: list[FunnelStage]
    total_applicants: int


class InterviewAssignment(BaseModel):
    candidate_id: UUID
    interviewer_id: UUID
    round: str
