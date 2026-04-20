from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import request_password_reset, reset_password
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import (
    register_admin,
    register_hr,
    register_candidate,
    login_user
)
from app.core.dependencies import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles

router = APIRouter()


# 🔹 ADMIN REGISTER (only ADMIN / SUPERADMIN)
@router.post("/admin/register")
def register_admin_route(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    return register_admin(db, data)


# 🔹 HR REGISTER (only ADMIN)
@router.post("/hr/register")
def register_hr_route(
    data: RegisterRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("ADMIN"))
):
    return register_hr(db, data)


# 🔹 CANDIDATE REGISTER (public)
@router.post("/candidate/register")
def register_candidate_route(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    return register_candidate(db, data)


# 🔹 LOGIN (common)
@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(db, data)


# 🔹 GET CURRENT USER
@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role
    }

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    return request_password_reset(db, data.email)


@router.post("/reset-password")
def reset_password_route(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    return reset_password(db, data)