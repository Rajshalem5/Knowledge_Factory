"""Authentication schemas - simplified without multi-tenancy."""

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, model_validator


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenPayload(BaseModel):
    sub: str | None = None
    email: str | None = None
    role: str | None = None
    type: str | None = None  # For refresh tokens


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class CandidateRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    college: str
    branch: str
    cgpa: float = Field(..., ge=0, le=10)
    passed_out_year: int
    language_choice: str = "english"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: str

    class Config:
        from_attributes = True
