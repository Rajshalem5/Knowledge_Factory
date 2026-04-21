"""
Authentication schemas: Login, Register, Tokens.
"""

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserRead"


class TokenPayload(BaseModel):
    sub: str | None = None
    tenant_id: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CandidateRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    college: str
    branch: str
    cgpa: float = Field(..., ge=0, le=10)
    passed_out_year: int
    language_choice: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: str
    tenant_id: UUID | None = None

    class Config:
        from_attributes = True
