import asyncio
from app.database import async_session_factory
from sqlalchemy import text

CAND_ID = "5970a536-7bd7-454d-8156-963ea04ffbab"

async def reset():
    async with async_session_factory() as db:
        # Delete proctoring evidence
        await db.execute(text(f"DELETE FROM proctoring_evidence WHERE session_id IN (SELECT id FROM proctoring_sessions WHERE user_id='{CAND_ID}')"))
        # Delete risk snapshots
        await db.execute(text(f"DELETE FROM risk_snapshots WHERE session_id IN (SELECT id FROM proctoring_sessions WHERE user_id='{CAND_ID}')"))
        # Delete proctoring events
        await db.execute(text(f"DELETE FROM proctoring_events WHERE session_id IN (SELECT id FROM proctoring_sessions WHERE user_id='{CAND_ID}')"))
        # Delete proctoring sessions
        await db.execute(text(f"DELETE FROM proctoring_sessions WHERE user_id='{CAND_ID}'"))
        # Delete submissions
        await db.execute(text(f"DELETE FROM submissions WHERE assessment_id IN (SELECT id FROM assessments WHERE candidate_id='{CAND_ID}')"))
        # Delete scores
        await db.execute(text(f"DELETE FROM scores WHERE candidate_id='{CAND_ID}'"))
        # Delete the completed assessment
        await db.execute(text(f"DELETE FROM assessments WHERE candidate_id='{CAND_ID}'"))
        # Reset candidate status
        await db.execute(text(f"UPDATE candidates SET status='ROUND1_PASSED' WHERE id='{CAND_ID}'"))
        await db.commit()
        print("Reset complete - candidate can start fresh ROUND_2")

asyncio.run(reset())
