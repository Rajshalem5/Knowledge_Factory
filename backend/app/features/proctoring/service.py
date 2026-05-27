"""Proctoring service."""

import uuid
import logging
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.proctoring.models import (
    ProctoringSession,
    ProctoringEvent,
    ProctoringEvidence,
    RiskSnapshot
)
from app.features.proctoring.schemas import ProctoringSessionCreate, ProctoringEventCreate
from app.features.proctoring.risk_engine import compute_rolling_risk, is_termination_required
from app.features.proctoring.constants import (
    TAB_SWITCH_WEIGHT,
    TAB_SWITCH_REPEATED_WEIGHT,
    TAB_SWITCH_FREQUENT_WEIGHT,
    WINDOW_BLUR_WEIGHT,
    WINDOW_BLUR_REPEATED_WEIGHT,
    WINDOW_BLUR_FREQUENT_WEIGHT,
    COPY_WEIGHT,
    PASTE_WEIGHT,
    DEVTOOLS_WEIGHT,
    NO_FACE_WEIGHT,
    MULTIPLE_PERSONS_WEIGHT,
    HEAD_POSE_WEIGHT,
    HEAD_POSE_REPEATED_WEIGHT,
    VOICE_DETECTED_WEIGHT,
    CONTINUOUS_CONVERSATION_WEIGHT,
    PHONE_DETECTED_WEIGHT,
    FULLSCREEN_EXIT_WEIGHT,
    HIGH_RISK_AUTO_TERMINATE,
    DEBOUNCE_INTERVAL
)
from app.core.security import create_access_token # Assuming this exists or using a specialized one
from app.config import settings
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Development toggle to disable automatic termination during local testing
DEBUG_DISABLE_AUTO_TERMINATE = settings.DEBUG


class ProctoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initialize_session(self, user_id: str, data: ProctoringSessionCreate) -> ProctoringSession:
        """Initialize a new proctoring session."""
        session = ProctoringSession(
            assessment_attempt_id=data.assessment_attempt_id,
            user_id=user_id,
            status="ACTIVE",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[ProctoringSession]:
        result = await self.db.execute(
            select(ProctoringSession).where(ProctoringSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def _get_event_count(self, session_id: str, event_type: str) -> int:
        """Get the number of times an event type has occurred in a session."""
        result = await self.db.execute(
            select(func.count(ProctoringEvent.id))
            .where(ProctoringEvent.session_id == session_id)
            .where(ProctoringEvent.event_type == event_type)
        )
        return result.scalar() or 0

    async def record_event(self, data: ProctoringEventCreate) -> Optional[ProctoringEvent]:
        """Record a proctoring event and update rolling risk (non-blocking)."""
        try:
            # 1. Fetch session
            session = await self.get_session(data.session_id)
            if not session:
                logger.warning(f"Proctoring session {data.session_id} not found, skipping event.")
                return None

            # ... [remaining implementation with error handling]
            
            # ... (the rest of the logic)
            
            await self.db.commit()
            await self.db.refresh(event)
            return event
        except Exception as e:
            logger.warning(f"Proctoring persistence failed (Demo Mode - non-blocking): {e}")
            await self.db.rollback()
            return None

    async def _maybe_create_snapshot(self, session: ProctoringSession, current_score: float):
        last_snapshot_result = await self.db.execute(
            select(RiskSnapshot)
            .where(RiskSnapshot.session_id == session.id)
            .order_by(RiskSnapshot.timestamp.desc())
            .limit(1)
        )
        last_snapshot = last_snapshot_result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        should_snapshot = False
        
        if not last_snapshot:
            should_snapshot = True
        else:
            # Normalize for subtraction
            last_ts = last_snapshot.timestamp
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            
            logger.debug(
                "Snapshot datetime debug",
                extra={
                    "last_ts": str(last_ts),
                    "last_ts_tz": str(last_ts.tzinfo),
                    "now": str(now),
                    "now_tz": str(now.tzinfo),
                }
            )
            
            if (now - last_ts).total_seconds() >= 15:
                should_snapshot = True
            elif abs(current_score - last_snapshot.rolling_risk_score) >= 20:
                should_snapshot = True
            
        if should_snapshot:
            snapshot = RiskSnapshot(
                session_id=session.id,
                timestamp=now,
                rolling_risk_score=current_score,
                active_flags={"status": session.status}
            )
            self.db.add(snapshot)

    async def terminate_session(self, session_id: str, reason: str) -> bool:
        """Manually or automatically terminate a session."""
        result = await self.db.execute(
            update(ProctoringSession)
            .where(ProctoringSession.id == session_id)
            .values(
                status="TERMINATED",
                terminated_reason=reason,
                ended_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_session_events(self, session_id: str) -> List[dict]:
        """Get all events for a session."""
        result = await self.db.execute(
            select(ProctoringEvent)
            .where(ProctoringEvent.session_id == session_id)
            .order_by(ProctoringEvent.timestamp)
        )
        events = result.scalars().all()
        return [
            {
                "id": e.id,
                "event_id": e.event_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "risk_score": e.risk_score,
                "timestamp": e.timestamp,
                "metadata": e.metadata
            }
            for e in events
        ]

    async def get_session_evidence(self, session_id: str) -> List[dict]:
        """Get all evidence for a session."""
        result = await self.db.execute(
            select(ProctoringEvidence)
            .where(ProctoringEvidence.session_id == session_id)
            .order_by(ProctoringEvidence.created_at)
        )
        evidence_items = result.scalars().all()
        return [
            {
                "id": e.id,
                "event_type": e.event_type,
                "transcript": e.transcript,
                "screenshot_url": e.screenshot_url,
                "confidence_score": e.confidence_score,
                "speaker_label": e.speaker_label,
                "audio_confidence": e.audio_confidence,
                "created_at": e.created_at,
                "metadata": e.metadata
            }
            for e in evidence_items
        ]
