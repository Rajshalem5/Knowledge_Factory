"""Full end-to-end pipeline test — fully self-contained.

Uses a temporary SQLite file to avoid polluting the dev database.
"""
import asyncio
import os
import tempfile
import uuid
from datetime import date
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import Base, get_db
from app.core.security import hash_password
from app.features.auth.models import User
from app.features.hiring_cycles.models import HiringCycle
from app.features.candidates.models import Candidate
from app.features.assessments.models import Assessment, Submission, Score
from app.features.proctoring.models import ProctoringRecord
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog

# Use a temporary file so both sync and async engines share the same database
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"kf_e2e_test_{uuid.uuid4().hex[:8]}.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
SYNC_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def seed_database():
    """Create tables and seed with HR user + active hiring cycle."""
    sync_engine = create_engine(SYNC_DATABASE_URL)
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    print("[seed] Tables created.")

    async with TestSessionFactory() as session:
        async with session.begin():
            hr = User(
                email="hr@knowledgefactory.com",
                password_hash=hash_password("Hr@12345"),
                name="HR Manager",
                role="HR",
                status="ACTIVE",
            )
            session.add(hr)

            admin = User(
                email="admin@knowledgefactory.io",
                password_hash=hash_password("Admin@12345"),
                name="Admin User",
                role="SUPERADMIN",
                status="ACTIVE",
            )
            session.add(admin)

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
    async with TestSessionFactory() as session:
        async with session.begin():
            from sqlalchemy import select
            stmt = select(User).where(User.email == "hr@knowledgefactory.com")
            found = (await session.execute(stmt)).scalar_one_or_none()
            print(f"[seed] HR user: {'OK' if found else 'MISSING'}")
            stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
            found = (await session.execute(stmt)).scalar_one_or_none()
            print(f"[seed] Active cycle: {'OK' if found else 'MISSING'}")

    print("[seed] Database ready.\n")


async def test_full_pipeline():
    try:
        await seed_database()

        # Override get_db to use our isolated test database
        async def _override_get_db():
            async with TestSessionFactory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        app.dependency_overrides[get_db] = _override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
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

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"2. Get my profile: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            candidate_id = r.json()['id']
            print(f"   Candidate ID: {candidate_id}")
            assert r.json()['status'] == 'APPLIED', f"Expected APPLIED, got {r.json()['status']}"
            print(f"   Status: {r.json()['status']} / display: {r.json()['display_status']}")

            r = await client.post('/api/auth/login', json={
                'email': 'hr@knowledgefactory.com',
                'password': 'Hr@12345',
            })
            print(f"3. HR Login: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            hr_token = r.json()['access_token']

            r = await client.post('/api/screening/run', headers={'Authorization': f'Bearer {hr_token}'})
            print(f"4. Run screening: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            result = r.json()
            print(f"   Result: {result}")
            assert result['screened'] >= 1, f"Expected >= 1 screened, got {result['screened']}"
            assert result['passed'] >= 1, f"Expected >= 1 passed, got {result['passed']}"

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"5. My profile after screening: {r.status_code}")
            assert r.status_code == 200
            print(f"   Status: {r.json()['status']}")
            assert r.json()['status'] == 'ROUND1_PASSED', f"Expected ROUND1_PASSED, got {r.json()['status']}"

            r = await client.post('/api/assessment/start',
                                  headers={'Authorization': f'Bearer {candidate_token}'},
                                  json={'round': 'ROUND_2'})
            print(f"6. Start assessment: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            assessment = r.json()
            assessment_id = assessment['id']
            print(f"   Assessment ID: {assessment_id}")
            assert assessment['status'] == 'IN_PROGRESS'

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"7. Status after assessment start: {r.json()['status']}")
            assert r.json()['status'] == 'ROUND2_IN_PROGRESS', f"Expected ROUND2_IN_PROGRESS, got {r.json()['status']}"

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

            r = await client.post(f'/api/assessment/{assessment_id}/complete',
                                  headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"9. Complete assessment: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            assert r.json()['status'] == 'COMPLETED', f"Expected COMPLETED, got {r.json()['status']}"
            print(f"   Assessment status: {r.json()['status']}")

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"10. Status after complete: {r.json()['status']}")
            assert r.json()['status'] == 'ROUND2_PASSED', f"Expected ROUND2_PASSED, got {r.json()['status']}"

            r = await client.post('/api/screening/run?branch=CSE&cgpa_min=7.0',
                                  headers={'Authorization': f'Bearer {hr_token}'})
            print(f"11. Screening with filters: {r.status_code}")
            assert r.status_code == 200
            print(f"    Result: {r.json()}")

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

            r = await client.get('/api/analytics/funnel?branch=CSE',
                                  headers={'Authorization': f'Bearer {hr_token}'})
            print(f"13. Funnel with branch filter: {r.status_code}")
            assert r.status_code == 200
            print(f"    Funnel: {r.json()}")

            r = await client.post('/api/assessment/start',
                                  headers={'Authorization': f'Bearer {candidate_token}'},
                                  json={'round': 'ROUND_3'})
            print(f"14. Start ROUND_3 assessment: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            r3_assessment = r.json()
            r3_assessment_id = r3_assessment['id']
            print(f"    Assessment ID: {r3_assessment_id}, Status: {r3_assessment['status']}")
            assert r3_assessment['round'] == 'ROUND_3'
            assert r3_assessment['status'] == 'IN_PROGRESS'

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"15. Status after ROUND_3 start: {r.json()['status']}")
            assert r.json()['status'] == 'ROUND3_IN_PROGRESS', f"Expected ROUND3_IN_PROGRESS, got {r.json()['status']}"

            r = await client.post('/api/assessment/submit-section',
                                  headers={'Authorization': f'Bearer {candidate_token}'},
                                  json={
                                      'assessment_id': r3_assessment_id,
                                      'section': 'CODING',
                                      'content': {'code': 'print("round3")', 'problemId': 'r2_p1'},
                                      'time_spent_seconds': 90,
                                  })
            print(f"16. Submit ROUND_3 section: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            print(f"    Result: {r.json()}")

            r = await client.post(f'/api/assessment/{r3_assessment_id}/complete',
                                  headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"17. Complete ROUND_3: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            assert r.json()['status'] == 'COMPLETED'
            print(f"    Assessment status: {r.json()['status']}")

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"    Candidate status: {r.json()['status']}")
            assert r.json()['status'] == 'ROUND3_PASSED', f"Expected ROUND3_PASSED, got {r.json()['status']}"

            r = await client.patch(f'/api/candidates/{candidate_id}/status',
                                   headers={'Authorization': f'Bearer {hr_token}'},
                                   json={'status': 'INTERVIEW_SCHEDULED'})
            print(f"18. Schedule interview: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            assert r.json()['status'] == 'INTERVIEW_SCHEDULED'
            print(f"    Status: {r.json()['status']}")

            r = await client.patch(f'/api/candidates/{candidate_id}/status',
                                   headers={'Authorization': f'Bearer {hr_token}'},
                                   json={'status': 'INTERVIEW_COMPLETED'})
            print(f"19. HR marks interview completed: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            assert r.json()['status'] == 'INTERVIEW_COMPLETED'
            print(f"    Status: {r.json()['status']}")

            r = await client.post(f'/api/selection/candidates/{candidate_id}/select',
                                  headers={'Authorization': f'Bearer {hr_token}'})
            print(f"20. Select candidate: {r.status_code}")
            assert r.status_code == 200, f"FAIL: {r.text[:200]}"
            data = r.json()
            assert data['status'] == 'SELECTED'
            print(f"    Result: {data}")

            r = await client.get('/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
            print(f"    Final status: {r.json()['status']}")
            assert r.json()['status'] == 'SELECTED', f"Expected SELECTED, got {r.json()['status']}"

            print("\n✓ FULL PIPELINE PASSED — All 20 steps OK! (APPLIED → SELECTED)")
            return True
    finally:
        app.dependency_overrides.pop(get_db, None)
        # Clean up temp file
        if os.path.exists(TEST_DB_PATH):
            os.unlink(TEST_DB_PATH)


if __name__ == '__main__':
    import sys
    success = asyncio.run(test_full_pipeline())
    if not success:
        sys.exit(1)
