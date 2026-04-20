from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import register_user, login_user # type: ignore
from app.core.dependencies import get_db
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, data)

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, data)
@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role
    }