from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.core.enums import Role, UserStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Role
    status: UserStatus = UserStatus.ACTIVE

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Role] = None
    status: Optional[UserStatus] = None

class PasswordReset(BaseModel):
    new_password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    status: UserStatus
    created_at: str

    class Config:
        from_attributes = True

class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

class UserListResponse(BaseModel):
    data: List[UserResponse]
    pagination: PaginationInfo
