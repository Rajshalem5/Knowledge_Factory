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
    created_at: datetime
    cycle_id: UUID

    class Config:
        from_attributes = True


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
