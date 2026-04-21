from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict

from ...core.database import get_db
from ...core.config import settings
from ...models.assessment import Assessment, Submission, Score, AssessmentStatus
from ...schemas.assessment import (
    AssessmentStartResponse,
    AssessmentQuestionsResponse,
    MonacoCodingProblem,
    MonacoMCQ,
    AssessmentSubmitRequest,
    AssessmentResultResponse
)
from ...services.question_bank import QuestionBank
from ...services.evaluation_service import get_evaluator

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate and start unique assessment for candidate
    
    - Generates unique test using candidate_id as seed
    - Stores questions in database
    - Returns assessment_id and metadata
    """
    # Check if assessment already exists
    existing = db.query(Assessment).filter(
        Assessment.candidate_id == candidate_id
    ).first()
    
    if existing:
        if existing.status == AssessmentStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment already submitted"
            )
        # Return existing assessment
        return AssessmentStartResponse(
            assessment_id=existing.id,
            candidate_id=existing.candidate_id,
            duration_minutes=settings.ASSESSMENT_DURATION_MINUTES,
            started_at=existing.started_at
        )
    
    # Generate unique questions
    questions = QuestionBank.generate_assessment(candidate_id)
    
    # Create assessment
    assessment = Assessment(
        candidate_id=candidate_id,
        questions_json=questions,
        status=AssessmentStatus.IN_PROGRESS
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return AssessmentStartResponse(
        assessment_id=assessment.id,
        candidate_id=assessment.candidate_id,
        duration_minutes=settings.ASSESSMENT_DURATION_MINUTES,
        started_at=assessment.started_at
    )


@router.get("/{assessment_id}/questions", response_model=AssessmentQuestionsResponse)
async def get_assessment_questions(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Monaco-compatible questions for assessment
    
    - Returns coding problems with boilerplate
    - Returns MCQs without correct answers
    - Does NOT expose hidden test cases
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    if assessment.status == AssessmentStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already submitted"
        )
    
    questions = assessment.questions_json
    
    # Format for Monaco editor
    coding_problems = []
    for problem in questions["coding"]:
        coding_problems.append(MonacoCodingProblem(
            id=problem["id"],
            title=problem["title"],
            description=problem["description"],
            boilerplate=problem["boilerplate"]["python"],  # Default to Python
            visible_test_cases=problem["visible_test_cases"],
            default_language="python"
        ))
    
    mcq_questions = []
    for mcq in questions["mcq"]:
        mcq_questions.append(MonacoMCQ(
            id=mcq["id"],
            question=mcq["question"],
            options=mcq["options"]
        ))
    
    return AssessmentQuestionsResponse(
        coding=coding_problems,
        mcq=mcq_questions
    )


@router.post("/submit")
async def submit_assessment(
    assessment_id: int,
    submission: AssessmentSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submit assessment and trigger evaluation
    
    - Saves submission
    - Locks assessment
    - Runs synchronous evaluation
    - Returns evaluation results
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    if assessment.status == AssessmentStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already submitted"
        )
    
    # Save submission
    submission_record = Submission(
        assessment_id=assessment_id,
        payload_json={
            "coding": [s.dict() for s in submission.coding],
            "mcq_answers": submission.mcq_answers
        }
    )
    db.add(submission_record)
    
    # Lock assessment
    assessment.status = AssessmentStatus.SUBMITTED
    assessment.ended_at = datetime.utcnow()
    
    db.commit()
    
    # Trigger evaluation
    evaluator = get_evaluator("phase1")
    result = await evaluator.evaluate(
        coding_submissions=[s.dict() for s in submission.coding],
        mcq_answers=submission.mcq_answers,
        questions=assessment.questions_json
    )
    
    # Save score
    score = Score(
        candidate_id=assessment.candidate_id,
        assessment_id=assessment_id,
        correctness=int(result.correctness),
        mcq_total=result.mcq_score,
        weighted_total=int(result.weighted_total),
        verdict=result.verdict,
        evaluation_details=result.details
    )
    db.add(score)
    
    assessment.status = AssessmentStatus.EVALUATED
    db.commit()
    
    return {
        "message": "Assessment submitted successfully",
        "assessment_id": assessment_id,
        "status": "evaluated"
    }


@router.get("/result", response_model=AssessmentResultResponse)
async def get_assessment_result(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Get assessment result for candidate
    
    - Returns scores and verdict
    - Only available after evaluation
    """
    score = db.query(Score).filter(Score.candidate_id == candidate_id).first()
    
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    return AssessmentResultResponse(
        total_score=score.weighted_total,
        coding_score=score.correctness,
        mcq_score=score.mcq_total,
        verdict=score.verdict,
        evaluation_details=score.evaluation_details
    )
