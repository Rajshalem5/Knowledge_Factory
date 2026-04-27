"""Authentication schemas: Login, Register, Tokens, OTP."""

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserRead"


class TokenPayload(BaseModel):
    sub: str | None = None
    tenant_id: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserRead"


class RefreshRequest(BaseModel):
    refresh_token: str


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)


class CandidateRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    college: str
    branch: str
    cgpa: float = Field(..., ge=0, le=10)
    passed_out_year: int
    language_choice: str = "english"


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: str
    tenant_id: UUID | None = None

    class Config:
        from_attributes = True
