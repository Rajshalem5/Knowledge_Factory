"""
Tests for the risk engine decay logic and scoring.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.features.proctoring.risk_engine import compute_rolling_risk, is_termination_required
from app.features.proctoring.constants import RISK_TERMINATION_THRESHOLD


class TestRiskEngineDecay:
    """Test exponential decay of risk scores."""

    def test_decay_with_no_events(self):
        """Test that score decays when no new events occur."""
        previous_score = 50.0
        now = datetime.now(timezone.utc)
        last_time = now - timedelta(seconds=10)

        new_score = compute_rolling_risk(
            previous_score=previous_score,
            last_event_time=last_time,
            current_time=now,
            event_weight=0
        )

        assert new_score < previous_score, "Score should decay over time"
        assert new_score > 0, "Score should remain positive"


    def test_decay_with_event_weight(self):
        """Test that new event adds weight to decayed score."""
        previous_score = 30.0
        now = datetime.now(timezone.utc)
        last_time = now - timedelta(seconds=5)

        new_score = compute_rolling_risk(
            previous_score=previous_score,
            last_event_time=last_time,
            current_time=now,
            event_weight=20
        )

        assert new_score > previous_score, "Score should increase with event"


    def test_score_clamped_max_100(self):
        """Test that score is clamped at 100."""
        new_score = compute_rolling_risk(
            previous_score=100.0,
            last_event_time=datetime.now(timezone.utc),
            current_time=datetime.now(timezone.utc),
            event_weight=50
        )

        assert new_score <= 100.0, "Score should not exceed 100"


    def test_score_clamped_min_0(self):
        """Test that score is clamped at 0."""
        new_score = compute_rolling_risk(
            previous_score=0.0,
            last_event_time=datetime.now(timezone.utc),
            current_time=datetime.now(timezone.utc),
            event_weight=0
        )

        assert new_score >= 0.0, "Score should not go below 0"


    def test_termination_threshold_exceeded(self):
        """Test termination check when threshold is exceeded."""
        score = RISK_TERMINATION_THRESHOLD + 1
        assert is_termination_required(score) is True


    def test_termination_threshold_not_exceeded(self):
        """Test termination check when threshold is not exceeded."""
        score = RISK_TERMINATION_THRESHOLD - 1
        assert is_termination_required(score) is False


    def test_termination_threshold_exact(self):
        """Test termination check at exact threshold."""
        score = RISK_TERMINATION_THRESHOLD
        assert is_termination_required(score) is True
