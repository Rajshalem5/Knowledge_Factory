from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import hash_password


# 🔹 COMMON USER CREATION FUNCTION
def create_user(db: Session, data, role: str):
    existing = db.query(User).filter(User.email == data.email).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role=role,
        status="ACTIVE"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": f"{role} registered successfully"}


# 🔹 ADMIN REGISTER
def register_admin(db: Session, data):
    return create_user(db, data, "ADMIN")


# 🔹 HR REGISTER
def register_hr(db: Session, data):
    return create_user(db, data, "HR")


# 🔹 CANDIDATE REGISTER
def register_candidate(db: Session, data):
    return create_user(db, data, "CANDIDATE")


# 🔹 LOGIN
def login_user(db: Session, data):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.email,
        "role": user.role   # 🔥 important for RBAC
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def request_password_reset(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()

    # 🔒 Don't reveal if email exists
    if not user:
        return {"message": "If email exists, reset link sent"}

    reset_token = create_access_token({
        "sub": user.email,
        "type": "password_reset"
    })

    return {
        "message": "Reset token generated",
        "reset_token": reset_token
    }


def reset_password(db: Session, data):
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        payload = jwt.decode(
            data.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        email = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(data.new_password)
    db.commit()

    return {"message": "Password reset successful"}