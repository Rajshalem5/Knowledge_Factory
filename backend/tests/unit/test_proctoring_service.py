"""Unit tests for the ProctoringService.

Tests violation event recording, warning thresholds, and automatic
termination logic for high-severity events and max-warnings exceeded.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.features.proctoring.service import ProctoringService
from app.features.proctoring.models import ProctoringRecord
from app.features.proctoring.schemas import ProctoringEventCreate
from app.core.enums import ProctoringEventType, ProctoringSeverity


@pytest.fixture
def mock_db():
    """Create a mock AsyncSession with proper async execute."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    execute_result = MagicMock()
    db.execute = AsyncMock(return_value=execute_result)
    return db


class TestProctoringService:
    """Test ProctoringService.record_event."""

    def _make_record(self, **overrides) -> ProctoringRecord:
        defaults = dict(
            id="pr-test",
            assessment_id="asm-test",
            candidate_id="cand-test",
            violations_json=[],  # Explicit list, not None
            warning_count=0,
            terminated=False,
            retention_expiry=datetime.now(timezone.utc).date() + timedelta(days=20),
        )
        defaults.update(overrides)
        return ProctoringRecord(**defaults)

    async def test_record_event_creates_new_record(self, mock_db):
        """A new ProctoringRecord is created when none exists."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        service = ProctoringService(mock_db)
        data = ProctoringEventCreate(
            assessment_id="asm-001",
            candidate_id="cand-001",
            event_type=ProctoringEventType.TAB_SWITCH,
            severity=ProctoringSeverity.LOW,
            evidence={"timestamp": 123},
        )
        result = await service.record_event(data)

        assert result["warning_count"] == 1
        assert result["terminated"] is False
        assert result["reason"] is None
        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, ProctoringRecord)
        assert added.assessment_id == "asm-001"

    async def test_record_event_updates_existing(self, mock_db):
        """Existing ProctoringRecord is updated."""
        existing = self._make_record(assessment_id="asm-001", candidate_id="cand-001")
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing

        service = ProctoringService(mock_db)
        data = ProctoringEventCreate(
            assessment_id="asm-001",
            candidate_id="cand-001",
            event_type=ProctoringEventType.COPY_PASTE,
            severity=ProctoringSeverity.MEDIUM,
        )
        result = await service.record_event(data)

        assert result["warning_count"] == 1
        assert result["terminated"] is False
        mock_db.add.assert_not_called()
        assert len(existing.violations_json) == 1
        assert existing.violations_json[0]["type"] == "copy_paste"

    async def test_high_severity_triggers_immediate_termination(self, mock_db):
        """A single HIGH severity event terminates immediately."""
        existing = self._make_record(assessment_id="asm-hi", candidate_id="cand-hi")
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing

        service = ProctoringService(mock_db)
        data = ProctoringEventCreate(
            assessment_id="asm-hi",
            candidate_id="cand-hi",
            event_type=ProctoringEventType.MULTIPLE_FACES,
            severity=ProctoringSeverity.HIGH,
        )
        result = await service.record_event(data)

        assert result["warning_count"] == 1
        assert result["terminated"] is True
        assert "High-severity" in (result["reason"] or "")

    async def test_max_warnings_triggers_termination_on_boundary(self, mock_db):
        """At PROCTORING_MAX_WARNINGS, termination triggers."""
        with patch("app.features.proctoring.service.settings.PROCTORING_MAX_WARNINGS", 25):
            existing = self._make_record(
                assessment_id="asm-max", candidate_id="cand-max", warning_count=24,
            )
            mock_db.execute.return_value.scalar_one_or_none.return_value = existing

            service = ProctoringService(mock_db)
            data = ProctoringEventCreate(
                assessment_id="asm-max",
                candidate_id="cand-max",
                event_type=ProctoringEventType.RIGHT_CLICK,
                severity=ProctoringSeverity.MEDIUM,
            )
            result = await service.record_event(data)

        assert result["warning_count"] == 25
        assert result["terminated"] is True
        assert "Exceeded maximum warnings" in (result["reason"] or "")

    async def test_below_max_warnings_no_termination(self, mock_db):
        """Below PROCTORING_MAX_WARNINGS, no termination."""
        with patch("app.features.proctoring.service.settings.PROCTORING_MAX_WARNINGS", 10):
            existing = self._make_record(
                assessment_id="asm-below", candidate_id="cand-below", warning_count=3,
            )
            mock_db.execute.return_value.scalar_one_or_none.return_value = existing

            service = ProctoringService(mock_db)
            data = ProctoringEventCreate(
                assessment_id="asm-below",
                candidate_id="cand-below",
                event_type=ProctoringEventType.TAB_SWITCH,
                severity=ProctoringSeverity.LOW,
            )
            result = await service.record_event(data)

        assert result["warning_count"] == 4
        assert result["terminated"] is False
        assert result["reason"] is None

    async def test_event_recorded_with_correct_fields(self, mock_db):
        """The recorded event includes type, severity, timestamp, and evidence."""
        existing = self._make_record(assessment_id="asm-fields", candidate_id="cand-fields")
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing

        service = ProctoringService(mock_db)
        data = ProctoringEventCreate(
            assessment_id="asm-fields",
            candidate_id="cand-fields",
            event_type=ProctoringEventType.PHONE_DETECTED,
            severity=ProctoringSeverity.HIGH,
            evidence={"camera_snapshot": "phone_in_hand.jpg"},
        )
        result = await service.record_event(data)

        assert result["warning_count"] == 1
        assert result["terminated"] is True
        event = existing.violations_json[0]
        assert event["type"] == "phone_detected"
        assert event["severity"] == "high"
        assert "timestamp" in event
        assert event["evidence"]["camera_snapshot"] == "phone_in_hand.jpg"
