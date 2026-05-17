"""Code execution routes — restricted to CANDIDATE role."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import CANDIDATE_ONLY
from app.features.code_execution.schemas import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    EvaluationRequest,
    EvaluationResult,
)
from app.features.code_execution.service import PistonExecutionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    current_user=Depends(CANDIDATE_ONLY),
):
    """Run code with custom stdin — used by the Run button."""
    service = PistonExecutionService()
    result = await service.execute_code(
        language=request.language,
        code=request.code,
        stdin=request.stdin or "",
    )
    logger.info("Execute: lang=%s stdin=%r status=%s stdout=%r stderr=%r",
                request.language, request.stdin, result.status, result.stdout, result.stderr)
    return result


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_code(
    request: EvaluationRequest,
    current_user=Depends(CANDIDATE_ONLY),
):
    """
    Evaluate code against test cases supplied in the request.
    For full scoring (public + private), use /evaluate-question/{question_id}.
    """
    service = PistonExecutionService()
    return await service.evaluate_code(
        language=request.language,
        code=request.code,
        test_cases=request.test_cases,
    )


@router.post("/evaluate-question/{question_id}", response_model=EvaluationResult)
async def evaluate_against_question(
    question_id: str,
    request: CodeExecutionRequest,
    current_user=Depends(CANDIDATE_ONLY),
):
    """
    Evaluate code against ALL test cases (public + private) for a question.
    Private test cases are never sent to the frontend — only the score is returned.
    """
    from app.features.questions.routes import get_full_question
    from app.features.code_execution.schemas import TestCase

    question = get_full_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    all_cases = [
        TestCase(input=tc.input, expected_output=tc.expected_output)
        for tc in question.public_test_cases + question.private_test_cases
    ]

    service = PistonExecutionService()
    return await service.evaluate_code(
        language=request.language,
        code=request.code,
        test_cases=all_cases,
    )
