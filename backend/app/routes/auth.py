from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.schemas.auth import ProfileRequest

from app.services.auth_service import (
    register_admin_profile,
    register_hr_profile,
    register_candidate_profile
)

router = APIRouter()


@router.post("/admin/register")
def create_admin(
    data: ProfileRequest,
    supabase_user_id: str = Query(..., description="Supabase user.id (UUID) from frontend signup"),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SUPERADMIN"))
):
    return register_admin_profile(
        db,
        data,
        supabase_user_id,
        current_user
    )


@router.post("/hr/register")
def create_hr(
    data: ProfileRequest,
    supabase_user_id: str = Query(..., description="Supabase user.id (UUID) from frontend signup"),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "SUPERADMIN",
            "ADMIN"
        )
    )
):
    return register_hr_profile(
        db,
        data,
        supabase_user_id,
        current_user
    )


@router.post("/candidate/register")
def create_candidate(
    data: ProfileRequest,
    supabase_user_id: str = Query(..., description="Supabase user.id (UUID) from frontend signup"),
    db: Session = Depends(get_db)
):
    return register_candidate_profile(
        db,
        data,
        supabase_user_id
    )


@router.post("/login")
def login():
    raise HTTPException(
        status_code=410,
        detail="Local login deprecated. Use Supabase Auth client for login/signup/reset."
    )


@router.post("/forgot-password")
def forgot_password():
    raise HTTPException(
        status_code=410,
        detail="Local password reset deprecated. Use Supabase Auth."
    )


@router.post("/reset-password")
def change_password():
    raise HTTPException(
        status_code=410,
        detail="Local password reset deprecated. Use Supabase Auth."
    )
@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name
    }

