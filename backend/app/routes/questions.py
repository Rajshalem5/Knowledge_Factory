# app/routes/questions.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_roles

from app.schemas.question import QuestionCreate
from app.services.question_service import (
    create_question,
    get_all_questions
)


router = APIRouter()


@router.post("/create")
def create_new_question(
    data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "SUPERADMIN",
            "ADMIN",
            "HR"
        )
    )
):
    return create_question(
        db,
        data,
        current_user
    )


@router.get("/list")
def list_questions(
    db: Session = Depends(get_db)
):
    return get_all_questions(db)
