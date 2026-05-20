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
    COPY_PASTE_WEIGHT,
    WINDOW_BLUR_WEIGHT,
    NO_FACE_WEIGHT,
    VOICE_DETECTED_WEIGHT,
    MULTIPLE_PERSONS_WEIGHT,
    PHONE_DETECTED_WEIGHT,
    FULLSCREEN_EXIT_WEIGHT,
    HIGH_RISK_AUTO_TERMINATE,
    DEBOUNCE_INTERVAL
)
from app.core.security import create_access_token # Assuming this exists or using a specialized one
from app.config import settings

logger = logging.getLogger(__name__)

# Development toggle to disable automatic termination during local testing
DEBUG_DISABLE_AUTO_TERMINATE = settings.DEBUG


WEIGHT_MAP = {
    "TAB_SWITCH": TAB_SWITCH_WEIGHT,
    "COPY_PASTE": COPY_PASTE_WEIGHT,
    "WINDOW_BLUR": WINDOW_BLUR_WEIGHT,
    "NO_FACE": NO_FACE_WEIGHT,
    "VOICE_DETECTED": VOICE_DETECTED_WEIGHT,
    "MULTIPLE_PERSONS": MULTIPLE_PERSONS_WEIGHT,
    "PHONE_DETECTED": PHONE_DETECTED_WEIGHT,
    "FULLSCREEN_EXIT": FULLSCREEN_EXIT_WEIGHT,
}

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

    async def record_event(self, data: ProctoringEventCreate) -> ProctoringEvent:
        """Record a proctoring event and update rolling risk."""
        # 1. Fetch session
        session = await self.get_session(data.session_id)
        if not session:
            logger.error(f"Proctoring session {data.session_id} not found")
            raise ValueError("Session not found")

        # 2. Check for duplicate event_id (UNIQUE constraint protection)
        existing_event_result = await self.db.execute(
            select(ProctoringEvent).where(ProctoringEvent.event_id == data.event_id)
        )
        existing_event = existing_event_result.scalar_one_or_none()
        if existing_event:
            logger.info(f"Duplicate event_id detected: {data.event_id}. Skipping insertion.")
            return existing_event

        # 3. Debounce repeated detections of the same type
        last_event_result = await self.db.execute(
            select(ProctoringEvent)
            .where(ProctoringEvent.session_id == data.session_id)
            .order_by(ProctoringEvent.timestamp.desc())
            .limit(1)
        )
        last_event = last_event_result.scalar_one_or_none()
        
        if last_event and last_event.event_type == data.event_type:
            last_ts = last_event.timestamp.replace(tzinfo=timezone.utc) if last_event.timestamp.tzinfo is None else last_event.timestamp
            time_since_last = (data.timestamp - last_ts).total_seconds()
            if time_since_last < DEBOUNCE_INTERVAL:
                logger.info(f"Debouncing event {data.event_type} for session {data.session_id} (only {time_since_last:.1f}s since last)")
                return last_event

        # 4. Compute new rolling risk
        last_time = last_event.timestamp if last_event else session.started_at
        
        weight = WEIGHT_MAP.get(data.event_type, 0.0)
        new_risk_score = compute_rolling_risk(
            previous_score=session.final_risk_score,
            last_event_time=last_time,
            current_time=data.timestamp,
            event_weight=weight
        )

        # 5. Persist Event
        logger.info(f"Event Accepted: {data.event_type} (Weight: {weight}) for session {data.session_id}")
        event = ProctoringEvent(
            id=str(uuid.uuid4()), # Ensure internal ID is unique
            session_id=data.session_id,
            event_id=data.event_id,
            timestamp=data.timestamp,
            event_type=data.event_type,
            severity=data.severity,
            risk_score=new_risk_score,
            meta=data.metadata
        )
        self.db.add(event)

        # 6. Persist Evidence if applicable
        if data.transcript or data.screenshot_url:
            evidence = ProctoringEvidence(
                session_id=data.session_id,
                event_type=data.event_type,
                transcript=data.transcript,
                screenshot_url=data.screenshot_url,
                confidence_score=data.confidence_score,
                speaker_label=data.speaker_label,
                audio_confidence=data.audio_confidence,
                meta=data.metadata
            )
            self.db.add(evidence)

        # 7. Update Session
        session.final_risk_score = new_risk_score
        if weight > 0:
            session.total_violations += 1

        # 8. Check for auto-termination
        if HIGH_RISK_AUTO_TERMINATE and is_termination_required(new_risk_score) and not DEBUG_DISABLE_AUTO_TERMINATE:
            session.status = "TERMINATED"
            session.terminated_reason = f"High risk score: {new_risk_score}"
            session.ended_at = datetime.now(timezone.utc)
            logger.warning(f"Session {session.id} terminated due to high risk (Score: {new_risk_score})")
        else:
            if new_risk_score > 0:
                if DEBUG_DISABLE_AUTO_TERMINATE and is_termination_required(new_risk_score):
                    logger.info(f"DEVELOPMENT MODE: Session {session.id} reached high risk ({new_risk_score:.2f}) but auto-termination is disabled.")
                else:
                    logger.info(f"Current Risk Score for session {session.id}: {new_risk_score:.2f}")

        # 9. Periodic Risk Snapshot
        await self._maybe_create_snapshot(session, new_risk_score)

        try:
            await self.db.commit()
            await self.db.refresh(event)
        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE constraint failed: proctoring_events.event_id" in str(e):
                logger.info(f"Concurrent duplicate event_id detected: {data.event_id}. Rolling back.")
                # Return the existing event
                res = await self.db.execute(select(ProctoringEvent).where(ProctoringEvent.event_id == data.event_id))
                return res.scalar_one()
            raise e
            
        return event

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
