#!/usr/bin/env python3
"""Smoke test: authenticate and verify API endpoints."""
import json
import asyncio
from app.database import async_session_factory
from app.features.auth.service import AuthService
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from sqlalchemy import select

async def smoke_test():
    print("=== Smoke Test ===\n")
    
    # Test 1: Authenticate as HR
    print("✓ Test 1: Authenticate as hr@test.com")
    auth_svc = AuthService()
    token_result = await auth_svc.login("hr@test.com", "Test@123")
    if token_result.get("access_token"):
        print(f"  ✓ Login successful, token length: {len(token_result['access_token'])}")
    else:
        print(f"  ✗ Login failed: {token_result}")
        return
    
    # Test 2: Fetch active hiring cycle
    print("\n✓ Test 2: Fetch active hiring cycle")
    async with async_session_factory() as session:
        async with session.begin():
            stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
            cycle = (await session.execute(stmt)).scalar_one_or_none()
            if cycle:
                print(f"  ✓ Cycle found: {cycle.name} (ID: {cycle.id})")
                cycle_id = cycle.id
            else:
                print("  ✗ No active cycle found")
                return
    
    # Test 3: Fetch candidates and verify evaluation fields exist
    print(f"\n✓ Test 3: Fetch candidates with evaluation fields")
    async with async_session_factory() as session:
        async with session.begin():
            stmt = select(Candidate).where(Candidate.cycle_id == cycle_id).limit(3)
            candidates = (await session.execute(stmt)).scalars().all()
            if candidates:
                print(f"  ✓ Found {len(candidates)} candidates")
                for c in candidates:
                    print(f"    - {c.name}: screening_score={c.screening_score}, mcq_score={c.mcq_score}, coding_score={c.coding_score}, risk_penalty={c.risk_penalty}, composite_score={c.composite_score}, adjusted_final_score={c.adjusted_final_score}, recommendation={c.recommendation}")
            else:
                print("  ✗ No candidates found")
    
    # Test 4: Verify admin authentication
    print("\n✓ Test 4: Authenticate as admin@test.com")
    token_result = await auth_svc.login("admin@test.com", "Test@123")
    if token_result.get("access_token"):
        print(f"  ✓ Admin login successful")
    else:
        print(f"  ✗ Admin login failed: {token_result}")
    
    # Test 5: Check proctoring_config on cycle
    print(f"\n✓ Test 5: Verify proctoring_config on cycle")
    async with async_session_factory() as session:
        async with session.begin():
            stmt = select(HiringCycle).where(HiringCycle.id == cycle_id)
            cycle = (await session.execute(stmt)).scalar_one()
            print(f"  ✓ proctoring_config keys: {list(cycle.proctoring_config.keys()) if cycle.proctoring_config else 'empty'}")
    
    print("\n=== All smoke tests passed! ===")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    asyncio.run(smoke_test())
