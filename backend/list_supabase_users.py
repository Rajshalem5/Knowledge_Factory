#!/usr/bin/env python3
"""
List existing Supabase Auth users (requires service role key).
"""

import asyncio
import httpx
import json

# Note: This would require the service role key, which we don't have access to
# Let me try a different approach - check if we can get session info

SUPABASE_URL = "https://nwlfflecgukgfgdcyihk.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53bGZmbGVjZ3VrZ2ZnZGN5aWhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0NDgzOTAsImV4cCI6MjA5MzAyNDM5MH0.9uzSUVWhpHDSVcm9ugxAv4KjyAJkHftGDTgn7XSGpwc"

async def check_auth_status():
    """Check auth status and available endpoints."""
    
    async with httpx.AsyncClient() as client:
        # Check if we can get user info
        print("Checking Supabase Auth endpoints...")
        
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
            }
        )
        
        print(f"User endpoint status: {response.status_code}")
        print(f"User endpoint response: {response.text}")

if __name__ == "__main__":
    asyncio.run(check_auth_status())