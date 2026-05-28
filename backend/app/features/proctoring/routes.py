"""Proctoring routes."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CANDIDATE_ONLY, get_current_user
from app.features.proctoring.schemas import (
    ProctoringSessionCreate,
    ProctoringSessionResponse,
    ProctoringEventCreate,
    ProctoringEventResponse
)
from app.features.proctoring.service import ProctoringService
from app.core.security import create_access_token, create_proctoring_token
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/session", response_model=ProctoringSessionResponse)
async def initialize_proctoring_session(
    data: ProctoringSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(CANDIDATE_ONLY)
):
    """
    Initialize a proctoring session and generate a WS token.
    """
    service = ProctoringService(db)
    session = await service.initialize_session(str(current_user.id), data)
    
    # Generate a specialized JWT token for the AI Proctoring Service
    expires_delta = timedelta(hours=2) # Sessions usually don't last longer
    expires_at = datetime.now(timezone.utc) + expires_delta
    
    # Use specialized token creation for proctoring
    token = create_proctoring_token(
        subject=str(current_user.id),
        session_id=session.id,
        expires_delta=expires_delta
    )
    
    # Use environment variable for the AI service WS URL
    ws_url = f"{settings.PROCTORING_SERVICE_WS_URL}/ws/proctor/{session.id}"
    
    return ProctoringSessionResponse(
        session_id=session.id,
        ws_url=ws_url,
        token=token,
        expires_at=expires_at
    )


@router.post("/webhook/event", status_code=status.HTTP_201_CREATED)
async def record_proctoring_event(
    data: ProctoringEventCreate,
    db: AsyncSession = Depends(get_db)
):
    """Webhook for the AI Proctoring Service to report violations."""
    service = ProctoringService(db)
    try:
        event = await service.record_event(data)
        import logging
        logging.getLogger(__name__).info(f"WEBHOOK RECEIVED: event_type={data.event_type} risk_score={data.risk_score} session_id={data.session_id}")
        if event is None:
            return {"status": "skipped", "message": "Session not found", "event_id": data.event_id}
        return {
            "id": event.id,
            "event_id": event.event_id,
            "session_id": event.session_id,
            "event_type": event.event_type,
            "severity": event.severity,
            "risk_score": event.risk_score,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "metadata": event.meta or {}
        }
    except ValueError as e:
        # Session not found
        logger.warning(f"Webhook error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Check if it's a unique constraint violation (duplicate event_id)
        error_str = str(e)
        if "UNIQUE constraint failed" in error_str or "duplicate key" in error_str.lower():
            logger.info(f"Webhook received duplicate event_id: {data.event_id}. Returning 200 OK.")
            return {"status": "skipped", "message": "Duplicate event_id", "event_id": data.event_id}
        
        logger.error(f"Error recording proctoring event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/terminate/{session_id}")
async def terminate_proctoring_session(
    session_id: str,
    reason: str = "Manual termination",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Terminate a proctoring session manually.
    """
    service = ProctoringService(db)
    success = await service.terminate_session(session_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "terminated"}


@router.get("/assessment/{assessment_id}/session")
async def get_session_by_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the proctoring session for a specific assessment attempt."""
    service = ProctoringService(db)
    session = await service.get_session_by_assessment(assessment_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Proctoring session not found for this assessment")
        
    return {
        "session_id": session.id,
        "status": session.status,
        "final_risk_score": session.final_risk_score,
        "total_violations": session.total_violations,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "terminated_reason": session.terminated_reason
    }

@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get current proctoring session status.
    """
    service = ProctoringService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.id,
        "status": session.status,
        "final_risk_score": session.final_risk_score,
        "total_violations": session.total_violations,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "terminated_reason": session.terminated_reason
    }


@router.get("/session/{session_id}/events")
async def get_session_events(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all events for a proctoring session.
    """
    service = ProctoringService(db)
    events = await service.get_session_events(session_id)
    return events


@router.get("/session/{session_id}/evidence")
async def get_session_evidence(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all evidence for a proctoring session (transcripts, screenshots).
    """
    service = ProctoringService(db)
    evidence = await service.get_session_evidence(session_id)
    return evidence
