#!/usr/bin/env python3
"""Reproduce the hiring cycle error directly via SQLAlchemy"""
import sys, json, asyncio
sys.path.insert(0, "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")

import os
os.chdir("/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")

# Need to import after setting up the environment
from app.database import async_session_factory
from sqlalchemy import select, text
from app.features.hiring_cycles.models import HiringCycle

async def main():
    async with async_session_factory() as session:
        # First check what columns the ORM thinks hiring_cycles has
        stmt = select(HiringCycle).limit(1)
        try:
            res = await session.execute(stmt)
            cycle = res.scalars().first()
            if cycle:
                print(f"Cycle loaded: id={cycle.id}")
                print(f"  name: {cycle.name}")
                print(f"  start_date: {cycle.start_date}")
                print(f"  end_date: {cycle.end_date}")
                print(f"  status: {cycle.status} (type: {type(cycle.status).__name__})")
                print(f"  eligibility_config: {cycle.eligibility_config} (type: {type(cycle.eligibility_config).__name__})")
                print(f"  assessment_config: {cycle.assessment_config}")
                print(f"  proctoring_config: {cycle.proctoring_config}")
                print(f"  created_by: {cycle.created_by}")
                print(f"  created_at: {cycle.created_at}")
                print(f"  updated_at: {cycle.updated_at}")
                
                # Now test the actual serialization that the route does
                result = {
                    "id": str(cycle.id),
                    "name": cycle.name,
                    "start_date": cycle.start_date.isoformat(),
                    "end_date": cycle.end_date.isoformat(),
                    "status": cycle.status.value,
                    "eligibility_config": cycle.eligibility_config,
                    "assessment_config": cycle.assessment_config,
                    "proctoring_config": cycle.proctoring_config,
                    "created_at": cycle.created_at.isoformat(),
                }
                print(f"\nSerialized: {json.dumps(result, indent=2, default=str)[:500]}")
            else:
                print("No hiring cycles found in DB")
                # Let's check raw
                r = await session.execute(text("SELECT * FROM hiring_cycles"))
                raw = r.fetchall()
                print(f"Raw rows: {len(raw)}")
                for row in raw:
                    print(f"  {dict(row._mapping)}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(main())
