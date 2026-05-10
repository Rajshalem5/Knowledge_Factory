"""Debug funnel filter properly with all models loaded."""
import asyncio

# Must import all models first so SQLAlchemy discovers them
import app.features.auth.models
import app.features.candidates.models
import app.features.hiring_cycles.models
import app.features.assessments.models
import app.features.proctoring.models
import app.features.interviews.models
import app.features.audit.models
import app.features.analytics.models

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

asyncio.run(main())
