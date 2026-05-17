"""Question generation routes — restricted to CANDIDATE role."""

from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import CANDIDATE_ONLY
from app.features.questions.schemas import (
    QuestionGenerationRequest,
    QuestionPublicView,
    Question,
)
from app.features.questions.ai_service import generate_question

router = APIRouter()

# In-memory store for generated questions (keyed by question id)
# In production this would be a DB table
_question_store: dict[str, Question] = {}


@router.post("/generate", response_model=QuestionPublicView)
async def generate(
    req: QuestionGenerationRequest,
    current_user=Depends(CANDIDATE_ONLY),
):
    """
    Generate a question via AI.
    Returns only public test cases to the frontend.
    Private test cases are stored server-side for evaluation.
    """
    try:
        question = await generate_question(
            topic=req.topic,
            difficulty=req.difficulty,
            num_public=req.num_public_cases,
            num_private=req.num_private_cases,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    # Store full question (with private cases) server-side
    _question_store[question.id] = question

    # Return only public view to frontend
    return QuestionPublicView(
        id=question.id,
        title=question.title,
        description=question.description,
        difficulty=question.difficulty,
        boilerplate=question.boilerplate,
        public_test_cases=question.public_test_cases,
    )


@router.get("/{question_id}/public", response_model=QuestionPublicView)
async def get_question_public(
    question_id: str,
    current_user=Depends(CANDIDATE_ONLY),
):
    """Get public view of a question (no private test cases)."""
    q = _question_store.get(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    return QuestionPublicView(
        id=q.id,
        title=q.title,
        description=q.description,
        difficulty=q.difficulty,
        boilerplate=q.boilerplate,
        public_test_cases=q.public_test_cases,
    )


def get_full_question(question_id: str) -> Question | None:
    """Internal helper — used by evaluation to get private test cases."""
    return _question_store.get(question_id)
