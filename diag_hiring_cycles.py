#!/usr/bin/env python3
"""Diagnose hiring cycles 500 error"""
import sys
sys.path.insert(0, "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")
import asyncio
from sqlalchemy import select, text
from app.database import async_session_factory

async def main():
    async with async_session_factory() as session:
        # Check hiring cycles table
        r = await session.execute(text("PRAGMA table_info(hiring_cycles)"))
        cols = r.fetchall()
        print("Hiring cycles columns:")
        for c in cols:
            print(f"  {c}")
        
        r = await session.execute(text("SELECT * FROM hiring_cycles"))
        rows = r.fetchall()
        print(f"\nHiring cycles rows ({len(rows)}):")
        for row in rows:
            print(f"  {dict(row._mapping)}")
        
        # Check if start_date or end_date is NULL
        if rows:
            for row in rows:
                d = dict(row._mapping)
                for k in ['start_date', 'end_date']:
                    if d.get(k) is None:
                        print(f"  ⚠️  NULL found in {k} for cycle {d.get('id')}")

asyncio.run(main())
