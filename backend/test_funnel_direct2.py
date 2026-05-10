"""Debug funnel filter: test analytics service directly with the live DB."""
import asyncio
from app.database import async_session_factory
from app.features.analytics.service import AnalyticsService

async def main():
    async with async_session_factory() as session:
        service = AnalyticsService(session)
        
        # Without filters
        result = await service.get_hiring_funnel()
        print(f'No filters: {result}')
        
        # With email filter
        result = await service.get_hiring_funnel(email='applied@test.com')
        print(f'email=applied@test.com: {result}')
        
        # With branch filter
        result = await service.get_hiring_funnel(branch='CIVIL')
        print(f'branch=CIVIL: {result}')
        
        # With search filter
        result = await service.get_hiring_funnel(search='alice')
        print(f'search=alice: {result}')

asyncio.run(main())
