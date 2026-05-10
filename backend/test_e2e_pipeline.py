"""Full end-to-end pipeline test — fully self-contained.

Creates tables, seeds data, then runs the full screening→assessment flow.
"""
import asyncio
import uuid
from datetime import date
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select

from app.main import app
from app.database import Base, async_session_factory
from app.core.security import hash_password
from app.features.auth.models import User
from app.features.hiring_cycles.models import HiringCycle
from app.features.candidates.models import Candidate
from app.features.assessments.models import Assessment, Submission, Score
from app.features.proctoring.models import ProctoringRecord
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog


async def seed_database():
    """Create tables and seed with HR user + active hiring cycle."""
    # Create tables synchronously
    sync_engine = create_engine("sqlite:///./knowledge_factory.db")
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    print("[seed] Tables created.")

    async with async_session_factory() as session:
        async with session.begin():
            # Seed HR user
            hr = User(
                email="hr@knowledgefactory.com",
                password_hash=hash_password("Hr@12345"),
                name="HR Manager",
                role="HR",
                status="ACTIVE",
            )
            session.add(hr)

            # Seed admin user
            admin = User(
                email="admin@knowledgefactory.io",
                password_hash=hash_password("Admin@12345"),
                name="Admin User",
                role="SUPERADMIN",
                status="ACTIVE",
            )
            session.add(admin)

            # Seed active hiring cycle
            cycle = HiringCycle(
                name="Summer Internship 2026",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                status="ACTIVE",
                eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE", "IT", "EEE"]},
            )
            session.add(cycle)
            await session.flush()
            print(f"[seed] Active hiring cycle: {cycle.id}")

    # Verify
    async with async_session_factory() as session:
        async with session.begin():
            stmt = select(User).where(User.email == "hr@knowledgefactory.com")
            found = (await session.execute(stmt)).scalar_one_or_none()
            print(f"[seed] HR user: {'OK' if found else 'MISSING'}")
            stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
            found = (await session.execute(stmt)).scalar_one_or_none()
            print(f"[seed] Active cycle: {'OK' if found else 'MISSING'}")

    print("[seed] Database ready.\n")


async def test_full_pipeline():
    await seed_database()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        # ── Step 1: Register a new candidate ───────────────────────
        email = f"e2e-{uuid.uuid4().hex[:8]}@test.com"
        r = await client.post('/api/auth/register', json={
            'name': 'E2E Test Candidate',
            'email': email,
            'password': 'Candidate@123',
            'college': 'Test University',
            'branch': 'CSE',
            'cgpa': 8.0,
            'passed_out_year': 2026,
            'language_choice': 'python',
        })
        print(f"1. Register: {r.status_code}")
        assert r.status_code == 201, f"FAIL: {r.text[:200]}"
        candidate_token = r.json()['access_token']
        assert candidate_token, "No access token returned"

        # ── Step 2: Get candidate profile ──────────────────────────
        r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
        print(f"2. Get my profile: {r.status_code}")
        assert r.status_code == 200, f"FAIL: {r.text[:200]}"
        candidate_id = r.json()['id']
        print(f"   Candidate ID: {candidate_id}")
        assert r.json()['status'] == 'APPLIED', f"Expected APPLIED, got {r.json()['status']}"
        print(f"   Status: {r.json()['status']} / display: {r.json()['display_status']}")

        # ── Step 3: Login as HR ────────────────────────────────────
        r = await client.post('/api/auth/login', json={
            'email': 'hr@knowledgefactory.com',
            'password': 'Hr@12345',
        })
        print(f"3. HR Login: {r.status_code}")
        assert r.status_code == 200, f"FAIL: {r.text[:200]}"
        hr_token = r.json()['access_token']

        # ── Step 4: Run screening ──────────────────────────────────
        r = await client.post('/api/screening/run', headers={'Authorization': f'Bearer {hr_token}'})
        print(f"4. Run screening: {r.status_code}")
        assert r.status_code == 200, f"FAIL: {r.text[:200]}"
        result = r.json()
        print(f"   Result: {result}")
        assert result['screened'] >= 1, f"Expected >= 1 screened, got {result['screened']}"
        assert result['passed'] >= 1, f"Expected >= 1 passed, got {result['passed']}"

        # ── Step 5: Check candidate status after screening ─────────
        r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
        print(f"5. My profile after screening: {r.status_code}")
        assert r.status_code == 200
        print(f"   Status: {r.json()['status']}")
        assert r.json()['status'] == 'ROUND1_PASSED', f"Expected ROUND1_PASSED, got {r.json()['status']}"

        # ── Step 6: Start assessment (ROUND_2) ──────────────────────
        r = await client.post('/api/assessment/start',
                              headers={'Authorization': f'Bearer {candidate_token}'},
                              json={'round': 'ROUND_2'})
        print(f"6. Start assessment: {r.status_code}")
        assert r.status_code == 200, f"FAIL: {r.text[:200]}"
        assessment = r.json()
        assessment_id = assessment['id']
        print(f"   Assessment ID: {assessment_id}")
        print(f"   Round: {assessment['round']}, Status: {assessment['status']}")
        assert assessment['status'] == 'IN_PROGRESS'

        # ── Step 7: Verify candidate status after starting ─────────
        r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
        print(f"7. Status after assessment start: {r.json()['status']}")
        assert r.json()['status'] == 'ROUND2_IN_PROGRESS', f"Expected ROUND2_IN_PROGRESS, got {r.json()['status']}"

        # ── Step 8: Submit section ─────────────────────────────────
        r = await client.post('/api/assessment/submit-section',
                              headers={'Authorization': f'Bearer {candidate_token}'},
                              json={
                                  'assessment_id': assessment_id,
                                  'section': 'CODING',
                                  'content': {'code': 'print("hello")', 'problemId': 'r2_p1'},
                                  'time_spent_seconds': 120,
                              })
        print(f"8. Submit section: {r.status_code}")
        assert r.status_code == 200, f"FAIL: {r.text[:200]}"
        print(f"   Result: {r.json()}")
        assert 'submission_id' in r.json()

        # ── Step 9: Complete assessment ────────────────────────────
        r = await client.post(f'/api/assessment/{assessment_id}/complete',
                              headers={'Authorization': f'Bearer {candidate_token}'})
        print(f"9. Complete assessment: {r.status_code}")
        assert r.status_code == 200, f"FAIL: {r.text[:200]}"
        assert r.json()['status'] == 'COMPLETED', f"Expected COMPLETED, got {r.json()['status']}"
        print(f"   Assessment status: {r.json()['status']}")

        # ── Step 10: Verify candidate advanced ─────────────────────
        r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
        print(f"10. Status after complete: {r.json()['status']}")
        assert r.json()['status'] == 'ROUND2_PASSED', f"Expected ROUND2_PASSED, got {r.json()['status']}"

        # ── Step 11: Run screening with extra filters ──────────────
        r = await client.post('/api/screening/run?branch=CSE&cgpa_min=7.0',
                              headers={'Authorization': f'Bearer {hr_token}'})
        print(f"11. Screening with filters: {r.status_code}")
        assert r.status_code == 200
        print(f"    Result: {r.json()}")

        # ── Step 12: Check pipeline stats ──────────────────────────
        r = await client.get('/api/screening/pipeline-stats',
                              headers={'Authorization': f'Bearer {hr_token}'})
        print(f"12. Pipeline stats: {r.status_code}")
        assert r.status_code == 200
        stats = r.json()['stats']
        print(f"    Stats keys: {list(stats.keys())}")
        assert 'APPLIED' in stats
        assert 'ROUND1_PASSED' in stats
        assert 'ROUND2_IN_PROGRESS' in stats
        assert 'ROUND2_PASSED' in stats

        # ── Step 13: Funnel with extra filters ─────────────────────
        r = await client.get('/api/analytics/funnel?branch=CSE',
                              headers={'Authorization': f'Bearer {hr_token}'})
        print(f"13. Funnel with branch filter: {r.status_code}")
        assert r.status_code == 200
        print(f"    Funnel: {r.json()}")

        print("\n✓ FULL PIPELINE PASSED — All 13 steps OK!")
        return True


if __name__ == '__main__':
    import sys
    success = asyncio.run(test_full_pipeline())
    if not success:
        sys.exit(1)
