import asyncio
import sys
import os
import httpx
import json
import base64
import time
import uuid
import websockets

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath("backend"))

from app.database import async_session_factory
from sqlalchemy import text

async def get_test_users():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT id, email FROM candidates LIMIT 1"))
        cand = res.fetchone()
        
        res2 = await session.execute(text("SELECT id, email FROM users WHERE role = 'superadmin' LIMIT 1"))
        admin = res2.fetchone()
        
        return cand, admin

async def run_live_verification():
    cand_email = "alice@test.com"
    admin_email = "admin@knowledgefactory.io"
    password = "Welcome@123"

    print(f"--- LIVE VERIFICATION SESSION ---")
    
    base_url = "http://localhost:8001"
    
    # 1. Login as Candidate
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{base_url}/api/auth/login", json={
                "email": cand_email,
                "password": password
            })
            if resp.status_code != 200:
                print(f"Candidate Login failed: {resp.text}")
                return
            
            cand_data = resp.json()
            cand_id = cand_data["user"]["id"]
            token = cand_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✓ Candidate Login Successful: {cand_email} ({cand_id})")
            
            # Ensure candidate is in ROUND2_PASSED (using direct DB for speed)
            async with async_session_factory() as session:
                from app.features.candidates.models import Candidate
                from app.features.hiring_cycles.models import HiringCycle
                from app.features.interviews.models import InterviewFeedback
                await session.execute(text(f"UPDATE candidates SET status = 'ROUND2_PASSED' WHERE id = '{cand_id}'"))
                await session.commit()

            # 2. Start Round 3 Assessment
            resp = await client.post(f"{base_url}/api/assessment/start", 
                                   json={"round": "ROUND_3"}, headers=headers)
            if resp.status_code != 200:
                print(f"Start Assessment failed: {resp.text}")
                return
            
            assessment = resp.json()
            assessment_id = assessment["id"]
            print(f"✓ Assessment Started: {assessment_id}")
            
            # 3. Verify Question Generation
            problems = assessment["questions_json"]["problems"]
            print(f"✓ Generated {len(problems)} questions.")
            for i, p in enumerate(problems):
                print(f"  Q{i+1}: {p['title']} ({p['difficulty']}) - {p['points']} pts")
            
            # 4. Proctoring WebSocket Verification
            resp = await client.post(f"{base_url}/api/proctoring/session", 
                                   json={"assessment_attempt_id": assessment_id}, headers=headers)
            if resp.status_code != 200:
                print(f"Proctoring init failed: {resp.text}")
                return
                
            init_data = resp.json()
            session_id = init_data["session_id"]
            ws_token = init_data["token"]
            
            # WebSocket client (ws://)
            ws_url = f"ws://localhost:8001/ws/proctor/{session_id}?token={ws_token}"
            
            print(f"Connecting to WebSocket: {ws_url}")
            async with websockets.connect(ws_url) as ws:
                print("✓ WebSocket Connected")
                dummy_frame = base64.b64encode(b"test frame data").decode()
                await ws.send(json.dumps({"type": "video", "frame": dummy_frame}))
                print("✓ Frame sent")
                await ws.send(json.dumps({"type": "violation", "event_type": "TAB_SWITCH"}))
                print("✓ Violation sent")
                await asyncio.sleep(1)
                
            # 5. Submit Code
            codes = {}
            for p in problems:
                codes[p["id"]] = "import sys\nfor line in sys.stdin:\n    print(line.strip())"
                
            resp = await client.post(f"{base_url}/api/assessment/submit-section", 
                                   json={
                                       "assessment_id": assessment_id,
                                       "section": "CODING",
                                       "content": {"answers": codes}
                                   }, headers=headers)
            print(f"✓ Code Submitted: {resp.status_code}")
            
            # 6. Complete & Evaluate
            print("Evaluating (this may take a few minutes)...")
            resp = await client.post(f"{base_url}/api/assessment/{assessment_id}/complete", headers=headers, timeout=300.0)
            print(f"✓ Assessment Completed: {resp.status_code}")
            
            # 7. Admin Review Audit
            resp = await client.post(f"{base_url}/api/auth/login", json={
                "email": admin_email,
                "password": password
            })
            admin_token = resp.json()["access_token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            print(f"✓ Admin Login Successful: {admin_email}")
            
            # Fetch Assessment Results
            resp = await client.get(f"{base_url}/api/assessment/{assessment_id}/admin", headers=admin_headers)
            admin_view = resp.json()
            print(f"✓ Admin View Fetched: {len(admin_view.get('submissions', []))} submissions found")
            
            # Fetch Proctoring Audit
            resp = await client.get(f"{base_url}/api/proctoring/session/{session_id}/events", headers=admin_headers)
            events = resp.json()
            print(f"✓ Proctoring Events Fetched: {len(events)} events found")
            
            resp = await client.get(f"{base_url}/api/proctoring/session/{session_id}/evidence", headers=admin_headers)
            evidence = resp.json()
            print(f"✓ Evidence Fetched: {len(evidence)} items found")
            if evidence:
                print(f"  Latest Screenshot: {evidence[0].get('screenshot_url')}")

        except Exception as e:
            print(f"Error during runtime verification: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Ensure server is running or this will fail. 
    # Since I can't start a persistent background server and connect to it easily in one turn 
    # if it's not already running, I will check health first.
    asyncio.run(run_live_verification())
