"""
Integration with the Main Backend.
"""

import uuid
import logging
import httpx
import asyncio
from datetime import datetime, timezone
from app.core.config import get_config

logger = logging.getLogger(__name__)

async def emit_proctoring_event(
    session_id: str,
    event_type: str,
    severity: str,
    risk_score: float,
    transcript: str = None,
    screenshot_url: str = None,
    metadata: dict = None
):
    """
    Asynchronously emit a proctoring event to the main backend.
    """
    config = get_config()
    webhook_url = f"{config.MAIN_BACKEND_URL}/api/proctoring/webhook/event"
    
    # Use uuid4 for a truly unique event_id to satisfy UNIQUE constraints
    event_id = f"evt_{str(uuid.uuid4())[:18]}"
    
    payload = {
        "event_id": event_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "severity": severity,
        "risk_score": risk_score,
        "transcript": transcript,
        "screenshot_url": screenshot_url,
        "metadata": metadata or {}
    }
    
    # Run in background to not block inference
    asyncio.create_task(_send_webhook(webhook_url, payload))

async def _send_webhook(url: str, payload: dict, retries: int = 3):
    """
    Internal helper to send the webhook with retries.
    """
    async with httpx.AsyncClient() as client:
        for i in range(retries):
            try:
                response = await client.post(url, json=payload, timeout=5.0)
                if response.status_code < 300:
                    return
                logger.warning(f"Webhook failed with status {response.status_code}, retry {i+1}")
            except Exception as e:
                logger.warning(f"Webhook error: {e}, retry {i+1}")
            
            await asyncio.sleep(2 ** i) # Exponential backoff
        
        logger.error(f"Webhook failed after {retries} retries for session {payload.get('session_id')}")
