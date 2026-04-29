from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.models.user import User
from app.schemas.auth import ProfileRequest

def get_user_profile(db: Session, supabase_user_id: str) -> User:
    '''Fetch local profile by Supabase user ID.'''
    user = db.query(User).filter(
        User.id == supabase_user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )
    return user


def create_profile(
    db: Session,
    data: ProfileRequest,
    role: str,
    supabase_user_id: str,
    created_by=None
):
    '''Create local profile after Supabase signup. ID must match Supabase user.id (UUID str).'''
    # Check if profile exists
    existing_user = db.query(User).filter(
        User.id == supabase_user_id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists"
        )

    if role == "SUPERADMIN":
        existing_superadmin = db.query(User).filter(
            User.role == "SUPERADMIN"
        ).first()
        if existing_superadmin:
            raise HTTPException(
                status_code=400,
                detail="SuperAdmin already exists"
            )

    user = User(
        id=UUID(supabase_user_id),
        email=data.email,
        password_hash=None,
        full_name=data.full_name,
        role=role,
        status="ACTIVE",
        created_by=created_by
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": f"{role} profile created successfully"
    }


def register_admin_profile(
    db: Session,
    data: ProfileRequest,
    supabase_user_id: str,
    current_user
):
    return create_profile(
        db=db,
        data=data,
        role="ADMIN",
        supabase_user_id=supabase_user_id,
        created_by=current_user.id
    )


def register_hr_profile(
    db: Session,
    data: ProfileRequest,
    supabase_user_id: str,
    current_user
):
    return create_profile(
        db=db,
        data=data,
        role="HR",
        supabase_user_id=supabase_user_id,
        created_by=current_user.id
    )


def register_candidate_profile(
    db: Session,
    data: ProfileRequest,
    supabase_user_id: str
):
    return create_profile(
        db=db,
        data=data,
        role="CANDIDATE",
        supabase_user_id=supabase_user_id
    )

