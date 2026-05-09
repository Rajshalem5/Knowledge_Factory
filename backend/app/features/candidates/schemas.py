"""
Candidate schemas: Lists, Details, Updates.
"""

from uuid import UUID
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal

from app.core.enums import CandidateStatus


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    college: str
    branch: str
    cgpa: Decimal
    passed_out_year: int
    language_choice: str


class CandidateRead(CandidateBase):
    id: UUID
    status: CandidateStatus
    display_status: str = ""
    created_at: datetime
    cycle_id: UUID

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_compat(cls, candidate) -> "CandidateRead":
        """Build a CandidateRead from an ORM model, computing display_status."""
        status_val = CandidateStatus(candidate.status) if isinstance(candidate.status, str) else candidate.status
        return cls(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            college=candidate.college,
            branch=candidate.branch,
            cgpa=candidate.cgpa,
            passed_out_year=candidate.passed_out_year,
            language_choice=candidate.language_choice,
            status=status_val,
            display_status=status_val.display_status,
            created_at=candidate.created_at,
            cycle_id=candidate.cycle_id,
        )


class CandidateListResponse(BaseModel):
    data: list[CandidateRead]
    pagination: dict[str, Any]


class CandidateStatusUpdate(BaseModel):
    status: CandidateStatus


class BulkUploadPreview(BaseModel):
    batch_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    preview: list[dict]
    errors: list[dict]
