"""
Phase 2 assessment routes.

HR endpoints:
  POST /api/phase2/start/{applicant_id}   → AI assigns questions, starts assessment
  GET  /api/phase2/results/{applicant_id} → HR views candidate's scores

Candidate endpoints:
  GET  /api/phase2/my-assessment          → get assigned questions (public only)
  POST /api/phase2/submit                 → submit code for evaluation
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    get_current_user, AuthUser,
    HR_AND_ABOVE, CANDIDATE_ONLY,
)
from app.features.questions.assignment_service import assign_questions_to_candidate
from app.features.code_execution.service import PistonExecutionService

router = APIRouter()


# ── HR: Start Phase 2 for a candidate ─────────────────────────────

@router.post("/start/{applicant_id}")
async def start_phase2(
    applicant_id: str,
    db: AsyncSession = Depends(get_db),
    hr_user: AuthUser = Depends(HR_AND_ABOVE),
):
    """
    HR triggers Phase 2 for a shortlisted candidate.
    AI generates questions based on job description and assigns them randomly.
    """
    # Get applicant record
    result = await db.execute(
        text("""
            SELECT a.id, a.user_id, a.job_id, a.status
            FROM applicant_status a
            WHERE a.id = :id
        """),
        {"id": applicant_id},
    )
    applicant = result.fetchone()

    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    if applicant.status not in ("SHORTLISTED", "PHASE2_PENDING"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start Phase 2 for status '{applicant.status}'. Must be SHORTLISTED or PHASE2_PENDING."
        )

    # Check if assessment already exists
    result = await db.execute(
        text("SELECT id FROM assessments WHERE candidate_id = :cid AND job_id = :jid"),
        {"cid": applicant.user_id, "jid": applicant.job_id},
    )
    if result.fetchone():
        raise HTTPException(status_code=400, detail="Phase 2 already started for this candidate")

    # AI assigns questions
    try:
        assigned = await assign_questions_to_candidate(
            db=db,
            candidate_id=applicant.user_id,
            job_id=applicant.job_id,
            assigned_by=hr_user.id,
            num_questions=3,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Question assignment failed: {str(e)}")

    # Create assessment session
    assessment_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO assessments (id, candidate_id, job_id, status, created_at)
            VALUES (:id, :candidate_id, :job_id, 'NOT_STARTED', now())
        """),
        {"id": assessment_id, "candidate_id": applicant.user_id, "job_id": applicant.job_id},
    )

    # Update applicant status
    await db.execute(
        text("UPDATE applicant_status SET status = 'PHASE2_STARTED' WHERE id = :id"),
        {"id": applicant_id},
    )

    await db.commit()

    return {
        "message": "Phase 2 started",
        "assessment_id": assessment_id,
        "questions_assigned": len(assigned),
        "questions": [{"id": q["id"], "title": q["title"], "difficulty": q["difficulty"]} for q in assigned],
    }


# ── Candidate: Get their assigned questions ────────────────────────

@router.get("/my-assessment")
async def get_my_assessment(
    db: AsyncSession = Depends(get_db),
    candidate: AuthUser = Depends(CANDIDATE_ONLY),
):
    """
    Candidate gets their assigned questions.
    Returns ONLY public test cases — private ones stay server-side.
    """
    # Get assessment
    result = await db.execute(
        text("""
            SELECT a.id, a.job_id, a.status, a.language, a.time_limit_secs,
                   a.started_at, j.title as job_title
            FROM assessments a
            JOIN jobs j ON j.id = a.job_id
            WHERE a.candidate_id = :cid
            ORDER BY a.created_at DESC
            LIMIT 1
        """),
        {"cid": candidate.id},
    )
    assessment = result.fetchone()

    if not assessment:
        raise HTTPException(status_code=404, detail="No active assessment found")

    # Mark as in progress on first access
    if assessment.status == "NOT_STARTED":
        await db.execute(
            text("UPDATE assessments SET status = 'IN_PROGRESS', started_at = now() WHERE id = :id"),
            {"id": assessment.id},
        )
        await db.commit()

    # Get assigned questions — PUBLIC test cases only
    result = await db.execute(
        text("""
            SELECT
                cq.position,
                q.id,
                q.qid,
                q.title,
                q.description,
                q.difficulty,
                q.boilerplate,
                cq.public_snapshot as public_test_cases
            FROM candidate_questions cq
            JOIN questions q ON q.id = cq.question_id
            WHERE cq.candidate_id = :cid
              AND cq.job_id = :jid
            ORDER BY cq.position
        """),
        {"cid": candidate.id, "jid": assessment.job_id},
    )
    questions = result.fetchall()

    return {
        "assessment_id": str(assessment.id),
        "job_title": assessment.job_title,
        "status": assessment.status,
        "language": assessment.language,
        "time_limit_seconds": assessment.time_limit_secs,
        "started_at": assessment.started_at,
        "questions": [
            {
                "position": q.position,
                "id": str(q.id),
                "qid": q.qid,
                "title": q.title,
                "description": q.description,
                "difficulty": q.difficulty,
                "boilerplate": q.boilerplate,
                "public_test_cases": q.public_test_cases,
                # private_test_cases intentionally excluded
            }
            for q in questions
        ],
    }


# ── Candidate: Submit code ─────────────────────────────────────────

class SubmitRequest(BaseModel):
    question_id: str
    language: str
    code: str
    time_spent: int = 0


@router.post("/submit")
async def submit_code(
    req: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    candidate: AuthUser = Depends(CANDIDATE_ONLY),
):
    """
    Candidate submits code for a question.
    Backend fetches private test cases and evaluates via Piston.
    Score is stored. Private test cases never sent to frontend.
    """
    # Verify candidate is assigned this question
    result = await db.execute(
        text("""
            SELECT cq.job_id FROM candidate_questions cq
            WHERE cq.candidate_id = :cid AND cq.question_id = :qid
        """),
        {"cid": candidate.id, "qid": req.question_id},
    )
    assignment = result.fetchone()
    if not assignment:
        raise HTTPException(status_code=403, detail="Question not assigned to you")

    # Get private test cases (server-side only)
    result = await db.execute(
        text("SELECT private_test_cases, title FROM questions WHERE id = :id"),
        {"id": req.question_id},
    )
    question = result.fetchone()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    private_cases = question.private_test_cases or []

    # Run evaluation via Piston
    service = PistonExecutionService()
    from app.features.code_execution.schemas import TestCase as TC
    test_cases = [
        TC(input=tc["input"], expected_output=tc["expected_output"])
        for tc in private_cases
    ]

    eval_result = await service.evaluate_code(
        language=req.language,
        code=req.code,
        test_cases=test_cases,
    )

    # Calculate marks
    total_marks = 100.0
    marks_obtained = round(eval_result.score_percentage, 2)
    verdict = "PASS" if eval_result.score_percentage >= 50 else "FAIL"

    # Store submission
    submission_id = str(uuid.uuid4())
    sub_human_id = f"sub_{submission_id[:8]}"
    await db.execute(
        text("""
            INSERT INTO submissions (
                id, submission_id, qid, candidate_id, language, code,
                time_spent, created_at, updated_at
            ) VALUES (
                :id, :sub_id, :qid, :cid, :lang, :code,
                :time_spent, now(), now()
            )
        """),
        {
            "id": submission_id,
            "sub_id": sub_human_id,
            "qid": req.question_id,
            "cid": candidate.id,
            "lang": req.language,
            "code": req.code,
            "time_spent": req.time_spent,
        },
    )

    # Store score
    score_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO scores (
                id, score_id, candidate_id, submission_id, qid,
                score_percentage, marks_obtained, total_marks, verdict,
                created_at, updated_at
            ) VALUES (
                :id, :score_id, :cid, :sub_id, :qid,
                :score_pct, :marks, :total, :verdict,
                now(), now()
            )
        """),
        {
            "id": score_id,
            "score_id": f"sc_{score_id[:8]}",
            "cid": candidate.id,
            "sub_id": submission_id,
            "qid": req.question_id,
            "score_pct": eval_result.score_percentage,
            "marks": marks_obtained,
            "total": total_marks,
            "verdict": verdict,
        },
    )

    # Update applicant status if all questions submitted
    result = await db.execute(
        text("""
            SELECT COUNT(*) FROM candidate_questions
            WHERE candidate_id = :cid AND job_id = :jid
        """),
        {"cid": candidate.id, "jid": assignment.job_id},
    )
    total_questions = result.fetchone()[0]

    result = await db.execute(
        text("""
            SELECT COUNT(DISTINCT s.qid) FROM submissions s
            JOIN candidate_questions cq ON cq.question_id = s.qid
            WHERE s.candidate_id = :cid AND cq.job_id = :jid
        """),
        {"cid": candidate.id, "jid": assignment.job_id},
    )
    submitted_count = result.fetchone()[0]

    if submitted_count >= total_questions:
        await db.execute(
            text("""
                UPDATE applicant_status SET status = 'PHASE2_COMPLETED'
                WHERE user_id = :cid AND job_id = :jid
            """),
            {"cid": candidate.id, "jid": assignment.job_id},
        )
        await db.execute(
            text("""
                UPDATE assessments SET status = 'COMPLETED', ended_at = now()
                WHERE candidate_id = :cid AND job_id = :jid
            """),
            {"cid": candidate.id, "jid": assignment.job_id},
        )

    await db.commit()

    return {
        "submission_id": sub_human_id,
        "score_percentage": eval_result.score_percentage,
        "marks_obtained": marks_obtained,
        "total_marks": total_marks,
        "verdict": verdict,
        "passed_tests": eval_result.passed_tests,
        "total_tests": eval_result.total_tests,
        # test_results shown but private inputs masked
        "test_results": [
            {
                "test_number": tr["test_number"],
                "status": tr["status"],
                "expected": tr["expected"] if tr["status"] == "PASSED" else "hidden",
                "actual": tr["actual"],
            }
            for tr in eval_result.test_results
        ],
    }


# ── HR: View candidate results ─────────────────────────────────────

@router.get("/results/{applicant_id}")
async def get_results(
    applicant_id: str,
    db: AsyncSession = Depends(get_db),
    hr_user: AuthUser = Depends(HR_AND_ABOVE),
):
    """HR views a candidate's Phase 2 scores."""
    result = await db.execute(
        text("""
            SELECT a.user_id, a.job_id, a.status,
                   u.full_name, u.email
            FROM applicant_status a
            JOIN users u ON u.id = a.user_id
            WHERE a.id = :id
        """),
        {"id": applicant_id},
    )
    applicant = result.fetchone()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    result = await db.execute(
        text("""
            SELECT
                q.title, q.difficulty,
                s.language, s.code,
                sc.score_percentage, sc.marks_obtained, sc.total_marks, sc.verdict,
                sc.created_at
            FROM scores sc
            JOIN submissions s ON s.id = sc.submission_id
            JOIN questions q ON q.id = sc.qid
            WHERE sc.candidate_id = :cid
              AND sc.qid IN (
                  SELECT question_id FROM candidate_questions WHERE job_id = :jid
              )
            ORDER BY sc.created_at
        """),
        {"cid": applicant.user_id, "jid": applicant.job_id},
    )
    scores = result.fetchall()

    total_score = sum(s.score_percentage for s in scores) / len(scores) if scores else 0

    return {
        "candidate": {"name": applicant.full_name, "email": applicant.email},
        "status": applicant.status,
        "overall_score": round(total_score, 2),
        "overall_verdict": "PASS" if total_score >= 50 else "FAIL",
        "question_scores": [
            {
                "title": s.title,
                "difficulty": s.difficulty,
                "language": s.language,
                "score_percentage": float(s.score_percentage),
                "marks_obtained": float(s.marks_obtained),
                "total_marks": float(s.total_marks),
                "verdict": s.verdict,
                "submitted_at": s.created_at,
            }
            for s in scores
        ],
    }
