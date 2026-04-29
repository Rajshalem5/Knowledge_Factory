# app/services/auth_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from jose import jwt, JWTError

from app.models.user import User

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)


def create_user(
    db: Session,
    data,
    role: str,
    created_by=None
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
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
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=role,
        status="ACTIVE",
        created_by=created_by
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": f"{role} registered successfully"
    }


def register_admin(
    db: Session,
    data,
    current_user
):
    return create_user(
        db=db,
        data=data,
        role="ADMIN",
        created_by=current_user.id
    )


def register_hr(
    db: Session,
    data,
    current_user
):
    return create_user(
        db=db,
        data=data,
        role="HR",
        created_by=current_user.id
    )


def register_candidate(
    db: Session,
    data
):
    return create_user(
        db=db,
        data=data,
        role="CANDIDATE"
    )


def login_user(
    db: Session,
    data
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Account inactive"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "sub": user.email,
        "role": user.role,
        "user_id": str(user.id)
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


def request_password_reset(
    db: Session,
    email: str
):
    user = db.query(User).filter(
        User.email == email
    ).first()

    return {
        "message": "If email exists, reset link sent"
    }


def reset_password(
    db: Session,
    data
):
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    try:
        payload = jwt.decode(
            data.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        email = payload.get("sub")

    except JWTError:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.password_hash = hash_password(
        data.new_password
    )

    db.commit()

    return {
        "message": "Password reset successful"
    }