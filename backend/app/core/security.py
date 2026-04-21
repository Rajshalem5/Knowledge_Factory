"""
Security utilities: JWT encode/decode, password hashing.

This module implements the security architecture described in Section 9.1:
- JWT access tokens (RS256/HS256)
- Password hashing with Bcrypt directly (avoiding passlib issues on Python 3.13)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )


def create_access_token(subject: str | Any, tenant_id: str | None = None, role: str | None = None) -> str:
    """
    Create a JWT access token.
    """
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "role": role,
    }
    
    algorithm = "RS256" if settings.JWT_PRIVATE_KEY else "HS256"
    secret = settings.JWT_PRIVATE_KEY if settings.JWT_PRIVATE_KEY else "development-secret-key"
    
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt
