"""Unit tests for the EmailLog (notification) model."""

from datetime import datetime, timezone
from app.features.notifications.models import EmailLog


class TestEmailLog:
    """Test EmailLog model creation and string representation."""

    def test_email_log_creation(self):
        """An EmailLog can be instantiated with all required fields."""
        now = datetime.now(timezone.utc)
        log = EmailLog(
            id="test-id-001",
            template_name="welcome_email",
            recipient_email="candidate@test.com",
            subject="Welcome to Knowledge Factory",
            status="SENT",
            provider_message_id="provider-msg-001",
            error_message=None,
            sent_at=now,
        )
        assert log.id == "test-id-001"
        assert log.template_name == "welcome_email"
        assert log.recipient_email == "candidate@test.com"
        assert log.subject == "Welcome to Knowledge Factory"
        assert log.status == "SENT"
        assert log.provider_message_id == "provider-msg-001"
        assert log.error_message is None
        assert log.sent_at == now

    def test_email_log_supports_various_statuses(self):
        """EmailLog works with different status values."""
        now = datetime.now(timezone.utc)
        for status in ("SENT", "DELIVERED", "BOUNCED", "FAILED"):
            log = EmailLog(
                id=f"test-{status.lower()}",
                template_name="test",
                recipient_email="user@test.com",
                subject="Test",
                status=status,
                sent_at=now,
            )
            assert log.status == status

    def test_email_log_supports_null_provider(self):
        """provider_message_id and error_message can be null."""
        now = datetime.now(timezone.utc)
        log = EmailLog(
            id="test-id-003",
            template_name="notification",
            recipient_email="user@test.com",
            subject="Test",
            status="FAILED",
            provider_message_id=None,
            error_message="Connection refused",
            sent_at=now,
        )
        assert log.provider_message_id is None
        assert log.error_message == "Connection refused"

    def test_email_log_repr(self):
        """String representation includes email and status."""
        now = datetime.now(timezone.utc)
        log = EmailLog(
            id="test-id-004",
            template_name="test",
            recipient_email="candidate@test.com",
            subject="Test Subject",
            status="SENT",
            sent_at=now,
        )
        rep = repr(log)
        assert "candidate@test.com" in rep
        assert "SENT" in rep
        assert "EmailLog" in rep
