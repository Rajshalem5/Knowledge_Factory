"""Security utilities - modernized with Argon2 and simplified token structure."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

# Use argon2-cffi for secure password hashing
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHash
    _ph = PasswordHasher()
    _USE_ARGON2 = True
except ImportError:
    _USE_ARGON2 = False
    import bcrypt

from jose import jwt

from app.config import settings


def _get_secret() -> str:
    """Return JWT signing secret."""
    if settings.JWT_PRIVATE_KEY:
        return settings.JWT_PRIVATE_KEY
    return secrets.token_urlsafe(64)


def _get_public_key() -> str:
    """Get public key (same as secret for HS256)."""
    if settings.JWT_PUBLIC_KEY:
        return settings.JWT_PUBLIC_KEY
    return _get_secret()


_ALGORITHM = "RS256" if settings.JWT_PRIVATE_KEY else "HS256"


def hash_password(password: str) -> str:
    """Hash password using Argon2 (preferred) or bcrypt fallback."""
    if _USE_ARGON2:
        return _ph.hash(password)
    else:
        # Fallback to bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    if _USE_ARGON2:
        try:
            _ph.verify(hashed_password, plain_password)
            return True
        except (VerifyMismatchError, InvalidHash):
            return False
    else:
        # Fallback to bcrypt
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )


def create_access_token(
    subject: str | Any,
    email: str | None = None,
    role: str | None = None,
) -> str:
    """Create JWT access token."""
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "email": email if email else None,
        "role": role,
    }

    return jwt.encode(to_encode, _get_secret(), algorithm=_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create refresh token."""
    expires_delta = timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "type": "refresh",
    }

    return jwt.encode(to_encode, _get_secret(), algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT token."""
    try:
        return jwt.decode(
            token,
            _get_public_key(),
            algorithms=[_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except Exception:
        return None
