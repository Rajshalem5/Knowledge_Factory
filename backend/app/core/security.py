# app/core/security.py

from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(
        password,
        hashed_password
    )


def create_access_token(data: dict):
    expire_time = datetime.now(
        timezone.utc
    ) + timedelta(
        hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
    )

    payload = data.copy()

    payload.update({
        "exp": expire_time
    })

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
