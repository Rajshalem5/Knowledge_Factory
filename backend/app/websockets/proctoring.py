import asyncio
import logging
import base64
import os
import uuid
import time
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.database import get_db, async_session_factory
from app.config import settings
from app.features.proctoring.service import ProctoringService
from app.features.proctoring.schemas import ProctoringEventCreate
from app.features.proctoring.models import ProctoringEvidence, ProctoringSession

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure screenshots directory exists
os.makedirs(settings.SCREENSHOT_STORAGE_PATH, exist_ok=True)

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

manager = ConnectionManager()

def verify_ws_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.PROCTORING_JWT_SECRET, algorithms=["HS256"])
        session_id = payload.get("session_id")
        if not session_id:
            raise ValueError("Invalid token: no session_id")
        return session_id
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")

@router.websocket("/ws/proctor/{session_id}")
async def proctoring_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...)
):
    try:
        verified_session_id = verify_ws_token(token)
        if verified_session_id != session_id:
            await websocket.close(code=4003)
            return
    except ValueError as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=4003)
        return

    await manager.connect(websocket, session_id)
    logger.info(f"WebSocket connected for session: {session_id}")

    # Track time to take periodic snapshots
    last_snapshot_time = time.time()
    snapshot_interval = 15.0  # seconds

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            async with async_session_factory() as db:
                service = ProctoringService(db)
                
                if msg_type == "video":
                    # Periodic snapshot check
                    current_time = time.time()
                    if current_time - last_snapshot_time >= snapshot_interval:
                        last_snapshot_time = current_time
                        frame = data.get("frame")
                        if frame:
                            filepath = save_screenshot(frame, session_id, "periodic_snapshot")
                            if filepath:
                                await record_evidence(db, session_id, "PERIODIC_SNAPSHOT", filepath)
                
                elif msg_type == "violation":
                    # Received frontend violation (tab switch, etc.)
                    event_type = data.get("event_type", "UNKNOWN")
                    # Send to proctoring service
                    evt = ProctoringEventCreate(
                        session_id=session_id,
                        event_id=str(uuid.uuid4()),
                        timestamp=datetime.now(timezone.utc),
                        event_type=event_type,
                        severity="MEDIUM" if event_type in ["TAB_SWITCH", "WINDOW_BLUR"] else "HIGH",
                        risk_score=0.0, # Service computes actual score
                        metadata={"details": f"Frontend reported {event_type}"}
                    )
                    saved_evt = await service.record_event(evt)
                    
                    # Also notify frontend of updated risk
                    session = await service.get_session(session_id)
                    if session:
                        await manager.send_message({
                            "type": "risk_update",
                            "risk_score": session.final_risk_score,
                            "risk_level": "HIGH" if session.final_risk_score >= 60 else "MEDIUM" if session.final_risk_score >= 20 else "LOW"
                        }, session_id)
                        
                        if session.status == "TERMINATED":
                            await manager.send_message({
                                "type": "termination",
                                "reason": session.terminated_reason
                            }, session_id)
                            
                # TODO: We can add actual computer vision inference here on 'frame'
                # For now, we rely on the frontend sending 'violation' events or we take periodic snapshots.
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


def save_screenshot(base64_data: str, session_id: str, suffix: str) -> str | None:
    try:
        image_data = base64.b64decode(base64_data)
        filename = f"{session_id}_{int(time.time())}_{suffix}.jpg"
        filepath = os.path.join(settings.SCREENSHOT_STORAGE_PATH, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)
        return filepath
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return None

async def record_evidence(db: AsyncSession, session_id: str, event_type: str, filepath: str):
    try:
        evidence = ProctoringEvidence(
            session_id=session_id,
            event_type=event_type,
            screenshot_url=f"/api/proctoring/screenshots/{os.path.basename(filepath)}"
        )
        db.add(evidence)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to record evidence: {e}")
        await db.rollback()
