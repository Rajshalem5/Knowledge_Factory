"""Security utilities: JWT encode/decode, password hashing, refresh tokens.

Per architecture doc Section 9.1:
- JWT access tokens (HS256 in dev, RS256 in prod)
- Refresh tokens stored in httpOnly cookies
- Password hashing with bcrypt cost factor 12
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.config import settings


def _get_secret() -> str:
    """Return JWT signing secret — PEM key if configured, else crypto-random."""
    if settings.JWT_PRIVATE_KEY:
        return settings.JWT_PRIVATE_KEY
    # Dev fallback: generate a stable random secret from env or fresh each restart
    return secrets.token_urlsafe(64)


def _get_public_key() -> str:
    if settings.JWT_PUBLIC_KEY:
        return settings.JWT_PUBLIC_KEY
    return _get_secret()


_ALGORITHM = "RS256" if settings.JWT_PRIVATE_KEY else "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    subject: str | Any,
    tenant_id: str | None = None,
    role: str | None = None,
) -> str:
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "role": role,
    }

    return jwt.encode(to_encode, _get_secret(), algorithm=_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expires_delta = timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "type": "refresh",
    }

    return jwt.encode(to_encode, _get_secret(), algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            _get_public_key(),
            algorithms=[_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except Exception:
        return None
