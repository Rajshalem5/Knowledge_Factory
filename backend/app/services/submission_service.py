# app/services/submission_service.py

import uuid
from sqlalchemy.orm import Session

from app.models.submission import Submission


def create_submission(db: Session, data, current_user):
    submission = Submission(
        submission_id=f"SUB-{uuid.uuid4().hex[:8]}",
        qid=data.qid,
        candidate_id=current_user.id,
        language=data.language,
        code=data.code,
        mcq_answers=data.mcq_answers,
        time_spent=data.time_spent
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return submission
