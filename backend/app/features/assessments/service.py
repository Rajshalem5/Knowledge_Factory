"""Assessment service: start, submit, evaluate."""

import logging
import uuid
import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssessmentRound, AssessmentStatus, CandidateStatus
from app.features.assessments.models import Assessment, Submission, Score
from app.features.assessments.schemas import AssessmentStart, SubmissionCreate
from app.features.candidates.models import Candidate
from app.features.proctoring.models import ProctoringSession
from app.features.questions.ai_service import generate_question, generate_mcq_questions

logger = logging.getLogger(__name__)


class AssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_assessment(self, candidate_id: str, req: AssessmentStart) -> Assessment:
        logger.info("start_assessment called | candidate_id=%s | round=%s", candidate_id, req.round)

        # ═══ TRANSACTIONAL BLOCK ═══
        # Using separate block to ensure consistent state before starting heavy AI generation
        async with self.db.begin_nested():
            # 1. Validate candidate exists
            c_stmt = select(Candidate).where(Candidate.id == str(candidate_id))
            c_res = await self.db.execute(c_stmt)
            candidate = c_res.scalar_one_or_none()
            if not candidate:
                logger.error("Candidate not found | candidate_id=%s", candidate_id)
                raise ValueError("Candidate not found")
            
            # 2. ═══ CHECK EXISTING ASSESSMENT FIRST (Atomic Check) ═══
            existing_stmt = (
                select(Assessment)
                .where(
                    Assessment.candidate_id == str(candidate_id),
                    Assessment.round == req.round,
                    Assessment.status.in_([AssessmentStatus.IN_PROGRESS]),
                )
                .order_by(Assessment.started_at.desc())
            )
            existing_result = await self.db.execute(existing_stmt)
            existing = existing_result.scalars().first()

            if existing:
                logger.info(
                    "[Audit] Reusing existing assessment | candidate_id=%s | assessment_id=%s | round=%s",
                    candidate_id, existing.id, req.round
                )
                return existing

            # 3. Round-to-status mapping
            round_status_map = {
                AssessmentRound.ROUND_2: (CandidateStatus.ROUND1_PASSED, CandidateStatus.ROUND2_IN_PROGRESS),
                AssessmentRound.ROUND_3: (CandidateStatus.ROUND2_PASSED, CandidateStatus.ROUND3_IN_PROGRESS),
            }
            status_mapping = round_status_map.get(req.round)
            if status_mapping:
                required_status, next_status = status_mapping
                current = CandidateStatus(candidate.status) if isinstance(candidate.status, str) else candidate.status
                
                if current != required_status:
                     raise ValueError(f"Candidate not eligible for {req.round.value}")
                
                candidate.status = next_status

        # ═══ AI GENERATION (Outside the tight nested transaction to avoid blocking DB) ═══
        logger.info(f"Starting AI question generation for round {req.round}...")
        questions_data = await self._generate_questions(req.round, candidate)

        # ═══ PERSIST NEW ASSESSMENT ═══
        try:
            assessment_id = str(uuid.uuid4())
            assessment = Assessment(
                id=assessment_id,
                candidate_id=candidate_id,
                round=req.round,
                questions_json=questions_data,
                link_token=uuid.uuid4().hex,
                link_expiry=datetime.now(timezone.utc) + timedelta(days=5),
                started_at=datetime.now(timezone.utc),
                status=AssessmentStatus.IN_PROGRESS,
                time_limit=30 if req.round == AssessmentRound.ROUND_2 else 60
            )
            self.db.add(assessment)

            proctoring_session = ProctoringSession(
                assessment_attempt_id=assessment_id,
                user_id=candidate_id,
            )
            self.db.add(proctoring_session)

            await self.db.flush()
            logger.info(
                "[Audit] Created new assessment | candidate_id=%s | assessment_id=%s | round=%s",
                candidate_id, assessment_id, req.round
            )
            return assessment
        except Exception as e:
            # Check for race condition (Duplicate error from unique index)
            if "UNIQUE" in str(e) or "idx_one_active_assessment" in str(e):
                logger.warning("[Audit] Concurrent creation race detected. Retrying lookup...")
                # Re-fetch the one that was just created by another request
                await self.db.rollback()
                return await self.start_assessment(candidate_id, req)
            raise

    async def _generate_questions(self, round_type: AssessmentRound, candidate: Candidate) -> dict:
        """Call AI service to generate questions based on round type."""
        try:
            if round_type == AssessmentRound.ROUND_2:
                # MCQ Round - Generate from multiple topics in parallel
                available_topics = [
                    "Aptitude", "Reasoning", "DBMS", "OS", "Networking", 
                    "OOPs", "Java", "Python", "JavaScript", "SQL", "DSA Fundamentals"
                ]
                # Pick 3 random topics
                selected_topics = random.sample(available_topics, 3)
                
                logger.info(f"Generating MCQs for topics: {selected_topics}")
                
                # Each topic generates 4 questions = 12 total
                tasks = [generate_mcq_questions(topic=t, count=4) for t in selected_topics]
                results = await asyncio.gather(*tasks)
                
                all_questions = []
                for res in results:
                    all_questions.extend(res)
                
                if not all_questions:
                    raise ValueError("AI failed to generate any MCQ questions")
                
                # Shuffle the combined list
                random.shuffle(all_questions)
                return {"questions": all_questions}
            else:
                # Coding Round
                topic = candidate.language_choice or "arrays"
                q = await generate_question(topic=topic, difficulty="medium")
                return {
                    "problems": [
                        {
                            "id": q.id,
                            "title": q.title,
                            "description": q.description,
                            "difficulty": q.difficulty,
                            "starter_code": q.boilerplate.get(candidate.language_choice, q.boilerplate.get("python")),
                            "test_cases": [
                                {"input": tc.input, "expectedOutput": tc.expected_output}
                                for tc in q.public_test_cases
                            ],
                            "_private_cases": [
                                {"input": tc.input, "expectedOutput": tc.expected_output}
                                for tc in q.private_test_cases
                            ]
                        }
                    ]
                }
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_sample_questions(round_type)

    @staticmethod
    def _generate_sample_questions(round_type: AssessmentRound) -> dict:
        """Generate sample questions for development fallback."""
        if round_type == AssessmentRound.ROUND_2:
            return {
                "questions": [
                    {
                        "id": "fallback_1",
                        "question": "What is the time complexity of binary search?",
                        "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"],
                        "correct_answer": "O(log n)",
                        "explanation": "Binary search divides the search space by half in each step.",
                        "difficulty": "easy",
                        "topic": "Algorithms"
                    },
                    {
                        "id": "fallback_2",
                        "question": "Which of the following is not a pillar of OOPs?",
                        "options": ["Encapsulation", "Inheritance", "Polymorphism", "Compilation"],
                        "correct_answer": "Compilation",
                        "explanation": "Pillars are Encapsulation, Abstraction, Inheritance, Polymorphism.",
                        "difficulty": "easy",
                        "topic": "OOPs"
                    }
                ]
            }
        return {
            "problems": [
                {
                    "id": "fallback_code_1",
                    "title": "Hello World",
                    "description": "Print 'Hello, World!' to stdout.",
                    "difficulty": "easy",
                    "starter_code": "print('Hello, World!')",
                    "test_cases": [{"input": "", "expectedOutput": "Hello, World!"}]
                }
            ]
        }

    async def submit_section(self, candidate_id: str, data: SubmissionCreate) -> dict[str, Any]:
        """Submit a section. Returns passed/failed test case counts."""
        # Verify the candidate owns this assessment
        stmt = select(Assessment).where(Assessment.id == data.assessment_id)
        res = await self.db.execute(stmt)
        assessment = res.scalar_one_or_none()

        if not assessment or str(assessment.candidate_id) != str(candidate_id):
            raise ValueError("Assessment not found or access denied")

        # Validate assessment is in progress
        status_val = AssessmentStatus(assessment.status) if isinstance(assessment.status, str) else assessment.status
        if status_val != AssessmentStatus.IN_PROGRESS:
            raise ValueError("Assessment is not in progress — submissions are only accepted for active assessments")

        # Create submission
        section = data.section
        json_payload = {"code" if data.section == "CODING" else "answers": data.content}
        submission = Submission(
            assessment_id=data.assessment_id,
            section=section,
            payload_json=json_payload,
            time_spent_seconds=data.time_spent_seconds,
        )
        self.db.add(submission)

        await self.db.flush()
        return {"submission_id": submission.id, "passed": 0, "failed": 0}

    async def complete_assessment(self, candidate_id: str, assessment_id: str) -> Assessment:
        """Mark an assessment as completed and transition the candidate to the next pipeline stage."""
        stmt = select(Assessment).where(Assessment.id == assessment_id)
        res = await self.db.execute(stmt)
        assessment = res.scalar_one_or_none()

        if not assessment or str(assessment.candidate_id) != str(candidate_id):
            raise ValueError("Assessment not found or access denied")

        # Validate assessment is in progress
        assessment_status = AssessmentStatus(assessment.status) if isinstance(assessment.status, str) else assessment.status
        if assessment_status != AssessmentStatus.IN_PROGRESS:
            if assessment_status == AssessmentStatus.COMPLETED:
                return assessment
            raise ValueError(f"Assessment cannot be completed in its current state: {assessment_status.value}")

        # Fetch submissions to evaluate
        sub_stmt = select(Submission).where(Submission.assessment_id == assessment_id)
        sub_res = await self.db.execute(sub_stmt)
        submissions = sub_res.scalars().all()
        
        if not submissions:
            raise ValueError("No submissions found for this assessment")

        candidate_stmt = select(Candidate).where(Candidate.id == str(candidate_id))
        candidate_res = await self.db.execute(candidate_stmt)
        candidate = candidate_res.scalar_one_or_none()
        if not candidate:
            raise ValueError("Candidate not found")

        # ═══ EVALUATE ROUND ═══
        round_val = AssessmentRound(assessment.round) if isinstance(assessment.round, str) else assessment.round
        
        if round_val == AssessmentRound.ROUND_2:
            # MCQ Evaluation
            correct_count = 0
            total_questions = len(assessment.questions_json.get("questions", []))
            
            # Find the latest MCQ submission
            mcq_sub = next((s for s in reversed(submissions) if s.section == "MCQ"), None)
            if mcq_sub:
                answers = mcq_sub.payload_json.get("answers", {})
                for q in assessment.questions_json.get("questions", []):
                    q_id = q.get("id")
                    correct_ans = q.get("correct_answer")
                    user_ans = answers.get(q_id)
                    
                    # AI might return index or string. Handle both.
                    options = q.get("options", [])
                    if isinstance(correct_ans, int) and 0 <= correct_ans < len(options):
                         correct_str = options[correct_ans]
                    else:
                         correct_str = str(correct_ans)
                         
                    if isinstance(user_ans, int) and 0 <= user_ans < len(options):
                         user_str = options[user_ans]
                    else:
                         user_str = str(user_ans)

                    if user_str == correct_str:
                        correct_count += 1
            
            # Store Score
            from decimal import Decimal
            score = Score(
                candidate_id=candidate_id,
                round=round_val,
                correctness=int((correct_count / total_questions * 100) if total_questions > 0 else 0),
                quality=0, design=0, edge_cases=0, efficiency=0,
                mcq_total=correct_count,
                weighted_total=Decimal(correct_count),
                verdict="PASS" if (total_questions > 0 and (correct_count / total_questions) >= 0.5) else "FAIL",
                feedback_json={"correct_count": correct_count, "total": total_questions}
            )
            self.db.add(score)
            
            # Transition status
            if score.verdict == "PASS":
                candidate.status = CandidateStatus.ROUND2_PASSED
            else:
                candidate.status = CandidateStatus.ROUND2_REJECTED

        elif round_val == AssessmentRound.ROUND_3:
            # Coding Evaluation (Placeholder for AI/Judge0)
            candidate.status = CandidateStatus.ROUND3_PASSED

        assessment.status = AssessmentStatus.COMPLETED
        assessment.ended_at = datetime.now(timezone.utc)

        await self.db.flush()
        return assessment

    async def get_assessment(self, candidate_id: str) -> list[Assessment]:
        stmt = (
            select(Assessment)
            .where(Assessment.candidate_id == str(candidate_id))
            .order_by(Assessment.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
