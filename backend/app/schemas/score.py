# app/schemas/score.py

from pydantic import BaseModel


class ScoreResponse(BaseModel):
    id: str
    score_id: str
    candidate_id: str
    submission_id: str
    qid: str
    score_percentage: float
    marks_obtained: float
    total_marks: float
    verdict: str
