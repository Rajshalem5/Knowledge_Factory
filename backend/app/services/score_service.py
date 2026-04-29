# app/services/score_service.py

import uuid
from sqlalchemy.orm import Session

from app.models.score import Score


def create_score(
    db: Session,
    candidate_id: str,
    submission_id: str,
    qid: str,
    score_percentage: float,
    marks_obtained: float,
    total_marks: float
):
    verdict = "PASS" if score_percentage >= 50 else "FAIL"

    score = Score(
        score_id=f"SCR-{uuid.uuid4().hex[:8]}",
        candidate_id=candidate_id,
        submission_id=submission_id,
        qid=qid,
        score_percentage=score_percentage,
        marks_obtained=marks_obtained,
        total_marks=total_marks,
        verdict=verdict
    )

    db.add(score)
    db.commit()
    db.refresh(score)

    return score
