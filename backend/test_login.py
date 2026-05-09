"""Debug admin login."""
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        # Try login
        resp = await ac.post('/api/auth/login', json={
            'email': 'admin@knowledgefactory.io',
            'password': 'Admin@12345',
        })
        print(f'Login status: {resp.status_code}')
        print(f'Login body: {resp.text}')

        if resp.status_code == 200:
            token = resp.json()['access_token']
            me_resp = await ac.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
            print(f'Me status: {me_resp.status_code}')
            print(f'Me body: {me_resp.text}')

asyncio.run(test())
