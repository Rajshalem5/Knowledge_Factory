"""Quick test: verify enhanced filtering (target_statuses) works."""
import asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

async def test_enhanced():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        # Login as HR
        r = await client.post('/api/auth/login', json={
            'email': 'hr@knowledgefactory.com',
            'password': 'Hr@12345',
        })
        hr_token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {hr_token}'}

        # Test 1: Default screening (APPLIED only)
        r = await client.post('/api/screening/run', headers=headers)
        print(f"Default screening: {r.status_code} {r.json()}")
        assert r.status_code == 200

        # Test 2: Screening with target_statuses
        r = await client.post('/api/screening/run?target_statuses=APPLIED,ROUND1_REVIEW', headers=headers)
        print(f"Multi-status screening: {r.status_code} {r.json()}")
        assert r.status_code == 200

        # Test 3: Screening with invalid status
        r = await client.post('/api/screening/run?target_statuses=INVALID_STATUS', headers=headers)
        print(f"Invalid status: {r.status_code} {r.json()}")
        assert r.status_code == 422

        # Test 4: Screening with extra filters + target_statuses
        r = await client.post('/api/screening/run?target_statuses=APPLIED&branch=CSE&cgpa_min=7.0', headers=headers)
        print(f"Filtered + status: {r.status_code} {r.json()}")
        assert r.status_code == 200

        print("\n✓ Enhanced filtering tests passed!")
        return True

if __name__ == '__main__':
    import sys
    success = asyncio.run(test_enhanced())
    if not success:
        sys.exit(1)
