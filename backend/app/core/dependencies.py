from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from supabase import create_client #type: ignore

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User

security = HTTPBearer()

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        auth_user = response.user

        if not auth_user:
            raise Exception()

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.id == auth_user.id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    return user