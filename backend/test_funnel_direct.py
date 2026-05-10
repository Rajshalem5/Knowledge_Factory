"""Debug funnel filter: test via direct app import."""
import asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

async def main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        r = await client.post('/api/auth/login', json={
            'email': 'hr@knowledgefactory.com', 'password': 'Hr@12345'
        })
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test funnel with email filter directly
        r = await client.get('/api/candidates?email=applied@test.com', headers=headers)
        print(f'Candidates with email filter: total={r.json()["pagination"]["total"]}')
        
        r = await client.get('/api/analytics/funnel?email=applied@test.com', headers=headers)
        print(f'Funnel (email=applied@test.com): {r.json()}')
        
        r = await client.get('/api/analytics/funnel?branch=CIVIL', headers=headers)
        print(f'Funnel (branch=CIVIL): {r.json()}')
        
        # Now test directly from the analytics service
        from app.database import TestSessionFactory
        from app.features.analytics.service import AnalyticsService
        
        async with TestSessionFactory() as session:
            service = AnalyticsService(session)
            result = await service.get_hiring_funnel(email='applied@test.com')
            print(f'Direct service call (email=applied@test.com): {result}')
            
            result = await service.get_hiring_funnel()
            print(f'Direct service call (no filters): {result}')

asyncio.run(main())
