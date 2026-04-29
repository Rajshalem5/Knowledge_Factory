from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.get("/me")
def get_me(
    current_user=Depends(get_current_user)
):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name
    }