"""Evaluation and Selection Service."""

import logging
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.candidates.models import Candidate
from app.features.assessments.models import Score
from app.features.proctoring.models import ProctoringSession
from app.core.enums import CandidateStatus, EvaluationRecommendation, AssessmentRound

logger = logging.getLogger(__name__)

class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_screening_score(self, candidate: Candidate, cycle_config: dict) -> float:
        """
        Calculate screening score out of 100.
        CGPA = 40%
        Degree Match = 20%
        Branch Match = 20%
        Year Match = 10%
        Skills Match = 10%
        """
        score = 0.0
        
        # 1. CGPA (40%) - Scale 0-10 to 0-40
        cgpa = float(candidate.cgpa)
        score += (cgpa / 10.0) * 40.0
        
        # 2. Degree Match (20%)
        allowed_degrees = cycle_config.get("allowed_degrees", [])
        if not allowed_degrees or (candidate.degree and candidate.degree.lower() in [d.lower() for d in allowed_degrees]):
            score += 20.0
            
        # 3. Branch Match (20%)
        allowed_branches = cycle_config.get("allowed_branches", [])
        if not allowed_branches or candidate.branch.lower() in [b.lower() for b in allowed_branches]:
            score += 20.0
            
        # 4. Year Match (10%)
        allowed_years = cycle_config.get("passed_out_years", [])
        if not allowed_years or candidate.passed_out_year in allowed_years:
            score += 10.0
            
        # 5. Skills Match (10%)
        # Simple placeholder for skill matching
        required_skills = cycle_config.get("required_skills", [])
        if not required_skills:
            score += 10.0
        elif candidate.skills:
            cand_skills = candidate.skills.lower()
            matched = sum(1 for s in required_skills if s.lower() in cand_skills)
            score += (matched / len(required_skills)) * 10.0 if required_skills else 10.0
            
        return min(round(score, 2), 100.0)

    async def update_candidate_evaluation(self, candidate_id: str):
        """Recalculate all scores and recommendation for a candidate."""
        # Refresh candidate to get cycle relationship
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        res = await self.db.execute(stmt)
        candidate = res.scalar_one_or_none()
        if not candidate:
            return

        # 1. Screening Score
        cycle_cfg = {}
        if candidate.cycle:
            cycle_cfg = candidate.cycle.eligibility_config or {}
        
        candidate.screening_score = Decimal(str(await self.calculate_screening_score(candidate, cycle_cfg)))

        # 2. MCQ Score (Round 2)
        mcq_stmt = select(Score).where(Score.candidate_id == candidate_id, Score.round == AssessmentRound.ROUND_2).order_by(Score.evaluated_at.desc())
        mcq_res = await self.db.execute(mcq_stmt)
        mcq_score_obj = mcq_res.scalars().first()
        if mcq_score_obj:
            candidate.mcq_score = Decimal(str(mcq_score_obj.correctness)) # Correctness is percentage

        # 3. Coding Score (Round 3)
        coding_stmt = select(Score).where(Score.candidate_id == candidate_id, Score.round == AssessmentRound.ROUND_3).order_by(Score.evaluated_at.desc())
        coding_res = await self.db.execute(coding_stmt)
        coding_score_obj = coding_res.scalars().first()
        if coding_score_obj:
            candidate.coding_score = Decimal(str(coding_score_obj.weighted_total))

        # 4. Proctoring Penalty
        # Get max risk across all proctoring sessions for this candidate
        risk_stmt = select(ProctoringSession).where(ProctoringSession.user_id == candidate_id)
        risk_res = await self.db.execute(risk_stmt)
        risk_sessions = risk_res.scalars().all()
        
        max_risk = 0.0
        if risk_sessions:
            max_risk = max(float(s.final_risk_score) for s in risk_sessions)
            
        penalty = 0.0
        if max_risk > 100:
            penalty = 15.0 # Flag for review but capped penalty
        elif max_risk > 60:
            penalty = 10.0
        elif max_risk > 30:
            penalty = 5.0
            
        candidate.risk_penalty = Decimal(str(penalty))

        # 5. Composite Score
        # 20% Screening, 30% MCQ, 50% Coding
        comp = (float(candidate.screening_score) * 0.20) + \
               (float(candidate.mcq_score) * 0.30) + \
               (float(candidate.coding_score) * 0.50)
        
        candidate.composite_score = Decimal(str(round(comp, 2)))
        candidate.adjusted_final_score = Decimal(str(round(max(0, comp - penalty), 2)))

        # 6. Recommendation
        final = float(candidate.adjusted_final_score)
        if final >= 85:
            candidate.recommendation = EvaluationRecommendation.STRONGLY_RECOMMENDED
        elif final >= 70:
            candidate.recommendation = EvaluationRecommendation.RECOMMENDED
        elif final >= 60:
            candidate.recommendation = EvaluationRecommendation.BORDERLINE
        else:
            candidate.recommendation = EvaluationRecommendation.NOT_RECOMMENDED

        logger.info(f"Updated evaluation for candidate {candidate_id}: Score={candidate.adjusted_final_score}, Rec={candidate.recommendation}")
        await self.db.flush()
        
    async def get_ranked_candidates(self, cycle_id: str):
        """Get candidates ranked by adjusted final score."""
        stmt = (
            select(Candidate)
            .where(Candidate.cycle_id == cycle_id)
            .order_by(Candidate.adjusted_final_score.desc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()
