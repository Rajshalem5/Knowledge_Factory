"""
WebSocket message schemas for the AI Proctoring Backend.

This module defines Pydantic models for messages exchanged over the
WebSocket connection at /ws/proctor/{session_id}.

Requirements: 11.3, 11.4, 11.5
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class WSIncomingMessage(BaseModel):
    """
    Schema for messages sent by the WebSocket client to the server.
    """

    type: str
    frame: Optional[str] = None
    audio: Optional[str] = None
    event_type: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: Optional[str] = None


class WSEventMessage(BaseModel):
    """
    Schema for event messages sent by the server to the WebSocket client.

    After the Worker_Manager processes an audio or video task, the result
    is forwarded to the client as a ``WSEventMessage``.

    Attributes:
        event: Name of the detected event (e.g. ``"mobile_detected"``,
               ``"looking_away"``).
        risk_level: Categorical risk classification — one of
                    ``"LOW"``, ``"MEDIUM"``, or ``"HIGH"``.
        timestamp: UTC datetime at which the event was detected.
        session_id: Identifier of the proctoring session this event
                    belongs to.
        details: Optional additional payload specific to the event type
                 (e.g. detection bounding boxes, transcript text).
                 May be any JSON-serialisable value.

    Example::

        {
            "event": "keyword_detected",
            "risk_level": "MEDIUM",
            "timestamp": "2024-01-15T10:30:00Z",
            "session_id": "exam-session-42",
            "details": {"rule_flags": ["keyword_detected"], "risk_score": 2}
        }
    """

    event: str
    risk_level: str
    timestamp: datetime
    session_id: str
    details: Optional[Any] = None
