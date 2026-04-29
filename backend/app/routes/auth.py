# app/routes/auth.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_roles

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)

from app.services.auth_service import (
    register_admin,
    register_hr,
    register_candidate,
    login_user,
    request_password_reset,
    reset_password
)


router = APIRouter()


@router.post("/admin/register")
def create_admin(
    data: RegisterRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SUPERADMIN"))
):
    return register_admin(
        db,
        data,
        current_user
    )


@router.post("/hr/register")
def create_hr(
    data: RegisterRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "SUPERADMIN",
            "ADMIN"
        )
    )
):
    return register_hr(
        db,
        data,
        current_user
    )


@router.post("/candidate/register")
def create_candidate(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    return register_candidate(
        db,
        data
    )


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(
        db,
        data
    )


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    return request_password_reset(
        db,
        data.email
    )


@router.post("/reset-password")
def change_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    return reset_password(
        db,
        data
    )
