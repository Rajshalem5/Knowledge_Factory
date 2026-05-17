"""Email integration — SMTP with console fallback.

Configure via environment variables:
  SMTP_HOST       — SMTP server (e.g. smtp.gmail.com)
  SMTP_PORT       — SMTP port (default 587)
  SMTP_USER       — SMTP username
  SMTP_PASSWORD   — SMTP password
  SMTP_FROM       — From address (default: noreply@knowledgefactory.com)

If SMTP_HOST is not set, emails are logged to console (dev mode).
"""

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ── SMTP Configuration from env ────────────────────────────────────
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@knowledgefactory.com")

_USE_SMTP = bool(SMTP_HOST and SMTP_USER)


async def send_email(
    to: str,
    subject: str,
    body: str,
    html: str | None = None,
) -> bool:
    """Send a transactional email via SMTP or log as fallback."""
    if _USE_SMTP:
        return await _smtp_send(to, subject, body, html)
    else:
        logger.info(
            "📧 [SMTP not configured] Would send to=%s subject=%s body=%s...",
            to, subject, body[:100] if body else "(empty)",
        )
        return True


async def send_password_reset_email(to: str, reset_token: str) -> bool:
    """Send a password reset email."""
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    if _USE_SMTP:
        return await send_email(
            to=to,
            subject="Password Reset - Knowledge Factory",
            body=f"Reset your password using this link: {reset_link}\n\nToken: {reset_token}",
            html=f"<p>Reset your password using <a href='{reset_link}'>this link</a>.</p>"
            f"<p>Or use this token: <code>{reset_token}</code></p>",
        )
    else:
        logger.info(
            "🔑 PASSWORD RESET: to=%s link=%s",
            to, reset_link,
        )
        return True


async def _smtp_send(to: str, subject: str, body: str, html: str | None = None) -> bool:
    """Send via SMTP synchronously using a thread pool executor."""
    import asyncio
    import smtplib

    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to

        msg.attach(MIMEText(body, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info("✅ Email sent to %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("❌ Email failed to %s: %s", to, exc)
        return False
