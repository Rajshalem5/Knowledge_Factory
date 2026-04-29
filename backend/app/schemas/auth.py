# app/schemas/auth.py

from pydantic import BaseModel, EmailStr


class ProfileRequest(BaseModel):
    email: EmailStr
    full_name: str













