"""Email integration: SES / SendGrid wrapper.

Sends transactional emails (OTP, password reset, assessment invites,
offer letters) and supports batch sends via Celery tasks.

Current implementation logs to stdout for development;
production builds should plug into SendGrid/SES.
"""

import logging

logger = logging.getLogger(__name__)


async def send_email(
    to: str,
    subject: str,
    body: str,
    html: str | None = None,
) -> bool:
    """Send a single transactional email.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text body.
        html: Optional HTML body (preferred if both provided).

    Returns:
        True if the email was accepted for delivery.
    """
    logger.info(
        "Email stub — would send email to=%s subject=%s body_preview=%s...",
        to,
        subject,
        body[:100] if body else "(empty)",
    )
    # TODO: Replace with actual SendGrid/SES integration in production
    return True


async def send_password_reset_email(to: str, reset_token: str) -> bool:
    """Send a password reset email with the reset token embedded in a link."""
    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
    logger.info(
        "PASSWORD RESET: to=%s link=%s token_preview=%s...",
        to,
        reset_link,
        reset_token[:20],
    )
    return await send_email(
        to=to,
        subject="Password Reset - Knowledge Factory",
        body=f"Reset your password using this link: {reset_link}\n\nToken: {reset_token}",
        html=f"<p>Reset your password using <a href='{reset_link}'>this link</a>.</p>",
    )
