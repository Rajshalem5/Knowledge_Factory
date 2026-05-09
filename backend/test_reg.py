"""Test registration with JSON body."""
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        resp = await ac.post('/api/auth/register', json={
            'name': 'Login Test Candidate',
            'email': 'login@test.com',
            'password': 'Candidate@123',
            'college': 'Test College',
            'branch': 'IT',
            'cgpa': 9.0,
            'passed_out_year': 2026,
        })
        print(f'Status: {resp.status_code}')
        print(f'Body: {resp.text}')

asyncio.run(test())
