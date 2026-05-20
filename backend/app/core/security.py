"""Security utilities - modernized with Argon2 and simplified token structure."""

import secrets
import logging
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Use argon2-cffi for secure password hashing
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHash
    _ph = PasswordHasher()
    _USE_ARGON2 = True
    logger.info("Using Argon2 for password hashing")
except ImportError:
    _USE_ARGON2 = False
    logger.info("Argon2 not found, bcrypt will be used for password hashing")

from jose import jwt

from app.config import settings

# Use stable secret from config, fallback to JWT_PRIVATE_KEY if set
_SECRET = settings.JWT_PRIVATE_KEY or settings.JWT_SECRET_KEY
_ALGORITHM = "RS256" if settings.JWT_PRIVATE_KEY else "HS256"


def _get_secret() -> str:
    return _SECRET


def _get_public_key() -> str:
    return settings.JWT_PUBLIC_KEY if settings.JWT_PUBLIC_KEY else _SECRET


def hash_password(password: str) -> str:
    """Hash password using bcrypt (standardized for consistency)."""
    # Always use bcrypt as requested for consistency
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    logger.debug(f"Hashed password with bcrypt. Prefix: {hashed[:10]}...")
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    if not hashed_password:
        logger.warning("Empty hash provided for verification")
        return False
    
    prefix = hashed_password[:10]
    logger.debug(f"Verifying password against hash with prefix: {prefix}")

    # Robust check for Argon2 if hash starts with $argon2
    if hashed_password.startswith("$argon2"):
        if _USE_ARGON2:
            try:
                _ph.verify(hashed_password, plain_password)
                logger.debug("Argon2 verification successful")
                return True
            except (VerifyMismatchError, InvalidHash) as e:
                logger.debug(f"Argon2 verification failed: {type(e).__name__}")
                return False
        else:
            logger.error("Hash is Argon2 but argon2-cffi is not installed. Verification will fail.")
            return False
    
    # Default to bcrypt
    try:
        result = bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
        logger.debug(f"Bcrypt verification {'successful' if result else 'failed'}")
        return result
    except ValueError as e:
        logger.error(f"Bcrypt verification error (possibly invalid salt or Argon2 hash passed to bcrypt): {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False


def create_proctoring_token(
    subject: str,
    session_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a specialized JWT token for the AI Proctoring Service.
    Signed with PROCTORING_JWT_SECRET.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=2)

    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "session_id": session_id,
        "type": "proctoring_ws",
    }

    # Use specialized secret for proctoring
    return jwt.encode(to_encode, settings.PROCTORING_JWT_SECRET, algorithm="HS256")


def create_access_token(
    subject: str | Any,
    email: str | None = None,
    role: str | None = None,
    token_type: str | None = None,
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

    if token_type:
        to_encode["type"] = token_type

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
