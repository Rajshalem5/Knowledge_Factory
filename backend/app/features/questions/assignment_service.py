"""
AI-powered question assignment service.

When HR starts Phase 2 for a candidate:
1. Read the job description + skillset
2. Ask AI to generate N questions relevant to the job
3. Save questions to the questions table
4. Randomly assign them to the candidate via candidate_questions
5. Private test cases stay server-side only
"""

import uuid
import random
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.features.questions.ai_service import generate_question


async def assign_questions_to_candidate(
    db: AsyncSession,
    candidate_id: str,
    job_id: str,
    assigned_by: str,
    num_questions: int = 3,
) -> list[dict]:
    """
    AI generates questions based on job description, then assigns them
    randomly to the candidate.

    Returns list of public question views (no private test cases).
    """

    # 1. Get job details
    result = await db.execute(
        text("SELECT title, job_description, skillset FROM jobs WHERE id = :id"),
        {"id": job_id},
    )
    job = result.fetchone()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # 2. Check if questions already exist for this job in the bank
    result = await db.execute(
        text("""
            SELECT q.id, q.qid, q.title, q.difficulty, q.boilerplate,
                   q.public_test_cases, q.private_test_cases,
                   q.input_format, q.output_format, q.constraints
            FROM job_questions jq
            JOIN questions q ON q.id = jq.question_id
            WHERE jq.job_id = :job_id AND q.is_active = true
            ORDER BY RANDOM()
            LIMIT :limit
        """),
        {"job_id": job_id, "limit": num_questions},
    )
    existing = result.fetchall()

    questions_to_assign = list(existing)

    # 3. If not enough questions in bank, generate new ones with AI
    needed = num_questions - len(questions_to_assign)
    if needed > 0:
        # Build topic from job skillset
        skillset = job.skillset if job.skillset else []
        topic = f"{job.title}: {', '.join(skillset[:3])}" if skillset else job.title

        for _ in range(needed):
            try:
                # Randomly vary difficulty
                difficulty = random.choice(["EASY", "MEDIUM", "MEDIUM", "HARD"])

                q = await generate_question(
                    topic=topic,
                    difficulty=difficulty.lower(),
                    num_public=2,
                    num_private=4,
                )

                # Save to questions table
                q_id = str(uuid.uuid4())
                await db.execute(
                    text("""
                        INSERT INTO questions (
                            id, qid, title, description, difficulty, topics,
                            input_format, output_format, constraints,
                            boilerplate, public_test_cases, private_test_cases,
                            generated_by_ai, ai_model, ai_prompt,
                            is_active, created_by, created_at,
                            times_used, avg_passrate
                        ) VALUES (
                            :id, :qid, :title, :description, :difficulty, :topics,
                            :input_format, :output_format, :constraints,
                            :boilerplate, :public_test_cases, :private_test_cases,
                            true, :ai_model, :ai_prompt,
                            true, :created_by, now(),
                            0, 0
                        )
                    """),
                    {
                        "id": q_id,
                        "qid": q.id,
                        "title": q.title,
                        "description": q.description,
                        "difficulty": difficulty,
                        "topics": [topic],
                        "input_format": "",
                        "output_format": "",
                        "constraints": "",
                        "boilerplate": q.boilerplate,
                        "public_test_cases": [
                            {"input": tc.input, "expected_output": tc.expected_output}
                            for tc in q.public_test_cases
                        ],
                        "private_test_cases": [
                            {"input": tc.input, "expected_output": tc.expected_output}
                            for tc in q.private_test_cases
                        ],
                        "ai_model": settings.AI_MODEL,
                        "ai_prompt": topic,
                        "created_by": assigned_by,
                    },
                )

                # Link question to job
                await db.execute(
                    text("""
                        INSERT INTO job_questions (id, job_id, question_id, assigned_by, position, created_at)
                        VALUES (:id, :job_id, :question_id, :assigned_by, :position, now())
                        ON CONFLICT (job_id, question_id) DO NOTHING
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "job_id": job_id,
                        "question_id": q_id,
                        "assigned_by": assigned_by,
                        "position": len(questions_to_assign) + 1,
                    },
                )

                # Add to assignment list as a mock row
                questions_to_assign.append({
                    "id": q_id,
                    "title": q.title,
                    "difficulty": difficulty,
                    "boilerplate": q.boilerplate,
                    "public_test_cases": [
                        {"input": tc.input, "expected_output": tc.expected_output}
                        for tc in q.public_test_cases
                    ],
                    "private_test_cases": [
                        {"input": tc.input, "expected_output": tc.expected_output}
                        for tc in q.private_test_cases
                    ],
                })

            except Exception as e:
                print(f"Warning: AI question generation failed: {e}")
                continue

    # 4. Assign questions to candidate (random order)
    random.shuffle(questions_to_assign)
    assigned = []

    for pos, q in enumerate(questions_to_assign[:num_questions], 1):
        # Handle both Row objects and dicts
        if hasattr(q, '_mapping'):
            q_id = str(q.id)
            public_cases = q.public_test_cases
            title = q.title
            difficulty = q.difficulty
            boilerplate = q.boilerplate
        else:
            q_id = q["id"]
            public_cases = q["public_test_cases"]
            title = q["title"]
            difficulty = q["difficulty"]
            boilerplate = q["boilerplate"]

        await db.execute(
            text("""
                INSERT INTO candidate_questions (
                    id, candidate_id, job_id, question_id,
                    public_snapshot, position, assigned_at
                ) VALUES (
                    :id, :candidate_id, :job_id, :question_id,
                    :public_snapshot, :position, now()
                )
                ON CONFLICT (candidate_id, question_id) DO NOTHING
            """),
            {
                "id": str(uuid.uuid4()),
                "candidate_id": candidate_id,
                "job_id": job_id,
                "question_id": q_id,
                "public_snapshot": public_cases,
                "position": pos,
            },
        )

        # Update times_used
        await db.execute(
            text("UPDATE questions SET times_used = times_used + 1 WHERE id = :id"),
            {"id": q_id},
        )

        assigned.append({
            "id": q_id,
            "title": title,
            "difficulty": difficulty,
            "boilerplate": boilerplate,
            "public_test_cases": public_cases,
            "position": pos,
        })

    await db.commit()
    return assigned
