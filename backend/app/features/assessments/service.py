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
from app.features.code_execution.service import PistonExecutionService
from app.features.code_execution.schemas import TestCase as ExecutionTestCase

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
                time_limit=45 if req.round == AssessmentRound.ROUND_2 else 60
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
                # MCQ Round - Revised for Freshers/Tier-3
                available_topics = [
                    "Programming Fundamentals", "OOP Basics", "SQL Basics", 
                    "Web Fundamentals", "Git Basics", "APIs", 
                    "Java Basics", "Python Basics", "React Basics"
                ]
                # Pick 4 random topics
                selected_topics = random.sample(available_topics, 4)
                
                logger.info(f"Generating MCQs for topics: {selected_topics}")
                
                # Distribution: 70% Easy, 25% Medium, 5% Hard
                # Total 12 questions (3 per topic)
                # ~8 Easy, ~3 Medium, ~1 Hard
                difficulties = ["easy"] * 8 + ["medium"] * 3 + ["hard"] * 1
                random.shuffle(difficulties)
                
                tasks = []
                for i, topic in enumerate(selected_topics):
                    # 3 questions per topic
                    for j in range(3):
                        diff = difficulties.pop()
                        tasks.append(generate_mcq_questions(topic=topic, count=1, difficulty=diff))
                
                results = await asyncio.gather(*tasks)
                
                all_questions = []
                for res in results:
                    all_questions.extend(res)
                
                if not all_questions:
                    raise ValueError("AI failed to generate any MCQ questions")
                
                # Shuffle the combined list
                random.shuffle(all_questions)
                # Add Pattern Coding Section for Round 2 (Continuous)
                pattern_topics = ["Basic Loops", "Conditional Logic"]
                pattern_tasks = [generate_question(topic=random.choice(pattern_topics), difficulty="easy")]
                pattern_results = await asyncio.gather(*pattern_tasks)
                
                problems = []
                for q in pattern_results:
                    problems.append({
                        "id": q.id,
                        "title": q.title,
                        "description": q.description,
                        "difficulty": "easy",
                        "points": 20,
                        "suggested_duration_mins": 10,
                        "starter_code": q.boilerplate.get(candidate.language_choice, q.boilerplate.get("python", "")),
                        "test_cases": [
                            {"input": tc.input, "expectedOutput": tc.expected_output}
                            for tc in q.public_test_cases
                        ],
                        "_private_cases": [
                            {"input": tc.input, "expectedOutput": tc.expected_output}
                            for tc in q.private_test_cases
                        ]
                    })
                
                return {"questions": all_questions, "problems": problems}
            else:
                # Coding Round - Revised for Freshers (3 questions)
                available_coding_topics = [
                    "Strings", "Arrays", "HashMaps", "Loops", 
                    "Functions", "Basic Sorting", "Basic Searching", "Simple Data Processing"
                ]
                # Pick 3 random topics
                selected_topics = random.sample(available_coding_topics, 3)
                
                logger.info(f"Generating Coding Problems for topics: {selected_topics}")
                
                # Q1: Easy
                # Q2: Easy-Medium (Calling it easy for the prompt but with slightly more logic)
                # Q3: Medium
                
                tasks = [
                    generate_question(topic=selected_topics[0], difficulty="easy"),
                    generate_question(topic=selected_topics[1], difficulty="easy"), # "Easy-Medium" mapped to easy with prompt hints
                    generate_question(topic=selected_topics[2], difficulty="medium")
                ]
                
                results = await asyncio.gather(*tasks)
                
                problems = []
                for i, q in enumerate(results):
                    # Assign points and suggested duration
                    if i == 0:
                        points = 20
                        duration_mins = 15
                        diff_label = "easy"
                    elif i == 1:
                        points = 30
                        duration_mins = 20
                        diff_label = "easy-medium"
                    else:
                        points = 50
                        duration_mins = 25
                        diff_label = "medium"
                        
                    problems.append({
                        "id": q.id,
                        "title": q.title,
                        "description": q.description,
                        "difficulty": diff_label,
                        "points": points,
                        "suggested_duration_mins": duration_mins,
                        "starter_code": q.boilerplate.get(candidate.language_choice, q.boilerplate.get("python", "")),
                        "test_cases": [
                            {"input": tc.input, "expectedOutput": tc.expected_output}
                            for tc in q.public_test_cases
                        ],
                        "_private_cases": [
                            {"input": tc.input, "expectedOutput": tc.expected_output}
                            for tc in q.private_test_cases
                        ]
                    })
                    
                return {"problems": problems}

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
                        "question": "What is the time complexity of searching an element in a sorted array using Binary Search?",
                        "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"],
                        "correct_answer": "O(log n)",
                        "explanation": "Binary search divides the search space by half in each step.",
                        "difficulty": "easy",
                        "topic": "Algorithms"
                    },
                    {
                        "id": "fallback_2",
                        "question": "Which of the following is a core pillar of OOP?",
                        "options": ["Compilation", "Interpretation", "Encapsulation", "Garbage Collection"],
                        "correct_answer": "Encapsulation",
                        "explanation": "The four pillars of OOP are Encapsulation, Abstraction, Inheritance, and Polymorphism.",
                        "difficulty": "easy",
                        "topic": "OOP Basics"
                    }
                ],
                "problems": [
                    {
                        "id": "pattern_1",
                        "title": "Square Pattern",
                        "description": "Print a 3x3 grid of stars (*).",
                        "difficulty": "easy",
                        "points": 20,
                        "suggested_duration_mins": 10,
                        "starter_code": "print('***\\n***\\n***')",
                        "test_cases": [{"input": "", "expectedOutput": "***\\n***\\n***"}],
                        "_private_cases": [{"input": "", "expectedOutput": "***\\n***\\n***"}]
                    }
                ]
            }
        return {
            "problems": [
                {
                    "id": "fallback_code_1",
                    "title": "Sum of Two Numbers",
                    "description": "Read two integers from stdin and print their sum.",
                    "difficulty": "easy",
                    "points": 20,
                    "suggested_duration_mins": 15,
                    "starter_code": "import sys\\na, b = map(int, sys.stdin.read().split())\\nprint(a + b)",
                    "test_cases": [{"input": "5 10", "expectedOutput": "15"}],
                    "_private_cases": [{"input": "100 200", "expectedOutput": "300"}]
                },
                {
                    "id": "fallback_code_2",
                    "title": "Find Largest in Array",
                    "description": "Given an array of integers, find the largest element.",
                    "difficulty": "easy-medium",
                    "points": 30,
                    "suggested_duration_mins": 20,
                    "starter_code": "import sys\\ndata = list(map(int, sys.stdin.read().split()))\\nprint(max(data))",
                    "test_cases": [{"input": "1 5 3 9 2", "expectedOutput": "9"}],
                    "_private_cases": [{"input": "10 20 5", "expectedOutput": "20"}]
                },
                {
                    "id": "fallback_code_3",
                    "title": "Count Vowels",
                    "description": "Given a string, count the number of vowels in it.",
                    "difficulty": "medium",
                    "points": 50,
                    "suggested_duration_mins": 25,
                    "starter_code": "import sys\\ns = sys.stdin.read().strip()\\ncount = sum(1 for char in s if char.lower() in 'aeiou')\\nprint(count)",
                    "test_cases": [{"input": "Hello World", "expectedOutput": "3"}],
                    "_private_cases": [{"input": "Knowledge Factory", "expectedOutput": "5"}]
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
        json_payload = data.content
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
                answers = mcq_sub.payload_json.get("answers")
                if answers is None:
                    # Fallback if frontend sent answers directly at top level
                    answers = mcq_sub.payload_json
                    
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
            # Coding Evaluation (Automated) - Redesigned
            from decimal import Decimal
            
            # 1. Get all coding submissions to find the latest code per problem
            coding_submissions = [s for s in submissions if s.section == "CODING"]
            
            # Extract latest code for each problem
            # The frontend can send either a full dictionary in 'answers' OR individual {problemId: code}
            latest_codes = {}
            for sub in coding_submissions:
                payload = sub.payload_json
                if "answers" in payload:
                    for pid, pcode in payload["answers"].items():
                        latest_codes[pid] = pcode
                if "problemId" in payload and "code" in payload:
                    latest_codes[payload["problemId"]] = payload["code"]
                elif "code" in payload and not "problemId" in payload:
                    # Fallback for single question or legacy
                    problems = assessment.questions_json.get("problems", [])
                    if problems:
                        latest_codes[problems[0]["id"]] = payload["code"]

            # 2. Get question metadata
            problems = assessment.questions_json.get("problems", [])
            if not problems:
                raise ValueError("No coding problems found in assessment metadata")
            
            # 3. Execute evaluation using Piston
            executor = PistonExecutionService()
            language = candidate.language_choice or "python"
            
            total_weighted_score = 0.0
            results_by_problem = {}
            q1_passed_at_least_one = False
            
            total_possible_score = sum(p.get("points", 100) for p in problems)
            
            for i, problem in enumerate(problems):
                pid = problem["id"]
                points = problem.get("points", 100)
                source_code = latest_codes.get(pid, "")
                
                logger.info(f"Evaluating problem {i+1}/{len(problems)}: {pid} (Points: {points})")
                
                public_cases = problem.get("test_cases", [])
                private_cases = problem.get("_private_cases", [])
                
                all_test_cases = []
                for tc in public_cases:
                    all_test_cases.append(ExecutionTestCase(input=tc["input"], expected_output=tc["expectedOutput"]))
                for tc in private_cases:
                    all_test_cases.append(ExecutionTestCase(input=tc["input"], expected_output=tc["expectedOutput"]))
                
                logger.info(f"Problem {pid}: Found {len(all_test_cases)} test cases.")
                
                if not all_test_cases or not source_code.strip():
                    logger.warning(f"Problem {pid}: No test cases or no source code. Skipping.")
                    results_by_problem[pid] = {
                        "score_percentage": 0.0,
                        "points_earned": 0.0,
                        "passed_tests": 0,
                        "total_tests": len(all_test_cases),
                        "code": source_code,
                        "test_results": []
                    }
                    continue
                    
                eval_result = await executor.evaluate_code(
                    language=language,
                    code=source_code,
                    test_cases=all_test_cases
                )
                
                logger.info(f"Problem {pid}: Evaluation complete. Score: {eval_result.score_percentage}%")

                
                pct = eval_result.score_percentage
                points_earned = (pct / 100.0) * points
                total_weighted_score += points_earned
                
                results_by_problem[pid] = {
                    "score_percentage": pct,
                    "points_earned": points_earned,
                    "passed_tests": eval_result.passed_tests,
                    "total_tests": eval_result.total_tests,
                    "code": source_code,
                    "test_results": eval_result.test_results
                }
                
                # Check Q1 specific rule (i == 0)
                if i == 0 and eval_result.passed_tests > 0:
                    q1_passed_at_least_one = True
            
            final_percentage = (total_weighted_score / total_possible_score) * 100.0 if total_possible_score > 0 else 0.0
            
            # Pass criteria: >= 40% AND Q1 >= 1 passing test case
            # This aligns with freshers where solving Q1 and part of Q2 is considered a 'pass'
            verdict = "PASS" if (final_percentage >= 40.0 and q1_passed_at_least_one) else "FAIL"

            # 4. Fetch proctoring risk if available
            risk_stmt = select(ProctoringSession).where(ProctoringSession.assessment_attempt_id == assessment_id)
            risk_res = await self.db.execute(risk_stmt)
            proctoring = risk_res.scalar_one_or_none()
            risk_score = proctoring.final_risk_score if proctoring else 0.0

            # 5. Store Score
            total_tests_across_all = sum(r["total_tests"] for r in results_by_problem.values())
            passed_tests_across_all = sum(r["passed_tests"] for r in results_by_problem.values())

            score = Score(
                candidate_id=candidate_id,
                round=round_val,
                correctness=int(final_percentage),
                quality=0, design=0, edge_cases=0, efficiency=0,
                mcq_total=0,
                weighted_total=Decimal(str(final_percentage)),
                verdict=verdict,
                feedback_json={
                    "total_tests": total_tests_across_all,
                    "passed_tests": passed_tests_across_all,
                    "failed_tests": total_tests_across_all - passed_tests_across_all,
                    "score_percentage": final_percentage,
                    "results_by_problem": results_by_problem,
                    "language": language,
                    "proctoring_risk": float(risk_score)
                }
            )
            self.db.add(score)

            # 6. Transition candidate status
            if score.verdict == "PASS":
                candidate.status = CandidateStatus.ROUND3_PASSED
            else:
                candidate.status = CandidateStatus.ROUND3_REJECTED

        assessment.status = AssessmentStatus.COMPLETED
        assessment.ended_at = datetime.now(timezone.utc)

        await self.db.flush()
        
        # Trigger composite score and recommendation calculation
        from app.features.selection.service import EvaluationService
        eval_svc = EvaluationService(self.db)
        await eval_svc.update_candidate_evaluation(candidate_id)

        return assessment

    async def get_assessment(self, candidate_id: str) -> list[Assessment]:
        stmt = (
            select(Assessment)
            .where(Assessment.candidate_id == str(candidate_id))
            .order_by(Assessment.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_assessment_result(self, candidate_id: str, assessment_id: str) -> dict:
        """Fetch the final result for a completed assessment."""
        # 1. Verify assessment exists and belongs to candidate
        stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.candidate_id == str(candidate_id))
        res = await self.db.execute(stmt)
        assessment = res.scalar_one_or_none()
        if not assessment:
            raise ValueError("Assessment not found")
        
        # 2. Fetch the score
        score_stmt = select(Score).where(Score.candidate_id == str(candidate_id), Score.round == assessment.round).order_by(Score.evaluated_at.desc())
        score_res = await self.db.execute(score_stmt)
        score = score_res.scalars().first()
        
        if not score:
            raise ValueError("Score not found. Is the assessment completed?")
            
        return {
            "assessment_id": assessment_id,
            "round": assessment.round,
            "score": float(score.weighted_total),
            "passed_tests": score.feedback_json.get("passed_tests", score.mcq_total),
            "total_tests": score.feedback_json.get("total_tests", score.feedback_json.get("total", 0)),
            "verdict": score.verdict,
            "status": "Passed" if score.verdict == "PASS" else "Failed",
            "summary": f"Passed Test Cases: {score.feedback_json.get('passed_tests', score.mcq_total)}/{score.feedback_json.get('total_tests', score.feedback_json.get('total', 0))}"
        }
