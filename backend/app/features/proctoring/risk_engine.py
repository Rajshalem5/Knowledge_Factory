"""Weighted rolling risk scoring engine."""

import math
import logging
from datetime import datetime, timezone
from app.config import settings
from app.features.proctoring.constants import (
    RISK_DECAY_PERCENT,
    RISK_DECAY_INTERVAL,
    RISK_TERMINATION_THRESHOLD
)

logger = logging.getLogger(__name__)

def compute_rolling_risk(
    previous_score: float,
    last_event_time: datetime,
    current_time: datetime,
    event_weight: float = 0
) -> float:
    """
    Compute new rolling risk score with exponential decay.
    
    Formula:
    rolling_risk = decay(previous_score) + event_weight
    """
    # Standardize to timezone-aware UTC
    if last_event_time.tzinfo is None:
        last_event_time = last_event_time.replace(tzinfo=timezone.utc)
    
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    # Ensure both are UTC if they were already aware but in different zones
    last_event_time = last_event_time.astimezone(timezone.utc)
    current_time = current_time.astimezone(timezone.utc)

    logger.debug(
        "Rolling risk datetime check",
        extra={
            "last_event_time": str(last_event_time),
            "last_event_tz": str(last_event_time.tzinfo),
            "current_time": str(current_time),
            "current_time_tz": str(current_time.tzinfo),
        }
    )

    # Calculate seconds since last update
    seconds_passed = (current_time - last_event_time).total_seconds()
    
    # Handle negative time if events arrive out of order
    if seconds_passed < 0:
        logger.warning(f"Negative time delta detected in risk calculation: {seconds_passed}s. Treating as 0.")
        seconds_passed = 0
    
    # Apply exponential decay
    # Every RISK_DECAY_INTERVAL seconds, the score decays by RISK_DECAY_PERCENT
    decay_steps = seconds_passed / RISK_DECAY_INTERVAL
    decayed_score = previous_score * math.pow(1 - RISK_DECAY_PERCENT, decay_steps)
    
    # Add new event weight
    new_score = decayed_score + event_weight
    
    # Clamp between 0 and 100
    risk_score = max(0.0, min(100.0, new_score))
    logger.info(f"Computed risk score: {risk_score:.2f} (decayed from {previous_score:.2f} over {seconds_passed:.1f}s)")
    return risk_score

def is_termination_required(score: float) -> bool:
    """
    Check if the score exceeds the termination threshold.
    In DEBUG/development mode, we raise the threshold significantly (e.g., 500)
    so that 100 doesn't instantly terminate the assessment.
    """
    threshold = RISK_TERMINATION_THRESHOLD
    if settings.DEBUG:
        # In development, we want to see the violations without being kicked out.
        # We set it to 500 so it's virtually impossible to hit without extreme persistence.
        threshold = 500.0
        if score >= RISK_TERMINATION_THRESHOLD:
            logger.info(f"DEVELOPMENT MODE: Risk score {score:.2f} exceeds production threshold {RISK_TERMINATION_THRESHOLD}, but auto-termination is relaxed.")

    is_required = score >= threshold
    if is_required:
        logger.warning(f"Termination threshold reached! Score: {score:.2f}, Threshold: {threshold}")
    
    return is_required
